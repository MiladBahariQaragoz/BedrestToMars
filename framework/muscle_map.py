"""The muscle map: functional class and family for every muscle in the dataset.

`muscle_function_class` ships as `NA` in the frozen dataset because assigning it is a
judgement about physiology rather than an extraction (`PLAN.md` task 2.7). The judgement
lives in `data/muscle_map.csv`, one reviewable line per muscle with its reasoning, and this
module joins it onto the rows at load time. The frozen dataset is never rewritten.

    python framework/muscle_map.py          # print the assignment for review
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = REPO_ROOT / "data" / "muscle_map.csv"


@dataclass(frozen=True)
class Muscle:
    """One muscle's functional assignment."""

    name: str
    family: str
    function_class: str
    components: tuple[str, ...]
    fibre_profile: str
    rationale: str


def load(path: Path | None = None) -> dict[str, Muscle]:
    """Read the map, keyed by muscle name."""
    source = path or MAP_FILE
    entries: dict[str, Muscle] = {}
    with source.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = row["muscle"].strip()
            if name in entries:
                raise ValueError(f"{source.name} lists {name} twice")
            components = tuple(
                part for part in row["components"].split("|") if part.strip()
            )
            entries[name] = Muscle(
                name=name,
                family=row["muscle_family"].strip(),
                function_class=row["muscle_function_class"].strip(),
                components=components,
                fibre_profile=row["fibre_profile"].strip(),
                rationale=row["rationale"].strip(),
            )
    return entries


def annotate(
    rows: list[dict[str, str]], path: Path | None = None
) -> list[dict[str, str]]:
    """Return copies of `rows` with `muscle_function_class` and `muscle_family` filled.

    Raises if a row names a muscle the map does not cover, so a new muscle entering the
    extraction cannot silently arrive unclassified.
    """
    mapping = load(path)
    annotated: list[dict[str, str]] = []
    for row in rows:
        muscle = row["muscle"]
        entry = mapping.get(muscle)
        if entry is None:
            raise KeyError(f"{muscle} is not in {MAP_FILE.name}")
        updated = dict(row)
        updated["muscle_function_class"] = entry.function_class
        updated["muscle_family"] = entry.family
        annotated.append(updated)
    return annotated


def main() -> int:
    mapping = load()
    by_class: dict[str, list[Muscle]] = {}
    for entry in mapping.values():
        by_class.setdefault(entry.function_class, []).append(entry)
    for function_class in sorted(by_class):
        members = sorted(by_class[function_class], key=lambda m: (m.family, m.name))
        print(f"\n{function_class} ({len(members)})")
        for entry in members:
            print(f"  {entry.family:<16} {entry.name:<40} {entry.rationale}")
    print(f"\n{len(mapping)} muscles mapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
