"""Extract De Martino et al. 2022 (AGBRESA reconditioning, lumbopelvic muscles).

    python framework/extractors/demartino2022_agbresa_spine.py

Source: Europe PMC full text of the study behind screening record scopus_00516. Table 2
reports muscle volume in mm3 for four lumbopelvic muscles at up to five intervertebral disc
levels, in two reconditioning arms, at baseline, the end of 60-day head-down tilt, and
recovery day 13.

Two things make this paper worth a parser of its own. It is the same 24 participants as
Tran 2021 - the AGBRESA campaign, regrouped for the reconditioning phase - so it shares a
cohort_id and must never be counted as an independent study. And psoas major *grows* during
bed rest while the erector spinae shrinks, which is a real result and the sort of thing a
model trained only on leg muscles would never see.
"""

from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FULLTEXT = next(REPO_ROOT.glob("resources/fulltext/*scopus_00516*.xml"))
TEMPLATE = REPO_ROOT / "data" / "extraction_template.csv"
TARGET = REPO_ROOT / "data" / "raw" / "extraction_qaragoz.csv"
HEADER = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))

STUDY_ID = "demartino2022"

# Table label -> (vocabulary term, is_composite, number of disc levels reported)
MUSCLES = {
    "Lumbar multifidus": ("multifidus", False, 5),
    "Lumbar erector spinae": ("lumbar_erector_spinae", True, 5),
    "Psoas major": ("psoas", False, 5),
    "Quadratus lumborum": ("quadratus_lumborum", False, 3),
}

LEVELS = ["L1/L2", "L2/L3", "L3/L4", "L4/L5", "L5/S1"]

ARMS = {
    "SR": dict(arm_id="sr", arm_type="control", cm_modality="none",
               cm_dose="standard reconditioning after bed rest"),
    "SR + FRED": dict(arm_id="sr_fred", arm_type="countermeasure", cm_modality="combined",
                      cm_dose="standard reconditioning plus the Functional Re-adaptive Exercise Device"),
}

# Table row label -> (phase, timepoint_days, days_from_unloading_end)
TIMES = {"HDT59": ("bed_rest", "59", "NA"), "R13": ("recovery", "73", "13")}

STUDY = dict(
    study_id=STUDY_ID, cohort_id="agbresa", campaign_name="AGBRESA",
    first_author="De Martino", year="2022", doi="10.3389/fphys.2022.862793",
    source_file=FULLTEXT.name, design="HDBR_-6", hdt_angle_deg="-6", duration_days="60",
    exposure_flag="analogue", n_arm="12", n_analysed="12", sex="mixed", pct_female="33.3",
    age_mean="33", population="healthy_young", laterality="NA",
    outcome_type="volume", modality="MRI", unit_original="mm3", unit_si="cm3",
    variance_of="baseline", variance_type="SD", data_source="table", page_ref="Table 2",
    extraction_confidence="high", extractor="qaragoz", extraction_date="2026-09-04",
    double_extracted="FALSE", qc_flag="laterality_unstated;shared_cohort_with_tran2021",
    notes=("same AGBRESA participants as tran2021, regrouped for the post-bed-rest "
           "reconditioning phase; sex split and age taken from the campaign description "
           "rather than this paper's own table"),
)

VALUE = re.compile(r"(\d+)\s*±\s*(\d+)")


def table_text() -> str:
    raw = FULLTEXT.read_text(encoding="utf-8", errors="replace")
    for block in re.findall(r"<table-wrap\b.*?</table-wrap>", raw, re.S):
        text = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", block)))
        if "multifidus" in text.lower() and "Psoas" in text:
            return text
    raise SystemExit("Table 2 not found")


def parse() -> list:
    text = table_text()
    rows = []

    labels = list(MUSCLES)
    for index, label in enumerate(labels):
        start = text.index(label)
        end = text.index(labels[index + 1]) if index + 1 < len(labels) else len(text)
        muscle_block = text[start:end]
        vocabulary, composite, level_count = MUSCLES[label]

        for arm_label, arm in ARMS.items():
            pattern = re.escape(arm_label) + r"\s+BDC(.*?)(?=SR \+ FRED|Lumbar erector|Psoas|Quadratus|$)"
            match = re.search(pattern, muscle_block, re.S)
            if not match:
                print(f"  ! {label}/{arm_label} not found", file=sys.stderr)
                continue
            segment = match.group(1)

            baseline_values = VALUE.findall(segment)[:level_count]
            for time_label, (phase, day, after) in TIMES.items():
                time_match = re.search(re.escape(time_label) + r"(.*?)(?=HDT59|R13|SR|$)", segment, re.S)
                if not time_match:
                    continue
                follow_values = VALUE.findall(time_match.group(1))[:level_count]
                if len(follow_values) < level_count or len(baseline_values) < level_count:
                    print(f"  ! {label}/{arm_label}/{time_label}: incomplete row", file=sys.stderr)
                    continue

                for level, (baseline, baseline_sd), (followup, _sd) in zip(
                        LEVELS[:level_count], baseline_values, follow_values):
                    baseline_mm3, followup_mm3 = float(baseline), float(followup)
                    pct = (followup_mm3 - baseline_mm3) / baseline_mm3 * 100
                    record = {column: "NA" for column in HEADER}
                    record.update(STUDY)
                    record.update(arm)
                    record.update(
                        muscle=vocabulary, is_composite=str(composite).upper(),
                        measurement_site=f"{level} intervertebral disc level",
                        phase=phase, timepoint_days=day, days_from_unloading_end=after,
                        value_baseline_original=baseline, value_followup_original=followup,
                        value_baseline=f"{baseline_mm3/1000:g}",
                        value_followup=f"{followup_mm3/1000:g}",
                        change_absolute=f"{(followup_mm3 - baseline_mm3)/1000:g}",
                        pct_change=f"{pct:.2f}", variance_value=f"{float(baseline_sd)/1000:g}",
                    )
                    site = re.sub(r"[^a-z0-9]+", "_", record["measurement_site"].lower()).strip("_")
                    record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                                        "__{modality}_{outcome_type}").format(**record) + "__" + site[:24]
                    rows.append(record)
    return rows


if __name__ == "__main__":
    extracted = parse()
    existing = list(csv.DictReader(TARGET.open(encoding="utf-8-sig")))
    keep = [r for r in existing if r["study_id"] != STUDY_ID]
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(keep)
        writer.writerows(extracted)
    print(f"{len(extracted)} rows extracted for {STUDY_ID}", file=sys.stderr)
