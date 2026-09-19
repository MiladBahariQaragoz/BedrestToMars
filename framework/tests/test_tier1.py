"""Checks on the three-level meta-regression.

The estimator is tested against data whose variance components and fixed effects are known,
because on the real corpus there is nothing to check an answer against. Every generator here
draws from the model in `DESIGN.md` section 7: a cohort intercept, a study intercept inside
the cohort, a muscle intercept inside the cohort, and weighted residual noise.

    python framework/tests/test_tier1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import cv
import data_loader
import features
import tier1

CONFIG = data_loader.load_config()
DURATIONS = np.array([5.0, 14.0, 30.0, 60.0, 90.0, 119.0])
MUSCLES = ("plantar_flexors", "knee_extensors", "hip_flexors")


def _draw(
    seed: int,
    n_cohorts: int = 40,
    sigma_cohort: float = 2.0,
    sigma_study: float = 1.0,
    sigma_muscle: float = 1.5,
    sigma_residual: float = 1.0,
    intercept: float = -2.0,
    slope: float = -3.0,
    family_effect: float = -4.0,
    form: str = "log",
    design_form: str | None = None,
    tau: float = 10.0,
    cohort_slope_sd: float = 0.0,
    durations_per_cohort: int = 2,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    """Draw a corpus from the model, and return it as the estimator wants it.

    `family_effect` is the contrast of the first muscle against the other two, which is the
    quantity the muscle ranking reports. `cohort_slope_sd` adds a per-campaign duration
    slope the estimator does not model - the misspecification the cluster-robust sandwich
    exists to survive. `durations_per_cohort=1` reproduces the awkward shape of the real
    corpus, where most campaigns ran a single duration and duration is therefore almost
    entirely a between-campaign contrast.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for index in range(n_cohorts):
        cohort = f"campaign_{index:02d}"
        cohort_effect = rng.normal(0.0, sigma_cohort)
        cohort_slope = rng.normal(0.0, cohort_slope_sd) if cohort_slope_sd else 0.0
        muscle_effects = {name: rng.normal(0.0, sigma_muscle) for name in MUSCLES}
        schedule = rng.choice(DURATIONS, size=durations_per_cohort, replace=False)
        for study_index in range(2):
            study = f"{cohort}_paper{study_index}"
            study_effect = rng.normal(0.0, sigma_study)
            for days in schedule:
                for muscle in MUSCLES:
                    basis = (
                        np.log(days)
                        if form == "log"
                        else 1.0 - float(np.exp(-days / tau))
                    )
                    signal = (
                        intercept
                        + (slope + cohort_slope) * basis
                        + (family_effect if muscle == MUSCLES[0] else 0.0)
                    )
                    rows.append(
                        {
                            "cohort_id": cohort,
                            "study_id": study,
                            "muscle": muscle,
                            "duration_days": float(days),
                            "signal": signal
                            + cohort_effect
                            + study_effect
                            + muscle_effects[muscle],
                            "n_analysed": float(rng.integers(6, 25)),
                        }
                    )

    frame = pd.DataFrame(rows)
    scale = frame["n_analysed"] / frame["n_analysed"].mean()
    noise = rng.normal(0.0, sigma_residual, size=len(frame)) / np.sqrt(scale)
    target = frame["signal"] + noise

    encoding = design_form or form
    basis = (
        np.log(frame["duration_days"])
        if encoding == "log"
        else 1.0 - np.exp(-frame["duration_days"] / tau)
    )
    design = pd.DataFrame(
        {
            "intercept": 1.0,
            f"duration_{encoding}": basis,
            "muscle_family_first": (frame["muscle"] == MUSCLES[0]).astype(float),
        }
    )
    return (
        design,
        target,
        frame["cohort_id"],
        frame["study_id"],
        frame["muscle"],
        frame["n_analysed"],
    )


def _fit_drawn(seed: int, **kwargs) -> tier1.Tier1Fit:
    design, target, cohort, study, muscle, weights = _draw(seed, **kwargs)
    return tier1.fit(design, target, cohort, study, muscle, weights=weights)


def test_recovers_known_fixed_effects() -> None:
    fitted = _fit_drawn(seed=11)
    estimates = dict(zip(fitted.columns, fitted.coefficients))
    assert abs(estimates["duration_log"] - (-3.0)) < 0.3
    assert abs(estimates["muscle_family_first"] - (-4.0)) < 0.6


def test_recovers_known_variance_components() -> None:
    """The three levels are what the model is for: it has to tell them apart."""
    fitted = _fit_drawn(seed=12, n_cohorts=70)
    variance = fitted.variance_components
    assert abs(np.sqrt(variance["cohort"]) - 2.0) < 0.8
    assert abs(np.sqrt(variance["muscle"]) - 1.5) < 0.6
    assert abs(np.sqrt(variance["residual"]) - 1.0) < 0.4


def test_ignoring_the_levels_would_understate_the_uncertainty() -> None:
    """The reason for the whole apparatus, stated as a test.

    Drawn the way the corpus actually looks: one duration per campaign, several papers and
    several muscles inside it. Treating those rows as independent evidence about duration
    is what produces a confident wrong interval - 37 rows from one campaign counted as 37
    campaigns. Where duration varies *within* a campaign the comparison reverses, which is
    why the shape of the draw is part of the test rather than an afterthought.
    """
    design, target, cohort, study, muscle, weights = _draw(seed=13, durations_per_cohort=1)
    fitted = tier1.fit(design, target, cohort, study, muscle, weights=weights)
    naive = tier1.fit(
        design, target, cohort, study, muscle, weights=weights, independent=True
    )
    column = list(fitted.columns).index("duration_log")
    textbook = float(np.sqrt(np.diag(naive.cov_model)[column]))
    assert fitted.standard_errors[column] > textbook


def test_confidence_intervals_cover_the_truth() -> None:
    """A 95% interval has to contain the true slope about 95% of the time, or it is decoration.

    Sixteen draws is what the suite can afford; the estimator was checked once over forty,
    where coverage was 38/40 and the mean reported standard error (0.33) sat on the
    empirical spread of the estimates (0.31). The threshold here is loose enough that a
    calibrated interval passes it essentially always, and a badly scaled one does not.
    """
    covered = 0
    draws = range(200, 216)
    for seed in draws:
        fitted = _fit_drawn(seed=seed, durations_per_cohort=1)
        column = list(fitted.columns).index("duration_log")
        low, high = fitted.conf_int()[column]
        covered += int(low <= -3.0 <= high)
    assert covered >= 13, f"only {covered}/{len(draws)} intervals covered the true slope"


def test_cluster_robust_survives_a_misspecified_slope() -> None:
    """A per-campaign slope the model does not carry: the sandwich must notice."""
    design, target, cohort, study, muscle, weights = _draw(
        seed=31, cohort_slope_sd=1.2, n_cohorts=50
    )
    fitted = tier1.fit(design, target, cohort, study, muscle, weights=weights)
    column = list(fitted.columns).index("duration_log")
    robust = fitted.standard_errors[column]
    model_based = float(np.sqrt(np.diag(fitted.cov_model)[column]))
    assert robust > model_based


def test_weights_move_the_fit_towards_the_heavier_campaigns() -> None:
    design, target, cohort, study, muscle, weights = _draw(seed=41)
    heavy = target.copy()
    heavy[weights > weights.median()] += 5.0
    weighted = tier1.fit(design, heavy, cohort, study, muscle, weights=weights)
    unweighted = tier1.fit(design, heavy, cohort, study, muscle)
    column = list(weighted.columns).index("intercept")
    assert weighted.coefficients[column] > unweighted.coefficients[column]


def test_aic_prefers_the_form_that_generated_the_data() -> None:
    truth = dict(seed=51, form="saturating", tau=10.0, slope=-12.0)
    design, target, cohort, study, muscle, weights = _draw(**truth)
    saturating = tier1.fit(design, target, cohort, study, muscle, weights=weights)
    wrong_design, *_ = _draw(design_form="log", **truth)
    logarithmic = tier1.fit(wrong_design, target, cohort, study, muscle, weights=weights)
    assert saturating.aic < logarithmic.aic


def test_a_singular_design_is_refused_by_name() -> None:
    design, target, cohort, study, muscle, weights = _draw(seed=61, n_cohorts=12)
    design["duplicate"] = design["duration_log"]
    try:
        tier1.fit(design, target, cohort, study, muscle, weights=weights)
    except tier1.Tier1Error as error:
        assert "duplicate" in str(error) or "rank" in str(error)
        return
    raise AssertionError("a rank-deficient design must be refused, not fitted")


def test_aliased_columns_are_reported_rather_than_silently_kept() -> None:
    design, _, _, _, _, _ = _draw(seed=62, n_cohorts=8)
    design["constant"] = 3.0
    design["duplicate"] = design["duration_log"]
    kept, dropped = tier1.drop_aliased(design)
    assert set(dropped) == {"constant", "duplicate"}
    assert list(kept.columns) == ["intercept", "duration_log", "muscle_family_first"]


def test_a_contrast_carries_its_own_interval() -> None:
    """F2 and F3 are contrasts with bands, not point estimates."""
    fitted = _fit_drawn(seed=71)
    vector = np.zeros(len(fitted.columns))
    vector[list(fitted.columns).index("muscle_family_first")] = 1.0
    contrast = fitted.contrast(vector)
    assert contrast["ci_low"] < contrast["estimate"] < contrast["ci_high"]
    assert abs(contrast["estimate"] - (-4.0)) < 0.6
    column = list(fitted.columns).index("muscle_family_first")
    assert abs(contrast["se"] - fitted.standard_errors[column]) < 1e-9


def test_degrees_of_freedom_are_the_campaigns_not_the_rows() -> None:
    fitted = _fit_drawn(seed=81, n_cohorts=15)
    assert fitted.n_cohorts == 15
    assert fitted.df == 14
    assert fitted.n_obs > 100


def test_the_saturating_form_profiles_tau_over_the_declared_grid() -> None:
    frame = data_loader.subset(data_loader.load(CONFIG), CONFIG)
    resolved = features.resolve(frame, CONFIG, subset="A")
    fitted = tier1.fit_form(resolved, CONFIG, form="saturating")
    assert fitted.tau in [float(value) for value in CONFIG["features"]["saturating_tau_grid"]]
    assert fitted.n_params == len(fitted.columns) + 4 + 1  # variances, and tau itself


def test_it_fits_the_real_subset_a() -> None:
    frame = data_loader.subset(data_loader.load(CONFIG), CONFIG)
    resolved = features.resolve(frame, CONFIG, subset="A")
    fitted = tier1.fit_form(resolved, CONFIG, form="log")
    assert fitted.n_obs == 342
    assert fitted.n_cohorts == 31
    assert np.isfinite(fitted.coefficients).all()
    assert np.isfinite(fitted.standard_errors).all()
    assert fitted.variance_components["cohort"] > 0.0
    assert fitted.variance_components["residual"] > 0.0


def test_the_real_design_never_carries_the_campaign_identity() -> None:
    frame = data_loader.subset(data_loader.load(CONFIG), CONFIG)
    resolved = features.resolve(frame, CONFIG, subset="A")
    design = features.design_from_resolved(resolved, CONFIG, form="log", intercept=True)
    cv.assert_groups_absent(design, CONFIG)


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
