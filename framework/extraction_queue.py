"""Show what is extracted, what is not, and what to do next.

    python framework/extraction_queue.py

Writes docs/literature-review/extraction_queue.md - the resume point. Any session, at any
time, can read that file and know exactly which studies still need extracting and in what
order, without re-deriving anything.

A study counts as done when at least one row in data/raw/extraction_qaragoz.csv cites its
source file or its record id. Studies excluded at full text are listed separately so nobody
re-reads a paper that was already ruled out.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING = REPO_ROOT / "data" / "search" / "screening.csv"
EXTRACTION = REPO_ROOT / "data" / "raw" / "extraction_qaragoz.csv"
PARTIAL = REPO_ROOT / "data" / "raw" / "extraction_partial.csv"
FULLTEXT_DIR = REPO_ROOT / "resources" / "fulltext"
DIGEST_DIR = REPO_ROOT / "data" / "search" / "fulltext_digests"
QUEUE_MD = REPO_ROOT / "docs" / "literature-review" / "extraction_queue.md"

csv.field_size_limit(10_000_000)


def safe_name(row: dict) -> str:
    author = (row["authors"].split(",")[0].split(";")[0] or "anon").strip().lower()
    author = "".join(character for character in author if character.isalnum())[:20]
    return f"{author or 'anon'}{row['year']}_{row['record_id']}"


def main() -> int:
    screening = list(csv.DictReader(SCREENING.open(encoding="utf-8-sig")))
    extraction = list(csv.DictReader(EXTRACTION.open(encoding="utf-8-sig")))

    partial = list(csv.DictReader(PARTIAL.open(encoding="utf-8-sig"))) if PARTIAL.exists() else []
    partial_sources = {row["source_file"] for row in partial}
    partial_ids = {row["record_id"] for row in screening
                   if any(row["record_id"] in source for source in partial_sources)}

    sources = {row["source_file"] for row in extraction}
    done_ids = {row["record_id"] for row in screening
                if any(row["record_id"] in source for source in sources)}
    study_for = {}
    for row in extraction:
        for record in screening:
            if record["record_id"] in row["source_file"]:
                study_for[record["record_id"]] = row["study_id"]

    included = [r for r in screening if r["screen_ta"] == "include" and r["screen_ft"] != "exclude"]
    excluded_ft = [r for r in screening if r["screen_ft"] == "exclude"]

    done, pending, partially, blocked, missing = [], [], [], [], []
    for row in included:
        stem = safe_name(row)
        has_xml = (FULLTEXT_DIR / f"{stem}.xml").exists()
        has_pdf = (FULLTEXT_DIR / f"{stem}.pdf").exists()
        entry = (row, "xml" if has_xml else ("pdf" if has_pdf else "-"))
        if row["record_id"] in done_ids:
            done.append(entry)
        elif row["record_id"] in partial_ids:
            # A headline number was recovered into the partial table; the rest of the paper
            # still needs its figures digitising.
            partially.append(entry)
        elif row["screen_ft"] == "maybe":
            # Values exist but only inside a figure: needs digitising or an email to the
            # authors, so it is not something the next extraction session can just pick up.
            blocked.append(entry)
        elif has_xml or has_pdf:
            pending.append(entry)
        else:
            missing.append(entry)

    # XML first: its tables can be parsed, which is several times faster than a PDF.
    pending.sort(key=lambda entry: (entry[1] != "xml", -int(entry[0]["year"] or 0)))

    rows_by_study = {}
    for row in extraction:
        rows_by_study[row["study_id"]] = rows_by_study.get(row["study_id"], 0) + 1

    lines = [
        "# Extraction Queue",
        "",
        f"Regenerated {date.today().isoformat()} by `framework/extraction_queue.py`. This is the",
        "resume point: if work stops here, start again at the top of the pending table.",
        "",
        f"- **{len(done)} extracted**, {sum(rows_by_study.values())} rows in "
        "`data/raw/extraction_qaragoz.csv`",
        f"- **{len(pending)} pending** with a full text on disk",
        f"- **{len(partially)} partially extracted** into "
        "`data/raw/extraction_partial.csv` - a headline number recovered, the rest still in figures",
        f"- {len(blocked)} blocked because their numbers exist only in figures",
        f"- {len(missing)} have no full text on disk",
        f"- {len(excluded_ft)} were excluded at full text and must not be re-read",
        "",
        "## How to continue",
        "",
        "1. Take the top row of the pending table.",
        "2. Read `data/search/fulltext_digests/<record_id>.md` - it holds the study-level facts,",
        "   the tables that mention a muscle outcome, and every sentence with a muscle term and a",
        "   number. If the numbers are not in there, open the file named in the Source column.",
        "3. Add the study to `framework/extractors/typed_rows.py`, or give it its own parser in",
        "   `framework/extractors/` if it has a large results table.",
        "4. Run the extractor, then `python framework/validate_extraction.py data/raw/extraction_qaragoz.csv`.",
        "5. Run `python framework/extraction_report.py` and `python framework/extraction_queue.py`.",
        "6. Commit. One commit per batch, naming the studies.",
        "",
        "If a paper turns out to have no usable numbers, it is a full-text exclusion: add a row to",
        "`screen_decisions_fulltext.csv` with the reason instead of leaving it pending forever.",
        "",
        "## Pending",
        "",
        "| # | Year | Source | Record | Study |",
        "|---|---|---|---|---|",
    ]
    for index, (row, source) in enumerate(pending, start=1):
        lines.append(f"| {index} | {row['year']} | {source} | `{row['record_id']}` | "
                     f"{row['title'][:78]} |")

    if partially:
        lines += ["", "## Partially extracted", "",
                  "One or two numbers recovered from the abstract or results text; the full set",
                  "still needs figure digitising. Rows are in `data/raw/extraction_partial.csv`.",
                  "", "| Record | Study |", "|---|---|"]
        for row, _source in partially:
            lines.append(f"| `{row['record_id']}` | {row['title'][:80]} |")

    if blocked:
        lines += ["", "## Blocked - values only in figures", "",
                  "These need WebPlotDigitizer or a request to the corresponding author, so they",
                  "are not part of the ordinary extraction queue.", "",
                  "| Record | Study |", "|---|---|"]
        for row, _source in blocked:
            lines.append(f"| `{row['record_id']}` | {row['title'][:80]} |")

    lines += ["", "## Extracted", "", "| Study | Record | Rows |", "|---|---|---|"]
    for row, _source in sorted(done, key=lambda entry: entry[0]["year"], reverse=True):
        study = study_for.get(row["record_id"], "?")
        lines.append(f"| `{study}` | `{row['record_id']}` | {rows_by_study.get(study, 0)} |")

    if missing:
        lines += ["", "## No full text on disk", "", "| Record | Study |", "|---|---|"]
        for row, _source in missing:
            lines.append(f"| `{row['record_id']}` | {row['title'][:80]} |")

    QUEUE_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(done)} extracted, {len(partially)} partial, {len(pending)} pending, "
          f"{len(blocked)} blocked, {len(missing)} without full text")
    for row, source in pending[:8]:
        print(f"  next: {source:4s} {row['record_id']:14s} {row['title'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
