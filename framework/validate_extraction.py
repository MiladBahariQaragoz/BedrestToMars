"""Validate an extraction table against data/schema.md v1.0.

Usage:
    python framework/validate_extraction.py data/raw/extraction_partner.csv

Exits non-zero if any check fails, so it can be wired into a pre-commit hook or `make`.
The checks are section 7 of data/schema.md in executable form.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COHORTS_CSV = REPO_ROOT / "data" / "cohorts.csv"
TEMPLATE_CSV = REPO_ROOT / "data" / "extraction_template.csv"

MISSING = {"", "NA", "na", "N/A", "nan", "None"}

ENUMS = {
    "design": {"HDBR_-6", "HDBR_other", "horizontal_BR", "dry_immersion", "ULLS", "spaceflight"},
    "phase": {"bed_rest", "recovery"},
    "exposure_flag": {"analogue", "dry_immersion", "spaceflight"},
    "arm_type": {"control", "countermeasure"},
    "cm_modality": {"none", "resistive", "flywheel", "aerobic", "RVE", "WBV", "nutrition",
                    "artificial_gravity", "LBNP", "NMES", "BFR", "combined"},
    "sex": {"M", "F", "mixed"},
    "population": {"healthy_young", "healthy_middle_aged", "healthy_older", "clinical"},
    "nutrition_controlled": {"yes", "no"},
    "muscle_function_class": {"antigravity_extensor", "flexor", "mixed"},
    "laterality": {"left", "right", "mean", "dominant"},
    "outcome_type": {"volume", "CSA", "lean_mass", "PCSA", "thickness"},
    "modality": {"MRI", "CT", "DXA", "ultrasound", "anthropometry"},
    "unit_si": {"cm3", "cm2", "kg", "mm", "pct_only"},
    "variance_of": {"baseline", "followup", "change"},
    "variance_type": {"SD", "SE", "CI95", "IQR"},
    "data_source": {"table", "text", "figure_digitized", "supplement", "author_correspondence"},
    "extraction_confidence": {"high", "medium", "low"},
    "double_extracted": {"TRUE", "FALSE"},
    "is_composite": {"TRUE", "FALSE"},
}

MUSCLES = {
    "soleus", "gastrocnemius_medialis", "gastrocnemius_lateralis", "gastrocnemius_total",
    "triceps_surae", "tibialis_anterior", "peroneals", "deep_posterior_compartment",
    "vastus_lateralis", "vastus_medialis", "vastus_intermedius", "rectus_femoris",
    "quadriceps", "hamstrings", "adductors", "gluteus_maximus", "gluteus_medius", "gluteus_minimus", "psoas",
    "multifidus", "whole_thigh", "whole_calf", "whole_lower_limb",
    "anterior_thigh_compartment", "posterior_thigh_compartment",
    "flexor_digitorum_longus", "tibialis_posterior",
    "anterior_tibial_group", "flexor_digitorum_with_tibialis_posterior", "flexor_hallucis_longus", "vasti", "adductor_brevis", "adductor_longus", "adductor_magnus", "gracilis", "sartorius", "biceps_femoris_long_head", "biceps_femoris_short_head", "semimembranosus", "semitendinosus", "popliteus", "obturator_externus", "obturator_internus", "quadratus_femoris", "iliopsoas",
}

KEY_FIELDS = ("study_id", "arm_id", "muscle", "phase", "timepoint_days",
              "outcome_type", "modality")

REQUIRED_ALWAYS = (
    "study_id", "cohort_id", "first_author", "year", "doi", "source_file", "design",
    "duration_days", "phase", "timepoint_days", "exposure_flag", "arm_id", "arm_type", "cm_modality",
    "n_arm", "n_analysed", "sex", "age_mean", "population", "muscle", "is_composite",
    "outcome_type", "modality", "unit_original", "unit_si", "pct_change",
    "data_source", "page_ref", "extractor", "extraction_date", "extraction_confidence",
    "double_extracted",
)


def is_missing(value: str) -> bool:
    return value.strip() in MISSING


def as_float(value: str):
    try:
        return float(value.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def expected_row_id(row: dict) -> str:
    return ("{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}"
            "__{modality}_{outcome_type}").format(**row)


def load_known_cohorts() -> set:
    if not COHORTS_CSV.exists():
        return set()
    with COHORTS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {row["cohort_id"].strip() for row in csv.DictReader(handle)}


def validate(path: Path) -> list:
    errors = []

    with TEMPLATE_CSV.open(encoding="utf-8-sig", newline="") as handle:
        expected_columns = next(csv.reader(handle))

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)

    # Check 1 - columns present and in schema order
    if columns != expected_columns:
        missing = [c for c in expected_columns if c not in columns]
        extra = [c for c in columns if c not in expected_columns]
        if missing:
            errors.append(f"header: missing columns {missing}")
        if extra:
            errors.append(f"header: unknown columns {extra}")
        if not missing and not extra:
            errors.append("header: columns are in the wrong order; match data/extraction_template.csv")
        return errors  # every later check assumes the header is right

    known_cohorts = load_known_cohorts()

    # Check 2 - no duplicate primary key
    keys = Counter(tuple(row[field].strip() for field in KEY_FIELDS) for row in rows)
    for key, count in keys.items():
        if count > 1:
            errors.append(f"duplicate primary key {key} appears {count} times")

    for line_number, row in enumerate(rows, start=2):  # line 1 is the header
        where = f"line {line_number}"

        for field in REQUIRED_ALWAYS:
            if is_missing(row[field]):
                errors.append(f"{where}: required field '{field}' is empty")

        # Check 3 - generated row_id
        if row["row_id"].strip() != expected_row_id(row):
            errors.append(f"{where}: row_id should be '{expected_row_id(row)}'")

        # Check 4 - enums and controlled vocabulary
        for field, allowed in ENUMS.items():
            value = row[field].strip()
            if not is_missing(value) and value not in allowed:
                errors.append(f"{where}: '{field}' = '{value}' is not in {sorted(allowed)}")
        muscle = row["muscle"].strip()
        if not is_missing(muscle) and muscle not in MUSCLES:
            errors.append(
                f"{where}: muscle '{muscle}' is not in the controlled vocabulary - "
                "add it to data/schema.md first"
            )

        # Check 5 - pct_change present and sane
        pct_change = as_float(row["pct_change"])
        if pct_change is None:
            errors.append(f"{where}: pct_change is not a number")
        elif not -80.0 <= pct_change <= 40.0:
            errors.append(f"{where}: pct_change = {pct_change} is outside the plausible range -80..40")

        # Check 6 - the recomputed percentage agrees with the recorded one
        baseline = as_float(row["value_baseline"])
        followup = as_float(row["value_followup"])
        skip_agreement = "pct_of_individual_means" in row["qc_flag"]
        if baseline and followup is not None and pct_change is not None and not skip_agreement:
            recomputed = (followup - baseline) / baseline * 100.0
            if abs(recomputed - pct_change) > 0.5:
                errors.append(
                    f"{where}: pct_change = {pct_change} but baseline/follow-up give {recomputed:.2f}"
                )

        # Check 7 - recovery rows carry days_from_unloading_end
        is_recovery = row["phase"].strip() == "recovery"
        has_days_after = not is_missing(row["days_from_unloading_end"])
        if is_recovery and not has_days_after:
            errors.append(f"{where}: phase = recovery requires days_from_unloading_end")
        if not is_recovery and has_days_after:
            errors.append(f"{where}: days_from_unloading_end is only for recovery rows")

        # Check 8 - pct_female exactly when sex = mixed
        is_mixed = row["sex"].strip() == "mixed"
        has_pct_female = not is_missing(row["pct_female"])
        if is_mixed and not has_pct_female:
            errors.append(f"{where}: sex = mixed requires pct_female")
        if not is_mixed and has_pct_female:
            errors.append(f"{where}: pct_female is only for mixed-sex arms")

        # Check 9 - digitizer_tool exactly when the source is a digitised figure
        is_digitized = row["data_source"].strip() == "figure_digitized"
        has_tool = not is_missing(row["digitizer_tool"])
        if is_digitized and not has_tool:
            errors.append(f"{where}: data_source = figure_digitized requires digitizer_tool")
        if not is_digitized and has_tool:
            errors.append(f"{where}: digitizer_tool is only for digitised figures")

        # Check 10 - n_analysed never exceeds n_arm
        n_arm = as_float(row["n_arm"])
        n_analysed = as_float(row["n_analysed"])
        if n_arm is not None and n_analysed is not None and n_analysed > n_arm:
            errors.append(f"{where}: n_analysed ({n_analysed}) exceeds n_arm ({n_arm})")

        # Check 12 - the cohort is known
        cohort_id = row["cohort_id"].strip()
        if known_cohorts and not is_missing(cohort_id) and cohort_id not in known_cohorts:
            errors.append(f"{where}: cohort_id '{cohort_id}' is not in data/cohorts.csv")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    exit_code = 0
    for argument in sys.argv[1:]:
        path = Path(argument)
        errors = validate(path)
        if errors:
            exit_code = 1
            print(f"FAIL {path} - {len(errors)} problem(s):")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
