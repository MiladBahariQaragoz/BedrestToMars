# PRISMA Counts

The numbers behind the flow diagram in the report and the one-line study count in the talk.
Every figure here is produced by counting rows in `data/search/screening.csv`, never typed
from memory.

## Identification

| Source | Records |
|---|---|
| PubMed | |
| Embase | |
| Scopus | |
| Web of Science | |
| Cochrane CENTRAL | |
| Europe PMC (full text) | |
| NASA NTRS | |
| Trial registries | |
| Citation chasing | |
| Hand-searching | |
| **Total identified** | |
| Duplicates removed | |
| **Records screened** | |

## Screening

| Step | Records |
|---|---|
| Excluded at title/abstract | |
| Full texts sought | |
| Full texts not retrievable | |
| Full texts assessed | |
| Excluded at full text | |
| **Studies included** | |
| of which **new** (not already in `resources/`) | |
| **Distinct cohorts** in the modelling set | |

## Exclusions at full text, by reason

Codes are the fixed list in `PLAN.md` §2. These are the numbers an audience asks about.

| Reason | Count |
|---|---|
| `not_human` | |
| `not_unloading_model` | |
| `duration_too_short` | |
| `no_muscle_outcome` | |
| `upper_limb_only` | |
| `no_baseline_or_followup` | |
| `disease_causes_wasting` | |
| `review_or_editorial` | |
| `duplicate_report` | |
| `no_full_text` | |
| `language` | |

## The two numbers that go on a slide

- **Studies in the modelling set:** _N_
- **Distinct cohorts:** _M_

`M`, not `N`, is the honest sample size for cross-validation, and saying so before anyone
asks is worth more than a good R².
