"""Checks on the measurement-site normalisation.

    python framework/tests/test_measurement_site.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import measurement_site

import data_loader

DATASET = REPO_ROOT / data_loader.load_config()["dataset"]["path"]

KINDS = {"unstated", "whole_muscle", "partial_region", "single_slice", "multi_slice_mean"}


def dataset_rows() -> list[dict[str, str]]:
    with DATASET.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_dataset_value_is_mapped() -> None:
    mapping = measurement_site.load()
    unmapped = {row["measurement_site"] for row in dataset_rows()} - set(mapping)
    assert not unmapped, f"measurement_site values missing from the map: {sorted(unmapped)}"


def test_controlled_vocabulary() -> None:
    for value, entry in measurement_site.load().items():
        assert entry.kind in KINDS, f"{value!r}: {entry.kind}"


def test_both_spellings_of_missing_collapse() -> None:
    mapping = measurement_site.load()
    assert mapping["NA"].kind == "unstated"
    assert mapping["na"].kind == "unstated"
    assert mapping["NA"].position_pct is None


def test_position_is_a_percentage_or_absent() -> None:
    for value, entry in measurement_site.load().items():
        if entry.position_pct is not None:
            assert 0 <= entry.position_pct <= 100, f"{value!r}: {entry.position_pct}"
            assert entry.kind in {"single_slice", "multi_slice_mean"}, value


def test_annotate_fills_every_row() -> None:
    rows = measurement_site.annotate(dataset_rows())
    assert len(rows) == 742
    for row in rows:
        assert row["site_kind"] in KINDS


def test_annotate_does_not_mutate_its_input() -> None:
    rows = dataset_rows()
    measurement_site.annotate(rows)
    assert "site_kind" not in rows[0]


def test_unknown_site_raises() -> None:
    rows = [{"measurement_site": "somewhere new"}]
    try:
        measurement_site.annotate(rows)
    except KeyError:
        return
    raise AssertionError("an unmapped site must raise rather than default silently")


def test_site_is_unstated_on_most_rows() -> None:
    """Half the corpus does not say where it measured - the model must not pretend it does."""
    rows = measurement_site.annotate(dataset_rows())
    unstated = sum(1 for row in rows if row["site_kind"] == "unstated")
    assert unstated == 520, unstated


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
