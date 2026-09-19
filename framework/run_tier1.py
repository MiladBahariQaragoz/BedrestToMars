"""Fit tier 1 and write the two files the report and the figures read.

This is `PLAN.md` task 4.1 and the primary scientific result: the first numbers in the
project that come with a confidence interval rather than a prediction error. Tier 2 answers
"how wrong is a prediction"; this answers "how much muscle, per day, plus or minus what".

    python framework/run_tier1.py      # writes results/tier1_curve.json
                                       #        results/tier1_muscle_ranking.csv

Two fits, one specification. Subset A carries the duration-response curve, because it keeps
the six campaigns that report only a whole segment and with them the short-duration end of
the curve. Subset B carries the muscle ranking, because a ranking of named muscles cannot
include a row that says "the whole calf".

The headline duration form is chosen by a rule written down before anything was fitted
(`DESIGN.md` section 7.1, `tier1.headline_form` and `tier1.aic_margin` in the config): the
saturating exponential unless another parametric form beats it by more than four AIC points.
The restricted cubic spline is reported beside them as a shape check and is never the
headline, because "it fits better" is not a claim anyone can act on.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy

import data_loader
import features
import tier1

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    return result.stdout.strip()


def _variance_report(fitted: tier1.Tier1Fit) -> dict[str, Any]:
    """The variance components, and the share of the total each level holds."""
    components = {name: float(value) for name, value in fitted.variance_components.items()}
    total = sum(components.values())
    shares = {
        name: (float(value / total) if total > 0 else 0.0)
        for name, value in components.items()
    }
    return {**components, "share_of_total": shares}


def _form_report(fitted: tier1.Tier1Fit) -> dict[str, Any]:
    report: dict[str, Any] = {
        "loglik": float(fitted.loglik),
        "aic": float(fitted.aic),
        "n_params": int(fitted.n_params),
        "n_obs": int(fitted.n_obs),
        "n_cohorts": int(fitted.n_cohorts),
        "df": int(fitted.df),
        "converged": bool(fitted.converged),
        "variance_components": _variance_report(fitted),
        "fixed_effects": fitted.summary(),
        "dropped_columns": list(fitted.dropped_columns),
    }
    if fitted.form == "saturating":
        report["tau_days"] = float(fitted.tau or float("nan"))
        report["tau_at_grid_edge"] = bool(fitted.tau_at_grid_edge)
        asymptote = tier1.asymptote(fitted)
        asymptote["caveat"] = (
            "tau sits at the edge of the declared grid, so the profile never turned over: "
            "the curve is still falling at the longest observation and this asymptote is an "
            "extrapolation beyond 119 days, not a plateau the data show"
            if fitted.tau_at_grid_edge
            else "the eventual loss the fitted curve approaches, read at the reference scenario"
        )
        report["asymptote_pct"] = asymptote
    if fitted.form == "spline":
        report["knots_days"] = [float(knot) for knot in (fitted.knots or ())]
    return report


def _headline(forms: dict[str, tier1.Tier1Fit], config: dict[str, Any]) -> dict[str, Any]:
    """Apply the selection rule, and record the rule beside the choice it made."""
    settings = config["tier1"]
    preferred = settings["headline_form"]
    margin = float(settings["aic_margin"])

    parametric = {
        name: fitted.aic for name, fitted in forms.items() if name != "spline"
    }
    best = min(parametric, key=parametric.get)
    chosen = (
        best if parametric[best] < parametric[preferred] - margin else preferred
    )

    spline_delta = float(forms["spline"].aic - forms[chosen].aic)
    return {
        "form": chosen,
        "rule": (
            f"{preferred} unless another parametric form beats it by more than "
            f"{margin:.0f} AIC points; the spline is a shape check and is never the headline"
        ),
        "aic": {name: float(fitted.aic) for name, fitted in forms.items()},
        "spline_check": {
            "aic_delta_vs_headline": spline_delta,
            "shape_beyond_the_parametric_forms": bool(spline_delta < -margin),
            "meaning": (
                "a large negative delta means the data bend in a way the parametric forms "
                "cannot follow, and the headline curve should be read with that caveat"
            ),
        },
    }


def _reference_levels(resolved: pd.DataFrame) -> dict[str, str]:
    """Which level each dummy set leaves out - the scenario every contrast is against."""
    modality_outcome = resolved["modality"] + "_" + resolved["outcome_type"]
    return {
        "muscle_family": sorted(resolved["muscle_family"].unique())[0],
        "arm_type": sorted(resolved["arm_type"].unique())[0],
        "modality_outcome": sorted(modality_outcome.unique())[0],
    }


def _curve(
    fitted: tier1.Tier1Fit, resolved: pd.DataFrame, config: dict[str, Any]
) -> dict[str, Any]:
    start, stop, step = config["tier1"]["curve_days"]
    grid = np.arange(float(start), float(stop) + float(step) / 2.0, float(step))
    points = tier1.curve(fitted, grid)
    reference = _reference_levels(resolved)
    return {
        **points,
        "form": fitted.form,
        "scenario": {
            **reference,
            "is_composite": 0.0,
            "meaning": (
                "the fitted curve at the reference level of every categorical term: a "
                "control arm, the reference muscle family, the reference modality, not a "
                "composite. Other scenarios shift the curve, they do not reshape it"
            ),
        },
    }


def _ranking(
    fitted: tier1.Tier1Fit, resolved: pd.DataFrame, config: dict[str, Any]
) -> list[dict[str, Any]]:
    """One row per muscle family: its contrast against the reference, and its own level."""
    days = float(config["tier1"]["ranking_days"])
    reference = _reference_levels(resolved)["muscle_family"]
    counts = resolved.groupby("muscle_family").agg(
        n_rows=("row_id", "size"), n_cohorts=("cohort_id", "nunique")
    )

    rows: list[dict[str, Any]] = []
    for family in sorted(resolved["muscle_family"].unique()):
        column = f"muscle_family_{family}"
        is_reference = family == reference
        overrides = {} if is_reference else {column: 1.0}
        note = ""

        if is_reference:
            contrast = {"estimate": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0}
            p_value = float("nan")
        elif column not in fitted.columns:
            contrast = {"estimate": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0}
            p_value = float("nan")
            overrides = {}
            note = "column dropped as aliased; this family is not separable in subset B"
        else:
            vector = np.zeros(len(fitted.columns))
            vector[list(fitted.columns).index(column)] = 1.0
            contrast = fitted.contrast(vector)
            index = list(fitted.columns).index(column)
            p_value = float(fitted.p_values[index])

        predicted = fitted.contrast(tier1.scenario_vector(fitted, days, overrides))
        rows.append(
            {
                "muscle_family": family,
                "n_rows": int(counts.loc[family, "n_rows"]),
                "n_cohorts": int(counts.loc[family, "n_cohorts"]),
                "contrast_pp": float(contrast["estimate"]),
                "se_pp": float(contrast["se"]),
                "ci_low": float(contrast["ci_low"]),
                "ci_high": float(contrast["ci_high"]),
                "p": p_value,
                "predicted_pct": float(predicted["estimate"]),
                "predicted_ci_low": float(predicted["ci_low"]),
                "predicted_ci_high": float(predicted["ci_high"]),
                "is_reference": bool(is_reference),
                "note": note,
            }
        )
    return sorted(rows, key=lambda row: row["predicted_pct"])


def run(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fit both subsets and return everything the two result files hold."""
    config = config or data_loader.load_config()
    frame = data_loader.subset(data_loader.load(config), config)
    level = float(config["tier1"]["ci_level"])

    curve_rows = features.resolve(frame, config, subset="A")
    ranking_rows = features.resolve(frame, config, subset="B")

    forms = {
        form: tier1.fit_form(curve_rows, config, form=form, ci_level=level)
        for form in config["tier1"]["forms"]
    }
    headline = _headline(forms, config)
    ranking_fit = tier1.fit_form(
        ranking_rows, config, form=headline["form"], ci_level=level
    )

    dataset_path = REPO_ROOT / config["dataset"]["path"]
    return {
        "forms": {name: _form_report(fitted) for name, fitted in forms.items()},
        "headline": headline,
        "curve": _curve(forms[headline["form"]], curve_rows, config),
        "muscle_ranking": _ranking(ranking_fit, ranking_rows, config),
        "ranking_model": _form_report(ranking_fit),
        "provenance": {
            "dataset_version": config["dataset"]["version"],
            "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "curve_subset": {
                "subset": "A",
                "rows": int(len(curve_rows)),
                "cohorts": int(curve_rows["cohort_id"].nunique()),
            },
            "ranking_subset": {
                "subset": "B",
                "rows": int(len(ranking_rows)),
                "cohorts": int(ranking_rows["cohort_id"].nunique()),
            },
            "estimation": "maximum likelihood",
            "inference": "cluster-robust on cohort_id",
            "ci_level": level,
            "weighted_by": config["target"]["weight_column"],
            "seed": int(config["seed"]),
            "git_commit": _git_commit(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }


RANKING_COLUMNS = [
    "muscle_family",
    "n_rows",
    "n_cohorts",
    "contrast_pp",
    "se_pp",
    "ci_low",
    "ci_high",
    "p",
    "predicted_pct",
    "predicted_ci_low",
    "predicted_ci_high",
    "is_reference",
    "note",
]


def write(result: dict[str, Any], curve_path: Path, ranking_path: Path) -> None:
    """Write the curve as JSON and the ranking as a CSV a spreadsheet can open."""
    curve_path.parent.mkdir(parents=True, exist_ok=True)
    curve_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    ranking_path.parent.mkdir(parents=True, exist_ok=True)
    with ranking_path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=RANKING_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in result["muscle_ranking"]:
            writer.writerow({name: row[name] for name in RANKING_COLUMNS})


def main() -> int:
    config = data_loader.load_config()
    result = run(config)
    write(
        result,
        REPO_ROOT / "results" / "tier1_curve.json",
        REPO_ROOT / "results" / "tier1_muscle_ranking.csv",
    )

    provenance = result["provenance"]
    curve = provenance["curve_subset"]
    print(
        f"subset {curve['subset']}: {curve['rows']} rows, {curve['cohorts']} campaigns, "
        f"{result['forms']['log']['df']} degrees of freedom\n"
    )
    print(f"{'form':<12}{'AIC':>10}{'cohort var':>13}{'residual var':>14}")
    for form, report in result["forms"].items():
        variance = report["variance_components"]
        print(
            f"{form:<12}{report['aic']:>10.1f}{variance['cohort']:>13.2f}"
            f"{variance['residual']:>14.2f}"
        )

    headline = result["headline"]
    print(f"\nheadline form: {headline['form']}  ({headline['rule']})")
    saturating = result["forms"]["saturating"]
    asymptote = saturating["asymptote_pct"]
    print(
        f"saturating: tau {saturating['tau_days']:.0f} days, eventual loss "
        f"{asymptote['estimate']:.1f}% "
        f"({asymptote['ci_low']:.1f} to {asymptote['ci_high']:.1f})"
    )

    print(f"\n{'muscle family':<22}{'at 60 days':>12}{'95% CI':>20}{'rows':>7}{'campaigns':>11}")
    for row in result["muscle_ranking"]:
        interval = f"{row['predicted_ci_low']:.1f} to {row['predicted_ci_high']:.1f}"
        print(
            f"{row['muscle_family']:<22}{row['predicted_pct']:>12.1f}{interval:>20}"
            f"{row['n_rows']:>7}{row['n_cohorts']:>11}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
