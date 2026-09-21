"""Draw the report's figures and write its data tables from the results files.

    python report/make_figures.py        # writes report/figures/*.pdf and report/generated/*.tex

The slide figures in `figures/` are drawn for a 16:9 deck with 24 pt text. A printed report
wants the same numbers at column width, in vector form, with no title baked into the image,
so this script redraws them in that format. Like `framework/plot_figures.py`, it types no
number: every value is read from `results/` or counted from the frozen dataset through the
framework's own loader, so a refit followed by a rerun cannot leave a stale value in the report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPORT = Path(__file__).resolve().parent
REPO_ROOT = REPORT.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader  # noqa: E402
import features  # noqa: E402

RESULTS = REPO_ROOT / "results"
FIGURES = REPORT / "figures"
GENERATED = REPORT / "generated"

WIDTH = 6.3  # inches: the text width of an A4 page with 2.5 cm margins
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")  # dataviz slots 1-3, validated all-pairs

CLASS_LABELS = {
    "antigravity_extensor": "Antigravity extensors",
    "mixed": "Mixed function",
    "flexor": "Flexors",
}
FAMILY_LABELS = {
    "plantar_flexors": "Plantar flexors",
    "dorsiflexors": "Dorsiflexors",
    "knee_extensors": "Knee extensors",
    "knee_flexors": "Knee flexors",
    "hip_abductors": "Hip abductors",
    "hip_adductors": "Hip adductors",
    "hip_extensors": "Hip extensors",
    "hip_flexors": "Hip flexors",
    "hip_rotators": "Hip rotators",
    "whole_limb": "Whole segment",
    "evertors": "Evertors",
    "trunk_extensors": "Trunk extensors",
}
CAMPAIGNS = {
    "agbresa": "AGBRESA",
    "berlin_bbr1": "Berlin BBR1",
    "berlin_bbr2": "Berlin BBR2-2",
    "birmingham_br5_nct04422665": "Birmingham BR-5",
    "brace_br60": "BRACE",
    "cavanagh_br84": "HDBR-84 (Cavanagh)",
    "cook_ulls30": "ULLS-30 (Cook)",
    "copenhagen_br5": "Copenhagen BR-5",
    "di5_toulouse": "Toulouse dry immersion",
    "dlr_hdt5_crossover": "DLR HDT-5 crossover",
    "dlr_rsl_br60": "DLR RSL",
    "drummond_br7": "BR-7, older adults (Drummond)",
    "imbp_br21": "HDBR-21 (Orlova)",
    "iss_hides_astronauts": "ISS astronauts (Hides)",
    "izola_br10": "BR-10 (Franchi, Šimunič)",
    "izola_br14": "Izola BR-14",
    "krainski_hdbr35": "Dallas HDBR-35",
    "liphardt_br21": "HDBR-21 (Liphardt)",
    "lunhab_br10": "LunHab",
    "maastricht_br14": "Maastricht BR-14",
    "maastricht_br7": "Maastricht BR-7",
    "maastricht_br7_feeding": "Maastricht BR-7, feeding",
    "mcgill_hdbr14": "McGill HDBR-14",
    "medes_ltbr90": "MEDES LTBR",
    "nasa_ames_hdbr30": "NASA Ames HDBR-30",
    "nasa_br17wk": "NASA 17-week BR",
    "nasa_sprint_br70": "NASA SPRINT",
    "nasa_utmb_c3": "NASA UTMB Campaign 3",
    "padova_ulls10": "ULLS-10 (Sarto)",
    "planhab_br10": "PlanHab BR-10",
    "planhab_br21": "PlanHab BR-21",
    "space_vs_br_2026": "Spaceflight vs. BR (Böcker)",
    "tanner_br5": "Utah BR-5",
    "valdoltra_br35": "Valdoltra BR-35",
    "wbv_hdt14": "DLR VBR",
    "wise2005": "WISE-2005",
}
DESIGNS = {
    "HDBR_-6": "Head-down tilt bed rest",
    "horizontal_BR": "Horizontal bed rest",
    "ULLS": "Limb suspension",
    "dry_immersion": "Dry immersion",
    "spaceflight": "Spaceflight",
}
DESIGN_SHORT = {
    "HDBR_-6": "HDBR",
    "horizontal_BR": "HBR",
    "ULLS": "ULLS",
    "dry_immersion": "DI",
    "spaceflight": "SF",
}
MODEL_LABELS = {
    "duration_only (log)": "Duration curve (log)",
    "random_forest": "Random forest",
    "svr": "Support vector regression",
    "ridge": "Ridge regression",
    "gradient_boosting": "Gradient boosting",
}
TERM_LABELS = {
    "intercept": "Intercept",
    "duration_log": "ln(days)",
    "duration_saturating": r"$1-e^{-t/\tau}$",
    "arm_type_countermeasure": "Countermeasure arm",
    "is_composite": "Composite muscle",
}


# --- helpers ------------------------------------------------------------------------------


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": ["Arial", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.5,
            "axes.edgecolor": INK_2,
            "axes.labelcolor": INK,
            "axes.linewidth": 0.6,
            "xtick.color": INK_2,
            "ytick.color": INK_2,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": GRID,
            "grid.linewidth": 0.5,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
        }
    )


def _json(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def _save(figure: plt.Figure, name: str) -> Path:
    path = FIGURES / f"{name}.pdf"
    figure.savefig(path)
    plt.close(figure)
    return path


def _num(value: float, digits: int = 2, signed: bool = False) -> str:
    """A number for LaTeX: a true minus sign, optionally a plus on positives."""
    text = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return text.replace("-", "$-$").replace("+", "$+$") if signed else text.replace("-", "$-$")


def _ci(low: float, high: float, digits: int = 2) -> str:
    return f"{_num(low, digits)} to {_num(high, digits)}"


def _p(value: float) -> str:
    if not np.isfinite(value):
        return "---"
    if value < 0.001:
        return "$<$0.001"
    return f"{value:.3f}"


def _tex(path: str, body: str) -> Path:
    target = GENERATED / path
    target.write_text(
        "% Generated by report/make_figures.py from results/ - do not edit by hand.\n" + body,
        encoding="utf-8",
    )
    return target


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )


def load() -> dict:
    config = data_loader.load_config()
    frame = data_loader.load(config)
    modelled = data_loader.subset(frame, config)
    return {
        "config": config,
        "dataset": frame,
        "modelled": modelled,
        "A": features.resolve(modelled, config, subset="A"),
        "B": features.resolve(modelled, config, subset="B"),
        "tier1": _json("tier1_curve.json"),
        "baseline": _json("baseline.json"),
        "forecast": _json("forecast.json"),
        "ablation": _json("forecast_ablation.json"),
        "validation": _json("forecast_validation.json"),
        "repeats": _json("forecast_repeats.json"),
        "predictions": pd.read_csv(RESULTS / "forecast_predictions.csv"),
        "models": pd.read_csv(RESULTS / "model_comparison.csv"),
        "comparison": pd.read_csv(RESULTS / "forecast_comparison.csv"),
        "ablation_table": pd.read_csv(RESULTS / "forecast_ablation.csv"),
        "validation_table": pd.read_csv(RESULTS / "forecast_validation.csv"),
        "recognition": pd.read_csv(RESULTS / "forecast_recognition.csv"),
        "importance": pd.read_csv(RESULTS / "importance_stability.csv"),
        "ranking": pd.read_csv(RESULTS / "tier1_muscle_ranking.csv"),
        "cohorts": pd.read_csv(REPO_ROOT / "data" / "cohorts.csv"),
        "muscle_map": pd.read_csv(REPO_ROOT / "data" / "muscle_map.csv"),
    }


# --- figures ------------------------------------------------------------------------------


def fig_campaigns(data: dict) -> Path:
    """Every modelled campaign as a bar to its planned length, with its scan days marked."""
    config, resolved = data["config"], data["A"]
    time = config["features"]["time_column"]
    campaigns = (
        resolved.groupby("cohort_id")
        .agg(planned=("duration_days", "max"), design=("design", "first"), rows=("row_id", "size"))
        .sort_values(["planned", "rows"], ascending=[True, True])
    )
    order = list(campaigns.index)
    design_colour = {"HDBR_-6": SERIES[0], "horizontal_BR": SERIES[1]}
    other = SERIES[2]

    figure, axis = plt.subplots(figsize=(WIDTH, 5.4))
    for position, cohort in enumerate(order):
        row = campaigns.loc[cohort]
        colour = design_colour.get(row["design"], other)
        axis.plot([0, row["planned"]], [position, position], color=colour, linewidth=2.4,
                  solid_capstyle="butt", alpha=0.30, zorder=1)
        scans = resolved.loc[resolved["cohort_id"] == cohort].groupby(time).size()
        axis.scatter(scans.index, [position] * len(scans), s=8 + 1.6 * scans.to_numpy(),
                     color=colour, edgecolors="white", linewidths=0.6, zorder=2)
        axis.text(row["planned"] + 2.5, position, f"{int(row['rows'])}", va="center",
                  ha="left", fontsize=6.5, color=INK_2)
    axis.set_yticks(range(len(order)))
    axis.set_yticklabels([CAMPAIGNS.get(c, c) for c in order], fontsize=6.8)
    axis.set_xlim(0, 132)
    axis.set_xticks([0, 14, 30, 60, 90, 119])
    axis.set_ylim(-0.8, len(order) - 0.2)
    axis.set_xlabel("Days of unloading")
    axis.grid(axis="x")
    axis.set_axisbelow(True)
    axis.tick_params(axis="y", length=0)
    handles = [
        plt.Line2D([], [], color=SERIES[0], marker="o", linewidth=0, label="Head-down tilt bed rest"),
        plt.Line2D([], [], color=SERIES[1], marker="o", linewidth=0, label="Horizontal bed rest"),
        plt.Line2D([], [], color=other, marker="o", linewidth=0, label="Limb suspension or dry immersion"),
    ]
    axis.legend(handles=handles, loc="lower right", fontsize=7)
    return _save(figure, "fig_campaigns")


def fig_duration(data: dict) -> Path:
    """Control-arm observations on the day of the scan, with the tier-1 curve and its band."""
    config, resolved, tier1 = data["config"], data["A"], data["tier1"]
    time = config["features"]["time_column"]
    control = resolved[resolved["arm_type"] == "control"]
    curve = tier1["curve"]
    days = np.asarray(curve["days"], dtype=float)
    tau = tier1["forms"]["saturating"]["tau_days"]

    figure, axis = plt.subplots(figsize=(WIDTH, 3.4))
    markers = {"antigravity_extensor": "o", "mixed": "s", "flexor": "^"}
    for (name, label), colour in zip(CLASS_LABELS.items(), SERIES):
        rows = control[control["muscle_function_class"] == name]
        axis.scatter(rows[time], rows["pct_change"].astype(float), s=14, marker=markers[name],
                     color=colour, edgecolors="white", linewidths=0.5, alpha=0.9, zorder=2,
                     label=f"{label} (n = {len(rows)})")
    axis.fill_between(days, curve["ci_low"], curve["ci_high"], color=INK_2, alpha=0.14,
                      linewidth=0, zorder=1, label="95% cluster-robust confidence band")
    axis.plot(days, curve["fit"], color=INK, linewidth=1.6, zorder=3,
              label=rf"Tier-1 saturating curve ($\tau$ = {tau:.0f} days)")
    axis.axhline(0, color=MUTED, linewidth=0.6, zorder=0)
    axis.set_xlim(0, 125)
    axis.set_xticks([0, 14, 30, 60, 90, 119])
    axis.set_xlabel("Day of unloading at the scan")
    axis.set_ylabel("Change from baseline (%)")
    axis.grid(axis="y")
    axis.set_axisbelow(True)
    axis.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), ncol=3, fontsize=7,
                handletextpad=0.4, columnspacing=1.2, borderaxespad=0.0)
    return _save(figure, "fig_duration")


def fig_ranking(data: dict) -> Path:
    """The muscle-family ranking at 60 days, with cluster-robust intervals."""
    ranking = data["ranking"].sort_values("predicted_pct", ascending=False).reset_index(drop=True)
    figure, axis = plt.subplots(figsize=(WIDTH, 2.8))
    positions = np.arange(len(ranking))
    for position, row in ranking.iterrows():
        reference = bool(row["is_reference"])
        colour = INK if reference else SERIES[0]
        axis.plot([row["predicted_ci_low"], row["predicted_ci_high"]], [position, position],
                  color=colour, linewidth=1.3, solid_capstyle="round")
        axis.scatter([row["predicted_pct"]], [position], s=26, color=colour,
                     marker="D" if reference else "o", edgecolors="white", linewidths=0.8, zorder=3)
        plural = "s" if int(row["n_cohorts"]) != 1 else ""
        axis.text(1.5, position, f"{int(row['n_rows'])} rows, {int(row['n_cohorts'])} campaign{plural}",
                  va="center", ha="left", fontsize=6.8, color=INK_2)
    reference_value = float(ranking.loc[ranking["is_reference"], "predicted_pct"].iloc[0])
    axis.axvline(reference_value, color=MUTED, linewidth=0.6, linestyle=(0, (3, 2)), zorder=0)
    axis.set_yticks(positions)
    axis.set_yticklabels([FAMILY_LABELS.get(f, f) + (" (reference)" if r else "")
                          for f, r in zip(ranking["muscle_family"], ranking["is_reference"])])
    axis.set_xlim(-21, 9.5)
    axis.set_xticks([-20, -15, -10, -5, 0])
    axis.set_xlabel("Fitted change at day 60, control arm (%), with 95% cluster-robust CI")
    axis.grid(axis="x")
    axis.set_axisbelow(True)
    axis.tick_params(axis="y", length=0)
    axis.spines["left"].set_visible(False)
    return _save(figure, "fig_ranking")


def _model_table(data: dict) -> pd.DataFrame:
    baseline = data["baseline"]["forms"]
    rows = []
    for key, label, kind in (("linear", "Duration curve, linear", "baseline"),
                             ("saturating", "Duration curve, saturating", "baseline"),
                             ("log", "Duration curve, logarithmic", "reference")):
        form = baseline[key]
        rows.append((label, form["mae"], form["ci95"]["low"], form["ci95"]["high"],
                     form.get("r2_pooled", np.nan), kind))
    for _, model in data["models"].iloc[1:].iterrows():
        rows.append((MODEL_LABELS[model["model"]], model["loco_mae_pp"], model["ci95_low"],
                     model["ci95_high"], model["r2_pooled"], "family"))
    return pd.DataFrame(rows, columns=["label", "mae", "low", "high", "r2", "kind"])


def fig_models(data: dict) -> Path:
    """Out-of-campaign error of every baseline form and tier-2 family, and pooled R-squared."""
    table = _model_table(data)
    colours = {"baseline": MUTED, "reference": INK, "family": SERIES[0]}
    figure, (left, right) = plt.subplots(1, 2, figsize=(WIDTH, 2.5), sharey=True,
                                         gridspec_kw={"width_ratios": [2.2, 1], "wspace": 0.08})
    positions = np.arange(len(table))[::-1]
    for position, (_, row) in zip(positions, table.iterrows()):
        colour = colours[row["kind"]]
        left.plot([row["low"], row["high"]], [position, position], color=colour, linewidth=1.3)
        left.scatter([row["mae"]], [position], s=24, color=colour, edgecolors="white", zorder=3)
        if np.isfinite(row["r2"]):
            right.barh(position, max(row["r2"], 0), height=0.45, color=colour)
            right.text(max(row["r2"], 0) + 0.01, position, f"{row['r2']:.2f}", va="center",
                       fontsize=6.8, color=INK_2)
    reference = float(table.loc[table["kind"] == "reference", "mae"].iloc[0])
    left.axvline(reference, color=INK, linewidth=0.6, linestyle=(0, (3, 2)))
    left.set_yticks(positions)
    left.set_yticklabels(table["label"])
    left.set_xlabel("Out-of-campaign MAE (pp), 95% campaign-bootstrap CI")
    left.set_title("a   Error in held-out campaigns")
    left.grid(axis="x")
    left.set_axisbelow(True)
    left.tick_params(axis="y", length=0)
    right.set_xlim(0, 0.46)
    right.set_xlabel("Pooled out-of-fold $R^2$")
    right.set_title("b   Variance explained")
    right.grid(axis="x")
    right.set_axisbelow(True)
    right.tick_params(axis="y", length=0)
    return _save(figure, "fig_models")


def _without_history(data: dict) -> pd.DataFrame:
    predictions = data["predictions"]
    return predictions[predictions["arm"] == "without_history"]


def fig_jev_campaigns(data: dict) -> Path:
    """Per held-out campaign: how much closer Jev's forecasts are than the duration curve's."""
    errors = _without_history(data).groupby(["cohort", "model"])["abs_error"].mean().unstack()
    rows = _without_history(data).groupby("cohort").size() / 2
    gains = (errors["duration_curve"] - errors["jev"]).sort_values()
    figure, axis = plt.subplots(figsize=(WIDTH, 4.6))
    positions = np.arange(len(gains))
    colours = [SERIES[0] if value > 0 else SERIES[1] for value in gains]
    axis.barh(positions, gains.to_numpy(), height=0.62, color=colours)
    for position, (cohort, value) in zip(positions, gains.items()):
        offset = 0.06 if value >= 0 else -0.06
        axis.text(value + offset, position, f"{int(rows[cohort])}", va="center",
                  ha="left" if value >= 0 else "right", fontsize=6.3, color=INK_2)
    axis.axvline(0, color=INK_2, linewidth=0.7)
    axis.set_yticks(positions)
    axis.set_yticklabels([CAMPAIGNS.get(c, c) for c in gains.index], fontsize=6.8)
    axis.set_xlabel("Campaign MAE of the duration curve minus campaign MAE of Jev (pp)")
    axis.grid(axis="x")
    axis.set_axisbelow(True)
    axis.tick_params(axis="y", length=0)
    handles = [plt.Rectangle((0, 0), 1, 1, color=SERIES[0], label=f"Jev closer ({int((gains > 0).sum())})"),
               plt.Rectangle((0, 0), 1, 1, color=SERIES[1], label=f"Curve closer ({int((gains <= 0).sum())})")]
    axis.legend(handles=handles, loc="lower right", fontsize=7)
    return _save(figure, "fig_jev_campaigns")


ABLATION_LABELS = {
    "full": "Full state (as run)",
    "generic": "Generic description",
    "reordered": "Reference rows reordered",
    "shifted_bins": "Ranges shifted half a step",
    "scrambled_reference": "Reference values shuffled",
    "no_reference": "No reference data",
    "scrambled_history": "Earlier scans shuffled",
}


def fig_jev_checks(data: dict) -> Path:
    """The paired gain over each arm's reference under every ablation and presentation check."""
    ablation = data["ablation_table"].set_index("variant")
    validation = data["validation_table"]
    without = []
    for key in ("full", "generic", "reordered", "shifted_bins", "scrambled_reference", "no_reference"):
        if key in ablation.index and key not in ("reordered", "shifted_bins"):
            row = ablation.loc[key]
            without.append((key, row["paired_mae_gain_vs_curve_pp"], row["paired_mae_gain_vs_curve_pp_low"],
                            row["paired_mae_gain_vs_curve_pp_high"]))
        else:
            row = validation[(validation["arm"] == "without_history") & (validation["variant"] == key)].iloc[0]
            without.append((key, row["paired_gain_pp"], row["paired_gain_low"], row["paired_gain_high"]))
    history = []
    for key in ("full", "generic", "reordered", "shifted_bins", "scrambled_history",
                "scrambled_reference", "no_reference"):
        row = validation[(validation["arm"] == "with_history") & (validation["variant"] == key)].iloc[0]
        history.append((key, row["paired_gain_pp"], row["paired_gain_low"], row["paired_gain_high"]))

    figure, (left, right) = plt.subplots(1, 2, figsize=(WIDTH, 2.7),
                                         gridspec_kw={"wspace": 0.95})
    for axis, rows, title in ((left, without, "a   Without history (32 campaigns)"),
                              (right, history, "b   With history (5 campaigns)")):
        positions = np.arange(len(rows))[::-1]
        for position, (key, point, low, high) in zip(positions, rows):
            colour = SERIES[0] if low > 0 else (SERIES[1] if high < 0 else MUTED)
            axis.plot([low, high], [position, position], color=colour, linewidth=1.3)
            axis.scatter([point], [position], s=22, color=colour, edgecolors="white", zorder=3)
        axis.axvline(0, color=INK_2, linewidth=0.7)
        axis.set_yticks(positions)
        axis.set_yticklabels([ABLATION_LABELS[key] for key, *_ in rows], fontsize=6.8)
        axis.set_title(title)
        axis.set_xlabel("Paired MAE gain (pp)")
        axis.grid(axis="x")
        axis.set_axisbelow(True)
        axis.tick_params(axis="y", length=0)
    return _save(figure, "fig_jev_checks")


def fig_jev_scatter(data: dict) -> Path:
    """Forecast against observed value for the curve and for Jev, every row of subset A."""
    rows = _without_history(data)
    figure, axes = plt.subplots(1, 2, figsize=(WIDTH, 3.0), sharex=True, sharey=True,
                                gridspec_kw={"wspace": 0.08})
    limits = (-32, 26)
    comparison = data["comparison"].set_index(["arm", "model"])
    for axis, (model, label, colour) in zip(axes, (("duration_curve", "a   Duration curve", MUTED),
                                                  ("jev", "b   Jev (TypeSafe)", SERIES[0]))):
        subset = rows[rows["model"] == model]
        axis.plot(limits, limits, color=INK_2, linewidth=0.6, linestyle=(0, (3, 2)), zorder=1)
        axis.scatter(subset["truth"], subset["point"], s=9, color=colour, edgecolors="white",
                     linewidths=0.4, alpha=0.9, zorder=2)
        stats = comparison.loc[("without_history", model)]
        axis.text(0.04, 0.96, f"MAE {stats['mae_pp']:.2f} pp\npooled $R^2$ {stats['r2_pooled']:.2f}",
                  transform=axis.transAxes, va="top", fontsize=7, color=INK)
        axis.set_title(label)
        axis.set_xlim(limits)
        axis.set_ylim(limits)
        axis.set_xlabel("Observed change (%)")
        axis.grid(True)
        axis.set_axisbelow(True)
        axis.set_aspect("equal")
    axes[0].set_ylabel("Forecast (%)")
    return _save(figure, "fig_jev_scatter")


def fig_recognition(data: dict) -> Path:
    """Recognition probe: probability on the true campaign name against the campaign's gain."""
    table = data["recognition"]
    chance = 1.0 / (len(data["config"]["forecast"]["ablation"]["recognition"]["campaigns"]) + 1)
    offsets = {  # label placement only, chosen so that no two names overlap
        "brace_br60": (-6, 5, "right"),
        "nasa_utmb_c3": (6, -7, "left"),
        "berlin_bbr1": (7, 3, "left"),
        "planhab_br21": (6, 5, "left"),
        "lunhab_br10": (6, -8, "left"),
        "nasa_sprint_br70": (-6, 0, "right"),
    }
    figure, axis = plt.subplots(figsize=(WIDTH * 0.66, 2.7))
    recognised = table["top1"] >= 0.5
    for mask, colour, marker in ((~recognised, SERIES[0], "o"), (recognised, SERIES[1], "D")):
        axis.scatter(table.loc[mask, "mean_p_true"], table.loc[mask, "paired_mae_gain_pp"],
                     s=10 + 1.2 * table.loc[mask, "rows"].to_numpy(), color=colour, marker=marker,
                     edgecolors="white", linewidths=0.6, zorder=3)
    for _, row in table.iterrows():
        dx, dy, ha = offsets.get(row["cohort"], (6, 2, "left"))
        axis.annotate(CAMPAIGNS.get(row["cohort"], row["cohort"]),
                      (row["mean_p_true"], row["paired_mae_gain_pp"]), xytext=(dx, dy),
                      textcoords="offset points", fontsize=6.2, color=INK_2, ha=ha, va="center")
    axis.axvline(chance, color=MUTED, linewidth=0.6, linestyle=(0, (3, 2)))
    axis.text(chance + 0.006, 2.35, "chance (1/12)", fontsize=6.2, color=MUTED, va="center")
    axis.axhline(0, color=INK_2, linewidth=0.6)
    axis.set_xlim(0, 0.62)
    axis.set_ylim(-0.9, 3.2)
    axis.set_xlabel("Mean probability placed on the true campaign name")
    axis.set_ylabel("Paired MAE gain over curve (pp)")
    axis.grid(True)
    axis.set_axisbelow(True)
    handles = [
        plt.Line2D([], [], color=SERIES[0], marker="o", linewidth=0, markersize=5, label="Not recognised"),
        plt.Line2D([], [], color=SERIES[1], marker="D", linewidth=0, markersize=4.5,
                   label="Recognised (named first on at least half its rows)"),
    ]
    axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.5)
    return _save(figure, "fig_recognition")


# --- tables -------------------------------------------------------------------------------


def _counts(series: pd.Series, labels: dict[str, str] | None = None) -> str:
    counts = series.fillna("not stated").value_counts()
    return "; ".join(f"{(labels or {}).get(k, str(k).replace('_', ' '))} {v}" for k, v in counts.items())


def tab_dataset(data: dict) -> Path:
    frame = data["dataset"]
    rows = [
        ("Rows (study $\\times$ arm $\\times$ muscle $\\times$ occasion)", f"{len(frame)}"),
        ("Studies", f"{frame['study_id'].nunique()}, published {frame['year'].min()}--{frame['year'].max()}"),
        ("Independent campaigns (cohorts)", f"{frame['cohort_id'].nunique()}"),
        ("Distinct muscles or muscle groups", f"{frame['muscle'].nunique()}; "
         f"{int((frame['is_composite'] == 'TRUE').sum())} rows are composites"),
        ("Design", _counts(frame["design"], DESIGNS)),
        ("Planned unloading", f"{frame.loc[frame['design'] != 'spaceflight', 'duration_days'].min()}--"
         f"{frame.loc[frame['design'] != 'spaceflight', 'duration_days'].max()} days on the ground; "
         f"{frame.loc[frame['design'] == 'spaceflight', 'duration_days'].max()} days in spaceflight"),
        ("Phase", _counts(frame["phase"], {"bed_rest": "during unloading", "recovery": "recovery"})),
        ("Arm", _counts(frame["arm_type"])),
        ("Modality", _counts(frame["modality"])),
        ("Outcome", _counts(frame["outcome_type"], {"CSA": "CSA", "lean_mass": "lean mass"})),
        ("Source of the value", _counts(frame["data_source"], {"figure_digitized": "figure (digitised)",
                                                               "repository": "open data repository"})),
        ("Extraction confidence", _counts(frame["extraction_confidence"])),
        ("Population", _counts(frame["population"])),
        ("Sex", _counts(frame["sex"], {"M": "men only", "F": "women only", "mixed": "mixed"})),
    ]
    body = "\n".join(f"{label} & {value} \\\\" for label, value in rows)
    return _tex("tab_dataset.tex", body + "\n")


def tab_subsets(data: dict) -> Path:
    config, frame = data["config"], data["dataset"]
    phase = frame[frame["phase"] == config["subset"]["phase"]]
    lower = phase[~phase["muscle"].isin(config["subset"]["drop_muscles"])]
    steps = [
        ("All rows of \\texttt{dataset\\_v1.1.csv}", frame),
        ("Predicate 1: during unloading (\\texttt{phase = bed\\_rest})", phase),
        ("Predicate 2: lower-limb muscles only", lower),
        ("Predicate 3: one tissue per occasion --- subset A", data["A"]),
        ("Named muscles only --- subset B", data["B"]),
    ]
    body = "\n".join(
        f"{label} & {len(rows)} & {rows['study_id'].nunique()} & {rows['cohort_id'].nunique()} \\\\"
        for label, rows in steps
    )
    return _tex("tab_subsets.tex", body + "\n")


def tab_tier1_forms(data: dict) -> Path:
    tier1 = data["tier1"]
    forms = tier1["forms"]
    headline = forms["saturating"]["aic"]
    log_slope = next(f for f in forms["log"]["fixed_effects"] if f["term"] == "duration_log")
    doubling = [log_slope[k] * np.log(2) for k in ("estimate", "ci_low", "ci_high")]
    asymptote = forms["saturating"]["asymptote_pct"]
    knots = ", ".join(f"{k:.0f}" for k in forms["spline"]["knots_days"])
    lines = [
        ("Logarithmic, $a + b\\ln t$", forms["log"],
         f"$b$ = {_num(log_slope['estimate'])} pp per $e$-fold ({_ci(log_slope['ci_low'], log_slope['ci_high'])}); "
         f"{_num(doubling[0])} pp per doubling ({_ci(doubling[1], doubling[2])})"),
        ("Saturating, $A(1 - e^{-t/\\tau})$", forms["saturating"],
         f"$\\tau = {forms['saturating']['tau_days']:.0f}$ days; eventual loss $A$ = {_num(asymptote['estimate'], 1)}\\% "
         f"({_ci(asymptote['ci_low'], asymptote['ci_high'], 1)})"),
        ("Restricted cubic spline", forms["spline"], f"Knots at {knots} days (shape check only)"),
    ]
    body = "\n".join(
        f"{label} & {form['aic']:.1f} & {_num(form['aic'] - headline, 1, signed=True) if form is not forms['saturating'] else '0.0'} & "
        f"{form['n_params']} & {value} \\\\"
        for label, form, value in lines
    )
    return _tex("tab_tier1_forms.tex", body + "\n")


def tab_curve(data: dict) -> Path:
    curve = data["tier1"]["curve"]
    days = [5, 14, 30, 60, 90, 119]
    index = [curve["days"].index(float(day)) for day in days]
    header = " & ".join(f"{day}" for day in days)
    fit = " & ".join(_num(curve["fit"][i], 1) for i in index)
    band = " & ".join(f"{_num(curve['ci_low'][i], 1)} to {_num(curve['ci_high'][i], 1)}" for i in index)
    body = (f"Day of unloading & {header} \\\\\n\\midrule\n"
            f"Fitted change (\\%) & {fit} \\\\\n"
            f"95\\% CI & {band} \\\\\n")
    return _tex("tab_curve.tex", body)


def tab_variance(data: dict) -> Path:
    tier1 = data["tier1"]
    rows = [("Subset A, saturating form", tier1["forms"]["saturating"]["variance_components"]),
            ("Subset B, ranking model", tier1["ranking_model"]["variance_components"])]
    body = []
    for label, components in rows:
        shares = components["share_of_total"]
        cells = " & ".join(f"{components[k]:.2f} ({100 * shares[k]:.0f}\\%)"
                           for k in ("cohort", "study", "muscle", "residual"))
        body.append(f"{label} & {cells} \\\\")
    return _tex("tab_variance.tex", "\n".join(body) + "\n")


def tab_ranking(data: dict) -> Path:
    ranking = data["ranking"].sort_values("predicted_pct").reset_index(drop=True)
    body = []
    for _, row in ranking.iterrows():
        name = FAMILY_LABELS.get(row["muscle_family"], row["muscle_family"])
        if row["is_reference"]:
            contrast, p = "reference", "---"
        else:
            contrast = f"{_num(row['contrast_pp'], 2, signed=True)} ({_ci(row['ci_low'], row['ci_high'])})"
            p = _p(row["p"])
        body.append(f"{name} & {int(row['n_rows'])} & {int(row['n_cohorts'])} & "
                    f"{_num(row['predicted_pct'], 1)} ({_ci(row['predicted_ci_low'], row['predicted_ci_high'], 1)}) & "
                    f"{contrast} & {p} \\\\")
    return _tex("tab_ranking.tex", "\n".join(body) + "\n")


def _term_label(term: str) -> str:
    if term in TERM_LABELS:
        return TERM_LABELS[term]
    if term.startswith("muscle_family_"):
        return FAMILY_LABELS.get(term[len("muscle_family_"):], term)
    if term.startswith("modality_outcome_"):
        modality, _, outcome = term[len("modality_outcome_"):].partition("_")
        outcome = {"volume": "volume", "CSA": "CSA", "lean_mass": "lean mass", "thickness": "thickness"}[outcome]
        return f"{modality.replace('ultrasound', 'Ultrasound')} {outcome}"
    return _escape(term)


def tab_fixed_effects(data: dict) -> Path:
    tier1 = data["tier1"]
    first = {f["term"]: f for f in tier1["forms"]["saturating"]["fixed_effects"]}
    second = {f["term"]: f for f in tier1["ranking_model"]["fixed_effects"]}
    order = list(first) + [term for term in second if term not in first]
    groups = {"muscle_family_": "Muscle family (vs. knee extensors)",
              "modality_outcome_": "Modality and outcome (vs. CT CSA)"}
    body, opened = [], set()
    for term in order:
        for prefix, heading in groups.items():
            if term.startswith(prefix) and prefix not in opened:
                body.append(f"\\addlinespace\n\\multicolumn{{5}}{{@{{}}l}}{{\\textit{{{heading}}}}} \\\\")
                opened.add(prefix)
        cells = []
        for source in (first, second):
            effect = source.get(term)
            if effect is None:
                cells.append("--- & ---")
            else:
                cells.append(f"{_num(effect['estimate'], 2)} ({_ci(effect['ci_low'], effect['ci_high'])}) & {_p(effect['p'])}")
        indent = "\\quad " if any(term.startswith(p) for p in groups) else ""
        body.append(f"{indent}{_term_label(term)} & {' & '.join(cells)} \\\\")
    return _tex("tab_fixed_effects.tex", "\n".join(body) + "\n")


def tab_models(data: dict) -> Path:
    baseline = data["baseline"]["forms"]
    body = []
    for key, label in (("linear", "Duration curve, linear"), ("log", "Duration curve, logarithmic"),
                       ("saturating", "Duration curve, saturating")):
        form = baseline[key]
        body.append(f"{label} & {form['mae']:.2f} & {_ci(form['ci95']['low'], form['ci95']['high'])} & "
                    f"{form['rmse']:.2f} & {'reference' if key == 'log' else _num((baseline['log']['mae'] - form['mae']) / baseline['log']['mae'] * 100, 1, signed=True) + '\\%'} & "
                    f"{form['r2_pooled']:.2f} & {CAMPAIGNS.get(form['worst_fold']['cohort'], form['worst_fold']['cohort'])} ({form['worst_fold']['mae']:.1f}) \\\\")
    body.append("\\addlinespace")
    for _, model in data["models"].iloc[1:].sort_values("loco_mae_pp").iterrows():
        body.append(f"{MODEL_LABELS[model['model']]} & {model['loco_mae_pp']:.2f} & {_ci(model['ci95_low'], model['ci95_high'])} & "
                    f"{model['rmse_pp']:.2f} & {_num(model['vs_baseline_relative'] * 100, 1, signed=True)}\\% & "
                    f"{model['r2_pooled']:.2f} & {CAMPAIGNS.get(model['worst_fold_cohort'], model['worst_fold_cohort'])} ({model['worst_fold_mae_pp']:.1f}) \\\\")
    return _tex("tab_models.tex", "\n".join(body) + "\n")


def tab_importance(data: dict) -> Path:
    table = data["importance"]
    table = table[table["folds_in_top_k"] > 0]
    body = "\n".join(
        f"{_term_label(row['feature'].replace('duration_saturating', 'duration_saturating'))} & "
        f"{int(row['folds_in_top_k'])} of 32 & {100 * row['share']:.0f}\\% & {row['mean_importance']:.2f} \\\\"
        for _, row in table.iterrows()
    )
    return _tex("tab_importance.tex", body + "\n")


FORECAST_MODELS = {
    "jev": "Jev (TypeSafe)",
    "duration_curve": "Duration curve",
    "last_scan": "Last scan",
    "last_scan_plus_curve": "Last scan plus curve step",
}


def tab_forecast(data: dict) -> Path:
    table = data["comparison"]
    body = []
    for arm, heading in (("without_history", "Without history: percent change from baseline"),
                         ("with_history", "With history: change since the previous scan")):
        rows = table[table["arm"] == arm]
        first = rows.iloc[0]
        body.append(f"\\addlinespace\n\\multicolumn{{8}}{{@{{}}l}}{{\\textit{{{heading} "
                    f"({int(first['rows'])} rows, {int(first['folds'])} campaigns)}}}} \\\\")
        for _, row in rows.iterrows():
            name = FORECAST_MODELS[row["model"]] + ("$^{\\dagger}$" if row["is_reference"] else "")
            body.append(f"\\quad {name} & {row['mae_pp']:.2f} & {_ci(row['mae_ci95_low'], row['mae_ci95_high'])} & "
                        f"{row['crps_pp']:.2f} & {row['log_score']:.2f} & "
                        f"{100 * row['coverage_50']:.0f}\\% / {row['width_50_pp']:.1f} & "
                        f"{100 * row['coverage_80']:.0f}\\% / {row['width_80_pp']:.1f} & {_num(row['r2_pooled'], 2)} \\\\")
    return _tex("tab_forecast.tex", "\n".join(body) + "\n")


def tab_ablation(data: dict) -> Path:
    table = data["ablation_table"]
    body = []
    for _, row in table.iterrows():
        name = ABLATION_LABELS.get(row["variant"], "Duration curve (reference)")
        if row["variant"] == "duration_curve":
            body.append(f"\\addlinespace\n{name} & {row['mae_pp']:.2f} & {row['crps_pp']:.2f} & "
                        f"{100 * row['coverage_80']:.0f}\\% & --- & --- & --- \\\\")
            continue
        change = ("---" if row["variant"] == "full" else
                  f"{_num(row['paired_mae_change_vs_full_pp'], 2, signed=True)} ({_ci(row['paired_mae_change_vs_full_pp_low'], row['paired_mae_change_vs_full_pp_high'])})")
        body.append(f"{name} & {row['mae_pp']:.2f} & {row['crps_pp']:.2f} & {100 * row['coverage_80']:.0f}\\% & "
                    f"{_num(row['paired_mae_gain_vs_curve_pp'], 2, signed=True)} ({_ci(row['paired_mae_gain_vs_curve_pp_low'], row['paired_mae_gain_vs_curve_pp_high'])}) & "
                    f"{change} & {int(row['campaigns_better_than_curve'])} of 32 \\\\")
    return _tex("tab_ablation.tex", "\n".join(body) + "\n")


def tab_validation(data: dict) -> Path:
    table = data["validation_table"]
    body = []
    for arm, heading in (("without_history", "Without history (346 rows, 32 campaigns; reference: duration curve)"),
                         ("with_history", "With history (84 rows, 5 campaigns; reference: last scan plus curve step)")):
        body.append(f"\\addlinespace\n\\multicolumn{{5}}{{@{{}}l}}{{\\textit{{{heading}}}}} \\\\")
        for _, row in table[table["arm"] == arm].iterrows():
            change = ("---" if row["variant"] == "full" else
                      f"{_num(row['change_vs_full_pp'], 2, signed=True)} ({_ci(row['change_vs_full_low'], row['change_vs_full_high'])})")
            body.append(f"\\quad {ABLATION_LABELS[row['variant']]} & {row['jev_mae_pp']:.2f} & {row['reference_mae_pp']:.2f} & "
                        f"{_num(row['paired_gain_pp'], 2, signed=True)} ({_ci(row['paired_gain_low'], row['paired_gain_high'])}) & {change} \\\\")
    return _tex("tab_validation.tex", "\n".join(body) + "\n")


def tab_recognition(data: dict) -> Path:
    table = data["recognition"].sort_values("paired_mae_gain_pp", ascending=False)
    labels = {_slug(v): v for v in data["config"]["forecast"]["ablation"]["recognition"]["campaigns"].values()}
    labels["none_of_these_campaigns"] = "None of these"
    body = "\n".join(
        f"{CAMPAIGNS.get(row['cohort'], row['cohort'])} & {int(row['rows'])} & {row['mean_p_true']:.2f} & "
        f"{100 * row['top1']:.0f}\\% & {_escape(labels.get(row['top_choice'], row['top_choice']))} & "
        f"{_num(row['paired_mae_gain_pp'], 2, signed=True)} \\\\"
        for _, row in table.iterrows()
    )
    return _tex("tab_recognition.tex", body + "\n")


def _slug(name: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def tab_campaigns(data: dict) -> Path:
    frame, resolved = data["dataset"], data["A"]
    cohorts = data["cohorts"].set_index("cohort_id")
    grouped = frame.groupby("cohort_id")
    table = pd.DataFrame({
        "design": grouped["design"].first(),
        "planned": grouped["duration_days"].max(),
        "studies": grouped["study_id"].agg(lambda s: sorted(set(s))),
        "rows": grouped.size(),
        "rows_a": resolved.groupby("cohort_id").size(),
        "modality": grouped["modality"].agg(lambda s: ", ".join(sorted(set(s)))),
    }).fillna({"rows_a": 0}).sort_values(["planned", "rows"])
    body = []
    for cohort, row in table.iterrows():
        cites = ",".join(s for s in row["studies"] if s != "nlsp_mr035g_c3")
        cite = f"\\cite{{{cites}}}" if cites else ""
        if "nlsp_mr035g_c3" in row["studies"]:
            cite = (cite + " " if cite else "") + "\\cite{nlsp2026}"
        name = CAMPAIGNS.get(cohort, cohort)
        registry = cohorts.loc[cohort, "registry_id"] if cohort in cohorts.index else "NA"
        registry = "" if (not isinstance(registry, str) or registry == "NA") else f" \\newline {{\\scriptsize {registry}}}"
        body.append(f"{name}{registry} & {DESIGN_SHORT.get(row['design'], row['design'])} & {int(row['planned'])} & "
                    f"{len(row['studies'])} {cite} & {row['modality']} & {int(row['rows'])} & {int(row['rows_a'])} \\\\")
    return _tex("tab_campaigns.tex", "\n".join(body) + "\n")


def tab_muscle_map(data: dict) -> Path:
    table = data["muscle_map"].sort_values(["muscle_family", "muscle"])
    classes = {"antigravity_extensor": "Antigravity", "mixed": "Mixed", "flexor": "Flexor"}
    body = "\n".join(
        f"{_escape(row['muscle']).replace(chr(92) + '_', ' ')} & {FAMILY_LABELS.get(row['muscle_family'], _escape(row['muscle_family']))} & "
        f"{classes.get(row['muscle_function_class'], row['muscle_function_class'])} & "
        f"{_escape(str(row['fibre_profile']).replace('_', ' '))} & {_escape(row['rationale'])} \\\\"
        for _, row in table.iterrows()
    )
    return _tex("tab_muscle_map.tex", body + "\n")


def tab_class_means(data: dict) -> Path:
    """Unadjusted control-arm means by functional class, on the rows before resolution."""
    modelled = data["modelled"]
    control = modelled[modelled["arm_type"] == "control"]
    means = control.groupby("muscle_function_class")["pct_change"].agg(["size", "mean"])
    body = "\n".join(
        f"{CLASS_LABELS[name]} & {int(means.loc[name, 'size'])} & {_num(means.loc[name, 'mean'], 1)} \\\\"
        for name in ("antigravity_extensor", "mixed", "flexor")
    )
    return _tex("tab_class_means.tex", body + "\n")


def main() -> int:
    _style()
    FIGURES.mkdir(exist_ok=True)
    GENERATED.mkdir(exist_ok=True)
    data = load()
    written = [
        fig_campaigns(data), fig_duration(data), fig_ranking(data), fig_models(data),
        fig_jev_campaigns(data), fig_jev_checks(data), fig_jev_scatter(data), fig_recognition(data),
        tab_dataset(data), tab_subsets(data), tab_tier1_forms(data), tab_curve(data),
        tab_variance(data), tab_ranking(data), tab_fixed_effects(data), tab_models(data),
        tab_importance(data), tab_forecast(data), tab_ablation(data), tab_validation(data),
        tab_recognition(data), tab_campaigns(data), tab_muscle_map(data), tab_class_means(data),
    ]
    for path in written:
        print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
