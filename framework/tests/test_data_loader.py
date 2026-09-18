"""Checks on loading the frozen dataset.

    python framework/tests/test_data_loader.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader


def test_config_loads_with_the_declared_seed() -> None:
    config = data_loader.load_config()
    assert config["seed"] == 20260918
    assert config["cv"]["group_column"] == "cohort_id"


def test_load_returns_the_whole_frozen_dataset() -> None:
    frame = data_loader.load()
    assert len(frame) == 737


def test_load_annotates_muscle_and_site() -> None:
    frame = data_loader.load()
    assert frame["muscle_function_class"].isin(
        {"antigravity_extensor", "flexor", "mixed"}
    ).all()
    assert (frame["muscle_family"] != "").all()
    assert frame["site_kind"].notna().all()


def test_load_keeps_provenance_columns() -> None:
    """The loader does not decide what is modelled - features.py does."""
    frame = data_loader.load()
    for column in ("row_id", "doi", "cohort_id", "page_ref"):
        assert column in frame.columns


def test_a_changed_dataset_is_refused() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "data").mkdir()
        (root / "framework").mkdir()
        shutil.copy(REPO_ROOT / "data" / "dataset_v1.0.csv", root / "data")
        shutil.copy(REPO_ROOT / "data" / "dataset_v1.0.sha256", root / "data")
        shutil.copy(REPO_ROOT / "data" / "muscle_map.csv", root / "data")
        shutil.copy(REPO_ROOT / "data" / "measurement_site_map.csv", root / "data")
        target = root / "data" / "dataset_v1.0.csv"
        target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        config = data_loader.load_config()
        try:
            data_loader.load(config, repo_root=root)
        except data_loader.DatasetChanged:
            return
    raise AssertionError("an edited dataset must be refused, not silently modelled")


def test_subset_applies_the_declared_predicates() -> None:
    frame = data_loader.subset(data_loader.load())
    assert len(frame) == 421
    assert frame["cohort_id"].nunique() == 31
    assert (frame["phase"] == "bed_rest").all()
    assert not frame["muscle"].isin({"psoas", "multifidus"}).any()


def test_target_is_inside_the_declared_range() -> None:
    config = data_loader.load_config()
    low, high = config["target"]["valid_range"]
    values = data_loader.subset(data_loader.load())[config["target"]["column"]]
    assert values.between(low, high).all()


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
