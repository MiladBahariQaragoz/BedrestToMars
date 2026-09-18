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

from typing import Any

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


def design_matrix(
    frame: pd.DataFrame, config: dict[str, Any], subset: str = "A", tau: float | None = None
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return `(X, y, groups)` for the requested subset.

    `groups` is `cohort_id` and is never a column of `X`: a model that can read the campaign
    identity has already failed the validation in `cv.py`.
    """
    resolved = resolve(frame, config, subset=subset)
    settings = config["features"]

    columns: dict[str, pd.Series] = {}
    form = settings["duration_form"]
    tau = tau if tau is not None else float(settings["saturating_tau_grid"][3])
    columns[f"duration_{form}"] = pd.Series(
        duration_basis(resolved["duration_days"].to_numpy(), form=form, tau=tau),
        index=resolved.index,
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

    matrix = pd.DataFrame(columns, index=resolved.index)
    target = resolved[config["target"]["column"]].astype(float)
    groups = resolved[config["cv"]["group_column"]]
    return matrix, target, groups


def weights(frame: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    """Analysis weights: the number of participants actually measured, never `n_arm`."""
    column = config["target"]["weight_column"]
    values = pd.to_numeric(frame[column], errors="coerce")
    return values.fillna(values.median())
