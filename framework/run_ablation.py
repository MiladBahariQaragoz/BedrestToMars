"""Run the tier-3 ablations and the recognition probe.

`DESIGN.md` section 9.3.2. Tier 3's first run beat the duration curve, and more than half of
the gain came from three much-published campaigns. Two explanations fit that: the model reads
something real in the description and the reference data, or it recognises a published study
and recalls its number. This runner separates them as far as one dataset can.

* **Ablations**, on the arm without history. `generic` describes the target only by what
  identifies no study - muscle, role, method, kind of group and day. `scrambled_reference`
  shuffles the other campaigns' values among their rows. `no_reference` removes the other
  campaigns altogether. `full` is the first run itself, answered from its cache.
* **The recognition probe.** The description the full forecast sends is shown on its own, with
  one question: which of these named campaigns does it come from?

    python framework/run_ablation.py            # calls TypeSafe for any answer not cached
    python framework/run_ablation.py --offline  # cached answers only; what `make all` runs

Writes `results/forecast_ablation.json`, `results/forecast_ablation.csv` and
`results/forecast_recognition.csv`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

import data_loader
import features
import forecast
import run_baseline
import run_forecast

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE = "duration_curve"


def _variant_predictions(
    config: dict[str, Any],
    resolved: pd.DataFrame,
    answer: run_forecast.Answerer,
    arm: str,
    variant: str,
    levels: list[float],
) -> pd.DataFrame:
    plan = run_forecast.fold_plan(config, resolved, arm, variant=variant)
    responses = answer([{"state": e["state"], "questions": e["questions"]} for e in plan])
    predictions = run_forecast._prediction_rows(
        plan, responses, forecast.arm_bins(config, arm), levels
    )
    predictions["model"] = predictions["model"].replace({"jev": f"jev_{variant}"})
    if variant != "full":
        predictions = predictions[predictions["model"] != REFERENCE]
    return predictions


def _probe(
    config: dict[str, Any], resolved: pd.DataFrame, answer: run_forecast.Answerer
) -> pd.DataFrame:
    """One row per probed forecast: the probability the model gave the true campaign."""
    campaigns = config["forecast"]["ablation"]["recognition"]["campaigns"]
    rows = resolved[resolved["cohort_id"].isin(campaigns)]
    question = forecast.recognition_question(config)
    requests = [
        {"state": forecast.recognition_state(row, config), "questions": {"campaign": question}}
        for _, row in rows.iterrows()
    ]
    responses = answer(requests)
    records = []
    for (_, row), response in zip(rows.iterrows(), responses):
        given = response["answers"]["campaign"]
        label = forecast.recognition_label(str(row["cohort_id"]), config)
        total = sum(given["probabilities"].values()) or 1.0
        records.append(
            {
                "cohort": str(row["cohort_id"]),
                "label": label,
                "choice": given["choice"],
                "p_true": float(given["probabilities"].get(label, 0.0)) / total,
                "top1": float(given["choice"] == label),
            }
        )
    return pd.DataFrame(records)


def _recognition_summary(
    probe: pd.DataFrame, gains: pd.Series, config: dict[str, Any]
) -> dict[str, Any]:
    options = len(forecast.recognition_question(config)["criteria"])
    per_campaign = probe.groupby("cohort").agg(
        rows=("p_true", "size"),
        mean_p_true=("p_true", "mean"),
        top1=("top1", "mean"),
        top_choice=("choice", lambda values: values.value_counts().index[0]),
    )
    per_campaign["paired_mae_gain_pp"] = gains.reindex(per_campaign.index)

    recognition = per_campaign["mean_p_true"].to_numpy(dtype=float)
    gain = per_campaign["paired_mae_gain_pp"].to_numpy(dtype=float)
    rho, p_value = (None, None)
    if np.ptp(recognition) > 0 and np.ptp(gain) > 0:
        result = stats.spearmanr(recognition, gain)
        rho, p_value = float(result.statistic), float(result.pvalue)

    return {
        "rows": int(len(probe)),
        "chance": 1.0 / options,
        "mean_p_true": float(probe["p_true"].mean()),
        "top1_accuracy": float(probe["top1"].mean()),
        "campaigns": {
            cohort: {
                "rows": int(values["rows"]),
                "mean_p_true": float(values["mean_p_true"]),
                "top1": float(values["top1"]),
                "top_choice": str(values["top_choice"]),
                "paired_mae_gain_pp": float(values["paired_mae_gain_pp"]),
            }
            for cohort, values in per_campaign.iterrows()
        },
        "spearman_with_gain": {"rho": rho, "p": p_value, "n": int(len(per_campaign))},
    }


def run(
    config: dict[str, Any] | None = None,
    answerer: run_forecast.Answerer | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    config = config or data_loader.load_config()
    settings = config["forecast"]
    arm = settings["ablation"]["arm"]
    levels = [float(level) for level in settings["interval_levels"]]
    resolved = features.resolve(data_loader.subset(data_loader.load(config), config), config, "A")
    answer = answerer or run_forecast._answerer(config, offline)

    variants = ["full", *settings["ablation"]["variants"]]
    predictions = pd.concat(
        [_variant_predictions(config, resolved, answer, arm, v, levels) for v in variants],
        ignore_index=True,
    )

    blocks: dict[str, Any] = {}
    for variant in variants:
        model = f"jev_{variant}"
        summary = run_forecast.summarise(predictions[predictions["model"] == model], config, levels)
        gains, versus_curve = run_forecast._paired_gain(
            predictions, REFERENCE, "abs_error", config, model=model
        )
        _, versus_full = run_forecast._paired_gain(
            predictions, "jev_full", "abs_error", config, model=model
        )
        blocks[variant] = {
            **summary,
            "description": settings["ablation"]["variants"].get(variant, "the first run itself"),
            "campaigns_better_than_curve": int((gains > 0).sum()),
            "paired_mae_gain_vs_curve_pp": versus_curve,
            "paired_mae_change_vs_full_pp": versus_full,
        }
    curve = run_forecast.summarise(predictions[predictions["model"] == REFERENCE], config, levels)

    full_gains, _ = run_forecast._paired_gain(
        predictions, REFERENCE, "abs_error", config, model="jev_full"
    )
    probe = _probe(config, resolved, answer)

    dataset_path = REPO_ROOT / config["dataset"]["path"]
    return {
        "arm": arm,
        "variants": blocks,
        "reference": {REFERENCE: curve},
        "recognition": _recognition_summary(probe, full_gains, config),
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
    }


def write(result: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "forecast_ablation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )

    rows = []
    for name, block in [*result["variants"].items(), *result["reference"].items()]:
        row = {
            "variant": name,
            "rows": block["rows"],
            "folds": block["folds"],
            "mae_pp": round(block["mae"], 3),
            "mae_ci95_low": round(block["mae_ci95"]["low"], 3),
            "mae_ci95_high": round(block["mae_ci95"]["high"], 3),
            "crps_pp": round(block["crps"], 3),
            "coverage_80": round(block["coverage_80"], 3),
            "width_80_pp": round(block["width_80"], 2),
        }
        for key in ("paired_mae_gain_vs_curve_pp", "paired_mae_change_vs_full_pp"):
            if key in block:
                row[key] = round(block[key]["point"], 3)
                row[f"{key}_low"] = round(block[key]["low"], 3)
                row[f"{key}_high"] = round(block[key]["high"], 3)
        if "campaigns_better_than_curve" in block:
            row["campaigns_better_than_curve"] = block["campaigns_better_than_curve"]
        rows.append(row)
    pd.DataFrame(rows).to_csv(directory / "forecast_ablation.csv", index=False)

    probe = pd.DataFrame(
        [{"cohort": cohort, **values} for cohort, values in result["recognition"]["campaigns"].items()]
    ).sort_values("paired_mae_gain_pp", ascending=False)
    probe.round(4).to_csv(directory / "forecast_recognition.csv", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="cached answers only")
    args = parser.parse_args()

    result = run(offline=args.offline)
    write(result, REPO_ROOT / "results")

    provenance = result["provenance"]
    print(f"{provenance['cache_hits']} answers from cache, {provenance['api_calls']} API calls\n")
    print(f"{'variant':<22}{'MAE':>7}{'gain vs curve':>24}{'change vs full':>24}")
    for name, block in result["variants"].items():
        gain, change = block["paired_mae_gain_vs_curve_pp"], block["paired_mae_change_vs_full_pp"]
        print(
            f"{name:<22}{block['mae']:>7.2f}"
            f"{gain['point']:>+8.2f} ({gain['low']:+.2f} to {gain['high']:+.2f})"
            f"{change['point']:>+8.2f} ({change['low']:+.2f} to {change['high']:+.2f})"
        )
    print(f"{'duration_curve':<22}{result['reference'][REFERENCE]['mae']:>7.2f}")

    probe = result["recognition"]
    link = probe["spearman_with_gain"]
    print(
        f"\nrecognition: mean probability on the true campaign {probe['mean_p_true']:.2f} "
        f"(chance {probe['chance']:.2f}), top-1 {probe['top1_accuracy']:.0%}; "
        f"Spearman with gain rho={link['rho']} p={link['p']} n={link['n']}"
    )
    for cohort, values in sorted(
        probe["campaigns"].items(), key=lambda item: -item[1]["paired_mae_gain_pp"]
    ):
        print(
            f"  {cohort:<18} gain {values['paired_mae_gain_pp']:+.2f}  p(true) "
            f"{values['mean_p_true']:.2f}  top-1 {values['top1']:.0%}  top choice {values['top_choice']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
