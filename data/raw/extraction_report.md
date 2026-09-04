# Extraction Progress

Generated 2026-09-04 from `data/raw/extraction_falk.csv`.

- **507 rows** across **24 studies** and **16 cohorts**
- **263** rows measured during unloading, 244 during recovery
- **43 distinct muscles**
- Every row is `double_extracted = FALSE`: 0 have been checked by a second person

## By study

| Study | Cohort | Design | Days | n rows | Muscles | Arms |
|---|---|---|---|---|---|---|
| `belavy2017` | `medes_ltbr90` | HDBR_-6 | 90 | 288 | 24 | 2 |
| `demartino2022` | `agbresa` | HDBR_-6 | 60 | 72 | 4 | 2 |
| `rogers2025` | `medes_women_br60` | HDBR_-6 | 60 | 17 | 17 | 1 |
| `smeuninx2021` | `birmingham_br5_nct04422665` | horizontal_BR | 5 | 16 | 2 | 2 |
| `mandic2026` | `brace_br60` | HDBR_-6 | 60 | 15 | 3 | 3 |
| `bocker2026` | `space_vs_br_2026` | spaceflight | 180 | 12 | 1 | 1 |
| `hansen2024` | `copenhagen_br5` | horizontal_BR | 5 | 12 | 3 | 4 |
| `tran2021` | `agbresa` | HDBR_-6 | 60 | 9 | 3 | 3 |
| `trappe2024sprint` | `nasa_sprint_br70` | HDBR_-6 | 70 | 9 | 3 | 3 |
| `smeuninx2025` | `birmingham_br5_nct04422665` | horizontal_BR | 5 | 8 | 1 | 2 |
| `trappe2023` | `medes_women_br60` | HDBR_-6 | 60 | 8 | 2 | 2 |
| `mulder2015` | `dlr_hdt5_crossover` | HDBR_-6 | 5 | 6 | 2 | 3 |
| `demartino2021` | `agbresa` | HDBR_-6 | 60 | 6 | 2 | 3 |
| `fuchs2025` | `maastricht_br14` | horizontal_BR | 14 | 5 | 4 | 1 |
| `franchi2022` | `izola_br10` | horizontal_BR | 10 | 5 | 5 | 1 |
| `simunic2026` | `izola_br10` | horizontal_BR | 10 | 4 | 4 | 1 |
| `arbeille2024` | `brace_br60` | HDBR_-6 | 60 | 3 | 1 | 3 |
| `kramer2017` | `dlr_rsl_br60` | HDBR_-6 | 60 | 2 | 1 | 2 |
| `hajjboutros2023` | `mcgill_hdbr14` | HDBR_-6 | 14 | 2 | 1 | 2 |
| `lagace2026` | `mcgill_hdbr14` | HDBR_-6 | 14 | 2 | 1 | 2 |
| `fuchs2025bfr` | `maastricht_br14` | horizontal_BR | 14 | 2 | 1 | 2 |
| `orlova2026` | `imbp_br21` | HDBR_-6 | 21 | 2 | 2 | 1 |
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
- **`medes_women_br60`** — rogers2025, trappe2023

## The duration axis, in unloading rows

| Unloading duration (days) | Rows |
|---|---|
| 5 | 42 |
| 7 | 1 |
| 10 | 10 |
| 14 | 9 |
| 21 | 2 |
| 60 | 90 |
| 70 | 9 |
| 90 | 100 |

## How the numbers were measured and where they came from

- **Modality:** MRI 462, DXA 19, CT 14, ultrasound 12
- **Outcome:** volume 432, CSA 45, lean_mass 19, thickness 11
- **Source:** table 470, text 37
- **Confidence:** high 497, medium 7, low 3

## The most and least affected muscles so far

Mean percent change across unloading rows, muscles with at least four rows.

| Muscle | Rows | Mean % change |
|---|---|---|
| `soleus` | 8 | -18.0 |
| `peroneals` | 5 | -17.3 |
| `gastrocnemius_lateralis` | 5 | -15.8 |
| `gastrocnemius_medialis` | 6 | -14.5 |
| `triceps_surae` | 10 | -13.5 |
| `semimembranosus` | 6 | -13.4 |
| `flexor_hallucis_longus` | 4 | -13.4 |
| `flexor_digitorum_with_tibialis_posterior` | 4 | -12.6 |
| `biceps_femoris_long_head` | 7 | -12.1 |
| `vasti` | 5 | -11.9 |
| `anterior_tibial_group` | 5 | -10.4 |
| `quadratus_femoris` | 4 | -10.0 |
| `quadratus_lumborum` | 6 | -9.6 |
| `sartorius` | 5 | -9.1 |
| `adductor_magnus` | 5 | -9.0 |
| `anterior_thigh_compartment` | 7 | -8.2 |
| `semitendinosus` | 6 | -7.4 |
| `posterior_thigh_compartment` | 7 | -6.3 |
| `multifidus` | 13 | -6.2 |
| `biceps_femoris_short_head` | 6 | -5.8 |
| `gluteus_maximus` | 7 | -5.7 |
| `adductor_longus` | 5 | -5.0 |
| `gracilis` | 5 | -4.9 |
| `rectus_femoris` | 5 | -4.9 |
| `whole_thigh` | 10 | -4.2 |
| `adductor_brevis` | 4 | -4.1 |
| `iliopsoas` | 4 | -4.0 |
| `quadriceps` | 28 | -3.8 |
| `whole_lower_limb` | 9 | -3.4 |
| `popliteus` | 4 | -3.3 |
| `vastus_lateralis` | 13 | -2.1 |
| `lumbar_erector_spinae` | 13 | -1.7 |
| `obturator_externus` | 4 | +0.5 |
| `psoas` | 10 | +1.9 |
| `obturator_internus` | 4 | +6.2 |

These averages pool every duration and both control and countermeasure arms, so they
are a sanity check and nothing more - a soleus row from day 89 of bed rest and one
from day 5 are in the same column here. The real comparison is the model's job.
