"""Leave-one-cohort-out splitting, and the assertion that keeps it honest.

A cohort is a bed-rest campaign, not a paper. Three papers report the Berlin BedRest study;
they are one set of participants. A split that puts two of those papers on opposite sides of
a fold boundary is measuring memorisation and reporting it as accuracy.

The guard here is not a convention, it is an assertion that runs on every fold, and
`framework/tests/test_cv.py` hands it a random split and requires it to fail.
"""

from __future__ import annotations

from typing import Any, Iterator

import numpy as np
import pandas as pd


class LeakageError(AssertionError):
    """A split, or a design matrix, would let a model see the cohort it is scored on."""


def loco_split(groups: pd.Series) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield `(train_idx, test_idx)` with one whole campaign held out each time."""
    values = pd.Series(groups).to_numpy()
    for cohort in pd.unique(values):
        test = np.flatnonzero(values == cohort)
        train = np.flatnonzero(values != cohort)
        yield train, test


def assert_no_leakage(
    train_idx: np.ndarray, test_idx: np.ndarray, groups: pd.Series
) -> None:
    """Refuse a fold whose training and test sides share a campaign."""
    values = pd.Series(groups).to_numpy()
    train_cohorts = set(values[np.asarray(train_idx)])
    test_cohorts = set(values[np.asarray(test_idx)])
    shared = train_cohorts & test_cohorts
    if shared:
        raise LeakageError(
            f"{len(shared)} cohort(s) appear on both sides of the fold: {sorted(shared)}. "
            "Split by campaign, not by paper or by row."
        )
    if set(np.asarray(train_idx)) & set(np.asarray(test_idx)):
        raise LeakageError("the same rows appear in training and test")


def assert_groups_absent(matrix: pd.DataFrame, config: dict[str, Any]) -> None:
    """Refuse a design matrix that carries the campaign identity, or anything like it."""
    forbidden = set(config["features"]["never_model"])
    present = forbidden & set(matrix.columns)
    if present:
        raise LeakageError(
            f"the design matrix carries columns that identify the source rather than the "
            f"physiology: {sorted(present)}"
        )


def fold_summary(groups: pd.Series) -> pd.DataFrame:
    """One row per fold: which campaign is held out and how many rows it has."""
    values = pd.Series(groups)
    rows = [
        {"fold": index, "held_out_cohort": cohort, "n_test": int((values == cohort).sum())}
        for index, cohort in enumerate(pd.unique(values.to_numpy()))
    ]
    return pd.DataFrame(rows)
