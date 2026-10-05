"""Build the browsable HTML inventory of the extraction tables.

    python framework/build_data_report.py              # standalone file, opens in a browser
    python framework/build_data_report.py --fragment   # headless form, for publishing

Reads the four tables in data/raw/, injects them into framework/report_template.html and
writes docs/data_report.html. The report is regenerated rather than maintained, so it can
never drift from the CSVs it describes - same contract as extraction_report.py.

The template holds head content (title, font link, styles) followed by body content, and no
document skeleton, because a publisher supplies one. --fragment emits it that way. Without
the flag the skeleton is added here, which is what makes the file openable off the disk.

The template carries the layout and the prose; this script carries the numbers. Three things
are injected: every row in a slim column subset for the charts and the browser, the field
completeness count for all 61 schema columns, and one real record broken into the seven
groups the schema actually answers.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

csv.field_size_limit(10_000_000)

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "framework" / "report_template.html"
REPORT = REPO_ROOT / "docs" / "data_report.html"

TABLES = {
    "main": REPO_ROOT / "data" / "raw" / "extraction_qaragoz.csv",
    "partial": REPO_ROOT / "data" / "raw" / "extraction_partial.csv",
    "figures": REPO_ROOT / "data" / "raw" / "extraction_figures.csv",
    "nasa": REPO_ROOT / "data" / "raw" / "extraction_nasa.csv",
}

# The columns the charts and the row browser need. The full 61 stay in the CSVs; shipping
# them all would triple the page weight to show fields nothing on the page reads.
SLIM = ["study_id", "cohort_id", "campaign_name", "first_author", "year", "design",
        "exposure_flag", "duration_days", "phase", "timepoint_days", "days_from_unloading_end",
        "arm_id", "arm_type", "cm_modality", "n_analysed", "sex", "age_mean", "population",
        "muscle", "is_composite", "measurement_site", "outcome_type", "modality", "unit_si",
        "value_baseline", "value_followup", "pct_change", "data_source",
        "extraction_confidence", "qc_flag", "doi"]

# One row, regrouped into the questions the schema answers. The gloss is what a reader needs
# to know about the group, not a restatement of the field names.
GROUPS = [
    ("Which paper", ["row_id", "study_id", "cohort_id", "campaign_name", "registry_id",
                     "first_author", "year", "doi", "source_file"],
     "<code>cohort_id</code> is the campaign, not the paper &mdash; it is what validation groups on.",
     ["cohort_id"]),
    ("What the exposure was", ["design", "hdt_angle_deg", "duration_days", "phase",
                               "timepoint_days", "days_from_unloading_end", "exposure_flag"],
     "How long they were unloaded, and when in that window this measurement was taken.",
     ["duration_days"]),
    ("Which arm of the study", ["arm_id", "arm_type", "cm_modality", "cm_dose", "n_arm", "n_analysed"],
     "A countermeasure arm is not a bed-rest observation and must never be pooled as one.",
     ["arm_type"]),
    ("Who the participants were", ["sex", "pct_female", "age_mean", "age_sd", "age_min",
                                   "age_max", "population", "bmi_mean", "body_mass_mean_kg",
                                   "nutrition_controlled"],
     "<code>n_analysed</code>, above, is the weight; these describe who those people were.",
     []),
    ("Which muscle", ["muscle", "muscle_function_class", "is_composite", "composite_of",
                      "laterality", "measurement_site"],
     "One controlled vocabulary. <code>triceps_surae</code> is never the same row as soleus plus gastrocnemius.",
     ["muscle"]),
    ("What was measured, and what it came out as",
     ["outcome_type", "modality", "unit_original", "value_baseline_original",
      "value_followup_original", "unit_si", "value_baseline", "value_followup",
      "change_absolute", "pct_change", "variance_of", "variance_type", "variance_value", "p_value"],
     "Printed values are kept verbatim alongside the converted ones. <code>pct_change</code> is the target variable.",
     ["pct_change"]),
    ("How much to trust it", ["data_source", "digitizer_tool", "page_ref", "extractor",
                              "extraction_date", "extraction_confidence", "double_extracted",
                              "qc_flag", "notes"],
     "Every judgement call made while reading the paper is written down here rather than smoothed away.",
     ["qc_flag"]),
]

ANATOMY_PICK = {"study_id": "tran2021", "muscle": "gluteus_maximus", "phase": "bed_rest"}

# The skeleton a publisher would otherwise wrap around the template, reproduced so the file
# opens the same way off the disk: standards mode, a viewport, and the same small reset.
SKELETON = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 0; font: 14px system-ui, -apple-system, "Segoe UI", sans-serif; background: #fdfdfc; }}
  img {{ max-width: 100%; }}
  [hidden] {{ display: none !important; }}
</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""


def wrap(html: str) -> str:
    """Split the template into head and body at the end of its style block."""
    marker = "</style>"
    cut = html.index(marker) + len(marker)
    return SKELETON.format(head=html[:cut].strip(), body=html[cut:].strip())


def load() -> tuple[list[dict], list[str]]:
    rows, header = [], None
    for label, path in TABLES.items():
        reader = csv.DictReader(path.open(encoding="utf-8-sig"))
        header = header or list(reader.fieldnames)
        for row in reader:
            row["_table"] = label
            rows.append(row)
    return rows, header


def pick_anatomy(rows: list[dict]) -> list[dict]:
    match = next((r for r in rows
                  if all(r.get(k) == v for k, v in ANATOMY_PICK.items())), None)
    if match is None:
        raise SystemExit(f"no row matching {ANATOMY_PICK}; update ANATOMY_PICK")

    blocks = []
    for title, fields, gloss, key in GROUPS:
        blocks.append({
            "title": title,
            "gloss": gloss,
            "key": key,
            "fields": [[name, match.get(name, "NA")] for name in fields],
        })
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragment", action="store_true",
                        help="omit the document skeleton, for a publisher that supplies one")
    parser.add_argument("--out", type=Path, default=REPORT, help="output path")
    args = parser.parse_args()

    rows, header = load()
    payload = {
        "cols": ["table"] + SLIM,
        "rows": [[row["_table"]] + [row.get(c, "NA") for c in SLIM] for row in rows],
        "coverage": [[c, sum(1 for r in rows if r.get(c) not in ("NA", "", None))] for c in header],
        "anatomy": pick_anatomy(rows),
    }

    # </script> anywhere in the data would close the tag holding it early.
    encoded = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")

    # Every count the prose quotes is filled from the rows rather than typed into the template,
    # so the text cannot fall behind the tables when rows are added, corrected or merged.
    cohort_studies = {}
    for r in rows:
        cohort_studies.setdefault(r["cohort_id"], set()).add(r["study_id"])
    counts = {
        "__N_ROWS__": len(rows),
        "__N_STUDIES__": len({r["study_id"] for r in rows}),
        "__N_COHORTS__": len(cohort_studies),
        "__N_SHARED_COHORTS__": sum(len(s) > 1 for s in cohort_studies.values()),
        "__N_RECOVERY__": sum(r["phase"] == "recovery" for r in rows),
        "__N_SPACEFLIGHT__": sum(r["exposure_flag"] == "spaceflight" for r in rows),
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DATE__", date.today().isoformat()).replace("__DATA__", encoded)
    for placeholder, value in counts.items():
        html = html.replace(placeholder, str(value))
    if not args.fragment:
        html = wrap(html)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")

    print(f"wrote {args.out}: {len(rows)} rows, "
          f"{len({r['study_id'] for r in rows})} studies, "
          f"{len({r['cohort_id'] for r in rows})} cohorts, "
          f"{args.out.stat().st_size // 1024} KB"
          f"{' (fragment)' if args.fragment else ' (standalone)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
