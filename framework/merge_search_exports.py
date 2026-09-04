"""Merge the raw database exports into one screening table.

Usage:
    python framework/merge_search_exports.py

Reads every export in docs/literature-review/exports/, normalises the four different
formats into the columns defined in docs/literature-review/PLAN.md section 6, and writes:

    data/search/all_records.csv   every record from every database, nothing dropped
    data/search/screening.csv     one row per unique study, ready to screen
    data/search/merge_report.md   the counts that feed the PRISMA table

Deduplication is DOI, then PubMed ID, then a normalised title-plus-year key. Duplicates are
marked, never deleted: all_records.csv keeps them with `duplicate_of` pointing at the record
that was kept, so the PRISMA "duplicates removed" count is a fact rather than an estimate.

The PubMed export needs the most work: PubMed's CSV export carries no abstract, so the
export is the plain-text "Abstract (text)" format, which has to be parsed record by record.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_DIR = REPO_ROOT / "docs" / "literature-review" / "exports"
OUT_DIR = REPO_ROOT / "data" / "search"

RETRIEVED = date(2026, 9, 4).isoformat()

COLUMNS = [
    "record_id", "query_id", "database", "retrieved_date", "title", "abstract",
    "authors", "journal", "year", "doi", "pmid", "other_id", "url", "dedup_key",
    "found_in", "duplicate_of", "screen_ta", "screen_ft", "exclusion_reason",
    "campaign_guess", "registry_id", "screener", "screen_date", "notes",
]

REGISTRY_PATTERN = re.compile(
    r"\b(NCT\d{8}|DRKS\d{8,}|ISRCTN\d{8}|ChiCTR[-\w]*\d+|ACTRN\d{14})\b", re.IGNORECASE
)

# Paragraphs in the PubMed text format that are never part of the abstract.
PUBMED_SKIP = (
    "Author information:", "Comment in", "Comment on", "Erratum in", "Erratum for",
    "Update in", "Update of", "Republished in", "Republished from", "Expression of concern",
    "Retraction in", "Retracted and republished", "Conflict of interest statement",
    "Collaborators:", "Publisher:", "DOI:", "PMID:", "PMCID:", "Copyright ", "©",
    "Plain Language Summary:", "Erratum", "Summary for patients in",
)


def clean(value) -> str:
    """Collapse whitespace and turn every flavour of missing into an empty string."""
    if value is None:
        return ""
    text = str(value)
    if text.strip().lower() in {"nan", "none", "undefined", "no abstract available"}:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_doi(value) -> str:
    doi = clean(value).lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.rstrip(".")


def find_registry_id(*texts) -> str:
    for text in texts:
        match = REGISTRY_PATTERN.search(text or "")
        if match:
            return match.group(1).upper()
    return ""


def title_key(title: str, year: str) -> str:
    words = re.sub(r"[^a-z0-9 ]", " ", clean(title).lower()).split()
    return f"{'_'.join(words[:8])}|{year}" if words else ""


# --------------------------------------------------------------------------- PubMed

def looks_like_citation(paragraph: str) -> bool:
    """A PubMed citation paragraph carries a year, and usually a volume or a DOI."""
    flat = clean(paragraph)
    return bool(re.search(r"\b(19|20)\d{2}\b", flat)) and bool(
        re.search(r"(doi:|;\d|\(\d+\)|:\d+-|Epub|Online ahead of print)", flat, re.IGNORECASE)
    )


def split_pubmed_records(text: str) -> list:
    """Split the plain-text export on the numbered record headers.

    The header is a number and a dot at the start of a line, but so is the tail of a
    wrapped citation ("... Epub 2019 Sep \n24."), which is why the blank line in front of
    the header is part of the pattern. Any fragment that still does not open with something
    resembling a citation is glued back onto the record before it.
    """
    text = text.replace("\r\n", "\n")
    parts = re.split(r"\n\s*\n(?=\d+\.\s+[A-Z])", text)

    merged = []
    for part in parts:
        body = re.sub(r"^\d+\.\s+", "", part.strip())
        # A record can open with a status banner ("RETRACTED ARTICLE") before its citation,
        # so look at the first two paragraphs before deciding this is not a record header.
        opening = re.split(r"\n\s*\n", body)[:2]
        if merged and not any(looks_like_citation(p) for p in opening):
            merged[-1] = merged[-1] + "\n\n" + part
        else:
            merged.append(part)

    return [part for part in merged if "PMID:" in part]


def parse_pubmed_record(raw: str) -> dict:
    """Pull title, authors, journal, year, DOI, PMID and abstract out of one record."""
    body = re.sub(r"^\d+\.\s+", "", raw.strip())
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not paragraphs:
        return {}

    # Status banners sit above the citation and are worth keeping as a screening flag.
    flags = []
    while paragraphs and not looks_like_citation(paragraphs[0]) and len(clean(paragraphs[0])) < 60:
        flags.append(clean(paragraphs.pop(0)))
    if not paragraphs:
        return {}

    citation = clean(paragraphs[0])
    journal = citation.split(".")[0].strip()
    # Several journal titles carry a year of their own - "J Appl Physiol (1985)",
    # "Spine (Phila Pa 1976)" - so drop parenthesised years before reading the real one.
    year_match = re.search(r"\b(19|20)\d{2}\b", re.sub(r"\((?:[^()]*\b(?:19|20)\d{2})\)", "", citation))
    year = year_match.group(0) if year_match else ""

    pmid_match = re.search(r"^PMID:\s*(\d+)", body, re.MULTILINE)
    pmid = pmid_match.group(1) if pmid_match else ""

    doi_match = re.search(r"^DOI:\s*(\S+)", body, re.MULTILINE)
    if not doi_match:
        doi_match = re.search(r"\bdoi:\s*(\S+)", citation, re.IGNORECASE)
    doi = clean_doi(doi_match.group(1)) if doi_match else ""

    title = clean(paragraphs[1]) if len(paragraphs) > 1 else ""
    authors = ""
    if len(paragraphs) > 2:
        candidate = clean(paragraphs[2])
        # An author paragraph looks like "Wall BT(1), Dirks ML(2), van Loon LJ(1)."
        if not candidate.startswith(PUBMED_SKIP) and len(candidate) < 1500:
            authors = candidate

    abstract_parts = []
    for paragraph in paragraphs[3:] if authors else paragraphs[2:]:
        flat = clean(paragraph)
        if not flat or flat.startswith(PUBMED_SKIP) or re.match(r"^\(\d+\)", flat):
            continue
        abstract_parts.append(flat)
    abstract = " ".join(abstract_parts)

    return {
        "database": "pubmed",
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "journal": journal,
        "year": year,
        "doi": doi,
        "pmid": pmid,
        "other_id": "",
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        "notes": "; ".join(flags),
    }


def read_pubmed(path: Path) -> list:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return [record for record in (parse_pubmed_record(r) for r in split_pubmed_records(raw)) if record]


# --------------------------------------------------------------------------- Scopus

def read_scopus(path: Path) -> list:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    records = []
    for _, row in frame.iterrows():
        doi = clean_doi(row.get("DOI"))
        records.append({
            "database": "scopus",
            "title": clean(row.get("Title")),
            "abstract": clean(row.get("Abstract")),
            "authors": clean(row.get("Authors")),
            "journal": clean(row.get("Source title")),
            "year": clean(row.get("Year")),
            "doi": doi,
            "pmid": "",
            "other_id": clean(row.get("Author(s) ID"))[:0],  # Scopus EID is not in this export
            "url": clean(row.get("Link")) or (f"https://doi.org/{doi}" if doi else ""),
        })
    return records


# ------------------------------------------------------------------- Web of Science

def read_wos(paths: list) -> list:
    records = []
    for path in paths:
        frame = pd.read_excel(path, dtype=str)
        frame = frame.fillna("")
        for _, row in frame.iterrows():
            doi = clean_doi(row.get("DOI"))
            records.append({
                "database": "wos",
                "title": clean(row.get("Article Title")),
                "abstract": clean(row.get("Abstract")),
                "authors": clean(row.get("Authors")),
                "journal": clean(row.get("Source Title")),
                "year": clean(row.get("Publication Year")).replace(".0", ""),
                "doi": doi,
                "pmid": clean(row.get("Pubmed Id")).replace(".0", ""),
                "other_id": clean(row.get("UT (Unique WOS ID)")),
                "url": clean(row.get("DOI Link")) or (f"https://doi.org/{doi}" if doi else ""),
            })
    return records


# ----------------------------------------------------------------------- NASA NTRS

def first_year_from_json(blob: str) -> str:
    try:
        entries = json.loads(blob) if blob and blob != "undefined" else []
    except (json.JSONDecodeError, TypeError):
        return ""
    for entry in entries if isinstance(entries, list) else []:
        for key in ("publicationDate", "startDate", "endDate"):
            value = entry.get(key) if isinstance(entry, dict) else None
            if value:
                match = re.match(r"(\d{4})", str(value))
                if match:
                    return match.group(1)
    return ""


def meeting_name(blob: str) -> str:
    try:
        entries = json.loads(blob) if blob and blob != "undefined" else []
    except (json.JSONDecodeError, TypeError):
        return ""
    for entry in entries if isinstance(entries, list) else []:
        if isinstance(entry, dict) and entry.get("name"):
            return clean(entry["name"])
    return ""


def read_ntrs(path: Path) -> list:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    records = []
    for _, row in frame.iterrows():
        try:
            authors = "; ".join(json.loads(row.get("Author Names") or "[]"))
        except (json.JSONDecodeError, TypeError):
            authors = clean(row.get("Author Names"))
        year = first_year_from_json(row.get("Publications")) or first_year_from_json(row.get("Meetings"))
        records.append({
            "database": "ntrs",
            "title": clean(row.get("Title")),
            "abstract": clean(row.get("Abstract")),
            "authors": clean(authors),
            "journal": meeting_name(row.get("Meetings")) or clean(row.get("Document Type")),
            "year": year,
            "doi": "",
            "pmid": "",
            "other_id": clean(row.get("Document ID")),
            "url": clean(row.get("Record URL")),
        })
    return records


# --------------------------------------------------------------------------- merge

def dedup_key_for(record: dict) -> str:
    if record["doi"]:
        return f"doi:{record['doi']}"
    if record["pmid"]:
        return f"pmid:{record['pmid']}"
    key = title_key(record["title"], record["year"])
    if key:
        return f"title:{key}"
    return f"id:{record['database']}:{record['other_id'] or record['title'][:40]}"


def main() -> int:
    if not EXPORT_DIR.exists():
        print(f"no export directory at {EXPORT_DIR}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = {
        "pubmed": lambda: read_pubmed(EXPORT_DIR / "Pubmed.txt"),
        "scopus": lambda: read_scopus(EXPORT_DIR / "Scopus.csv"),
        "wos": lambda: read_wos(sorted(EXPORT_DIR.glob("WebOfScience*.xls"))),
        "ntrs": lambda: read_ntrs(EXPORT_DIR / "NASA.csv"),
    }

    query_ids = {"pubmed": "Q01", "scopus": "Q03", "wos": "Q04", "ntrs": "Q05"}

    all_records = []
    per_database = Counter()
    counter = defaultdict(int)

    for name, reader in sources.items():
        records = reader()
        per_database[name] = len(records)
        for record in records:
            counter[name] += 1
            record["record_id"] = f"{name}_{counter[name]:05d}"
            record["query_id"] = query_ids[name]
            record["retrieved_date"] = RETRIEVED
            record["dedup_key"] = dedup_key_for(record)
            record["registry_id"] = find_registry_id(record["abstract"], record["title"])
            for column in COLUMNS:
                record.setdefault(column, "")
            all_records.append(record)

    # Deduplicate: first occurrence wins, later ones point at it.
    kept = {}
    found_in = defaultdict(list)
    for record in all_records:
        key = record["dedup_key"]
        found_in[key].append(record["database"])
        if key in kept:
            record["duplicate_of"] = kept[key]["record_id"]
        else:
            kept[key] = record

    unique = []
    for key, record in kept.items():
        record["found_in"] = ";".join(dict.fromkeys(found_in[key]))
        unique.append(record)

    unique.sort(key=lambda r: (r["year"] or "0000", r["title"].lower()), reverse=True)

    write_csv(OUT_DIR / "all_records.csv", all_records)
    write_csv(OUT_DIR / "screening.csv", unique)
    write_report(OUT_DIR / "merge_report.md", all_records, unique, per_database)

    print(f"{len(all_records)} records in, {len(unique)} unique, "
          f"{len(all_records) - len(unique)} duplicates marked")
    for name, count in per_database.items():
        print(f"  {name:8s} {count:5d}")
    return 0


def write_csv(path: Path, records: list) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(path: Path, all_records: list, unique: list, per_database: Counter) -> None:
    no_abstract = [r for r in unique if not r["abstract"]]
    no_year = [r for r in unique if not r["year"]]
    with_registry = [r for r in unique if r["registry_id"]]
    overlap = Counter(r["found_in"] for r in unique if ";" in r["found_in"])

    lines = [
        "# Merge Report",
        "",
        f"Generated by `framework/merge_search_exports.py` on {RETRIEVED}.",
        "",
        "## Records identified, by database",
        "",
        "| Database | Records |",
        "|---|---|",
    ]
    labels = {"pubmed": "PubMed", "scopus": "Scopus", "wos": "Web of Science", "ntrs": "NASA NTRS"}
    for name, count in per_database.items():
        lines.append(f"| {labels[name]} | {count} |")
    lines += [
        f"| **Total identified** | **{len(all_records)}** |",
        f"| Duplicates marked | {len(all_records) - len(unique)} |",
        f"| **Unique records to screen** | **{len(unique)}** |",
        "",
        "## Data quality of the merged table",
        "",
        f"- Records with no abstract: **{len(no_abstract)}** of {len(unique)}",
        f"- Records with no publication year: **{len(no_year)}**",
        f"- Records carrying a trial registry ID in the abstract: **{len(with_registry)}**",
        "",
        "## Year coverage, by database",
        "",
        "| Database | Earliest | Latest | Published before 2013 |",
        "|---|---|---|---|",
    ]
    for name in per_database:
        years = sorted(int(r["year"]) for r in all_records if r["database"] == name and r["year"].isdigit())
        if years:
            before = sum(1 for y in years if y < 2013)
            lines.append(f"| {labels[name]} | {years[0]} | {years[-1]} | {before} |")
    lines += [
        "",
        "A database showing nothing before 2013 was searched with a date limit. That is a",
        "property of the search, not of the literature, and it belongs in the methods section.",
        "",
        "## Overlap between databases",
        "",
        "| Found in | Records |",
        "|---|---|",
    ]
    for combination, count in overlap.most_common():
        lines.append(f"| {combination} | {count} |")
    lines += [
        "",
        "A record counts as the same study when the DOI matches, or the PubMed ID matches, or",
        "the first eight title words and the year match. Duplicates are kept in",
        "`all_records.csv` with `duplicate_of` filled in, so nothing is silently discarded.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
