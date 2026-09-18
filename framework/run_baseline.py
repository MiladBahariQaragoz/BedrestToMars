"""Fit the duration-only baseline in all three forms and write the result.

This is `PLAN.md` task 3.4 and, under `DESIGN.md` section 9, it is also the reference every
tier-2 model is measured against. It is deliberately the first thing in the project that
produces a number, because everything later is a comparison with it.

    python framework/run_baseline.py            # writes results/baseline.json
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import cv
import data_loader
import evaluate
import features
import models

REPO_ROOT = Path(__file__).resolve().parent.parent
FORMS = ("linear", "log", "saturating")


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    return result.stdout.strip()


def _fit_one_form(
    form: str,
    days: np.ndarray,
    values: np.ndarray,
    weights: np.ndarray,
    groups: pd.Series,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Score one curve shape out of cohort, then refit it on everything for reporting."""
    grid = config["features"]["saturating_tau_grid"]
    rows: list[dict[str, Any]] = []
    out_of_fold = np.full(len(values), np.nan, dtype=float)
    for fold, (train, test) in enumerate(cv.loco_split(groups)):
        cv.assert_no_leakage(train, test, groups)
        model = models.DurationOnlyBaseline(form=form, tau_grid=grid)
        model.fit(days[train], values[train], weights[train])
        out_of_fold[test] = model.predict(days[test])
        scores = evaluate.metrics(values[test], out_of_fold[test])
        rows.append(
            {
                "fold": fold,
                "held_out_cohort": groups.iloc[test[0]],
                "n_test": len(test),
                "tau": model.tau,
                **scores,
            }
        )
    folds = pd.DataFrame(rows)
    aggregated = evaluate.aggregate(folds, weight_by=config["evaluate"]["weight_by"])
    interval = evaluate.bootstrap_ci(folds, config, metric="mae")

    full = models.DurationOnlyBaseline(form=form, tau_grid=grid).fit(days, values, weights)
    summary: dict[str, Any] = {
        "folds": len(folds),
        "mae": aggregated["mae"],
        "rmse": aggregated["rmse"],
        "r2": aggregated["r2"],
        "mae_row_weighted": evaluate.aggregate(folds, weight_by="row")["mae"],
        "r2_pooled": evaluate.metrics(values, out_of_fold)["r2"],
        "ci95": {"low": interval["low"], "high": interval["high"]},
        "worst_fold": {
            "cohort": folds.loc[folds["mae"].idxmax(), "held_out_cohort"],
            "mae": float(folds["mae"].max()),
        },
        "coefficients": [float(value) for value in np.atleast_1d(full.coefficients)],
    }
    if form == "saturating":
        summary["tau_days"] = float(full.tau or float("nan"))
        summary["asymptote_pct"] = float(full.asymptote or float("nan"))
        summary["predicted_pct"] = {
            str(day): float(full.predict(np.array([day]))[0])
            for day in (14, 30, 60, 90, 119)
        }
    else:
        summary["predicted_pct"] = {
            str(day): float(full.predict(np.array([day]))[0])
            for day in (14, 30, 60, 90, 119)
        }
    return summary


def run(config: dict[str, Any] | None = None, subset: str = "A") -> dict[str, Any]:
    """Fit and score the baseline in every form. Returns the result as plain data."""
    config = config or data_loader.load_config()
    frame = data_loader.subset(data_loader.load(config), config)
    resolved = features.resolve(frame, config, subset=subset)

    days = resolved["duration_days"].to_numpy(dtype=float)
    values = resolved[config["target"]["column"]].to_numpy(dtype=float)
    weights = features.weights(resolved, config).to_numpy(dtype=float)
    groups = resolved[config["cv"]["group_column"]]

    dataset_path = REPO_ROOT / config["dataset"]["path"]
    result = {
        "forms": {
            form: _fit_one_form(form, days, values, weights, groups, config)
            for form in FORMS
        },
        "provenance": {
            "dataset_version": config["dataset"]["version"],
            "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "subset": subset,
            "rows": int(len(resolved)),
            "cohorts": int(groups.nunique()),
            "studies": int(resolved["study_id"].nunique()),
            "seed": int(config["seed"]),
            "weighted_by": config["evaluate"]["weight_by"],
            "git_commit": _git_commit(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    best = min(result["forms"], key=lambda form: result["forms"][form]["mae"])
    result["best_form_by_out_of_cohort_mae"] = best
    return result


def write(result: dict[str, Any], path: Path) -> None:
    """Write the result as formatted JSON, so a diff between runs is readable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    config = data_loader.load_config()
    result = run(config)
    write(result, REPO_ROOT / "results" / "baseline.json")

    provenance = result["provenance"]
    print(
        f"subset {provenance['subset']}: {provenance['rows']} rows, "
        f"{provenance['cohorts']} cohorts, {provenance['studies']} studies\n"
    )
    print(f"{'form':<12}{'LOCO MAE':>10}{'95% CI':>18}{'pooled R²':>12}")
    for form, scores in result["forms"].items():
        interval = f"{scores['ci95']['low']:.2f} to {scores['ci95']['high']:.2f}"
        print(
            f"{form:<12}{scores['mae']:>10.2f}{interval:>18}{scores['r2_pooled']:>12.2f}"
        )
    saturating = result["forms"]["saturating"]
    print(
        f"\nsaturating curve: tau {saturating['tau_days']:.0f} days, "
        f"eventual loss {saturating['asymptote_pct']:.1f}%"
    )
    print(f"best form by out-of-cohort MAE: {result['best_form_by_out_of_cohort_mae']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
