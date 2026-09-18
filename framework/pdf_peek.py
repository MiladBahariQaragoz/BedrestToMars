"""Print the number-dense passages of a paper, so its results table can be read.

    python framework/pdf_peek.py pubmed_00194 [more record ids...]

Most of the remaining full texts are PDFs, where a results table flattens into a run of
text. This finds the passages that look like results - a muscle term surrounded by numbers -
and prints a window around each, densest first, plus the study-level facts extraction needs.

It reads; it never writes. What the numbers mean is still a person's call.
"""

from __future__ import annotations

import glob
import html
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MUSCLE = re.compile(
    r"muscle volume|muscle mass|muscle size|cross[- ]?sectional area|\bCSA\b|\bACSA\b|"
    r"lean mass|lean tissue|muscle thickness|quadriceps|soleus|gastrocnemi|vastus|"
    r"triceps surae|plantar ?flexor|knee extensor|thigh|calf|multifidus", re.IGNORECASE)
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")

FACTS = [
    ("participants", re.compile(r"(\d{1,3})\s+(?:healthy\s+)?(?:young\s+|older\s+)?"
                                r"(?:men|women|males|females|participants|subjects|volunteers)",
                                re.IGNORECASE)),
    ("age", re.compile(r"(?:age[ds]?[^.]{0,30})?(\d{2}(?:[.,]\d)?)\s*±\s*(\d{1,2}(?:[.,]\d)?)"
                       r"\s*(?:years|yr|y)\b", re.IGNORECASE)),
    ("age range", re.compile(r"aged?\s+(\d{2})\s*(?:-|to|–)\s*(\d{2})", re.IGNORECASE)),
    ("duration", re.compile(r"(\d{1,3})[\s-]*(?:days?|weeks?)\s+of\s+"
                            r"(?:bed ?rest|head[- ]down|HDT|unloading|immersion|suspension)",
                            re.IGNORECASE)),
    ("registry", re.compile(r"\b(NCT\d{8}|DRKS\d{6,}|ISRCTN\d{8})\b")),
    ("modality", re.compile(r"\b(MRI|magnetic resonance|computed tomography|pQCT|DXA|DEXA|"
                            r"ultrasound|ultrasonograph\w+)\b", re.IGNORECASE)),
]


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


def dense_windows(text: str, width: int = 900, top: int = 3) -> list:
    """Windows around muscle terms, ranked by how many numbers they contain."""
    candidates = []
    for match in MUSCLE.finditer(text):
        start = max(0, match.start() - 120)
        window = text[start:start + width]
        candidates.append((len(NUMBER.findall(window)), start, window))
    candidates.sort(reverse=True)

    chosen = []
    for count, start, window in candidates:
        if any(abs(start - other) < width // 2 for _, other, _ in chosen):
            continue
        chosen.append((count, start, window))
        if len(chosen) >= top:
            break
    return chosen


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for record_id in sys.argv[1:]:
        text = load(record_id)
        print(f"########## {record_id}")
        if not text:
            print("  no full text on disk")
            continue
        for name, pattern in FACTS:
            hits = []
            for match in pattern.finditer(text):
                value = match.group(0).strip()
                if value not in hits:
                    hits.append(value)
                if len(hits) >= 4:
                    break
            print(f"  {name:13s} {' | '.join(hits) if hits else '-'}")
        for count, _start, window in dense_windows(text):
            print(f"  --- {count} numbers ---")
            print("  " + window)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
