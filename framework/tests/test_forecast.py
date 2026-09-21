"""Checks on the forecast arithmetic and on what the language model is allowed to see.

    python framework/tests/test_forecast.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import cv
import data_loader
import features
import forecast

CONFIG = data_loader.load_config()
FRAME = data_loader.subset(data_loader.load(CONFIG), CONFIG)
RESOLVED = features.resolve(FRAME, CONFIG, subset="A")

# Bins used by the arithmetic checks: (-inf,-4) [-4,-2) [-2,0) [0,2) [2,inf)
SMALL = forecast.make_bins([-4, -2, 0, 2])


# --- bins -------------------------------------------------------------------------------


def test_bins_cover_the_real_line_with_two_open_ends() -> None:
    assert SMALL.count == 5
    assert forecast.bin_index(SMALL, -10.0) == 0
    assert forecast.bin_index(SMALL, -4.0) == 1
    assert forecast.bin_index(SMALL, 1.9) == 3
    assert forecast.bin_index(SMALL, 2.0) == 4
    assert forecast.bin_index(SMALL, 50.0) == 4


def test_every_bin_has_a_unique_label() -> None:
    assert len(set(SMALL.labels)) == SMALL.count


def test_representatives_are_midpoints_and_open_bins_sit_half_a_step_out() -> None:
    assert list(SMALL.representatives) == [-5.0, -3.0, -1.0, 1.0, 3.0]


def test_bin_edges_must_be_evenly_spaced() -> None:
    try:
        forecast.make_bins([-4, -2, 1])
    except ValueError:
        return
    raise AssertionError("uneven edges were accepted")


# --- turning a distribution into a forecast --------------------------------------------


def test_point_forecast_is_the_probability_weighted_mean() -> None:
    probs = np.array([0.0, 0.5, 0.5, 0.0, 0.0])
    assert forecast.point(SMALL, probs) == -2.0


def test_interval_is_the_shortest_run_of_bins_reaching_the_level() -> None:
    probs = np.array([0.0, 0.1, 0.6, 0.2, 0.1])
    assert forecast.interval(SMALL, probs, 0.5) == (-2.0, 0.0)
    assert forecast.interval(SMALL, probs, 0.8) == (-2.0, 2.0)


def test_an_open_bin_covers_everything_beyond_its_edge() -> None:
    probs = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
    low, high = forecast.interval(SMALL, probs, 0.5)
    assert low == -math.inf and high == -4.0
    assert forecast.covered((low, high), -100.0)
    assert forecast.interval_width(SMALL, (low, high)) == 2.0


# --- proper scores ----------------------------------------------------------------------


def test_crps_of_a_point_mass_is_its_distance_from_the_true_bin() -> None:
    probs = np.array([0.0, 0.0, 1.0, 0.0, 0.0])
    assert forecast.crps(SMALL, probs, 3.0) == 4.0


def test_crps_is_zero_when_all_mass_sits_on_the_true_bin() -> None:
    probs = np.array([0.0, 0.0, 1.0, 0.0, 0.0])
    assert forecast.crps(SMALL, probs, -1.5) == 0.0


def test_log_score_is_clipped_when_the_true_bin_got_nothing() -> None:
    probs = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
    assert math.isclose(forecast.log_score(SMALL, probs, 1.0), -math.log(1e-6))


def test_score_row_reports_every_metric() -> None:
    probs = np.array([0.0, 0.1, 0.6, 0.2, 0.1])
    scores = forecast.score_row(SMALL, probs, truth=-1.0, levels=(0.5, 0.8))
    assert set(scores) >= {
        "point", "abs_error", "crps", "log_score",
        "covered_50", "width_50", "covered_80", "width_80",
    }
    assert scores["covered_50"] == 1.0 and scores["width_50"] == 2.0


# --- baseline distributions -------------------------------------------------------------


def test_empirical_distribution_places_the_residuals_around_the_centre() -> None:
    probs = forecast.empirical_distribution(SMALL, -1.0, np.array([0.0, 0.0, 2.0]))
    assert np.allclose(probs, [0.0, 0.0, 2 / 3, 1 / 3, 0.0])


def test_empirical_distribution_without_residuals_is_a_point_mass() -> None:
    probs = forecast.empirical_distribution(SMALL, 0.5, np.array([]))
    assert np.allclose(probs, [0.0, 0.0, 0.0, 1.0, 0.0])


def test_answer_probabilities_are_ordered_by_bin_and_renormalised() -> None:
    answer = {"probabilities": {SMALL.labels[2]: 0.3, SMALL.labels[3]: 0.3}}
    probs = forecast.probabilities_from_answer(SMALL, answer)
    assert np.allclose(probs, [0.0, 0.0, 0.5, 0.5, 0.0])


# --- earlier scans of the same measurement ---------------------------------------------


def _series(times: list[float], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cohort_id": "c", "arm_id": "a", "muscle": "soleus",
            "measurement_site": "NA", "modality": "MRI", "outcome_type": "volume",
            "laterality": "right", "timepoint_days": times, "pct_change": values,
        }
    )


def test_a_scan_with_earlier_scans_gets_the_latest_one_as_its_previous() -> None:
    rows = forecast.with_history(_series([14, 28, 42], [-3.0, -6.0, -9.0]), CONFIG)
    assert len(rows) == 2
    last = rows[rows["timepoint_days"] == 42].iloc[0]
    assert last["prev_time"] == 28 and last["prev_value"] == -6.0
    assert [day for day, _ in last["history"]] == [14, 28]


def test_two_scans_on_the_same_day_are_averaged_and_never_precede_each_other() -> None:
    rows = forecast.with_history(_series([14, 28, 28], [-3.0, -5.0, -7.0]), CONFIG)
    assert len(rows) == 2
    assert set(rows["prev_value"]) == {-3.0}
    rows = forecast.with_history(_series([14, 14, 28], [-3.0, -5.0, -7.0]), CONFIG)
    assert list(rows["prev_value"]) == [-4.0]


def test_the_real_history_arm_is_84_rows_from_5_campaigns() -> None:
    rows = forecast.with_history(RESOLVED, CONFIG)
    assert len(rows) == 84
    assert rows["cohort_id"].nunique() == 5


# --- what the model is shown ------------------------------------------------------------


def _fold(cohort: str, history: bool) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    rows = forecast.with_history(RESOLVED, CONFIG) if history else RESOLVED
    target = rows[rows["cohort_id"] == cohort].iloc[-1]
    train = RESOLVED[RESOLVED["cohort_id"] != cohort]
    held_out = RESOLVED[RESOLVED["cohort_id"] == cohort]
    return target, train, held_out


def _state(cohort: str, history: bool, budget: int | None = None) -> tuple[dict, dict]:
    target, train, held_out = _fold(cohort, history)
    arm = "with_history" if history else "without_history"
    return forecast.build_state(target, train, held_out, arm, CONFIG, token_budget=budget)


def _identities() -> set[str]:
    columns = ["cohort_id", "campaign_name", "study_id", "first_author", "doi", "registry_id"]
    values = set()
    for column in columns:
        values.update(str(value) for value in FRAME[column].unique())
    return {value for value in values if len(value) >= 5 and value.upper() != "NA"}


def test_no_state_names_a_paper_author_or_campaign() -> None:
    for cohort, history in (("berlin_bbr1", True), ("medes_ltbr90", False)):
        text = json.dumps(_state(cohort, history)[0])
        leaked = sorted(value for value in _identities() if value in text)
        assert not leaked, leaked


def test_the_target_outcome_never_enters_the_state() -> None:
    target, train, held_out = _fold("berlin_bbr1", history=True)
    target = target.copy()
    for column in ("pct_change", "value_followup", "change_absolute", "p_value"):
        target[column] = -77.7
    state, _ = forecast.build_state(target, train, held_out, "with_history", CONFIG)
    assert "77.7" not in json.dumps(state)


def test_the_history_arm_only_sees_earlier_scans_of_the_held_out_campaign() -> None:
    target, _, _ = _fold("berlin_bbr1", history=True)
    state, _ = _state("berlin_bbr1", history=True)
    day = float(target["timepoint_days"])
    assert state["this_measurement"]["scans_so_far"]
    assert all(scan["day"] < day for scan in state["this_measurement"]["scans_so_far"])
    assert all(scan["day"] < day for scan in state["earlier_scans_in_this_campaign"])


def test_the_arm_without_history_sees_nothing_of_the_held_out_campaign() -> None:
    state, _ = _state("berlin_bbr1", history=False)
    assert "this_measurement" not in state
    assert "earlier_scans_in_this_campaign" not in state


def test_reference_rows_from_the_held_out_campaign_are_refused() -> None:
    target, _, held_out = _fold("berlin_bbr1", history=False)
    try:
        forecast.build_state(target, RESOLVED, held_out, "without_history", CONFIG)
    except cv.LeakageError:
        return
    raise AssertionError("training rows from the held-out campaign were accepted")


def test_the_state_is_trimmed_to_the_token_budget() -> None:
    full, full_info = _state("medes_ltbr90", history=True)
    small, info = _state("medes_ltbr90", history=True, budget=4000)
    assert info["estimated_tokens"] <= 4000
    assert info["observations_kept"] < full_info["observations_kept"]
    assert len(small["observations_other_campaigns"]) == info["observations_kept"]


def test_every_real_state_fits_the_declared_budget() -> None:
    budget = CONFIG["forecast"]["state_token_budget"]
    for cohort in ("medes_ltbr90", "berlin_bbr1"):
        for history in (True, False):
            _, info = _state(cohort, history)
            assert info["estimated_tokens"] <= budget, (cohort, history, info)


def test_the_state_says_what_each_functional_role_means_and_gives_rates_their_unit() -> None:
    state, _ = _state("berlin_bbr1", history=True)
    role = state["measurement"]["functional_role"]
    assert len(role.split()) > 2, role
    assert state["this_measurement"]["average_change_per_day_so_far"].endswith("per day")


# --- ablation variants ------------------------------------------------------------------


def _variant(cohort: str, variant: str) -> dict:
    target, train, held_out = _fold(cohort, history=False)
    state, _ = forecast.build_state(
        target, train, held_out, "without_history", CONFIG, variant=variant
    )
    return state


def test_the_generic_variant_withholds_participants_protocol_detail_and_planned_length() -> None:
    state = _variant("wise2005", "generic")
    assert "participants" not in state
    assert set(state["protocol"]) <= {"unloading", "group"}
    assert state["protocol"]["group"] in {"control, no countermeasure", "countermeasure"}
    assert set(state["target"]) == {"day_of_bed_rest"}
    assert state["measurement"]["muscle"]
    assert "measurement_site" not in state["measurement"]


def test_the_no_reference_variant_drops_every_block_from_other_campaigns() -> None:
    state = _variant("wise2005", "no_reference")
    assert "observations_other_campaigns" not in state
    assert "typical_curve_other_campaigns" not in state
    assert "participants" in state


def test_an_unknown_variant_is_refused() -> None:
    try:
        _variant("wise2005", "anything")
    except ValueError:
        return
    raise AssertionError("an undeclared variant was accepted")


def test_scrambling_shuffles_the_values_and_nothing_else() -> None:
    train = RESOLVED[RESOLVED["cohort_id"] != "wise2005"]
    first = forecast.scramble(train, seed=7)
    again = forecast.scramble(train, seed=7)
    assert list(first["pct_change"]) == list(again["pct_change"])
    assert sorted(first["pct_change"]) == sorted(train["pct_change"])
    assert list(first["pct_change"]) != list(train["pct_change"])
    rest = [column for column in train.columns if column != "pct_change"]
    assert first[rest].equals(train[rest])


def test_the_recognition_state_describes_the_target_without_naming_it() -> None:
    target = RESOLVED[RESOLVED["cohort_id"] == "wise2005"].iloc[0]
    state = forecast.recognition_state(target, CONFIG)
    assert set(state) == {"participants", "protocol", "measurement", "target"}
    text = json.dumps(state)
    assert "WISE" not in text and "wise2005" not in text


def test_the_recognition_question_offers_each_named_campaign_once_and_none() -> None:
    settings = CONFIG["forecast"]["ablation"]["recognition"]
    question = forecast.recognition_question(CONFIG)
    names = set(settings["campaigns"].values())
    assert question["type"] == "choice"
    assert set(question["criteria"].values()) == names | {settings["none_label"]}
    assert len(question["criteria"]) == len(names) + 1


# --- the question -----------------------------------------------------------------------


def test_the_question_offers_one_option_per_bin() -> None:
    for arm in ("with_history", "without_history"):
        bins = forecast.arm_bins(CONFIG, arm)
        question = forecast.question(bins, arm)
        assert question["type"] == "choice"
        assert list(question["criteria"]) == list(bins.labels)
        assert "target.day_of_bed_rest" in json.dumps(question["instructions"])


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as error:  # an import-level gap must show as a failure, not a crash
            failures += 1
            print(f"FAIL {test.__name__}: {type(error).__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
