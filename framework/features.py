"""Turn verified rows into the two modelling subsets and a numeric design matrix.

Two things happen here, and both are decisions rather than mechanics, which is why they are
declared in `config.yaml` and described in `DESIGN.md` sections 3.1 and 5.

* **Resolution.** A paper that reports the quadriceps *and* its four heads has measured one
  piece of tissue twice. Within a measurement occasion the components win and the composite
  is dropped. Whole-segment rows are never suppressed this way - they are the only thing six
  campaigns report, and they carry the short-duration end of the curve.
* **Encoding.** Duration enters through a basis function, not raw, because the relationship
  is not linear in days. Everything else is a within-cohort contrast or a correction term.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd

OCCASION = ["cohort_id", "arm_id", "timepoint_days", "modality", "outcome_type"]


def resolve(
    frame: pd.DataFrame, config: dict[str, Any], subset: str = "A"
) -> pd.DataFrame:
    """Apply the one-tissue-one-row rule and the subset's whole-segment policy."""
    whole_segment = set(config["subset"]["whole_segment_muscles"])
    keep_whole = config["subsets"][subset]["include_whole_segment"]

    kept: list[pd.DataFrame] = []
    for _, occasion in frame.groupby(OCCASION, dropna=False, sort=False):
        named = occasion[~occasion["muscle"].isin(whole_segment)]
        has_components = (named["is_composite"] == "FALSE").any()
        drop = (
            has_components
            & (occasion["is_composite"] == "TRUE")
            & ~occasion["muscle"].isin(whole_segment)
        )
        kept.append(occasion[~drop])

    resolved = pd.concat(kept).sort_index()
    if not keep_whole:
        resolved = resolved[~resolved["muscle"].isin(whole_segment)]
    return resolved.reset_index(drop=True)


def duration_basis(
    days: np.ndarray, form: str = "saturating", tau: float = 21.0
) -> np.ndarray:
    """Map unloading duration onto the scale the model works on.

    `log` reproduces the form fitted by Marusic et al. (2021), so our curve can be laid
    over a published one. `saturating` is `1 - exp(-t/tau)`: it rises fast and flattens,
    and `tau` is how many days it takes to reach roughly 63% of the eventual loss.
    """
    days = np.asarray(days, dtype=float)
    if form == "linear":
        return days
    if form == "log":
        return np.log(np.clip(days, 1e-9, None))
    if form == "saturating":
        return 1.0 - np.exp(-days / float(tau))
    raise ValueError(f"unknown duration form: {form}")


def spline_knots(days: np.ndarray, config: dict[str, Any]) -> tuple[float, ...]:
    """The knot positions, taken from the declared percentiles of observed duration.

    Placing knots at quantiles rather than at round numbers of days is what keeps the
    shape check honest: the spline is told where the data are, not where we expect the
    curve to bend.
    """
    percentiles = config["features"]["spline_knots_pct"]
    values = np.asarray(days, dtype=float)
    return tuple(float(value) for value in np.percentile(values, percentiles))


def spline_basis(days: np.ndarray, knots: Sequence[float]) -> np.ndarray:
    """A restricted cubic spline on duration, as two columns.

    The restriction is that the fitted function is linear before the first knot and after
    the last one, so the curve cannot invent a shape at the ends where there are almost no
    campaigns. With three knots that costs two degrees of freedom. The construction is the
    standard one (Harrell, *Regression Modeling Strategies*, section 2.4.4).

    This form is a diagnostic, never the headline curve: it says whether the parametric
    forms in `duration_basis` are lying about the shape (DESIGN.md section 7.1).
    """
    days = np.asarray(days, dtype=float)
    if len(knots) != 3:
        raise ValueError(f"the declared basis needs exactly three knots, got {len(knots)}")
    first, middle, last = (float(knot) for knot in knots)
    if not first < middle < last:
        raise ValueError(f"knots must be strictly increasing, got {knots}")

    def cube(values: np.ndarray) -> np.ndarray:
        return np.clip(values, 0.0, None) ** 3

    scale = (last - first) ** 2
    nonlinear = (
        cube(days - first)
        - cube(days - middle) * (last - first) / (last - middle)
        + cube(days - last) * (middle - first) / (last - middle)
    ) / scale
    return np.column_stack([days, nonlinear])


def design_from_resolved(
    resolved: pd.DataFrame,
    config: dict[str, Any],
    form: str | None = None,
    tau: float | None = None,
    intercept: bool = False,
) -> pd.DataFrame:
    """Encode already-resolved rows as a numeric design matrix.

    Split out from `design_matrix` because tier 1 fits three duration forms against the
    same resolved rows and needs an intercept it can interpret, while tier 2 takes the
    single form the config declares and lets its estimators carry their own.
    """
    settings = config["features"]
    columns: dict[str, pd.Series] = {}
    if intercept:
        columns["intercept"] = pd.Series(1.0, index=resolved.index)

    form = form or settings["duration_form"]
    days = resolved["duration_days"].to_numpy(dtype=float)
    if form == "spline":
        basis = spline_basis(days, spline_knots(days, config))
        for number in (1, 2):
            columns[f"duration_spline_{number}"] = pd.Series(
                basis[:, number - 1], index=resolved.index
            )
    else:
        tau = tau if tau is not None else float(settings["saturating_tau_grid"][3])
        columns[f"duration_{form}"] = pd.Series(
            duration_basis(days, form=form, tau=tau), index=resolved.index
        )

    modality_outcome = resolved["modality"] + "_" + resolved["outcome_type"]
    categorical = {
        "muscle_family": resolved["muscle_family"],
        "arm_type": resolved["arm_type"],
        "modality_outcome": modality_outcome,
    }
    for name, values in categorical.items():
        if name not in settings["categorical"]:
            continue
        dummies = pd.get_dummies(values, prefix=name, drop_first=True, dtype=float)
        for column in dummies.columns:
            columns[column] = dummies[column]

    for name in settings["binary"]:
        columns[name] = (resolved[name] == "TRUE").astype(float)

    return pd.DataFrame(columns, index=resolved.index)


def design_matrix(
    frame: pd.DataFrame, config: dict[str, Any], subset: str = "A", tau: float | None = None
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return `(X, y, groups)` for the requested subset.

    `groups` is `cohort_id` and is never a column of `X`: a model that can read the campaign
    identity has already failed the validation in `cv.py`.
    """
    resolved = resolve(frame, config, subset=subset)
    matrix = design_from_resolved(resolved, config, tau=tau)
    target = resolved[config["target"]["column"]].astype(float)
    groups = resolved[config["cv"]["group_column"]]
    return matrix, target, groups


def weights(frame: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    """Analysis weights: the number of participants actually measured, never `n_arm`."""
    column = config["target"]["weight_column"]
    values = pd.to_numeric(frame[column], errors="coerce")
    return values.fillna(values.median())
