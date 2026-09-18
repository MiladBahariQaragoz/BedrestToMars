"""Checks on the muscle map and the annotation it drives.

Run directly - the project has no test runner dependency:

    python framework/tests/test_muscle_map.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import csv

import muscle_map

DATASET = REPO_ROOT / "data" / "dataset_v1.0.csv"

CLASSES = {"antigravity_extensor", "flexor", "mixed"}
FAMILIES = {
    "knee_extensors",
    "knee_flexors",
    "plantar_flexors",
    "dorsiflexors",
    "evertors",
    "hip_extensors",
    "hip_abductors",
    "hip_flexors",
    "hip_adductors",
    "hip_rotators",
    "trunk_extensors",
    "whole_limb",
}


def dataset_rows() -> list[dict[str, str]]:
    with DATASET.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_dataset_muscle_is_mapped() -> None:
    mapping = muscle_map.load()
    unmapped = {row["muscle"] for row in dataset_rows()} - set(mapping)
    assert not unmapped, f"muscles missing from the map: {sorted(unmapped)}"


def test_no_entry_is_unused() -> None:
    """A map entry for a muscle nobody measured is a typo until proven otherwise."""
    mapping = muscle_map.load()
    measured = {row["muscle"] for row in dataset_rows()}
    unused = set(mapping) - measured
    assert not unused, f"map entries for muscles not in the dataset: {sorted(unused)}"


def test_controlled_vocabulary() -> None:
    for muscle, entry in muscle_map.load().items():
        assert entry.function_class in CLASSES, f"{muscle}: {entry.function_class}"
        assert entry.family in FAMILIES, f"{muscle}: {entry.family}"


def test_components_refer_to_known_muscles() -> None:
    mapping = muscle_map.load()
    for muscle, entry in mapping.items():
        for component in entry.components:
            assert component in mapping, f"{muscle} lists unknown component {component}"
            assert component != muscle, f"{muscle} lists itself as a component"


def test_components_only_on_composites() -> None:
    """Only muscles the dataset marks composite may declare components."""
    composite = {
        row["muscle"] for row in dataset_rows() if row["is_composite"] == "TRUE"
    }
    for muscle, entry in muscle_map.load().items():
        if entry.components:
            assert muscle in composite, f"{muscle} declares components but is not composite"


def test_every_rationale_is_written() -> None:
    for muscle, entry in muscle_map.load().items():
        assert len(entry.rationale) > 20, f"{muscle} has no usable rationale"


def test_annotate_fills_every_row() -> None:
    rows = muscle_map.annotate(dataset_rows())
    assert len(rows) == 737
    for row in rows:
        assert row["muscle_function_class"] in CLASSES
        assert row["muscle_family"] in FAMILIES


def test_annotate_does_not_mutate_its_input() -> None:
    rows = dataset_rows()
    before = rows[0]["muscle_function_class"]
    muscle_map.annotate(rows)
    assert rows[0]["muscle_function_class"] == before


def test_annotate_overwrites_the_frozen_placeholder() -> None:
    """The frozen dataset ships muscle_function_class as NA on every row."""
    raw = dataset_rows()
    assert {row["muscle_function_class"] for row in raw} == {"NA"}
    annotated = muscle_map.annotate(raw)
    assert "NA" not in {row["muscle_function_class"] for row in annotated}


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
