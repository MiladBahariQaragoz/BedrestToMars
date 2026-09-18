"""Checks on the baseline and the estimator registry.

    python framework/tests/test_models.py
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


def test_saturating_baseline_recovers_a_known_curve() -> None:
    days = np.array([5, 7, 14, 21, 35, 60, 90, 119], dtype=float)
    truth = -20.0 * (1.0 - np.exp(-days / 28.0))
    baseline = models.DurationOnlyBaseline(form="saturating", tau_grid=[7, 14, 28, 60])
    baseline.fit(days, truth)
    assert baseline.tau == 28.0
    assert np.allclose(baseline.predict(days), truth, atol=1e-6)
    assert baseline.asymptote is not None
    assert abs(baseline.asymptote - (-20.0)) < 0.5


def test_linear_baseline_recovers_a_known_curve() -> None:
    """PLAN.md task 3.4 asks for all three forms, linear included, however poorly it fits."""
    days = np.array([5.0, 20.0, 60.0, 119.0])
    truth = -0.5 - 0.2 * days
    baseline = models.DurationOnlyBaseline(form="linear")
    baseline.fit(days, truth)
    assert np.allclose(baseline.predict(days), truth, atol=1e-8)
    assert baseline.tau is None


def test_log_baseline_recovers_a_known_curve() -> None:
    days = np.array([5, 10, 20, 40, 80], dtype=float)
    truth = 2.0 - 3.0 * np.log(days)
    baseline = models.DurationOnlyBaseline(form="log")
    baseline.fit(days, truth)
    assert np.allclose(baseline.predict(days), truth, atol=1e-8)


def test_weights_move_the_fit_towards_the_heavier_points() -> None:
    """Two campaigns disagree at 90 days; the one with more participants should win."""
    days = np.array([10.0, 90.0, 90.0])
    values = np.array([-5.0, -30.0, -10.0])
    unweighted = models.DurationOnlyBaseline(form="log").fit(days, values)
    weighted = models.DurationOnlyBaseline(form="log").fit(
        days, values, weights=np.array([1.0, 50.0, 1.0])
    )
    at_ninety_unweighted = unweighted.predict(np.array([90.0]))[0]
    at_ninety_weighted = weighted.predict(np.array([90.0]))[0]
    assert at_ninety_weighted < at_ninety_unweighted
    assert abs(at_ninety_weighted + 30.0) < abs(at_ninety_unweighted + 30.0)


def test_predictions_are_finite_on_the_real_subset() -> None:
    frame = data_loader.subset(data_loader.load(CONFIG), CONFIG)
    days = frame["duration_days"].to_numpy(dtype=float)
    target = frame["pct_change"].to_numpy(dtype=float)
    baseline = models.DurationOnlyBaseline(
        form="saturating", tau_grid=CONFIG["features"]["saturating_tau_grid"]
    ).fit(days, target)
    assert np.isfinite(baseline.predict(days)).all()


def test_baseline_is_always_available() -> None:
    assert "duration_only" in models.available(CONFIG)


def test_missing_optional_dependency_names_requirements() -> None:
    """Tier 2 needs scikit-learn. If it is absent, say so in one sentence, not a traceback."""
    if models.sklearn_available():
        return
    try:
        models.build("random_forest", CONFIG)
    except models.DependencyMissing as error:
        assert "requirements.txt" in str(error)
        return
    raise AssertionError("building an sklearn model without sklearn must raise")


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
