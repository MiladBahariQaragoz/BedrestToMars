"""Rows read off published figures.

    python framework/extractors/figure_rows.py

Twenty-four of the included studies publish their muscle outcomes only as charts. This file
holds what could be recovered from them, in a third table -
data/raw/extraction_figures.csv - so that a number read off a bar chart is never silently
mixed with a number read out of a results table.

Two kinds of row live here, and the `digitizer_tool` field says which:

    "page text beside the figure"  the value is printed in the surrounding prose and is
                                   exact; the figure only told us where to look
    "visual reading of rendered figure at 190 dpi"  the value was read off the chart against
                                   its axis, and is an estimate

Nothing here is better than `medium` confidence, and every row carries `figure_derived` in
`qc_flag`. Validated with:

    python framework/validate_extraction.py data/raw/extraction_figures.csv --partial
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO_ROOT / "data" / "extraction_template.csv"
TARGET = REPO_ROOT / "data" / "raw" / "extraction_figures.csv"
HEADER = next(csv.reader(TEMPLATE.open(encoding="utf-8-sig")))

ROWS = []

EXACT = "page text beside the figure"
READ = "visual reading of rendered figure at 190 dpi"


def add(**fields):
    record = {column: "NA" for column in HEADER}
    record.update(extractor="qaragoz", extraction_date="2026-09-04", double_extracted="FALSE",
                  data_source="figure_digitized")
    record.update(fields)
    site = re.sub(r"[^a-z0-9]+", "_", (record.get("measurement_site") or "").lower()).strip("_")
    suffix = "" if site in {"", "na"} else "__" + site[:24]
    record["row_id"] = ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
                        "__{modality}_{outcome_type}").format(**record) + suffix
    ROWS.append(record)


# ------------------------------------------------- Mekjavic 2021 - male lower leg (exact)
# Rendering Figure 4 put the results prose on the same page, and it gives the male values
# the abstract omitted. Exact numbers, not estimates.
for arm_id, cm_dose, pct, sd in [
    ("nbr", "NA", -6.2, 1.8),
    ("hbr", "normobaric hypoxia at a simulated 4000 m", -7.7, 3.3),
]:
    add(study_id="mekjavic2021", cohort_id="planhab_br10", campaign_name="PlanHab-type 10-day bed rest",
        first_author="Mekjavic", year="2021", doi="10.1113/ep087834",
        source_file="mekjavicib122021_pubmed_00342_p10.png", design="horizontal_BR",
        duration_days="10", phase="bed_rest", timepoint_days="10", exposure_flag="analogue",
        arm_id=f"{arm_id}_male", arm_type="control", cm_modality="none", cm_dose=cm_dose,
        n_arm="11", n_analysed="11", sex="M", population="healthy_young",
        muscle="whole_calf", is_composite="TRUE", outcome_type="CSA", modality="CT",
        unit_original="%", unit_si="pct_only", pct_change=str(pct), variance_of="change",
        variance_type="SD", variance_value=str(sd), digitizer_tool=EXACT,
        page_ref="Figure 4 and surrounding text", extraction_confidence="high",
        qc_flag="figure_derived;value_exact_from_page_text",
        notes=("the male lower-leg CSA values are printed in the prose beside Figure 4; the "
               "abstract gave only the female arm. Crossover, so arms share participants"))


# --------------------------------------------------- Krainski 2014 - all four muscle groups
# Figure 4 prints the percent change under each panel, for both arms, which is more than the
# abstract carried. Baseline volumes are the plotted group means, read off the axis.
KRAINSKI = dict(
    study_id="krainski2014", cohort_id="krainski_hdbr35",
    campaign_name="5-week HDBR with rowing ergometry", first_author="Krainski", year="2014",
    doi="10.1152/japplphysiol.00803.2013",
    source_file="krainskif12014_pubmed_00369_p6.png", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="35", phase="bed_rest", timepoint_days="35", exposure_flag="analogue",
    population="healthy_young", is_composite="TRUE", outcome_type="volume", modality="MRI",
    unit_original="%", unit_si="pct_only", variance_of="change", variance_type="NA",
    page_ref="Figure 4", extraction_confidence="medium",
    qc_flag="figure_derived;percent_exact_from_panel_label;baseline_read_from_axis",
    notes=("the percent change is printed under each panel of Figure 4 and is exact; the "
           "baseline volume is the plotted group mean read against the axis and is an "
           "estimate, carried only as context"),
)
for muscle, arm_id, arm_type, cm, dose, n, pct, baseline in [
    ("quadriceps", "br", "control", "none", "NA", 9, -9, 618),
    ("quadriceps", "exbr", "countermeasure", "combined", "rowing ergometry six days a week plus resistive strength training twice a week", 18, -5, 640),
    ("hamstrings", "br", "control", "none", "NA", 9, -8, 195),
    ("hamstrings", "exbr", "countermeasure", "combined", "rowing ergometry six days a week plus resistive strength training twice a week", 18, -7, 222),
    ("triceps_surae", "br", "control", "none", "NA", 9, -19, 362),
    ("triceps_surae", "exbr", "countermeasure", "combined", "rowing ergometry six days a week plus resistive strength training twice a week", 18, -14, 362),
    ("anterior_tibial_group", "br", "control", "none", "NA", 9, -9, 79),
    ("anterior_tibial_group", "exbr", "countermeasure", "combined", "rowing ergometry six days a week plus resistive strength training twice a week", 18, -5, 73),
]:
    add(**KRAINSKI, muscle=muscle, arm_id=arm_id, arm_type=arm_type, cm_modality=cm,
        cm_dose=dose, n_arm=str(n), n_analysed=str(n), pct_change=str(pct),
        value_baseline_original=str(baseline), value_baseline=str(baseline),
        digitizer_tool=EXACT)


# ------------------------------------------------- Rittweger 2013 - the flywheel arm (exact)
for arm_id, arm_type, cm, dose, n, pct, sd in [
    ("fw", "countermeasure", "flywheel", "resistive flywheel exercise 2-3 times per week", 8, -18.6, 3.0),
]:
    add(study_id="rittweger2013", cohort_id="medes_ltbr90",
        campaign_name="Long Term Bed Rest (LTBR), MEDES Toulouse", first_author="Rittweger",
        year="2013", doi="10.1002/mus.23644",
        source_file="rittwegerj12013_pubmed_00227_p4.png", design="HDBR_-6",
        hdt_angle_deg="-6", duration_days="90", phase="bed_rest", timepoint_days="89",
        exposure_flag="analogue", arm_id=arm_id, arm_type=arm_type, cm_modality=cm,
        cm_dose=dose, n_arm=str(n), n_analysed=str(n), sex="M", population="healthy_young",
        muscle="whole_calf", is_composite="TRUE", outcome_type="CSA", modality="CT",
        unit_original="%", unit_si="pct_only", pct_change=str(pct), variance_of="change",
        variance_type="SD", variance_value=str(sd), digitizer_tool=EXACT,
        page_ref="Figure 1 and surrounding text", extraction_confidence="high",
        qc_flag="figure_derived;value_exact_from_page_text;pqct_reported_as_CT",
        notes=("the exercise arm's 18.6% loss is printed beside Figure 1; the partial table "
               "already holds the control arm's 26.6%. Same MEDES LTBR cohort as belavy2017"))


# ------------------------------------------------------- Tanner 2015 - read from the chart
TANNER = dict(
    study_id="tanner2015", cohort_id="tanner_br5", campaign_name="5-day bed rest, young and older adults",
    first_author="Tanner", year="2015", doi="10.1113/jp270699",
    source_file="tannerre12015_pubmed_00386_p7.png", design="horizontal_BR",
    duration_days="5", phase="bed_rest", timepoint_days="5", exposure_flag="analogue",
    arm_type="control", cm_modality="none", muscle="whole_lower_limb", is_composite="TRUE",
    outcome_type="lean_mass", modality="DXA", unit_original="%", unit_si="pct_only",
    variance_of="change", variance_type="SE", digitizer_tool=READ, page_ref="Figure 2A",
    extraction_confidence="medium",
    qc_flag="figure_derived;read_from_bar_chart;values_approximate",
    notes=("percent change in leg lean mass read off Figure 2A against its axis - the bars "
           "are small and the reading is approximate. Baseline leg lean mass is printed in "
           "the text: 15.7 kg young, 13.4 kg older"),
)
for arm_id, population, n, age, age_se, baseline, pct, se in [
    ("young", "healthy_young", 14, 22, 1, 15.7, -0.3, 0.7),
    ("old", "healthy_older", 9, 68, 1, 13.4, -3.8, 0.8),
]:
    add(**TANNER, arm_id=arm_id, population=population, n_arm=str(n), n_analysed=str(n),
        age_mean=str(age), age_sd=str(age_se), value_baseline=str(baseline),
        value_baseline_original=str(baseline), pct_change=str(pct), variance_value=str(se))


# ----------------------------------------------------------- Lair 2026 - the first dry immersion
# Figure 3F plots quadriceps MRI CSA in pixel counts. The printed change is 218 pixels
# [95% CI 120 to 317] and the plotted baseline is about 7,800 pixels, so the percent change
# is those two combined - the paper never prints it directly. Pixel counts are proportional
# to area for one acquisition protocol, so the ratio is meaningful even though the unit is not.
add(study_id="lair2026", cohort_id="di5_toulouse", campaign_name="5-day dry immersion",
    registry_id="NCT03915457", first_author="Lair", year="2026",
    doi="10.1152/japplphysiol.00481.2025",
    source_file="lairb12026_pubmed_00900_p7.png", design="dry_immersion", duration_days="5",
    phase="bed_rest", timepoint_days="5", exposure_flag="dry_immersion", arm_id="ctrl",
    arm_type="control", cm_modality="none", n_arm="18", n_analysed="18",
    population="healthy_young", muscle="quadriceps", is_composite="TRUE",
    outcome_type="CSA", modality="MRI", unit_original="pixel count", unit_si="pct_only",
    pct_change="-2.8", variance_of="change", variance_type="CI95", variance_value="1.3",
    digitizer_tool="printed change with the baseline read off Figure 3F",
    page_ref="Figure 3F and Results text", extraction_confidence="low",
    qc_flag=("figure_derived;pct_derived_from_printed_change_and_read_baseline;"
             "outcome_in_pixel_counts"),
    notes=("the dataset's first dry immersion row. The paper reports a 218-pixel fall in "
           "quadriceps CSA with a 95% CI of 120 to 317 and plots a baseline near 7,800 "
           "pixels; dividing gives -2.8% with a CI half-width near 1.3 points. Low confidence "
           "because the denominator was read off a chart"))


# ------------------------------------------------ Dulac 2024 - upper quadriceps volume (read)
# J Physiol 603.13, online 2024. Fourteen days of 6 deg head-down tilt in adults aged 55-65,
# control against a multimodal in-bed exercise programme - the only older cohort with an MRI
# outcome. Fig. 2C plots baseline upper-quadriceps volume and Fig. 2D the change in cm3 at the
# end of bed rest and on day 6 of recovery; no value is printed anywhere, so the percent change
# is the read change over the read baseline. The figure labels the occasions HDBR14 and R7;
# the Methods say day 13 of bed rest and day 6 of recovery, which is what is used here.
DULAC = dict(
    study_id="dulac2024", cohort_id="mcgill_hdbr14",
    campaign_name="McGill 14-day HDBR in older adults", registry_id="NCT04964999",
    first_author="Dulac", year="2024", doi="10.1113/JP285897",
    source_file="dulac2024_15_1pdf_p7.png", design="HDBR_-6", hdt_angle_deg="-6",
    duration_days="14", exposure_flag="analogue", sex="mixed", population="healthy_older",
    muscle="quadriceps", is_composite="TRUE", laterality="right",
    measurement_site="upper 33% of thigh", outcome_type="volume", modality="MRI",
    unit_original="cm3", unit_si="cm3", digitizer_tool="visual reading of rendered figure at 300 dpi",
    page_ref="p. 3819, Fig. 2C and 2D", extraction_confidence="low",
)
DULAC_ARMS = {
    "ctrl": dict(arm_id="ctrl", arm_type="control", cm_modality="none", n_arm="11",
                 pct_female="45.5", age_mean="58.4", age_sd="3.9", bmi_mean="24.5"),
    "ex": dict(arm_id="ex", arm_type="countermeasure", cm_modality="combined",
               cm_dose=("three in-bed sessions a day, 60-62 min in total: HIIT, continuous and "
                        "progressive aerobic, upper- and lower-body resistance"),
               n_arm="11", pct_female="54.5", age_mean="58.4", age_sd="3.4", bmi_mean="26.1"),
}
# arm, phase, day, days after bed rest, n in Fig. 2D, read baseline, read change, percent
for arm, phase, day, after, n, baseline, change, pct in [
    ("ctrl", "bed_rest", "13", "NA", 11, 61.9, -4.0, -6.4),
    ("ex", "bed_rest", "13", "NA", 9, 70.2, -0.6, -0.9),
    ("ctrl", "recovery", "20", "6", 9, 61.9, -2.1, -3.4),
    ("ex", "recovery", "20", "6", 9, 70.2, 0.7, 0.9),
]:
    flags = "figure_derived;pct_derived_from_read_change_and_read_baseline"
    if arm == "ex":
        flags += ";baseline_n_differs_from_change_n"
    if phase == "recovery":
        flags += ";recovery_measurement"
    add(**DULAC, **DULAC_ARMS[arm], phase=phase, timepoint_days=day,
        days_from_unloading_end=after, n_analysed=str(n),
        value_baseline_original=str(baseline), value_baseline=str(baseline),
        change_absolute=str(change), pct_change=str(pct), qc_flag=flags,
        notes=("baseline read off Fig. 2C (control n = 11, exercise n = 7) and the mean change "
               "off Fig. 2D (control n = 11 in bed rest and 9 in recovery, after two were "
               "withdrawn on recovery day 3; exercise n = 9); the two readings are good to "
               "about 1 cm3 and 0.1 cm3. Upper-thigh slab of two 1 cm slices at 33% of femur "
               "length, right leg"))


# ---------------------------------------- Alkner 2004 - quadriceps in the exercise arm (read)
# The text says only that the flywheel group "showed no change" in quadriceps volume; Fig. 1
# plots it. Read the same way, the bed-rest-only bars come out at 968, 876 and 791 cm3 against
# the 973, 879 and 793 that trappe2023 prints for the same men, so the reading is good to a
# few cm3.
add(study_id="alkner2004", cohort_id="medes_ltbr90",
    campaign_name="Long Term Bed Rest (LTBR), MEDES Toulouse", first_author="Alkner",
    year="2004", doi="10.1007/s00421-004-1172-8", source_file="alkner2004_7pdf_p5.png",
    design="HDBR_-6", hdt_angle_deg="-6", duration_days="90", phase="bed_rest",
    timepoint_days="89", exposure_flag="analogue", arm_id="bre", arm_type="countermeasure",
    cm_modality="flywheel",
    cm_dose=("flywheel supine squat 4 x 7 and calf press 4 x 14 maximal coupled "
             "concentric-eccentric actions every third day from day 5"),
    n_arm="9", n_analysed="8", sex="M", age_mean="33", age_sd="5",
    population="healthy_young", muscle="quadriceps", is_composite="TRUE",
    composite_of="vasti;rectus_femoris", laterality="mean", outcome_type="volume",
    modality="MRI", unit_original="cm3", unit_si="cm3", value_baseline_original="1103",
    value_baseline="1103", value_followup_original="1095", value_followup="1095",
    change_absolute="-8", pct_change="-0.73", digitizer_tool=READ,
    page_ref="Fig. 1, p. 298", extraction_confidence="low",
    qc_flag="figure_derived;values_read_from_bar_heights;overlaps_other_paper",
    notes=("pre and day-89 bar heights for the flywheel group; the text reports no change. "
           "belavy2017 segments the same campaign's quadriceps muscles itself"))


if __name__ == "__main__":
    if not TARGET.exists():
        TARGET.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    studies = {row["study_id"] for row in ROWS}
    existing = list(csv.DictReader(TARGET.open(encoding="utf-8-sig")))
    keep = [row for row in existing if row["study_id"] not in studies]
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(keep)
        writer.writerows(ROWS)
    print(f"{len(ROWS)} figure rows written for {len(studies)} studies: {sorted(studies)}")
