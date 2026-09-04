"""Rows recovered from papers that never published a complete set of numbers.

    python framework/extractors/partial_rows.py

These 36 studies were parked during the main extraction because their muscle results live
in figures. Most of them still print one or two headline numbers - usually in the abstract,
sometimes in a results sentence - and a percent change with a known duration and exposure is
a usable row even when the group size or the baseline value is missing.

They are kept in data/raw/extraction_partial.csv rather than the main table because they are
systematically weaker: fewer fields, lower confidence, and no baseline to recompute against.
Merging the two files is a deliberate decision for the modelling stage, not a default - and
the `qc_flag` on every row says exactly what is missing.

Validated with:
    python framework/validate_extraction.py data/raw/extraction_partial.csv --partial
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO_ROOT / "data" / "extraction_template.csv"
TARGET = REPO_ROOT / "data" / "raw" / "extraction_partial.csv"
HEADER = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))

ROWS = []


def add(**fields):
    record = {column: "NA" for column in HEADER}
    record.update(extractor="falk", extraction_date="2026-09-04", double_extracted="FALSE",
                  data_source="text", page_ref="abstract")
    record.update(fields)
    site = re.sub(r"[^a-z0-9]+", "_", (record.get("measurement_site") or "").lower()).strip("_")
    suffix = "" if site in {"", "na"} else "__" + site[:24]
    record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                        "__{modality}_{outcome_type}").format(**record) + suffix
    ROWS.append(record)


# --------------------------------------------------------------- Mekjavic 2021 (PlanHab)
# Twelve women and eleven men, three ten-day interventions. Only the female lower-leg CSA
# values are printed in the abstract; the male values and the thigh are in figures.
for arm_id, cm_dose, pct, sd in [
    ("nbr", "NA", -8.0, 1.6),
    ("hbr", "normobaric hypoxia at a simulated 4000 m", -9.9, 2.6),
]:
    add(study_id="mekjavic2021", cohort_id="planhab_br10", campaign_name="PlanHab-type 10-day bed rest",
        first_author="Mekjavic", year="2021", doi="10.1113/ep087834",
        source_file="mekjavicib122021_pubmed_00342.pdf", design="horizontal_BR",
        duration_days="10", phase="bed_rest", timepoint_days="10", exposure_flag="analogue",
        arm_id=arm_id, arm_type="control", cm_modality="none", cm_dose=cm_dose,
        n_arm="12", n_analysed="12", sex="F", population="healthy_young",
        muscle="whole_calf", is_composite="TRUE", outcome_type="CSA", modality="CT",
        unit_original="%", unit_si="pct_only", pct_change=str(pct), variance_of="change",
        variance_type="SD", variance_value=str(sd), extraction_confidence="medium",
        qc_flag="partial_record;female_arm_only;age_not_reported_in_abstract",
        notes=("female lower-leg CSA from the abstract; the male values and every thigh value "
               "are in figures. Crossover, so the two arms share participants"))


# ------------------------------------------------------------------ Debevec 2018 (PlanHab)
# Fourteen men, three 21-day crossover interventions. Thigh muscle size by pQCT.
for arm_id, cm_dose, pct, se in [
    ("nbr", "NA", -6.9, 0.8),
    ("hbr", "normobaric hypoxia at a simulated 4000 m", -9.7, 1.2),
]:
    add(study_id="debevec2018", cohort_id="planhab_br21", campaign_name="PlanHab 21-day bed rest",
        first_author="Debevec", year="2018", doi="10.3389/fphys.2018.00494",
        source_file="debevect2018_scopus_01419.xml", design="horizontal_BR",
        duration_days="21", phase="bed_rest", timepoint_days="21", exposure_flag="analogue",
        arm_id=arm_id, arm_type="control", cm_modality="none", cm_dose=cm_dose,
        n_arm="14", n_analysed="14", sex="M", population="healthy_young",
        muscle="whole_thigh", is_composite="TRUE", outcome_type="CSA", modality="CT",
        unit_original="%", unit_si="pct_only", pct_change=str(pct), variance_of="change",
        variance_type="SE", variance_value=str(se), extraction_confidence="medium",
        qc_flag="partial_record;pqct_reported_as_CT;age_not_reported_in_abstract",
        notes=("thigh muscle size from the abstract; per-muscle values are in Figure 2. "
               "Crossover, so the arms share participants. Hypoxia aggravates the loss"))


# ----------------------------------------------------------------- Holt 2016 (WISE-2005)
for arm_id, arm_type, cm, dose, pct, sd in [
    ("ctrl", "control", "none", "NA", -10.9, 3.4),
    ("ex", "countermeasure", "combined", "flywheel resistive exercise and LBNP treadmill", -4.3, 3.4),
]:
    add(study_id="holt2016", cohort_id="wise2005", campaign_name="WISE-2005",
        first_author="Holt", year="2016", doi="10.1152/japplphysiol.00532.2015",
        source_file="holtja12016_pubmed_00310.pdf", design="HDBR_-6", hdt_angle_deg="-6",
        duration_days="60", phase="bed_rest", timepoint_days="60", exposure_flag="analogue",
        arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose,
        sex="F", population="healthy_young",
        muscle="lumbar_erector_spinae", is_composite="TRUE",
        measurement_site="total lumbar paraspinal muscle", outcome_type="CSA",
        modality="MRI", unit_original="%", unit_si="pct_only", pct_change=str(pct),
        variance_of="change", variance_type="SD", variance_value=str(sd),
        extraction_confidence="medium",
        qc_flag="partial_record;group_size_not_in_abstract;composite_of_four_paraspinal_muscles",
        notes=("total lumbar paraspinal CSA - the sum of four muscles - so it is recorded "
               "against the erector spinae term with a composite site label. Group sizes are "
               "in the full text, not the abstract"))


# ------------------------------------------------------------------ Cavanagh 2016 (84 days)
for muscle, pct, sd in [("quadriceps", -7.2, 5.9), ("gastrocnemius_total", -13.8, 6.1)]:
    add(study_id="cavanagh2016", cohort_id="cavanagh_br84", campaign_name="84-day bed rest with individualised exercise",
        first_author="Cavanagh", year="2016", doi="10.1016/j.bonr.2016.10.001",
        source_file="cavanaghpr2016_scopus_01121.xml", design="HDBR_-6", hdt_angle_deg="-6",
        duration_days="84", phase="bed_rest", timepoint_days="84", exposure_flag="analogue",
        arm_id="ex", arm_type="countermeasure", cm_modality="combined",
        cm_dose="individualised exercise prescription replacing daily load",
        population="healthy_young", muscle=muscle, is_composite="TRUE",
        outcome_type="volume", modality="MRI", unit_original="%", unit_si="pct_only",
        pct_change=str(pct), variance_of="change", variance_type="SD", variance_value=str(sd),
        extraction_confidence="medium",
        qc_flag="partial_record;exercise_arm_only;group_size_not_in_abstract",
        notes=("exercise group only - the control values are truncated in the abstract and "
               "sit in a figure in the paper"))


# ------------------------------------------------------------------- Krainski 2014 (5 weeks)
for arm_id, arm_type, cm, dose, n, muscle, pct, sd in [
    ("br", "control", "none", "NA", 9, "quadriceps", -9.0, 4.0),
    ("br", "control", "none", "NA", 9, "triceps_surae", -19.0, 6.0),
    ("exbr", "countermeasure", "combined", "rowing ergometry six days a week plus resistive strength training twice a week", 18, "quadriceps", -5.0, 4.0),
    ("exbr", "countermeasure", "combined", "rowing ergometry six days a week plus resistive strength training twice a week", 18, "whole_calf", -14.0, 6.0),
]:
    add(study_id="krainski2014", cohort_id="krainski_hdbr35",
        campaign_name="5-week HDBR with rowing ergometry", first_author="Krainski",
        year="2014", doi="10.1152/japplphysiol.00803.2013",
        source_file="krainskif12014_pubmed_00369.pdf", design="HDBR_-6", hdt_angle_deg="-6",
        duration_days="35", phase="bed_rest", timepoint_days="35", exposure_flag="analogue",
        arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose, n_arm=str(n),
        n_analysed=str(n), population="healthy_young", muscle=muscle, is_composite="TRUE",
        outcome_type="volume", modality="MRI", unit_original="%", unit_si="pct_only",
        pct_change=str(pct), variance_of="change", variance_type="SD", variance_value=str(sd),
        extraction_confidence="medium",
        qc_flag="partial_record;muscle_group_naming_inconsistent_in_abstract",
        notes=("the abstract names plantar flexors for the sedentary arm and calf muscle for "
               "the exercise arm; both are recorded as printed rather than harmonised"))


# --------------------------------------------------------------------- Cook 2014 (30-d ULLS)
for arm_id, arm_type, cm, dose, n, muscle, pct in [
    ("ulls", "control", "none", "NA", 8, "quadriceps", -7.0),
    ("ulls", "control", "none", "NA", 8, "triceps_surae", -8.0),
    ("ulls_ex", "countermeasure", "BFR", "blood flow restricted knee extensor exercise three times a week", 8, "quadriceps", -1.0),
    ("ulls_ex", "countermeasure", "BFR", "blood flow restricted knee extensor exercise three times a week", 8, "triceps_surae", -5.0),
]:
    add(study_id="cook2014", cohort_id="cook_ulls30", campaign_name="30-day unilateral lower limb suspension",
        first_author="Cook", year="2014", doi="10.1007/s00421-014-2864-3",
        source_file="cooksb12014_pubmed_00240.pdf", design="ULLS", duration_days="30",
        phase="bed_rest", timepoint_days="30", exposure_flag="analogue", arm_id=arm_id,
        arm_type=arm_type, cm_modality=cm, cm_dose=dose, n_arm=str(n), n_analysed=str(n),
        population="healthy_young", muscle=muscle, is_composite="TRUE",
        outcome_type="CSA", modality="MRI", unit_original="%", unit_si="pct_only",
        pct_change=str(pct), variance_of="change", variance_type="NA",
        extraction_confidence="medium",
        qc_flag="partial_record;no_dispersion_in_abstract;sign_inferred_from_wording",
        notes=("the abstract prints unsigned magnitudes described as decrements, so the sign "
               "is taken from the wording. The exercise arm's knee extensor value is given as "
               "an insignificant reduction of about 1%"))


# --------------------------------------------------------------------- Drummond 2013 (7 days)
add(study_id="drummond2013", cohort_id="drummond_br7", campaign_name="7-day bed rest in older adults",
    first_author="Drummond", year="2013", doi="10.1152/ajpregu.00072.2013",
    source_file="drummondmj12013_pubmed_00216.pdf", design="horizontal_BR",
    duration_days="7", phase="bed_rest", timepoint_days="7", exposure_flag="analogue",
    arm_id="ctrl", arm_type="control", cm_modality="none", n_arm="6", n_analysed="6",
    population="healthy_older", muscle="whole_lower_limb", is_composite="TRUE",
    outcome_type="lean_mass", modality="DXA", unit_original="%", unit_si="pct_only",
    pct_change="-4.0", variance_of="change", variance_type="NA",
    extraction_confidence="low",
    qc_flag="partial_record;approximate_value;no_dispersion_in_abstract",
    notes="the abstract says participants lost about 4% leg lean mass; no dispersion given")


# ------------------------------------------------------------------ Rittweger 2013 (89 days)
add(study_id="rittweger2013", cohort_id="medes_ltbr90",
    campaign_name="Long Term Bed Rest (LTBR), MEDES Toulouse", first_author="Rittweger",
    year="2013", doi="10.1002/mus.23644", source_file="rittwegerj12013_pubmed_00227.pdf",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="90", phase="bed_rest",
    timepoint_days="89", exposure_flag="analogue", arm_id="ctrl", arm_type="control",
    cm_modality="none", n_arm="17", n_analysed="17", sex="M", population="healthy_young",
    muscle="whole_calf", is_composite="TRUE", outcome_type="CSA", modality="CT",
    unit_original="%", unit_si="pct_only", pct_change="-26.6", variance_of="change",
    variance_type="SD", variance_value="3.8", extraction_confidence="medium",
    qc_flag="partial_record;pqct_reported_as_CT;n_derived_from_total_minus_exercise_group",
    notes=("25 men of whom 8 performed flywheel exercise, so the control arm is 17. Same "
           "MEDES LTBR campaign as belavy2017 - the largest single loss in the dataset"))


# --------------------------------------------------------------------- Dirks 2019 (7 days)
for arm_id, dose, pct, sd in [
    ("intermittent", "intermittent feeding pattern", -1.1, 0.6),
    ("continuous", "continuous feeding pattern", -0.8, 0.5),
]:
    add(study_id="dirks2019", cohort_id="maastricht_br7_feeding",
        campaign_name="7-day bed rest with two feeding patterns", first_author="Dirks",
        year="2019", doi="10.1152/ajpendo.00378.2018", source_file="dirksml12019_pubmed_00384.pdf",
        design="horizontal_BR", duration_days="7", phase="bed_rest", timepoint_days="7",
        exposure_flag="analogue", arm_id=arm_id, arm_type="countermeasure",
        cm_modality="nutrition", cm_dose=dose, n_arm="10", n_analysed="10", sex="M",
        age_mean="25", age_sd="1", population="healthy_young", muscle="quadriceps",
        is_composite="TRUE", outcome_type="CSA", modality="CT", unit_original="%",
        unit_si="pct_only", pct_change=str(pct), variance_of="change", variance_type="SD",
        variance_value=str(sd), extraction_confidence="medium",
        qc_flag="partial_record;group_size_split_assumed_even",
        notes=("20 men across two feeding patterns; the abstract does not give the split, so "
               "ten per arm is assumed and flagged. Same group as dirks2016 - check for "
               "participant overlap before treating them as separate cohorts"))


# --------------------------------------------------------- Holt 2015 (WISE-2005 abstract)
# Conference abstract companion to holt2016, reporting both total CSA and functional CSA -
# the lean-tissue-only area inside the same outline. Group sizes are not given.
for arm_id, arm_type, cm, dose, site, pct in [
    ("ctrl", "control", "none", "NA", "total paraspinal CSA", -12.0),
    ("ex", "countermeasure", "combined", "flywheel resistive exercise and LBNP treadmill", "total paraspinal CSA", -6.0),
    ("ctrl", "control", "none", "NA", "paraspinal functional CSA (lean tissue only)", -19.0),
    ("ex", "countermeasure", "combined", "flywheel resistive exercise and LBNP treadmill", "paraspinal functional CSA (lean tissue only)", -5.0),
]:
    add(study_id="holt2015", cohort_id="wise2005", campaign_name="WISE-2005",
        first_author="Holt", year="2015", doi="10.1249/01.mss.0000478309.26945.3d",
        source_file="holt2015_wos_00614.pdf", design="HDBR_-6", hdt_angle_deg="-6",
        duration_days="60", phase="bed_rest", timepoint_days="60", exposure_flag="analogue",
        arm_id=arm_id, arm_type=arm_type, cm_modality=cm, cm_dose=dose, sex="F",
        population="healthy_young", muscle="lumbar_erector_spinae", is_composite="TRUE",
        measurement_site=site, outcome_type="CSA", modality="MRI", unit_original="%",
        unit_si="pct_only", pct_change=str(pct), variance_of="change", variance_type="NA",
        extraction_confidence="low",
        qc_flag="partial_record;conference_abstract;no_dispersion;group_size_not_reported",
        notes=("conference abstract for the same WISE-2005 analysis as holt2016, whose full "
               "paper gives 10.9% and 4.3% for total CSA - the two disagree slightly and the "
               "full paper should win when they are reconciled"))


# ------------------------------------------------------- Hides 2016 (spaceflight multifidus)
# Same astronaut series as hides2021. Crew size and mission durations are not stated, so
# duration is carried from the companion paper and flagged.
for site, pct, baseline, followup in [
    ("L2 vertebral level", 7.0, None, None),
    ("L3 vertebral level", 7.0, None, None),
    ("L4 vertebral level", -1.0, None, None),
    ("L5 vertebral level", -29.1, 9.86, 6.99),
]:
    add(study_id="hides2016", cohort_id="iss_hides_astronauts",
        campaign_name="ISS long-duration missions (Hides series)", first_author="Hides",
        year="2016", doi="10.1007/s00586-015-4311-5",
        source_file="hidesja12016_pubmed_00250.pdf", design="spaceflight",
        duration_days="180", phase="recovery", timepoint_days="181",
        days_from_unloading_end="1", exposure_flag="spaceflight", arm_id="ctrl",
        arm_type="control", cm_modality="none", population="healthy_middle_aged",
        muscle="multifidus", is_composite="FALSE", laterality="mean",
        measurement_site=site, outcome_type="CSA", modality="MRI",
        unit_original="cm2" if baseline else "%",
        unit_si="cm2" if baseline else "pct_only",
        value_baseline=str(baseline) if baseline else "NA",
        value_followup=str(followup) if followup else "NA",
        pct_change=str(pct), variance_of="change", variance_type="NA",
        extraction_confidence="low",
        qc_flag=("partial_record;age_not_published;crew_size_not_reported;"
                 "duration_carried_from_companion_paper;values_read_from_prose"),
        notes=("values described in the text rather than tabulated - L2 and L3 both increase "
               "about 7%, L4 changes little, L5 falls from 9.86 to 6.99 cm2. Same crew series "
               "as hides2021, so one cohort"))


# ------------------------------------------------------------------------- Rejc 2018
add(study_id="rejc2018", cohort_id="izola_br14", campaign_name="14-day bed rest, young and older men",
    first_author="Rejc", year="2018", doi="10.1113/jp274772",
    source_file="rejce12018_pubmed_00379.pdf", design="horizontal_BR", duration_days="14",
    phase="bed_rest", timepoint_days="14", exposure_flag="analogue", arm_id="old",
    arm_type="control", cm_modality="none", sex="M", population="healthy_older",
    muscle="quadriceps", is_composite="TRUE", laterality="right", outcome_type="volume",
    modality="MRI", unit_original="%", unit_si="pct_only", pct_change="-8.3",
    variance_of="change", variance_type="NA", extraction_confidence="low",
    qc_flag="partial_record;young_arm_value_unreadable;no_dispersion;group_size_not_recovered",
    notes=("the older arm's 8.3% loss is legible; the young arm's value is mangled by PDF "
           "text extraction. Same campaign as pisot2016, which reports both arms cleanly - "
           "prefer that row and treat this one as a cross-check"))


if __name__ == "__main__":
    studies = {row["study_id"] for row in ROWS}
    existing = list(csv.DictReader(TARGET.open(encoding="utf-8-sig")))
    keep = [row for row in existing if row["study_id"] not in studies]
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(keep)
        writer.writerows(ROWS)
    print(f"{len(ROWS)} partial rows written for {len(studies)} studies: {sorted(studies)}")
