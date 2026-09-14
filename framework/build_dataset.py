"""Freeze the modelling dataset from the three extraction tables.

    python framework/build_dataset.py

Reads the main, partial and figure tables in data/raw/, drops every row flagged as a second
copy of an observation another row already carries (see data/reconciliation_log.md), and
writes data/dataset_v<VERSION>.csv - the 61 schema columns with a source_table column in
front - plus its SHA-256 in data/dataset_v<VERSION>.sha256.

Everything a model might filter on stays in: spaceflight, dry immersion, recovery, DXA,
partial and figure-derived rows all remain, each identifiable by its own column. Choosing the
modelling subset is a decision for the framework's config, not a property of this file.

A written version is frozen. Rebuilding an unchanged dataset is a no-op. If the file has been
edited by hand, or the tables no longer rebuild it, the build stops rather than overwrite it:
a change to the data is a new VERSION and an entry in the reconciliation log.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter
from pathlib import Path

VERSION = "1.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
TABLES = {
    "main": REPO_ROOT / "data" / "raw" / "extraction_qaragoz.csv",
    "partial": REPO_ROOT / "data" / "raw" / "extraction_partial.csv",
    "figures": REPO_ROOT / "data" / "raw" / "extraction_figures.csv",
}
COHORTS = REPO_ROOT / "data" / "cohorts.csv"
OUT = REPO_ROOT / "data" / f"dataset_v{VERSION}.csv"
CHECKSUM = REPO_ROOT / "data" / f"dataset_v{VERSION}.sha256"

# qc_flag tokens marking a row as the second copy of an observation another row carries
DUPLICATE_FLAGS = {"duplicate_of_other_row", "duplicate_of_figure_row"}

# PLAN.md section 6: below this, in bed-rest rows, the P4 modelling is not honest
MINIMUM = {"rows": 60, "cohorts": 8, "muscles": 4, "durations": 4}


def load() -> tuple[list[dict], list[str]]:
    rows, header = [], None
    for table, path in TABLES.items():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = header or list(reader.fieldnames)
            if list(reader.fieldnames) != header:
                raise SystemExit(f"{path.name}: columns differ from the main table")
            rows.extend({"source_table": table, **row} for row in reader)
    return rows, ["source_table"] + header


def qc(rows: list[dict]) -> list[str]:
    """Checks that span the three tables; each table is validated on its own already."""
    problems = []
    repeated = [rid for rid, n in Counter(r["row_id"] for r in rows).items() if n > 1]
    if repeated:
        problems.append(f"row_id repeated across tables: {repeated}")

    with COHORTS.open(encoding="utf-8-sig", newline="") as handle:
        known = {r["cohort_id"] for r in csv.DictReader(handle)}
    orphans = sorted({r["cohort_id"] for r in rows} - known)
    if orphans:
        problems.append(f"cohort_id not in data/cohorts.csv: {orphans}")

    for r in rows:
        try:
            pct = float(r["pct_change"])
        except ValueError:
            problems.append(f"{r['row_id']}: pct_change is not a number")
            continue
        if not -80 <= pct <= 40:
            problems.append(f"{r['row_id']}: pct_change {pct} is outside -80..40")

    bed_rest = [r for r in rows if r["exposure_flag"] != "spaceflight" and r["phase"] == "bed_rest"]
    size = {"rows": len(bed_rest), "cohorts": len({r["cohort_id"] for r in bed_rest}),
            "muscles": len({r["muscle"] for r in bed_rest}),
            "durations": len({r["duration_days"] for r in bed_rest})}
    short = {k: v for k, v in size.items() if v < MINIMUM[k]}
    if short:
        problems.append(f"below the minimum viable dataset: {short}")
    return problems


def render(rows: list[dict], header: list[str]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def main() -> int:
    rows, header = load()
    kept = [r for r in rows if not DUPLICATE_FLAGS & set(r["qc_flag"].split(";"))]
    problems = qc(kept)
    if problems:
        print(f"QC failed - {OUT.name} not written:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    content = render(kept, header)
    digest = hashlib.sha256(content).hexdigest()

    if OUT.exists():
        existing = OUT.read_bytes()
        recorded = CHECKSUM.read_text(encoding="utf-8").split()[0] if CHECKSUM.exists() else None
        if recorded and hashlib.sha256(existing).hexdigest() != recorded:
            print(f"{OUT.name} no longer matches {CHECKSUM.name}: the frozen file was edited. "
                  "Restore it from git; nothing was written.")
            return 1
        if existing != content:
            print(f"{OUT.name} is frozen and the tables no longer rebuild it. Bump VERSION and "
                  "log the change in data/reconciliation_log.md; nothing was written.")
            return 1
        print(f"{OUT.name} unchanged: {len(kept)} rows, sha256 {digest[:12]}")
        return 0

    OUT.write_bytes(content)
    CHECKSUM.write_text(f"{digest}  {OUT.name}\n", encoding="utf-8", newline="\n")
    print(f"froze {OUT.name}: {len(kept)} rows ({len(rows) - len(kept)} duplicates dropped), "
          f"{len({r['study_id'] for r in kept})} studies, "
          f"{len({r['cohort_id'] for r in kept})} cohorts, sha256 {digest[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
