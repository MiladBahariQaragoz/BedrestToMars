# Extraction Progress

Generated 2026-09-14 from `data/raw/extraction_qaragoz.csv`.

- **575 rows** across **32 studies** and **24 cohorts**
- **318** rows measured during unloading, 257 during recovery
- **48 distinct muscles**
- Every row is `double_extracted = FALSE`: 0 have been checked by a second person

## By study

| Study | Cohort | Design | Days | n rows | Muscles | Arms |
|---|---|---|---|---|---|---|
| `belavy2017` | `medes_ltbr90` | HDBR_-6 | 90 | 288 | 24 | 2 |
| `demartino2022` | `agbresa` | HDBR_-6 | 60 | 72 | 4 | 2 |
| `liphardt2020` | `liphardt_br21` | HDBR_-6 | 21 | 20 | 4 | 1 |
| `zange2009` | `wbv_hdt14` | HDBR_-6 | 14 | 20 | 10 | 2 |
| `rogers2025` | `wise2005` | HDBR_-6 | 60 | 17 | 17 | 1 |
| `smeuninx2021` | `birmingham_br5_nct04422665` | horizontal_BR | 5 | 16 | 2 | 2 |
| `mandic2026` | `brace_br60` | HDBR_-6 | 60 | 15 | 3 | 3 |
| `bocker2026` | `space_vs_br_2026` | spaceflight | 180 | 12 | 1 | 1 |
| `hansen2024` | `copenhagen_br5` | horizontal_BR | 5 | 12 | 3 | 4 |
| `tran2021` | `agbresa` | HDBR_-6 | 60 | 9 | 3 | 3 |
| `trappe2024sprint` | `nasa_sprint_br70` | HDBR_-6 | 70 | 9 | 3 | 3 |
| `leblanc1992` | `nasa_br17wk` | horizontal_BR | 119 | 9 | 6 | 1 |
| `smeuninx2025` | `birmingham_br5_nct04422665` | horizontal_BR | 5 | 8 | 1 | 2 |
| `trappe2023` | `wise2005` | HDBR_-6 | 60 | 8 | 2 | 2 |
| `mulder2015` | `dlr_hdt5_crossover` | HDBR_-6 | 5 | 6 | 2 | 3 |
| `demartino2021` | `agbresa` | HDBR_-6 | 60 | 6 | 2 | 3 |
| `berg2007` | `valdoltra_br35` | horizontal_BR | 35 | 6 | 3 | 1 |
| `fuchs2025` | `maastricht_br14` | horizontal_BR | 14 | 5 | 4 | 1 |
| `franchi2022` | `izola_br10` | horizontal_BR | 10 | 5 | 5 | 1 |
| `simunic2026` | `izola_br10` | horizontal_BR | 10 | 4 | 4 | 1 |
| `mcdonnell2019` | `lunhab_br10` | horizontal_BR | 10 | 4 | 2 | 2 |
| `hides2021` | `iss_hides_astronauts` | spaceflight | 180 | 4 | 1 | 1 |
| `arbeille2024` | `brace_br60` | HDBR_-6 | 60 | 3 | 1 | 3 |
| `greenleaf1994` | `nasa_ames_hdbr30` | HDBR_-6 | 30 | 3 | 1 | 3 |
| `kramer2017` | `dlr_rsl_br60` | HDBR_-6 | 60 | 2 | 1 | 2 |
| `hajjboutros2023` | `mcgill_hdbr14` | HDBR_-6 | 14 | 2 | 1 | 2 |
| `lagace2026` | `mcgill_hdbr14` | HDBR_-6 | 14 | 2 | 1 | 2 |
| `fuchs2025bfr` | `maastricht_br14` | horizontal_BR | 14 | 2 | 1 | 2 |
| `orlova2026` | `imbp_br21` | HDBR_-6 | 21 | 2 | 2 | 1 |
| `pisot2016` | `izola_br14` | horizontal_BR | 14 | 2 | 1 | 2 |
| `dirks2016` | `maastricht_br7` | horizontal_BR | 7 | 1 | 1 | 1 |
| `ulls2022` | `padova_ulls10` | ULLS | 10 | 1 | 1 | 1 |

## Cohorts carrying more than one study

These are the reason validation is grouped by cohort rather than by paper.

- **`agbresa`** — demartino2021, demartino2022, tran2021
- **`birmingham_br5_nct04422665`** — smeuninx2021, smeuninx2025
- **`brace_br60`** — arbeille2024, mandic2026
- **`izola_br10`** — franchi2022, simunic2026
- **`maastricht_br14`** — fuchs2025, fuchs2025bfr
- **`mcgill_hdbr14`** — hajjboutros2023, lagace2026
- **`medes_ltbr90`** — belavy2017, trappe2023
- **`wise2005`** — rogers2025, trappe2023

## The duration axis, in unloading rows

| Unloading duration (days) | Rows |
|---|---|
| 5 | 42 |
| 7 | 1 |
| 10 | 14 |
| 14 | 31 |
| 21 | 22 |
| 35 | 3 |
| 60 | 90 |
| 70 | 9 |
| 90 | 100 |
| 119 | 6 |

## How the numbers were measured and where they came from

- **Modality:** MRI 510, DXA 29, CT 20, ultrasound 16
- **Outcome:** volume 460, CSA 75, lean_mass 29, thickness 11
- **Source:** table 523, text 52
- **Confidence:** high 552, medium 20, low 3

## The most and least affected muscles so far

Mean percent change across unloading rows, muscles with at least four rows.

| Muscle | Rows | Mean % change |
|---|---|---|
| `peroneals` | 5 | -17.3 |
| `soleus` | 10 | -15.5 |
| `vastus_medialis` | 5 | -15.1 |
| `triceps_surae` | 13 | -13.6 |
| `semimembranosus` | 6 | -13.4 |
| `flexor_hallucis_longus` | 4 | -13.4 |
| `gastrocnemius_lateralis` | 7 | -12.9 |
| `flexor_digitorum_with_tibialis_posterior` | 4 | -12.6 |
| `gastrocnemius_medialis` | 8 | -12.6 |
| `anterior_tibial_group` | 6 | -12.2 |
| `biceps_femoris_long_head` | 7 | -12.1 |
| `vasti` | 7 | -10.4 |
| `quadratus_femoris` | 4 | -10.0 |
| `quadratus_lumborum` | 6 | -9.6 |
| `sartorius` | 5 | -9.1 |
| `adductor_magnus` | 5 | -9.0 |
| `anterior_thigh_compartment` | 7 | -8.2 |
| `semitendinosus` | 6 | -7.4 |
| `vastus_intermedius` | 8 | -6.6 |
| `whole_calf` | 4 | -6.5 |
| `multifidus` | 13 | -6.2 |
| `posterior_thigh_compartment` | 7 | -6.2 |
| `biceps_femoris_short_head` | 6 | -5.8 |
| `gluteus_maximus` | 7 | -5.7 |
| `adductor_longus` | 5 | -5.0 |
| `gracilis` | 5 | -4.9 |
| `vastus_lateralis` | 18 | -4.7 |
| `whole_thigh` | 13 | -4.7 |
| `rectus_femoris` | 12 | -4.6 |
| `quadriceps` | 33 | -4.3 |
| `whole_lower_limb` | 10 | -4.2 |
| `adductor_brevis` | 4 | -4.1 |
| `iliopsoas` | 4 | -4.0 |
| `popliteus` | 4 | -3.3 |
| `lumbar_erector_spinae` | 14 | -2.3 |
| `obturator_externus` | 4 | +0.5 |
| `psoas` | 10 | +1.9 |
| `obturator_internus` | 4 | +6.2 |

These averages pool every duration and both control and countermeasure arms, so they
are a sanity check and nothing more - a soleus row from day 89 of bed rest and one
from day 5 are in the same column here. The real comparison is the model's job.

## The partial table

`data/raw/extraction_partial.csv` holds **29 rows from 12 studies** recovered from papers that never published a full
set of numbers - usually a headline percentage in an abstract, with the group
size or the baseline value missing. They are kept separate on purpose: every
row carries `partial_record` in `qc_flag` plus a note saying what is absent,
and merging the two files is a modelling decision rather than a default.

| Study | Cohort | Rows | Confidence |
|---|---|---|---|
| `cavanagh2016` | `cavanagh_br84` | 2 | medium 2 |
| `cook2014` | `cook_ulls30` | 4 | medium 4 |
| `debevec2018` | `planhab_br21` | 2 | medium 2 |
| `dirks2019` | `maastricht_br7_feeding` | 2 | medium 2 |
| `drummond2013` | `drummond_br7` | 1 | low 1 |
| `hides2016` | `iss_hides_astronauts` | 4 | low 4 |
| `holt2015` | `wise2005` | 4 | low 4 |
| `holt2016` | `wise2005` | 2 | medium 2 |
| `krainski2014` | `krainski_hdbr35` | 4 | medium 4 |
| `mekjavic2021` | `planhab_br10` | 2 | medium 2 |
| `rejc2018` | `izola_br14` | 1 | low 1 |
| `rittweger2013` | `medes_ltbr90` | 1 | medium 1 |

## The figure table

`data/raw/extraction_figures.csv` holds **14 rows from 5 studies** whose results are published only as charts.

Rendering the figure page turned out to recover two different things, and
`digitizer_tool` records which applies to each row:

- **page text beside the figure** — 11 rows
- **visual reading of rendered figure at 190 dpi** — 2 rows
- **printed change with the baseline read off Figure 3F** — 1 rows

The first kind is exact: the value was printed in the prose beside the chart,
and the figure only told us which page to look at. The second is an estimate
read against the axis. No row here is better than `medium` confidence unless
its value came from the page text.

| Study | Cohort | Rows |
|---|---|---|
| `krainski2014` | `krainski_hdbr35` | 8 |
| `lair2026` | `di5_toulouse` | 1 |
| `mekjavic2021` | `planhab_br10` | 2 |
| `rittweger2013` | `medes_ltbr90` | 1 |
| `tanner2015` | `tanner_br5` | 2 |
