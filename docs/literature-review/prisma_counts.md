# PRISMA Counts

The numbers behind the flow diagram in the report and the one-line study count in the talk.
Every figure here is produced by counting rows in `data/search/screening.csv`, never typed
from memory.

## Identification

Filled from `data/search/merge_report.md`, generated 2026-09-04. Every search was limited to
**2013 onwards** — see `PLAN.md` §10; this must be stated in the methods section.

| Source | Records | Status |
|---|---|---|
| PubMed | 1412 | run 2026-09-04 |
| Embase | 0 | **not run** — no institutional access |
| Scopus | 1757 | run 2026-09-04 |
| Web of Science | 1876 | run 2026-09-04 |
| Cochrane CENTRAL | 0 | not yet run |
| Europe PMC (full text) | 0 | not yet run |
| NASA NTRS | 686 | run 2026-09-04 |
| Trial registries | 0 | not yet run |
| Citation chasing | 0 | not yet run |
| Hand-searching | 0 | not yet run |
| **Total identified** | **5731** | |
| Duplicates removed | 2141 | marked, not deleted, in `all_records.csv` |
| **Records screened** | **3590** | `data/search/screening.csv` |

Separately, **15 records** were already held in `resources/` before the search began, of
which ten are modelling candidates. They are a convenience corpus, not a search result, and
are counted on their own line in the flow diagram rather than folded into the numbers above.

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
