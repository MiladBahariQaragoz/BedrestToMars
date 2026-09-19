"""Checks on the sensitivity analyses of DESIGN.md section 12.

S6 is the one that exists: inverse-variance weights instead of `n_analysed`. The point of
the test file is less the arithmetic than the comparison being a fair one - a weighting
scheme can only be judged against the same rows, not against a larger set that happens to
include studies the other scheme cannot use.

    python framework/tests/test_sensitivity.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import sensitivity

CONFIG = data_loader.load_config()
RESULT = sensitivity.run_s6(CONFIG)  # fitted once: three fits is not a per-test cost


def _row(**overrides: object) -> pd.DataFrame:
    base = {
        "value_baseline": "100",
        "variance_of": "change",
        "variance_type": "SD",
        "variance_value": "10",
        "n_analysed": "25",
    }
    return pd.DataFrame([{**base, **overrides}])


def test_a_standard_deviation_becomes_a_standard_error_of_the_percent_change() -> None:
    """SD 10 on a baseline of 100 with 25 participants: SE of the mean change is 2 units,
    which is 2 percentage points of a baseline of 100."""
    error = sensitivity.percent_change_standard_error(_row())
    assert abs(float(error.iloc[0]) - 2.0) < 1e-9


def test_a_standard_error_is_taken_as_it_stands() -> None:
    error = sensitivity.percent_change_standard_error(
        _row(variance_type="SE", variance_value="2")
    )
    assert abs(float(error.iloc[0]) - 2.0) < 1e-9


def test_a_dispersion_of_the_baseline_is_not_a_dispersion_of_the_change() -> None:
    """The SD of the baseline says how different the participants were, not how uncertain
    the change is. Using one for the other would invent precision."""
    error = sensitivity.percent_change_standard_error(_row(variance_of="baseline"))
    assert np.isnan(float(error.iloc[0]))


def test_an_interquartile_range_is_refused_rather_than_converted() -> None:
    error = sensitivity.percent_change_standard_error(_row(variance_type="IQR"))
    assert np.isnan(float(error.iloc[0]))


def test_weights_are_the_inverse_of_the_squared_standard_error() -> None:
    weights = sensitivity.inverse_variance_weights(_row())
    assert abs(float(weights.iloc[0]) - 0.25) < 1e-9


def test_the_restricted_set_is_much_smaller_and_says_so() -> None:
    """The finding, not a detail: most campaigns never publish a dispersion of the change."""
    restricted = RESULT["restricted"]
    assert restricted["rows"] == 161
    assert restricted["cohorts"] == 8
    assert restricted["rows"] < RESULT["primary"]["rows"]
    assert restricted["cohorts"] < RESULT["primary"]["cohorts"]


def test_the_comparison_that_isolates_the_weighting_is_on_identical_rows() -> None:
    by_size = RESULT["analyses"]["restricted_n_analysed"]
    by_precision = RESULT["analyses"]["restricted_inverse_variance"]
    assert by_size["n_obs"] == by_precision["n_obs"] == RESULT["restricted"]["rows"]
    assert by_size["n_cohorts"] == by_precision["n_cohorts"] == RESULT["restricted"]["cohorts"]


def test_every_analysis_reports_the_headline_coefficient_with_an_interval() -> None:
    for name, analysis in RESULT["analyses"].items():
        headline = analysis["headline"]
        assert headline["ci_low"] <= headline["estimate"] <= headline["ci_high"], name
        assert headline["term"].startswith("duration_"), name
        assert analysis["loco_mae_pp"] > 0.0, name


def test_the_primary_analysis_is_the_one_the_report_quotes() -> None:
    primary = RESULT["analyses"]["primary"]
    assert primary["n_obs"] == 346
    assert primary["n_cohorts"] == 32
    assert primary["weights"] == "n_analysed"


def test_writing_produces_a_table_a_reader_can_scan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sensitivity.md"
        sensitivity.write(RESULT, path)
        text = path.read_text(encoding="utf-8")
        assert "| S6 |" in text
        assert "inverse" in text.lower()
        assert text.count("\n|") >= 4


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
