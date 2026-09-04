"""Download the full text of every included study that can be fetched automatically.

Usage:
    python framework/fetch_fulltexts.py

Two sources, in order of usefulness:

1. **Europe PMC XML.** Structured full text with the tables intact, so numbers can be read
   out of a table element instead of a PDF. This is the cheap path and it is why the
   screening table carries an `in_epmc` column at all.
2. **Open-access PDFs** from the link OpenAlex reports. Best effort: many publishers refuse
   an automated request, and the ones that refuse are listed for a person to fetch by hand.

Everything lands in resources/fulltext/, which is gitignored along with the rest of
resources/ - the repository keeps the extraction table, not the papers.

Writes docs/literature-review/fulltext_todo.md: what was fetched, and the exact list of
papers that need a person with a library login.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING_CSV = REPO_ROOT / "data" / "search" / "screening.csv"
FULLTEXT_DIR = REPO_ROOT / "resources" / "fulltext"
TODO_MD = REPO_ROOT / "docs" / "literature-review" / "fulltext_todo.md"

EPMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
EPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
USER_AGENT = "BedrestToMars-literature-review/1.0 (academic use)"
# PMC serves its PDFs only to a browser-shaped request.
BROWSER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"

csv.field_size_limit(10_000_000)


def safe_name(row: dict) -> str:
    author = (row["authors"].split(",")[0].split(";")[0] or "anon").strip().lower()
    author = "".join(character for character in author if character.isalnum())[:20]
    return f"{author or 'anon'}{row['year']}_{row['record_id']}"


def fetch(url: str, timeout: int = 60, attempts: int = 3, browser_agent: bool = False) -> bytes:
    """Fetch with a short backoff - Europe PMC rate-limits a burst of requests."""
    last_error = None
    agent = BROWSER_AGENT if browser_agent else USER_AGENT
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": agent})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - the caller reports the class
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise last_error


def pmcid_for_doi(doi: str) -> str:
    """Europe PMC sometimes holds a full text the screening table did not know about."""
    if not doi:
        return ""
    query = urllib.parse.urlencode({"query": f'DOI:"{doi}"', "format": "json", "resultType": "lite"})
    try:
        payload = json.loads(fetch(f"{EPMC_SEARCH}?{query}", attempts=2).decode("utf-8"))
    except Exception:
        return ""
    for result in payload.get("resultList", {}).get("result", []):
        if result.get("pmcid") and result.get("inEPMC") == "Y":
            return result["pmcid"]
    return ""


def fetch_epmc(row: dict) -> tuple:
    path = FULLTEXT_DIR / f"{safe_name(row)}.xml"
    if path.exists() and path.stat().st_size > 2000:
        return "cached", path
    try:
        content = fetch(EPMC_FULLTEXT.format(pmcid=row["pmcid"]))
    except Exception as error:
        return f"failed: {type(error).__name__}", None
    if len(content) < 2000 or b"<article" not in content[:4000]:
        return "failed: no article body", None
    path.write_bytes(content)
    return "ok", path


def fetch_pmc_pdf(row: dict) -> tuple:
    """Some PMC deposits carry a PDF but no XML - author manuscripts, mostly."""
    if not row.get("pmcid"):
        return "no pmcid", None
    path = FULLTEXT_DIR / f"{safe_name(row)}.pdf"
    if path.exists() and path.stat().st_size > 20000:
        return "cached", path
    url = f"https://pmc.ncbi.nlm.nih.gov/articles/{row['pmcid']}/pdf/"
    try:
        content = fetch(url, attempts=2, browser_agent=True)
    except Exception as error:
        return f"failed: {type(error).__name__}", None
    if not content.startswith(b"%PDF"):
        return "failed: not a PDF", None
    path.write_bytes(content)
    return "ok", path


def fetch_pdf(row: dict) -> tuple:
    url = row["oa_url"]
    if not url:
        return "no link", None
    path = FULLTEXT_DIR / f"{safe_name(row)}.pdf"
    if path.exists() and path.stat().st_size > 20000:
        return "cached", path
    try:
        content = fetch(url)
    except Exception as error:
        return f"failed: {type(error).__name__}", None
    if not content.startswith(b"%PDF"):
        return "failed: not a PDF", None
    path.write_bytes(content)
    return "ok", path


def main() -> int:
    FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)

    with SCREENING_CSV.open(encoding="utf-8-sig", newline="") as handle:
        included = [r for r in csv.DictReader(handle) if r["screen_ta"] == "include"]

    results = Counter()
    fetched, manual = [], []

    for row in included:
        if row["in_epmc"] == "yes" and row["pmcid"]:
            status, path = fetch_epmc(row)
            source = "europepmc-xml"
            if status.startswith("failed"):
                status, path = fetch_pmc_pdf(row)
                source = "pmc-pdf"
        elif row["is_oa"] == "yes":
            status, path = fetch_pdf(row)
            source = "oa-pdf"
            if status.startswith("failed"):
                found = pmcid_for_doi(row["doi"])
                if found:
                    row["pmcid"] = found
                    status, path = fetch_epmc(row)
                    source = "europepmc-xml"
                    if status.startswith("failed"):
                        status, path = fetch_pmc_pdf(row)
                        source = "pmc-pdf"
        else:
            status, path, source = "needs library access", None, "closed"

        results[f"{source}: {status.split(':')[0]}"] += 1
        record = (row, source, status, path)
        (fetched if status in {"ok", "cached"} else manual).append(record)
        print(f"  {status:26s} {source:14s} {row['title'][:60]}")
        if status == "ok":
            time.sleep(0.3)

    write_todo(fetched, manual)

    print()
    for key, count in results.most_common():
        print(f"{key:34s} {count}")
    print(f"\n{len(fetched)} of {len(included)} full texts on disk in resources/fulltext/")
    print(f"{len(manual)} need a person - see {TODO_MD.relative_to(REPO_ROOT)}")
    return 0


def write_todo(fetched: list, manual: list) -> None:
    xml = [f for f in fetched if f[1] == "europepmc-xml"]
    pdf = [f for f in fetched if f[1] in {"oa-pdf", "pmc-pdf"}]
    closed = [m for m in manual if m[1] == "closed"]
    failed = [m for m in manual if m[1] != "closed"]

    lines = [
        "# Full Texts — what is on disk and what needs a person",
        "",
        f"Generated by `framework/fetch_fulltexts.py`. {len(fetched)} of "
        f"{len(fetched) + len(manual)} included studies were fetched automatically into",
        "`resources/fulltext/` (gitignored, so they live in the shared Drive folder only).",
        "",
        "| Source | Studies | Usable for |",
        "|---|---|---|",
        f"| Europe PMC XML | {len(xml)} | Tables can be read directly; the cheap extraction path |",
        f"| Open-access PDF | {len(pdf)} | Reading by hand |",
        f"| Publisher refused the automated request | {len(failed)} | Needs a browser |",
        f"| No open version found | {len(closed)} | Needs a library login |",
        "",
        "---",
        "",
        "## Needs a library login",
        "",
        "These have no open version. Download the PDF and drop it in `resources/fulltext/`",
        "using the filename in the first column, so the extraction scripts find it.",
        "",
        "| Filename to save as | Year | Study | Link |",
        "|---|---|---|---|",
    ]
    for row, _source, _status, _path in closed:
        link = f"https://doi.org/{row['doi']}" if row["doi"] else row["url"]
        lines.append(f"| `{safe_name(row)}.pdf` | {row['year']} | {row['title'][:90]} | [{row['doi'] or 'link'}]({link}) |")

    lines += [
        "",
        "## Open access, but the publisher blocked the automated download",
        "",
        "Free to read — they just refuse a script. Opening each link in a browser and saving",
        "the PDF takes about a minute each.",
        "",
        "| Filename to save as | Year | Study | Link |",
        "|---|---|---|---|",
    ]
    for row, _source, status, _path in failed:
        link = row["oa_url"] or (f"https://doi.org/{row['doi']}" if row["doi"] else row["url"])
        lines.append(f"| `{safe_name(row)}.pdf` | {row['year']} | {row['title'][:90]} | [open]({link}) |")

    lines += [
        "",
        "## Already on disk",
        "",
        "| File | Year | Study |",
        "|---|---|---|",
    ]
    for row, source, _status, path in fetched:
        lines.append(f"| `{path.name}` | {row['year']} | {row['title'][:95]} |")

    lines.append("")
    TODO_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
