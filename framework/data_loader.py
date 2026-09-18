"""Load the frozen dataset, verify it, and attach the derived columns.

The dataset is frozen and checked byte for byte against its SHA-256. If the file has been
edited, this module refuses to hand it to a model: a result computed from an unrecorded
version of the data is worse than no result, because it looks the same as a real one.

The two derived columns the model needs but the frozen file does not carry -
`muscle_function_class` / `muscle_family` and `site_kind` / `site_position_pct` - are joined
on here from their reviewable tables (`muscle_map.py`, `measurement_site.py`).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

import measurement_site
import muscle_map

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


class DatasetChanged(RuntimeError):
    """The dataset on disk is not the frozen one the config names."""


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Read `config.yaml`. Every declared choice in the framework comes from here."""
    with (path or CONFIG_PATH).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _verify_sha256(dataset: Path, expected_file: Path) -> None:
    expected = expected_file.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(dataset.read_bytes()).hexdigest()
    if actual != expected:
        raise DatasetChanged(
            f"{dataset.name} hashes to {actual[:12]}… but {expected_file.name} "
            f"expects {expected[:12]}…. Freeze a new version rather than editing v1.0."
        )


def load(
    config: dict[str, Any] | None = None, repo_root: Path | None = None
) -> pd.DataFrame:
    """Return every row of the frozen dataset, verified and annotated."""
    config = config or load_config()
    root = repo_root or REPO_ROOT
    dataset = root / config["dataset"]["path"]

    if config["dataset"].get("verify_sha256", True):
        _verify_sha256(dataset, root / config["dataset"]["sha256_path"])

    rows = pd.read_csv(dataset, dtype=str, keep_default_na=False).to_dict("records")
    rows = muscle_map.annotate(rows, path=root / config["maps"]["muscle"])
    rows = measurement_site.annotate(
        rows, path=root / config["maps"]["measurement_site"]
    )

    frame = pd.DataFrame(rows)
    for column in ("duration_days", "timepoint_days", "pct_change", "n_analysed"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def subset(
    frame: pd.DataFrame, config: dict[str, Any] | None = None
) -> pd.DataFrame:
    """Apply the subset predicates declared in the config (DESIGN.md section 3)."""
    config = config or load_config()
    rules = config["subset"]
    kept = frame[frame["phase"] == rules["phase"]]
    kept = kept[~kept["muscle"].isin(rules["drop_muscles"])]
    return kept.reset_index(drop=True)


def main() -> int:
    config = load_config()
    frame = subset(load(config), config)
    print(f"{len(frame)} rows, {frame['cohort_id'].nunique()} cohorts, "
          f"{frame['study_id'].nunique()} studies")
    print(frame.groupby("muscle_function_class")["pct_change"].agg(["count", "mean"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
