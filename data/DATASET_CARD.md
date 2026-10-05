# Dataset card — `dataset_v1.1`

**Frozen 2026-09-19** on `feat/nasa-integration`, git tag `dataset-v1.1`.

- File: [`dataset_v1.1.csv`](dataset_v1.1.csv)
- SHA-256: `dd214c6aa33dee7ab62358bc56c1e6a72eb330085484022ba1ee2bad394395b9` ([`dataset_v1.1.sha256`](dataset_v1.1.sha256))
- Rebuild: `python framework/build_dataset.py` reproduces the file byte for byte from the four
  tables in `data/raw/`. It refuses to overwrite it if either the file or the tables have changed.
- Previous release: `dataset_v1.0.csv` (2026-09-14, tag `dataset-v1.0`) is still in the
  repository and still rebuilds from its own three tables. It was not edited.

## What changed since v1.0

v1.1 adds five rows and one campaign, taken from NASA's open bed-rest archive rather than from
a paper: the NASA Flight Analog Project's **UTMB Campaign 3**, 90 days of 6° head-down bed
rest, whole-lower-limb lean mass by DXA, 13 participants
(cohort `nasa_utmb_c3`, table [`data/raw/extraction_nasa.csv`](raw/extraction_nasa.csv)).

The archive holds seven campaign folders and six of them are deliberately **not** pooled —
four because their participants are already in the dataset as literature rows, two because
they carry no phase labels and the baseline would have to be guessed. The reasoning for each
is in [`reconciliation_log.md`](reconciliation_log.md) §v1.1 and
[`nasa/CARD.md`](nasa/CARD.md); the code that enforces it is
[`framework/extract_nasa.py`](../framework/extract_nasa.py).

Everything else in this card is v1.0 with the new rows counted in.

## What it is

Muscle size before and after unloading in healthy adults, extracted from published bed-rest,
head-down-tilt, limb-suspension, dry-immersion and spaceflight studies, plus one campaign from
an open data archive. One row is one study × arm × muscle × measurement occasion, compared
with that arm's own baseline ([`schema.md`](schema.md) §1). The target is `pct_change`,
negative for loss.

The file is the four extraction tables stacked, with a `source_table` column in front (`main`,
`partial`, `figures`, `nasa`) and the 61 schema columns after it, in schema order. Ten rows are
left out because each is a second copy of an observation another row already carries
([`reconciliation_log.md`](reconciliation_log.md)). Nothing else is filtered. Spaceflight, dry
immersion, recovery, DXA, partial and figure-derived rows are all in, each marked by its own
column, so the modelling subset is chosen in the framework's config rather than built into
the file.

## Contents

| | |
|---|---|
| Rows | 742 — 693 from the main table, 25 partial, 19 read from figures, 5 from the NASA archive |
| Studies | 52, published 1992–2026 |
| Independent cohorts (campaigns) | 36 — this, not the row count, is the sample size for validation |
| Distinct muscles or muscle groups | 51; 276 rows are composites such as `quadriceps` |
| Exposure | 727 analogue (568 head-down tilt, 154 horizontal bed rest, 5 limb suspension), 1 dry immersion, 14 spaceflight |
| Unloading duration | 5 to 119 days of bed rest; about 180 days of spaceflight |
| Phase | 478 during unloading, 264 in recovery |
| Arms | 470 control, 272 countermeasure |
| Modality | 655 MRI, 37 DXA, 30 CT, 20 ultrasound |
| Outcome | 594 volume, 100 CSA, 37 lean mass, 11 thickness |
| Where the number came from | 637 table, 81 text, 19 figure, 5 open data repository |
| Extraction confidence | 674 high, 49 medium, 19 low |
| Participants | 692 rows healthy young, 42 healthy older, 8 middle-aged astronauts; 567 rows men only, 40 women only, 113 mixed |

The unloading-phase rows alone — the core of a duration–response model — are 478 rows from 32
cohorts across 13 durations, well above the minimum set in `PLAN.md` §6 (60 rows, 8 cohorts,
4 muscles, 4 durations).

## Where it came from

- **572 rows from the systematic search** of PubMed, Scopus, Web of Science and NASA NTRS,
  limited to 2013 onwards ([`search_log.md`](../docs/literature-review/search_log.md),
  [`prisma_counts.md`](../docs/literature-review/prisma_counts.md)).
- **165 rows from the pre-search corpus**: nine papers held in `resources/` before the search,
  and the only source of pre-2013 data ([`screening_decisions.md`](../docs/screening_decisions.md)).
- **5 rows from the NASA Life Sciences Portal**, fetched 2026-09-19 as open US government data
  ([`nasa/CARD.md`](nasa/CARD.md), [`nasa/MANIFEST.json`](nasa/MANIFEST.json)). These are the
  only rows in the file that were computed from individual-participant measurements rather than
  read from a publication.

Every literature row names its DOI, source file and page, table or figure (`source_file`,
`page_ref`); the NASA rows name their folder and the two columns they were computed from. The
extraction code is in `framework/extractors/` and `framework/extract_nasa.py`, the campaign map
in [`cohorts.csv`](cohorts.csv), and each table passes `framework/validate_extraction.py`.

## Quality, stated plainly

- **No row has been double-extracted by a second person**; `double_extracted` is `FALSE`
  throughout.
- The 572 search rows were checked against the original papers on 2026-09-04 in an AI-assisted
  independent source verification: 556 of the 580 rows then present agreed, and no numeric
  conflict is left unresolved. The 165 corpus rows were added afterwards and have not yet been
  checked by anyone else. The 5 NASA rows are computed rather than typed, and reproduce by
  rerunning `framework/extract_nasa.py` against files whose SHA-256 is recorded in
  `nasa/MANIFEST.json`.
- 19 rows are read off figures and carry `low` confidence. 25 partial rows lack a group size or
  a dispersion.
- `pct_change` is the paper's printed mean of the individual changes where it differs from the
  recomputation from group means by more than rounding (`pct_of_individual_means`), and the
  recomputation otherwise (`pct_recomputed_from_group_means`). They are different estimators,
  and every row says which it holds. The NASA rows are means of individual percent changes
  computed from the participants directly, and carry the same flag.
- 547 rows do not say which leg was imaged (`laterality_unstated`).

## Known limitations

1. **Small and clustered.** 36 cohorts, 15 of them contributing five rows or fewer, while one
   campaign — the 90-day LTBR study at MEDES, `medes_ltbr90` — supplies 299 rows (40%).
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
6. **Recovery rows answer a different question.** The 264 of them must never enter a
   duration–response fit without a flag (schema rule 7).
7. **Spaceflight is not yet usable as lower-limb validation.** Of the 14 spaceflight rows, 8 are
   lumbar multifidus; only one study (`bocker2026`) measures the calf.
8. **Bed rest is an analogue, not microgravity**, and anything beyond 119 days is
   extrapolation.
9. **Mostly young men.** 42 rows come from older adults and 40 from women-only groups.
10. **The NASA cohort is four DXA occasions, three of them from one participant.** Only the
    day-63 and the recovery rows rest on all 13 participants; the day-30, day-45 and day-58 rows
    are one woman scanned through her own bed rest, weighted `n_analysed = 1`. The cohort is
    also DXA-only, so it drops out of any analysis restricted to MRI (schema rule 5), and it
    contributes only `whole_lower_limb`, so it is absent from subset B entirely.
11. **`data/nasa/` is larger than what was pooled, on purpose.** Four of its seven folders are
    campaigns already in the dataset (`nasa_sprint_br70`, `wise2005`). Anything that reads
    `data/nasa/` directly must filter on `overlaps_dataset_cohort` in `nasa/MANIFEST.json`, or
    it will count those participants twice.

## Columns

`source_table`, then the 61 columns of [`schema.md`](schema.md) §2 in that order.
`muscle_function_class` is still empty in the file: it is derived at load time from
`muscle_map.csv` (`PLAN.md` task 2.7).

## Changing it

v1.1 is frozen. A correction, a new study or a new flag goes into the extraction tables and
`reconciliation_log.md`, and is released by raising `VERSION` in `framework/build_dataset.py`
to 1.2 and tagging `dataset-v1.2`. The build will not overwrite v1.1, and
`framework/config.yaml` names the version every result was fitted against.

## How to cite

Until a DOI is minted (`PLAN.md` task 6.10): *From Bed Rest to Mars dataset, v1.1 (2026), git
tag `dataset-v1.1`, https://github.com/MiladBahariQaragoz/BedrestToMars.* For any single value,
cite the source paper as well; every literature row names its DOI. For the `nasa_utmb_c3` rows,
cite the NASA Life Sciences Data Archive / NLSP and the principal investigators named on the
experiment page for `4469ebdc-0a65-55e8-bbff-3cf6b044c4c6`.
