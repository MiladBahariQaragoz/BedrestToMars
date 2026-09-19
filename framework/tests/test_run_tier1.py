"""Checks on the tier-1 run and the two files it writes.

The fit itself is checked against known truth in `test_tier1.py`. What is checked here is
the run: that all three duration forms are reported, that the headline is chosen by the
rule declared before fitting rather than by whichever number came out best, and that the
two result files say enough for someone else to read them without the code.

    python framework/tests/test_run_tier1.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import run_tier1

CONFIG = data_loader.load_config()
RESULT = run_tier1.run(CONFIG)  # fitted once: the suite cannot afford it per test


def test_all_three_duration_forms_are_reported() -> None:
    assert set(RESULT["forms"]) == {"log", "saturating", "spline"}
    for form, fitted in RESULT["forms"].items():
        assert fitted["fixed_effects"], form
        assert fitted["variance_components"]["residual"] > 0.0, form
        assert fitted["aic"] == fitted["aic"], form  # not NaN


def test_the_headline_form_follows_the_declared_rule() -> None:
    """DESIGN.md section 7.1: saturating unless AIC beats it by more than the margin."""
    headline = RESULT["headline"]["form"]
    assert headline != "spline", "the spline is a diagnostic, never the headline curve"
    margin = CONFIG["tier1"]["aic_margin"]
    saturating = RESULT["forms"]["saturating"]["aic"]
    logarithmic = RESULT["forms"]["log"]["aic"]
    expected = "log" if logarithmic < saturating - margin else "saturating"
    assert headline == expected


def test_the_spline_is_reported_as_a_shape_check() -> None:
    check = RESULT["headline"]["spline_check"]
    assert "aic_delta_vs_headline" in check
    assert isinstance(check["shape_beyond_the_parametric_forms"], bool)


def test_every_coefficient_carries_an_interval_on_campaign_degrees_of_freedom() -> None:
    for form, fitted in RESULT["forms"].items():
        assert fitted["df"] == 30, form
        for effect in fitted["fixed_effects"]:
            assert effect["ci_low"] <= effect["estimate"] <= effect["ci_high"], effect
            assert effect["se"] > 0.0, effect


def test_the_saturating_form_reports_tau_and_an_asymptote_with_an_interval() -> None:
    """The two numbers a countermeasure planner asks for, and how sure we are of them."""
    saturating = RESULT["forms"]["saturating"]
    assert saturating["tau_days"] in CONFIG["features"]["saturating_tau_grid"]
    asymptote = saturating["asymptote_pct"]
    assert asymptote["estimate"] < 0.0
    assert asymptote["ci_low"] < asymptote["estimate"] < asymptote["ci_high"]


def test_a_tau_on_the_edge_of_the_grid_is_flagged() -> None:
    """A profile that stops at the edge of the grid has not found a plateau, it has run out
    of grid - and then the asymptote is an extrapolation wearing a confidence interval."""
    saturating = RESULT["forms"]["saturating"]
    grid = [float(value) for value in CONFIG["features"]["saturating_tau_grid"]]
    on_edge = saturating["tau_days"] >= max(grid)
    assert saturating["tau_at_grid_edge"] is on_edge
    if on_edge:
        assert "grid" in saturating["asymptote_pct"]["caveat"]


def test_the_curve_has_a_band_around_every_point() -> None:
    curve = RESULT["curve"]
    assert len(curve["days"]) == len(curve["fit"]) > 10
    for low, fit, high in zip(curve["ci_low"], curve["fit"], curve["ci_high"]):
        assert low < fit < high
    assert curve["days"][0] == 5 and curve["days"][-1] == 119


def test_the_curve_says_whose_curve_it_is() -> None:
    """A curve is drawn for one scenario; not naming it is how a slide misleads."""
    scenario = RESULT["curve"]["scenario"]
    assert scenario["arm_type"] == "control"
    assert scenario["muscle_family"] == RESULT["curve"]["scenario"]["muscle_family"]
    assert "reference" in scenario["meaning"]


def test_the_reference_family_is_the_declared_one_not_the_alphabet() -> None:
    """Every contrast inherits the reference's uncertainty, so the reference is a choice."""
    declared = CONFIG["tier1"]["reference_levels"]["muscle_family"]
    assert RESULT["curve"]["scenario"]["muscle_family"] == declared
    reference = [row for row in RESULT["muscle_ranking"] if row["is_reference"]]
    assert [row["muscle_family"] for row in reference] == [declared]


def test_the_declared_contrasts_are_reported_whatever_the_reference_is() -> None:
    """Antigravity against not-antigravity is the comparison the talk makes; it must not
    depend on which level happened to be absorbed into the intercept."""
    contrasts = RESULT["key_contrasts"]
    assert contrasts
    for contrast in contrasts:
        assert contrast["ci_low"] <= contrast["estimate"] <= contrast["ci_high"]
        assert 0.0 <= contrast["p"] <= 1.0
    pairs = {(contrast["left"], contrast["right"]) for contrast in contrasts}
    assert ("plantar_flexors", "dorsiflexors") in pairs


def test_the_ranking_covers_every_family_in_subset_b() -> None:
    ranking = RESULT["muscle_ranking"]
    families = {row["muscle_family"] for row in ranking}
    assert len(families) == len(ranking) > 4
    references = [row for row in ranking if row["is_reference"]]
    assert len(references) == 1
    assert references[0]["contrast_pp"] == 0.0


def test_the_ranking_is_sorted_worst_first_and_carries_intervals() -> None:
    ranking = RESULT["muscle_ranking"]
    predicted = [row["predicted_pct"] for row in ranking]
    assert predicted == sorted(predicted)
    for row in ranking:
        assert row["ci_low"] <= row["contrast_pp"] <= row["ci_high"], row
        assert row["n_rows"] > 0 and row["n_cohorts"] > 0


def test_provenance_names_both_subsets_and_the_frozen_dataset() -> None:
    provenance = RESULT["provenance"]
    assert provenance["dataset_version"] == "1.0"
    assert len(provenance["dataset_sha256"]) == 64
    assert provenance["curve_subset"] == {"subset": "A", "rows": 342, "cohorts": 31}
    assert provenance["ranking_subset"] == {"subset": "B", "rows": 304, "cohorts": 25}
    assert provenance["estimation"] == "maximum likelihood"
    assert provenance["inference"] == "cluster-robust on cohort_id"


def test_dropped_columns_are_recorded_rather_than_lost() -> None:
    for form, fitted in RESULT["forms"].items():
        assert isinstance(fitted["dropped_columns"], list), form


def test_writing_produces_a_readable_json_and_a_readable_csv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        curve_path = Path(tmp) / "tier1_curve.json"
        ranking_path = Path(tmp) / "tier1_muscle_ranking.csv"
        run_tier1.write(RESULT, curve_path, ranking_path)

        loaded = json.loads(curve_path.read_text(encoding="utf-8"))
        assert loaded["headline"]["form"] in {"log", "saturating"}

        lines = ranking_path.read_text(encoding="utf-8").strip().splitlines()
        assert lines[0].startswith("muscle_family,")
        assert len(lines) == len(RESULT["muscle_ranking"]) + 1


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
