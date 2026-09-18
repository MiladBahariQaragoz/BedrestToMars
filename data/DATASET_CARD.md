# Dataset card — `dataset_v1.0`

**Frozen 2026-09-14** on `feat/integration`, git tag `dataset-v1.0`.

- File: [`dataset_v1.0.csv`](dataset_v1.0.csv)
- SHA-256: `a253cbec6f486ad493210be173d7aea57f96523298f9c7b42dd1a8891c1c02f7` ([`dataset_v1.0.sha256`](dataset_v1.0.sha256))
- Rebuild: `python framework/build_dataset.py` reproduces the file byte for byte from the three
  tables in `data/raw/`. It refuses to overwrite it if either the file or the tables have changed.

## What it is

Muscle size before and after unloading in healthy adults, extracted from published bed-rest,
head-down-tilt, limb-suspension, dry-immersion and spaceflight studies. One row is one study ×
arm × muscle × measurement occasion, compared with that arm's own baseline
([`schema.md`](schema.md) §1). The target is `pct_change`, negative for loss.

The file is the three extraction tables stacked, with a `source_table` column in front (`main`,
`partial`, `figures`) and the 61 schema columns after it, in schema order. Ten rows are left
out because each is a second copy of an observation another row already carries
([`reconciliation_log.md`](reconciliation_log.md)). Nothing else is filtered. Spaceflight, dry
immersion, recovery, DXA, partial and figure-derived rows are all in, each marked by its own
column, so the modelling subset is chosen in the framework's config rather than built into
the file.

## Contents

| | |
|---|---|
| Rows | 737 — 693 from the main table, 25 partial, 19 read from figures |
| Studies | 51, published 1992–2026 |
| Independent cohorts (campaigns) | 35 — this, not the row count, is the sample size for validation |
| Distinct muscles or muscle groups | 51; 271 rows are composites such as `quadriceps` |
| Exposure | 722 analogue (563 head-down tilt, 154 horizontal bed rest, 5 limb suspension), 1 dry immersion, 14 spaceflight |
| Unloading duration | 5 to 119 days of bed rest; about 180 days of spaceflight |
| Phase | 474 during unloading, 263 in recovery |
| Arms | 465 control, 272 countermeasure |
| Modality | 655 MRI, 32 DXA, 30 CT, 20 ultrasound |
| Outcome | 594 volume, 100 CSA, 32 lean mass, 11 thickness |
| Where in the paper | 637 table, 81 text, 19 figure |
| Extraction confidence | 669 high, 49 medium, 19 low |
| Participants | 687 rows healthy young, 42 healthy older, 8 middle-aged astronauts; 567 rows men only, 37 women only, 111 mixed |

The unloading-phase rows alone — the core of a duration–response model — are 474 rows from 31
cohorts across 13 durations, well above the minimum set in `PLAN.md` §6 (60 rows, 8 cohorts,
4 muscles, 4 durations).

## Where it came from

- **572 rows from the systematic search** of PubMed, Scopus, Web of Science and NASA NTRS,
  limited to 2013 onwards ([`search_log.md`](../docs/literature-review/search_log.md),
  [`prisma_counts.md`](../docs/literature-review/prisma_counts.md)).
- **165 rows from the pre-search corpus**: nine papers held in `resources/` before the search,
  and the only source of pre-2013 data ([`screening_decisions.md`](../docs/screening_decisions.md)).

Every row names its DOI, source file and page, table or figure (`source_file`, `page_ref`).
The extraction code is in `framework/extractors/`, the campaign map in
[`cohorts.csv`](cohorts.csv), and each table passes `framework/validate_extraction.py`.

## Quality, stated plainly

- **No row has been double-extracted by a second person**; `double_extracted` is `FALSE`
  throughout.
- The 572 search rows were checked against the original papers on 2026-09-04 in an AI-assisted
  independent source verification: 556 of the 580 rows then present agreed, and no numeric
  conflict is left unresolved. The 165 corpus rows were added afterwards and have not yet been
  checked by anyone else.
- 19 rows are read off figures and carry `low` confidence. 25 partial rows lack a group size or
  a dispersion.
- `pct_change` is the paper's printed mean of the individual changes where it differs from the
  recomputation from group means by more than rounding (`pct_of_individual_means`), and the
  recomputation otherwise (`pct_recomputed_from_group_means`). They are different estimators,
  and every row says which it holds.
- 507 rows do not say which leg was imaged (`laterality_unstated`).

## Known limitations

1. **Small and clustered.** 35 cohorts, 15 of them contributing five rows or fewer, while one
   campaign — the 90-day LTBR study at MEDES, `medes_ltbr90` — supplies 299 rows (41%).
   Validate leave-one-cohort-out and weight by cohort, not by row.
2. **Search limits.** The search starts in 2013; older work enters only through a convenience
   corpus of nine papers. Embase was not searched. 19 included studies publish their muscle
   results only as charts with no baseline and are not extracted.
3. **Mixed measurements in one target column.** MRI volume, CT CSA, DXA lean mass and
   ultrasound thickness do not measure the same thing, and the site along a muscle matters.
   `modality`, `outcome_type` and `measurement_site` must enter the model or stratify it.
4. **Composite and component rows coexist.** `quadriceps` is not the sum of its heads; a model
   given both is fitting the same tissue twice (schema rule 4).
5. **Not all rows are lower limb.** 105 rows are trunk or hip-flexor muscles (multifidus,
   erector spinae, quadratus lumborum, psoas, iliopsoas) and belong out of a lower-limb model.
6. **Recovery rows answer a different question.** The 263 of them must never enter a
   duration–response fit without a flag (schema rule 7).
7. **Spaceflight is not yet usable as lower-limb validation.** Of the 14 spaceflight rows, 8 are
   lumbar multifidus; only one study (`bocker2026`) measures the calf.
8. **Bed rest is an analogue, not microgravity**, and anything beyond 119 days is
   extrapolation.
9. **Mostly young men.** 42 rows come from older adults and 37 from women-only groups.

## Columns

`source_table`, then the 61 columns of [`schema.md`](schema.md) §2 in that order.
`muscle_function_class` is still empty: deriving it is `PLAN.md` task 2.7.

## Changing it

v1.0 is frozen. A correction, a new study or a new flag goes into the extraction tables and
`reconciliation_log.md`, and is released by raising `VERSION` in `framework/build_dataset.py`
to 1.1 and tagging `dataset-v1.1`. The build will not overwrite v1.0.

## How to cite

Until a DOI is minted (`PLAN.md` task 6.10): *From Bed Rest to Mars dataset, v1.0 (2026), git
tag `dataset-v1.0`, https://github.com/MiladBahariQaragoz/BedrestToMars.* For any single value,
cite the source paper as well; every row names its DOI.
