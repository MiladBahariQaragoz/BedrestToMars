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
import re
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
    site = re.sub(r"[^a-z0-9]+", "_", (record.get("measurement_site") or "").lower()).strip("_")
    suffix = "" if site in {"", "na"} else "__" + site[:24]
    record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                        "__{modality}_{outcome_type}").format(**record) + suffix
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


# --------------------------------------------- Smeuninx 2021 and 2025 (NCT04422665)
# Two papers from one registered trial in Birmingham: 10 healthy older men, 5 days of bed
# rest, unilateral leg exercise so each participant contributes a control leg and an
# exercised leg. Quadriceps CSA by MRI at four sites along the thigh - the sites disagree
# with each other, which is why measurement_site is part of the key.
SMEUNINX = dict(
    cohort_id="birmingham_br5_nct04422665",
    campaign_name="5-day bed rest with unilateral leg exercise",
    registry_id="NCT04422665", design="horizontal_BR", duration_days="5", phase="bed_rest",
    timepoint_days="5", exposure_flag="analogue", n_arm="10", n_analysed="10", sex="M",
    population="healthy_older", age_min="65", age_max="80", laterality="NA",
    outcome_type="CSA", modality="MRI", unit_original="mm2", unit_si="cm2",
    variance_of="baseline", variance_type="SD", data_source="table",
    extraction_confidence="high",
    qc_flag="laterality_unstated;within_participant_arms",
    notes=("unilateral design: the two arms are the two legs of the same ten men, so they are "
           "not independent and must never be treated as separate cohorts"),
)
SMEUNINX_STUDIES = [
    ("smeuninx2025", "Smeuninx", "2025", "10.1113/jp285130",
     "smeuninxb12025_pubmed_00421.xml", "Table 3",
     "single bout of unilateral leg resistance exercise the evening before bed rest", [
         ("quadriceps", "20% patella-trochanter", "ctrl", "control", "none", 4630, 4612, 594),
         ("quadriceps", "40% patella-trochanter", "ctrl", "control", "none", 6607, 6533, 651),
         ("quadriceps", "60% patella-trochanter", "ctrl", "control", "none", 7008, 6778, 749),
         ("quadriceps", "80% patella-trochanter", "ctrl", "control", "none", 4993, 4869, 702),
         ("quadriceps", "20% patella-trochanter", "ex", "countermeasure", "resistive", 4682, 4670, 630),
         ("quadriceps", "40% patella-trochanter", "ex", "countermeasure", "resistive", 6804, 6775, 667),
         ("quadriceps", "60% patella-trochanter", "ex", "countermeasure", "resistive", 7183, 7050, 704),
         ("quadriceps", "80% patella-trochanter", "ex", "countermeasure", "resistive", 5116, 5023, 625),
     ]),
    ("smeuninx2021", "Smeuninx", "2021", "10.1002/jcsm.12661",
     "smeuninxb12021_pubmed_00344.xml", "Table 3",
     "four bouts of high-volume unilateral leg resistance training over the 7 days before bed rest", [
         ("quadriceps", "20% patella-trochanter", "ctrl", "control", "none", 4770, 4760, 649),
         ("quadriceps", "40% patella-trochanter", "ctrl", "control", "none", 6823, 6776, 677),
         ("quadriceps", "60% patella-trochanter", "ctrl", "control", "none", 7168, 6917, 826),
         ("quadriceps", "80% patella-trochanter", "ctrl", "control", "none", 5086, 4963, 759),
         ("quadriceps", "20% patella-trochanter", "ex", "countermeasure", "resistive", 4787, 4774, 600),
         ("quadriceps", "40% patella-trochanter", "ex", "countermeasure", "resistive", 6855, 6809, 692),
         ("quadriceps", "60% patella-trochanter", "ex", "countermeasure", "resistive", 7260, 7040, 868),
         ("quadriceps", "80% patella-trochanter", "ex", "countermeasure", "resistive", 5148, 5027, 679),
         ("vastus_lateralis", "20% patella-trochanter", "ctrl", "control", "none", 1198, 1186, 145),
         ("vastus_lateralis", "40% patella-trochanter", "ctrl", "control", "none", 1889, 1860, 193),
         ("vastus_lateralis", "60% patella-trochanter", "ctrl", "control", "none", 2246, 2158, 338),
         ("vastus_lateralis", "80% patella-trochanter", "ctrl", "control", "none", 1290, 1271, 266),
         ("vastus_lateralis", "20% patella-trochanter", "ex", "countermeasure", "resistive", 1203, 1199, 116),
         ("vastus_lateralis", "40% patella-trochanter", "ex", "countermeasure", "resistive", 1919, 1892, 184),
         ("vastus_lateralis", "60% patella-trochanter", "ex", "countermeasure", "resistive", 2316, 2221, 300),
         ("vastus_lateralis", "80% patella-trochanter", "ex", "countermeasure", "resistive", 1338, 1315, 202),
     ]),
]
for study_id, author, year, doi, source, page, dose, values in SMEUNINX_STUDIES:
    for muscle, site, arm_id, arm_type, cm, baseline, followup, sd in values:
        pct = (followup - baseline) / baseline * 100
        add(**SMEUNINX, study_id=study_id, first_author=author, year=year, doi=doi,
            source_file=source, page_ref=page, muscle=muscle,
            is_composite="TRUE" if muscle == "quadriceps" else "FALSE",
            measurement_site=site, arm_id=arm_id, arm_type=arm_type, cm_modality=cm,
            cm_dose=dose if arm_type == "countermeasure" else "NA",
            value_baseline_original=str(baseline), value_followup_original=str(followup),
            value_baseline=f"{baseline/100:g}", value_followup=f"{followup/100:g}",
            change_absolute=f"{(followup - baseline)/100:g}", pct_change=f"{pct:.2f}",
            variance_value=f"{sd/100:g}")


# ------------------------------------------------------------------------ Mulder 2015
# Eur J Appl Physiol 10.1007/s00421-014-3045-0. Crossover: the same 10 men completed all
# three conditions, 5 days of 6 deg HDT each. Maximum CSA of the right limb by MRI at R+0.
MULDER = dict(
    study_id="mulder2015", cohort_id="dlr_hdt5_crossover",
    campaign_name="5-day HDT crossover with locomotion replacement training",
    first_author="Mulder", year="2015", doi="10.1007/s00421-014-3045-0",
    source_file="muldere12015_pubmed_00193.xml", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="5", phase="bed_rest", timepoint_days="5", exposure_flag="analogue",
    n_arm="10", n_analysed="10", sex="M", age_mean="29.4", age_sd="5.9",
    population="healthy_young", body_mass_mean_kg="77.7", laterality="right",
    measurement_site="maximum CSA", outcome_type="CSA", modality="MRI",
    unit_original="mm2", unit_si="cm2", variance_of="baseline", variance_type="NA",
    data_source="table", page_ref="Table 2", extraction_confidence="high",
    qc_flag="variance_type_unstated;within_participant_arms",
    notes=("crossover design - the same ten men completed all three conditions, so the arms "
           "share participants entirely. The table gives no dispersion type; the values look "
           "like standard errors but the paper does not say, so variance_type is left NA"),
)
MULDER_ARMS = {
    "con": ("control", "none", "NA"),
    "sta": ("countermeasure", "none", "25 min of upright standing daily"),
    "lrt": ("countermeasure", "combined", "locomotion replacement training, 25 min daily"),
}
MULDER_VALUES = [
    ("quadriceps", "TRUE", {"con": (7835, 7665, 227), "sta": (7875, 7669, 231),
                            "lrt": (7785, 7856, 227)}),
    ("triceps_surae", "TRUE", {"con": (5516, 5384, 164), "sta": (5578, 5409, 158),
                               "lrt": (5430, 5464, 153)}),
]
for muscle, composite, arms in MULDER_VALUES:
    for arm_id, (baseline, followup, sd) in arms.items():
        arm_type, cm, dose = MULDER_ARMS[arm_id]
        pct = (followup - baseline) / baseline * 100
        add(**MULDER, muscle=muscle, is_composite=composite, arm_id=arm_id,
            arm_type=arm_type, cm_modality=cm, cm_dose=dose,
            value_baseline_original=str(baseline), value_followup_original=str(followup),
            value_baseline=f"{baseline/100:g}", value_followup=f"{followup/100:g}",
            change_absolute=f"{(followup - baseline)/100:g}", pct_change=f"{pct:.2f}",
            variance_value=f"{sd/100:g}")


# ------------------------------------------------------------------------ Kramer 2017
# Sci Rep 10.1038/s41598-017-13659-8. 60-day bed rest at DLR, jump training versus control,
# DRKS00012946. The DXA follow-up is at recovery day 7, not the end of bed rest - a recovery
# row, and mislabelling it would understate the loss.
KRAMER = dict(
    study_id="kramer2017", cohort_id="dlr_rsl_br60",
    campaign_name="60-day bed rest with reactive jump training (DLR :envihab)",
    registry_id="DRKS00012946", first_author="Kramer", year="2017",
    doi="10.1038/s41598-017-13659-8", source_file="kramera12017_pubmed_00352.xml",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="60", phase="recovery",
    timepoint_days="67", days_from_unloading_end="7", exposure_flag="analogue",
    sex="M", population="healthy_young", muscle="whole_lower_limb", is_composite="TRUE",
    laterality="NA", outcome_type="lean_mass", modality="DXA", unit_original="kg",
    unit_si="kg", variance_of="baseline", variance_type="SD", data_source="table",
    page_ref="Table 1", extraction_confidence="high",
    qc_flag="laterality_unstated;recovery_measurement",
    notes=("DXA was performed at baseline and at recovery day 7, so this is a recovery row "
           "and understates the loss present at the end of bed rest"),
)
for arm_id, arm_type, cm, dose, n, age, age_sd, baseline, followup, sd in [
    ("jump", "countermeasure", "resistive",
     "48 reactive jump training sessions in a sledge system", 12, 30, 7, 19.4, 19.3, 1.4),
    ("ctrl", "control", "none", "NA", 11, 28, 6, 19.6, 18.6, 2.4),
]:
    pct = (followup - baseline) / baseline * 100
    add(**KRAMER, arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        n_arm=str(n), n_analysed=str(n), age_mean=str(age), age_sd=str(age_sd),
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.1f}", pct_change=f"{pct:.2f}",
        variance_value=str(sd))


# ------------------------------------------------------------- Hajj-Boutros 2023 (McGill)
# 14 days of 6 deg HDT in adults aged 55-65, control versus a multimodal in-bed exercise
# countermeasure. Same registered campaign as Dulac 2024 (NCT04964999), so it shares a
# cohort_id: these are the same people measured for a different outcome.
MCGILL = dict(
    study_id="hajjboutros2023", cohort_id="mcgill_hdbr14",
    campaign_name="McGill 14-day HDBR in older adults", registry_id="NCT04964999",
    first_author="Hajj-Boutros", year="2023", doi="10.1159/000534063",
    source_file="hajjboutrosg2023_pubmed_00024.xml", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="14", phase="bed_rest", timepoint_days="14", exposure_flag="analogue",
    n_arm="11", n_analysed="11", sex="mixed", population="healthy_older",
    muscle="whole_lower_limb", is_composite="TRUE", laterality="NA",
    outcome_type="lean_mass", modality="DXA", unit_original="kg", unit_si="kg",
    variance_of="baseline", variance_type="SD", data_source="table", page_ref="Table 2",
    extraction_confidence="high", qc_flag="laterality_unstated",
    notes=("leg lean mass by DXA; same participants as dulac2024, whose MRI muscle volumes "
           "are only available as a figure"),
)
for arm_id, arm_type, cm, dose, pct_f, age, age_sd, bmi, baseline, followup, sd in [
    ("ctrl", "control", "none", "NA", 45.5, 58.4, 3.9, 24.0, 16.9, 16.5, 4.3),
    ("ex", "countermeasure", "combined",
     "three in-bed sessions daily totalling 60-62 min: HIIT, continuous and progressive "
     "aerobic, upper- and lower-body resistance", 54.5, 58.4, 3.4, 25.7, 17.8, 17.5, 4.0),
]:
    pct = (followup - baseline) / baseline * 100
    add(**MCGILL, arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        pct_female=str(pct_f), age_mean=str(age), age_sd=str(age_sd), bmi_mean=str(bmi),
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.1f}", pct_change=f"{pct:.2f}",
        variance_value=str(sd))


# ------------------------------------------------------------------ Mandic 2026 (BRACE)
# Exp Physiol 10.1113/EP093145. 60 days of head-down tilt, 24 men in three arms: control,
# supine cycling, and supine cycling under artificial gravity. Table 2 gives fat-free muscle
# volume of the thigh by MRI at baseline and day 52, left and right separately.
BRACE = dict(
    study_id="mandic2026", cohort_id="brace_br60", campaign_name="BRACE",
    first_author="Mandic", year="2026", doi="10.1113/ep093145",
    source_file="mandicm2026_pubmed_00238.xml", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="60", phase="bed_rest", timepoint_days="52", exposure_flag="analogue",
    n_arm="8", n_analysed="8", sex="M", population="healthy_young", bmi_mean="24",
    is_composite="TRUE", outcome_type="volume", modality="MRI", unit_original="L",
    unit_si="cm3", variance_of="change", variance_type="SD", data_source="table",
    page_ref="Table 2", extraction_confidence="high",
    qc_flag="pct_of_individual_means",
    notes=("fat-free muscle volume from fat-referenced MRI with automatic segmentation; the "
           "printed percentage is the mean of individual changes"),
)
BRACE_ARMS = {
    "c": ("control", "none", "NA", 29, 7),
    "ex": ("countermeasure", "aerobic", "supine cycling", 30, 5),
    "ex_ag": ("countermeasure", "artificial_gravity", "supine cycling under artificial gravity", 30, 6),
}
# (muscle, laterality, {arm: (baseline L, follow-up L, printed % change, SD of that %)})
BRACE_VALUES = [
    ("whole_thigh", "mean", {"c": (12.9, 11.6, -10.5, 2.6), "ex": (14.1, 13.1, -6.9, 2.4),
                             "ex_ag": (13.3, 12.7, -4.3, 2.4)}),
    ("anterior_thigh_compartment", "left", {"c": (2.4, 2.1, -14.5, 3.7), "ex": (2.6, 2.4, -6.8, 2.9),
                                            "ex_ag": (2.5, 2.4, -3.5, 3.0)}),
    ("posterior_thigh_compartment", "left", {"c": (4.0, 3.7, -8.0, 2.2), "ex": (4.5, 4.2, -6.9, 2.4),
                                             "ex_ag": (4.2, 4.0, -4.5, 2.4)}),
    ("anterior_thigh_compartment", "right", {"c": (2.4, 2.1, -14.0, 4.5), "ex": (2.6, 2.4, -7.3, 3.2),
                                             "ex_ag": (2.4, 2.3, -3.9, 4.2)}),
    ("posterior_thigh_compartment", "right", {"c": (4.1, 3.7, -8.5, 2.2), "ex": (4.5, 4.2, -6.8, 2.6),
                                              "ex_ag": (4.2, 4.0, -4.6, 1.5)}),
]
for muscle, laterality, arms in BRACE_VALUES:
    for arm_id, (baseline, followup, pct, sd) in arms.items():
        arm_type, cm, dose, age, age_sd = BRACE_ARMS[arm_id]
        add(**BRACE, muscle=muscle, laterality=laterality, arm_id=arm_id, arm_type=arm_type,
            cm_modality=cm, cm_dose=dose, age_mean=str(age), age_sd=str(age_sd),
            measurement_site=f"{laterality} thigh" if laterality != "mean" else "whole thigh",
            value_baseline_original=str(baseline), value_followup_original=str(followup),
            value_baseline=f"{baseline*1000:g}", value_followup=f"{followup*1000:g}",
            change_absolute=f"{(followup-baseline)*1000:g}", pct_change=str(pct),
            variance_value=str(sd))


# ------------------------------------------------------------------ Lagace 2026 (McGill)
# Exp Physiol 10.1113/EP093524. Same registered McGill campaign as Dulac and Hajj-Boutros.
# Body composition was measured only in recovery, as medians with interquartile ranges, and
# the sample shrinks between timepoints - so these rows are low confidence by construction.
LAGACE = dict(
    study_id="lagace2026", cohort_id="mcgill_hdbr14",
    campaign_name="McGill 14-day HDBR in older adults", registry_id="NCT04964999",
    first_author="Lagace", year="2026", doi="10.1113/ep093524",
    source_file="lagacejc2026_scopus_00312.xml", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="14", phase="recovery", timepoint_days="17", days_from_unloading_end="3",
    exposure_flag="analogue", n_arm="11", n_analysed="11", sex="mixed",
    population="healthy_older", muscle="whole_lower_limb", is_composite="TRUE",
    laterality="NA", outcome_type="lean_mass", modality="DXA", unit_original="kg",
    unit_si="kg", variance_of="baseline", variance_type="IQR", data_source="table",
    page_ref="Table 2", extraction_confidence="low",
    qc_flag="laterality_unstated;median_not_mean;recovery_measurement",
    notes=("values are medians with interquartile ranges, not means; body composition was "
           "measured at baseline and in recovery only, never during bed rest, so this "
           "understates the loss. Same participants as dulac2024 and hajjboutros2023"),
)
for arm_id, arm_type, cm, dose, pct_f, age, baseline, followup, iqr in [
    ("ctrl", "control", "none", "NA", 45.5, 58, 15.3, 15.5, 5.2),
    ("ex", "countermeasure", "combined",
     "three in-bed sessions daily: HIIT, continuous and progressive aerobic, upper- and "
     "lower-body resistance", 54.5, 59, 15.9, 15.6, 7.9),
]:
    pct = (followup - baseline) / baseline * 100
    add(**LAGACE, arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        pct_female=str(pct_f), age_mean=str(age),
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.1f}", pct_change=f"{pct:.2f}",
        variance_value=str(iqr))


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
