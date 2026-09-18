"""The baseline everything is measured against, and the four comparative families.

The baseline is a curve through duration alone: how much muscle is gone after `t` days,
with nothing else in the model. It is the number the four model families have to beat before
any of them earns a place in the talk, and under `PLAN.md` section 8 the honest answer may
well be that none of them does.

Tier 2 needs scikit-learn. The core of the framework - loading, features, folds, the
baseline, evaluation - deliberately needs only numpy and pandas, so a machine without the
optional stack can still reproduce the primary result.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

import numpy as np


class DependencyMissing(RuntimeError):
    """An optional package the requested model needs is not installed."""


def sklearn_available() -> bool:
    try:
        import sklearn  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _weighted_least_squares(
    design: np.ndarray, target: np.ndarray, weights: np.ndarray | None
) -> np.ndarray:
    if weights is None:
        weights = np.ones_like(target, dtype=float)
    root = np.sqrt(np.asarray(weights, dtype=float))
    coefficients, *_ = np.linalg.lstsq(design * root[:, None], target * root, rcond=None)
    return coefficients


class DurationOnlyBaseline:
    """Muscle change as a function of unloading duration and nothing else.

    `form="linear"` fits `a + b·t`, kept because `PLAN.md` task 3.4 asks for all three forms
    and because the straight line is what the saturating curve has to beat.
    `form="log"` fits `a + b·ln(t)`, the shape Marusic et al. (2021) fitted to 40 studies.
    `form="saturating"` fits `A·(1 − exp(−t/tau))`, choosing `tau` from the declared grid by
    weighted least squares. `A` is then the estimated eventual loss and `tau` the number of
    days to reach about 63% of it - both quantities a countermeasure planner can use.
    """

    def __init__(
        self, form: str = "saturating", tau_grid: Sequence[float] | None = None
    ) -> None:
        self.form = form
        self.tau_grid = [float(value) for value in (tau_grid or [7, 14, 21, 28, 45, 60, 90])]
        self.coefficients: np.ndarray | None = None
        self.tau: float | None = None

    @property
    def asymptote(self) -> float | None:
        """The eventual loss `A`, defined only for the saturating form."""
        if self.form != "saturating" or self.coefficients is None:
            return None
        return float(self.coefficients[0] + self.coefficients[1])

    def _design(self, days: np.ndarray, tau: float) -> np.ndarray:
        days = np.asarray(days, dtype=float)
        if self.form == "linear":
            return np.column_stack([np.ones_like(days), days])
        if self.form == "log":
            return np.column_stack([np.ones_like(days), np.log(np.clip(days, 1e-9, None))])
        if self.form == "saturating":
            return np.column_stack(
                [np.ones_like(days), 1.0 - np.exp(-days / tau)]
            )
        raise ValueError(f"unknown baseline form: {self.form}")

    def fit(
        self,
        days: np.ndarray,
        target: np.ndarray,
        weights: np.ndarray | None = None,
    ) -> "DurationOnlyBaseline":
        days = np.asarray(days, dtype=float)
        target = np.asarray(target, dtype=float)

        if self.form in {"log", "linear"}:
            self.tau = None
            self.coefficients = _weighted_least_squares(
                self._design(days, tau=1.0), target, weights
            )
            return self

        best: tuple[float, float, np.ndarray] | None = None
        for tau in self.tau_grid:
            coefficients = _weighted_least_squares(self._design(days, tau), target, weights)
            residual = target - self._design(days, tau) @ coefficients
            scale = np.ones_like(target) if weights is None else np.asarray(weights, float)
            error = float(np.sum(scale * residual**2))
            if best is None or error < best[0]:
                best = (error, tau, coefficients)
        assert best is not None
        _, self.tau, self.coefficients = best
        return self

    def predict(self, days: np.ndarray) -> np.ndarray:
        if self.coefficients is None:
            raise RuntimeError("the baseline must be fitted before it predicts")
        return self._design(np.asarray(days, dtype=float), self.tau or 1.0) @ self.coefficients


def available(config: dict[str, Any]) -> list[str]:
    """Which estimators can be built on this machine, in reporting order."""
    names = ["duration_only"]
    if sklearn_available():
        names.extend(config["models"]["families"])
    return names


def build(name: str, config: dict[str, Any]) -> Callable[[], Any]:
    """Return a factory for one estimator, declared entirely by the config."""
    seed = int(config["seed"])

    if name == "duration_only":
        grid = config["features"]["saturating_tau_grid"]
        form = config["features"]["duration_form"]
        return lambda: DurationOnlyBaseline(form=form, tau_grid=grid)

    if not sklearn_available():
        raise DependencyMissing(
            f"{name} needs scikit-learn, which is not installed. "
            "Install the optional stack with `pip install -r requirements.txt`; "
            "the baseline and every tier-1 result run without it."
        )

    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVR

    factories: dict[str, Callable[[], Any]] = {
        "ridge": lambda: make_pipeline(
            StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))
        ),
        "random_forest": lambda: RandomForestRegressor(
            n_estimators=500, min_samples_leaf=3, random_state=seed, n_jobs=1
        ),  # the search parallelises over folds; nesting the two only fights for cores
        "svr": lambda: make_pipeline(StandardScaler(), SVR(kernel="rbf", C=10.0)),
        "gradient_boosting": lambda: GradientBoostingRegressor(
            n_estimators=300, max_depth=2, learning_rate=0.05, random_state=seed
        ),
    }
    if name not in factories:
        raise KeyError(f"unknown model family: {name}")
    return factories[name]
