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
TARGET = REPO_ROOT / "data" / "raw" / "extraction_qaragoz.csv"
HEADER = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))

ROWS = []


def add(**fields):
    record = {column: "NA" for column in HEADER}
    record.update(extractor="qaragoz", extraction_date="2026-09-04", double_extracted="FALSE")
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


# ------------------------------------------------- Printed against recomputed percent change
# Schema rule 3 keeps a paper's printed percent change when it disagrees with the one
# recomputed from the group means, because the printed figure is usually the mean of the
# individual changes. A whole-number printed figure only disagrees once the gap is larger
# than its own rounding, so within half a point the recomputed value is kept as the more
# precise of the two. Agreed on 2026-09-14 when resolving the 2026-09-04 source QC; every
# case is listed in data/reconciliation_log.md. Used by Fuchs, Kramer and Trappe SPRINT.
PRINTED_PCT_NOTE = ("QC 2026-09-04: source-printed percent retained per schema §4 rule 3; "
                    "printed group means remain in baseline/follow-up fields.")


def pct_fields(recomputed, printed, recomputed_format, qc_flag, notes, kept_note="",
               rounding=0.5, printed_note=PRINTED_PCT_NOTE):
    """pct_change, qc_flag and notes for a row whose paper also prints its percent change.

    `rounding` is half a unit in the printed figure's last digit: 0.5 for a whole-number
    percentage, 0.05 for one printed to a decimal place. `printed_note` is what the notes say
    when the printed value wins.
    """
    if abs(recomputed - printed) > rounding:
        flags = [f for f in qc_flag.split(";")
                 if f not in ("", "NA", "pct_recomputed_from_group_means")]
        return dict(pct_change=f"{printed:g}",
                    qc_flag=";".join(flags + ["pct_of_individual_means"]),
                    notes=f"{notes}; {printed_note}")
    return dict(pct_change=format(recomputed, recomputed_format), qc_flag=qc_flag,
                notes=notes + kept_note)


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
    notes = FUCHS["notes"] + f"; paper states a {printed} decline for this measure"
    add(**{**FUCHS, **pct_fields(pct, -float(printed.rstrip("%")), ".1f", FUCHS["qc_flag"], notes)},
        muscle=muscle, is_composite=composite, outcome_type=outcome, modality=modality,
        unit_original=unit_orig, unit_si=unit_si,
        value_baseline_original=original, value_followup_original=original_follow,
        value_baseline=f"{baseline:g}", value_followup=f"{followup:g}",
        change_absolute=f"{followup - baseline:g}", variance_value=str(sd))


# ----------------------------------------------------------------------- Rogers 2025
# J Appl Physiol 10.1152/japplphysiol.00483.2025. Bedrest control group of the WISE-2005
# women's campaign at MEDES Toulouse - the acknowledgements name it - so it shares a cohort
# with the Holt papers: 8 women, 60 days of 6 deg head-down tilt, MRI volumes of 17
# individually segmented lower-limb muscles. Two-month percentages are printed in the
# Results text; the one-month values exist only in Figs 1-2 and are not extracted here.
ROGERS = dict(
    study_id="rogers2025", cohort_id="wise2005",
    campaign_name="WISE-2005",
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
# arm, type, countermeasure, dose, n, age, age SD, baseline kg, follow-up kg, baseline SD,
# the percent change Table 1 prints
for arm_id, arm_type, cm, dose, n, age, age_sd, baseline, followup, sd, printed in [
    ("jump", "countermeasure", "resistive",
     "48 reactive jump training sessions in a sledge system", 12, 30, 7, 19.4, 19.3, 1.4, 0.0),
    ("ctrl", "control", "none", "NA", 11, 28, 6, 19.6, 18.6, 2.4, -5.0),
]:
    pct = (followup - baseline) / baseline * 100
    kept = f"; Table 1 prints {printed:g}%, which matches this value within rounding"
    add(**{**KRAMER, **pct_fields(pct, printed, ".2f", KRAMER["qc_flag"], KRAMER["notes"], kept)},
        arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        n_arm=str(n), n_analysed=str(n), age_mean=str(age), age_sd=str(age_sd),
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.1f}", variance_value=str(sd))


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


# --------------------------------------------------------- Hermans 2025 (Maastricht BFR)
# J Physiol 10.1113/JP286065. 14 days of strict bed rest, 12 young men, one leg under daily
# blood flow restriction. Same cohort as fuchs2025 - the control leg values are identical
# (10.2 to 9.7 kg), which is how the shared cohort was spotted.
BFR = dict(
    study_id="fuchs2025bfr", cohort_id="maastricht_br14", first_author="Fuchs",
    year="2025", doi="10.1113/jp286065", source_file="fuchscj12025_pubmed_00326.xml",
    design="horizontal_BR", duration_days="14", phase="bed_rest", timepoint_days="14",
    exposure_flag="analogue", n_arm="12", n_analysed="12", sex="M", age_mean="24",
    age_sd="3", population="healthy_young", muscle="whole_lower_limb", is_composite="TRUE",
    laterality="NA", outcome_type="lean_mass", modality="DXA", unit_original="kg",
    unit_si="kg", variance_of="baseline", variance_type="SD", data_source="table",
    page_ref="Table 3", extraction_confidence="high",
    qc_flag="laterality_unstated;within_participant_arms",
    notes=("the two arms are the two legs of the same twelve men; shares maastricht_br14 "
           "with fuchs2025, which reports the same control-leg values"),
)
for arm_id, arm_type, cm, dose, baseline, followup, sd in [
    ("ctrl", "control", "none", "NA", 10.2, 9.7, 1.6),
    ("bfr", "countermeasure", "BFR", "daily blood flow restriction of one leg", 10.2, 9.6, 1.7),
]:
    pct = (followup - baseline) / baseline * 100
    add(**BFR, arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.1f}", pct_change=f"{pct:.2f}",
        variance_value=str(sd))


# ------------------------------------------------------------------- Simunic-type 2026 TMG
# Med Sci Sports Exerc 10.1249/MSS.0000000000003986. 10 days of horizontal bed rest in ten
# young men, muscle thickness by ultrasound in four muscles. The table labels thickness in
# millimetres but prints values around 2, which cannot be millimetres for a vastus
# lateralis - almost certainly centimetres. Recorded as printed and flagged.
TMG = dict(
    study_id="simunic2026", cohort_id="izola_br10", campaign_name="10-day horizontal bed rest",
    first_author="Simunic", year="2026", doi="10.1249/mss.0000000000003986",
    source_file="simunicb12026_pubmed_00389.xml", design="horizontal_BR", duration_days="10",
    phase="bed_rest", timepoint_days="10", exposure_flag="analogue", arm_id="ctrl",
    arm_type="control", cm_modality="none", n_arm="10", n_analysed="10", sex="M",
    age_mean="22.9", age_sd="5.0", population="healthy_young", laterality="NA",
    measurement_site="muscle belly", is_composite="FALSE", outcome_type="thickness",
    modality="ultrasound", unit_original="mm as printed", unit_si="mm",
    variance_of="baseline", variance_type="SD", data_source="table", page_ref="Table 2",
    extraction_confidence="medium",
    qc_flag="laterality_unstated;unit_suspect",
    notes=("table labels muscle thickness in mm but the values are around 2, which is "
           "implausible for these muscles and is almost certainly cm; recorded as printed "
           "and flagged rather than silently converted"),
)
for muscle, baseline, followup, sd in [
    ("vastus_lateralis", 2.60, 2.42, 0.46),
    ("gastrocnemius_medialis", 1.79, 1.87, 0.22),
    ("biceps_femoris_long_head", 1.98, 2.03, 0.28),
    ("tibialis_anterior", 2.66, 2.61, 0.30),
]:
    pct = (followup - baseline) / baseline * 100
    add(**TMG, muscle=muscle,
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.2f}", pct_change=f"{pct:.2f}",
        variance_value=str(sd))


# ------------------------------------------------- Spaceflight vs bed rest (npj Microgravity)
# 10.1038/s41526-026-00611-2. Muscle cross-sectional area by pQCT at 38% and 66% of tibia
# length, after 6-month missions (n = 13) and after 60 days of strict 6 deg head-down tilt
# bed rest without countermeasures (n = 11). Every timepoint is post-return or
# post-ambulation, so all of these are recovery rows - and the spaceflight rows are the
# first in the dataset carrying exposure_flag = spaceflight.
COMPARE = dict(
    study_id="bocker2026", cohort_id="space_vs_br_2026",
    campaign_name="6-month missions compared with 60-day bed rest",
    first_author="Bocker", year="2026", doi="10.1038/s41526-026-00611-2",
    source_file="bockerj2026_scopus_00324.xml", phase="recovery", sex="M",
    population="healthy_young", muscle="whole_calf", is_composite="TRUE", laterality="NA",
    outcome_type="CSA", modality="CT", unit_original="%", unit_si="pct_only",
    variance_of="change", variance_type="SD", data_source="table", page_ref="Table 1",
    extraction_confidence="high", arm_id="ctrl", arm_type="control", cm_modality="none",
    qc_flag="laterality_unstated;pqct_reported_as_CT;recovery_measurement",
    notes=("pQCT muscle area, recorded as modality CT because the vocabulary has no pQCT "
           "term; every timepoint is after return or re-ambulation, so all rows are recovery"),
)
# (exposure, design, duration, n, age_min, age_max, site, {days after: (pct, sd)})
COMPARE_VALUES = [
    ("spaceflight", "spaceflight", 180, 13, 34, 56, "38% tibia length",
     {1: (-13.3, 5.0), 14: (-6.5, 4.0), 90: (-0.8, 3.2)}),
    ("spaceflight", "spaceflight", 180, 13, 34, 56, "66% tibia length",
     {1: (-12.5, 4.9), 14: (-6.6, 3.9), 90: (-0.3, 3.9)}),
    ("analogue", "HDBR_-6", 60, 11, 22, 39, "38% tibia length",
     {3: (-6.2, 4.0), 14: (-3.5, 5.2), 90: (-0.4, 2.4)}),
    ("analogue", "HDBR_-6", 60, 11, 22, 39, "66% tibia length",
     {3: (-7.9, 2.7), 14: (-3.7, 3.8), 90: (2.1, 2.5)}),
]
for flag, design, duration, n, age_min, age_max, site, timepoints in COMPARE_VALUES:
    for after, (pct, sd) in timepoints.items():
        add(**COMPARE, exposure_flag=flag, design=design, duration_days=str(duration),
            hdt_angle_deg="-6" if design == "HDBR_-6" else "NA",
            timepoint_days=str(duration + after), days_from_unloading_end=str(after),
            n_arm=str(n), n_analysed=str(n), age_min=str(age_min), age_max=str(age_max),
            measurement_site=site, pct_change=str(pct), variance_value=str(sd))


# ---------------------------------------------------------------------- Hansen 2024 NMES
# 5 days of bed rest in young and older adults, one leg receiving neuromuscular electrical
# stimulation. Three outcomes on the same legs: leg lean mass and mid-thigh lean mass by
# DXA, vastus lateralis thickness by ultrasound - three rows per leg per age group, which
# the modality part of the key now allows.
NMES = dict(
    study_id="hansen2024", cohort_id="copenhagen_br5", campaign_name="5-day bed rest with unilateral NMES",
    first_author="Hansen", year="2024", doi="10.14814/phy2.16166",
    source_file="hansensk122024_pubmed_00189.xml", design="horizontal_BR", duration_days="5",
    phase="bed_rest", timepoint_days="5", exposure_flag="analogue",
    n_arm="16", n_analysed="16", sex="mixed", pct_female="50.0",
    laterality="NA", variance_of="baseline", variance_type="SD", data_source="table",
    page_ref="Table 3", extraction_confidence="high",
    qc_flag="laterality_unstated;within_participant_arms;age_range_not_mean",
    notes=("32 participants, 50/50 male and female, split into a young group aged 18-30 "
           "and an old group aged 65-80; the two arms are the two legs of the same people. "
           "The paper gives inclusion ranges rather than mean ages"),
)
# (muscle, is_composite, outcome, modality, unit_original, unit_si, site)
NMES_MEASURES = {
    "leg_lean": ("whole_lower_limb", "TRUE", "lean_mass", "DXA", "g", "kg", "NA"),
    "midthigh": ("whole_thigh", "TRUE", "lean_mass", "DXA", "g", "kg", "mid-thigh"),
    "vl_thick": ("vastus_lateralis", "FALSE", "thickness", "ultrasound", "cm", "mm", "muscle belly"),
}
# measure -> age group -> arm -> (baseline, follow-up, SD)
NMES_VALUES = {
    "leg_lean": {
        "young": {"con": (8399, 8226, 1975), "nmes": (8573, 8400, 2003)},
        "old": {"con": (7752, 7482, 1386), "nmes": (7761, 7531, 1445)},
    },
    "midthigh": {
        "young": {"con": (664, 656, 138), "nmes": (680, 677, 133)},
        "old": {"con": (619, 606, 111), "nmes": (610, 607, 107)},
    },
    "vl_thick": {
        "young": {"con": (2.36, 2.23, 0.43), "nmes": (2.35, 2.37, 0.34)},
        "old": {"con": (2.14, 2.01, 0.39), "nmes": (2.02, 2.14, 0.36)},
    },
}
AGE_GROUPS = {"young": ("healthy_young", "18", "30"), "old": ("healthy_older", "65", "80")}
for measure, groups in NMES_VALUES.items():
    muscle, composite, outcome, modality, unit_orig, unit_si, site = NMES_MEASURES[measure]
    for group, arms in groups.items():
        population, age_min, age_max = AGE_GROUPS[group]
        for arm, (baseline, followup, sd) in arms.items():
            pct = (followup - baseline) / baseline * 100
            scale = 1000.0 if unit_orig == "g" else (0.1 if unit_orig == "cm" else 1.0)
            add(**NMES, muscle=muscle, is_composite=composite, outcome_type=outcome,
                modality=modality, unit_original=unit_orig, unit_si=unit_si,
                measurement_site=site, population=population, age_min=age_min, age_max=age_max,
                arm_id=f"{arm}_{group}",
                arm_type="control" if arm == "con" else "countermeasure",
                cm_modality="none" if arm == "con" else "NMES",
                cm_dose="NA" if arm == "con" else "daily neuromuscular electrical stimulation of one leg",
                value_baseline_original=str(baseline), value_followup_original=str(followup),
                value_baseline=f"{baseline/scale:g}" if unit_orig == "g" else f"{baseline/scale:g}",
                value_followup=f"{followup/scale:g}" if unit_orig == "g" else f"{followup/scale:g}",
                change_absolute=f"{(followup-baseline)/scale:g}", pct_change=f"{pct:.2f}",
                variance_value=f"{sd/scale:g}")


# ----------------------------------------------------- BRACE ultrasound (Arbeille 2024)
# Same BRACE campaign as mandic2026: 24 males, 6 deg HDT, measured at day 55. The only
# muscle outcome is vastus intermedius thickness, and it is reported as percent change.
BRACE_US = dict(
    study_id="arbeille2024", cohort_id="brace_br60", campaign_name="BRACE",
    first_author="Arbeille", year="2024", doi="10.3389/fphys.2024.1482860",
    source_file="arbeillep2024_scopus_00458.xml", design="HDBR_-6", hdt_angle_deg="-6", duration_days="60",
    phase="bed_rest", timepoint_days="55", exposure_flag="analogue", n_arm="8",
    n_analysed="8", sex="M", age_mean="29.4", age_sd="5.6", bmi_mean="23.88",
    population="healthy_young", muscle="vastus_intermedius", is_composite="FALSE",
    laterality="NA", measurement_site="muscle belly", outcome_type="thickness",
    modality="ultrasound", unit_original="%", unit_si="pct_only", variance_of="change",
    variance_type="SD", data_source="table", page_ref="Table 1",
    extraction_confidence="high",
    qc_flag="laterality_unstated;shared_cohort_with_mandic2026",
    notes=("same 24 participants as mandic2026 - both report the BRACE campaign, so the two "
           "papers are one cohort. Only the vastus intermedius row is a muscle outcome; the "
           "rest of the table is vascular"),
)
for arm_id, arm_type, cm, dose, pct, sd in [
    ("c", "control", "none", "NA", -23.1, 12.2),
    ("ex", "countermeasure", "aerobic", "supine cycling", 9.13, 18.5),
    ("ex_ag", "countermeasure", "artificial_gravity", "supine cycling under artificial gravity", 24.3, 17.6),
]:
    add(**BRACE_US, arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        pct_change=str(pct), variance_value=str(sd))


# ------------------------------------------------------------------ Trappe 2023 (sex)
# J Appl Physiol. Quadriceps and triceps surae volumes by MRI in 8 women over 2 months and
# 9 men over 3 months of 6 deg head-down tilt. The paper states the data were reported
# previously in separate publications. The women are the eight WISE-2005 controls Rogers
# 2025 reports - Rogers names the campaign in its acknowledgements - so they share the
# wise2005 cohort. The men may overlap another Toulouse campaign, hence the flag.
TRAPPE = dict(
    study_id="trappe2023", first_author="Trappe", year="2023",
    doi="10.1152/japplphysiol.00412.2023", source_file="trappeta12023_pubmed_00152.pdf",
    design="HDBR_-6", hdt_angle_deg="-6", exposure_flag="analogue",
    arm_type="control", cm_modality="none", phase="bed_rest", population="healthy_young",
    is_composite="TRUE", laterality="NA", outcome_type="volume", modality="MRI",
    unit_original="cm3", unit_si="cm3", variance_of="baseline", variance_type="SE",
    data_source="table", page_ref="Table 2", extraction_confidence="high",
    qc_flag="laterality_unstated;possible_cohort_overlap",
    notes=("values are means with standard errors, not SDs; the paper says these data were "
           "reported previously in separate publications - the women are the WISE-2005 "
           "controls also reported by rogers2025, and the men may overlap another Toulouse "
           "campaign"),
)
# (sex, cohort, n, age, age_se, muscle, baseline, {timepoint: (value, sd)})
TRAPPE_VALUES = [
    ("F", "wise2005", 8, 34, 1, "quadriceps", 716, 39, {29: (596, 32), 57: (564, 31)}, 60),
    ("F", "wise2005", 8, 34, 1, "triceps_surae", 374, 15, {29: (307, 13), 57: (266, 10)}, 60),
    ("M", "medes_ltbr90", 9, 32, 1, "quadriceps", 973, 47, {29: (879, 42), 89: (793, 39)}, 90),
    ("M", "medes_ltbr90", 9, 32, 1, "triceps_surae", 494, 33, {29: (415, 24), 89: (350, 18)}, 90),
]
for sex, cohort, n, age, age_se, muscle, baseline, baseline_sd, timepoints, duration in TRAPPE_VALUES:
    for day, (followup, sd) in timepoints.items():
        pct = (followup - baseline) / baseline * 100
        # Women and men are separate groups measured on the same day, so the arm id has
        # to carry the sex or the two collide in the primary key.
        add(**TRAPPE, cohort_id=cohort, arm_id="ctrl_women" if sex == "F" else "ctrl_men",
            sex=sex, n_arm=str(n), n_analysed=str(n),
            age_mean=str(age), age_sd=str(age_se), duration_days=str(duration),
            timepoint_days=str(day), muscle=muscle,
            value_baseline_original=str(baseline), value_followup_original=str(followup),
            value_baseline=str(baseline), value_followup=str(followup),
            change_absolute=str(followup - baseline), pct_change=f"{pct:.2f}",
            variance_value=str(baseline_sd))


# ------------------------------------------------------------- Trappe 2024 (NASA SPRINT)
# J Appl Physiol 10.1152/japplphysiol.00489.2023. 70 days of bed rest with three arms:
# bed rest alone, bed rest with the SPRINT resistance and aerobic programme, and the same
# plus testosterone. Quadriceps, triceps surae and soleus volumes by MRI at day 70.
SPRINT = dict(
    study_id="trappe2024sprint", cohort_id="nasa_sprint_br70",
    campaign_name="NASA SPRINT 70-day bed rest", first_author="Trappe", year="2024",
    doi="10.1152/japplphysiol.00489.2023", source_file="trappeta12024_pubmed_00293.pdf",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="70", phase="bed_rest",
    timepoint_days="70", exposure_flag="analogue", sex="M", population="healthy_young",
    laterality="NA", outcome_type="volume", modality="MRI",
    unit_original="cm3", unit_si="cm3", variance_of="baseline", variance_type="SD",
    data_source="table", page_ref="Table 1", extraction_confidence="high",
    qc_flag="laterality_unstated",
    notes=("the paper prints the change as an unsigned magnitude; percent change here is "
           "recomputed from the pre and post means, which also recovers its sign - the two "
           "exercise arms gained quadriceps volume"),
)
SPRINT_ARMS = {
    "br": ("control", "none", "NA", 9, 37, 8),
    "bre": ("countermeasure", "combined", "SPRINT resistance and aerobic exercise", 9, 34, 5),
    "bre_t": ("countermeasure", "combined", "SPRINT exercise plus testosterone", 8, 33, 10),
}
# muscle, composite, {arm: (pre, post, pre SD, the unsigned change Table 1 prints)}
SPRINT_VALUES = [
    ("quadriceps", "TRUE", {"br": (928, 841, 242, 9), "bre": (944, 969, 151, 3), "bre_t": (1001, 1043, 238, 4)}),
    ("triceps_surae", "TRUE", {"br": (375, 287, 129, 23), "bre": (383, 355, 76, 7), "bre_t": (355, 330, 85, 6)}),
    ("soleus", "FALSE", {"br": (243, 185, 79, 24), "bre": (241, 219, 44, 9), "bre_t": (224, 204, 68, 8)}),
]
for muscle, composite, arms in SPRINT_VALUES:
    for arm_id, (baseline, followup, sd, printed) in arms.items():
        arm_type, cm, dose, n, age, age_sd = SPRINT_ARMS[arm_id]
        pct = (followup - baseline) / baseline * 100
        signed = printed if pct > 0 else -printed  # Table 1 prints magnitudes only
        kept = f"; Table 1 prints {printed}%, which matches this value within rounding"
        add(**{**SPRINT, **pct_fields(pct, signed, ".2f", SPRINT["qc_flag"], SPRINT["notes"], kept)},
            muscle=muscle, is_composite=composite, arm_id=arm_id,
            arm_type=arm_type, cm_modality=cm, cm_dose=dose, n_arm=str(n), n_analysed=str(n),
            age_mean=str(age), age_sd=str(age_sd),
            value_baseline_original=str(baseline), value_followup_original=str(followup),
            value_baseline=str(baseline), value_followup=str(followup),
            change_absolute=str(followup - baseline), variance_value=str(sd))


# ------------------------------------------------------------------------ Orlova 2026
# J Physiol 10.1113/JP290722. Three weeks of head-down bed rest in 12 men aged 24-40, with
# lean mass reported separately for calf and thigh as medians with interquartile ranges.
ORLOVA = dict(
    study_id="orlova2026", cohort_id="imbp_br21", campaign_name="3-week head-down bed rest",
    first_author="Orlova", year="2026", doi="10.1113/jp290722",
    source_file="orlovama12026_pubmed_00194.pdf", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="21", phase="bed_rest", timepoint_days="21", exposure_flag="analogue",
    arm_id="ctrl", arm_type="control", cm_modality="none", n_arm="12", n_analysed="12",
    sex="M", age_min="24", age_max="40", population="healthy_young", is_composite="TRUE",
    laterality="NA", outcome_type="lean_mass", modality="DXA", unit_original="%",
    unit_si="pct_only", variance_of="change", variance_type="IQR", data_source="text",
    page_ref="Results, muscle function paragraph", extraction_confidence="high",
    qc_flag="laterality_unstated;median_not_mean",
    notes=("medians with interquartile ranges; the paper reports a greater loss in the calf "
           "than the thigh, which is the muscle-specificity result in miniature"),
)
for muscle, pct, low, high in [("whole_calf", -6.0, 4.0, 8.0), ("whole_thigh", -4.5, 0.2, 6.7)]:
    add(**{**ORLOVA, "notes": ORLOVA["notes"] + f"; interquartile range {low} to {high}%"},
        muscle=muscle, pct_change=str(pct), variance_value=f"{high - low:.1f}")


# ------------------------------------------------------------------------ Sarto-type ULLS
# 10 days of unilateral lower limb suspension; quadriceps CSA by extended-field-of-view
# ultrasound, averaged over 30, 50 and 70% of femur length. The only size number the paper
# prints in text is the 4.5% loss.
ULLS = dict(
    study_id="ulls2022", cohort_id="padova_ulls10", campaign_name="10-day ULLS",
    first_author="Sarto", year="2022", doi="10.1113/jp283381",
    source_file="sartof12022_pubmed_00662.xml", design="ULLS", duration_days="10", phase="bed_rest",
    timepoint_days="10", exposure_flag="analogue", arm_id="ulls", arm_type="control",
    cm_modality="none", n_arm="11", n_analysed="11", sex="M", age_min="18", age_max="40",
    population="healthy_young", muscle="quadriceps", is_composite="TRUE", laterality="NA",
    measurement_site="mean of 30, 50 and 70% femur length", outcome_type="CSA",
    modality="ultrasound", unit_original="%", unit_si="pct_only", pct_change="-4.5",
    data_source="text", page_ref="Discussion", extraction_confidence="medium",
    qc_flag="laterality_unstated;variance_type_unstated",
    notes=("only the summary percentage is given in the text; the per-site values are in a "
           "figure. Suspended limb only - the contralateral limb is not a bed rest control"),
)
add(**ULLS)


# ------------------------------------------------------------------- Franchi 2022 (hamstrings)
# Med Sci Sports Exerc 10.1249/MSS.0000000000002922. Ten days of horizontal bed rest, MRI
# volumes of the four hamstring muscles plus the group pooled. The interesting part is how
# small the losses are: the hamstrings are flexors, and they lose 2-4% where the soleus
# loses 15% over a comparable period.
FRANCHI = dict(
    study_id="franchi2022", cohort_id="izola_br10", campaign_name="10-day horizontal bed rest",
    first_author="Franchi", year="2022", doi="10.1249/mss.0000000000002922",
    source_file="franchimv2022_pubmed_00880.pdf", design="horizontal_BR", duration_days="10",
    phase="bed_rest", timepoint_days="10", exposure_flag="analogue", arm_id="ctrl",
    arm_type="control", cm_modality="none", n_arm="12", n_analysed="12", sex="M",
    age_mean="23", age_sd="5", population="healthy_young", laterality="NA",
    measurement_site="whole muscle", outcome_type="volume", modality="MRI",
    unit_original="%", unit_si="pct_only", variance_of="change", variance_type="CI95",
    data_source="text", page_ref="Results, muscle volume paragraph",
    extraction_confidence="high", qc_flag="laterality_unstated",
    notes=("percent changes printed in the Results text with Hedges g and 95% confidence "
           "intervals; the variance field holds the CI half-width"),
)
for muscle, composite, pct, low, high in [
    ("biceps_femoris_long_head", "FALSE", -3.53, -0.68, 1.076),
    ("biceps_femoris_short_head", "FALSE", -3.54, -0.72, 1.03),
    ("semitendinosus", "FALSE", -2.63, -0.75, 1.01),
    ("semimembranosus", "FALSE", -2.01, -0.75, 1.01),
    ("hamstrings", "TRUE", -2.78, -0.69, 1.06),
]:
    add(**FRANCHI, muscle=muscle, is_composite=composite, pct_change=str(pct),
        variance_value=f"{(high - low) / 2:.2f}")


# --------------------------------------------------------- De Martino 2021 (AGBRESA lumbar)
# J Appl Physiol 10.1152/japplphysiol.00990.2020. The same AGBRESA campaign as tran2021 and
# demartino2022, this time during bed rest rather than reconditioning, and it prints the
# registry number the earlier papers did not: DRKS00015677.
DEMARTINO21 = dict(
    study_id="demartino2021", cohort_id="agbresa", campaign_name="AGBRESA",
    registry_id="DRKS00015677", first_author="De Martino", year="2021",
    doi="10.1152/japplphysiol.00990.2020", source_file="demartinoe12021_pubmed_00343.pdf",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="60", phase="bed_rest",
    timepoint_days="59", exposure_flag="analogue", n_arm="8", n_analysed="8", sex="mixed",
    pct_female="33.3", age_mean="33", population="healthy_young", is_composite="FALSE",
    laterality="NA", outcome_type="volume", modality="MRI", unit_original="%",
    unit_si="pct_only", variance_of="change", variance_type="SD", data_source="text",
    page_ref="Results", extraction_confidence="high",
    qc_flag="laterality_unstated;shared_cohort_with_tran2021",
    notes=("same AGBRESA participants as tran2021 and demartino2022; the lumbar erector "
           "spinae grows at L5/S1 while the multifidus shrinks, which is why both are kept"),
)
DEMARTINO21_ARMS = {
    "ctrl": ("control", "none", "NA"),
    "cag": ("countermeasure", "artificial_gravity", "30 min continuous centrifugation daily"),
    "iag": ("countermeasure", "artificial_gravity", "6 x 5 min intermittent centrifugation daily"),
}
for muscle, site, values in [
    ("multifidus", "all lumbar levels averaged",
     {"ctrl": (-6.49, 3.52), "cag": (-5.77, 3.91), "iag": (-6.11, 3.47)}),
    ("lumbar_erector_spinae", "L5/S1 intervertebral disc level",
     {"ctrl": (7.94, 11.98), "cag": (7.53, 8.40), "iag": (9.71, 8.60)}),
]:
    for arm_id, (pct, sd) in values.items():
        arm_type, cm, dose = DEMARTINO21_ARMS[arm_id]
        add(**DEMARTINO21, muscle=muscle, measurement_site=site, arm_id=arm_id,
            arm_type=arm_type, cm_modality=cm, cm_dose=dose,
            pct_change=str(pct), variance_value=str(sd))


# ------------------------------------------------------------------ McDonnell 2019 (LunHab)
# Exp Physiol 10.1113/EP087473. Eleven men completed three ten-day arms in a crossover:
# normoxic bed rest, hypoxic bed rest, and hypoxic ambulatory confinement. Only the two bed
# rest arms are unloading; the ambulatory arm is the control for hypoxia, not for unloading,
# so it is deliberately not extracted.
LUNHAB = dict(
    study_id="mcdonnell2019", cohort_id="lunhab_br10",
    campaign_name="LunHab 10-day bed rest and hypoxia crossover",
    first_author="McDonnell", year="2019", doi="10.1113/ep087482",
    source_file="mcdonnellac12019_pubmed_00348.pdf", design="horizontal_BR",
    duration_days="10", phase="bed_rest", timepoint_days="10", exposure_flag="analogue",
    n_arm="11", n_analysed="11", sex="M", age_min="20", age_max="45",
    population="healthy_young", is_composite="TRUE", laterality="NA",
    outcome_type="lean_mass", modality="DXA", unit_original="%", unit_si="pct_only",
    variance_of="change", variance_type="SD", data_source="text", page_ref="Results, Table 2",
    extraction_confidence="high",
    qc_flag="laterality_unstated;within_participant_arms;age_range_not_mean",
    notes=("crossover: the same eleven men completed every arm, so the arms share "
           "participants entirely. The hypoxic ambulatory arm is not an unloading exposure "
           "and is not extracted"),
)
for arm_id, arm_type, dose, muscle, pct, sd in [
    ("nbr", "control", "NA", "whole_calf", -4.0, 6.1),
    ("nbr", "control", "NA", "whole_thigh", -3.7, 2.3),
    ("hbr", "control", "normobaric hypoxia during bed rest", "whole_calf", -4.9, 7.9),
    ("hbr", "control", "normobaric hypoxia during bed rest", "whole_thigh", -3.8, 5.6),
]:
    add(**LUNHAB, arm_id=arm_id, arm_type=arm_type, cm_modality="none", cm_dose=dose,
        muscle=muscle, pct_change=str(pct), variance_value=str(sd))


# ----------------------------------------------------------------------- Pisot 2016
# J Appl Physiol 10.1152/japplphysiol.00858.2015. Fourteen days of bed rest in seven young
# men and sixteen older men, quadriceps volume of the right leg by MRI. One of the few
# direct age contrasts in the dataset, and the older men lose about half again as much.
PISOT = dict(
    study_id="pisot2016", cohort_id="izola_br14", campaign_name="14-day bed rest, young and older men",
    first_author="Pisot", year="2016", doi="10.1152/japplphysiol.00858.2015",
    source_file="pisotr12016_pubmed_00392.pdf", design="horizontal_BR", duration_days="14",
    phase="bed_rest", timepoint_days="14", exposure_flag="analogue", arm_type="control",
    cm_modality="none", sex="M", muscle="quadriceps", is_composite="TRUE",
    laterality="right", outcome_type="volume", modality="MRI", unit_original="ml",
    unit_si="cm3", variance_of="change", variance_type="SD", data_source="text",
    page_ref="Results, Fig. 1A", extraction_confidence="high",
    qc_flag="age_range_not_mean",
    notes=("percent change printed in the Results text; baseline volumes from the same "
           "section. Older men lost 8.4% against 5.7% in the young over identical exposure"),
)
for arm_id, population, age_min, age_max, n, baseline, pct, sd in [
    ("young", "healthy_young", "18", "30", 7, 1987, -5.7, 3.9),
    ("old", "healthy_older", "55", "65", 16, 1666, -8.4, 3.7),
]:
    add(**PISOT, arm_id=arm_id, population=population, age_min=age_min, age_max=age_max,
        n_arm=str(n), n_analysed=str(n), value_baseline_original=str(baseline),
        value_baseline=str(baseline), pct_change=str(pct), variance_value=str(sd))


# ------------------------------------------------------------------------ Hides 2021
# Spine J 10.1016/j.spinee.2020.09.006. Lumbar multifidus CSA by ultrasound before flight
# and on return day 1, for astronauts after six-month ISS missions. Real spaceflight, so
# exposure_flag = spaceflight, and every row is a recovery measurement because the first
# scan happens after landing.
HIDES = dict(
    study_id="hides2021", cohort_id="iss_hides_astronauts",
    campaign_name="ISS long-duration missions (Hides series)", first_author="Hides",
    year="2021", doi="10.1016/j.spinee.2020.09.006",
    source_file="hidesja12021_pubmed_00935.pdf", design="spaceflight", duration_days="180",
    phase="recovery", timepoint_days="181", days_from_unloading_end="1",
    exposure_flag="spaceflight", arm_id="ctrl", arm_type="control", cm_modality="none",
    n_arm="6", n_analysed="6", sex="mixed", pct_female="20.0",
    population="healthy_middle_aged", muscle="multifidus", is_composite="FALSE",
    laterality="mean", outcome_type="CSA", modality="ultrasound", unit_original="cm2",
    unit_si="cm2", variance_of="baseline", variance_type="SD", data_source="table",
    page_ref="Table of astronaut means", extraction_confidence="medium",
    qc_flag="spaceflight_exposure;recovery_measurement;n_inconsistent_in_paper;age_not_published",
    notes=("the results table says six astronauts over eight missions while the methods text "
           "says five astronauts over seven - n follows the table that carries these values. "
           "Age is not published for astronaut cohorts and is left NA rather than "
           "guessed; the sex split follows the methods text, which describes five "
           "astronauts, four male. Return-day-one scan, so losses are already partly recovered; "
           "QC 2026-09-04: source methods specify ultrasound; modality corrected from MRI after "
           "full-source verification."),
)
for level, baseline, followup, sd in [
    ("L2", 3.26, 3.47, 0.72), ("L3", 5.22, 4.56, 1.02),
    ("L4", 8.00, 7.51, 1.12), ("L5", 10.07, 9.03, 1.41),
]:
    pct = (followup - baseline) / baseline * 100
    add(**HIDES, measurement_site=f"{level} vertebral level",
        value_baseline_original=str(baseline), value_followup_original=str(followup),
        value_baseline=str(baseline), value_followup=str(followup),
        change_absolute=f"{followup - baseline:.2f}", pct_change=f"{pct:.2f}",
        variance_value=str(sd))


# --------------------------------------------------------------------- Liphardt 2020
# Transl Sports Med 10.1002/tsm2.122. Twenty-one days of bed rest, control group of eleven,
# anatomical CSA by MRI at five points along the thigh for each quadriceps head. This is the
# clearest evidence in the dataset that where you measure changes the answer: rectus femoris
# barely moves at the proximal site and loses 7% at the distal one, while vastus medialis
# loses 12-17% along its whole length.
LIPHARDT = dict(
    study_id="liphardt2020", cohort_id="liphardt_br21", campaign_name="21-day bed rest",
    first_author="Liphardt", year="2020", doi="10.1002/tsm2.122",
    source_file="liphardtam2020_scopus_00594.pdf", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="21", phase="bed_rest", timepoint_days="21", exposure_flag="analogue",
    arm_id="con", arm_type="control", cm_modality="none", n_arm="11", n_analysed="11",
    sex="M", age_mean="35.2", age_sd="8.1", population="healthy_young", laterality="NA",
    outcome_type="CSA", modality="MRI", unit_original="cm2", unit_si="cm2",
    variance_of="baseline", variance_type="SD", data_source="table", page_ref="Table 1",
    extraction_confidence="high", qc_flag="laterality_unstated",
    notes=("ACSA measured at five points along a region of interest running from the "
           "proximal rectus femoris tendon to the distal femoral neck; the percentage is the "
           "mean deviation printed per site. Baseline SD is the ACSA SD at that site"),
)
# muscle -> [(site label, baseline ACSA, baseline SD, mean percent deviation)]
LIPHARDT_VALUES = {
    "rectus_femoris": [("10% of ROI", 2.6, 0.4, -0.0), ("30% of ROI", 7.6, 1.3, -5.0),
                       ("50% of ROI", 11.6, 2.5, -4.6), ("70% of ROI", 15.6, 3.2, -5.2),
                       ("90% of ROI", 15.4, 2.8, -7.1)],
    "vastus_lateralis": [("10% of ROI", 16.8, 2.9, -9.4), ("30% of ROI", 24.7, 3.5, -10.1),
                         ("50% of ROI", 30.9, 3.6, -12.6), ("70% of ROI", 32.7, 2.9, -12.6),
                         ("90% of ROI", 26.6, 3.3, -13.0)],
    "vastus_intermedius": [("10% of ROI", 18.3, 1.8, -11.9), ("30% of ROI", 23.0, 2.6, -11.8),
                           ("50% of ROI", 25.5, 3.4, -13.2), ("70% of ROI", 20.7, 3.1, -14.1),
                           ("90% of ROI", 14.5, 3.4, -11.9)],
    "vastus_medialis": [("10% of ROI", 25.0, 3.4, -11.9), ("30% of ROI", 19.8, 2.5, -15.1),
                        ("50% of ROI", 12.7, 1.5, -14.6), ("70% of ROI", 8.6, 1.8, -16.9),
                        ("90% of ROI", 4.0, 1.7, -16.8)],
}
for muscle, sites in LIPHARDT_VALUES.items():
    for site, baseline, sd, pct in sites:
        add(**LIPHARDT, muscle=muscle, is_composite="FALSE", measurement_site=site,
            value_baseline_original=str(baseline), value_baseline=str(baseline),
            pct_change=str(pct), variance_value=str(sd))


# ============================================================================================
# The pre-search corpus in resources/
#
# The papers held before the systematic search began (docs/screening_decisions.md). The
# search was limited to 2013 onwards, so these are the dataset's only pre-2013 rows, its
# 119-day upper end, and the campaigns the abstract was first written from. Their source_file
# is the bare file name in resources/ rather than a name in resources/fulltext/.
# ============================================================================================

RULE3_NOTE = ("printed percent change kept per schema §4 rule 3 - it is the mean of the "
              "individual changes - with the group means left in the baseline and follow-up fields")


# ------------------------------------------------------------------------ LeBlanc 1992
# J Appl Physiol 73:2172-2178. Eight men, 17 weeks of horizontal bed rest - the longest
# unloading in the dataset. MRI volume losses are printed only as approximate values read off
# regression lines (Figs 2-4). The thigh, imaged in two men, is given only as a shared "16-18%"
# for quadriceps and hamstrings and is not extracted; psoas "no change" has no value to record.
# Regional lean mass by dual-photon absorptiometry, the forerunner of DXA, is in Table 2.
LEBLANC = dict(
    study_id="leblanc1992", cohort_id="nasa_br17wk", campaign_name="17-week bed rest (Houston)",
    first_author="LeBlanc", year="1992", doi="10.1152/jappl.1992.73.5.2172",
    source_file="6.pdf", design="horizontal_BR", hdt_angle_deg="0", duration_days="119",
    exposure_flag="analogue", arm_id="ctrl", arm_type="control", cm_modality="none",
    n_arm="8", sex="M", age_mean="32", age_sd="12", age_min="19", age_max="52",
    population="healthy_young", body_mass_mean_kg="74", nutrition_controlled="yes",
    laterality="NA", unit_original="%", unit_si="pct_only",
)
# muscle, components, measurement site, percent change at 17 weeks, men imaged
for muscle, parts, site, pct, n in [
    ("triceps_surae", "gastrocnemius;soleus", "NA", -30, 8),
    ("anterior_tibial_group", "NA", "NA", -21, 8),
    ("lumbar_erector_spinae",
     "rotatores;multifidus;semispinalis;spinalis;longissimus;iliocostalis",
     "intrinsic lower back", -9, 6),
]:
    add(**LEBLANC, phase="bed_rest", timepoint_days="119", muscle=muscle, is_composite="TRUE",
        composite_of=parts, measurement_site=site, outcome_type="volume", modality="MRI",
        n_analysed=str(n), pct_change=str(pct), data_source="text",
        page_ref="p. 2176, Results (regression estimates at 17 wk, Figs 2 and 4)",
        extraction_confidence="medium",
        qc_flag="laterality_unstated;pct_estimated_from_regression;no_dispersion_published",
        notes=("the paper gives the 17-week loss as approximately this value, estimated from "
               "a linear regression through every scan; 'ankle extensors' are gastrocnemius "
               "and soleus, 'ankle flexors' are recorded as the anterior tibial group, and the "
               "back is imaged in six of the eight men"))

# region, baseline lean mass (kg), percent change at 17 wk, weekly slope and its SD,
# percent of baseline after 8 wk of reambulation
for muscle, baseline, pct_bed, slope, slope_sd, pct_rec in [
    ("whole_lower_limb", 20.1, -11.9, -0.70, 0.08, -3.5),
    ("whole_thigh", 13.4, -12.2, -0.72, 0.13, -4.8),
    ("whole_calf", 6.7, -11.2, -0.66, 0.05, -0.9),
]:
    for phase, day, days_after, pct in [("bed_rest", "119", "NA", pct_bed),
                                        ("recovery", "175", "56", pct_rec)]:
        flags = "dpa_reported_as_DXA;pct_estimated_from_regression"
        if phase == "recovery":
            flags += ";recovery_measurement;recovery_with_supervised_exercise"
        add(**{**LEBLANC, "unit_original": "kg", "unit_si": "kg"}, phase=phase,
            timepoint_days=day, days_from_unloading_end=days_after, muscle=muscle,
            is_composite="TRUE", outcome_type="lean_mass", modality="DXA", n_analysed="6",
            value_baseline_original=str(baseline), value_baseline=str(baseline),
            pct_change=str(pct), data_source="table", page_ref="p. 2174, Table 2",
            extraction_confidence="medium", qc_flag=flags,
            notes=(f"dual-photon absorptiometry, both legs; percent change is the regression "
                   f"slope ({slope} +/- {slope_sd} SD %/wk during bed rest) times the time, as "
                   f"the paper computes it. Two of the eight men lost their DPA data to a "
                   f"source change. Reambulation included supervised weight training from "
                   f"about week 3"))


# ----------------------------------------------------------------------- Greenleaf 1994
# NASA Technical Memorandum 4580 (NASA Ames). Nineteen men, 30 days of 6 deg head-down tilt,
# three arms: no exercise, intense isotonic cycle training and isokinetic knee training. The
# posterior leg group was scanned on recovery day 3, so these are recovery rows. Volumes are
# summed pixel counts: the unit cannot be converted, but the percent change is exact.
GREENLEAF = dict(
    study_id="greenleaf1994", cohort_id="nasa_ames_hdbr30",
    campaign_name="NASA Ames 30-day HDBR with isotonic and isokinetic training",
    first_author="Greenleaf", year="1994", doi="NASA-TM-4580", source_file="1.pdf",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="30", phase="recovery",
    timepoint_days="33", days_from_unloading_end="3", exposure_flag="analogue", sex="M",
    age_mean="36", age_sd="4", age_min="32", age_max="42", population="healthy_young",
    body_mass_mean_kg="76.5", muscle="plantar_flexors", is_composite="TRUE",
    composite_of=("soleus;gastrocnemius_medialis;gastrocnemius_lateralis;tibialis_posterior;"
                  "flexor_digitorum_longus;flexor_hallucis_longus"),
    laterality="NA", outcome_type="volume", modality="MRI", unit_original="pixels",
    unit_si="pct_only", variance_of="change", variance_type="SE", data_source="table",
    page_ref="Table 2 (report p. 5)", extraction_confidence="high",
    qc_flag=("recovery_measurement;outcome_in_pixel_counts;laterality_unstated;"
             "no_doi_report_number_in_doi_field;age_reported_for_whole_sample"),
    notes=("a NASA technical memorandum with no DOI, so the report number (NTRS accession "
           "N94-29401) stands in the doi field. Image quality did not separate soleus from "
           "gastrocnemius, so the whole posterior leg group was traced. The printed change is "
           "the mean of individual changes; the pixel sums recompute to within 0.3 points. Age "
           "is given only for all nineteen men"),
)
for arm_id, arm_type, cm, dose, n, pre, post, pct, se in [
    ("noe", "control", "none", "NA", 5, 536478, 502190, -6.3, 0.8),
    ("ite", "countermeasure", "aerobic",
     "supine cycle ergometry, 2-min stages from 40 to 90% of peak VO2, 60 min/day", 7,
     538541, 516688, -4.3, 1.6),
    ("ike", "countermeasure", "resistive",
     "isokinetic knee flexion-extension at 100 deg/s, 10 bouts of 5 maximal repetitions, "
     "15 min per leg daily", 7, 574858, 530892, -7.7, 1.6),
]:
    add(**GREENLEAF, arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        n_arm=str(n), n_analysed=str(n), value_baseline_original=str(pre),
        value_followup_original=str(post), pct_change=str(pct), variance_value=str(se))


# ----------------------------------------------------------------------------- Berg 2007
# Eur J Appl Physiol 99:283-289. Ten men, 35 days of strict horizontal bed rest at Valdoltra
# Orthopaedic Hospital in Slovenia. CT CSA of the right leg at three levels, before, straight
# after, and after four weeks of supervised retraining. The five ambulatory controls were never
# unloaded and are not an arm here.
BERG = dict(
    study_id="berg2007", cohort_id="valdoltra_br35",
    campaign_name="35-day bed rest, Valdoltra Orthopaedic Hospital", first_author="Berg",
    year="2007", doi="10.1007/s00421-006-0346-y", source_file="8.pdf",
    design="horizontal_BR", hdt_angle_deg="0", duration_days="35", exposure_flag="analogue",
    arm_id="ctrl", arm_type="control", cm_modality="none", n_arm="10", n_analysed="10",
    sex="M", age_mean="25", age_sd="5", population="healthy_young",
    body_mass_mean_kg="70.5", is_composite="TRUE", laterality="right", outcome_type="CSA",
    modality="CT", unit_original="mm2", unit_si="cm2", variance_of="baseline",
    variance_type="SD", data_source="text", page_ref="p. 286, Results - Muscle morphology",
    extraction_confidence="high",
)
# muscle, components, level, pre, post, after retraining (mm2), pre SD, printed % change
BERG_VALUES = [
    ("plantar_flexors",
     "soleus;gastrocnemius;tibialis_posterior;flexor_digitorum_longus;flexor_hallucis_longus",
     "upper calf", 4518, 3976, 4435, 693, -11.9),
    ("quadriceps", "vastus_lateralis;vastus_medialis;vastus_intermedius;rectus_femoris",
     "mid-thigh", 7347, 6650, 7309, 740, -9.4),
    ("gluteals", "gluteus_maximus;gluteus_medius;gluteus_minimus", "gluteal level",
     8931, 8728, 8707, 771, -2.2),
]
for muscle, parts, site, pre, post, rec, sd, printed in BERG_VALUES:
    common = dict(muscle=muscle, composite_of=parts, measurement_site=site,
                  value_baseline_original=str(pre), value_baseline=f"{pre / 100:g}",
                  variance_value=f"{sd / 100:g}")
    pct = (post - pre) / pre * 100
    add(**{**BERG, **pct_fields(pct, printed, ".2f", "NA", "CT at a fixed level after 2 h "
                                "supine", rounding=0.05, printed_note=RULE3_NOTE)},
        **common, phase="bed_rest", timepoint_days="35",
        value_followup_original=str(post), value_followup=f"{post / 100:g}",
        change_absolute=f"{(post - pre) / 100:g}")
    pct = (rec - pre) / pre * 100
    add(**BERG, **common, phase="recovery", timepoint_days="63", days_from_unloading_end="28",
        value_followup_original=str(rec), value_followup=f"{rec / 100:g}",
        change_absolute=f"{(rec - pre) / 100:g}", pct_change=f"{pct:.2f}",
        qc_flag="recovery_measurement;recovery_with_supervised_exercise",
        notes=("after four weeks of supervised cycle or resistance retraining, three sessions "
               "a week; the paper pools the two retraining groups"))


# ---------------------------------------------------------------------------- Zange 2009
# Eur J Appl Physiol 105:271-277. Eight men, two 14-day phases of 6 deg head-down tilt 5.5
# months apart in a randomised crossover: once with 20 Hz whole-body vibration twice a day,
# once with the same routine on a plate switched off. In both phases the men left the bed
# twice a day to stand, so neither arm is strict bed rest. Tables 1-3 print the pre-bed-rest
# volume of the imaged segment and the percent change for both legs summed; post volumes are
# not printed. The combined "soleus + lateral gastrocnemius" row is left out, since both parts
# are extracted on their own.
ZANGE = dict(
    study_id="zange2009", cohort_id="wbv_hdt14",
    campaign_name="Vibration Bed Rest Study (VBR), DLR Cologne", first_author="Zange",
    year="2009", doi="10.1007/s00421-008-0899-z", source_file="11 (2).pdf",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="14", phase="bed_rest",
    timepoint_days="14", exposure_flag="analogue", n_arm="8", n_analysed="8", sex="M",
    age_mean="26", age_sd="5", population="healthy_young", body_mass_mean_kg="78.1",
    nutrition_controlled="yes", laterality="mean", outcome_type="volume", modality="MRI",
    unit_original="ml", unit_si="cm3", variance_of="change", variance_type="SD",
    data_source="table", extraction_confidence="high",
    qc_flag="crossover_arms_share_participants;daily_upright_standing_in_both_arms",
    notes=("volume of the imaged segment of each muscle, both legs summed, so laterality is "
           "recorded as mean. MRI at noon on the day the men left the bed. Crossover - both "
           "arms are the same eight men, and calf volumes differed between the two phases"),
)
ZANGE_ARMS = {
    "wbv": dict(arm_id="wbv", arm_type="countermeasure", cm_modality="WBV",
                cm_dose=("20 Hz, 2-4 mm, 5 x 1 min standing at 30 deg knee flexion with 15% "
                         "of body weight added, twice daily")),
    "ctrl": dict(arm_id="ctrl", arm_type="control", cm_modality="none",
                 cm_dose="the same standing routine on a switched-off plate, twice daily"),
}
ZANGE_PAGES = {"Table 1": "Table 1, p. 274", "Table 2": "Table 2, p. 274",
               "Table 3": "Table 3, p. 275"}
# muscle, composite, components, table, {arm: (pre ml, percent change, SD of the change)}
ZANGE_VALUES = [
    ("quadriceps", "TRUE", "vasti;rectus_femoris", "Table 1",
     {"wbv": (2981.9, -6.6, 1.7), "ctrl": (2938.2, -5.8, 1.6)}),
    ("vasti", "TRUE", "vastus_lateralis;vastus_medialis;vastus_intermedius", "Table 1",
     {"wbv": (2625.6, -7.0, 1.7), "ctrl": (2583.9, -5.9, 1.9)}),
    ("rectus_femoris", "FALSE", "NA", "Table 1",
     {"wbv": (356.3, -3.6, 3.7), "ctrl": (354.3, -4.8, 4.0)}),
    ("hamstrings", "TRUE", "lateral_hamstrings;medial_hamstrings", "Table 2",
     {"wbv": (1228.7, -6.1, 1.2), "ctrl": (1194.9, -4.3, 2.0)}),
    ("lateral_hamstrings", "TRUE", "biceps_femoris_long_head;biceps_femoris_short_head",
     "Table 2", {"wbv": (546.3, -5.8, 2.6), "ctrl": (534.8, -4.6, 2.9)}),
    ("medial_hamstrings", "TRUE", "semimembranosus;semitendinosus", "Table 2",
     {"wbv": (682.4, -6.3, 0.6), "ctrl": (660.1, -4.1, 1.6)}),
    ("triceps_surae", "TRUE", "soleus;gastrocnemius_medialis;gastrocnemius_lateralis",
     "Table 3", {"wbv": (1532.9, -6.4, 4.1), "ctrl": (1504.8, -6.5, 3.0)}),
    ("gastrocnemius_medialis", "FALSE", "NA", "Table 3",
     {"wbv": (420.4, -7.3, 5.4), "ctrl": (401.3, -6.6, 6.1)}),
    ("gastrocnemius_lateralis", "FALSE", "NA", "Table 3",
     {"wbv": (254.0, -5.5, 8.2), "ctrl": (250.5, -5.9, 8.9)}),
    ("soleus", "FALSE", "NA", "Table 3",
     {"wbv": (858.5, -5.8, 8.1), "ctrl": (853.0, -6.5, 4.9)}),
]
for muscle, composite, parts, table, arms in ZANGE_VALUES:
    for arm, (pre, pct, sd) in arms.items():
        add(**ZANGE, **ZANGE_ARMS[arm], muscle=muscle, is_composite=composite,
            composite_of=parts, page_ref=ZANGE_PAGES[table],
            value_baseline_original=f"{pre:g}", value_baseline=f"{pre:g}",
            pct_change=f"{pct:g}", variance_value=f"{sd:g}")


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
