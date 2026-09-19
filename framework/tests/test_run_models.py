"""Checks on the tier-2 comparison: nested tuning, fold discipline, and the comparison.

    python framework/tests/test_run_models.py

Skips itself with a clear message when scikit-learn is absent, because the core of the
framework is meant to run without it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import models

CONFIG = data_loader.load_config()

if not models.sklearn_available():  # pragma: no cover - environment dependent
    print("skipped: scikit-learn is not installed (see requirements.txt)")
    raise SystemExit(0)

import run_models

FRAME = data_loader.subset(data_loader.load(CONFIG), CONFIG)
_SMALL = dict(CONFIG)


def test_every_declared_family_has_a_grid() -> None:
    grids = CONFIG["models"]["grids"]
    for family in CONFIG["models"]["families"]:
        assert family in grids, family


def test_tuning_happens_inside_the_training_fold_only() -> None:
    """The search must never see the held-out campaign, and must group by campaign."""
    search = run_models.build_search("svr", CONFIG)
    from sklearn.model_selection import GroupKFold

    assert isinstance(search.cv, GroupKFold)
    assert search.cv.get_n_splits() == CONFIG["models"]["inner_folds"]


def test_one_family_runs_across_every_campaign() -> None:
    result = run_models.run_family("ridge", FRAME, CONFIG, subset="A")
    assert len(result["folds"]) == 32
    assert np.isfinite([fold["mae"] for fold in result["folds"]]).all()
    assert result["chosen_parameters"]
    assert len(result["chosen_parameters"]) == 32


def test_the_comparison_is_against_the_duration_curve() -> None:
    comparison = run_models.compare("ridge", FRAME, CONFIG, subset="A")
    assert comparison["baseline_mae"] > 0
    assert "relative_improvement" in comparison
    assert comparison["threshold"] == 0.15


def test_results_carry_their_provenance() -> None:
    result = run_models.run_family("ridge", FRAME, CONFIG, subset="A")
    assert result["model"] == "ridge"
    assert result["n_rows"] == 346
    assert result["n_cohorts"] == 32


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
