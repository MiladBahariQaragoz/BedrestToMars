# Screening Report — stage 1 triage

Produced by `framework/triage_screening.py` on 2026-09-04, applying the eligibility
criteria in `docs/literature-review/PLAN.md` §2. No record is auto-*included*: the
script only rules records out, and only on high-confidence signals.

## Triage outcome

| Bucket | Records | Meaning |
|---|---|---|
| `priority` | 183 | Core unloading model, a muscle outcome and a lower-limb term. Read these first |
| `maybe` | 979 | Passed the exclusions but is missing one signal. Read after the priority set |
| `campaign_lead` | 481 | A real unloading campaign reporting something other than muscle. No rows, but a lead for the cohort map |
| `auto_exclude` | 1947 | Ruled out by rule, with the triggering phrase recorded in `notes` |
| **Total** | **3590** | |

## Auto-exclusions, by reason

| Reason | Records |
|---|---|
| `not_unloading_model` | 1034 |
| `no_muscle_outcome` | 820 |
| `review_or_editorial` | 329 |
| `not_human` | 245 |

## Priority set, by year

| Year | Records |
|---|---|
| 2026 | 17 |
| 2025 | 24 |
| 2024 | 12 |
| 2023 | 10 |
| 2022 | 12 |
| 2021 | 14 |
| 2020 | 18 |
| 2019 | 12 |
| 2018 | 12 |
| 2017 | 10 |
| 2016 | 13 |
| 2015 | 8 |
| 2014 | 12 |
| 2013 | 9 |

Every auto-exclusion is reversible: the reason and the phrase that triggered it are
in `exclusion_reason` and `notes`, so a rule that turns out to be too aggressive can
be found and undone by filtering one column.
