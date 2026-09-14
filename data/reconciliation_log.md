# Reconciliation Log

P2 tasks 2.1 and 2.2 (`PLAN.md` §6): every disagreement found when the extraction was
checked against the original papers, and what was done about it. Decisions dated 2026-09-14.

## The check

On 2026-09-04 the partner re-extracted every provenance record from the original papers,
with AI assistance, and compared the result with `data/raw/extraction_qaragoz.csv`,
`extraction_partial.csv` and `extraction_figures.csv`. The work was staged: three studies
(26 rows) to test the method, then 113 rows (all 14 figure-derived rows and 99 table-derived
rows), then all 580.

| Measure | Result |
|---|---|
| Provenance records checked | 580 — 537 main, 29 partial, 14 figures |
| Recovered from the source | 580 — 575 high confidence, 5 medium |
| Agree without correction | 556 |
| Flagged | 24 rows, plus 3 duplicated observations |
| Unresolved numeric conflicts | 0 |
| Percent-change gap, median / mean / max | 0 / 0.012 / 1.04 percentage points |

**How to describe it.** This is AI-assisted independent source verification. It is not a
human double extraction, and because the assistant had seen a few rows earlier it is not
fully blinded either. `double_extracted` therefore stays `FALSE` on every row: the schema
reserves `TRUE` for a row that a second person has re-extracted. The methods section and the
Q&A use the wording in this paragraph.

The partner's full comparison, row-level patch and validation notes are kept in the shared
Drive folder, not in this repository.

## Resolutions

### Modality — 8 rows corrected

Hides 2016 (four partial rows) and Hides 2021 (four main rows) were coded as MRI. Both papers
measure lumbar multifidus by ultrasound. `modality` is now `ultrasound`, which also changes
the `row_id` of all eight, because modality is part of the key.

### Printed against recomputed percent change — 16 rows reviewed, 5 changed

Schema §4 rule 3 keeps a paper's own printed percent change when it disagrees with the one
recomputed from the group means, because the printed figure is usually the mean of the
individual changes. In all 16 rows below the paper prints a whole-number percentage, and a
whole number only disagrees with a recomputed value once the gap is larger than its own
rounding. The rule is therefore applied where the gap exceeds 0.5 percentage points. Below
that, the recomputed value is kept as the more precise of the two, and the printed figure is
recorded in `notes`.

| Row | Recomputed | Printed | Gap | Kept |
|---|---|---|---|---|
| `trappe2024sprint`, BRE+T arm, triceps surae | −7.04 | −6 | 1.04 | printed |
| `trappe2024sprint`, BRE+T arm, soleus | −8.93 | −8 | 0.93 | printed |
| `fuchs2025`, posterior thigh, MRI | −4.7 | −4 | 0.65 | printed |
| `fuchs2025`, whole thigh, MRI | −5.6 | −5 | 0.63 | printed |
| `kramer2017`, jump arm, leg lean mass | −0.52 | 0 | 0.52 | printed |
| `trappe2024sprint`, BR arm, triceps surae | −23.47 | −23 | 0.47 | recomputed |
| `trappe2024sprint`, BR arm, quadriceps | −9.38 | −9 | 0.38 | recomputed |
| `trappe2024sprint`, BRE arm, quadriceps | +2.65 | +3 | 0.35 | recomputed |
| `trappe2024sprint`, BRE arm, triceps surae | −7.31 | −7 | 0.31 | recomputed |
| `trappe2024sprint`, BRE+T arm, quadriceps | +4.20 | +4 | 0.20 | recomputed |
| `fuchs2025`, whole thigh, CT | −5.8 | −6 | 0.19 | recomputed |
| `fuchs2025`, anterior thigh, MRI | −7.1 | −7 | 0.14 | recomputed |
| `trappe2024sprint`, BR arm, soleus | −23.87 | −24 | 0.13 | recomputed |
| `trappe2024sprint`, BRE arm, soleus | −9.13 | −9 | 0.13 | recomputed |
| `kramer2017`, control arm, leg lean mass | −5.10 | −5 | 0.10 | recomputed |
| `fuchs2025`, whole lower limb, DXA | −4.9 | −5 | 0.10 | recomputed |

Gaps are measured against the unrounded recomputation. The printed values were re-read from
Table 1 of Trappe 2024 and Kramer 2017 before they were entered.

The one item the partner left for review, the Hides 2016 row at L5, is rounding of a
single-astronaut value — the paper says "29 %" and its printed endpoints give −29.1 % — so
−29.1 stays.

### Duplicated observations — 4 partial rows flagged

Krainski 2014's abstract percentages sit in the partial table, and the same percentages, with
baselines, sit in the figure table, read from Figure 4. Three pairs share a `row_id`. The
fourth pair was found while resolving the first three: the exercise arm's "calf" row in the
partial table is the row Figure 4 labels triceps surae, −14 % in both. All four partial rows
now carry `duplicate_of_figure_row`. They stay as provenance, and they are dropped when the
tables are merged for modelling, so the merged table holds 576 observations rather than 580.

### Cohort map — two corrections

- **Five `cohorts.csv` rows repaired.** Site names containing a comma had not been quoted, so
  `lunhab_br10`, `izola_br14`, `planhab_br10`, `planhab_br21` and `krainski_hdbr35` parsed
  into ten fields, with everything after the site shifted one column. The validator reads
  only `cohort_id`, which is why it did not catch this.
- **`medes_women_br60` merged into `wise2005`.** Raised by the partner's source audit
  (2026-09-05) and confirmed in the paper: Rogers 2025 thanks MEDES for conducting the WISE
  bedrest investigation. Rogers 2025, the women in Trappe 2023 and the two Holt papers are
  therefore one campaign. Under two identifiers the same women would have sat on both sides
  of a leave-one-cohort-out split. Distinct cohorts across the three tables fall from 30 to 29.

### Report counts — now derived from the data

`docs/data_report.html` said 248 recovery rows and ten spaceflight rows; counted across all
three tables there are 252 and 14. Every count quoted in the report's prose is now filled
from the rows by `framework/build_data_report.py`, so the text cannot fall behind again.

### Study count — corrected

`docs/literature-review/prisma_counts.md` and the run log in `docs/literature-review/PLAN.md`
said 27 extracted studies. The main table holds 28.
