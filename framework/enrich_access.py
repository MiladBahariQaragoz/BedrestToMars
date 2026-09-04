"""Stage 2 of the screen: can we actually get the data out of this paper?

Usage:
    python framework/enrich_access.py

For every record that survived triage, this asks two questions that decide how expensive
extraction will be:

1. **Is the full text open, and is it machine-readable?** Europe PMC is checked first,
   because a paper with full text in Europe PMC can be pulled as XML with its tables intact -
   the difference between minutes and an afternoon per study. OpenAlex fills in open-access
   status and a link for everything else.
2. **Does the abstract already carry numbers?** A percent change or a volume in the abstract
   means at least one usable row even if the full text is paywalled.

Adds these columns to data/search/screening.csv:

    is_oa, oa_status, oa_url, in_epmc, pmcid, abstract_has_numbers, extractability

Responses are cached in data/search/.access_cache.json, so re-running costs nothing and the
network is only touched for records that have not been looked up before.

Both APIs are public and anonymous. Only DOIs are sent.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING_CSV = REPO_ROOT / "data" / "search" / "screening.csv"
CACHE_JSON = REPO_ROOT / "data" / "search" / ".access_cache.json"

EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
OPENALEX = "https://api.openalex.org/works"
USER_AGENT = "BedrestToMars-literature-review/1.0 (academic use)"

TRIAGE_TO_ENRICH = {"priority", "maybe"}
EPMC_BATCH = 20
OPENALEX_BATCH = 40

csv.field_size_limit(10_000_000)

NUMBERS = re.compile(
    r"(\d+(?:\.\d+)?\s?%)"                       # 12.3%
    r"|(\d+(?:\.\d+)?\s?(cm\s?[23³²]|cm\^[23]|mm[23³²]|ml\b|cm2\b|cm3\b))"
    r"|((decreas|reduc|declin|los[ts]|increas)\w*\s+(?:by\s+)?\d+(?:\.\d+)?)"
    r"|(\bp\s?[<=>]\s?0?\.\d+)",
    re.IGNORECASE,
)


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def load_cache() -> dict:
    if CACHE_JSON.exists():
        return json.loads(CACHE_JSON.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_JSON.write_text(json.dumps(cache, indent=0), encoding="utf-8")


def chunks(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def query_europepmc(dois: list, cache: dict) -> None:
    """Ask Europe PMC which of these DOIs it holds, and whether the full text is there."""
    for batch in chunks(dois, EPMC_BATCH):
        query = " OR ".join(f'DOI:"{doi}"' for doi in batch)
        url = f"{EUROPEPMC}?{urllib.parse.urlencode({'query': query, 'format': 'json', 'pageSize': 100, 'resultType': 'lite'})}"
        try:
            payload = fetch_json(url)
        except Exception as error:  # network problems must not lose the run
            print(f"  europepmc batch failed: {type(error).__name__}", file=sys.stderr)
            continue
        for result in payload.get("resultList", {}).get("result", []):
            doi = (result.get("doi") or "").lower()
            if not doi:
                continue
            entry = cache.setdefault(doi, {})
            entry["in_epmc"] = "yes" if result.get("inEPMC") == "Y" else "no"
            entry["pmcid"] = result.get("pmcid", "")
            if result.get("isOpenAccess") == "Y":
                entry["is_oa"] = "yes"
                entry.setdefault("oa_status", "epmc_open")
        time.sleep(0.2)


def query_openalex(dois: list, cache: dict) -> None:
    """Fill in open-access status and a link for everything Europe PMC did not answer."""
    for batch in chunks(dois, OPENALEX_BATCH):
        joined = "|".join(f"https://doi.org/{doi}" for doi in batch)
        params = {"filter": f"doi:{joined}", "per-page": OPENALEX_BATCH,
                  "select": "doi,open_access,best_oa_location"}
        url = f"{OPENALEX}?{urllib.parse.urlencode(params)}"
        try:
            payload = fetch_json(url)
        except Exception as error:
            print(f"  openalex batch failed: {type(error).__name__}", file=sys.stderr)
            continue
        for work in payload.get("results", []):
            doi = (work.get("doi") or "").lower().replace("https://doi.org/", "")
            if not doi:
                continue
            entry = cache.setdefault(doi, {})
            access = work.get("open_access") or {}
            entry["is_oa"] = "yes" if access.get("is_oa") else "no"
            entry["oa_status"] = access.get("oa_status", "")
            best = work.get("best_oa_location") or {}
            entry["oa_url"] = best.get("pdf_url") or best.get("landing_page_url") or access.get("oa_url") or ""
        time.sleep(0.2)


def extractability(row: dict) -> str:
    """How cheap is it to get rows out of this paper, if it turns out to be eligible?"""
    if row["in_epmc"] == "yes":
        return "high"          # full text as XML, tables intact
    if row["is_oa"] == "yes":
        return "medium"        # readable, but the tables have to be read by hand
    if row["abstract_has_numbers"] == "yes":
        return "medium"        # at least one row is in the abstract itself
    return "low"               # paywalled and no numbers in the abstract


def main() -> int:
    with SCREENING_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    new_columns = ["is_oa", "oa_status", "oa_url", "in_epmc", "pmcid",
                   "abstract_has_numbers", "extractability"]
    for column in new_columns:
        if column not in columns:
            columns.append(column)

    targets = [r for r in rows if r.get("triage") in TRIAGE_TO_ENRICH]
    cache = load_cache()

    dois = sorted({r["doi"].lower() for r in targets if r["doi"] and r["doi"].lower() not in cache})
    print(f"{len(targets)} records to enrich, {len(dois)} DOIs not yet cached")

    if dois:
        print("  querying Europe PMC...")
        query_europepmc(dois, cache)
        save_cache(cache)
        missing_oa = [d for d in dois if not cache.get(d, {}).get("is_oa")]
        print(f"  querying OpenAlex for {len(missing_oa)} remaining...")
        query_openalex(missing_oa, cache)
        save_cache(cache)

    for row in rows:
        for column in new_columns:
            row.setdefault(column, "")
        if row.get("triage") not in TRIAGE_TO_ENRICH:
            continue
        entry = cache.get(row["doi"].lower(), {})
        row["is_oa"] = entry.get("is_oa", "unknown")
        row["oa_status"] = entry.get("oa_status", "")
        row["oa_url"] = entry.get("oa_url", "")
        row["in_epmc"] = entry.get("in_epmc", "no")
        row["pmcid"] = entry.get("pmcid", "")
        row["abstract_has_numbers"] = "yes" if NUMBERS.search(row["abstract"] or "") else "no"
        row["extractability"] = extractability(row)

    with SCREENING_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    report(rows)
    return 0


def report(rows: list) -> None:
    from collections import Counter
    for bucket in ("priority", "maybe"):
        selected = [r for r in rows if r.get("triage") == bucket]
        print(f"\n{bucket} ({len(selected)} records)")
        print("  open access:      ", dict(Counter(r["is_oa"] for r in selected)))
        print("  full text in EPMC:", dict(Counter(r["in_epmc"] for r in selected)))
        print("  numbers in abstract:", dict(Counter(r["abstract_has_numbers"] for r in selected)))
        print("  extractability:   ", dict(Counter(r["extractability"] for r in selected)))


if __name__ == "__main__":
    raise SystemExit(main())
