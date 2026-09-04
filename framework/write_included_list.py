"""Write the human-readable list of studies included at title/abstract.

Usage:
    python framework/write_included_list.py

Produces docs/literature-review/included_studies.md - the handover document between
screening and extraction. It carries titles, identifiers and how each paper can be read,
which is safe to commit; the bulk records stay out of git.

Ordered by how cheap the paper is to extract, because that is the order the extraction week
should work in: full text in Europe PMC first, then open access, then the rest.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING_CSV = REPO_ROOT / "data" / "search" / "screening.csv"
OUT_MD = REPO_ROOT / "docs" / "literature-review" / "included_studies.md"

csv.field_size_limit(10_000_000)

ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}


def main() -> int:
    with SCREENING_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["screen_ta"] == "include"]

    rows.sort(key=lambda r: (ORDER.get(r["extractability"], 3), -int(r["year"] or 0)))

    lines = [
        "# Studies Included at Title/Abstract",
        "",
        f"{len(rows)} records, screened on {date.today().isoformat()}. This is the queue for",
        "full-text screening and extraction, ordered by how cheap each paper is to mine.",
        "",
        "`epmc` means Europe PMC holds the full text, so it can be pulled as XML with its",
        "tables intact - the same route that produced the Dulac full text in P0. `oa` means",
        "open access but not machine-readable. Everything else needs library access.",
        "",
        "Inclusion here is a title-and-abstract judgement. A paper only earns a place in the",
        "dataset once the full text shows a baseline and a follow-up value, or a percent",
        "change, per arm and per muscle. Expect some of these to fall at that step; record the",
        "reason in `screen_ft` when they do.",
        "",
        "| # | Year | Access | Study | Identifier |",
        "|---|---|---|---|---|",
    ]

    for index, row in enumerate(rows, start=1):
        access = "epmc" if row["in_epmc"] == "yes" else ("oa" if row["is_oa"] == "yes" else "-")
        title = row["title"].replace("|", "-")[:120]
        if row["doi"]:
            identifier = f"[{row['doi']}](https://doi.org/{row['doi']})"
        elif row["pmid"]:
            identifier = f"PMID {row['pmid']}"
        else:
            identifier = row["other_id"] or row["record_id"]
        lines.append(f"| {index} | {row['year']} | {access} | {title} | {identifier} |")

    access_counts = Counter(
        "epmc" if r["in_epmc"] == "yes" else ("oa" if r["is_oa"] == "yes" else "closed")
        for r in rows
    )
    registry = [r for r in rows if r["registry_id"]]

    lines += [
        "",
        "## What this queue looks like",
        "",
        f"- **Machine-readable full text (Europe PMC): {access_counts['epmc']}**",
        f"- Open access, read by hand: {access_counts['oa']}",
        f"- Needs library access: {access_counts['closed']}",
        f"- Carrying a trial registry ID already: {len(registry)}",
        "",
        "## Before extraction starts",
        "",
        "1. **Give every study a `cohort_id`** in `data/cohorts.csv`, matched on registry ID",
        "   where one exists. Several of these are the same campaign reported twice - the",
        "   McGill 14-day series, the WISE-2005 papers, the 60-day artificial-gravity studies.",
        "   Two papers from one campaign are one cohort, and that is what the validation depends on.",
        "2. **Pull the Europe PMC full texts in bulk** rather than one at a time.",
        "3. **Work top to bottom.** The cheap papers first means the dataset exists early and",
        "   grows, rather than arriving all at once in the last two days.",
        "",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(REPO_ROOT)} with {len(rows)} studies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
