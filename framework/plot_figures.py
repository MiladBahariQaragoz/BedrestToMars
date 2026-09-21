"""Draw the five figures of PLAN.md section 9 from the results files.

    python framework/plot_figures.py        # writes figures/F1_corpus ... F5_models, SVG and PNG

Every number drawn is read from `results/` or counted from `data/`; none is typed here, and
every title is computed from the numbers it states, so a refit cannot leave a stale claim on a
slide.

Each figure is drawn on a full 16:9 slide, 13.33 by 7.5 inches, so it can be placed at 1:1 and
no text falls below the 24 pt slide body (`PLAN.md` task 5.9). Colours come from the dataviz
reference palette: its first three categorical slots, which pass the colourblind checks for
every pair at once, the only use in which three colours share a scatter. Everything else is
ink and grey, with one accent for the thing a figure is about.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

import data_loader
import features

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS = REPO_ROOT / "results"
SEARCH = REPO_ROOT / "data" / "search"

FIGSIZE = (13.333, 7.5)
BODY = 24
TITLE = 28

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")   # validated all-pairs, light surface
ACCENT = SERIES[0]

SHORT_CLASS_LABELS = {
    "antigravity_extensor": "Antigravity",
    "mixed": "Mixed",
    "flexor": "Flexors",
}
MODEL_LABELS = {
    "duration_only": "Duration curve",
    "ridge": "Ridge regression",
    "random_forest": "Random forest",
    "svr": "Support vector",
    "gradient_boosting": "Gradient boosting",
    "jev": "Jev (TypeSafe)",
}


def words(value: Any) -> str:
    text = str(value).replace("_", " ")
    return text[:1].upper() + text[1:]


def _smaller(value: float) -> str:
    """A signed percent change as words: -11.4 is "11% smaller", +2 is "2% larger"."""
    return f"{abs(value):.0f}% {'smaller' if value < 0 else 'larger'}"


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": ["Segoe UI", "DejaVu Sans"],
            "font.size": BODY,
            "axes.titlesize": TITLE,
            "axes.labelsize": BODY,
            "xtick.labelsize": BODY,
            "ytick.labelsize": BODY,
            "legend.fontsize": BODY,
            "legend.title_fontsize": BODY,
            "axes.edgecolor": AXIS,
            "axes.linewidth": 1.0,
            "axes.labelcolor": INK_2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": AXIS,
            "ytick.color": AXIS,
            "xtick.labelcolor": INK_2,
            "ytick.labelcolor": INK_2,
            "text.color": INK,
            "grid.color": GRID,
            "grid.linewidth": 1.0,
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "svg.fonttype": "path",
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
        }
    )


def _figure() -> plt.Figure:
    _style()
    return plt.figure(figsize=FIGSIZE)


def _title(figure: plt.Figure, title: str, subtitle: str | None = None) -> None:
    figure.text(0.03, 0.955, title, fontsize=TITLE, fontweight="semibold", color=INK, va="top")
    if subtitle:
        figure.text(0.03, 0.885, subtitle, fontsize=BODY, color=INK_2, va="top")


# --- inputs -----------------------------------------------------------------------------


def screening_counts() -> dict[str, int]:
    """The flow-diagram counts, counted from the search tables rather than copied."""
    records = pd.read_csv(SEARCH / "all_records.csv", dtype=str, keep_default_na=False)
    screening = pd.read_csv(SEARCH / "screening.csv", dtype=str, keep_default_na=False)
    decision = screening["screen_ta"]
    return {
        "identified": int(len(records)),
        "duplicates": int((records["duplicate_of"] != "").sum()),
        "screened": int(len(screening)),
        "excluded": int((decision == "exclude").sum()),
        "included": int((decision == "include").sum()),
        "not_yet_screened": int(decision.isin(["", "maybe"]).sum()),
    }


def _json(name: str) -> dict[str, Any]:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def load_inputs(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or data_loader.load_config()
    dataset = data_loader.load(config)
    resolved = features.resolve(data_loader.subset(dataset, config), config, subset="A")
    return {
        "config": config,
        "dataset": dataset,
        "resolved": resolved,
        "tier1": _json("tier1_curve.json"),
        "ranking": pd.read_csv(RESULTS / "tier1_muscle_ranking.csv"),
        "baseline": _json("baseline.json"),
        "models": pd.read_csv(RESULTS / "model_comparison.csv"),
        "forecast": _json("forecast.json"),
        "screening": screening_counts(),
    }


# --- F1: the corpus ---------------------------------------------------------------------


def _box(axis, x: float, y: float, width: float, height: float, lines: list[str],
         accent: bool = False) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0,rounding_size=0.12",
            facecolor=(ACCENT, 0.10) if accent else "#ffffff",
            edgecolor=ACCENT if accent else AXIS, linewidth=1.5,
        )
    )
    step = 0.42
    top = y + height / 2 + step * (len(lines) - 1) / 2
    for index, line in enumerate(lines):
        axis.text(
            x + width / 2, top - index * step, line, ha="center", va="center",
            fontsize=BODY, fontweight="semibold" if index == 0 else "normal",
            color=INK if index == 0 else INK_2,
        )


def _arrow(axis, start: tuple[float, float], end: tuple[float, float]) -> None:
    axis.annotate(
        "", xy=end, xytext=start,
        arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 2, "mutation_scale": 22},
    )


def _canvas(figure: plt.Figure, rect: list[float], width: float, height: float):
    axis = figure.add_axes(rect)
    axis.set_xlim(0, width)
    axis.set_ylim(0, height)
    axis.axis("off")
    return axis


def f1_corpus(inputs: dict[str, Any]) -> plt.Figure:
    counts = inputs["screening"]
    dataset, resolved = inputs["dataset"], inputs["resolved"]
    time = inputs["config"]["features"]["time_column"]
    campaigns = int(resolved["cohort_id"].nunique())

    figure = _figure()
    _title(
        figure,
        f"From {counts['identified']:,} records to {campaigns} modelled campaigns",
    )

    flow = _canvas(figure, [0.02, 0.02, 0.50, 0.84], 6.6, 6.3)
    rows = [
        (5.35, [f"{counts['identified']:,} records found"], f"{counts['duplicates']:,} duplicates"),
        (4.05, [f"{counts['screened']:,} screened"], f"{counts['not_yet_screened']:,} not yet"),
        (2.75, [f"{counts['included']} read in full"], None),
        (1.45, [f"{dataset['study_id'].nunique()} studies,",
                f"{dataset['cohort_id'].nunique()} campaigns"], "+ prior papers\n+ NASA archive"),
        (0.15, [f"{len(resolved)} rows, {campaigns} campaigns"], None),
    ]
    for index, (y, lines, aside) in enumerate(rows):
        height = 0.95 if len(lines) == 1 else 1.15
        top = y + height
        _box(flow, 0.2, y, 4.3, height, lines, accent=index == len(rows) - 1)
        if aside:
            flow.text(4.75, y + height / 2, aside, fontsize=BODY, color=INK_2, va="center")
        if index + 1 < len(rows):
            next_y, next_lines, _ = rows[index + 1]
            next_top = next_y + (0.95 if len(next_lines) == 1 else 1.15)
            _arrow(flow, (2.35, y), (2.35, next_top + 0.02))
        del top

    strip = figure.add_axes([0.60, 0.20, 0.37, 0.62])
    per_campaign = (
        resolved.groupby("cohort_id")
        .agg(planned=("duration_days", "max"), n=("n_analysed", "max"))
        .sort_values("planned")
    )
    positions = np.arange(len(per_campaign))
    strip.barh(positions, per_campaign["planned"], height=0.55, color=ACCENT, alpha=0.85)
    for position, cohort in zip(positions, per_campaign.index):
        days = np.unique(resolved.loc[resolved["cohort_id"] == cohort, time].to_numpy(dtype=float))
        strip.scatter(days, np.full(len(days), position), s=40, color=INK,
                      edgecolors=SURFACE, linewidths=1.5, zorder=3)
    strip.set_yticks([])
    strip.spines["left"].set_visible(False)
    strip.set_xticks([0, 30, 60, 90, 120])
    strip.set_xlabel("Days of bed rest")
    strip.grid(axis="x")
    strip.set_axisbelow(True)
    strip.set_title("One bar per campaign", fontsize=BODY, color=INK_2, loc="left", pad=12)
    figure.text(0.60, 0.035, "Dots mark the scans", fontsize=BODY, color=INK_2)
    return figure


# --- F2: the duration-response ----------------------------------------------------------


def f2_duration(inputs: dict[str, Any]) -> plt.Figure:
    config, resolved, tier1 = inputs["config"], inputs["resolved"], inputs["tier1"]
    time = config["features"]["time_column"]
    control = resolved[resolved["arm_type"] == "control"]
    curve = tier1["curve"]
    days = np.asarray(curve["days"], dtype=float)
    fit = np.asarray(curve["fit"], dtype=float)

    def at(day: float) -> float:
        return float(np.interp(day, days, fit))

    last = int(days.max())
    figure = _figure()
    _title(
        figure,
        f"Muscles shrink with bed rest: {_smaller(at(60))} by day 60, "
        f"{abs(at(last)):.0f}% by day {last}",
        f"{len(control)} control-arm measurements, {control['cohort_id'].nunique()} campaigns",
    )
    axis = figure.add_axes([0.09, 0.14, 0.57, 0.66])
    for (name, label), colour in zip(SHORT_CLASS_LABELS.items(), SERIES):
        rows = control[control["muscle_function_class"] == name]
        axis.scatter(
            rows[time], rows["pct_change"], s=70, color=colour, edgecolors=SURFACE,
            linewidths=1.5, label=f"{label} ({len(rows)})", zorder=2,
        )
    axis.fill_between(days, curve["ci_low"], curve["ci_high"], color=INK_2, alpha=0.12,
                      linewidth=0, zorder=1)
    axis.plot(days, fit, color=INK, linewidth=3, zorder=3)
    axis.axhline(0, color=AXIS, linewidth=1, zorder=0)
    axis.set_xlim(0, 125)
    axis.set_xticks([0, 30, 60, 90, 120])
    axis.set_xlabel("Day of bed rest")
    axis.set_ylabel("Change in muscle size (%)")
    axis.grid(axis="y")
    axis.set_axisbelow(True)
    axis.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False,
                title="Measurements", alignment="left")
    figure.text(0.69, 0.32, "Line: tier-1 curve", fontsize=BODY, color=INK)
    figure.text(0.69, 0.26, "for the reference case,", fontsize=BODY, color=INK_2)
    figure.text(0.69, 0.20, "with its 95% CI", fontsize=BODY, color=INK_2)
    return figure


# --- F3: the muscle ranking -------------------------------------------------------------


def f3_muscles(inputs: dict[str, Any]) -> plt.Figure:
    ranking = inputs["ranking"].sort_values("predicted_pct", ascending=False)
    provenance = inputs["tier1"]["provenance"]["ranking_subset"]
    day = int(inputs["config"]["tier1"]["ranking_days"])
    worst = inputs["ranking"].sort_values("predicted_pct").iloc[0]

    figure = _figure()
    _title(
        figure,
        f"{words(worst['muscle_family'])} shrink most: {_smaller(worst['predicted_pct'])} "
        f"by day {day}",
        f"Tier-1 prediction for a control arm, 95% CI; "
        f"{provenance['rows']} rows, {provenance['cohorts']} campaigns",
    )
    axis = figure.add_axes([0.25, 0.17, 0.50, 0.64])
    positions = np.arange(len(ranking))
    axis.hlines(positions, ranking["predicted_ci_low"], ranking["predicted_ci_high"],
                color=ACCENT, linewidth=3)
    axis.scatter(ranking["predicted_pct"], positions, s=150, color=ACCENT,
                 edgecolors=SURFACE, linewidths=2, zorder=3)
    axis.axvline(0, color=AXIS, linewidth=1)
    axis.set_yticks(positions, [words(family) for family in ranking["muscle_family"]])
    axis.tick_params(axis="y", length=0)
    axis.spines["left"].set_visible(False)
    axis.set_xlabel(f"Change in muscle size by day {day} (%)")
    axis.grid(axis="x")
    axis.set_axisbelow(True)

    figure.text(0.79, 0.075, "rows / campaigns", fontsize=BODY, color=INK_2, va="center")
    for position, (_, row) in zip(positions, ranking.iterrows()):
        y = axis.transData.transform((0, position))[1]
        y = figure.transFigure.inverted().transform((0, y))[1]
        figure.text(0.79, y, f"{int(row['n_rows'])} / {int(row['n_cohorts'])}",
                    fontsize=BODY, color=INK_2, va="center")
    return figure


# --- F4: the framework ------------------------------------------------------------------


def f4_framework(inputs: dict[str, Any]) -> plt.Figure:
    counts, dataset, resolved = inputs["screening"], inputs["dataset"], inputs["resolved"]
    version = inputs["config"]["dataset"]["version"]
    figure = _figure()
    axis = _canvas(figure, [0, 0, 1, 1], 13.333, 7.5)
    axis.text(0.4, 7.0, "One dataset, one validation, three tiers of model",
              fontsize=TITLE, fontweight="semibold", va="center")

    top, middle, bottom = 4.95, 3.05, 1.05
    width, height = 3.9, 1.25
    xs = (0.4, 4.72, 9.03)
    _box(axis, xs[0], top, width, height, ["Literature search", f"{counts['identified']:,} records"])
    _box(axis, xs[1], top, width, height, ["Screening and", "extraction"])
    _box(axis, xs[2], top, width, height, [f"Frozen dataset v{version}", f"{len(dataset)} rows"])
    _arrow(axis, (xs[0] + width, top + height / 2), (xs[1] - 0.03, top + height / 2))
    _arrow(axis, (xs[1] + width, top + height / 2), (xs[2] - 0.03, top + height / 2))

    campaigns = resolved["cohort_id"].nunique()
    folds_w = xs[2] + width - xs[0]
    _box(axis, xs[0], middle, folds_w, height,
         [f"Modelling subset: {len(resolved)} rows, {campaigns} campaigns",
          f"leave-one-campaign-out, {campaigns} folds"])
    _arrow(axis, (xs[2] + width / 2, top), (xs[2] + width / 2, middle + height + 0.03))

    tiers = [["Tier 1", "meta-regression"], ["Tier 2", "four ML families"], ["Tier 3", "Jev forecast"]]
    for x, lines in zip(xs, tiers):
        _box(axis, x, bottom, width, height, lines, accent=True)
        _arrow(axis, (x + width / 2, middle), (x + width / 2, bottom + height + 0.03))
    axis.text(0.4, 0.45, "Tiers 2 and 3 are scored out of campaign against the duration curve",
              fontsize=BODY, color=INK_2, va="center")
    return figure


# --- F5: the model comparison -----------------------------------------------------------


def _model_rows(inputs: dict[str, Any]) -> pd.DataFrame:
    baseline = inputs["baseline"]["forms"]["log"]
    rows = [{"model": "duration_only", "mae": baseline["mae"],
             "low": baseline["ci95"]["low"], "high": baseline["ci95"]["high"]}]
    for _, row in inputs["models"].iterrows():
        if row["model"].startswith("duration_only"):
            continue
        rows.append({"model": row["model"], "mae": row["loco_mae_pp"],
                     "low": row["ci95_low"], "high": row["ci95_high"]})
    jev = inputs["forecast"]["arms"]["without_history"]["models"]["jev"]
    rows.append({"model": "jev", "mae": jev["mae"],
                 "low": jev["mae_ci95"]["low"], "high": jev["mae_ci95"]["high"]})
    return pd.DataFrame(rows)


def f5_models(inputs: dict[str, Any]) -> plt.Figure:
    rows = _model_rows(inputs).sort_values("mae", ascending=False).reset_index(drop=True)
    provenance = inputs["baseline"]["provenance"]
    baseline = float(inputs["baseline"]["forms"]["log"]["mae"])
    best = rows.iloc[-1]

    figure = _figure()
    _title(
        figure,
        f"Lowest out-of-campaign error: {MODEL_LABELS[best['model']]}, {best['mae']:.2f} pp",
        f"Mean absolute error, 95% CI; {provenance['rows']} rows, {provenance['cohorts']} campaigns",
    )
    axis = figure.add_axes([0.30, 0.16, 0.62, 0.66])
    positions = np.arange(len(rows))
    colours = [ACCENT if model == "jev" else (INK if model == "duration_only" else INK_2)
               for model in rows["model"]]
    axis.hlines(positions, rows["low"], rows["high"], colors=colours, linewidth=3)
    axis.scatter(rows["mae"], positions, s=150, c=colours, edgecolors=SURFACE, linewidths=2,
                 zorder=3)
    axis.axvline(baseline, color=INK, linewidth=1)
    axis.set_yticks(positions, [MODEL_LABELS[model] for model in rows["model"]])
    axis.tick_params(axis="y", length=0)
    axis.spines["left"].set_visible(False)
    axis.set_xlabel("Error on the held-out campaign (percentage points)")
    axis.grid(axis="x")
    axis.set_axisbelow(True)
    return figure


FIGURES: dict[str, Callable[[dict[str, Any]], plt.Figure]] = {
    "F1_corpus": f1_corpus,
    "F2_duration": f2_duration,
    "F3_muscles": f3_muscles,
    "F4_framework": f4_framework,
    "F5_models": f5_models,
}


def render_all(directory: Path, config: dict[str, Any] | None = None) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs(config)
    written: list[Path] = []
    for name, draw in FIGURES.items():
        figure = draw(inputs)
        for suffix, options in ((".svg", {}), (".png", {"dpi": 150})):
            path = directory / f"{name}{suffix}"
            figure.savefig(path, **options)
            written.append(path)
        plt.close(figure)
    return written


def main() -> int:
    for path in render_all(REPO_ROOT / "figures"):
        print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
