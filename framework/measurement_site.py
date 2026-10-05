"""Normalise `measurement_site` into something a model can use.

The column is free text as the papers wrote it, with two spellings of "not reported"
(`NA` and `na`) and forty distinct strings in all. `data/measurement_site_map.csv` turns each
one into a kind and, where the paper gave one, a position along the segment as a percentage.
The frozen dataset is never rewritten; the columns are derived at load time.

Where along a muscle you measure changes the answer - quadriceps CSA at 20% of thigh length
often shows no significant loss while 60% does - so the site has to be either a feature or a
stratification variable, and it cannot be either while it is prose.

    python framework/measurement_site.py     # print the mapping for review
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = REPO_ROOT / "data" / "measurement_site_map.csv"


@dataclass(frozen=True)
class Site:
    """One free-text site string and what it means."""

    raw: str
    kind: str
    position_pct: float | None
    reference: str
    notes: str


def load(path: Path | None = None) -> dict[str, Site]:
    """Read the map, keyed by the raw string as it appears in the dataset."""
    source = path or MAP_FILE
    entries: dict[str, Site] = {}
    with source.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = row["measurement_site"]
            if raw in entries:
                raise ValueError(f"{source.name} lists {raw!r} twice")
            position = row["site_position_pct"].strip()
            entries[raw] = Site(
                raw=raw,
                kind=row["site_kind"].strip(),
                position_pct=float(position) if position else None,
                reference=row["site_reference"].strip(),
                notes=row["notes"].strip(),
            )
    return entries


def annotate(
    rows: list[dict[str, str]], path: Path | None = None
) -> list[dict[str, str]]:
    """Return copies of `rows` with `site_kind` and `site_position_pct` added.

    Raises on a site string the map does not cover, so new free text cannot quietly become
    "unstated".
    """
    mapping = load(path)
    annotated: list[dict[str, str]] = []
    for row in rows:
        raw = row["measurement_site"]
        entry = mapping.get(raw)
        if entry is None:
            raise KeyError(f"{raw!r} is not in {MAP_FILE.name}")
        updated = dict(row)
        updated["site_kind"] = entry.kind
        updated["site_position_pct"] = (
            "" if entry.position_pct is None else str(entry.position_pct)
        )
        annotated.append(updated)
    return annotated


def main() -> int:
    mapping = load()
    by_kind: dict[str, list[Site]] = {}
    for entry in mapping.values():
        by_kind.setdefault(entry.kind, []).append(entry)
    for kind in sorted(by_kind):
        members = sorted(by_kind[kind], key=lambda site: site.raw)
        print(f"\n{kind} ({len(members)})")
        for entry in members:
            position = "" if entry.position_pct is None else f"{entry.position_pct:g}%"
            print(f"  {entry.raw:<46} {position:<6} {entry.reference}")
    print(f"\n{len(mapping)} site strings mapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
