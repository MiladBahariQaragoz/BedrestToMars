# Card — NASA NLSP open bed-rest data, `data/nasa/`

Fetched 2026-09-19 from the NASA Life Sciences Portal by `framework/fetch_nasa_nlsp.py`
(commit adds both). Every file's UUID and SHA-256 is in [`MANIFEST.json`](MANIFEST.json).

**One of the seven folders below is now part of `dataset_v1.1.csv`; the other six are a
companion set.** On 2026-09-19 the v1.1 process (`data/DATASET_CARD.md` §"Changing it")
took the three blocks of `MR035G_Campaign_3_DXA_Whole_Body` whose own scan dates confirm a
90-day bed rest, aggregated them to five cohort-level rows, and froze them as cohort
`nasa_utmb_c3` — see `framework/extract_nasa.py` and `data/reconciliation_log.md` §v1.1.
`dataset_v1.0.csv` is untouched and still rebuilds from its own three tables.

Nothing else here may be pooled without going through that same process, and for four of
the folders below pooling is not an upgrade but a double count (§"The rule").

## What it is

Derived, individual-participant CSVs from NASA flight-analog bed-rest campaigns,
published on [nlsp.nasa.gov](https://nlsp.nasa.gov/explore) as open downloads — no
account, no request form, no license click-through. US government open data. For any
analysis, cite the NASA Life Sciences Data Archive / NLSP and the principal
investigators named on the experiment pages.

| Folder | Campaign | Contains | Relationship to `dataset_v1.0` |
|---|---|---|---|
| `BEDREST_IRATS_MRI_ULTRASOUND_CFT70/` | UTMB Campaign 11 (CFT70), 70-day 6° HDBR, 2011–14 | Per-subject MRI volumes (27 subject ids: soleus, gastrocnemius med/lat, quadriceps, rectus femoris, vasti, adductors, hamstrings) and ultrasound thickness, bed rest + recovery | **Same campaign as cohort `nasa_sprint_br70`** (trappe2024sprint) |
| `BEDREST_IRATS_iDXA_CFT70/` | Campaign 11 | Per-subject iDXA incl. demographics tables (group-level summaries) | Same campaign as `nasa_sprint_br70` |
| `BRSMIDXA_CFT70_iDXA/` | Campaign 11 | Per-subject iDXA standard measures | Same campaign as `nasa_sprint_br70` |
| `MR035G_Campaign_1_DXA/` | UTMB Campaign 1, 60-day | Whole-body DXA incl. leg lean. Only 3 subject ids are visible in the 13 files — needs a close read before use | **New campaign — no cohort in v1.0** |
| `MR035G_Campaign_3_DXA_Whole_Body/` (+`_ReadMe/`) | UTMB Campaign 3, 60/90-day | Whole-body DXA incl. `L/R_LEG_LEAN` (118 of 183 files carry the leg-lean columns; 32 subject ids; phases C3A…H) | **Pooled into v1.1** as cohort `nasa_utmb_c3` — blocks C3A, C3C and C3D only (90 days, 13 participants). The other five blocks are shorter, or have no dated pre/post pair, and are left out |
| `MR035G_AG_PILOT_DXA_ANALYZED/` | Artificial-Gravity Pilot (UTMB, 2006) | Whole-body DXA, 16 subject ids | **New campaign — distinct from `agbresa` (2019)** |
| `MR035G_MEDES_DXA/` | MEDES/WISE 2005, 60-day, 24 women | Whole-body DXA — 24 subject ids, exactly the published WISE cohort | **Same campaign as cohort `wise2005`** |

Verified on download (2026-09-19): the soleus file carries per-subject volumes declining
through bed rest as expected, and campaign-3 files carry real `L/R_LEG_LEAN` trajectories
(e.g. subject 224: 10,630 g pre-test → 9,952 g at bed-rest day 64). Subject-id counts above
are counts of distinct ids seen in the files, not verified enrolments.

Deliberately **not** fetched, with reasons:

- `MR035G_*` heel / forearm / hip / femur / spine — bone only; this project models muscle
  size.
- iRAT `SUPINE_CYCLE` / `POWER_CYCLE` — exercise-performance summaries, not outcomes.
- `MR035G_AG_PILOT_DXA_SCREEN` — pre-study screening scans, not bed-rest outcomes.
- MR079G isokinetic strength, Functional Task Test, vertical jump — strength and function,
  not muscle size; candidates if the target ever extends.
- :envihab campaigns (AGBRESA, VaPER, SANS_CM) — catalog metadata only in NLSP; their data
  requires a [data request](https://nlsp.nasa.gov/data-request).

## The rule — read before any analysis touches this directory

1. **Never pool a NASA folder with the literature rows of the same campaign.** CFT70 is
   `nasa_sprint_br70`; MEDES/WISE is `wise2005`. The manifest carries the flag
   (`overlaps_dataset_cohort`) on every file, so the filter can be mechanical:
   `MANIFEST.json` is the single source of truth for what overlaps what.
2. **Counting campaigns, not files:** adding the three new campaigns takes the modelling
   subset from 31 to 34 independent cohorts and the full dataset from 35 to 38. The
   hundreds of individual rows inside each folder are measurements within one campaign —
   they are not independent data points, and any validation that treats them as such
   repeats the error the leave-one-cohort-out design exists to prevent.
3. **No new durations.** The additions are 60-, 70- and 90-day campaigns — durations
   v1.0 already holds. What this buys is replication strength and individual-level
   resolution, not coverage; the 119-day ceiling stands.
4. **Within CFT70, arms share participants.** The iRAT arms, the SPRINT arms and the
   testosterone experiment (`NNX10AP86G`) are one campaign with several arms — the check
   `cohorts.csv` already flags ("trappe2024sprint … check whether they share participants")
   is answered *yes* by the NLSP campaign structure.
5. **The intended use is external validation, not training:** fit on the literature data,
   check against NASA's raw participants — an upgrade of two existing cohorts to
   individual level and a held-out test the literature never saw.

## Reproduce

```bash
python framework/fetch_nasa_nlsp.py     # idempotent; re-hashes existing files
```

The script records source API, access date, per-file UUID, size and SHA-256 in
`MANIFEST.json`. If NLSP revises a file, its hash changes and the manifest names it.

Reading note: the CSVs carry a UTF-8 BOM, so open them with `encoding="utf-8-sig"`
(`pd.read_csv(..., encoding="utf-8-sig")`) or the first column name arrives with three
invisible characters attached.
