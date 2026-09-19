# From Bed Rest to Mars

Development of a literature-derived machine learning framework for predicting lower-limb
muscle atrophy in spaceflight analogues.

DGLRM accepted abstract — oral presentation plus written report.

- **Abstract (the contract):** [`proposal.md`](proposal.md) — never edited
- **Work plan:** [`PLAN.md`](PLAN.md)
- **Extraction schema (frozen):** [`data/schema.md`](data/schema.md)
- **Screening decisions:** [`docs/screening_decisions.md`](docs/screening_decisions.md)
- **Frozen dataset:** [`data/dataset_v1.1.csv`](data/dataset_v1.1.csv) (tag `dataset-v1.1`) — what is in it and its limits: [`data/DATASET_CARD.md`](data/DATASET_CARD.md). v1.0 stays in the repository and still rebuilds.
- **NASA open data companion:** [`data/nasa/CARD.md`](data/nasa/CARD.md) — what was fetched from the NASA Life Sciences Portal, which campaign of it v1.1 pooled, and which folders must never be pooled because the dataset already holds their participants
- **Where the project stands, with every number so far:** [`docs/STATUS.md`](docs/STATUS.md)
- **What to do next:** [`docs/NEXT_SESSION.md`](docs/NEXT_SESSION.md)
- **Framework design (also the methods section):** [`framework/DESIGN.md`](framework/DESIGN.md)
- **What may be published, and what may not:** [`docs/licensing.md`](docs/licensing.md) — the licence review of every file in the repository, and the two things that block making it public

---

## Team

| Role | Person |
|---|---|
| Scientific lead — literature search, screening, extraction, discussion | Partner |
| AI framework lead — schema, framework design, modelling, results | Qaragoz |

## Key dates

| Item | Date | Status |
|---|---|---|
| Presentation | 15 or 16 October 2026 | Confirmed by the team; the organisers assign which of the two days |
| Submission / upload deadline | 10 October 2026 | Confirmed by the team |
| Internal working schedule | as written in `PLAN.md` (P0 … P6) | Unchanged |

The internal schedule in `PLAN.md` finishes ahead of the real deadline. That gap is
deliberate buffer: it is not re-planned into additional scope. Work to the plan's dates
and treat everything after them as rehearsal and contingency.

## Open questions

| # | Question | Owner | Status |
|---|---|---|---|
| 0.2 | DGLRM author instructions — slide format, aspect ratio, time limit, disclosure slide, presentation language, and which of the two days we are on | Partner | Will be requested from the organisers directly |
| 1.1 | `data/schema.md` is frozen and says a change needs both leads. Dataset v1.1 added `repository` to the `data_source` enum, so that a row computed from an open data archive can say so and be exempt from naming a DOI and an author. Does the partner agree? | Both leads | Awaiting the partner. The change and its reasoning are in [`data/reconciliation_log.md`](data/reconciliation_log.md) §v1.1 |
| L1 | The repository has no `LICENSE` file, so nothing in it is open source yet. Which licences — code and dataset are different things | Both leads | Recommendation in [`docs/licensing.md`](docs/licensing.md) §6: a permissive software licence for the code, CC BY 4.0 for the dataset and docs |
| L2 | `data/search/fulltext_digests/` reproduces tables and sentences verbatim from 68 papers, at least 30 of which grant no reuse right. What happens to it before the repository goes public | Both leads | Recommendation in [`docs/licensing.md`](docs/licensing.md) §6: stop tracking the folder. Nothing downstream depends on it |
| L3 | NASA asks to be acknowledged as the source of its data, and the repository does not yet say so | Qaragoz | Text drafted in [`docs/licensing.md`](docs/licensing.md) §6 |

## Decisions log

### What is committed to this repository (task 0.4)

| Item | Committed? | Reason |
|---|---|---|
| `PLAN.md` | Yes | The plan is part of the work product |
| `proposal.md` | Yes | The accepted abstract is the contract everything is measured against |
| `resources/` (source PDFs) | **No** — gitignored | Copyrighted publisher material. The reference list and the extraction table carry the same information and are safe to share |
| Dataset spreadsheets (`*.xlsx`) | **Not yet** — gitignored | Decision deferred. The frozen CSV dataset produced in P2 (`data/dataset_v1.0.csv`) is the artefact intended for the repository; the working spreadsheets may stay out |
| Extraction tables, schema, code, figures | Yes | These are the reproducible core |
| Database exports and the tables merged from them (`docs/literature-review/exports/`, `data/search/all_records.csv`, `data/search/screening.csv`) | **No** — gitignored | Scopus and Web of Science licence terms restrict redistributing exported records, and this repository is public. The files stay in the shared Drive folder; the merge script and the derived counts are committed, so the tables can be rebuilt from anyone's own exports |
| The NASA NLSP archive (`data/nasa/`) | **Yes, for now** | US government work, not subject to copyright, and the manifest makes the download reproducible. Whether 470 files of individual-participant records need re-hosting at all is open question L4 in [`docs/licensing.md`](docs/licensing.md) |
| Full-text digests (`data/search/fulltext_digests/`) | **Under review** — currently committed | They reproduce paper tables and sentences verbatim. Open question L2; the recommendation is to stop tracking them |

### Branch model (task 0.3)

`main` is the trunk and receives merges only. One branch per work package:

| Branch | Owner | Work package |
|---|---|---|
| `feat/literature-review` | Partner | P1 scientific track: search, screening, extraction, cohort map |
| `feat/ai-framework` | Qaragoz | P1 AI track, P3 framework design, P4 model runs |
| `feat/integration` | Both | P2 reconciliation of extracted science with the framework |
| `feat/report-slides` | Both | P5 report, deck, figures |

Conventions: atomic commits, `type: what and why`, push after every intentional commit,
never `--no-verify`.

### The one sentence the talk exists to prove (task 0.8)

**Status: candidate selected, awaiting joint confirmation.**

> Lower-limb muscle loss in bed rest is governed by how long you unload and which muscle
> you look at — not by who the participant is. We built the structured dataset and the
> modelling framework that make that claim reproducible.

This sentence opens the deck and closes it unchanged, and it survives every fallback in
`PLAN.md` Section 13, including the case where the models are never run.

Alternatives considered, kept for the rehearsal in P6:

- *Dataset framing:* "The bed-rest literature already contains the answer to how fast the legs waste away; it is just scattered across thirty years of papers. We turned it into one documented dataset and a reproducible framework, so it can be modelled instead of re-read."
- *Mission framing (strong opener, weaker under cross-examination):* "A Mars transit countermeasure plan needs a number: how much soleus is left on day 180. We built the dataset and the framework that produce that number — and that state honestly how uncertain it is."
- *Methodological framing:* "Pooling published bed-rest studies is easy; pooling them honestly is not, because the cohorts overlap. Validated by campaign rather than by paper, duration and muscle identity still dominate."

Guardrails — the sentence never claims predictive accuracy, never asserts a study count
that the screening log does not support, and never equates bed rest with microgravity.

### Corpus status

See [`docs/screening_decisions.md`](docs/screening_decisions.md) for the include/exclude
decision on every source currently in `resources/`, with one line of reasoning each.

## Repository layout

```
data/      schema, extraction tables, cohort map, frozen dataset
docs/      screening decisions, related work, report, script, Q&A bank
framework/ data loading, features, cross-validation, models, evaluation, SHAP
results/   generated — never edited by hand
figures/   generated — never edited by hand
```
