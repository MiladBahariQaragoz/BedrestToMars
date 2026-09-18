"""Render the figures that hold muscle results, so their values can be read.

    python framework/render_figures.py [record_id ...]

Twenty-four included studies publish their muscle outcomes only as bar charts. This finds
the figures whose captions mention a muscle outcome and renders the page each one sits on at
high resolution into resources/figures/ (gitignored, like the rest of resources/).

For a PDF the page is rendered directly. For a Europe PMC XML the figure images are not in
the XML, so the record is reported as needing its publisher PDF instead.

Reading a value off a rendered chart is an estimate, not a measurement. Anything recovered
this way belongs in data/raw/extraction_figures.csv with `data_source = figure_digitized`,
a `digitizer_tool` naming how it was read, and confidence no higher than medium.
"""

from __future__ import annotations

import csv
import glob
import html
import re
import sys
from pathlib import Path

import fitz

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING = REPO_ROOT / "data" / "search" / "screening.csv"
FIGURE_DIR = REPO_ROOT / "resources" / "figures"

csv.field_size_limit(10_000_000)

MUSCLE_FIGURE = re.compile(
    r"muscle volume|muscle mass|muscle size|cross[- ]?sectional area|\bCSA\b|lean mass|"
    r"lean tissue|muscle thickness|quadriceps|soleus|gastrocnemi|vastus|triceps surae|"
    r"plantar ?flexor|thigh|calf|multifidus|hamstring|atrophy", re.IGNORECASE)

# Captions that mention a muscle but are clearly not results.
NOT_RESULTS = re.compile(r"study (design|overview|timeline)|experimental design|flow ?chart|"
                         r"representative (image|slice|scan)|schematic|CONSORT", re.IGNORECASE)


def flatten(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", fragment)))


def figure_captions_pdf(path: Path) -> list:
    """Return (page number, caption) for every figure caption mentioning a muscle."""
    found = []
    with fitz.open(path) as document:
        for number, page in enumerate(document):
            text = re.sub(r"\s+", " ", page.get_text())
            for match in re.finditer(r"(FIG(?:URE)?\.?\s*\d+[.:]?\s)(.{0,220})", text, re.IGNORECASE):
                caption = match.group(0)
                if MUSCLE_FIGURE.search(caption) and not NOT_RESULTS.search(caption):
                    found.append((number, caption.strip()))
    return found


def render(path: Path, pages: list, stem: str) -> list:
    written = []
    with fitz.open(path) as document:
        for number in sorted(set(pages)):
            if number >= document.page_count:
                continue
            pixmap = document[number].get_pixmap(dpi=190)
            target = FIGURE_DIR / f"{stem}_p{number + 1}.png"
            pixmap.save(target)
            written.append(target)
    return written


def main() -> int:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    screening = list(csv.DictReader(SCREENING.open(encoding="utf-8-sig")))
    wanted = sys.argv[1:]
    if wanted:
        records = [r for r in screening if r["record_id"] in wanted]
    else:
        records = [r for r in screening if r["screen_ft"] == "maybe"]

    for row in records:
        matches = glob.glob(str(REPO_ROOT / f"resources/fulltext/*{row['record_id']}*"))
        if not matches:
            print(f"{row['record_id']:14s} no full text")
            continue
        path = Path(matches[0])
        if path.suffix != ".pdf":
            print(f"{row['record_id']:14s} XML only - the figure images are not in the XML; "
                  "fetch the publisher PDF to digitise this one")
            continue

        captions = figure_captions_pdf(path)
        if not captions:
            print(f"{row['record_id']:14s} no muscle figure caption found")
            continue

        pages = [number for number, _caption in captions]
        written = render(path, pages, path.stem)
        print(f"{row['record_id']:14s} {len(captions)} caption(s) on {len(written)} page(s)")
        for _number, caption in captions[:3]:
            print(f"    {caption[:150]}")
        for target in written:
            print(f"    -> {target.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
