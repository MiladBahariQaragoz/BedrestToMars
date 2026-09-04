# Extraction Schema — v1.0 (frozen)

**Status:** frozen in P0. Changes after this point require both leads to agree and a
`fix:` commit that says what changed and why.
**Supersedes:** the draft table in `PLAN.md` Section 11.
**Template:** [`extraction_template.csv`](extraction_template.csv) — column order matches
this document exactly.

This schema is the contract between the two literature tracks. They run in parallel for a
week without daily contact, so every ambiguity left here becomes a disagreement in P2, and
every disagreement costs an hour.

---

## 1. What one row is

> **One row is one comparison against baseline:**
> one study × one intervention arm × one muscle (or muscle group) × one measurement occasion.

A row therefore always carries *both* the baseline value and the follow-up value, and the
percent change between them. **There are no baseline-only rows.** A 60-day study reporting
six muscles at two in-bed timepoints in two arms contributes 6 × 2 × 2 = 24 rows.

This is the one place where the draft schema in `PLAN.md` was self-contradictory: it asked
for `value_baseline` and `value_followup` on every row *and* for separate baseline rows at
`timepoint_days = 0`. Those rows would have had nothing to compare against and a
`pct_change` of zero, which is not a measurement — it would have silently pulled every
model's fit towards the origin.

**Primary key:** `study_id` + `arm_id` + `muscle` + `phase` + `timepoint_days` + `outcome_type`
+ `modality` + `measurement_site`. No two rows may share all eight.

The last two joined the key when Fuchs 2025 was extracted: it measures the *same* thigh in
the *same* participants at the *same* timepoint by DXA, CT and MRI, and reports a different
number each time. That is the study's whole point - it is the evidence behind the `modality`
sensitivity analysis - so the key has to let one muscle carry one row per measurement method.

`measurement_site` joined for the same reason one paper later: quadriceps CSA measured at
20, 40, 60 and 80% of thigh length gives four different answers in the same leg on the same
day, and the 20% site frequently shows no significant loss while the 60% site does. Collapsing
them would average away the within-muscle heterogeneity that Miokovic's work is about.

**`row_id` is generated, never typed:**
`{study_id}__{arm_id}__{muscle}__{phase}_{timepoint_days}__{modality}_{outcome_type}`
— for example `dulac2024__ex__quadriceps__bed_rest_13__MRI_volume`.

---

## 2. Fields

### 2.1 Identity and provenance of the study

| Field | Type | Required | Notes |
|---|---|---|---|
| `row_id` | string | generated | Never typed by hand. See the formula above |
| `study_id` | string | yes | `{firstauthor}{year}`, lower case, e.g. `belavy2009`, `dulac2024` |
| `cohort_id` | string | yes | **The campaign, not the paper.** All Berlin BedRest papers share one `cohort_id`. This single column is what makes the validation defensible |
| `campaign_name` | string | no | Human-readable: `Berlin BedRest Study (BBR2-2003)`, `WISE-2005`, `AGBRESA` |
| `registry_id` | string | no | `NCT…`, `DRKS…` — the most reliable way to detect that two papers share participants |
| `first_author` | string | yes | Surname only |
| `year` | int | yes | Year of the version being extracted; note preprint/issue mismatches in `notes` |
| `doi` | string | yes | Bare DOI, no `https://doi.org/` prefix |
| `source_file` | string | yes | File name in `resources/`, so any number can be traced back in seconds |

### 2.2 Unloading design

| Field | Type | Required | Notes |
|---|---|---|---|
| `design` | enum | yes | `HDBR_-6`, `HDBR_other`, `horizontal_BR`, `dry_immersion`, `ULLS`, `spaceflight`. **`spaceflight` and `dry_immersion` rows are extracted and kept, and always carry `exposure_flag`** — see below |
| `hdt_angle_deg` | float | no | Negative for head-down. `-6` for standard HDBR, `0` for horizontal bed rest |
| `duration_days` | int | yes | Total planned unloading duration of the campaign |
| `phase` | enum | yes | `bed_rest` or `recovery`. **Never mix the two in one model without a flag** |
| `timepoint_days` | int | yes | Days since the start of unloading. For `recovery` rows this keeps counting |
| `days_from_unloading_end` | int | conditional | Required when `phase = recovery`; `NA` otherwise |
| `exposure_flag` | enum | yes | `analogue` for bed rest and ULLS, `dry_immersion`, or `spaceflight`. One column, so either decision in P2 is one line of code rather than a re-extraction |

Recovery rows are not optional decoration. Dulac 2024 measures at day 13 of bed rest *and*
day 6 of recovery; pooling those two into one "post" value would understate the in-bed loss.

**Why `exposure_flag` exists.** Three exposures are being pooled onto one duration axis and
they are not equivalent. Dry immersion removes support from the soles of the feet as well as
unloading the limb, and it produces in days what bed rest produces in weeks; spaceflight is
the real thing rather than an analogue. Pooled without a marker, the immersion studies pull
down the early part of the duration-response and the model averages away a real difference.
The decision taken in P0 is therefore: **extract everything, flag the exposure, and decide in
P2** whether the flag stays a feature in the design matrix, forces a stratified fit, or
becomes an exclusion. The sensitivity analysis - fit with and without each exposure class -
is a slide either way.

### 2.3 Arm and participants

| Field | Type | Required | Notes |
|---|---|---|---|
| `arm_id` | string | yes | Short and stable within a study: `ctrl`, `ex`, `rve`, `wbv`, `nutr` |
| `arm_type` | enum | yes | `control` or `countermeasure` |
| `cm_modality` | enum | yes | `none`, `resistive`, `flywheel`, `aerobic`, `RVE`, `WBV`, `nutrition`, `artificial_gravity`, `LBNP`, `NMES`, `BFR`, `combined` |
| `cm_dose` | string | no | Free text, but structured: frequency × session length × intensity |
| `n_arm` | int | yes | Participants allocated to this arm |
| `n_analysed` | int | yes | Participants actually contributing *this* measurement. Often smaller. This is the N that any weighting uses |
| `sex` | enum | yes | `M`, `F`, `mixed` |
| `pct_female` | float | conditional | Required when `sex = mixed` |
| `age_mean`, `age_sd` | float | see note | Years |
| `age_min`, `age_max` | float | see note | The inclusion range where the paper gives one |

**Age: a mean or a range, but never nothing - with one exception.** Some papers publish only the inclusion
range - Smeuninx 2021 and 2025 say "10 healthy older men aged 65-80" and never print a
mean. The validator therefore asks for `age_mean` **or** both `age_min` and `age_max`.
Inventing a midpoint would be imputation, and rule 1 forbids it.
The exception is astronaut cohorts: crew demographics are routinely withheld, so a row
carrying `qc_flag = age_not_published` may leave all three age fields `NA`. Filling them
with a plausible range would be inventing data about identifiable people.

| `population` | enum | yes | `healthy_young`, `healthy_middle_aged`, `healthy_older`, `clinical` |
| `bmi_mean` | float | no | kg/m² |
| `body_mass_mean_kg` | float | no | Useful for normalising volumes |
| `nutrition_controlled` | enum | no | `yes`, `no`, `NA` — energy-controlled diets change the answer |

`population` is new, and it earns its column: the corpus is dominated by young men, and
Dulac 2024 (55–65 years) is currently the only older cohort. Without this field that
contrast is invisible to the model and to the discussion.

### 2.4 What was measured

| Field | Type | Required | Notes |
|---|---|---|---|
| `muscle` | vocabulary | yes | Controlled list in §3. Anything not on the list is added to the list first, not invented in a cell |
| `muscle_function_class` | enum | derived | `antigravity_extensor`, `flexor`, `mixed`. Derived in P2 from `muscle`, not typed |
| `is_composite` | bool | yes | `TRUE` for `triceps_surae`, `quadriceps`, `whole_lower_limb` |
| `composite_of` | string | conditional | Semicolon-separated component muscles where the paper says which ones are included |
| `laterality` | enum | when stated | `left`, `right`, `mean`, `dominant`. Many papers never say which leg was imaged; that is `NA` plus `qc_flag = laterality_unstated`, not a guess |
| `measurement_site` | string | no | For CSA especially: `50% femur length`, `mid-belly`, `largest slice`. Two CSAs at different sites are not the same measurement |
| `outcome_type` | enum | yes | `volume`, `CSA`, `lean_mass`, `PCSA`, `thickness` |
| `modality` | enum | yes | `MRI`, `CT`, `DXA`, `ultrasound`, `anthropometry` |

### 2.5 Values

| Field | Type | Required | Notes |
|---|---|---|---|
| `unit_original` | string | yes | Exactly as printed: `cm³`, `mL`, `mm²`, `g`, `%` |
| `value_baseline_original` | float | conditional | As printed, before any conversion |
| `value_followup_original` | float | conditional | As printed |
| `unit_si` | enum | yes | `cm3` for volume, `cm2` for CSA, `kg` for mass, `mm` for thickness, `pct_only` when only a percentage was published |
| `value_baseline` | float | conditional | Converted |
| `value_followup` | float | conditional | Converted |
| `change_absolute` | float | derived | `value_followup − value_baseline` |
| `pct_change` | float | **yes** | **The target variable.** Negative means loss |
| `variance_of` | enum | conditional | `baseline`, `followup`, `change`. Without this the number is unusable |
| `variance_type` | enum | conditional | `SD`, `SE`, `CI95`, `IQR` |
| `variance_value` | float | conditional | For `CI95`, store the half-width and put the bounds in `notes` |
| `p_value` | float | no | As printed; `NA` if only reported as a symbol |

`pct_change` is the only value field that is always required. Some papers publish nothing
but a percentage — that row is still usable for modelling, with `unit_si = pct_only` and
the absolute values left `NA`.

### 2.6 Provenance and quality control

| Field | Type | Required | Notes |
|---|---|---|---|
| `data_source` | enum | yes | `table`, `text`, `figure_digitized`, `supplement`, `author_correspondence` |
| `digitizer_tool` | string | conditional | Required when `data_source = figure_digitized`, e.g. `WebPlotDigitizer 4.7` |
| `page_ref` | string | **yes** | Page plus table or figure number, e.g. `p. 3818, Fig. 2D`. Not optional, ever |
| `extractor` | string | yes | Who typed the row |
| `extraction_date` | date | yes | ISO `YYYY-MM-DD` |
| `extraction_confidence` | enum | yes | `high` (printed table), `medium` (text or clean figure), `low` (dense figure, overlapping error bars) |
| `double_extracted` | bool | yes | `TRUE` once a second person has independently re-extracted the row |
| `qc_flag` | string | no | Short code for anything odd: `unit_ambiguous`, `n_mismatch`, `overlaps_other_paper` |
| `notes` | string | no | Free text. Longer than a sentence means it belongs in `reconciliation_log.md` |

---

## 3. Controlled vocabulary for `muscle`

`soleus`, `gastrocnemius_medialis`, `gastrocnemius_lateralis`, `gastrocnemius_total`,
`triceps_surae`, `tibialis_anterior`, `peroneals`, `deep_posterior_compartment`,
`vastus_lateralis`, `vastus_medialis`, `vastus_intermedius`, `rectus_femoris`,
`quadriceps`, `hamstrings`, `adductors`, `gluteus_maximus`, `gluteus_medius`,
`gluteus_minimus`, `psoas`,
`multifidus`, `whole_thigh`, `whole_calf`, `whole_lower_limb`,
`anterior_thigh_compartment`, `posterior_thigh_compartment`, `flexor_digitorum_longus`,
`tibialis_posterior`, `lumbar_erector_spinae`, `quadratus_lumborum`,
`anterior_tibial_group`, `flexor_digitorum_with_tibialis_posterior`, `flexor_hallucis_longus`, `vasti`, `adductor_brevis`, `adductor_longus`, `adductor_magnus`, `gracilis`, `sartorius`, `biceps_femoris_long_head`, `biceps_femoris_short_head`, `semimembranosus`, `semitendinosus`, `popliteus`, `obturator_externus`, `obturator_internus`, `quadratus_femoris`, `iliopsoas`.

The second block was added when Belavy 2017 was extracted: it reports 24 individually segmented muscles, and collapsing them into groups would throw away exactly the muscle-identity resolution the talk's second claim rests on.

Adding a term is a one-line commit to this file. Inventing one in a cell is not.

---

## 4. Ten rules that prevent most of the pain

1. **Never impute silently.** Missing is `NA`, and `NA` is a fact about the literature worth reporting.
2. **Sign convention:** `pct_change` is negative for atrophy. Fix this once, in P0, or lose an evening in P4 hunting a flipped sign.
3. **Recompute every percentage.** Where baseline and follow-up are both printed, compute `pct_change` yourself and compare against the printed value. A mismatch goes in `qc_flag`, not in the bin.
   **The commonest mismatch is not an error.** A paper's printed percent change is usually the *mean of each participant's own percent change*; recomputing from the group means gives the *percent change of the means*. These are different numbers, and with a small n and a wide spread they differ a lot - in Tran 2021 the gluteus medius control arm is −4.6% printed against −7.1% recomputed. The printed value is the better estimate of the average person's response, so **keep the printed value in `pct_change`, keep the group means in `value_baseline` and `value_followup`, and set `qc_flag = pct_of_individual_means`.** The validator then skips the agreement check for that row, and the limitations section has a sentence it would otherwise have missed.
4. **`triceps_surae` is not the sum of `soleus` and `gastrocnemius`.** Keep composite and component rows separately, flag them with `is_composite`, and decide explicitly in P2 how they are pooled. A model fed both is fitting the same tissue twice.
5. **DXA lean mass is not MRI volume.** Keep `modality` as a feature and run the sensitivity analysis without the DXA rows.
6. **One `cohort_id` per campaign, not per paper.** Two papers from one bed-rest campaign are one cohort. This is what makes Leave-One-Cohort-Out honest.
7. **Baseline and recovery are different questions.** Never let a `recovery` row into a duration–response model without an explicit flag in the design matrix.
8. **`n_analysed`, not `n_arm`, is the weight.** Dropouts are the norm in bed-rest campaigns, not the exception.
9. **Every row is traceable in under a minute** via `source_file` + `page_ref`. A row that cannot be traced is deleted, not defended.
10. **Digitised figures are labelled as such.** They are usable; they are not the same evidence as a printed table, and the sensitivity analysis excluding them is a slide, not an embarrassment.

---

## 5. Worked example

Dulac et al. 2024 reports upper quadriceps volume by MRI in two arms, at day 13 of bed rest
and day 6 of recovery, with the values presented in a figure rather than a table. Four of
the resulting rows, abbreviated to the fields that carry the argument:

| study_id | cohort_id | arm_id | muscle | phase | timepoint_days | n_analysed | pct_change | data_source | extraction_confidence |
|---|---|---|---|---|---|---|---|---|---|
| `dulac2024` | `mcgill_hdbr14` | `ctrl` | `quadriceps` | `bed_rest` | 13 | 11 | *from Fig. 2D* | `figure_digitized` | `medium` |
| `dulac2024` | `mcgill_hdbr14` | `ex` | `quadriceps` | `bed_rest` | 13 | 11 | *from Fig. 2D* | `figure_digitized` | `medium` |
| `dulac2024` | `mcgill_hdbr14` | `ctrl` | `quadriceps` | `recovery` | 20 | 9 | *from Fig. 2D* | `figure_digitized` | `medium` |
| `dulac2024` | `mcgill_hdbr14` | `ex` | `quadriceps` | `recovery` | 20 | 11 | *from Fig. 2D* | `figure_digitized` | `medium` |

Three things this example is meant to teach:

- `n_analysed` drops from 11 to 9 in the control arm at recovery, because two participants
  were withdrawn on day 3 of recovery. `n_arm` would have hidden that.
- The recovery rows carry `timepoint_days = 20` (14 days of bed rest + 6 of recovery) and
  `days_from_unloading_end = 6`. They are not "post" values.
- Every one of these rows is `figure_digitized`. That is a fact about the paper, and the
  right response is to record it and, if the values matter, write to the authors.

---

## 6. Double extraction

Full double extraction is not affordable in one week. The compromise:

- **Every row from a `figure_digitized` source is double-extracted.** Digitisation error is
  the largest avoidable error in this dataset.
- **A random 20% of table-sourced rows is double-extracted** as a quality estimate.
- Disagreements are resolved in P2 and logged in `data/reconciliation_log.md` — never
  overwritten in place. The disagreement rate is a number for the limitations section.

---

## 7. Validation checks

Run `python framework/validate_extraction.py data/raw/<file>.csv` before every commit of an
extraction table. The checks are the schema in executable form:

1. Every required column is present, in this document's order.
2. No duplicate primary key (`study_id` + `arm_id` + `muscle` + `phase` + `timepoint_days`).
3. `row_id` matches the generated formula.
4. Every enum cell is a member of its vocabulary.
5. `pct_change` is present and within a sane range (−80 to +40).
6. Where baseline and follow-up are both present, the recomputed percentage agrees with
   `pct_change` to within 0.5 percentage points.
7. `days_from_unloading_end` is present exactly when `phase = recovery`.
8. `pct_female` is present exactly when `sex = mixed`.
9. `digitizer_tool` is present exactly when `data_source = figure_digitized`.
10. `n_analysed` ≤ `n_arm`.
11. `page_ref` is non-empty on every row.
12. Every `cohort_id` appears in `data/cohorts.csv`.

---

## 8. What changed from the draft in `PLAN.md` Section 11

| Change | Why |
|---|---|
| Removed baseline-only rows; one row is now a baseline↔follow-up contrast | The draft asked for both and they contradicted each other |
| Added `phase` and `days_from_unloading_end` | Recovery measurements exist in the corpus and are a different question |
| Added `n_analysed` beside `n_arm` | Dropouts are routine; the analysed N is what any weighting needs |
| Added `population`, `age_min`, `age_max` | The corpus is young men plus one older cohort; the model cannot see that otherwise |
| Split variance into `variance_of` + type + value | An SD with no stated referent cannot be used |
| Added `unit_original` / `unit_si` pairs | Unit conversion errors are silent and fatal |
| Added `is_composite`, `composite_of`, `laterality`, `measurement_site` | Prevents double-counting the same tissue and comparing CSAs measured at different sites |
| Added `registry_id`, `campaign_name` | The cheapest reliable way to detect shared participants |
| Added `extraction_confidence`, `double_extracted`, `digitizer_tool`, `source_file` | Makes the quality of each row a column instead of a memory |
