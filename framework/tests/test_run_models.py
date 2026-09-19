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


def test_fixed_search_duck_types_the_search_interface() -> None:
    """A fixed-defaults family must be indistinguishable from a tuned one inside the loop."""
    from sklearn.linear_model import LinearRegression

    search = run_models.FixedSearch(LinearRegression())
    design = np.arange(40, dtype=float).reshape(-1, 1)
    target = -0.5 * design[:, 0]
    search.fit(design, target, groups=np.array(["a"] * 20 + ["b"] * 20))
    assert search.best_params_ == {}
    assert np.isfinite(search.predict(design)).all()


def test_tabpfn_searches_nothing_because_nothing_is_declared() -> None:
    """The empty grid in config is the contract: fixed defaults, fitted in-context."""
    if not models.tabpfn_available():
        return
    search = run_models.build_search("tabpfn", CONFIG)
    assert isinstance(search, run_models.FixedSearch)
    assert CONFIG["models"]["grids"]["tabpfn"] == {}


def test_tuning_happens_inside_the_training_fold_only() -> None:
    """The search must never see the held-out campaign, and must group by campaign."""
    search = run_models.build_search("svr", CONFIG)
    from sklearn.model_selection import GroupKFold

    assert isinstance(search.cv, GroupKFold)
    assert search.cv.get_n_splits() == CONFIG["models"]["inner_folds"]


def test_one_family_runs_across_every_campaign() -> None:
    result = run_models.run_family("ridge", FRAME, CONFIG, subset="A")
    assert len(result["folds"]) == 31
    assert np.isfinite([fold["mae"] for fold in result["folds"]]).all()
    assert result["chosen_parameters"]
    assert len(result["chosen_parameters"]) == 31


def test_the_comparison_is_against_the_duration_curve() -> None:
    comparison = run_models.compare("ridge", FRAME, CONFIG, subset="A")
    assert comparison["baseline_mae"] > 0
    assert "relative_improvement" in comparison
    assert comparison["threshold"] == 0.15


def test_results_carry_their_provenance() -> None:
    result = run_models.run_family("ridge", FRAME, CONFIG, subset="A")
    assert result["model"] == "ridge"
    assert result["n_rows"] == 342
    assert result["n_cohorts"] == 31


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
