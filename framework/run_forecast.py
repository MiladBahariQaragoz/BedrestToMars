"""Run the TypeSafe forecast in both arms and write the result.

`DESIGN.md` section 9.3. For every row, with its whole campaign held out, the model is shown
the participants, the protocol, the measurement and the other campaigns' data, and gives a
probability for each declared range. The baselines are given distributions of their own -
their point plus the residuals they made in training - so all of them are scored on the same
point error, intervals and proper scores.

    python framework/run_forecast.py            # calls TypeSafe for any answer not cached
    python framework/run_forecast.py --offline  # cached answers only; what `make all` runs

Writes `results/forecast.json`, `results/forecast_comparison.csv` and
`results/forecast_predictions.csv`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

import cv
import data_loader
import evaluate
import features
import forecast
import run_baseline
import typesafe_client

REPO_ROOT = Path(__file__).resolve().parent.parent
Answerer = Callable[[Sequence[dict[str, Any]]], list[dict[str, Any]]]


def _truth(row: pd.Series, arm: str, config: dict[str, Any]) -> float:
    value = float(row[config["target"]["column"]])
    return value if arm == "without_history" else value - float(row["prev_value"])


def fold_plan(
    config: dict[str, Any], resolved: pd.DataFrame, arm: str, variant: str = "full"
) -> list[dict[str, Any]]:
    """One entry per forecast: its state, question, truth and the baselines' distributions.

    `variant` selects an ablation (`DESIGN.md` section 9.3.2). Under `scrambled_reference`
    the model is shown the training rows with their values shuffled, and a curve fitted to
    those; the baselines keep the real curve, so the yardstick does not move.
    """
    if variant != "scrambled_reference" and variant not in forecast.VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    time = config["forecast"]["time_column"]
    target_column = config["target"]["column"]
    bins = forecast.arm_bins(config, arm)
    question = forecast.question(bins, arm)
    rows = resolved if arm == "without_history" else forecast.with_history(resolved, config)
    groups = resolved[config["cv"]["group_column"]]

    plan: list[dict[str, Any]] = []
    for fold, cohort in enumerate(pd.unique(rows["cohort_id"])):
        train = resolved[resolved["cohort_id"] != cohort]
        held_out = resolved[resolved["cohort_id"] == cohort]
        cv.assert_no_leakage(train.index.to_numpy(), held_out.index.to_numpy(), groups)

        curve = forecast.reference_curve(train, config)
        transitions = None
        if arm == "without_history":
            fitted = curve.predict(train[time].to_numpy(dtype=float))
            residuals = {"duration_curve": train[target_column].to_numpy(dtype=float) - fitted}
        else:
            transitions = forecast.with_history(train, config)
            change = (transitions[target_column] - transitions["prev_value"]).to_numpy(dtype=float)
            expected = curve.predict(transitions[time].to_numpy(dtype=float)) - curve.predict(
                transitions["prev_time"].to_numpy(dtype=float)
            )
            residuals = {"last_scan": change, "last_scan_plus_curve": change - expected}

        shown, shown_curve, shown_transitions, shown_variant = train, curve, transitions, variant
        if variant == "scrambled_reference":
            shown = forecast.scramble(train, seed=int(config["seed"]) + fold)
            shown_curve = forecast.reference_curve(shown, config)
            shown_transitions = (
                forecast.with_history(shown, config) if arm == "with_history" else None
            )
            shown_variant = "full"

        for index, row in rows[rows["cohort_id"] == cohort].iterrows():
            state, info = forecast.build_state(
                row, shown, held_out, arm, config, curve=shown_curve,
                train_transitions=shown_transitions, variant=shown_variant,
            )
            day = float(row[time])
            if arm == "without_history":
                centres = {"duration_curve": forecast.curve_at(curve, day)}
            else:
                step = forecast.curve_at(curve, day) - forecast.curve_at(curve, float(row["prev_time"]))
                centres = {"last_scan": 0.0, "last_scan_plus_curve": step}
            plan.append(
                {
                    "arm": arm,
                    "cohort": str(cohort),
                    "row_id": str(row.get("row_id", index)),
                    "day": day,
                    "truth": _truth(row, arm, config),
                    "state": state,
                    "questions": {"forecast": question},
                    "info": info,
                    "baselines": {
                        name: forecast.empirical_distribution(bins, centre, residuals[name])
                        for name, centre in centres.items()
                    },
                }
            )
    return plan


def _prediction_rows(
    plan: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    bins: forecast.Bins,
    levels: Sequence[float],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for entry, response in zip(plan, responses):
        answer = response["answers"]["forecast"]
        distributions = {
            "jev": forecast.probabilities_from_answer(bins, answer),
            **entry["baselines"],
        }
        for model, probs in distributions.items():
            record = {
                "arm": entry["arm"],
                "model": model,
                "cohort": entry["cohort"],
                "row_id": entry["row_id"],
                "day": entry["day"],
                "truth": entry["truth"],
                **forecast.score_row(bins, probs, entry["truth"], levels),
            }
            if model == "jev":
                record["confidence"] = float(answer.get("confidence", float("nan")))
                record["input_tokens"] = (response.get("usage") or {}).get("input_tokens")
                record["from_cache"] = bool(response.get("from_cache", False))
            rows.append(record)
    return pd.DataFrame(rows)


def _suffixes(levels: Sequence[float]) -> list[int]:
    return [int(round(level * 100)) for level in levels]


def _fold_table(predictions: pd.DataFrame, levels: Sequence[float]) -> pd.DataFrame:
    """One row per held-out campaign: the metrics averaged over that campaign's rows."""
    columns = {"mae": "abs_error", "crps": "crps", "log_score": "log_score"}
    for suffix in _suffixes(levels):
        columns[f"coverage_{suffix}"] = f"covered_{suffix}"
        columns[f"width_{suffix}"] = f"width_{suffix}"
    folds = predictions.groupby("cohort", sort=False).agg(
        n_test=("abs_error", "size"), **{name: (source, "mean") for name, source in columns.items()}
    )
    return folds.reset_index()


def summarise(
    predictions: pd.DataFrame, config: dict[str, Any], levels: Sequence[float]
) -> dict[str, Any]:
    """Every metric weighted by campaign, as the tier-2 table is, with campaign bootstrap CIs."""
    folds = _fold_table(predictions, levels)
    summary: dict[str, Any] = {"rows": int(len(predictions)), "folds": int(len(folds))}
    for column in folds.columns:
        if column in {"cohort", "n_test"}:
            continue
        summary[column] = float(folds[column].mean())
    for metric in ("mae", "crps"):
        interval = evaluate.bootstrap_ci(folds, config, metric=metric)
        summary[f"{metric}_ci95"] = {"low": interval["low"], "high": interval["high"]}
    r2 = evaluate.metrics(
        predictions["truth"].to_numpy(dtype=float), predictions["point"].to_numpy(dtype=float)
    )["r2"]
    summary["r2_pooled"] = r2 if np.isfinite(r2) else None
    worst = folds.loc[folds["mae"].idxmax()]
    summary["worst_fold"] = {"cohort": str(worst["cohort"]), "mae": float(worst["mae"])}
    if "confidence" in predictions and predictions["confidence"].notna().any():
        summary["mean_confidence"] = float(predictions["confidence"].mean())
    return summary


def _paired_gain(
    predictions: pd.DataFrame,
    reference: str,
    metric: str,
    config: dict[str, Any],
    model: str = "jev",
) -> tuple[pd.Series, dict[str, float]]:
    """The reference's error minus the model's, per campaign, with a campaign bootstrap.

    Two marginal intervals can overlap while the paired difference is clearly non-zero, or
    the reverse; the difference is the quantity a comparison claims, so it gets the interval.
    Positive means the model is better.
    """
    by_campaign = predictions.groupby(["cohort", "model"], sort=False)[metric].mean().unstack("model")
    gains = by_campaign[reference] - by_campaign[model]
    replicates = int(config["evaluate"]["bootstrap"]["replicates"])
    rng = np.random.default_rng(int(config["seed"]))
    values = gains.to_numpy(dtype=float)
    draws = np.array(
        [np.mean(rng.choice(values, size=len(values), replace=True)) for _ in range(replicates)]
    )
    interval = {
        "point": float(values.mean()),
        "low": float(np.quantile(draws, 0.025)),
        "high": float(np.quantile(draws, 0.975)),
    }
    return gains, interval


def _compare(
    models: dict[str, dict[str, Any]],
    reference: str,
    bar: float,
    predictions: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    jev, base = models["jev"], models[reference]
    mae_gains, mae_interval = _paired_gain(predictions, reference, "abs_error", config)
    crps_gains, crps_interval = _paired_gain(predictions, reference, "crps", config)
    mae_gain = (base["mae"] - jev["mae"]) / base["mae"]
    crps_gain = (base["crps"] - jev["crps"]) / base["crps"]
    return {
        "reference": reference,
        "bar": bar,
        "relative_mae_improvement": float(mae_gain),
        "relative_crps_improvement": float(crps_gain),
        "beats_bar_on_mae": bool(mae_gain >= bar),
        "beats_bar_on_crps": bool(crps_gain >= bar),
        "campaigns": int(len(mae_gains)),
        "campaigns_better_on_mae": int((mae_gains > 0).sum()),
        "campaigns_better_on_crps": int((crps_gains > 0).sum()),
        "paired_mae_gain_pp": mae_interval,
        "paired_crps_gain_pp": crps_interval,
    }


def _answerer(config: dict[str, Any], offline: bool) -> typesafe_client.CachedAnswerer:
    settings = config["forecast"]
    cache_dir = Path(settings["cache_dir"])
    if not cache_dir.is_absolute():
        cache_dir = REPO_ROOT / cache_dir
    client = None if offline else typesafe_client.client_from_config(config)
    return typesafe_client.CachedAnswerer(
        cache_dir, settings["model"], client=client, offline=offline,
        concurrency=int(settings["concurrency"]),
    )


def run(
    config: dict[str, Any] | None = None,
    answerer: Answerer | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    """Build every forecast, get the model's answers, score them and the baselines."""
    config = config or data_loader.load_config()
    settings = config["forecast"]
    levels = [float(level) for level in settings["interval_levels"]]
    frame = data_loader.subset(data_loader.load(config), config)
    resolved = features.resolve(frame, config, subset="A")

    plans = {arm: fold_plan(config, resolved, arm) for arm in settings["arms"]}
    answer = answerer or _answerer(config, offline)

    arms: dict[str, Any] = {}
    tables: list[pd.DataFrame] = []
    reported: set[str] = set()
    for arm, plan in plans.items():
        responses = answer([{"state": e["state"], "questions": e["questions"]} for e in plan])
        reported.update(str(response.get("model")) for response in responses)
        bins = forecast.arm_bins(config, arm)
        predictions = _prediction_rows(plan, responses, bins, levels)
        tables.append(predictions)

        models = {
            model: summarise(group, config, levels)
            for model, group in predictions.groupby("model", sort=False)
        }
        tokens = np.array([entry["info"]["estimated_tokens"] for entry in plan])
        jev_rows = predictions[predictions["model"] == "jev"]
        reported_tokens = pd.to_numeric(jev_rows["input_tokens"], errors="coerce").dropna()
        arms[arm] = {
            "target": settings["arms"][arm]["target"],
            "edges": list(bins.edges),
            "models": models,
            "comparison": _compare(
                models, settings["arms"][arm]["reference_baseline"],
                float(settings["relative_improvement_bar"]), predictions, config,
            ),
            "state_tokens_estimated": {"mean": float(tokens.mean()), "max": int(tokens.max())},
            "input_tokens_reported": {
                "total": int(reported_tokens.sum()),
                "max": int(reported_tokens.max()) if len(reported_tokens) else None,
            },
            "observations_kept_mean": float(
                np.mean([entry["info"]["observations_kept"] for entry in plan])
            ),
        }

    dataset_path = REPO_ROOT / config["dataset"]["path"]
    hits = getattr(answer, "hits", None)
    calls = getattr(answer, "calls", None)
    result = {
        "arms": arms,
        "provenance": {
            "model": settings["model"],
            "models_reported": sorted(reported),
            "endpoint": settings["endpoint"],
            "time_column": settings["time_column"],
            "dataset_version": config["dataset"]["version"],
            "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "subset": "A",
            "requests": int(sum(len(plan) for plan in plans.values())),
            "cache_hits": hits,
            "api_calls": calls,
            "seed": int(config["seed"]),
            "weighted_by": "cohort",
            "git_commit": run_baseline._git_commit(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    result["_predictions"] = pd.concat(tables, ignore_index=True)
    return result


def write(result: dict[str, Any], directory: Path) -> None:
    """The full result as JSON, one comparison table, and every row's forecast."""
    directory.mkdir(parents=True, exist_ok=True)
    body = {key: value for key, value in result.items() if key != "_predictions"}
    (directory / "forecast.json").write_text(
        json.dumps(body, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )

    rows = []
    for arm, block in result["arms"].items():
        comparison = block["comparison"]
        for model, summary in block["models"].items():
            rows.append(
                {
                    "arm": arm,
                    "model": model,
                    "rows": summary["rows"],
                    "folds": summary["folds"],
                    "mae_pp": round(summary["mae"], 3),
                    "mae_ci95_low": round(summary["mae_ci95"]["low"], 3),
                    "mae_ci95_high": round(summary["mae_ci95"]["high"], 3),
                    "crps_pp": round(summary["crps"], 3),
                    "log_score": round(summary["log_score"], 3),
                    "coverage_50": round(summary["coverage_50"], 3),
                    "width_50_pp": round(summary["width_50"], 2),
                    "coverage_80": round(summary["coverage_80"], 3),
                    "width_80_pp": round(summary["width_80"], 2),
                    "r2_pooled": None if summary["r2_pooled"] is None else round(summary["r2_pooled"], 3),
                    "is_reference": model == comparison["reference"],
                    "worst_fold_cohort": summary["worst_fold"]["cohort"],
                    "worst_fold_mae_pp": round(summary["worst_fold"]["mae"], 3),
                }
            )
    pd.DataFrame(rows).to_csv(directory / "forecast_comparison.csv", index=False)

    predictions = result["_predictions"].replace([np.inf, -np.inf], np.nan)
    predictions.round(4).to_csv(directory / "forecast_predictions.csv", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--offline", action="store_true",
        help="use cached answers only and fail on a miss, never calling the API",
    )
    args = parser.parse_args()

    result = run(offline=args.offline)
    write(result, REPO_ROOT / "results")

    provenance = result["provenance"]
    print(
        f"{provenance['requests']} forecasts, model {provenance['model']}, "
        f"{provenance['cache_hits']} from cache, {provenance['api_calls']} API calls\n"
    )
    for arm, block in result["arms"].items():
        print(f"{arm}  (target: {block['target']})")
        print(f"  {'model':<22}{'MAE':>7}{'95% CI':>15}{'CRPS':>7}{'cov80':>7}{'width80':>9}")
        for model, summary in block["models"].items():
            interval = f"{summary['mae_ci95']['low']:.2f}-{summary['mae_ci95']['high']:.2f}"
            print(
                f"  {model:<22}{summary['mae']:>7.2f}{interval:>15}{summary['crps']:>7.2f}"
                f"{summary['coverage_80']:>7.2f}{summary['width_80']:>9.1f}"
            )
        comparison = block["comparison"]
        print(
            f"  jev vs {comparison['reference']}: MAE {comparison['relative_mae_improvement']:+.1%}, "
            f"CRPS {comparison['relative_crps_improvement']:+.1%} "
            f"(bar {comparison['bar']:.0%}: {'met' if comparison['beats_bar_on_mae'] else 'not met'})"
        )
        paired = comparison["paired_mae_gain_pp"]
        print(
            f"  paired MAE gain {paired['point']:+.2f} pp (95% CI {paired['low']:+.2f} to "
            f"{paired['high']:+.2f}), better in {comparison['campaigns_better_on_mae']} of "
            f"{comparison['campaigns']} campaigns\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
