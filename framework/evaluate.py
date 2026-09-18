"""Run the fold loop, score it, and put an interval on the score.

Two rules from `DESIGN.md` section 8.3 are enforced here rather than left to whoever reads
the table. Metrics are reported per fold, because a model that is excellent on 28 campaigns
and hopeless on 3 is not a good model and a single average hides that. And the headline
number is weighted by campaign, not by row, so the one campaign contributing a quarter of
the rows does not quietly become a quarter of the result.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

import cv
import features
import models

METRICS = ("mae", "rmse", "r2")


def metrics(truth: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Mean absolute error and RMSE in percentage points, plus R²."""
    truth = np.asarray(truth, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    residual = truth - predicted
    total = float(np.sum((truth - truth.mean()) ** 2))
    return {
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "r2": float(1.0 - np.sum(residual**2) / total) if total > 0 else float("nan"),
    }


class _InterceptOnly:
    """Predict the training mean. The floor every other model has to clear."""

    def __init__(self) -> None:
        self.value = 0.0

    def fit(self, days: np.ndarray, target: np.ndarray, weights: np.ndarray | None = None):
        target = np.asarray(target, dtype=float)
        if weights is None:
            self.value = float(target.mean())
        else:
            weights = np.asarray(weights, dtype=float)
            self.value = float(np.sum(weights * target) / np.sum(weights))
        return self

    def predict(self, days: np.ndarray) -> np.ndarray:
        return np.full(len(np.asarray(days)), self.value, dtype=float)


def runnable(config: dict[str, Any]) -> list[str]:
    """Estimators that can actually be run on this machine."""
    return ["intercept_only", *models.available(config)]


def _factory(name: str, config: dict[str, Any]):
    if name == "intercept_only":
        return _InterceptOnly
    return models.build(name, config)


def run_loco(
    model_name: str,
    frame: pd.DataFrame,
    config: dict[str, Any],
    subset: str = "A",
) -> pd.DataFrame:
    """Fit and score one estimator with one campaign held out at a time.

    Everything the estimator sees is fitted inside the fold. The leakage guard runs on every
    fold rather than once at the start.
    """
    duration_only = model_name in {"duration_only", "intercept_only"}
    matrix, target, groups = features.design_matrix(frame, config, subset=subset)
    cv.assert_groups_absent(matrix, config)

    resolved = features.resolve(frame, config, subset=subset)
    weights = features.weights(resolved, config).to_numpy(dtype=float)
    days = resolved["duration_days"].to_numpy(dtype=float)
    values = target.to_numpy(dtype=float)
    design = matrix.to_numpy(dtype=float)
    factory = _factory(model_name, config)

    rows: list[dict[str, Any]] = []
    for fold, (train, test) in enumerate(cv.loco_split(groups)):
        if config["cv"].get("assert_no_leakage", True):
            cv.assert_no_leakage(train, test, groups)

        model = factory()
        if duration_only:
            model.fit(days[train], values[train], weights[train])
            predicted = model.predict(days[test])
        else:
            model.fit(design[train], values[train])
            predicted = model.predict(design[test])

        scores = metrics(values[test], predicted)
        rows.append(
            {
                "fold": fold,
                "model": model_name,
                "held_out_cohort": groups.iloc[test[0]],
                "n_test": len(test),
                "n_train": len(train),
                "tau": getattr(model, "tau", None),
                **scores,
            }
        )
    return pd.DataFrame(rows)


def out_of_fold_predictions(
    model_name: str,
    frame: pd.DataFrame,
    config: dict[str, Any],
    subset: str = "A",
) -> tuple[np.ndarray, np.ndarray, pd.Series]:
    """Every row's prediction from the fold in which it was held out.

    Per-fold R² is not a usable metric for this corpus: most campaigns ran a single
    duration, so a duration-only model predicts one value across the whole held-out fold and
    scores worse than that fold's own mean by construction. Pooling the out-of-fold
    predictions and computing R² once is the honest version of the same question, and it is
    what `results/` reports alongside MAE.
    """
    duration_only = model_name in {"duration_only", "intercept_only"}
    matrix, target, groups = features.design_matrix(frame, config, subset=subset)
    cv.assert_groups_absent(matrix, config)

    resolved = features.resolve(frame, config, subset=subset)
    weights = features.weights(resolved, config).to_numpy(dtype=float)
    days = resolved["duration_days"].to_numpy(dtype=float)
    values = target.to_numpy(dtype=float)
    design = matrix.to_numpy(dtype=float)
    factory = _factory(model_name, config)

    predicted = np.full(len(values), np.nan, dtype=float)
    for train, test in cv.loco_split(groups):
        if config["cv"].get("assert_no_leakage", True):
            cv.assert_no_leakage(train, test, groups)
        model = factory()
        if duration_only:
            model.fit(days[train], values[train], weights[train])
            predicted[test] = model.predict(days[test])
        else:
            model.fit(design[train], values[train])
            predicted[test] = model.predict(design[test])
    return values, predicted, groups


def aggregate(folds: pd.DataFrame, weight_by: str = "cohort") -> dict[str, float]:
    """Collapse the per-fold table to one number per metric.

    `cohort` gives every campaign one vote. `row` weights by how many rows the campaign
    happens to contribute, which is how a 300-row campaign takes over a slide.
    """
    present = [metric for metric in METRICS if metric in folds.columns]
    if weight_by == "cohort":
        return {metric: float(np.nanmean(folds[metric])) for metric in present}
    if weight_by == "row":
        weights = folds["n_test"].to_numpy(dtype=float)
        collapsed: dict[str, float] = {}
        for metric in present:
            values = folds[metric].to_numpy(dtype=float)
            mask = np.isfinite(values)
            collapsed[metric] = float(
                np.sum(weights[mask] * values[mask]) / np.sum(weights[mask])
            )
        return collapsed
    raise ValueError(f"unknown weighting: {weight_by}")


def bootstrap_ci(
    folds: pd.DataFrame,
    config: dict[str, Any],
    metric: str = "mae",
    replicates: int | None = None,
    level: float = 0.95,
) -> dict[str, float]:
    """Resample campaigns, not rows: the interval has to match the dependence structure."""
    replicates = replicates or int(config["evaluate"]["bootstrap"]["replicates"])
    rng = np.random.default_rng(int(config["seed"]))
    values = folds[metric].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    draws = np.array(
        [
            np.mean(rng.choice(values, size=len(values), replace=True))
            for _ in range(replicates)
        ]
    )
    tail = (1.0 - level) / 2.0
    return {
        "point": float(np.mean(values)),
        "low": float(np.quantile(draws, tail)),
        "high": float(np.quantile(draws, 1.0 - tail)),
        "replicates": replicates,
    }


def compare_with_baseline(
    folds: pd.DataFrame, baseline_folds: pd.DataFrame, metric: str = "mae"
) -> dict[str, float]:
    """Relative improvement over the duration-only curve, per `PLAN.md` section 8."""
    model_score = aggregate(folds)[metric]
    baseline_score = aggregate(baseline_folds)[metric]
    return {
        "model": model_score,
        "baseline": baseline_score,
        "relative_improvement": float(
            (baseline_score - model_score) / baseline_score
        ),
    }
