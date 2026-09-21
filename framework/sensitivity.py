"""The sensitivity analyses of `DESIGN.md` section 12, starting with S6.

Each one is the primary pipeline with a single declared change, reported beside the primary
result whether or not it moves anything. S6 asks whether the weighting scheme matters:
`DESIGN.md` section 7.2 weights rows by `n_analysed`, and the textbook alternative for
pooled aggregate data is to weight by the inverse of each estimate's variance.

**Why it cannot simply be swapped in.** An inverse-variance weight needs a dispersion *of
the change*, and most bed-rest papers do not print one: they print the spread of the
baseline, or nothing at all. On subset A that leaves 160 rows from 7 campaigns out of 342
from 31. Fitting those 160 rows and comparing them with the primary fit would confound two
changes at once - a different weighting scheme *and* a different corpus.

So S6 is three fits, not two: the primary, the same specification restricted to the rows
that carry a usable dispersion, and that restricted set weighted by precision. The
comparison that answers the question is between the last two; the first is there to show
what the restriction alone costs.

    python framework/sensitivity.py      # writes results/sensitivity.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import cv
import data_loader
import features
import tier1

REPO_ROOT = Path(__file__).resolve().parent.parent
USABLE_TYPES = ("SD", "SE")


def percent_change_standard_error(rows: pd.DataFrame) -> pd.Series:
    """The standard error of each row's percent change, or `NaN` where none can be built.

    A printed SD is the spread across participants, so the standard error of the mean change
    is `SD / sqrt(n_analysed)`; a printed SE already is that. Either is turned into
    percentage points of the group's own baseline, which is a first-order approximation that
    ignores the baseline's own uncertainty - acceptable because the alternative is to
    discard the row entirely.

    Three kinds of row get nothing, deliberately. A dispersion `of` the baseline describes
    how different the participants were, not how uncertain their change is. An interquartile
    range or a confidence interval could be converted under assumptions the papers do not
    state. And a row with no dispersion at all cannot be rescued.
    """
    baseline = pd.to_numeric(rows["value_baseline"], errors="coerce").abs()
    value = pd.to_numeric(rows["variance_value"], errors="coerce")
    analysed = pd.to_numeric(rows["n_analysed"], errors="coerce")

    is_sd = rows["variance_type"] == "SD"
    change_error = value.where(~is_sd, value / np.sqrt(analysed))
    error = 100.0 * change_error / baseline

    usable = (
        (rows["variance_of"] == "change")
        & rows["variance_type"].isin(USABLE_TYPES)
        & (value > 0)
        & (baseline > 0)
        & (analysed > 0)
    )
    return error.where(usable, np.nan)


def inverse_variance_weights(rows: pd.DataFrame) -> pd.Series:
    """One over the squared standard error: the classical meta-analytic weight."""
    error = percent_change_standard_error(rows)
    return 1.0 / error**2


def _loco_mae(
    design: pd.DataFrame,
    target: pd.Series,
    groups: pd.Series,
    study: pd.Series,
    muscle: pd.Series,
    weights: pd.Series,
) -> float:
    """Out-of-cohort mean absolute error, campaign-weighted, for a tier-1 specification.

    The design is built once on all the rows and then split, so a level that is missing from
    a training fold keeps its column; the column is dropped for that fold alone and its rows
    are predicted at the reference level, which is what "we have never seen this muscle in
    any other campaign" honestly means.
    """
    errors: list[float] = []
    for train, test in cv.loco_split(groups):
        cv.assert_no_leakage(train, test, groups)
        training, dropped = tier1.drop_aliased(design.iloc[train])
        fitted = tier1.fit(
            training,
            target.iloc[train],
            groups.iloc[train],
            study.iloc[train],
            muscle.iloc[train],
            weights=weights.iloc[train],
        )
        held_out = design.iloc[test].drop(columns=dropped)
        predicted = held_out.to_numpy(dtype=float) @ fitted.coefficients
        errors.append(float(np.mean(np.abs(target.iloc[test].to_numpy() - predicted))))
    return float(np.mean(errors))


def _analyse(
    label: str,
    resolved: pd.DataFrame,
    config: dict[str, Any],
    weights: pd.Series,
    weights_label: str,
) -> dict[str, Any]:
    """Fit one configuration and report its headline coefficient and out-of-cohort error."""
    form = config["tier1"]["headline_form"]
    references = config.get("tier1", {}).get("reference_levels") or None
    target = resolved[config["target"]["column"]].astype(float)
    groups = resolved[config["cv"]["group_column"]]

    fitted = tier1.fit_form(resolved, config, form=form, ci_level=config["tier1"]["ci_level"])
    if weights_label != "n_analysed":
        design = features.design_from_resolved(
            resolved,
            config,
            form=form,
            tau=fitted.tau,
            intercept=True,
            reference_levels=references,
        )
        design, dropped = tier1.drop_aliased(design)
        fitted = tier1.fit(
            design,
            target,
            groups,
            resolved["study_id"],
            resolved["muscle"],
            weights=weights,
            ci_level=config["tier1"]["ci_level"],
            extra_params=1 if form == "saturating" else 0,
            form=form,
            tau=fitted.tau,
            knots=fitted.knots,
        )
        fitted.dropped_columns = dropped

    duration = [term for term in fitted.summary() if term["term"].startswith("duration_")][0]
    design = features.design_from_resolved(
        resolved,
        config,
        form=form,
        tau=fitted.tau,
        intercept=True,
        reference_levels=references,
    )
    design, _ = tier1.drop_aliased(design)
    return {
        "label": label,
        "weights": weights_label,
        "n_obs": int(fitted.n_obs),
        "n_cohorts": int(fitted.n_cohorts),
        "headline": duration,
        "tau_days": float(fitted.tau) if fitted.tau else None,
        "loco_mae_pp": _loco_mae(
            design,
            target,
            groups,
            resolved["study_id"],
            resolved["muscle"],
            weights,
        ),
    }


def run_s6(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """S6: inverse-variance weights, against the same rows weighted by `n_analysed`."""
    config = config or data_loader.load_config()
    frame = data_loader.subset(data_loader.load(config), config)
    resolved = features.resolve(frame, config, subset="A")

    error = percent_change_standard_error(resolved)
    usable = error.notna()
    restricted = resolved[usable].reset_index(drop=True)

    analyses = {
        "primary": _analyse(
            "Primary - every row, weighted by participants analysed",
            resolved,
            config,
            features.weights(resolved, config),
            "n_analysed",
        ),
        "restricted_n_analysed": _analyse(
            "Restricted to rows carrying a dispersion of the change, weighted by participants",
            restricted,
            config,
            features.weights(restricted, config),
            "n_analysed",
        ),
        "restricted_inverse_variance": _analyse(
            "S6 - the same rows, weighted by the inverse of each estimate's variance",
            restricted,
            config,
            inverse_variance_weights(restricted),
            "inverse variance",
        ),
    }
    return {
        "analyses": analyses,
        "primary": {
            "rows": int(len(resolved)),
            "cohorts": int(resolved["cohort_id"].nunique()),
        },
        "restricted": {
            "rows": int(len(restricted)),
            "cohorts": int(restricted["cohort_id"].nunique()),
            "share_of_rows": float(len(restricted) / len(resolved)),
        },
    }


def write(result: dict[str, Any], path: Path) -> None:
    """Write the table `DESIGN.md` section 12 asks for: one row per declared change."""
    restricted = result["restricted"]
    primary = result["primary"]
    lines = [
        "# Sensitivity analyses",
        "",
        "Each row is the primary pipeline with one declared change. The headline coefficient",
        "is the duration term of the headline form; the error is out-of-cohort, campaign-",
        "weighted, from the same leave-one-cohort-out design as everything else.",
        "",
        f"S6 needs a dispersion *of the change*, which only **{restricted['rows']} of "
        f"{primary['rows']} rows** carry, across **{restricted['cohorts']} of "
        f"{primary['cohorts']} campaigns**. That is the finding as much as the coefficient is:",
        "the literature mostly does not publish what inverse-variance weighting needs, which",
        "is why `n_analysed` is the primary weight rather than a compromise.",
        "",
        "| # | Analysis | Weights | Rows | Campaigns | Duration coefficient (95% CI) | LOCO MAE |",
        "|---|---|---|---|---|---|---|",
    ]
    numbering = {
        "primary": "—",
        "restricted_n_analysed": "—",
        "restricted_inverse_variance": "S6",
    }
    for name, analysis in result["analyses"].items():
        headline = analysis["headline"]
        lines.append(
            f"| {numbering[name]} | {analysis['label']} | {analysis['weights']} | "
            f"{analysis['n_obs']} | {analysis['n_cohorts']} | "
            f"{headline['estimate']:.2f} ({headline['ci_low']:.2f} to "
            f"{headline['ci_high']:.2f}) | {analysis['loco_mae_pp']:.2f} pp |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config = data_loader.load_config()
    result = run_s6(config)
    write(result, REPO_ROOT / "results" / "sensitivity.md")
    restricted = result["restricted"]
    print(
        f"rows carrying a dispersion of the change: {restricted['rows']} "
        f"({restricted['share_of_rows']:.0%}) from {restricted['cohorts']} campaigns\n"
    )
    print(f"{'analysis':<34}{'weights':>18}{'coefficient':>14}{'LOCO MAE':>11}")
    for analysis in result["analyses"].values():
        headline = analysis["headline"]
        print(
            f"{analysis['label'][:33]:<34}{analysis['weights']:>18}"
            f"{headline['estimate']:>14.2f}{analysis['loco_mae_pp']:>11.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
