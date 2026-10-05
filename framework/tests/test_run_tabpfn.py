"""Checks on the post-hoc TabPFN comparison: same folds, same baseline, its own results file.

    python framework/tests/test_run_tabpfn.py

The fold loop is exercised with a stand-in estimator, so these checks run on any machine with
scikit-learn; the real family is smoke-tested in `test_models.py` where tabpfn is installed.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import models

CONFIG = data_loader.load_config()

if not models.sklearn_available():  # pragma: no cover - environment dependent
    print("skipped: scikit-learn is not installed (see requirements.txt)")
    raise SystemExit(0)

import run_baseline
import run_models
import run_tabpfn


def _with_stand_in(action):
    """Run `action` with every search replaced by a plain linear regression on fixed defaults."""
    from sklearn.linear_model import LinearRegression

    original = run_models.build_search
    run_models.build_search = lambda family, config: run_models.FixedSearch(LinearRegression())
    try:
        return action()
    finally:
        run_models.build_search = original


RESULT = _with_stand_in(lambda: run_tabpfn.run(CONFIG))


def test_the_family_is_scored_on_every_campaign_of_subset_a() -> None:
    entry = RESULT["models"]["tabpfn"]
    assert entry["n_rows"] == 346
    assert entry["n_cohorts"] == 32
    assert len(entry["folds"]) == 32


def test_it_is_compared_with_the_same_baseline_as_the_four_families() -> None:
    baseline = run_baseline.run(CONFIG, subset="A")
    form = baseline["best_form_by_out_of_cohort_mae"]
    assert RESULT["baseline"]["form"] == form
    assert abs(RESULT["baseline"]["mae"] - baseline["forms"][form]["mae"]) < 1e-9
    entry = RESULT["models"]["tabpfn"]
    expected = (RESULT["baseline"]["mae"] - entry["mae"]) / RESULT["baseline"]["mae"]
    assert abs(entry["relative_improvement"] - expected) < 1e-9
    assert entry["threshold"] == run_models.IMPROVEMENT_THRESHOLD


def test_it_is_marked_post_hoc_with_the_date_it_was_added() -> None:
    assert RESULT["status"]["post_hoc"] is True
    assert RESULT["status"]["added"] == "2026-09-19"


def test_provenance_names_every_package_the_number_depends_on() -> None:
    provenance = RESULT["provenance"]
    for key in ("dataset_sha256", "time_column", "sklearn", "tabpfn", "torch", "python", "seed"):
        assert key in provenance, key
    assert provenance["time_column"] == "timepoint_days"


def test_write_produces_its_own_table_and_leaves_the_four_families_alone() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        run_tabpfn.write(RESULT, target)
        written = sorted(path.name for path in target.iterdir())
        assert written == ["tabpfn_comparison.csv", "tabpfn_comparison.json"], written
        table = pd.read_csv(target / "tabpfn_comparison.csv")
        assert list(table["model"]) == [f"duration_only ({RESULT['baseline']['form']})", "tabpfn"]
        expected = pd.read_csv(REPO_ROOT / "results" / "model_comparison.csv").columns
        assert list(table.columns) == list(expected)
        record = json.loads((target / "tabpfn_comparison.json").read_text(encoding="utf-8"))
        assert record["models"]["tabpfn"]["n_cohorts"] == 32


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
