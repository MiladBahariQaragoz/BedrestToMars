"""Tier 1 - the three-level meta-regression that is the project's primary result.

Tier 2 can say how wrong a prediction is. Only this module can say how much muscle is lost
per day, with an interval around it, which is what both claims in the talk actually need.

The model is the one specified in `DESIGN.md` section 7:

    pct_change = f(duration) + muscle_family + arm_type + covariates
                 + u_cohort + u_study(cohort) + u_muscle(cohort) + residual

Three random intercepts, because the data have three levels: measurements sit inside
studies, studies sit inside campaigns, and the three Berlin papers are not three independent
observations of anything.

**How it is fitted.** Not by `statsmodels`: `MixedLM` carries two levels, and the third one
plus the cluster-robust sandwich would have to be built on top of it anyway. Instead the
marginal likelihood is written out and maximised directly. Because every random effect is
nested inside a campaign, the marginal covariance is block diagonal by campaign, so the
likelihood is a sum over 31 small blocks:

    V_c = sigma_residual^2 / w  +  sigma_cohort^2 J  +  sigma_study^2 S  +  sigma_muscle^2 M

with `J` all ones, `S` marking rows from the same paper and `M` rows measuring the same
muscle. The fixed effects are profiled out by generalised least squares at every step, so
the optimiser only ever searches the four variances.

**Maximum likelihood, not REML.** The three duration forms are compared by AIC and they do
not share a design matrix, which restricted likelihoods cannot be compared across. The price
is a mild downward bias in the variance components with 31 campaigns; the alternative is an
AIC table that means nothing.

**Inference is cluster-robust on the campaign.** The random effects model the correlation;
the sandwich protects the intervals if that model is wrong, which at 31 clusters it may be.
Degrees of freedom are the number of campaigns minus one - never the number of rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import optimize
from scipy import stats

import features

COMPONENTS = ("residual", "cohort", "study", "muscle")


class Tier1Error(RuntimeError):
    """The model cannot be fitted as asked, and guessing would produce a number anyway."""


@dataclass
class _Block:
    """One campaign: its rows, and the structure the random effects impose on them."""

    rows: np.ndarray
    design: np.ndarray
    target: np.ndarray
    inverse_weights: np.ndarray
    same_study: np.ndarray
    same_muscle: np.ndarray


@dataclass
class Tier1Fit:
    """A fitted model, and everything the report and the figures read off it."""

    columns: list[str]
    coefficients: np.ndarray
    cov: np.ndarray
    cov_model: np.ndarray
    variance_components: dict[str, float]
    loglik: float
    n_obs: int
    n_cohorts: int
    n_params: int
    ci_level: float = 0.95
    tau: float | None = None
    tau_at_grid_edge: bool = False
    knots: tuple[float, ...] | None = None
    form: str | None = None
    dropped_columns: list[str] = field(default_factory=list)
    converged: bool = True

    @property
    def df(self) -> int:
        """Campaigns minus one. The rows are not the sample size and never were."""
        return self.n_cohorts - 1

    @property
    def aic(self) -> float:
        return -2.0 * self.loglik + 2.0 * self.n_params

    @property
    def standard_errors(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))

    @property
    def t_values(self) -> np.ndarray:
        return self.coefficients / self.standard_errors

    @property
    def p_values(self) -> np.ndarray:
        return 2.0 * stats.t.sf(np.abs(self.t_values), self.df)

    def conf_int(self, level: float | None = None) -> np.ndarray:
        """One `[low, high]` row per coefficient, on `df` degrees of freedom."""
        level = self.ci_level if level is None else level
        quantile = float(stats.t.ppf(0.5 + level / 2.0, self.df))
        half_width = quantile * self.standard_errors
        return np.column_stack([self.coefficients - half_width, self.coefficients + half_width])

    def contrast(self, vector: np.ndarray, level: float | None = None) -> dict[str, float]:
        """Any linear combination of the coefficients, with its interval.

        The curve band and every muscle contrast are this function: a scenario written as a
        vector, multiplied through the cluster-robust covariance by the delta method.
        """
        vector = np.asarray(vector, dtype=float)
        if vector.shape != (len(self.columns),):
            raise Tier1Error(
                f"a contrast needs one weight per coefficient: expected "
                f"{len(self.columns)}, got {vector.shape}"
            )
        level = self.ci_level if level is None else level
        estimate = float(vector @ self.coefficients)
        variance = float(vector @ self.cov @ vector)
        error = float(np.sqrt(max(variance, 0.0)))
        quantile = float(stats.t.ppf(0.5 + level / 2.0, self.df))
        p_value = (
            float(2.0 * stats.t.sf(abs(estimate / error), self.df))
            if error > 0.0
            else float("nan")
        )
        return {
            "estimate": estimate,
            "se": error,
            "ci_low": estimate - quantile * error,
            "ci_high": estimate + quantile * error,
            "p": p_value,
        }

    def summary(self) -> list[dict[str, Any]]:
        """The fixed effects as plain data, in the order they enter the design."""
        intervals = self.conf_int()
        return [
            {
                "term": name,
                "estimate": float(self.coefficients[index]),
                "se": float(self.standard_errors[index]),
                "ci_low": float(intervals[index, 0]),
                "ci_high": float(intervals[index, 1]),
                "t": float(self.t_values[index]),
                "p": float(self.p_values[index]),
            }
            for index, name in enumerate(self.columns)
        ]


def drop_aliased(design: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Remove columns that carry no information the earlier columns do not already have.

    A dummy that is constant inside the subset, or one that repeats another column exactly,
    makes the design rank deficient. Dropping them here - by name, into the results file -
    is honest; letting a pseudo-inverse quietly split the coefficient between them is not.
    """
    kept: list[str] = []
    dropped: list[str] = []
    matrix = np.empty((len(design), 0), dtype=float)
    for column in design.columns:
        candidate = np.column_stack([matrix, design[column].to_numpy(dtype=float)])
        if np.linalg.matrix_rank(candidate) > matrix.shape[1]:
            matrix = candidate
            kept.append(column)
        else:
            dropped.append(column)
    return design[kept], dropped


def _blocks(
    design: np.ndarray,
    target: np.ndarray,
    weights: np.ndarray,
    cohort: pd.Series,
    study: pd.Series,
    muscle: pd.Series,
) -> list[_Block]:
    """Split the corpus into campaigns, which is where the covariance stops being dense."""
    cohort_values = pd.Series(cohort).to_numpy()
    study_values = pd.Series(study).to_numpy()
    muscle_values = pd.Series(muscle).to_numpy()

    blocks: list[_Block] = []
    for name in pd.unique(cohort_values):
        rows = np.flatnonzero(cohort_values == name)
        studies = study_values[rows]
        muscles = muscle_values[rows]
        blocks.append(
            _Block(
                rows=rows,
                design=design[rows],
                target=target[rows],
                inverse_weights=1.0 / weights[rows],
                same_study=(studies[:, None] == studies[None, :]).astype(float),
                same_muscle=(muscles[:, None] == muscles[None, :]).astype(float),
            )
        )
    return blocks


def _covariance(block: _Block, variances: np.ndarray, independent: bool) -> np.ndarray:
    """`V_c` for one campaign: residual noise plus the three nested intercepts."""
    residual, cohort, study, muscle = variances
    matrix = np.diag(residual * block.inverse_weights)
    if independent:
        return matrix
    matrix = matrix + cohort
    matrix = matrix + study * block.same_study
    matrix = matrix + muscle * block.same_muscle
    return matrix


def _generalised_least_squares(
    blocks: Sequence[_Block], variances: np.ndarray, independent: bool
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """One sweep: the GLS normal equations, the log determinant, and `y' V^-1 y`."""
    width = blocks[0].design.shape[1]
    normal = np.zeros((width, width))
    moment = np.zeros(width)
    log_determinant = 0.0
    quadratic = 0.0

    for block in blocks:
        covariance = _covariance(block, variances, independent)
        try:
            cholesky = np.linalg.cholesky(covariance)
        except np.linalg.LinAlgError as error:  # pragma: no cover - guarded by bounds
            raise Tier1Error(
                "the covariance of one campaign is not positive definite; the variance "
                "search has left the region where the model is defined"
            ) from error
        design = np.linalg.solve(cholesky, block.design)
        target = np.linalg.solve(cholesky, block.target)
        normal += design.T @ design
        moment += design.T @ target
        quadratic += float(target @ target)
        log_determinant += 2.0 * float(np.sum(np.log(np.diag(cholesky))))

    return normal, moment, log_determinant, quadratic


def _neg2_loglik(
    theta: np.ndarray, blocks: Sequence[_Block], n_obs: int, independent: bool
) -> float:
    variances = np.exp(theta)
    normal, moment, log_determinant, quadratic = _generalised_least_squares(
        blocks, variances, independent
    )
    try:
        coefficients = np.linalg.solve(normal, moment)
    except np.linalg.LinAlgError:  # pragma: no cover - the rank check runs first
        return float("inf")
    residual_quadratic = quadratic - float(coefficients @ moment)
    return log_determinant + residual_quadratic + n_obs * float(np.log(2.0 * np.pi))


def fit(
    design: pd.DataFrame,
    target: pd.Series | np.ndarray,
    cohort: pd.Series,
    study: pd.Series,
    muscle: pd.Series,
    weights: pd.Series | np.ndarray | None = None,
    ci_level: float = 0.95,
    independent: bool = False,
    extra_params: int = 0,
    form: str | None = None,
    tau: float | None = None,
    knots: tuple[float, ...] | None = None,
) -> Tier1Fit:
    """Fit the model by maximum likelihood and return it with cluster-robust inference.

    `independent=True` drops the random effects and fits weighted least squares instead.
    It exists so the tests can show what ignoring the three levels would do to an interval,
    and it is never the model that produces a reported number.
    """
    matrix = design.to_numpy(dtype=float)
    values = np.asarray(target, dtype=float)
    if weights is None:
        analysis_weights = np.ones(len(values), dtype=float)
    else:
        analysis_weights = np.asarray(weights, dtype=float)
        analysis_weights = analysis_weights / float(np.mean(analysis_weights))

    rank = int(np.linalg.matrix_rank(matrix))
    if rank < matrix.shape[1]:
        _, aliased = drop_aliased(design)
        raise Tier1Error(
            f"the design has rank {rank} but {matrix.shape[1]} columns. These carry nothing "
            f"the earlier columns do not: {aliased}. Drop them with `drop_aliased` and "
            "record them in the results file."
        )

    blocks = _blocks(matrix, values, analysis_weights, cohort, study, muscle)
    n_obs = len(values)
    spread = float(np.var(values))

    if independent:
        # Weighted least squares. The residual scale is not searched for - it is read off
        # the residuals in closed form - so there is nothing for an optimiser to do.
        unit = np.array([1.0, 0.0, 0.0, 0.0])
        normal, moment, _, quadratic = _generalised_least_squares(blocks, unit, True)
        coefficients = np.linalg.solve(normal, moment)
        residual_quadratic = quadratic - float(coefficients @ moment)
        variances = np.array([residual_quadratic / n_obs, 0.0, 0.0, 0.0])
        result_fun = _neg2_loglik(
            np.log(np.maximum(variances, 1e-300)), blocks, n_obs, True
        )
        converged = True
    else:
        # Variances are searched on the log scale, which keeps them positive without the
        # optimiser having to know that, and bounded away from the degenerate corners.
        start = np.log([0.5 * spread, 0.2 * spread, 0.1 * spread, 0.2 * spread])
        bounds = [(np.log(1e-8 * max(spread, 1e-8)), np.log(1e3 * max(spread, 1e-8)))] * 4
        search = optimize.minimize(
            _neg2_loglik,
            start,
            args=(blocks, n_obs, independent),
            method="L-BFGS-B",
            bounds=bounds,
        )
        variances = np.exp(search.x)
        converged = bool(search.success)
        result_fun = float(search.fun)

    normal, moment, _, _ = _generalised_least_squares(blocks, variances, independent)
    coefficients = np.linalg.solve(normal, moment)
    cov_model = np.linalg.inv(normal)

    meat = np.zeros_like(normal)
    for block in blocks:
        covariance = _covariance(block, variances, independent)
        residual = block.target - block.design @ coefficients
        score = block.design.T @ np.linalg.solve(covariance, residual)
        meat += np.outer(score, score)

    n_cohorts = len(blocks)
    width = matrix.shape[1]
    correction = (n_cohorts / max(n_cohorts - 1, 1)) * (
        (n_obs - 1) / max(n_obs - width, 1)
    )
    cov = cov_model @ meat @ cov_model * correction

    n_variance_params = 1 if independent else len(COMPONENTS)
    return Tier1Fit(
        columns=list(design.columns),
        coefficients=coefficients,
        cov=cov,
        cov_model=cov_model,
        variance_components=dict(zip(COMPONENTS, (float(value) for value in variances))),
        loglik=-0.5 * result_fun,
        n_obs=n_obs,
        n_cohorts=n_cohorts,
        n_params=width + n_variance_params + extra_params,
        ci_level=ci_level,
        tau=tau,
        knots=knots,
        form=form,
        converged=converged,
    )


def fit_form(
    resolved: pd.DataFrame,
    config: dict[str, Any],
    form: str,
    ci_level: float = 0.95,
) -> Tier1Fit:
    """Fit one duration form on already-resolved rows, profiling `tau` where there is one.

    `tau` is not searched continuously: it is chosen from the declared grid in the config,
    which keeps the fit reproducible and counts as the one extra parameter it is.
    """
    days = features.exposure_days(resolved, config)
    target = resolved[config["target"]["column"]].astype(float)
    weights = features.weights(resolved, config)
    cohort = resolved[config["cv"]["group_column"]]
    study = resolved["study_id"]
    muscle = resolved["muscle"]
    knots = tuple(features.spline_knots(days, config)) if form == "spline" else None

    references = config.get("tier1", {}).get("reference_levels") or None

    def _one(tau: float | None) -> Tier1Fit:
        design = features.design_from_resolved(
            resolved,
            config,
            form=form,
            tau=tau,
            intercept=True,
            reference_levels=references,
        )
        design, dropped = drop_aliased(design)
        fitted = fit(
            design,
            target,
            cohort,
            study,
            muscle,
            weights=weights,
            ci_level=ci_level,
            extra_params=1 if form == "saturating" else 0,
            form=form,
            tau=tau,
            knots=knots,
        )
        fitted.dropped_columns = dropped
        return fitted

    if form != "saturating":
        return _one(None)

    grid = [float(value) for value in config["features"]["saturating_tau_grid"]]
    best: Tier1Fit | None = None
    for candidate in grid:
        fitted = _one(candidate)
        if best is None or fitted.loglik > best.loglik:
            best = fitted
    assert best is not None
    # A profile that stops at an end of the grid has not found the best tau, it has found
    # the edge of what it was allowed to consider. The caller has to know which happened.
    best.tau_at_grid_edge = best.tau in (min(grid), max(grid))
    return best


def scenario_vector(
    fitted: Tier1Fit, days: float, overrides: dict[str, float] | None = None
) -> np.ndarray:
    """The reference scenario at one duration, as a contrast vector.

    Reference means every dummy at its baseline - the control arm of the reference muscle
    family, measured by the reference modality, not a composite. A curve has to be drawn
    for somebody, and this is the somebody, named in the results file rather than implied.
    """
    vector = np.zeros(len(fitted.columns), dtype=float)
    position = {name: index for index, name in enumerate(fitted.columns)}
    if "intercept" in position:
        vector[position["intercept"]] = 1.0

    if fitted.form == "spline":
        if fitted.knots is None:  # pragma: no cover - set by `fit_form`
            raise Tier1Error("a spline fit must carry the knots it was built with")
        basis = features.spline_basis(np.array([days], dtype=float), fitted.knots)[0]
        for number, value in enumerate(basis, start=1):
            column = f"duration_spline_{number}"
            if column in position:
                vector[position[column]] = float(value)
    else:
        form = fitted.form or "log"
        column = f"duration_{form}"
        if column in position:
            vector[position[column]] = float(
                features.duration_basis(
                    np.array([days], dtype=float), form=form, tau=fitted.tau or 21.0
                )[0]
            )

    for name, value in (overrides or {}).items():
        if name not in position:
            raise Tier1Error(f"{name} is not a column of this fit: {fitted.columns}")
        vector[position[name]] = float(value)
    return vector


def curve(
    fitted: Tier1Fit, days: Iterable[float], overrides: dict[str, float] | None = None
) -> dict[str, list[float]]:
    """The fitted curve on a grid of durations, with a cluster-robust confidence band."""
    grid = [float(day) for day in days]
    points = [fitted.contrast(scenario_vector(fitted, day, overrides)) for day in grid]
    return {
        "days": grid,
        "fit": [point["estimate"] for point in points],
        "ci_low": [point["ci_low"] for point in points],
        "ci_high": [point["ci_high"] for point in points],
    }


def asymptote(fitted: Tier1Fit) -> dict[str, float]:
    """The eventual loss `A` of a saturating fit: the curve evaluated at `t -> infinity`."""
    if fitted.form != "saturating":
        raise Tier1Error("only the saturating form has an asymptote")
    vector = np.zeros(len(fitted.columns), dtype=float)
    position = {name: index for index, name in enumerate(fitted.columns)}
    vector[position["intercept"]] = 1.0
    vector[position["duration_saturating"]] = 1.0
    return fitted.contrast(vector)
