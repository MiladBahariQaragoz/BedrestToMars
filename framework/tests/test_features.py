"""Checks on the subset resolution and the design matrix.

    python framework/tests/test_features.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import features

CONFIG = data_loader.load_config()
FRAME = data_loader.subset(data_loader.load(CONFIG), CONFIG)


def test_subset_a_keeps_every_campaign() -> None:
    subset_a = features.resolve(FRAME, CONFIG, subset="A")
    assert len(subset_a) == 342
    assert subset_a["cohort_id"].nunique() == 31


def test_subset_b_drops_whole_segment_rows_and_the_campaigns_that_only_have_them() -> None:
    subset_b = features.resolve(FRAME, CONFIG, subset="B")
    assert len(subset_b) == 304
    assert subset_b["cohort_id"].nunique() == 25
    assert not subset_b["muscle"].isin(CONFIG["subset"]["whole_segment_muscles"]).any()


def test_a_composite_is_dropped_when_its_components_are_present() -> None:
    """Schema rule 4: the same tissue never enters twice."""
    subset_a = features.resolve(FRAME, CONFIG, subset="A")
    occasion = ["cohort_id", "arm_id", "timepoint_days", "modality", "outcome_type"]
    for _, group in subset_a.groupby(occasion, dropna=False):
        whole = CONFIG["subset"]["whole_segment_muscles"]
        named = group[~group["muscle"].isin(whole)]
        has_components = (named["is_composite"] == "FALSE").any()
        has_composites = (named["is_composite"] == "TRUE").any()
        assert not (has_components and has_composites), group["row_id"].tolist()


def test_whole_segment_rows_survive_in_subset_a() -> None:
    subset_a = features.resolve(FRAME, CONFIG, subset="A")
    whole = subset_a[subset_a["muscle"].isin(CONFIG["subset"]["whole_segment_muscles"])]
    assert len(whole) == 38
    assert (whole["muscle_family"] == "whole_limb").all()


def test_log_duration_basis() -> None:
    days = np.array([7.0, 60.0])
    assert np.allclose(features.duration_basis(days, form="log"), np.log(days))


def test_saturating_basis_is_bounded_and_monotone() -> None:
    days = np.array([0.0, 7.0, 30.0, 120.0])
    values = features.duration_basis(days, form="saturating", tau=21.0)
    assert values[0] == 0.0
    assert np.all(np.diff(values) > 0)
    assert np.all(values < 1.0)


def test_design_matrix_has_no_missing_values_and_no_provenance() -> None:
    matrix, target, groups = features.design_matrix(FRAME, CONFIG, subset="A")
    assert len(matrix) == len(target) == len(groups) == 342
    assert not matrix.isna().any().any()
    for column in CONFIG["features"]["never_model"]:
        assert column not in matrix.columns
    assert np.issubdtype(matrix.to_numpy().dtype, np.number)


def test_design_matrix_carries_the_duration_and_the_muscle_families() -> None:
    matrix, _, _ = features.design_matrix(FRAME, CONFIG, subset="A")
    assert any(name.startswith("duration_") for name in matrix.columns)
    assert any(name.startswith("muscle_family_") for name in matrix.columns)


def test_groups_are_the_cohorts() -> None:
    _, _, groups = features.design_matrix(FRAME, CONFIG, subset="A")
    assert groups.nunique() == 31


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
