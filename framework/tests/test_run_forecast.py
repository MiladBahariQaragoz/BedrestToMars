"""Checks on the forecast run and what it writes. The model is replaced by two fakes.

    python framework/tests/test_run_forecast.py
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
import forecast
import run_forecast
import typesafe_client

CONFIG = data_loader.load_config()


def _labels(request: dict) -> list[str]:
    return list(request["questions"]["forecast"]["criteria"])


def _response(probabilities: dict[str, float]) -> dict:
    choice = max(probabilities, key=probabilities.get)
    return {
        "model": "fake",
        "answers": {
            "forecast": {
                "type": "choice", "choice": choice, "confidence": 0.5,
                "probabilities": probabilities,
            }
        },
        "usage": {"input_tokens": 100, "output_tokens": 0},
        "from_cache": False,
    }


def uniform(requests: list[dict]) -> list[dict]:
    """Every range equally likely."""
    out = []
    for request in requests:
        labels = _labels(request)
        out.append(_response({label: 1.0 / len(labels) for label in labels}))
    return out


def curve_echo(requests: list[dict]) -> list[dict]:
    """All probability on the range holding the typical curve's value, read off the state.

    For the arm without history this reproduces the duration-curve baseline's point, binned.
    If answers were matched to the wrong rows, its error would drift far from the baseline's.
    """
    out = []
    for request in requests:
        state = request["state"]
        day = state["target"]["day_of_bed_rest"]
        values = {entry["day"]: entry["change"] for entry in state["typical_curve_other_campaigns"]["values"]}
        if "this_measurement" in state:
            text = state["this_measurement"]["further_change_the_typical_curve_expects"]
            value = float(text.split()[0])
            arm = "with_history"
        else:
            value = float(values[day].rstrip("%"))
            arm = "without_history"
        bins = forecast.arm_bins(CONFIG, arm)
        labels = _labels(request)
        target = labels[forecast.bin_index(bins, value)]
        out.append(_response({label: float(label == target) for label in labels}))
    return out


UNIFORM = run_forecast.run(CONFIG, answerer=uniform)
ECHO = run_forecast.run(CONFIG, answerer=curve_echo)


def _summary(result: dict, arm: str, model: str) -> dict:
    return result["arms"][arm]["models"][model]


def test_the_arm_without_history_scores_every_row_of_every_campaign() -> None:
    for model in ("jev", "duration_curve"):
        summary = _summary(UNIFORM, "without_history", model)
        assert summary["rows"] == 346 and summary["folds"] == 32, (model, summary)


def test_the_history_arm_scores_84_rows_from_5_campaigns() -> None:
    for model in ("jev", "last_scan", "last_scan_plus_curve"):
        summary = _summary(UNIFORM, "with_history", model)
        assert summary["rows"] == 84 and summary["folds"] == 5, (model, summary)


def test_answers_are_matched_to_their_own_rows() -> None:
    for arm, reference in (("without_history", "duration_curve"), ("with_history", "last_scan_plus_curve")):
        echoed = _summary(ECHO, arm, "jev")["mae"]
        baseline = _summary(ECHO, arm, reference)["mae"]
        assert abs(echoed - baseline) < 0.75, (arm, echoed, baseline)


def test_a_uniform_forecast_is_scored_worse_than_the_curve_it_ignores() -> None:
    spread = _summary(UNIFORM, "without_history", "jev")
    curve = _summary(UNIFORM, "without_history", "duration_curve")
    assert spread["crps"] > curve["crps"]
    assert spread["width_80"] > curve["width_80"]
    assert 0.0 <= spread["coverage_50"] <= spread["coverage_80"] <= 1.0


def test_every_summary_carries_the_declared_metrics() -> None:
    wanted = {"mae", "mae_ci95", "crps", "crps_ci95", "log_score", "coverage_50", "width_50",
              "coverage_80", "width_80", "r2_pooled", "worst_fold"}
    for arm in CONFIG["forecast"]["arms"]:
        for model, summary in UNIFORM["arms"][arm]["models"].items():
            assert wanted <= set(summary), (arm, model, wanted - set(summary))


def test_the_comparison_names_each_arms_reference_and_the_bar() -> None:
    for arm, settings in CONFIG["forecast"]["arms"].items():
        comparison = UNIFORM["arms"][arm]["comparison"]
        assert comparison["reference"] == settings["reference_baseline"]
        assert comparison["bar"] == CONFIG["forecast"]["relative_improvement_bar"]
        assert isinstance(comparison["beats_bar_on_mae"], bool)


def test_the_comparison_reports_a_paired_campaign_gain_with_an_interval() -> None:
    """Two overlapping marginal intervals say little; the paired difference is what is quoted."""
    comparison = UNIFORM["arms"]["without_history"]["comparison"]
    assert comparison["campaigns"] == 32
    assert 0 <= comparison["campaigns_better_on_mae"] <= 32
    for metric in ("paired_mae_gain_pp", "paired_crps_gain_pp"):
        gain = comparison[metric]
        assert gain["low"] <= gain["point"] <= gain["high"], (metric, gain)
    assert comparison["paired_crps_gain_pp"]["point"] < 0  # spreading evenly loses to the curve
    echoed = ECHO["arms"]["without_history"]["comparison"]["paired_mae_gain_pp"]["point"]
    assert abs(echoed) < 0.75


def test_every_state_fits_the_token_budget() -> None:
    budget = CONFIG["forecast"]["state_token_budget"]
    for arm in CONFIG["forecast"]["arms"]:
        assert UNIFORM["arms"][arm]["state_tokens_estimated"]["max"] <= budget


def test_provenance_records_the_model_the_dataset_and_the_time_column() -> None:
    provenance = UNIFORM["provenance"]
    assert provenance["model"] == CONFIG["forecast"]["model"]
    assert provenance["models_reported"] == ["fake"]
    assert provenance["dataset_version"] == CONFIG["dataset"]["version"]
    assert len(provenance["dataset_sha256"]) == 64
    assert provenance["time_column"] == "timepoint_days"
    assert provenance["requests"] == 346 + 84


def test_writing_produces_the_json_and_both_tables() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_forecast.write(UNIFORM, Path(tmp))
        loaded = json.loads((Path(tmp) / "forecast.json").read_text(encoding="utf-8"))
        assert set(loaded["arms"]) == set(CONFIG["forecast"]["arms"])
        table = pd.read_csv(Path(tmp) / "forecast_comparison.csv")
        assert len(table) == 2 + 3
        predictions = pd.read_csv(Path(tmp) / "forecast_predictions.csv")
        assert len(predictions) == 346 * 2 + 84 * 3


def test_the_written_json_is_strict_json() -> None:
    """NaN and Infinity are Python's extensions; a strict reader refuses them."""
    with tempfile.TemporaryDirectory() as tmp:
        run_forecast.write(UNIFORM, Path(tmp))
        text = (Path(tmp) / "forecast.json").read_text(encoding="utf-8")
        json.loads(text, parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))


def test_an_offline_run_with_an_empty_cache_never_reaches_the_network() -> None:
    config = copy.deepcopy(CONFIG)
    with tempfile.TemporaryDirectory() as tmp:
        config["forecast"]["cache_dir"] = tmp
        try:
            run_forecast.run(config, offline=True)
        except typesafe_client.CacheMiss:
            return
    raise AssertionError("an offline run with an empty cache did not refuse")


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
