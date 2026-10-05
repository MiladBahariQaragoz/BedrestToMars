"""Checks on the tier-3 validation runs. The model is replaced by fakes; nothing is sent.

    python framework/tests/test_run_validation.py
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import features
import forecast
import run_forecast
import run_validation
import typesafe_client

CONFIG = data_loader.load_config()
RESOLVED = features.resolve(data_loader.subset(data_loader.load(CONFIG), CONFIG), CONFIG, "A")
RUNS = CONFIG["forecast"]["validation"]["runs"]
SIZE = {"with_history": (84, 5), "without_history": (346, 32)}


def _uniform_answer(question: dict) -> dict:
    labels = list(question["criteria"])
    return {"type": "choice", "choice": labels[0], "confidence": 0.0,
            "probabilities": {label: 1.0 / len(labels) for label in labels}}


def uniform(requests: list[dict]) -> list[dict]:
    out = []
    for request in requests:
        (name, question), = request["questions"].items()
        out.append({"model": "fake", "answers": {name: _uniform_answer(question)},
                    "usage": {"input_tokens": 10}, "from_cache": True})
    return out


class SameAgain:
    """A repeat client that answers exactly as the cache did."""

    def __init__(self) -> None:
        self.calls = 0

    def ask(self, state, questions) -> dict:
        self.calls += 1
        (name, question), = questions.items()
        return {"model": "fake", "answers": {name: _uniform_answer(question)}, "usage": {}}


REPEATER = SameAgain()
RESULT = run_validation.run(CONFIG, answerer=uniform, repeat_client=REPEATER)


def test_every_declared_run_is_scored_on_every_row_of_its_arm() -> None:
    for arm, variants in RUNS.items():
        rows, folds = SIZE[arm]
        assert set(RESULT["runs"][arm]) == set(variants), arm
        for variant in variants:
            jev = RESULT["runs"][arm][variant]["jev"]
            assert (jev["rows"], jev["folds"]) == (rows, folds), (arm, variant)


def test_each_run_reports_its_gain_over_the_reference_and_its_gap_to_full() -> None:
    for arm, variants in RUNS.items():
        for variant in variants:
            block = RESULT["runs"][arm][variant]
            for name in ("paired_mae_gain_vs_reference_pp", "paired_mae_change_vs_full_pp"):
                interval = block[name]
                assert interval["low"] <= interval["point"] <= interval["high"], (arm, variant, name)
        assert RESULT["runs"][arm]["full"]["paired_mae_change_vs_full_pp"]["point"] == 0.0


def test_shifted_bins_are_asked_and_scored_on_the_shifted_ranges() -> None:
    plan = run_forecast.fold_plan(CONFIG, RESOLVED, "without_history", variant="shifted_bins")
    shifted = forecast.shift_bins(forecast.arm_bins(CONFIG, "without_history"))
    assert list(plan[0]["questions"]["forecast"]["criteria"]) == list(shifted.labels)
    assert run_forecast.plan_bins(CONFIG, "without_history", "shifted_bins") == shifted


def test_scrambled_history_changes_what_is_shown_but_not_what_is_scored() -> None:
    full = run_forecast.fold_plan(CONFIG, RESOLVED, "with_history")
    scrambled = run_forecast.fold_plan(CONFIG, RESOLVED, "with_history", variant="scrambled_history")
    assert [e["truth"] for e in full] == [e["truth"] for e in scrambled]
    moved = sum(
        a["state"]["this_measurement"]["last_scan"] != b["state"]["this_measurement"]["last_scan"]
        for a, b in zip(full, scrambled)
    )
    assert moved >= len(full) // 2, moved
    for real, shuffled in zip(full, scrambled):
        values = lambda entry: sorted(
            scan["change"] for scan in entry["state"]["earlier_scans_in_this_campaign"]
        )
        # the same earlier values, reassigned - never a value from on or after the target day
        assert values(real) == values(shuffled), real["row_id"]


def test_scrambled_history_is_refused_where_there_is_no_history() -> None:
    try:
        run_forecast.fold_plan(CONFIG, RESOLVED, "without_history", variant="scrambled_history")
    except ValueError:
        return
    raise AssertionError("a history scramble was built for the arm that shows no history")


def test_what_the_history_buys_is_scored_on_the_same_rows_of_both_arms() -> None:
    value = RESULT["history_value"]
    assert value["rows"] == 84 and value["campaigns"] == 5
    for name in ("jev", "baselines"):
        interval = value[name]["paired_mae_gain_pp"]
        assert interval["low"] <= interval["point"] <= interval["high"], name


def test_the_repeat_check_asks_the_declared_number_of_requests_again() -> None:
    repeats = RESULT["repeats"]
    assert REPEATER.calls == CONFIG["forecast"]["validation"]["repeats"] == repeats["requests"]
    assert repeats["identical"] == repeats["requests"]
    assert repeats["max_abs_probability_difference"] == 0.0


def test_the_repeat_check_says_how_far_the_forecasts_themselves_moved() -> None:
    """Probabilities can wobble while the forecast holds; the forecast is what is scored."""
    repeats = RESULT["repeats"]
    assert repeats["mean_point_shift_pp"] == repeats["max_point_shift_pp"] == 0.0
    assert repeats["same_top_range"] == repeats["requests"]
    assert repeats["mae_first_pp"] == repeats["mae_second_pp"]


def test_comparing_repeats_counts_every_changed_answer() -> None:
    first = {"forecast": {"probabilities": {"a": 0.6, "b": 0.4}}}
    same = {"forecast": {"probabilities": {"a": 0.6, "b": 0.4}}}
    moved = {"forecast": {"probabilities": {"a": 0.5, "b": 0.5}}}
    report = run_validation.compare_repeats([first, first], [same, moved])
    assert report["identical"] == 1
    assert abs(report["max_abs_probability_difference"] - 0.1) < 1e-12


def test_writing_produces_the_validation_json_the_table_and_the_repeats() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_validation.write(RESULT, Path(tmp))
        text = (Path(tmp) / "forecast_validation.json").read_text(encoding="utf-8")
        json.loads(text, parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))
        table = pd.read_csv(Path(tmp) / "forecast_validation.csv")
        assert len(table) == sum(len(variants) for variants in RUNS.values())
        repeats = json.loads((Path(tmp) / "forecast_repeats.json").read_text(encoding="utf-8"))
        assert len(repeats) == CONFIG["forecast"]["validation"]["repeats"]


def test_an_offline_validation_with_an_empty_cache_never_reaches_the_network() -> None:
    config = copy.deepcopy(CONFIG)
    with tempfile.TemporaryDirectory() as tmp:
        config["forecast"]["cache_dir"] = tmp
        try:
            run_validation.run(config, offline=True)
        except typesafe_client.CacheMiss:
            return
    raise AssertionError("an offline validation with an empty cache did not refuse")


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as error:
            failures += 1
            print(f"FAIL {test.__name__}: {type(error).__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
