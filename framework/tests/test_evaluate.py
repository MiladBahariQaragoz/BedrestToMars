"""Checks on the metrics, the fold loop and the cohort bootstrap.

    python framework/tests/test_evaluate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import evaluate
import features
import models

CONFIG = data_loader.load_config()
FRAME = features.resolve(
    data_loader.subset(data_loader.load(CONFIG), CONFIG), CONFIG, subset="A"
)


def test_metrics_on_known_numbers() -> None:
    truth = np.array([-10.0, -20.0, -30.0])
    predicted = np.array([-12.0, -18.0, -33.0])
    scores = evaluate.metrics(truth, predicted)
    assert abs(scores["mae"] - (2 + 2 + 3) / 3) < 1e-12
    assert abs(scores["rmse"] - np.sqrt((4 + 4 + 9) / 3)) < 1e-12
    assert scores["r2"] < 1.0


def test_perfect_prediction_scores_perfectly() -> None:
    truth = np.array([-5.0, -15.0, -25.0])
    scores = evaluate.metrics(truth, truth)
    assert scores["mae"] == 0.0
    assert scores["r2"] == 1.0


def test_one_fold_per_campaign_with_finite_errors() -> None:
    folds = evaluate.run_loco("duration_only", FRAME, CONFIG, subset="A")
    assert len(folds) == 32
    assert np.isfinite(folds["mae"]).all()
    assert set(folds["held_out_cohort"]) == set(FRAME["cohort_id"])


def test_cohort_weighting_is_not_row_weighting() -> None:
    folds = pd.DataFrame(
        {
            "held_out_cohort": ["big", "small"],
            "n_test": [100, 2],
            "mae": [2.0, 20.0],
        }
    )
    by_cohort = evaluate.aggregate(folds, weight_by="cohort")["mae"]
    by_row = evaluate.aggregate(folds, weight_by="row")["mae"]
    assert abs(by_cohort - 11.0) < 1e-12
    assert by_row < by_cohort


def test_bootstrap_is_reproducible_and_brackets_the_estimate() -> None:
    folds = evaluate.run_loco("duration_only", FRAME, CONFIG, subset="A")
    first = evaluate.bootstrap_ci(folds, CONFIG, metric="mae", replicates=200)
    second = evaluate.bootstrap_ci(folds, CONFIG, metric="mae", replicates=200)
    assert first == second
    point = evaluate.aggregate(folds, weight_by="cohort")["mae"]
    assert first["low"] <= point <= first["high"]


def test_the_loop_refuses_a_design_matrix_carrying_the_cohort() -> None:
    import cv

    matrix = pd.DataFrame({"duration_log": [1.0, 2.0], "cohort_id": [0.0, 1.0]})
    try:
        cv.assert_groups_absent(matrix, CONFIG)
    except cv.LeakageError:
        return
    raise AssertionError("the loop must refuse a matrix that identifies the campaign")


def test_baseline_beats_predicting_the_mean() -> None:
    """A sanity floor: a duration curve should beat a flat line at the corpus mean."""
    folds = evaluate.run_loco("duration_only", FRAME, CONFIG, subset="A")
    curve = evaluate.aggregate(folds, weight_by="cohort")["mae"]
    flat = evaluate.aggregate(
        evaluate.run_loco("intercept_only", FRAME, CONFIG, subset="A"), weight_by="cohort"
    )["mae"]
    assert curve < flat


def test_pooled_r2_is_reported_because_per_fold_r2_cannot_work_here() -> None:
    """Most campaigns hold one duration, so a duration-only model predicts one value inside
    a fold and its per-fold R² is negative by construction. Pooling the out-of-fold
    predictions is the honest way to report explained variance."""
    truth, predicted, groups = evaluate.out_of_fold_predictions(
        "duration_only", FRAME, CONFIG, subset="A"
    )
    assert len(truth) == len(predicted) == len(groups) == 346
    pooled = evaluate.metrics(truth, predicted)
    per_fold = evaluate.aggregate(
        evaluate.run_loco("duration_only", FRAME, CONFIG, subset="A")
    )
    assert pooled["r2"] > per_fold["r2"]
    assert -1.0 < pooled["r2"] <= 1.0


def test_registry_reports_what_is_missing() -> None:
    reported = evaluate.runnable(CONFIG)
    assert "duration_only" in reported
    if not models.sklearn_available():
        assert "random_forest" not in reported


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
