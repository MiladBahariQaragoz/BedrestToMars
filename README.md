# From Bed Rest to Mars

Development of a literature-derived machine learning framework for predicting lower-limb
muscle atrophy in spaceflight analogues.

DGLRM accepted abstract — oral presentation plus written report.

- **Abstract (the contract):** [`proposal.md`](proposal.md) — never edited
- **Work plan:** [`PLAN.md`](PLAN.md)
- **Extraction schema (frozen):** [`data/schema.md`](data/schema.md)
- **Screening decisions:** [`docs/screening_decisions.md`](docs/screening_decisions.md)

---

## Team

| Role | Person |
|---|---|
| Scientific lead — literature search, screening, extraction, discussion | Partner |
| AI framework lead — schema, framework design, modelling, results | Falk |

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

## Decisions log

### What is committed to this repository (task 0.4)

| Item | Committed? | Reason |
|---|---|---|
| `PLAN.md` | Yes | The plan is part of the work product |
| `proposal.md` | Yes | The accepted abstract is the contract everything is measured against |
| `resources/` (source PDFs) | **No** — gitignored | Copyrighted publisher material. The reference list and the extraction table carry the same information and are safe to share |
| Dataset spreadsheets (`*.xlsx`) | **Not yet** — gitignored | Decision deferred. The frozen CSV dataset produced in P2 (`data/dataset_v1.0.csv`) is the artefact intended for the repository; the working spreadsheets may stay out |
| Extraction tables, schema, code, figures | Yes | These are the reproducible core |

### Branch model (task 0.3)

`main` is the trunk and receives merges only. One branch per work package:

| Branch | Owner | Work package |
|---|---|---|
| `feat/literature-review` | Partner | P1 scientific track: search, screening, extraction, cohort map |
| `feat/ai-framework` | Falk | P1 AI track, P3 framework design, P4 model runs |
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
