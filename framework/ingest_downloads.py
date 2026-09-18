"""File manually downloaded PDFs into resources/fulltext/ under the right names.

Usage:
    python framework/ingest_downloads.py [source_folder]

Publisher filenames are useless - `glu123.pdf`, `1-s2.0-S0002916523121502-main.pdf` - so
each PDF is identified by what is inside it, not what it is called:

1. the DOI, read out of the first two pages, matched against the screening table;
2. failing that, the title, fuzzy-matched against every screened record.

Matches are copied (never moved - the download stays where it was) to
resources/fulltext/<author><year>_<record_id>.pdf, the same naming the fetch script uses,
so both halves of the corpus sit in one folder under one convention.

Anything that cannot be matched confidently is listed at the end for a person to place by
hand. A wrong match is worse than no match: it would attach one paper's numbers to another
paper's row.
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
from difflib import SequenceMatcher
from pathlib import Path

import fitz  # PyMuPDF

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING_CSV = REPO_ROOT / "data" / "search" / "screening.csv"
FULLTEXT_DIR = REPO_ROOT / "resources" / "fulltext"
DEFAULT_SOURCE = Path.home() / "Downloads"

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9]+", re.IGNORECASE)
TITLE_THRESHOLD = 0.62

csv.field_size_limit(10_000_000)


def safe_name(row: dict) -> str:
    author = (row["authors"].split(",")[0].split(";")[0] or "anon").strip().lower()
    author = "".join(character for character in author if character.isalnum())[:20]
    return f"{author or 'anon'}{row['year']}_{row['record_id']}"


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def clean_doi(raw: str) -> str:
    return raw.lower().rstrip(").,;").rstrip(".")


def pdf_head(path: Path, pages: int = 2) -> str:
    try:
        with fitz.open(path) as document:
            return " ".join(document[i].get_text() for i in range(min(pages, document.page_count)))
    except Exception as error:  # a corrupt or encrypted download
        print(f"  ! could not read {path.name}: {type(error).__name__}")
        return ""


def match_record(text: str, records: list) -> tuple:
    """Return (record, how, score). DOI beats title; an uncertain title match returns None."""
    dois = {clean_doi(match.group(0)) for match in DOI_PATTERN.finditer(text)}
    by_doi = {r["doi"].lower(): r for r in records if r["doi"]}
    for doi in dois:
        if doi in by_doi:
            return by_doi[doi], f"doi {doi}", 1.0

    head = normalise(text[:1500])
    if not head:
        return None, "no text", 0.0

    best, best_score = None, 0.0
    for record in records:
        title = normalise(record["title"])
        if len(title) < 20:
            continue
        score = SequenceMatcher(None, title, head[:len(title) + 60]).ratio()
        if title[:60] in head:
            score = max(score, 0.95)
        if score > best_score:
            best, best_score = record, score
    if best_score >= TITLE_THRESHOLD:
        return best, f"title {best_score:.2f}", best_score
    return None, f"best title match {best_score:.2f}", best_score


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_dir():
        print(f"no such folder: {source}")
        return 1

    FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)

    with SCREENING_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    included = [r for r in rows if r["screen_ta"] == "include"]
    everything = [r for r in rows if r["screen_ta"] in {"include", "maybe"}]

    pdfs = sorted(source.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"{len(pdfs)} PDFs in {source}\n")

    placed, already, unmatched, off_list = [], [], [], []

    for pdf in pdfs:
        text = pdf_head(pdf)
        if not text.strip():
            unmatched.append((pdf, "no extractable text"))
            continue

        record, how, _score = match_record(text, included)
        pool = "included"
        if record is None:
            record, how, _score = match_record(text, everything)
            pool = "screened but not included"

        if record is None:
            unmatched.append((pdf, how))
            continue

        target = FULLTEXT_DIR / f"{safe_name(record)}.pdf"
        if pool != "included":
            off_list.append((pdf, record, how))
            continue
        if target.exists() and target.stat().st_size > 20000:
            already.append((pdf, record))
            continue

        shutil.copy2(pdf, target)
        placed.append((pdf, record, how))
        print(f"  placed  {target.name:44s} <- {pdf.name[:52]}  [{how}]")

    for pdf, record in already:
        print(f"  have    {safe_name(record)}.pdf already; skipped {pdf.name[:40]}")
    for pdf, record, how in off_list:
        print(f"  NOTE    {pdf.name[:50]} matches a record that is not on the include list "
              f"({record['record_id']}, {how})")
    for pdf, why in unmatched:
        print(f"  UNMATCHED {pdf.name[:60]} ({why})")

    print(f"\n{len(placed)} filed, {len(already)} already present, "
          f"{len(off_list)} matched outside the include list, {len(unmatched)} unmatched")

    on_disk = {p.stem.rsplit(".", 1)[0] for p in FULLTEXT_DIR.iterdir()}
    have = sum(1 for r in included if safe_name(r) in on_disk)
    print(f"full texts on disk for {have} of {len(included)} included studies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
