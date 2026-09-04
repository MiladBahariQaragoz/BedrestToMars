"""Extract Belavy et al. 2017 (LTBR, 90-day bed rest) into schema rows.

    python framework/extractors/belavy2017_ltbr.py > /dev/null

Source: BMJ Open Sport Exerc Med, doi 10.1136/bmjsem-2016-000196, full text from Europe PMC
(PMC5530106). Tables 1 and 2 report, for 24 individual lower-limb muscles and two arms,
baseline volume in cm3 and the mean (SD) percentage change at two bed-rest and four
recovery timepoints.

Why an extractor and not typing: 24 muscles x 2 arms x 6 timepoints is 288 rows. Typed by
hand that is a day of work and a dozen transcription errors; parsed from the table text it
is reproducible and the mistakes are systematic, which means findable.

The paper prints percentage change only - no follow-up volumes - so `value_followup` stays
NA rather than being back-calculated from the baseline and the percentage. Rule 1: never
impute silently.
"""

from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FULLTEXT = next(REPO_ROOT.glob("resources/fulltext/*scopus_01130*.xml"))
TEMPLATE = REPO_ROOT / "data" / "extraction_template.csv"
TARGET = REPO_ROOT / "data" / "raw" / "extraction_falk.csv"

# Table label -> (vocabulary term, is_composite, measurement site note)
MUSCLES = {
    "Anterior tibial muscles": ("anterior_tibial_group", True, ""),
    "Flexor digitorum with tibialis posterior": ("flexor_digitorum_with_tibialis_posterior", True, ""),
    "Flexor hallucis longus": ("flexor_hallucis_longus", False, ""),
    "Lateral gastrocnemius": ("gastrocnemius_lateralis", False, ""),
    "Medial gastrocnemius": ("gastrocnemius_medialis", False, ""),
    "Peroneals": ("peroneals", True, ""),
    "Soleus": ("soleus", False, ""),
    "Vasti": ("vasti", True, ""),
    "Rectus femoris": ("rectus_femoris", False, ""),
    "Adductor brevis": ("adductor_brevis", False, ""),
    "Adductor longus": ("adductor_longus", False, ""),
    "Adductor magnus": ("adductor_magnus", False, ""),
    "Gracilis": ("gracilis", False, ""),
    "Sartorius": ("sartorius", False, ""),
    "Biceps femoris long head": ("biceps_femoris_long_head", False, ""),
    "Biceps femoris short head": ("biceps_femoris_short_head", False, ""),
    "Semimembranosus": ("semimembranosus", False, ""),
    "Semitendinosus": ("semitendinosus", False, ""),
    "Popliteus": ("popliteus", False, ""),
    "Lower gluteus maximus": ("gluteus_maximus", False, "lower portion only"),
    "Obturator externus": ("obturator_externus", False, ""),
    "Obturator internus": ("obturator_internus", False, ""),
    "Quadratus femoris": ("quadratus_femoris", False, ""),
    "Iliopsoas": ("iliopsoas", False, ""),
}

# Column order after the baseline column, as printed in both tables.
TIMEPOINTS = [
    ("bed_rest", 28, ""),
    ("bed_rest", 89, ""),
    ("recovery", 103, 13),
    ("recovery", 180, 90),
    ("recovery", 270, 180),
    ("recovery", 450, 360),
]

ARMS = {
    "Inactive": dict(arm_id="ctrl", arm_type="control", cm_modality="none", cm_dose="NA",
                     n_arm="16", n_analysed="16", age_mean="32.5", age_sd="3.4",
                     body_mass_mean_kg="70.3"),
    "Flywheel": dict(arm_id="fly", arm_type="countermeasure", cm_modality="flywheel",
                     cm_dose="high-intensity concentric-eccentric flywheel resistance exercise every third day",
                     n_arm="9", n_analysed="9", age_mean="31.0", age_sd="5.5",
                     body_mass_mean_kg="70.9"),
}

STUDY = dict(
    study_id="belavy2017", cohort_id="medes_ltbr90",
    campaign_name="Long Term Bed Rest (LTBR), MEDES Toulouse", registry_id="NA",
    first_author="Belavy", year="2017", doi="10.1136/bmjsem-2016-000196",
    source_file=FULLTEXT.name, design="HDBR_-6", hdt_angle_deg="-6", duration_days="90",
    exposure_flag="analogue", sex="M", population="healthy_young",
    nutrition_controlled="yes", muscle_function_class="NA", laterality="NA",
    outcome_type="volume", modality="MRI", unit_original="cm3", unit_si="cm3",
    variance_of="change", variance_type="SD", data_source="table",
    extraction_confidence="high", extractor="falk", extraction_date="2026-09-04",
    double_extracted="FALSE",
)

VALUE = re.compile(r"(−|-)?\s?(\d+(?:\.\d+)?)\s*\(\s*(\d+(?:\.\d+)?)\s*\)")


def table_text() -> str:
    raw = FULLTEXT.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r"<table-wrap\b.*?</table-wrap>", raw, re.S)[:2]
    text = " ".join(html.unescape(re.sub("<[^>]+>", " ", block)) for block in blocks)
    return re.sub(r"\s+", " ", text)


def parse() -> list:
    text = table_text()
    positions = []
    for label in MUSCLES:
        # The label also appears in prose and in table 3; take the occurrence that is
        # followed by a group name, which is what a data row looks like.
        for match in re.finditer(re.escape(label) + r"\s+(Inactive|Flywheel|Fly-wheel)", text):
            positions.append((match.start(), label))
            break
    positions.sort()

    rows = []
    for index, (start, label) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        block = text[start:end]
        vocabulary, composite, site = MUSCLES[label]

        for arm_label, arm in ARMS.items():
            pattern = (re.escape(arm_label) if arm_label != "Flywheel" else r"Fly-?wheel")
            match = re.search(pattern + r"(.*?)(?=Inactive|Fly-?wheel|$)", block, re.S)
            if not match:
                print(f"  ! no {arm_label} row for {label}", file=sys.stderr)
                continue

            numbers = VALUE.findall(match.group(1))
            if len(numbers) < 7:
                print(f"  ! {label}/{arm_label}: found {len(numbers)} values, expected 7",
                      file=sys.stderr)
                continue

            baseline_sign, baseline, baseline_sd = numbers[0]
            for (phase, day, after), (sign, value, sd) in zip(TIMEPOINTS, numbers[1:7]):
                pct = float(value) * (-1 if sign else 1)
                record = {column: "NA" for column in HEADER}
                record.update(STUDY)
                record.update(arm)
                record.update(
                    phase=phase, timepoint_days=str(day),
                    days_from_unloading_end=str(after) if after != "" else "NA",
                    muscle=vocabulary, is_composite=str(composite).upper(),
                    measurement_site=site or "NA",
                    value_baseline_original=baseline, value_baseline=baseline,
                    pct_change=f"{pct:.1f}", variance_value=sd,
                    page_ref="Tables 1-2",
                    qc_flag="laterality_unstated",
                    notes=(f"baseline SD {baseline_sd} cm3; paper prints percentage change only, "
                           "so follow-up volume is left NA rather than back-calculated"),
                )
                record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                                    .format(**record))
                rows.append(record)
    return rows


HEADER = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))

if __name__ == "__main__":
    extracted = parse()
    existing = list(csv.DictReader(TARGET.open(encoding="utf-8-sig")))
    keep = [r for r in existing if r["study_id"] != "belavy2017"]
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(keep)
        writer.writerows(extracted)
    print(f"{len(extracted)} rows extracted for belavy2017 "
          f"({len({r['muscle'] for r in extracted})} muscles)", file=sys.stderr)
