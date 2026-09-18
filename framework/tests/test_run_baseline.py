"""Checks on the baseline run and what it writes.

    python framework/tests/test_run_baseline.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import run_baseline

CONFIG = data_loader.load_config()


def test_all_three_forms_are_fitted() -> None:
    result = run_baseline.run(CONFIG)
    assert set(result["forms"]) == {"linear", "log", "saturating"}


def test_every_form_is_scored_out_of_cohort() -> None:
    result = run_baseline.run(CONFIG)
    for form, scores in result["forms"].items():
        assert scores["folds"] == 31, form
        assert scores["mae"] > 0, form
        assert scores["ci95"]["low"] <= scores["mae"] <= scores["ci95"]["high"], form


def test_the_saturating_form_reports_its_parameters() -> None:
    """tau and the asymptote are the two numbers a countermeasure planner asks for."""
    saturating = run_baseline.run(CONFIG)["forms"]["saturating"]
    assert saturating["tau_days"] > 0
    assert saturating["asymptote_pct"] < 0


def test_pooled_r2_accompanies_every_form() -> None:
    for form, scores in run_baseline.run(CONFIG)["forms"].items():
        assert "r2_pooled" in scores, form
        assert scores["r2_pooled"] > scores["r2"], form


def test_provenance_is_recorded() -> None:
    result = run_baseline.run(CONFIG)
    provenance = result["provenance"]
    assert provenance["dataset_version"] == "1.0"
    assert len(provenance["dataset_sha256"]) == 64
    assert provenance["seed"] == CONFIG["seed"]
    assert provenance["rows"] == 342
    assert provenance["cohorts"] == 31


def test_writing_produces_readable_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "baseline.json"
        run_baseline.write(run_baseline.run(CONFIG), path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["forms"]["log"]["mae"] > 0


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
