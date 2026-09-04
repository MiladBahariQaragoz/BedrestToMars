"""Read every full text on disk and pull out what extraction needs.

Usage:
    python framework/scan_fulltexts.py

For each included study with a file in resources/fulltext/, this reads the whole paper -
XML where Europe PMC provided it, PDF text otherwise - and writes a digest containing only
the parts that decide anything:

* the study-level facts that are the same for every row: unloading duration, tilt angle,
  group sizes, age, sex, trial registration, countermeasure;
* every table whose caption or body mentions a muscle-size outcome, with its caption and
  the first rows of its body;
* every sentence carrying a muscle term together with a number - a percent change, a value
  with units, or a mean and SD.

Digests land in data/search/fulltext_digests/ and a one-line-per-study summary in
data/search/fulltext_scan.csv. Reading a digest is a two-minute job; reading the paper is
twenty. Nothing here decides anything on its own: a digest says where the numbers are, and
a person still says what they mean.
"""

from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING_CSV = REPO_ROOT / "data" / "search" / "screening.csv"
FULLTEXT_DIR = REPO_ROOT / "resources" / "fulltext"
DIGEST_DIR = REPO_ROOT / "data" / "search" / "fulltext_digests"
SCAN_CSV = REPO_ROOT / "data" / "search" / "fulltext_scan.csv"

csv.field_size_limit(10_000_000)

MUSCLE = re.compile(
    r"\b(soleus|gastrocnemi\w*|triceps surae|plantar ?flexor\w*|tibialis anterior|"
    r"quadriceps|vastus \w+|rectus femoris|knee extensor\w*|hamstring\w*|adductor\w*|"
    r"glute\w+|psoas|multifidus|paraspinal|thigh|calf|shank|lower limb|lower extremit\w*|"
    r"leg muscle\w*|lean (?:leg |body |tissue )?mass|muscle (?:volume|mass|size|thickness|"
    r"cross[- ]sectional area)|\bCSA\b|\bACSA\b|\bPCSA\b)", re.IGNORECASE)

NUMBER = re.compile(
    r"(-?\d+(?:[.,]\d+)?\s?%)"
    r"|(-?\d+(?:[.,]\d+)?\s?±\s?\d+(?:[.,]\d+)?)"
    r"|(-?\d+(?:[.,]\d+)?\s?(?:cm3|cm\^3|cm³|cm2|cm²|mm2|mm²|ml|kg|g)\b)")

FACTS = {
    "duration": re.compile(
        r"\b(\d{1,3})[\s-]*(day|days|week|weeks|wk|month|months)\b[^.]{0,40}?"
        r"(bed ?rest|head[- ]down|HDT|HDBR|immersion|unloading|suspension|immobili\w+|spaceflight)",
        re.IGNORECASE),
    "tilt": re.compile(r"(-?\d(?:\.\d)?)\s*(?:°|deg(?:rees)?)\s*head[- ]?down", re.IGNORECASE),
    "registry": re.compile(r"\b(NCT\d{8}|DRKS\d{6,}|ISRCTN\d{8})\b", re.IGNORECASE),
    "n_participants": re.compile(
        r"\b(?:n\s?=\s?(\d{1,3})|(\w+|\d{1,3})\s+(?:healthy\s+)?(?:male|female|men|women|"
        r"participants|volunteers|subjects))\b", re.IGNORECASE),
    "age": re.compile(r"(\d{2}(?:[.,]\d)?)\s?±\s?(\d{1,2}(?:[.,]\d)?)\s*(?:years|yr|y)\b", re.IGNORECASE),
    "modality": re.compile(
        r"\b(MRI|magnetic resonance|computed tomography|\bCT\b|pQCT|DXA|DEXA|"
        r"dual[- ]energy x[- ]ray|ultrasound|ultrasonograph\w+)\b", re.IGNORECASE),
    "countermeasure": re.compile(
        r"\b(resistive vibration|whole[- ]body vibration|flywheel|reactive jump\w*|"
        r"artificial gravity|centrifug\w+|resistance (?:exercise|training)|aerobic|"
        r"treadmill|cycling|lower body negative pressure|protein supplement\w*|leucine|"
        r"neuromuscular electrical stimulation|blood flow restrict\w+|testosterone)\b",
        re.IGNORECASE),
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def strip_tags(fragment: str) -> str:
    return clean(re.sub(r"<[^>]+>", " ", fragment))


def safe_name(row: dict) -> str:
    author = (row["authors"].split(",")[0].split(";")[0] or "anon").strip().lower()
    author = "".join(character for character in author if character.isalnum())[:20]
    return f"{author or 'anon'}{row['year']}_{row['record_id']}"


def read_xml(path: Path) -> tuple:
    raw = path.read_text(encoding="utf-8", errors="replace")
    tables = []
    for block in re.findall(r"<table-wrap\b.*?</table-wrap>", raw, re.S):
        caption = strip_tags(re.search(r"<caption>(.*?)</caption>", block, re.S).group(1)) \
            if re.search(r"<caption>(.*?)</caption>", block, re.S) else "(no caption)"
        body = strip_tags(block)
        if MUSCLE.search(caption) or MUSCLE.search(body[:2500]):
            tables.append((caption, body))
    body_match = re.search(r"<body>(.*)</body>", raw, re.S)
    text = strip_tags(body_match.group(1) if body_match else raw)
    return text, tables


def read_pdf(path: Path) -> tuple:
    try:
        with fitz.open(path) as document:
            text = " ".join(page.get_text() for page in document)
    except Exception as error:
        return f"__UNREADABLE__ {type(error).__name__}", []
    return clean(text), []


def sentences_with_numbers(text: str, limit: int = 22) -> list:
    found = []
    for sentence in re.split(r"(?<=[.;])\s+", text):
        if len(sentence) > 420 or len(sentence) < 30:
            continue
        if MUSCLE.search(sentence) and NUMBER.search(sentence):
            found.append(sentence.strip())
            if len(found) >= limit:
                break
    return found


def facts_from(text: str) -> dict:
    found = {}
    for name, pattern in FACTS.items():
        hits = []
        for match in pattern.finditer(text):
            value = clean(match.group(0))
            if value.lower() not in {h.lower() for h in hits}:
                hits.append(value)
            if len(hits) >= 6:
                break
        found[name] = hits
    return found


def main() -> int:
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)

    with SCREENING_CSV.open(encoding="utf-8-sig", newline="") as handle:
        included = [r for r in csv.DictReader(handle) if r["screen_ta"] == "include"]

    summary = []
    for row in included:
        stem = safe_name(row)
        xml_path = FULLTEXT_DIR / f"{stem}.xml"
        pdf_path = FULLTEXT_DIR / f"{stem}.pdf"

        if xml_path.exists():
            text, tables = read_xml(xml_path)
            source, source_file = "xml", xml_path.name
        elif pdf_path.exists():
            text, tables = read_pdf(pdf_path)
            source, source_file = "pdf", pdf_path.name
        else:
            summary.append({**base_summary(row), "source": "missing", "status": "no full text"})
            continue

        if text.startswith("__UNREADABLE__"):
            summary.append({**base_summary(row), "source": source, "status": text})
            continue

        facts = facts_from(text)
        numeric = sentences_with_numbers(text)
        write_digest(row, source_file, source, facts, tables, numeric, len(text))

        summary.append({
            **base_summary(row),
            "source": source,
            "status": "scanned",
            "chars": len(text),
            "muscle_tables": len(tables),
            "numeric_sentences": len(numeric),
            "duration_hits": " | ".join(facts["duration"][:3]),
            "registry": " ".join(facts["registry"][:2]),
            "modality": " ".join(sorted({m.upper() for m in facts["modality"]})[:4]),
            "countermeasure": " ".join(sorted({c.lower() for c in facts["countermeasure"]})[:5]),
        })

    with SCAN_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["record_id", "year", "first_author", "doi", "title", "source", "status",
                  "chars", "muscle_tables", "numeric_sentences", "duration_hits", "registry",
                  "modality", "countermeasure"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary)

    scanned = [s for s in summary if s.get("status") == "scanned"]
    with_tables = [s for s in scanned if s.get("muscle_tables")]
    with_numbers = [s for s in scanned if s.get("numeric_sentences")]
    print(f"{len(scanned)} of {len(included)} scanned")
    print(f"  with muscle tables (XML only): {len(with_tables)}")
    print(f"  with numeric muscle sentences: {len(with_numbers)}")
    print(f"  no numbers found at all:       {len(scanned) - len(with_numbers)}")
    print(f"digests in {DIGEST_DIR.relative_to(REPO_ROOT)}")
    return 0


def base_summary(row: dict) -> dict:
    return {"record_id": row["record_id"], "year": row["year"], "doi": row["doi"],
            "first_author": row["authors"].split(",")[0].split(";")[0][:30],
            "title": row["title"][:110], "chars": 0, "muscle_tables": 0,
            "numeric_sentences": 0, "duration_hits": "", "registry": "",
            "modality": "", "countermeasure": ""}


def write_digest(row, source_file, source, facts, tables, numeric, length) -> None:
    lines = [
        f"# {row['title']}",
        "",
        f"- record: `{row['record_id']}` · {row['year']} · doi `{row['doi'] or '-'}`",
        f"- source: `{source_file}` ({source}, {length} characters of text)",
        "",
        "## Study-level facts found in the text",
        "",
    ]
    for name in ("duration", "tilt", "registry", "n_participants", "age", "modality", "countermeasure"):
        values = facts.get(name) or ["-"]
        lines.append(f"- **{name}**: {' · '.join(values[:6])}")

    if tables:
        lines += ["", f"## Tables mentioning a muscle outcome ({len(tables)})", ""]
        for index, (caption, body) in enumerate(tables[:6], start=1):
            lines += [f"### Table {index} — {caption[:180]}", "", "```",
                      body[:1400], "```", ""]

    lines += ["", f"## Sentences carrying a muscle term and a number ({len(numeric)})", ""]
    for sentence in numeric:
        lines.append(f"- {sentence}")
    lines.append("")

    (DIGEST_DIR / f"{row['record_id']}.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
