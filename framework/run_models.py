"""Tier 2: the four comparative families, scored against the duration-only curve.

This is `PLAN.md` tasks 4.1 to 4.4. Every model is fitted inside a leave-one-cohort-out
loop, its hyperparameters chosen by a grouped search *within* the training fold, and its
error compared with the baseline from `run_baseline.py`. Under `PLAN.md` section 8 a model
earns a place in the talk by beating that baseline by 15% or more, and the honest outcome at
31 campaigns may well be that none of them does.

    python framework/run_models.py        # writes results/model_comparison.{csv,json}
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import cv
import data_loader
import evaluate
import explain
import features
import models
import run_baseline

REPO_ROOT = Path(__file__).resolve().parent.parent
IMPROVEMENT_THRESHOLD = 0.15


class FixedSearch:
    """An estimator with fixed declared defaults, wearing the interface of a search.

    `run_family` asks the returned object for `fit`, `predict` and `best_params_`. A family
    whose settings are fixed by declaration rather than tuned in-fold (the prior-fitted
    network has nothing to search) needs that interface without the search, so the fold loop
    and the chosen-parameters record stay identical for every family.
    """

    def __init__(self, estimator: Any) -> None:
        self.estimator = estimator
        self.best_params_: dict[str, Any] = {}

    def fit(self, design: np.ndarray, target: np.ndarray, groups: Any = None) -> "FixedSearch":
        self.estimator.fit(design, target)
        return self

    def predict(self, design: np.ndarray) -> np.ndarray:
        return self.estimator.predict(design)


def build_search(family: str, config: dict[str, Any]):
    """An estimator wrapped in a grouped search over the declared grid.

    The search splits the *training* fold by campaign, so a hyperparameter is never chosen
    with help from the campaign it will be scored on, and never chosen with help from the
    same participants appearing under another paper's name.
    """
    if family == "tabpfn":
        # Fixed declared defaults (`DESIGN.md`: nested tuning *or* fixed defaults). A
        # prior-fitted network is used in-context; there is no grid to search, and tuning
        # its few knobs against these 31 campaigns would only add a way to overfit.
        return FixedSearch(models.build(family, config)())

    from sklearn.model_selection import GridSearchCV, GroupKFold

    estimator = models.build(family, config)()
    grid = config["models"]["grids"][family]
    prefix = {
        "ridge": "ridgecv__",
        "svr": "svr__",
        "random_forest": "",
        "gradient_boosting": "",
    }[family]
    if family == "ridge":
        # RidgeCV picks its own penalty; the declared grid is applied to a plain Ridge so the
        # choice is visible in chosen_parameters rather than hidden inside the estimator.
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        estimator = make_pipeline(StandardScaler(), Ridge())
        prefix = "ridge__"

    param_grid = {f"{prefix}{name}": values for name, values in grid.items()}
    return GridSearchCV(
        estimator,
        param_grid,
        cv=GroupKFold(n_splits=int(config["models"]["inner_folds"])),
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
        refit=True,
    )


def run_family(
    family: str, frame: pd.DataFrame, config: dict[str, Any], subset: str = "A"
) -> dict[str, Any]:
    """Leave-one-cohort-out for one model family, with nested tuning inside each fold."""
    matrix, target, groups = features.design_matrix(frame, config, subset=subset)
    cv.assert_groups_absent(matrix, config)

    design = matrix.to_numpy(dtype=float)
    values = target.to_numpy(dtype=float)
    out_of_fold = np.full(len(values), np.nan, dtype=float)

    folds: list[dict[str, Any]] = []
    chosen: list[dict[str, Any]] = []
    for fold, (train, test) in enumerate(cv.loco_split(groups)):
        cv.assert_no_leakage(train, test, groups)
        search = build_search(family, config)
        search.fit(design[train], values[train], groups=groups.iloc[train])
        out_of_fold[test] = search.predict(design[test])
        scores = evaluate.metrics(values[test], out_of_fold[test])
        folds.append(
            {
                "fold": fold,
                "held_out_cohort": groups.iloc[test[0]],
                "n_test": len(test),
                **scores,
            }
        )
        chosen.append({"fold": fold, **search.best_params_})

    fold_frame = pd.DataFrame(folds)
    aggregated = evaluate.aggregate(fold_frame, weight_by=config["evaluate"]["weight_by"])
    interval = evaluate.bootstrap_ci(fold_frame, config, metric="mae")
    return {
        "model": family,
        "subset": subset,
        "n_rows": int(len(values)),
        "n_cohorts": int(groups.nunique()),
        "folds": folds,
        "chosen_parameters": chosen,
        "mae": aggregated["mae"],
        "rmse": aggregated["rmse"],
        "mae_row_weighted": evaluate.aggregate(fold_frame, weight_by="row")["mae"],
        "r2_pooled": evaluate.metrics(values, out_of_fold)["r2"],
        "ci95": {"low": interval["low"], "high": interval["high"]},
        "worst_fold": {
            "cohort": fold_frame.loc[fold_frame["mae"].idxmax(), "held_out_cohort"],
            "mae": float(fold_frame["mae"].max()),
        },
    }


def compare(
    family: str,
    frame: pd.DataFrame,
    config: dict[str, Any],
    subset: str = "A",
    baseline_mae: float | None = None,
) -> dict[str, Any]:
    """One family against the duration-only curve, on the rule agreed before fitting."""
    result = run_family(family, frame, config, subset=subset)
    if baseline_mae is None:
        baseline = run_baseline.run(config, subset=subset)
        baseline_mae = baseline["forms"][baseline["best_form_by_out_of_cohort_mae"]]["mae"]
    improvement = (baseline_mae - result["mae"]) / baseline_mae
    return {
        **result,
        "baseline_mae": float(baseline_mae),
        "relative_improvement": float(improvement),
        "threshold": IMPROVEMENT_THRESHOLD,
        "beats_baseline": bool(improvement >= IMPROVEMENT_THRESHOLD),
    }


def stability(
    best_family: str, frame: pd.DataFrame, config: dict[str, Any], subset: str = "A"
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Feature importance recomputed in every fold, reported as a stability table."""
    matrix, target, groups = features.design_matrix(frame, config, subset=subset)
    design = matrix.to_numpy(dtype=float)
    values = target.to_numpy(dtype=float)
    factory = models.build(best_family, config)
    return explain.explain_folds(
        factory,
        design,
        values,
        list(cv.loco_split(groups)),
        list(matrix.columns),
        config,
    )


def run(config: dict[str, Any] | None = None, subset: str = "A") -> dict[str, Any]:
    """Every available family, compared with the baseline, plus the stability table."""
    config = config or data_loader.load_config()
    frame = data_loader.subset(data_loader.load(config), config)

    baseline = run_baseline.run(config, subset=subset)
    best_form = baseline["best_form_by_out_of_cohort_mae"]
    baseline_mae = baseline["forms"][best_form]["mae"]

    families = [name for name in config["models"]["families"] if name in models.available(config)]
    comparisons = {
        family: compare(family, frame, config, subset=subset, baseline_mae=baseline_mae)
        for family in families
    }

    ranked = sorted(comparisons.values(), key=lambda entry: entry["mae"])
    best_family = ranked[0]["model"] if ranked else None
    stability_table, method = (
        stability(best_family, frame, config, subset=subset)
        if best_family
        else (pd.DataFrame(), {})
    )

    return {
        "baseline": {"form": best_form, "mae": baseline_mae},
        "models": comparisons,
        "best_model": best_family,
        "any_model_beats_baseline": any(
            entry["beats_baseline"] for entry in comparisons.values()
        ),
        "importance": {
            "method": method,
            "stability": stability_table.to_dict("records"),
        },
        "provenance": {
            **baseline["provenance"],
            "sklearn": __import__("sklearn").__version__,
            "tabpfn": __import__("tabpfn").__version__ if models.tabpfn_available() else "absent",
            "python": platform.python_version(),
        },
    }


def write(result: dict[str, Any], results_dir: Path) -> None:
    """Write the comparison table for the report and the full record as JSON."""
    results_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "model": entry["model"],
            "loco_mae_pp": round(entry["mae"], 3),
            "ci95_low": round(entry["ci95"]["low"], 3),
            "ci95_high": round(entry["ci95"]["high"], 3),
            "rmse_pp": round(entry["rmse"], 3),
            "r2_pooled": round(entry["r2_pooled"], 3),
            "vs_baseline_relative": round(entry["relative_improvement"], 3),
            "beats_baseline_by_15pct": entry["beats_baseline"],
            "worst_fold_cohort": entry["worst_fold"]["cohort"],
            "worst_fold_mae_pp": round(entry["worst_fold"]["mae"], 3),
        }
        for entry in sorted(result["models"].values(), key=lambda entry: entry["mae"])
    ]
    baseline_row = {
        "model": f"duration_only ({result['baseline']['form']})",
        "loco_mae_pp": round(result["baseline"]["mae"], 3),
        "ci95_low": "",
        "ci95_high": "",
        "rmse_pp": "",
        "r2_pooled": "",
        "vs_baseline_relative": 0.0,
        "beats_baseline_by_15pct": "",
        "worst_fold_cohort": "",
        "worst_fold_mae_pp": "",
    }
    pd.DataFrame([baseline_row, *rows]).to_csv(
        results_dir / "model_comparison.csv", index=False
    )
    (results_dir / "model_comparison.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    pd.DataFrame(result["importance"]["stability"]).to_csv(
        results_dir / "importance_stability.csv", index=False
    )


def main() -> int:
    config = data_loader.load_config()
    result = run(config)
    write(result, REPO_ROOT / "results")

    print(f"baseline: duration-only ({result['baseline']['form']}) "
          f"{result['baseline']['mae']:.2f} pp\n")
    print(f"{'model':<20}{'LOCO MAE':>10}{'95% CI':>18}{'vs baseline':>14}{'pooled R²':>12}")
    for entry in sorted(result["models"].values(), key=lambda item: item["mae"]):
        interval = f"{entry['ci95']['low']:.2f} to {entry['ci95']['high']:.2f}"
        print(
            f"{entry['model']:<20}{entry['mae']:>10.2f}{interval:>18}"
            f"{entry['relative_improvement']:>13.1%}{entry['r2_pooled']:>12.2f}"
        )
    verdict = (
        "at least one family beats the duration curve by 15% or more"
        if result["any_model_beats_baseline"]
        else "no family beats the duration curve by the 15% agreed in PLAN.md section 8"
    )
    print(f"\n{verdict}")
    method = result["importance"]["method"]
    print(f"importance method: {method.get('used')} ({method.get('note') or 'as requested'})")
    for row in result["importance"]["stability"][:5]:
        print(f"  {row['feature']:<34} top-3 in {row['share']:.0%} of folds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
