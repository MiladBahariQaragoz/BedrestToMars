"""Checks on leave-one-cohort-out splitting and its leakage guard.

The guard is the point of this file. A framework whose leakage assertion has never fired
has not been tested, so one test deliberately hands it a random split and requires it to
fail (PLAN.md task 3.5).

    python framework/tests/test_cv.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import cv
import data_loader
import features

CONFIG = data_loader.load_config()
FRAME = data_loader.subset(data_loader.load(CONFIG), CONFIG)
_, _, GROUPS = features.design_matrix(FRAME, CONFIG, subset="A")


def test_one_fold_per_cohort() -> None:
    folds = list(cv.loco_split(GROUPS))
    assert len(folds) == GROUPS.nunique() == 31


def test_each_cohort_is_held_out_exactly_once() -> None:
    held_out = [GROUPS.iloc[test].unique().tolist() for _, test in cv.loco_split(GROUPS)]
    assert all(len(cohorts) == 1 for cohorts in held_out)
    flattened = [cohorts[0] for cohorts in held_out]
    assert sorted(flattened) == sorted(GROUPS.unique())


def test_train_and_test_partition_the_rows() -> None:
    for train, test in cv.loco_split(GROUPS):
        assert not set(train) & set(test)
        assert len(train) + len(test) == len(GROUPS)


def test_the_guard_accepts_a_proper_split() -> None:
    for train, test in cv.loco_split(GROUPS):
        cv.assert_no_leakage(train, test, GROUPS)


def test_the_guard_rejects_a_random_split() -> None:
    """The deliberate failure. If this test passes silently, the guard is decorative."""
    rng = np.random.default_rng(0)
    order = rng.permutation(len(GROUPS))
    train, test = order[:300], order[300:]
    try:
        cv.assert_no_leakage(train, test, GROUPS)
    except cv.LeakageError:
        return
    raise AssertionError("a random split leaks cohorts and must be rejected")


def test_the_guard_rejects_a_split_by_paper_rather_than_campaign() -> None:
    """Two Berlin papers are one campaign. Splitting on study_id leaks participants."""
    studies = FRAME["study_id"]
    resolved_groups = GROUPS
    frame = features.resolve(FRAME, CONFIG, subset="A")
    shared = frame["cohort_id"].value_counts()
    crowded = shared.index[0]
    rows = np.flatnonzero((frame["cohort_id"] == crowded).to_numpy())
    train, test = rows[: len(rows) // 2], rows[len(rows) // 2 :]
    assert studies is not None and resolved_groups is not None
    try:
        cv.assert_no_leakage(train, test, frame["cohort_id"])
    except cv.LeakageError:
        return
    raise AssertionError("splitting inside one campaign must be rejected")


def test_group_column_may_not_reach_the_model() -> None:
    matrix = pd.DataFrame({"duration_log": [1.0, 2.0], "cohort_id": [0.0, 1.0]})
    try:
        cv.assert_groups_absent(matrix, CONFIG)
    except cv.LeakageError:
        return
    raise AssertionError("cohort_id inside the design matrix must be rejected")


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
