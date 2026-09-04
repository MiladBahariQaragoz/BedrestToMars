"""Sort the pending studies by whether their numbers can actually be read.

    python framework/triage_extractable.py

For every study still awaiting extraction, this asks one question: where do the muscle
numbers live? A paper with a results table can be extracted in minutes. A paper whose
muscle outcome exists only in a figure needs WebPlotDigitizer or an email to the authors,
and finding that out one paper at a time is slow.

Three verdicts:

    table    a table carries a muscle term together with numbers
    text     no such table, but a sentence gives a percent change
    figure   a figure caption mentions a muscle outcome and nothing else does

Prints a ranked list and writes nothing, so it is safe to run at any time. Acting on the
verdict - extracting, or recording a full-text decision - stays a human judgement.
"""

from __future__ import annotations

import csv
import html
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING = REPO_ROOT / "data" / "search" / "screening.csv"
EXTRACTION = REPO_ROOT / "data" / "raw" / "extraction_falk.csv"
FULLTEXT_DIR = REPO_ROOT / "resources" / "fulltext"

csv.field_size_limit(10_000_000)

MUSCLE = re.compile(
    r"(muscle volume|muscle mass|muscle size|cross[- ]sectional area|\bCSA\b|\bACSA\b|"
    r"lean mass|lean tissue|muscle thickness|quadriceps|soleus|gastrocnemi|vastus|"
    r"triceps surae|plantar ?flexor|thigh|calf)", re.IGNORECASE)
NUMERIC = re.compile(r"\d+(?:\.\d+)?\s*±\s*\d|\d+(?:\.\d+)?\s?%")
PERCENT_SENTENCE = re.compile(
    r"[^.]{0,110}(muscle volume|muscle mass|muscle size|CSA|lean mass|thickness|quadriceps|"
    r"soleus|gastrocnemi|thigh|calf)[^.]{0,110}(-|−)?\d+(\.\d+)?\s?%[^.]{0,80}\.", re.IGNORECASE)


def safe_name(row: dict) -> str:
    author = (row["authors"].split(",")[0].split(";")[0] or "anon").strip().lower()
    author = "".join(character for character in author if character.isalnum())[:20]
    return f"{author or 'anon'}{row['year']}_{row['record_id']}"


def flatten(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", fragment)))


def classify(path: Path) -> tuple:
    """Return (verdict, detail)."""
    if path.suffix == ".pdf":
        try:
            import fitz
            with fitz.open(path) as document:
                text = " ".join(page.get_text() for page in document)
        except Exception as error:
            return "unreadable", type(error).__name__
        text = re.sub(r"\s+", " ", text)
        sentences = PERCENT_SENTENCE.findall(text)
        if sentences:
            return "text", f"{len(sentences)} percent sentences"
        # A PDF has no table markup, so a flattened results table looks like a muscle term
        # sitting near a mean and a dispersion. That is still extractable, by eye.
        near = re.findall(r"(?:muscle volume|muscle mass|lean mass|CSA|thickness|quadriceps|"
                          r"soleus|gastrocnemi|thigh|calf)[^.]{0,80}\d+(?:\.\d+)?\s*±\s*\d",
                          text, re.IGNORECASE)
        if near:
            return "pdf-table", f"{len(near)} muscle values with a dispersion"
        return "unknown", "no percent sentences and no muscle value with a dispersion"

    raw = path.read_text(encoding="utf-8", errors="replace")
    tables = re.findall(r"<table-wrap\b.*?</table-wrap>", raw, re.S)
    good_tables = [t for t in tables
                   if MUSCLE.search(flatten(t)) and NUMERIC.search(flatten(t))]
    if good_tables:
        caption = flatten(good_tables[0])[:90]
        return "table", f"{len(good_tables)} table(s): {caption}"

    body = flatten(raw)
    sentences = PERCENT_SENTENCE.findall(body)
    if sentences:
        return "text", f"{len(sentences)} percent sentences"

    figures = [flatten(c) for c in re.findall(r"<fig .*?<caption>(.*?)</caption>", raw, re.S)]
    muscle_figures = [c for c in figures if MUSCLE.search(c)]
    if muscle_figures:
        return "figure", muscle_figures[0][:90]
    return "unknown", f"{len(tables)} tables, {len(figures)} figures, no muscle numbers found"


def main() -> int:
    screening = list(csv.DictReader(SCREENING.open(encoding="utf-8-sig")))
    extraction = list(csv.DictReader(EXTRACTION.open(encoding="utf-8-sig")))
    sources = {row["source_file"] for row in extraction}
    done = {row["record_id"] for row in screening
            if any(row["record_id"] in source for source in sources)}

    pending = [r for r in screening
               if r["screen_ta"] == "include" and r["screen_ft"] not in {"exclude", "maybe"}
               and r["record_id"] not in done]

    verdicts = Counter()
    results = []
    for row in pending:
        stem = safe_name(row)
        path = None
        for suffix in (".xml", ".pdf"):
            candidate = FULLTEXT_DIR / f"{stem}{suffix}"
            if candidate.exists():
                path = candidate
                break
        if path is None:
            verdicts["no file"] += 1
            continue
        verdict, detail = classify(path)
        verdicts[verdict] += 1
        results.append((verdict, row, detail))

    order = {"table": 0, "pdf-table": 1, "text": 2, "figure": 3, "unknown": 4, "unreadable": 5}
    results.sort(key=lambda item: (order.get(item[0], 9), -int(item[1]["year"] or 0)))

    for verdict, row, detail in results:
        print(f"{verdict:10s} {row['record_id']:14s} {row['title'][:52]:52s} {detail[:70]}")
    print()
    print("  ".join(f"{name}: {count}" for name, count in verdicts.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
