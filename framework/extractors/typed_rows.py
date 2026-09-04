"""Hand-typed extraction rows, for papers whose numbers live in prose or in a small table.

    python framework/extractors/typed_rows.py

One dictionary per study, transcribed from the full text with the page or table it came
from. Re-running replaces every row for the studies defined here, so a correction is an edit
and a re-run rather than a hunt through a 300-row CSV.

Papers with a large results table get their own parser instead - see belavy2017_ltbr.py.
Anything typed here is `double_extracted = FALSE` until a second person checks it.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO_ROOT / "data" / "extraction_template.csv"
TARGET = REPO_ROOT / "data" / "raw" / "extraction_falk.csv"
HEADER = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))

ROWS = []


def add(**fields):
    record = {column: "NA" for column in HEADER}
    record.update(extractor="falk", extraction_date="2026-09-04", double_extracted="FALSE")
    record.update(fields)
    record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                        "__{modality}_{outcome_type}").format(**record)
    ROWS.append(record)


# --------------------------------------------------------------- Tran 2021 (AGBRESA)
# Front Physiol 10.3389/fphys.2021.745811. 60-day 6 deg HDT, three arms, MRI gluteal volumes
# at baseline and day 59. Tables 1-3.
TRAN = dict(
    study_id="tran2021", cohort_id="agbresa", campaign_name="AGBRESA",
    first_author="Tran", year="2021", doi="10.3389/fphys.2021.745811",
    source_file="tranv2021_scopus_00673.xml", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="60", phase="bed_rest", timepoint_days="59", exposure_flag="analogue",
    sex="mixed", population="healthy_young", is_composite="FALSE",
    measurement_site="whole muscle", outcome_type="volume", modality="MRI",
    unit_original="cm3", unit_si="cm3", variance_of="baseline", variance_type="SD",
    data_source="table", page_ref="Tables 2 and 3", extraction_confidence="high",
    qc_flag="pct_of_individual_means;laterality_unstated",
    notes=("printed relative change is the mean of individual percent changes and does not "
           "match a recomputation from the group means; n_analysed reduced by imaging "
           "artefacts per the Table 1 footnotes"),
)
TRAN_ARMS = {
    "ctrl": dict(arm_id="ctrl", arm_type="control", cm_modality="none",
                 n_arm="8", pct_female="25.0", age_mean="34", age_sd="8", bmi_mean="25"),
    "cag": dict(arm_id="cag", arm_type="countermeasure", cm_modality="artificial_gravity",
                cm_dose="30 min continuous centrifugation daily", n_arm="8",
                pct_female="37.5", age_mean="32", age_sd="10", bmi_mean="24"),
    "iag": dict(arm_id="iag", arm_type="countermeasure", cm_modality="artificial_gravity",
                cm_dose="6 x 5 min intermittent centrifugation daily", n_arm="8",
                pct_female="37.5", age_mean="34", age_sd="11", bmi_mean="22"),
}
TRAN_VALUES = {
    "gluteus_maximus": {"ctrl": (3051, 2756, 956, -9.4, 7), "cag": (3158, 2835, 892, -10.4, 8),
                        "iag": (2662, 2439, 750, -7.9, 8)},
    "gluteus_medius": {"ctrl": (551, 512, 282, -4.6, 7), "cag": (681, 600, 177, -12.1, 7),
                       "iag": (504, 476, 205, -7.2, 7)},
    "gluteus_minimus": {"ctrl": (265, 210, 122, -6.9, 7), "cag": (299, 251, 47, -16.2, 7),
                        "iag": (232, 211, 90, -8.2, 6)},
}
for muscle, arms in TRAN_VALUES.items():
    for arm, (baseline, followup, sd, pct, analysed) in arms.items():
        add(**TRAN, **TRAN_ARMS[arm], muscle=muscle, n_analysed=str(analysed),
            value_baseline_original=str(baseline), value_followup_original=str(followup),
            value_baseline=str(baseline), value_followup=str(followup),
            change_absolute=str(followup - baseline), pct_change=str(pct),
            variance_value=str(sd))


# ------------------------------------------------------------------------ Dirks 2016
# Diabetes 10.2337/db15-1661. Extracted from the abstract; the full text is paywalled.
add(study_id="dirks2016", cohort_id="maastricht_br7", first_author="Dirks", year="2016",
    doi="10.2337/db15-1661", source_file="abstract only - full text not accessible",
    design="horizontal_BR", duration_days="7", phase="bed_rest", timepoint_days="7",
    exposure_flag="analogue", arm_id="ctrl", arm_type="control", cm_modality="none",
    n_arm="10", n_analysed="10", sex="M", age_mean="23", age_sd="1",
    population="healthy_young", bmi_mean="23.0", muscle="quadriceps", is_composite="TRUE",
    outcome_type="CSA", modality="CT", unit_original="%", unit_si="pct_only",
    pct_change="-3.2", data_source="text", page_ref="abstract",
    extraction_confidence="low", qc_flag="laterality_unstated;variance_type_unstated",
    notes=("full text paywalled; abstract prints 3.2 +/- 0.9% decline in quadriceps CSA, "
           "dispersion type not stated so the variance fields are left NA. The abstract also "
           "reports 1.4 +/- 0.2 kg lean tissue loss with no baseline, which cannot become a "
           "percent change"))


# ------------------------------------------------------------------------ Fuchs 2025
# Eur J Sport Sci 10.1002/ejsc.12299. Two weeks of strict bed rest, 12 young men, the same
# legs measured by DXA, CT and MRI - the evidence behind the modality sensitivity analysis.
FUCHS = dict(
    study_id="fuchs2025", cohort_id="maastricht_br14", first_author="Fuchs", year="2025",
    doi="10.1002/ejsc.12299", source_file="fuchscj12025_pubmed_00155.xml",
    design="horizontal_BR", duration_days="14", phase="bed_rest", timepoint_days="14",
    exposure_flag="analogue", arm_id="ctrl", arm_type="control", cm_modality="none",
    n_arm="12", n_analysed="12", sex="M", age_mean="24", age_sd="3",
    population="healthy_young", laterality="mean", data_source="text",
    page_ref="Results, DXA/CT/MRI sections", extraction_confidence="high",
    variance_of="change", variance_type="SD",
    qc_flag="pct_recomputed_from_group_means",
    notes=("study measures the same participants by three modalities; percent change is "
           "recomputed from the printed group means, and the paper's own rounded figure and "
           "mean absolute change are given in this note for comparison"),
)
# muscle, composite, outcome, modality, baseline, follow-up, unit_original, unit_si,
# change SD in SI units, the paper's rounded percentage
FUCHS_VALUES = [
    ("whole_lower_limb", "TRUE", "lean_mass", "DXA", 10.2, 9.7, "kg", "kg", 0.165, "5%"),
    ("whole_thigh", "TRUE", "CSA", "CT", 155.0, 146.0, "cm2", "cm2", 4.1, "6%"),
    ("whole_thigh", "TRUE", "volume", "MRI", 7100.0, 6700.0, "L", "cm3", 214.0, "5%"),
    ("anterior_thigh_compartment", "TRUE", "volume", "MRI", 2800.0, 2600.0, "L", "cm3", 112.0, "7%"),
    ("posterior_thigh_compartment", "TRUE", "volume", "MRI", 4300.0, 4100.0, "L", "cm3", 125.0, "4%"),
]
for muscle, composite, outcome, modality, baseline, followup, unit_orig, unit_si, sd, printed in FUCHS_VALUES:
    pct = (followup - baseline) / baseline * 100
    original = f"{baseline/1000:g}" if unit_orig == "L" else f"{baseline:g}"
    original_follow = f"{followup/1000:g}" if unit_orig == "L" else f"{followup:g}"
    add(**{**FUCHS,
           "notes": FUCHS["notes"] + f"; paper states a {printed} decline for this measure"},
        muscle=muscle, is_composite=composite, outcome_type=outcome, modality=modality,
        unit_original=unit_orig, unit_si=unit_si,
        value_baseline_original=original, value_followup_original=original_follow,
        value_baseline=f"{baseline:g}", value_followup=f"{followup:g}",
        change_absolute=f"{followup - baseline:g}", pct_change=f"{pct:.1f}",
        variance_value=str(sd))


# ----------------------------------------------------------------------- Rogers 2025
# J Appl Physiol 10.1152/japplphysiol.00483.2025. Bedrest control group of a larger women's
# campaign at MEDES Toulouse: 8 women, 60 days of 6 deg head-down tilt, MRI volumes of 17
# individually segmented lower-limb muscles. Two-month percentages are printed in the
# Results text; the one-month values exist only in Figs 1-2 and are not extracted here.
ROGERS = dict(
    study_id="rogers2025", cohort_id="medes_women_br60",
    campaign_name="60-day women's bedrest campaign, MEDES Toulouse",
    first_author="Rogers", year="2025", doi="10.1152/japplphysiol.00483.2025",
    source_file="rogerskr12025_pubmed_00026.pdf", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="60", phase="bed_rest", timepoint_days="60", exposure_flag="analogue",
    arm_id="ctrl", arm_type="control", cm_modality="none", n_arm="8", n_analysed="8",
    sex="F", age_mean="34", age_sd="4", body_mass_mean_kg="55.6",
    population="healthy_young", nutrition_controlled="yes", laterality="NA",
    outcome_type="volume", modality="MRI", unit_original="%", unit_si="pct_only",
    variance_of="change", variance_type="SD", data_source="text",
    page_ref="Results, muscle-specific atrophy paragraphs",
    qc_flag="laterality_unstated",
    notes=("percent change printed in the Results text; absolute volumes and the one-month "
           "timepoint are in Figs 1-2 and would need digitising"),
)
# muscle, composite, percent loss, SD (None where the paper gives no dispersion)
ROGERS_VALUES = [
    ("vasti", "TRUE", 22, 2), ("rectus_femoris", "FALSE", 10, 3),
    ("adductor_longus", "FALSE", 13, 5), ("adductor_magnus", "FALSE", 15, 5),
    ("gracilis", "FALSE", 13, 6), ("sartorius", "FALSE", 17, None),
    ("biceps_femoris_long_head", "FALSE", 20, 2), ("biceps_femoris_short_head", "FALSE", 11, 4),
    ("semimembranosus", "FALSE", 21, 3), ("semitendinosus", "FALSE", 13, 4),
    ("anterior_tibial_group", "TRUE", 15, None), ("flexor_digitorum_longus", "FALSE", 22, 5),
    ("peroneals", "TRUE", 23, 2), ("tibialis_posterior", "FALSE", 19, 6),
    ("soleus", "FALSE", 27, 4), ("gastrocnemius_lateralis", "FALSE", 28, 6),
    ("gastrocnemius_medialis", "FALSE", 29, 7),
]
for muscle, composite, loss, sd in ROGERS_VALUES:
    extra = {}
    if sd is None:
        extra = dict(variance_type="NA", extraction_confidence="medium",
                     notes=ROGERS["notes"] + "; value taken from the men-versus-women "
                                             "comparison in the Discussion, where no dispersion is given")
    else:
        extra = dict(extraction_confidence="high")
    add(**{**ROGERS, **extra}, muscle=muscle, is_composite=composite,
        pct_change=str(-loss), variance_value=str(sd) if sd is not None else "NA")


if __name__ == "__main__":
    studies = {row["study_id"] for row in ROWS}
    existing = list(csv.DictReader(TARGET.open(encoding="utf-8-sig")))
    keep = [row for row in existing if row["study_id"] not in studies]
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(keep)
        writer.writerows(ROWS)
    print(f"{len(ROWS)} typed rows written for {len(studies)} studies: {sorted(studies)}")
