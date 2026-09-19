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
    assert len(subset_a) == 346
    assert subset_a["cohort_id"].nunique() == 32


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
    assert len(whole) == 42
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
    assert len(matrix) == len(target) == len(groups) == 346
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
    assert groups.nunique() == 32


def test_spline_basis_is_two_columns_and_linear_in_its_first() -> None:
    """A restricted cubic spline with three knots spends two degrees of freedom."""
    days = np.array([5.0, 20.0, 60.0, 90.0, 119.0])
    basis = features.spline_basis(days, knots=(10.0, 45.0, 100.0))
    assert basis.shape == (5, 2)
    assert np.allclose(basis[:, 0], days)


def test_spline_basis_is_linear_beyond_the_outer_knots() -> None:
    """That restriction is the whole point of the form: the tails cannot run away."""
    knots = (10.0, 45.0, 100.0)
    beyond = np.array([100.0, 110.0, 120.0, 130.0])
    basis = features.spline_basis(beyond, knots=knots)
    second_differences = np.diff(basis[:, 1], n=2)
    assert np.allclose(second_differences, 0.0, atol=1e-8)


def test_spline_knots_come_from_the_declared_percentiles() -> None:
    days = FRAME["duration_days"].to_numpy(dtype=float)
    knots = features.spline_knots(days, CONFIG)
    assert len(knots) == 3
    assert list(knots) == sorted(knots)
    assert np.isclose(knots[1], np.percentile(days, 50))


def test_design_from_resolved_matches_the_full_design_matrix() -> None:
    """The two entry points must not drift apart: one is the other plus `resolve`."""
    resolved = features.resolve(FRAME, CONFIG, subset="A")
    matrix, _, _ = features.design_matrix(FRAME, CONFIG, subset="A")
    direct = features.design_from_resolved(resolved, CONFIG)
    assert list(direct.columns) == list(matrix.columns)
    assert np.allclose(direct.to_numpy(dtype=float), matrix.to_numpy(dtype=float))


def test_design_from_resolved_can_swap_the_duration_form() -> None:
    """Tier 1 fits three duration forms against one config, so the form is an argument."""
    resolved = features.resolve(FRAME, CONFIG, subset="A")
    logarithmic = features.design_from_resolved(resolved, CONFIG, form="log")
    spline = features.design_from_resolved(resolved, CONFIG, form="spline")
    assert "duration_log" in logarithmic.columns
    assert {"duration_spline_1", "duration_spline_2"} <= set(spline.columns)
    assert len(spline.columns) == len(logarithmic.columns) + 1


def test_the_reference_level_of_a_dummy_set_can_be_declared() -> None:
    """Which level is absorbed into the intercept is a choice, not the alphabet's business."""
    resolved = features.resolve(FRAME, CONFIG, subset="A")
    default = features.design_from_resolved(resolved, CONFIG)
    chosen = features.design_from_resolved(
        resolved, CONFIG, reference_levels={"muscle_family": "knee_extensors"}
    )
    assert "muscle_family_knee_extensors" not in chosen.columns
    assert "muscle_family_dorsiflexors" in chosen.columns
    assert "muscle_family_dorsiflexors" not in default.columns
    assert len(chosen.columns) == len(default.columns)


def test_an_unknown_reference_level_is_refused_rather_than_ignored() -> None:
    resolved = features.resolve(FRAME, CONFIG, subset="A")
    try:
        features.design_from_resolved(
            resolved, CONFIG, reference_levels={"muscle_family": "gluteus_maximus"}
        )
    except ValueError as error:
        assert "gluteus_maximus" in str(error)
        return
    raise AssertionError("a reference level that is not in the data must be refused")


def test_design_from_resolved_can_carry_an_intercept() -> None:
    resolved = features.resolve(FRAME, CONFIG, subset="A")
    with_intercept = features.design_from_resolved(resolved, CONFIG, intercept=True)
    assert with_intercept.columns[0] == "intercept"
    assert (with_intercept["intercept"] == 1.0).all()


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
