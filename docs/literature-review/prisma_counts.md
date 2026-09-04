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

Title/abstract screening ran on 2026-09-04 in two stages: a deterministic triage against the
§2 criteria (`framework/triage_screening.py`), then a human read of the priority set and the
top of the `maybe` set, recorded in `docs/literature-review/screen_decisions_*.csv`.

| Step | Records |
|---|---|
| Records screened | 3590 |
| Excluded at title/abstract | 2493 |
| **Included at title/abstract** | **74** |
| Still to screen | 1023 |
| Full texts sought | 74 |
| Full texts retrieved | 70 — 30 as machine-readable XML, 40 as PDF |
| Full texts not retrievable | 4 — 2 paywalled, 2 exist only as conference abstracts |
| Full texts assessed | 4 of 74 so far |
| Excluded at full text | 3, all `no_full_text` |
| **Studies included** | pending full text |
| of which **new** (not already in `resources/`) | pending |
| **Distinct cohorts** in the modelling set | pending |

The 1023 records still to screen are the remainder of the `maybe` bucket plus 80 priority
records that need a full text before a call can be made. They are not excluded and must not
be reported as such.

## Exclusions at title/abstract, by reason

Codes are the fixed list in `PLAN.md` §2. These are the numbers an audience asks about.

| Reason | Count |
|---|---|
| `not_unloading_model` | 1048 |
| `no_muscle_outcome` | 830 |
| `review_or_editorial` | 346 |
| `not_human` | 252 |
| `disease_causes_wasting` | 12 |
| `duration_too_short` | 5 |
| `upper_limb_only` | 0 |
| `no_baseline_or_followup` | 0 |
| `duplicate_report` | 0 |
| `no_full_text` | 0 |
| `language` | 0 |
| **Total** | **2493** |

481 of the `no_muscle_outcome` exclusions are real unloading campaigns that reported
something other than muscle — gait, motor units, cardiovascular. They contribute no rows,
but they identify campaigns, and they are kept as `campaign_lead` in the triage column for
building `data/cohorts.csv`.

## Exclusions at full text, by reason

| Reason | Count |
|---|---|
| `no_full_text` | 3 |

One of the four unobtainable studies survives anyway: the Dirks 2016 abstract prints a
3.2% decline in quadriceps CSA after seven days of bed rest, which is a complete row on
its own. It is extracted with `data_source = text` and `extraction_confidence = low`.

The two paywalled studies are an access failure rather than an absence. If the dataset
ends up thin, an interlibrary loan recovers them; the note in
`screen_decisions_fulltext.csv` says exactly what each one would contribute.

## The two numbers that go on a slide

- **Studies in the modelling set:** _N_
- **Distinct cohorts:** _M_

`M`, not `N`, is the honest sample size for cross-validation, and saying so before anyone
asks is worth more than a good R².
