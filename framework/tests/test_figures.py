"""Checks on the five figures of PLAN.md section 9.

    python framework/tests/test_figures.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.text
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import plot_figures

CONFIG = data_loader.load_config()
INPUTS = plot_figures.load_inputs(CONFIG)
FIGURES = {name: draw(INPUTS) for name, draw in plot_figures.FIGURES.items()}


def _undrawn_tick_labels(figure) -> set[int]:
    """Tick labels matplotlib keeps for locations outside the view, and never draws."""
    hidden: set[int] = set()
    for axis in figure.axes:
        for scale, limits in ((axis.xaxis, axis.get_xlim()), (axis.yaxis, axis.get_ylim())):
            low, high = sorted(limits)
            for tick in scale.get_major_ticks():
                if not low - 1e-9 <= tick.get_loc() <= high + 1e-9:
                    hidden.update({id(tick.label1), id(tick.label2)})
    return hidden


def _texts(figure) -> list[matplotlib.text.Text]:
    hidden = _undrawn_tick_labels(figure)
    return [
        text for text in figure.findobj(matplotlib.text.Text)
        if text.get_visible() and text.get_text().strip() and id(text) not in hidden
    ]


def _joined(figure) -> str:
    return " ".join(text.get_text() for text in _texts(figure))


def test_the_figure_set_is_the_declared_one() -> None:
    assert list(FIGURES) == [
        "F1_corpus", "F1b_campaigns", "F2_duration", "F3_muscles", "F4_framework",
        "F5_models", "F6_jev_campaigns", "F7_jev_checks", "F8_jev_scatter", "F9_jev_example",
    ]


def test_every_figure_is_drawn_on_a_full_slide_canvas() -> None:
    for name, figure in FIGURES.items():
        width, height = figure.get_size_inches()
        assert (round(width, 2), round(height, 2)) == (13.33, 7.5), name


def test_no_text_is_smaller_than_slide_body_text() -> None:
    """PLAN.md section 9: figure text at least as large as the 24 pt slide body."""
    for name, figure in FIGURES.items():
        small = [(t.get_text(), t.get_fontsize()) for t in _texts(figure) if t.get_fontsize() < 24]
        assert not small, (name, small[:5])


def _extent(artist, figure):
    return artist.get_window_extent(figure.canvas.get_renderer())


def test_no_text_runs_off_the_canvas() -> None:
    for name, figure in FIGURES.items():
        figure.canvas.draw()
        bounds = figure.bbox
        outside = [
            text.get_text() for text in _texts(figure)
            if (box := _extent(text, figure)).x0 < bounds.x0 - 1 or box.x1 > bounds.x1 + 1
            or box.y0 < bounds.y0 - 1 or box.y1 > bounds.y1 + 1
        ]
        assert not outside, (name, outside)


def test_no_text_lands_on_a_chart_it_does_not_belong_to() -> None:
    for name, figure in FIGURES.items():
        figure.canvas.draw()
        charts = [axis for axis in figure.axes if axis.axison]
        for text in _texts(figure):
            box = _extent(text, figure)
            for axis in charts:
                if text.axes is axis or text in axis.texts:
                    continue
                if text.axes is None and text in (axis.title, axis.xaxis.label, axis.yaxis.label):
                    continue
                if any(text is label for label in axis.get_xticklabels() + axis.get_yticklabels()):
                    continue
                assert not box.overlaps(axis.get_window_extent()), (name, text.get_text())


def test_every_data_figure_states_its_sample_on_the_figure() -> None:
    for name in FIGURES:
        if name != "F4_framework":
            assert "campaign" in _joined(FIGURES[name]), name


def test_the_duration_figure_uses_only_the_three_validated_colours() -> None:
    allowed = {mcolors.to_hex(colour) for colour in plot_figures.SERIES}
    used = set()
    for collection in FIGURES["F2_duration"].axes[0].collections:
        for colour in collection.get_facecolors():
            if colour[3] > 0.5:
                used.add(mcolors.to_hex(colour[:3]))
    assert used and used <= allowed, used - allowed


def test_the_muscle_figure_shows_every_family_in_the_ranking() -> None:
    ranking = pd.read_csv(REPO_ROOT / "results" / "tier1_muscle_ranking.csv")
    labels = [label.get_text() for label in FIGURES["F3_muscles"].axes[0].get_yticklabels()]
    expected = [plot_figures.words(family) for family in ranking["muscle_family"]]
    assert sorted(labels) == sorted(expected)


def test_the_model_figure_shows_every_model_and_a_line_at_the_baseline() -> None:
    text = _joined(FIGURES["F5_models"])
    for label in plot_figures.MODEL_LABELS.values():
        assert label in text, label
    baseline = INPUTS["baseline"]["forms"]["log"]["mae"]
    axis = FIGURES["F5_models"].axes[0]
    vertical = [line for line in axis.lines if len(set(line.get_xdata())) == 1]
    assert any(abs(line.get_xdata()[0] - baseline) < 1e-9 for line in vertical)


def test_the_model_figure_adds_tabpfn_as_post_hoc_in_its_own_colour() -> None:
    """TabPFN was added after the null result: it sits on F5 at its own error, labelled post hoc
    and coloured apart from the four declared families, so nobody reads it as one of them."""
    import json

    record = json.loads((REPO_ROOT / "results" / "tabpfn_comparison.json").read_text(encoding="utf-8"))
    tabpfn_mae = record["models"]["tabpfn"]["mae"]
    forest_mae = INPUTS["models"].set_index("model").loc["random_forest", "loco_mae_pp"]

    import matplotlib.collections

    axis = FIGURES["F5_models"].axes[0]
    points = next(c for c in axis.collections if isinstance(c, matplotlib.collections.PathCollection))
    offsets = points.get_offsets()
    colours = points.get_facecolors()
    labels = {tick.get_loc(): tick.label1.get_text() for tick in axis.yaxis.get_major_ticks()}

    at_tabpfn = [i for i, (x, _) in enumerate(offsets) if abs(x - tabpfn_mae) < 1e-9]
    at_forest = [i for i, (x, _) in enumerate(offsets) if abs(x - forest_mae) < 1e-9]
    assert len(at_tabpfn) == 1, "TabPFN must be drawn exactly once, at its own error"
    assert labels[offsets[at_tabpfn[0]][1]] == "TabPFN (post hoc)"
    assert not mcolors.same_color(colours[at_tabpfn[0]], colours[at_forest[0]])


def test_the_framework_diagram_names_the_three_tiers() -> None:
    text = _joined(FIGURES["F4_framework"])
    for stage in ("Tier 1", "Tier 2", "Tier 3", "leave-one-campaign-out"):
        assert stage in text, stage


def test_the_screening_counts_are_counted_from_the_search_tables() -> None:
    """The numbers docs/literature-review/prisma_counts.md reports, re-counted from the rows."""
    counts = plot_figures.screening_counts()
    assert counts["identified"] == 5731
    assert counts["duplicates"] == 2141
    assert counts["screened"] == 3590
    assert counts["excluded"] == 2493
    assert counts["included"] == 74
    assert counts["not_yet_screened"] == 1023


def test_the_row_funnel_is_counted_from_the_data() -> None:
    assert plot_figures.row_funnel(INPUTS) == {
        "all": 742, "recovery": 264, "trunk": 53, "counted_twice": 79, "modelled": 346,
    }


def test_the_corpus_figure_walks_from_every_row_to_the_modelled_ones_and_says_why() -> None:
    text = _joined(FIGURES["F1_corpus"])
    for part in ("742", "264", "53", "79", "346", "recovery", "trunk", "counted twice"):
        assert part in text, part


def test_the_campaign_figure_has_one_bar_per_campaign() -> None:
    axis = FIGURES["F1b_campaigns"].axes[0]
    assert len(axis.patches) == INPUTS["resolved"]["cohort_id"].nunique()


def _jev_gains() -> pd.Series:
    rows = pd.read_csv(REPO_ROOT / "results" / "forecast_predictions.csv")
    rows = rows[rows["arm"] == "without_history"]
    errors = rows.groupby(["cohort", "model"])["abs_error"].mean().unstack()
    return errors["duration_curve"] - errors["jev"]


def test_the_jev_campaign_figure_has_a_bar_for_each_held_out_campaign() -> None:
    gains = _jev_gains()
    axis = FIGURES["F6_jev_campaigns"].axes[0]
    heights = sorted(round(patch.get_height(), 9) for patch in axis.patches)
    assert heights == sorted(round(value, 9) for value in gains)
    assert f"{int((gains > 0).sum())} of {len(gains)}" in _joined(FIGURES["F6_jev_campaigns"])


def test_the_checks_figure_plots_every_scenario_at_its_recorded_gain() -> None:
    ablation = INPUTS["ablation"]["variants"]
    validation = INPUTS["validation"]["runs"]["without_history"]
    expected = {
        "full": ablation["full"]["paired_mae_gain_vs_curve_pp"]["point"],
        "generic": ablation["generic"]["paired_mae_gain_vs_curve_pp"]["point"],
        "reordered": validation["reordered"]["paired_mae_gain_vs_reference_pp"]["point"],
        "shifted_bins": validation["shifted_bins"]["paired_mae_gain_vs_reference_pp"]["point"],
        "scrambled_reference": ablation["scrambled_reference"]["paired_mae_gain_vs_curve_pp"]["point"],
        "no_reference": ablation["no_reference"]["paired_mae_gain_vs_curve_pp"]["point"],
    }
    plotted = plot_figures.check_rows(INPUTS)
    assert dict(zip(plotted["key"], plotted["gain"])) == expected
    labels = [label.get_text() for label in FIGURES["F7_jev_checks"].axes[0].get_yticklabels()]
    assert sorted(labels) == sorted(plotted["label"])


def test_the_scatter_figure_shows_the_curve_and_jev_on_every_row() -> None:
    axes = FIGURES["F8_jev_scatter"].axes
    assert len(axes) == 2
    for axis in axes:
        assert sum(len(c.get_offsets()) for c in axis.collections) == 346


def test_the_example_is_chosen_by_a_rule_not_by_hand() -> None:
    """The row whose Jev error sits closest to Jev's median error: typical, not flattering."""
    rows = pd.read_csv(REPO_ROOT / "results" / "forecast_predictions.csv")
    jev = rows[(rows["arm"] == "without_history") & (rows["model"] == "jev")]
    distance = (jev["abs_error"] - jev["abs_error"].median()).abs()
    expected = jev.loc[distance.sort_values(kind="stable").index[0], "row_id"]
    assert plot_figures.example_row(INPUTS) == expected
    axis = FIGURES["F9_jev_example"].axes[0]
    assert len(axis.patches) == 2 * plot_figures.forecast.arm_bins(CONFIG, "without_history").count


def test_render_all_writes_an_svg_and_a_png_for_every_figure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        written = plot_figures.render_all(Path(tmp), CONFIG)
        for name in FIGURES:
            for suffix in (".svg", ".png"):
                path = Path(tmp) / f"{name}{suffix}"
                assert path in written and path.stat().st_size > 1000, path


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as error:
            failures += 1
            print(f"FAIL {test.__name__}: {type(error).__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
