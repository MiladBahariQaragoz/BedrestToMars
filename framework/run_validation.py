"""Run the tier-3 validation battery.

`DESIGN.md` section 9.3.4. Every run holds out one campaign at a time, as tier 3 always has;
what is new is what changes between runs. On the arm that sees the earlier scans (t-1), the
ablations of section 9.3.2 are repeated and one is added: `scrambled_history` shuffles the
held-out campaign's own earlier values, to ask whether the model reads them at all. On both
arms two robustness checks ask whether the result depends on how the question was put:
`reordered` shows the same reference rows in another order, and `shifted_bins` moves every
range edge by half a step. The history arm is also scored against the arm without history on
the same 84 rows, which is what the earlier scans buy. And a set of requests is sent again
past the cache, to see whether the model answers the same question the same way twice.

    python framework/run_validation.py            # calls TypeSafe for anything not cached
    python framework/run_validation.py --offline  # cached answers only; what `make all` runs

Writes `results/forecast_validation.json`, `results/forecast_validation.csv` and
`results/forecast_repeats.json`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import data_loader
import features
import run_baseline
import run_forecast
import typesafe_client

REPO_ROOT = Path(__file__).resolve().parent.parent
REPEATS_FILE = REPO_ROOT / "results" / "forecast_repeats.json"


def _run(
    config: dict[str, Any],
    resolved: pd.DataFrame,
    answer: run_forecast.Answerer,
    arm: str,
    variant: str,
    levels: list[float],
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    plan = run_forecast.fold_plan(config, resolved, arm, variant=variant)
    responses = answer([{"state": e["state"], "questions": e["questions"]} for e in plan])
    predictions = run_forecast._prediction_rows(
        plan, responses, run_forecast.plan_bins(config, arm, variant), levels
    )
    predictions["variant"] = variant
    return plan, predictions


def compare_repeats(
    originals: list[dict[str, Any]], fresh: list[dict[str, Any]]
) -> dict[str, Any]:
    """How far a second answer to the same request moved from the first, per request."""
    differences = []
    for first, second in zip(originals, fresh):
        (name, answer), = first.items()
        before, after = answer["probabilities"], second[name]["probabilities"]
        labels = set(before) | set(after)
        differences.append(max(abs(before.get(l, 0.0) - after.get(l, 0.0)) for l in labels))
    values = np.asarray(differences, dtype=float)
    return {
        "requests": int(len(values)),
        "identical": int((values < 1e-6).sum()),
        "max_abs_probability_difference": float(values.max()) if len(values) else 0.0,
        "mean_abs_probability_difference": float(values.mean()) if len(values) else 0.0,
    }


def _paired(
    frame: pd.DataFrame, reference: str, model: str, config: dict[str, Any]
) -> dict[str, float]:
    return run_forecast._paired_gain(frame, reference, "abs_error", config, model=model)[1]


def _history_value(
    predictions: pd.DataFrame, config: dict[str, Any], levels: list[float]
) -> dict[str, Any]:
    """The history arm against the arm without it, on the same rows and the same scale.

    The history arm forecasts the change since the last scan; added to that scan it is a
    forecast of the level, and its absolute error is the same number on either scale.
    """
    full = predictions[predictions["variant"] == "full"]
    with_history = full[full["arm"] == "with_history"]
    without = full[(full["arm"] == "without_history") & full["row_id"].isin(with_history["row_id"])]

    def pair(first: str, second: str) -> dict[str, Any]:
        frame = pd.concat(
            [
                with_history[with_history["model"] == first].assign(model="with_history"),
                without[without["model"] == second].assign(model="without_history"),
            ]
        )
        return {
            "with_history": run_forecast.summarise(
                frame[frame["model"] == "with_history"], config, levels
            )["mae"],
            "without_history": run_forecast.summarise(
                frame[frame["model"] == "without_history"], config, levels
            )["mae"],
            "paired_mae_gain_pp": _paired(frame, "without_history", "with_history", config),
        }

    return {
        "rows": int(with_history["row_id"].nunique()),
        "campaigns": int(with_history["cohort"].nunique()),
        "jev": pair("jev", "jev"),
        "baselines": pair(
            config["forecast"]["arms"]["with_history"]["reference_baseline"],
            config["forecast"]["arms"]["without_history"]["reference_baseline"],
        ),
    }


def _repeat(
    config: dict[str, Any],
    plan: list[dict[str, Any]],
    answer: run_forecast.Answerer,
    offline: bool,
    repeat_client: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    count = int(config["forecast"]["validation"]["repeats"])
    requests = [{"state": e["state"], "questions": e["questions"]} for e in plan[:count]]
    originals = [response["answers"] for response in answer(requests)]
    if repeat_client is None and offline:
        if not REPEATS_FILE.exists():
            raise typesafe_client.CacheMiss(f"{REPEATS_FILE} holds no repeated answers")
        fresh = json.loads(REPEATS_FILE.read_text(encoding="utf-8"))
    else:
        client = repeat_client or typesafe_client.client_from_config(config)
        with ThreadPoolExecutor(max_workers=int(config["forecast"]["concurrency"])) as pool:
            fresh = list(pool.map(lambda r: client.ask(r["state"], r["questions"]), requests))
    return compare_repeats(originals, [f["answers"] for f in fresh]), fresh


def run(
    config: dict[str, Any] | None = None,
    answerer: run_forecast.Answerer | None = None,
    offline: bool = False,
    repeat_client: Any = None,
) -> dict[str, Any]:
    config = config or data_loader.load_config()
    settings = config["forecast"]
    levels = [float(level) for level in settings["interval_levels"]]
    resolved = features.resolve(data_loader.subset(data_loader.load(config), config), config, "A")
    answer = answerer or run_forecast._answerer(config, offline)

    plans: dict[tuple[str, str], list[dict[str, Any]]] = {}
    tables = []
    for arm, variants in settings["validation"]["runs"].items():
        for variant in variants:
            plans[(arm, variant)], table = _run(config, resolved, answer, arm, variant, levels)
            tables.append(table)
    predictions = pd.concat(tables, ignore_index=True)

    runs: dict[str, Any] = {}
    for arm, variants in settings["validation"]["runs"].items():
        reference = settings["arms"][arm]["reference_baseline"]
        rows = predictions[predictions["arm"] == arm]
        full = rows[(rows["variant"] == "full") & (rows["model"] == "jev")]
        runs[arm] = {}
        for variant in variants:
            part = rows[rows["variant"] == variant]
            jev = run_forecast.summarise(part[part["model"] == "jev"], config, levels)
            base = run_forecast.summarise(part[part["model"] == reference], config, levels)
            versus_full = pd.concat(
                [full.assign(model="jev_full"),
                 part[part["model"] == "jev"].assign(model="jev_variant")]
            )
            runs[arm][variant] = {
                "jev": jev,
                "reference": {"name": reference, **base},
                "relative_mae_improvement": float((base["mae"] - jev["mae"]) / base["mae"]),
                "paired_mae_gain_vs_reference_pp": _paired(part, reference, "jev", config),
                "paired_mae_change_vs_full_pp": _paired(versus_full, "jev_full", "jev_variant", config),
            }

    repeats, fresh = _repeat(config, plans[("without_history", "full")], answer, offline, repeat_client)
    dataset_path = REPO_ROOT / config["dataset"]["path"]
    return {
        "runs": runs,
        "history_value": _history_value(predictions, config, levels),
        "repeats": repeats,
        "provenance": {
            "model": settings["model"],
            "time_column": settings["time_column"],
            "dataset_version": config["dataset"]["version"],
            "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "seed": int(config["seed"]),
            "cache_hits": getattr(answer, "hits", None),
            "api_calls": getattr(answer, "calls", None),
            "git_commit": run_baseline._git_commit(),
            "python": platform.python_version(),
        },
        "_repeats": fresh,
    }


def write(result: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    body = {key: value for key, value in result.items() if not key.startswith("_")}
    (directory / "forecast_validation.json").write_text(
        json.dumps(body, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (directory / "forecast_repeats.json").write_text(
        json.dumps(result["_repeats"], indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = []
    for arm, variants in result["runs"].items():
        for variant, block in variants.items():
            jev, base = block["jev"], block["reference"]
            gain, change = block["paired_mae_gain_vs_reference_pp"], block["paired_mae_change_vs_full_pp"]
            rows.append(
                {
                    "arm": arm,
                    "variant": variant,
                    "rows": jev["rows"],
                    "folds": jev["folds"],
                    "jev_mae_pp": round(jev["mae"], 3),
                    "jev_crps_pp": round(jev["crps"], 3),
                    "jev_coverage_80": round(jev["coverage_80"], 3),
                    "reference": base["name"],
                    "reference_mae_pp": round(base["mae"], 3),
                    "relative_mae_improvement": round(block["relative_mae_improvement"], 3),
                    "paired_gain_pp": round(gain["point"], 3),
                    "paired_gain_low": round(gain["low"], 3),
                    "paired_gain_high": round(gain["high"], 3),
                    "change_vs_full_pp": round(change["point"], 3),
                    "change_vs_full_low": round(change["low"], 3),
                    "change_vs_full_high": round(change["high"], 3),
                }
            )
    pd.DataFrame(rows).to_csv(directory / "forecast_validation.csv", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="cached answers only")
    args = parser.parse_args()
    result = run(offline=args.offline)
    write(result, REPO_ROOT / "results")

    provenance = result["provenance"]
    print(f"{provenance['cache_hits']} answers from cache, {provenance['api_calls']} API calls\n")
    for arm, variants in result["runs"].items():
        print(f"{arm}")
        for variant, block in variants.items():
            gain, change = block["paired_mae_gain_vs_reference_pp"], block["paired_mae_change_vs_full_pp"]
            print(
                f"  {variant:<21} MAE {block['jev']['mae']:5.2f} vs {block['reference']['mae']:5.2f}"
                f"  gain {gain['point']:+.2f} ({gain['low']:+.2f} to {gain['high']:+.2f})"
                f"  vs full {change['point']:+.2f} ({change['low']:+.2f} to {change['high']:+.2f})"
            )
    value = result["history_value"]
    for name in ("jev", "baselines"):
        block = value[name]
        gain = block["paired_mae_gain_pp"]
        print(
            f"\nwhat the earlier scans buy ({name}, {value['rows']} rows, {value['campaigns']} campaigns): "
            f"{block['without_history']:.2f} -> {block['with_history']:.2f} pp, "
            f"paired {gain['point']:+.2f} ({gain['low']:+.2f} to {gain['high']:+.2f})"
        )
    repeats = result["repeats"]
    print(
        f"\nrepeats: {repeats['identical']} of {repeats['requests']} identical, "
        f"largest probability change {repeats['max_abs_probability_difference']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
