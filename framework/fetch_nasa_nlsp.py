"""Fetch the open NASA NLSP bed-rest muscle datasets into data/nasa/.

The NASA Life Sciences Portal (nlsp.nasa.gov) publishes derived, individual-participant
CSVs from the UTMB flight-analog bed-rest campaigns as open downloads - no account, no
request form. This fetcher pulls the muscle-relevant folders only, records a manifest
with the SHA-256 of every file, and is idempotent: a file that already exists with the
expected size is re-hashed, not re-downloaded, so the script can be run again safely.

Which folders are taken, and why the others are not, is declared in EXPERIMENTS below and
argued in data/nasa/CARD.md. The load-bearing rule: nothing here is part of
dataset_v1.0.csv. The frozen dataset is untouched; folders whose campaign already has a
cohort in the frozen data are flagged in OVERLAPS_DATASET and must never be pooled with
that cohort's literature rows.

    python framework/fetch_nasa_nlsp.py            # writes data/nasa/ + MANIFEST.json
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
API = "https://nlsp.nasa.gov/api/v1"
DEST = REPO_ROOT / "data" / "nasa"
HEADERS = {
    "User-Agent": "DGLRM-BedrestToMars/1.0 (open bed-rest atrophy dataset companion)"
}
PAUSE_SECONDS = 0.15

# Experiment UUID -> the folders to take. Muscle-size outcomes only: the DXA folders that
# are bone alone (heel, forearm, hip, femur, spine) and the cycling-performance folders of
# the iRAT experiment are deliberately absent - this project models muscle size.
EXPERIMENTS: dict[str, dict[str, str]] = {
    "bb0a11e1-ecc4-5b2c-8f0f-cf7da73e159c": {  # iRAT, UTMB Campaign 11 (70-day HDBR)
        "BEDREST_IRATS_MRI_ULTRASOUND_CFT70": "per-subject MRI volumes and ultrasound thickness",
        "BEDREST_IRATS_iDXA_CFT70": "per-subject iDXA, including the demographics tables",
    },
    "caa3b09f-28b8-5c50-b0af-5f6540147f24": {  # Standard Measures iDXA, Campaign 11
        "BRSMIDXA_CFT70_iDXA": "per-subject iDXA standard measures, 70-day campaign",
    },
    "4469ebdc-0a65-55e8-bbff-3cf6b044c4c6": {  # MR035G, bone densitometry (flight analog)
        "MR035G_Campaign_1_DXA": "whole-body DXA incl. leg lean, 60-day campaign 1",
        "MR035G_Campaign_3_DXA_Whole_Body": "whole-body DXA incl. leg lean, campaign 3",
        "MR035G_Campaign_3_DXA_ReadMe": "the campaign-3 column definitions",
        "MR035G_AG_PILOT_DXA_ANALYZED": "whole-body DXA, artificial-gravity pilot campaign",
        "MR035G_MEDES_DXA": "whole-body DXA, MEDES/WISE 2005 - see OVERLAPS_DATASET",
    },
}

# Folders whose participants already have a cohort in dataset_v1.0. They are archived
# because individual-level data upgrades those cohorts, but the same campaign must never
# enter an analysis twice - once as literature rows and once as NASA rows.
OVERLAPS_DATASET: dict[str, str] = {
    "BEDREST_IRATS_MRI_ULTRASOUND_CFT70": "nasa_sprint_br70",
    "BEDREST_IRATS_iDXA_CFT70": "nasa_sprint_br70",
    "BRSMIDXA_CFT70_iDXA": "nasa_sprint_br70",
    "MR035G_MEDES_DXA": "wise2005",
}


def _get(url: str, binary: bool = False, retries: int = 2) -> Any:
    """One GET with polite retries; NLSP has been stable but this is a remote service."""
    request = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read() if binary else response.read().decode("utf-8")
        except (urllib.error.URLError, OSError):
            if attempt == retries:
                raise
            time.sleep(2.0 * (attempt + 1))


def _file_tree(experiment: str) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    """Yield (folder label, file entries) for one experiment's dataset tree."""
    payload = json.loads(_get(f"{API}/data/lsda_experiment/{experiment}/full"))
    for folder in payload["related"]["datasets"]:
        yield folder["label"], folder.get("children") or []


def _target_name(entry: dict[str, Any]) -> str:
    """The NLSP labels carry no extension; the downloads are CSV."""
    name = entry["label"]
    return name if "." in name else f"{name}.csv"


def fetch() -> dict[str, Any]:
    """Download every declared folder and write the manifest beside the data."""
    DEST.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "accessed": time.strftime("%Y-%m-%d"),
        "source": API,
        "policy": {
            "muscle_size_folders_only": True,
            "overlaps_dataset_v1_0": OVERLAPS_DATASET,
            "experiments": {
                experiment: dict(folders)
                for experiment, folders in EXPERIMENTS.items()
            },
        },
        "files": [],
    }
    downloaded = skipped = 0

    for experiment, folders in EXPERIMENTS.items():
        for folder_label, entries in _file_tree(experiment):
            if folder_label not in folders:
                continue
            folder_dir = DEST / folder_label
            folder_dir.mkdir(parents=True, exist_ok=True)
            for entry in entries:
                target = folder_dir / _target_name(entry)
                expected = int(entry.get("file_size") or 0)
                if target.exists() and target.stat().st_size == expected:
                    payload = None  # already on disk; hash it rather than re-download
                else:
                    payload = _get(f"{API}/files/{entry['key']}/download", binary=True)
                    target.write_bytes(payload)
                    downloaded += 1
                    time.sleep(PAUSE_SECONDS)
                digest = hashlib.sha256(target.read_bytes()).hexdigest()
                skipped += int(payload is None)
                manifest["files"].append(
                    {
                        "folder": folder_label,
                        "file": target.name,
                        "uuid": entry["key"],
                        "bytes": target.stat().st_size,
                        "sha256": digest,
                        "overlaps_dataset_cohort": OVERLAPS_DATASET.get(folder_label, ""),
                    }
                )
            print(f"  {folder_label:<45} {len(entries):>4} files")

    (DEST / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    total = sum(item["bytes"] for item in manifest["files"])
    print(
        f"\n{downloaded} downloaded, {skipped} already present, "
        f"{len(manifest['files'])} in manifest, {total / 1024:.0f} KB total"
    )
    return manifest


if __name__ == "__main__":
    fetch()
