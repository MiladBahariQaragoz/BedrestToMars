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


def test_there_are_five_figures() -> None:
    assert list(FIGURES) == ["F1_corpus", "F2_duration", "F3_muscles", "F4_framework", "F5_models"]


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
    for name in ("F1_corpus", "F2_duration", "F3_muscles", "F5_models"):
        assert "campaigns" in _joined(FIGURES[name]), name


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
