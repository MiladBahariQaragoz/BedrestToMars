"""Summarise the extraction table as it stands.

    python framework/extraction_report.py

Writes data/raw/extraction_report.md - what is in the dataset, per study and per cohort,
plus the shape of the duration axis the models will have to fit. Regenerated rather than
maintained by hand, so it can never disagree with the CSV it describes.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTION = REPO_ROOT / "data" / "raw" / "extraction_falk.csv"
REPORT = REPO_ROOT / "data" / "raw" / "extraction_report.md"

csv.field_size_limit(10_000_000)


def main() -> int:
    rows = list(csv.DictReader(EXTRACTION.open(encoding="utf-8-sig")))
    bed_rest = [r for r in rows if r["phase"] == "bed_rest"]

    by_study = defaultdict(list)
    for row in rows:
        by_study[row["study_id"]].append(row)

    lines = [
        "# Extraction Progress",
        "",
        f"Generated {date.today().isoformat()} from `data/raw/extraction_falk.csv`.",
        "",
        f"- **{len(rows)} rows** across **{len({r['study_id'] for r in rows})} studies** "
        f"and **{len({r['cohort_id'] for r in rows})} cohorts**",
        f"- **{len(bed_rest)}** rows measured during unloading, "
        f"{len(rows) - len(bed_rest)} during recovery",
        f"- **{len({r['muscle'] for r in rows})} distinct muscles**",
        f"- Every row is `double_extracted = FALSE`: "
        f"{sum(1 for r in rows if r['double_extracted'] == 'TRUE')} have been checked by a second person",
        "",
        "## By study",
        "",
        "| Study | Cohort | Design | Days | n rows | Muscles | Arms |",
        "|---|---|---|---|---|---|---|",
    ]
    for study_id in sorted(by_study, key=lambda s: -len(by_study[s])):
        study_rows = by_study[study_id]
        first = study_rows[0]
        lines.append(
            f"| `{study_id}` | `{first['cohort_id']}` | {first['design']} | "
            f"{first['duration_days']} | {len(study_rows)} | "
            f"{len({r['muscle'] for r in study_rows})} | "
            f"{len({r['arm_id'] for r in study_rows})} |")

    cohorts = defaultdict(set)
    for row in rows:
        cohorts[row["cohort_id"]].add(row["study_id"])
    shared = {c: s for c, s in cohorts.items() if len(s) > 1}

    lines += [
        "",
        "## Cohorts carrying more than one study",
        "",
        "These are the reason validation is grouped by cohort rather than by paper.",
        "",
    ]
    if shared:
        for cohort, studies in sorted(shared.items()):
            lines.append(f"- **`{cohort}`** — {', '.join(sorted(studies))}")
    else:
        lines.append("- none yet")

    durations = Counter(int(r["duration_days"]) for r in bed_rest if r["duration_days"].isdigit())
    lines += [
        "",
        "## The duration axis, in unloading rows",
        "",
        "| Unloading duration (days) | Rows |",
        "|---|---|",
    ]
    for duration, count in sorted(durations.items()):
        lines.append(f"| {duration} | {count} |")

    modality = Counter(r["modality"] for r in rows)
    outcome = Counter(r["outcome_type"] for r in rows)
    confidence = Counter(r["extraction_confidence"] for r in rows)
    source = Counter(r["data_source"] for r in rows)
    lines += [
        "",
        "## How the numbers were measured and where they came from",
        "",
        f"- **Modality:** {', '.join(f'{k} {v}' for k, v in modality.most_common())}",
        f"- **Outcome:** {', '.join(f'{k} {v}' for k, v in outcome.most_common())}",
        f"- **Source:** {', '.join(f'{k} {v}' for k, v in source.most_common())}",
        f"- **Confidence:** {', '.join(f'{k} {v}' for k, v in confidence.most_common())}",
        "",
        "## The most and least affected muscles so far",
        "",
        "Mean percent change across unloading rows, muscles with at least four rows.",
        "",
        "| Muscle | Rows | Mean % change |",
        "|---|---|---|",
    ]
    per_muscle = defaultdict(list)
    for row in bed_rest:
        try:
            per_muscle[row["muscle"]].append(float(row["pct_change"]))
        except ValueError:
            continue
    ranked = sorted(((m, v) for m, v in per_muscle.items() if len(v) >= 4),
                    key=lambda item: sum(item[1]) / len(item[1]))
    for muscle, values in ranked:
        lines.append(f"| `{muscle}` | {len(values)} | {sum(values)/len(values):+.1f} |")

    lines += [
        "",
        "These averages pool every duration and both control and countermeasure arms, so they",
        "are a sanity check and nothing more - a soleus row from day 89 of bed rest and one",
        "from day 5 are in the same column here. The real comparison is the model's job.",
        "",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}: {len(rows)} rows, "
          f"{len(by_study)} studies, {len(cohorts)} cohorts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
