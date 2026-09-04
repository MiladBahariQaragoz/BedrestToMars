"""For each pending study, show the best evidence that a row could be built from it.

    python framework/suggest_disposition.py

Extraction has reached the tail of the queue, where most remaining papers keep their muscle
results in figures. Opening each one to discover that is slow, so this prints, per study,
the single strongest candidate sentence - a muscle term with a percent change, or with a
pre and post pair - and a suggested disposition:

    EXTRACT   a usable number is printed in the text
    PARK      nothing usable found; likely figure-only, and a person should confirm

The suggestion is evidence, not a decision. Nothing is written.
"""

from __future__ import annotations

import csv
import glob
import html
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING = REPO_ROOT / "data" / "search" / "screening.csv"
EXTRACTION = REPO_ROOT / "data" / "raw" / "extraction_falk.csv"

csv.field_size_limit(10_000_000)

MUSCLE_WORDS = (r"muscle volume|muscle mass|muscle size|cross[- ]?sectional area|\bCSA\b|"
                r"lean mass|lean tissue|muscle thickness|quadriceps|soleus|gastrocnemi|"
                r"vastus|triceps surae|plantar ?flexor|thigh|calf|multifidus|hamstring")

PERCENT = re.compile(rf"[^.]{{0,120}}({MUSCLE_WORDS})[^.]{{0,120}}"
                     rf"(?:decreas|reduc|declin|loss|lost|chang|atroph)\w*[^.]{{0,60}}"
                     rf"(-|−)?\d+(?:\.\d+)?\s?%[^.]{{0,60}}\.", re.IGNORECASE)
PREPOST = re.compile(rf"({MUSCLE_WORDS})[^.]{{0,80}}\d+(?:\.\d+)?\s*±\s*\d+(?:\.\d+)?"
                     rf"[^.]{{0,60}}\d+(?:\.\d+)?\s*±\s*\d", re.IGNORECASE)


def load(record_id: str) -> str:
    matches = glob.glob(str(REPO_ROOT / f"resources/fulltext/*{record_id}*"))
    if not matches:
        return ""
    path = Path(matches[0])
    if path.suffix == ".pdf":
        import fitz
        with fitz.open(path) as document:
            text = " ".join(page.get_text() for page in document)
    else:
        text = html.unescape(re.sub("<[^>]+>", " ", path.read_text(encoding="utf-8", errors="replace")))
    return re.sub(r"\s+", " ", text)


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
    for row in pending:
        text = load(row["record_id"])
        if not text:
            print(f"PARK     {row['record_id']:14s} no full text")
            verdicts["park"] += 1
            continue

        percent = PERCENT.search(text)
        prepost = PREPOST.search(text)
        if percent:
            verdict, evidence = "EXTRACT", percent.group(0).strip()
        elif prepost:
            verdict, evidence = "EXTRACT", prepost.group(0).strip()
        else:
            verdict, evidence = "PARK", "no muscle number in text"
        verdicts[verdict.lower()] += 1
        print(f"{verdict:8s} {row['record_id']:14s} {row['title'][:44]:44s} {evidence[:150]}")

    print()
    print("  ".join(f"{name}: {count}" for name, count in verdicts.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
