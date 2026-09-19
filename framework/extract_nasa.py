"""Turn the open NASA NLSP bed-rest DXA archive into extraction rows for the dataset.

    python framework/extract_nasa.py            # writes data/raw/extraction_nasa.csv

Only one of the seven folders in `data/nasa/` can enter the pooled dataset, and the reasons
the other six cannot are the rules written in `data/nasa/CARD.md`:

- `BEDREST_IRATS_*_CFT70` and `BRSMIDXA_CFT70_iDXA` are the campaign behind cohort
  `nasa_sprint_br70`, and `MR035G_MEDES_DXA` is the campaign behind `wise2005`. Their
  participants are already in the dataset as literature rows. Pooling them would be a double
  count, not an upgrade, so they stay a companion set for external validation.
- `MR035G_Campaign_1_DXA` and `MR035G_AG_PILOT_DXA_ANALYZED` carry no `TEST_PHASE` and no
  `BR_DAY` column anywhere in the folder - only scan dates. Which scan is the baseline and
  which is the follow-up would have to be guessed from the calendar, and schema rule 1
  forbids imputing it.

That leaves `MR035G_Campaign_3_DXA_Whole_Body`, which labels every scan with its phase and
its day relative to the start of bed rest, and carries `L_LEG_LEAN` and `R_LEG_LEAN`.

Campaign 3 ran in eight lettered blocks between 2005 and 2010, and they are not all the same
length. This script therefore does not take the folder's word for anything: for every
participant it derives the start of bed rest from a pre-test scan (`SCAN_DATE` plus `BR_DAY`,
which counts down to the start) and the end from a post-test scan (`SCAN_DATE` minus
`BR_DAY`, which counts up from the end), and keeps only the blocks whose derived duration
agrees with the duration declared in BLOCKS below. Blocks whose scan dates are missing, or
whose participants only ever produced a post-test scan, are dropped and named in the report.

One output row is one measurement occasion for the arm, aggregated over the participants
measured at it - the same grain as every other row in `data/dataset_v1.x.csv`. The
individual trajectories are deliberately *not* emitted: the participants inside one campaign
are not independent observations, and a leave-one-cohort-out design that treated them as
such would be measuring its own bookkeeping (`data/nasa/CARD.md`, rule 2).
"""

from __future__ import annotations

import csv
import datetime
import glob
import os
import statistics
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "data" / "nasa" / "MR035G_Campaign_3_DXA_Whole_Body"
TEMPLATE = REPO_ROOT / "data" / "extraction_template.csv"
OUT = REPO_ROOT / "data" / "raw" / "extraction_nasa.csv"

# The NLSP experiment these files belong to, for anyone tracing a row back to the archive.
EXPERIMENT_UUID = "4469ebdc-0a65-55e8-bbff-3cf6b044c4c6"
SOURCE_REF = "data/nasa/MR035G_Campaign_3_DXA_Whole_Body"

STUDY_ID = "nlsp_mr035g_c3"
COHORT_ID = "nasa_utmb_c3"
ACCESS_YEAR = "2026"          # the year the archive was fetched; the campaign itself ran 2005-2007
EXTRACTION_DATE = "2026-09-19"

# Blocks of Campaign 3 that may be pooled, with the bed-rest duration each one must turn out
# to have. A block whose participants' scan dates give a different answer is a block this
# script has misunderstood, and it stops rather than write the row.
BLOCKS = {"C3A": 90, "C3C": 90, "C3D": 90}
DURATION_TOLERANCE_DAYS = 3   # scheduling scatter around the planned length, not a difference

# Measurement occasions, as windows on BR_DAY. A window collects the scans a block scheduled
# as one occasion; the row is then labelled with the mean of the days actually scanned, so
# the label is a fact about the scans rather than about the window.
BED_REST_WINDOWS = [(28, 32), (43, 47), (55, 59), (60, 67)]
RECOVERY_WINDOW = (1, 5)      # days after reambulation; the 6-month and 1-year rescans carry
                              # TEST_PHASE = NA and are skipped with the rest of the unlabelled scans


def parse_date(value: str) -> datetime.date | None:
    for pattern in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.datetime.strptime((value or "").strip(), pattern).date()
        except ValueError:
            continue
    return None


def parse_int(value: str) -> int | None:
    try:
        return int(float((value or "").strip()))
    except ValueError:
        return None


def load_scans() -> list[dict]:
    """Every labelled leg-lean scan in the folder, each one counted once.

    The same scan is published several times over - once in a block's combined file and
    again in the per-participant files - so scans are keyed by what they measured rather
    than by file. Averaging a duplicate would not move a mean, but counting one would
    overstate how many measurements a row rests on.
    """
    unique: dict[tuple, dict] = {}
    for path in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.csv"))):
        with open(path, encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows or "L_LEG_LEAN" not in rows[0]:
            continue
        for row in rows:
            phase = (row.get("TEST_PHASE") or "").strip()
            if phase in ("", "NA"):
                continue  # unlabelled: the 6-month and 1-year rescans, and a few stray scans
            try:
                legs_g = float(row["L_LEG_LEAN"]) + float(row["R_LEG_LEAN"])
            except (TypeError, ValueError):
                continue
            day = parse_int(row.get("BR_DAY", ""))
            if day is None:
                continue
            scan = {
                "block": (row.get("CAMPAIGN") or "").strip(),
                "subject": (row.get("SUBJECT") or "").strip(),
                "phase": phase,
                "day": day,
                "date": parse_date(row.get("SCAN_DATE", "")),
                "legs_kg": round(legs_g / 1000.0, 6),
                "sex": (row.get("SEX") or "").strip(),
                "age": parse_int(row.get("AGE") or row.get("Age") or ""),
            }
            key = (scan["block"], scan["subject"], phase, day, scan["date"], scan["legs_kg"])
            unique.setdefault(key, scan)
    return list(unique.values())


def by_participant(scans: list[dict]) -> dict[tuple, dict]:
    """Collapse the scans into one record per participant: a baseline and its follow-ups."""
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for scan in scans:
        grouped[(scan["block"], scan["subject"])].append(scan)

    people = {}
    for who, own in grouped.items():
        pre = [s for s in own if s["phase"] == "PRE_TEST"]
        if not pre:
            continue  # no baseline: schema section 1 - a row always compares against one
        starts = [s["date"] + datetime.timedelta(days=s["day"]) for s in pre if s["date"]]
        ends = [s["date"] - datetime.timedelta(days=s["day"])
                for s in own if s["phase"] == "POST_TEST" and s["date"]]
        ages = [s["age"] for s in own if s["age"]]
        occasions = defaultdict(list)
        for scan in own:
            if scan["phase"] != "PRE_TEST":
                occasions[(scan["phase"], scan["day"])].append(scan["legs_kg"])
        people[who] = {
            "block": who[0],
            "subject": who[1],
            "baseline_kg": statistics.fmean(s["legs_kg"] for s in pre),
            "start": min(starts) if starts else None,
            "end": min(ends) if ends else None,
            "sex": next((s["sex"] for s in own if s["sex"]), ""),
            "age": min(ages) if ages else None,
            "occasions": {key: statistics.fmean(values) for key, values in occasions.items()},
        }
    return people


def check_blocks(people: dict[tuple, dict]) -> tuple[dict[str, list[dict]], list[str]]:
    """Keep the declared blocks, and only once their own dates confirm the declared length."""
    kept: dict[str, list[dict]] = defaultdict(list)
    report = []
    for block in sorted({p["block"] for p in people.values()}):
        members = [p for p in people.values() if p["block"] == block]
        if block not in BLOCKS:
            report.append(f"  {block}: not pooled - no declared duration in BLOCKS")
            continue
        declared = BLOCKS[block]
        measured = [(p["end"] - p["start"]).days for p in members if p["start"] and p["end"]]
        if not measured:
            report.append(f"  {block}: not pooled - no participant has both a dated "
                          f"pre-test and a dated post-test scan")
            continue
        off = [d for d in measured if abs(d - declared) > DURATION_TOLERANCE_DAYS]
        if off:
            raise SystemExit(
                f"{block}: declared {declared} days, but the scan dates give {sorted(set(measured))}. "
                "Either BLOCKS is wrong or the files changed; nothing was written."
            )
        kept[block] = members
        report.append(f"  {block}: pooled - {len(members)} participants, "
                      f"{declared} days confirmed by {len(measured)} of them "
                      f"({sorted(set(measured))})")
    return kept, report


def occasion_rows(kept: dict[str, list[dict]]) -> list[dict]:
    """One row per measurement occasion, pooled across the blocks that share a duration."""
    duration = {BLOCKS[block] for block in kept}
    if len(duration) != 1:
        raise SystemExit(f"the pooled blocks do not share a duration: {sorted(duration)}")
    duration_days = duration.pop()

    members = [person for block in kept for person in kept[block]]
    arm_size = len(members)
    windows = [("bed_rest", low, high) for low, high in BED_REST_WINDOWS]
    windows.append(("recovery", *RECOVERY_WINDOW))

    rows = []
    for phase, low, high in windows:
        source_phase = "IN_TEST" if phase == "bed_rest" else "POST_TEST"
        contributions = []
        for person in members:
            days = [day for (scan_phase, day) in person["occasions"]
                    if scan_phase == source_phase and low <= day <= high]
            if not days:
                continue
            if len(days) > 1:
                raise SystemExit(f"{person['block']}/{person['subject']}: days {days} all fall in "
                                 f"the {phase} window {low}-{high}; the windows overlap an occasion")
            day = days[0]
            follow_up = person["occasions"][(source_phase, day)]
            contributions.append({
                "person": person,
                "day": day,
                "baseline_kg": person["baseline_kg"],
                "followup_kg": follow_up,
                "pct": (follow_up - person["baseline_kg"]) / person["baseline_kg"] * 100.0,
            })
        if not contributions:
            continue

        pct_changes = [c["pct"] for c in contributions]
        day_mean = round(statistics.fmean(c["day"] for c in contributions))
        ages = [c["person"]["age"] for c in contributions if c["person"]["age"]]
        females = [c for c in contributions if c["person"]["sex"] == "F"]
        rows.append({
            "phase": phase,
            "timepoint_days": duration_days + day_mean if phase == "recovery" else day_mean,
            "days_from_unloading_end": day_mean if phase == "recovery" else None,
            "duration_days": duration_days,
            "n_arm": arm_size,
            "n_analysed": len(contributions),
            "baseline_kg": statistics.fmean(c["baseline_kg"] for c in contributions),
            "followup_kg": statistics.fmean(c["followup_kg"] for c in contributions),
            "pct_change": statistics.fmean(pct_changes),
            "pct_sd": statistics.stdev(pct_changes) if len(pct_changes) > 1 else None,
            "age_mean": statistics.fmean(ages) if ages else None,
            "n_with_age": len(ages),
            "pct_female": len(females) / len(contributions) * 100.0,
            "sex": "mixed" if females and len(females) < len(contributions)
                   else ("F" if females else "M"),
            "days_spanned": sorted({c["day"] for c in contributions}),
            "blocks": sorted({c["person"]["block"] for c in contributions}),
        })
    return rows


def number(value: float | None, digits: int) -> str:
    return "NA" if value is None else f"{value:.{digits}f}"


def to_schema(row: dict) -> dict:
    """Fill the 61 schema columns for one occasion."""
    note = (
        f"NASA NLSP open data, experiment {EXPERIMENT_UUID}, UTMB Campaign 3 block(s) "
        f"{'+'.join(row['blocks'])}; computed by framework/extract_nasa.py from L_LEG_LEAN + "
        f"R_LEG_LEAN. Scanned on BR_DAY {', '.join(str(d) for d in row['days_spanned'])}; "
        f"age known for {row['n_with_age']} of {row['n_analysed']} participants"
    )
    qc = ["pct_of_individual_means", "repository_row"]
    if row["n_with_age"] < row["n_analysed"]:
        qc.append("age_partially_published")

    record = {
        "study_id": STUDY_ID,
        "cohort_id": COHORT_ID,
        "campaign_name": "NASA Flight Analog Project, UTMB Campaign 3 (MR035G)",
        "registry_id": "NA",
        "first_author": "NA",
        "year": ACCESS_YEAR,
        "doi": "NA",
        "source_file": SOURCE_REF,
        "design": "HDBR_-6",
        "hdt_angle_deg": "-6",
        "duration_days": str(row["duration_days"]),
        "phase": row["phase"],
        "timepoint_days": str(row["timepoint_days"]),
        "days_from_unloading_end": ("NA" if row["days_from_unloading_end"] is None
                                    else str(row["days_from_unloading_end"])),
        "exposure_flag": "analogue",
        "arm_id": "ctrl",
        "arm_type": "control",
        "cm_modality": "none",
        "cm_dose": "NA",
        "n_arm": str(row["n_arm"]),
        "n_analysed": str(row["n_analysed"]),
        "sex": row["sex"],
        "pct_female": number(row["pct_female"], 1) if row["sex"] == "mixed" else "NA",
        "age_mean": number(row["age_mean"], 1),
        "age_sd": "NA",
        "age_min": "NA",
        "age_max": "NA",
        "population": "healthy_young",
        "bmi_mean": "NA",
        "body_mass_mean_kg": "NA",
        "nutrition_controlled": "NA",
        "muscle": "whole_lower_limb",
        "muscle_function_class": "NA",
        "is_composite": "TRUE",
        "composite_of": "NA",
        "laterality": "mean",
        "measurement_site": "NA",
        "outcome_type": "lean_mass",
        "modality": "DXA",
        "unit_original": "g",
        "value_baseline_original": number(row["baseline_kg"] * 1000.0, 1),
        "value_followup_original": number(row["followup_kg"] * 1000.0, 1),
        "unit_si": "kg",
        "value_baseline": number(row["baseline_kg"], 3),
        "value_followup": number(row["followup_kg"], 3),
        "change_absolute": number(row["followup_kg"] - row["baseline_kg"], 3),
        "pct_change": number(row["pct_change"], 2),
        "variance_of": "change" if row["pct_sd"] is not None else "NA",
        "variance_type": "SD" if row["pct_sd"] is not None else "NA",
        "variance_value": number(row["pct_sd"], 2),
        "p_value": "NA",
        "data_source": "repository",
        "digitizer_tool": "NA",
        "page_ref": f"{SOURCE_REF}, columns L_LEG_LEAN + R_LEG_LEAN",
        "extractor": "qaragoz",
        "extraction_date": EXTRACTION_DATE,
        "extraction_confidence": "high",
        "double_extracted": "FALSE",
        "qc_flag": ";".join(qc),
        "notes": note,
    }
    record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                        "__{modality}_{outcome_type}").format(**record)
    return record


def main() -> int:
    with TEMPLATE.open(encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle))

    people = by_participant(load_scans())
    kept, report = check_blocks(people)
    print(f"{len(people)} participants with a baseline in {SOURCE_DIR.name}:")
    for line in report:
        print(line)
    if not kept:
        print("nothing to pool; no file written")
        return 1

    rows = [to_schema(row) for row in occasion_rows(kept)]
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nwrote {OUT.relative_to(REPO_ROOT)}: {len(rows)} rows")
    for row in rows:
        print(f"  {row['phase']:8s} day {row['timepoint_days']:>3s}  n={row['n_analysed']:>2s}  "
              f"{row['value_baseline']:>7s} -> {row['value_followup']:>7s} kg  "
              f"{row['pct_change']:>6s}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
