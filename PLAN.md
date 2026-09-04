# DGLRM Project Plan
### "From Bed Rest to Mars" — Agreed Work Plan for the Accepted Abstract

**Status:** v2.0 · Rewritten 2026-09-04 to match the schedule agreed by the team
**Deliverable:** oral presentation, 10–15 min + Q&A, plus a written report
**Team:** Falk — AI framework lead · Partner — scientific lead
**Assumed presentation date:** 2026-10-02 — *placeholder; replace with the real date and shift every milestone by the same offset.*

---

## 1. The Agreed Schedule

This is the plan the team agreed on, laid out on the calendar. The four work packages map one-to-one onto the four Git branches in Section 3.

| # | Work package | Length | Dates | Branch | Lead |
|---|---|---|---|---|---|
| **P0** | Kickoff: repository, scope lock, schema | 1 day | Sep 4 | `main` | Both |
| **P1** | Literature research — two parallel tracks | 7 days | Sep 5 – Sep 11 | `feat/literature-review` · `feat/ai-framework` | Split |
| **P2** | Match the scientific part with the AI part | 3 days | Sep 12 – Sep 14 | `feat/integration` | Both |
| **P3** | Design of the framework | 1 day | Sep 15 | `feat/ai-framework` | Falk |
| **P4** | *Optional:* run the framework on the real data, four ML models | 6 days | Sep 16 – Sep 21 | `feat/ai-framework` | Falk |
| **P5** | Report + slides | 7 days | Sep 22 – Sep 28 | `feat/report-slides` | Both |
| **P6** | Rehearse, submit, present | 4 days | Sep 29 – Oct 2 | `main` | Both |

**The agreed work is 18 days; the runway is 28.** That gap is not slack to be absorbed — it is deliberately spent on P4 and P6. Two consequences worth stating up front:

- **P4 stops being "if we had time."** It gets a real six-day window. That is the difference between presenting a *designed* framework and presenting a framework with results in it, which is a materially better talk.
- **P6 is a phase, not an afterthought.** Four days of rehearsal and Q&A hardening is what turns a finished deck into a talk that survives its own question period.

If anything slips, it slips into P4's window first. P4 is the designed shock absorber; P5 and P6 are not negotiable.

---

## 2. Read This Before Starting — Three Findings from `resources/`

All fifteen PDFs currently in `resources/` were read. Three findings change what the literature week has to accomplish.

### Finding 1 — Only about nine of the fifteen sources are muscle-atrophy studies

| File | Identification | In scope? |
|---|---|---|
| `1.pdf` | Greenleaf et al., NASA TM-4580 — leg muscle volume, 30-day 6° HDBR, isotonic/isokinetic training | **Core** |
| `6.pdf` | LeBlanc et al. — regional muscle mass after 17 weeks of bed rest | **Core** |
| `7.pdf` | Alkner & Tesch — knee extensor and plantar flexor size/function, 90-day bed rest ± resistance exercise | **Core** |
| `8.pdf` | Berg et al. — hip, thigh and calf muscle atrophy after 5-week bed rest | **Core** |
| `9.pdf` | Trappe et al. — thigh and calf muscle size, 60-day bed rest in women ± exercise/nutrition | **Core** |
| `11 (2).pdf` | Zange et al. — 20 Hz whole-body vibration, 14-day 6° HDT, leg muscle volume | **Core** |
| `12.pdf` | Belavý et al. — differential atrophy of the lower-limb musculature during prolonged bed rest | **Core** |
| `13.pdf` | Belavý et al. — MRI estimation of individual lower-limb muscle volume change | **Core (methods)** |
| `14.pdf` | Miokovic et al. — heterogeneous atrophy within individual muscles, 60-day bed rest | **Core** |
| `2.pdf` | Louisy et al. — leg vein filling/emptying and leg volumes, long-term HDBR | Vascular, not muscle |
| `3.pdf` | Belin de Chantemèle et al. — calf venous volume, 90-day bed rest ± countermeasure | Vascular, not muscle |
| `4.pdf` | Bleeker et al. — leg and arm venous properties, 18-day bed rest | Vascular, not muscle |
| `5.pdf` | van Duijnhoven et al. — bed rest and exercise countermeasure on leg venous function | Vascular, not muscle |
| `10.pdf` | Akima et al. — thigh muscle tissue in boys with Duchenne muscular dystrophy | **Not bed rest** |
| `15_1.pdf` | Dulac et al. 2024, *J Physiol* — 14-day 6° HDBR in adults aged 55–65, MRI leg muscle volume ± multimodal exercise (DOI 10.1113/JP285897, NCT04964999) | **Core** |

The abstract states "15 bed-rest and HDBR studies." After `15_1.pdf` was identified in P0, the folder supports **ten** muscle-outcome studies, four vascular studies used as context, and one excluded clinical study. Every one of those decisions, with its reasoning, is in [`docs/screening_decisions.md`](docs/screening_decisions.md). **This is precisely what the P1 literature week is for.** The scientific track's primary target is closing that gap by finding five or more additional bed-rest/HDBR/dry-immersion muscle papers, so that "15 studies" is true rather than aspirational. If the target is not met by the end of P1, the scope statement gets corrected instead — "15 unloading studies, of which N contributed muscle-morphology outcomes" is entirely defensible, whereas a printed abstract that does not match the spoken talk is not.

### Finding 2 — The date range 1992–2025 is nearly, but not yet, supported

Identifying `15_1.pdf` as Dulac et al. (2024) moves the upper bound of the corpus from 2013 to 2024 and makes the printed range very nearly true. What remains is a decade-wide hole between Miokovic et al. (2012/2013) and Dulac (2024). The P1 search must reach recent campaigns — dry immersion studies, AGBRESA (2019–2021), recent NASA and ESA 30- and 60-day bed rest campaigns — or the range on the slide gets corrected to what the corpus actually covers.

### Finding 3 — The studies are not independent, which breaks Leave-One-Study-Out

`12.pdf`, `13.pdf` and `14.pdf` all come from the Charité Berlin group (Belavý, Miokovic, Armbrecht, Felsenberg) and almost certainly report overlapping analyses of the same Berlin BedRest cohort. `4.pdf` and `5.pdf` share the Nijmegen group and probably participants. `3.pdf` and `7.pdf` both describe 90-day campaigns that may trace to the same Toulouse/MEDES programme.

The McGill 14-day campaign behind `15_1.pdf` (NCT04964999) has also produced several further papers — motor-unit properties, executive function, insulin resistance — so the same trap is waiting in any recent literature the P1 search brings back.

If the same participants appear in two "studies," Leave-One-Study-Out cross-validation leaks data between the training and test folds, and the reported performance is optimistically biased.

**Consequence for the framework:** validation is **Leave-One-Cohort-Out (LOCO)**, where a cohort is a unique bed-rest campaign rather than a unique paper. Building the campaign map is a P1 deliverable on the scientific track. Presented as a deliberate methodological choice, this turns the corpus's biggest weakness into one of the strongest slides in the deck.

---

## 3. Repository and the Four Branches

One repository, four working branches, `main` as the trunk. The branches are not arbitrary: each owns exactly one work package, so a merge into `main` is the same event as a phase closing.

| Branch | Owner | Work package | Merges into `main` at |
|---|---|---|---|
| `feat/literature-review` | Partner | P1 scientific track: study search, screening, extraction, cohort map | End of P1 |
| `feat/ai-framework` | Falk | P1 AI track, P3 framework design, P4 optional model runs | End of P3, again at end of P4 |
| `feat/integration` | Both | P2: reconciling the extracted science with the framework's data requirements | End of P2 |
| `feat/report-slides` | Both | P5: written report, deck, figures | End of P5 |

**Rules, following the team's existing Git conventions**

- Never commit directly to `main`. `main` only ever receives merges from the four branches.
- Atomic commits, one thing each. Message format `type: what and why` — `feat`, `fix`, `refactor`, `chore`.
- Push after every intentional commit. First push on a branch: `git push -u origin <branch>`.
- Branch `feat/integration` from `main` *after* `feat/literature-review` has merged, so it starts from the reconciled state rather than a stale trunk.
- `feat/ai-framework` is long-lived across P1, P3 and P4. Rebase it onto `main` after each merge so it never drifts.

**`.gitignore` must contain** `node_modules/`, `.env`, `.env.local`, `.env.*.local`, `dist/`, `build/`, `.next/`, `.DS_Store`, plus `__pycache__/`, `.ipynb_checkpoints/` and `*.pyc` for the Python side.

**Decide at init and record in `README.md`:** whether `PLAN.md` and the source PDFs in `resources/` are committed. The PDFs are copyrighted publisher material — the safe default is to commit the extraction table and the reference list, and keep `resources/` out of a public repository through `.gitignore`. If the repository stays private this is a non-issue; if it will ever be published alongside the dataset, decide now rather than during a history rewrite in the final week.

### Layout

```
DGLRM/
├── README.md                       # Decisions log: scope, dates, who decided what
├── PLAN.md                         # This file
├── proposal.md                     # The accepted abstract. Never edit it; it is the contract
├── Makefile                        # `make all` regenerates every number and figure
├── resources/                      # Source PDFs (gitignored if the repo goes public)
├── data/
│   ├── schema.md
│   ├── cohorts.csv                 # study_id -> cohort_id
│   ├── raw/
│   │   ├── extraction_partner.csv
│   │   └── extraction_falk.csv
│   ├── reconciliation_log.md
│   ├── dataset_v1.0.csv            # FROZEN at the end of P2
│   └── DATASET_CARD.md
├── framework/
│   ├── DESIGN.md                   # The P3 deliverable
│   ├── config.yaml
│   ├── data_loader.py
│   ├── features.py
│   ├── cv.py                       # Leave-One-Cohort-Out
│   ├── models.py
│   ├── evaluate.py
│   └── explain.py                  # SHAP
├── results/
├── figures/final/
└── docs/
    ├── related_work.md             # P1 AI track
    ├── report.md                   # P5
    ├── limitations.md
    ├── script.md                   # Spoken script
    └── qa_bank.md
```

---

## 4. P0 — Kickoff (1 day, Sep 4)

Everything in this phase is cheap now and expensive later.

| # | Task | Owner | Output | Status |
|---|---|---|---|---|
| 0.1 | Confirm the real presentation date, session, time limit, upload deadline, and whether the talk is in German or English | Partner | One line in `README.md` | Open — 15 or 16 Oct, upload 10 Oct |
| 0.2 | Read the DGLRM author instructions: slide format, aspect ratio, disclosure slide requirements | Partner | Checklist in `README.md` | Open — to be requested from the organisers |
| 0.3 | Initialise the repository, create the four branches, write `.gitignore` and `README.md` | Falk | Repo pushed | **Done** |
| 0.4 | Decide what is committed: `PLAN.md`, `resources/`, the dataset. Record the decision | Both | `README.md` | **Done** — `README.md` |
| 0.5 | Freeze the extraction schema (Section 11) and generate the empty CSV template | Falk | `data/schema.md` + template | **Done** — `data/schema.md` + template + validator |
| 0.6 | Identify `15_1.pdf` — OCR it or replace it with a text-layer copy | Falk | Identified or removed | **Done** — Dulac et al. 2024, core study |
| 0.7 | Decide the fate of the four vascular papers and the DMD paper: context, or excluded | Both | Include/exclude with one line of reasoning each | **Done** — `docs/screening_decisions.md` |
| 0.8 | Agree the one sentence the talk exists to prove (Section 9) | Both | `README.md`, top of the deck outline | Candidate in `README.md`, awaiting joint confirmation |

**Definition of success.** The repository is live with four branches. The schema is frozen. Both people can state the same answer to "how many studies are in the modelling set, and why?" The extraction template exists, so the literature week starts by filling a form rather than by inventing one.

**Why the schema is frozen on day one:** the two literature tracks run in parallel for a week without daily contact. If the scientific track extracts into an ad-hoc spreadsheet while the AI track assumes a different shape, P2 is spent reformatting instead of reconciling. The schema is the contract between the two tracks.

---

## 5. P1 — Literature Research (7 days, Sep 5 – Sep 11)

Two tracks, run in parallel, on two branches. They are deliberately independent: neither blocks the other, and they converge in P2.

### 5.1 Scientific track — Partner · `feat/literature-review`

| # | Task | Output |
|---|---|---|
| 1.1 | Systematic search to close the gap in Finding 1: PubMed, Scopus, Web of Science, NASA Technical Reports Server. Target five to seven additional bed-rest/HDBR muscle-morphology studies | New PDFs in `resources/`, each logged with the search string and database |
| 1.2 | Deliberately search recent campaigns to address Finding 2: AGBRESA, dry immersion, recent ESA/NASA/MEDES bed rest | Recent studies added, or a written statement that none qualify |
| 1.3 | Screen every candidate against written inclusion and exclusion criteria | `docs/screening_log.md` — a table of every study screened, with the reason for each exclusion |
| 1.4 | Build the cohort map addressing Finding 3: which papers report the same participants | `data/cohorts.csv` mapping `study_id → cohort_id` |
| 1.5 | Extract every included study into the frozen schema | `data/raw/extraction_partner.csv` |
| 1.6 | Digitise figure-only data where no table exists (WebPlotDigitizer), flagged `data_source = figure_digitized` | Digitised rows, marked |
| 1.7 | Draft the physiological background: why antigravity muscles, why bed rest is the analogue, what countermeasures currently do | `docs/background.md` |
| 1.8 | Draft the limitations list from the scientific side | First half of `docs/limitations.md` |

**Search terms to start from:** `(bed rest OR head-down tilt OR HDBR OR dry immersion OR unloading) AND (muscle volume OR cross-sectional area OR atrophy OR CSA) AND (soleus OR gastrocnemius OR quadriceps OR triceps surae OR lower limb) AND (MRI OR CT OR DXA)`. Log every query verbatim — the search strategy is a slide, and it is the first thing a methodologist asks about.

### 5.2 AI track — Falk · `feat/ai-framework`

The AI half of the literature week is not "read about random forests." It is establishing what a defensible modelling framework looks like at this sample size, and what has already been done, so that the design in P3 is a considered choice rather than a default.

| # | Task | Output |
|---|---|---|
| 1.9 | Survey prior work applying ML to spaceflight, bed rest or disuse-atrophy prediction. What exists, what it claimed, what N it used | `docs/related_work.md` |
| 1.10 | Review methodology for supervised learning on small, clustered, literature-derived datasets: grouped cross-validation, nested tuning, study-level bootstrap, learning curves | Methods section of `docs/related_work.md` |
| 1.11 | Review how the meta-analysis literature handles what this project is doing — aggregate-data meta-regression, mixed-effects models, variance weighting — and state honestly where the ML framework differs and where it overlaps | A written position: what ML adds beyond meta-regression |
| 1.12 | Review interpretability at small N: what SHAP does and does not license, and how to test feature-ranking stability across folds | Interpretability section |
| 1.13 | Define the evaluation protocol on paper before any code: target variable, metrics, baseline, CV scheme, uncertainty quantification | `framework/DESIGN.md` skeleton |
| 1.14 | Define the data requirements the framework needs from the extraction, and send them to the scientific track mid-week | A short requirements note — **the single most valuable cross-track message of the week** |

**Positioning note.** Question 12 in the Q&A bank — "why not a mixed-effects meta-regression?" — is the sharpest question this project will face, and it is a methods question, not a physiology question. Task 1.11 exists so that it gets answered in one confident paragraph rather than improvised on stage.

**Definition of success for P1.**

- The scientific track has a written screening log, a cohort map, and an extraction file in the frozen schema. Every row traces to a study, a table or figure, and a page number.
- The corpus question from Finding 1 is resolved in one direction or the other, in writing.
- The AI track has `docs/related_work.md` and a first `framework/DESIGN.md` naming the target variable, the metrics, the baseline and the CV scheme.
- The data-requirements note reached the scientific track by **Sep 8 at the latest** — mid-week, not at the end. A requirement that arrives on day seven cannot be acted on.
- Both branches merge into `main` cleanly at the end of the week.

**The one thing that can go wrong here:** the two tracks working for seven days without talking. Book one 30-minute call on Sep 8. Its only agenda is the requirements note and anything the extraction has turned out to make impossible.

---

## 6. P2 — Match the Scientific Part with the AI Part (3 days, Sep 12 – Sep 14)

Branch `feat/integration`, both people, and the highest-value three days in the plan. This is where a literature review becomes a dataset.

### Day 1 (Sep 12) — Reconcile

| # | Task | Owner |
|---|---|---|
| 2.1 | Falk independently extracts two to three studies already extracted by the partner, blind, and the two files are compared | Both |
| 2.2 | Resolve every numeric disagreement, and log each one with its resolution | Both |
| 2.3 | Resolve the composite problem: `triceps_surae` is not the sum of `soleus` and `gastrocnemius`. Decide explicitly how composite and component rows coexist | Both |
| 2.4 | Resolve the modality problem: MRI volume, CT CSA and DXA lean mass are not the same measurement. Decide whether they share a target column, and record the decision | Both |
| 2.5 | Fix the sign convention once: `pct_change` is negative for atrophy, everywhere | Falk |

The double-extraction check in 2.1 is not bureaucracy. It is the only evidence the team will have that the extraction is reproducible, and "we independently double-extracted a subset and agreed to within X %" is a one-line answer to an entire category of Q&A.

### Day 2 (Sep 13) — Map science onto features

| # | Task | Owner |
|---|---|---|
| 2.6 | Map each extracted variable to a model feature, a stratification variable, or "recorded but not modelled" — and justify each exclusion | Both |
| 2.7 | Derive `muscle_function_class` (antigravity extensor, flexor, mixed) with the partner deciding the assignment for each muscle | Partner |
| 2.8 | Decide the encoding of the countermeasure: binary presence, modality category, or a crude dose ordinal. At this N, simpler wins | Both |
| 2.9 | Sanity-check the merged dataset against physiology: is any row implausible? Does the duration–response go the right way? | Partner |
| 2.10 | Confirm `cohort_id` covers every study, and that no cohort appears under two identifiers | Both |

### Day 3 (Sep 14) — Freeze

| # | Task | Owner |
|---|---|---|
| 2.11 | Automated QC: range checks, unit consistency, impossible values, duplicate rows, orphan references | Falk |
| 2.12 | Write the dataset card: provenance, exclusions, known limitations, how to cite | Both |
| 2.13 | Produce the two descriptive figures that do not depend on any model — duration–response and muscle ranking | Falk |
| 2.14 | **Freeze** `data/dataset_v1.0.csv`, tag it, merge `feat/integration` into `main` | Falk |

**Definition of success for P2.**

- Independent double extraction agrees to **≥ 95 %** on numeric fields before reconciliation and 100 % after. Below 90 % means the schema was ambiguous — fix the schema and re-extract the affected fields rather than papering over it.
- `qc_dataset.py` exits clean.
- **Minimum viable dataset: 60 rows across ≥ 8 independent cohorts, ≥ 4 muscle groups, ≥ 4 distinct unloading durations.** Below that, the P4 modelling is not honest and the talk moves down the fallback ladder in Section 13.
- Every column is either a modelled feature or explicitly marked as not modelled, with a reason.
- The dataset is frozen and tagged `dataset-v1.0`. **Nothing touches it again.** Any later change requires a v1.1 tag and a log entry.
- The two descriptive figures exist. Even in the worst case, the talk now has real results in it.

---

## 7. P3 — Design of the Framework (1 day, Sep 15)

One day, on `feat/ai-framework`. The output is a design document and a runnable skeleton, not a finished analysis.

| # | Task | Output |
|---|---|---|
| 3.1 | Finalise `framework/DESIGN.md`: problem statement, target, feature set, model families, CV protocol, metrics, interpretability, and the explicit assumptions | The document that becomes the methods slides *and* the report's methods section |
| 3.2 | Draw the framework as one diagram: sources → extraction → schema → dataset → LOCO CV → four model families → evaluation → SHAP | `figures/framework.svg` — the single most reusable asset in the project |
| 3.3 | Specify the module interfaces (`data_loader`, `features`, `cv`, `models`, `evaluate`, `explain`) and write the skeleton with docstrings and typed signatures | Runnable skeleton, no results |
| 3.4 | Implement the **baseline first**: percentage loss as a function of duration alone, in linear, log and saturating-exponential form | `results/baseline.json` |
| 3.5 | Implement `cv.py` — Leave-One-Cohort-Out, grouped on `cohort_id`, with an assertion that fails loudly if any cohort appears in both a training and a test fold | The leakage guard |
| 3.6 | Write `config.yaml` so that every choice — features, models, folds, seeds — is declared in one file rather than scattered through code | Reproducibility by construction |

**Definition of success for P3.**

- `framework/DESIGN.md` is complete enough that someone else could implement it. If it is complete, the talk's methods section is already written.
- The framework diagram is presentation-ready. **This is the slide that carries the whole AI contribution** — if P4 never happens, this figure and this document *are* the deliverable, and they fully satisfy the abstract's wording that a comparative framework "was designed."
- The baseline runs and produces a number. Everything later is measured against it.
- The leakage assertion exists and has been tested by deliberately feeding it a bad split to confirm it fails.
- Every choice sits in `config.yaml`, not in code.

**Scope discipline.** One day means one day. No model tuning, no results, no figures beyond the diagram. The temptation to start fitting models on day one of a designed framework is exactly how a one-day phase becomes a four-day phase.

---

## 8. P4 — Optional: Run the Framework (6 days, Sep 16 – Sep 21)

This was agreed as "if we had time." The calendar says there is time: six days. Treat it as planned work with a hard stop, not as a stretch goal — and if P1 or P2 overran, this is the window that absorbs it.

| # | Task | Output |
|---|---|---|
| 4.1 | Fit Linear Regression, Random Forest, Support Vector Regression and Gradient Boosting inside the LOCO loop, with all preprocessing fitted per fold | `results/model_comparison.csv` |
| 4.2 | Nested hyperparameter tuning, or fixed declared defaults. Tuning on the test fold is the one unrecoverable mistake here | Documented in `DESIGN.md` |
| 4.3 | Study-level bootstrap for 95 % confidence intervals on every reported metric | CIs on MAE, RMSE, R² |
| 4.4 | SHAP on the best model, plus a top-feature stability check across folds | `figures/shap_*.png` + a stability table |
| 4.5 | Sensitivity analyses: with and without figure-digitised rows; with and without the largest cohort; sex-stratified if N allows | `results/sensitivity.md` |
| 4.6 | Physiological plausibility review — does the model assert anything known to be false? | Partner's written sign-off |
| 4.7 | Optional, only if 4.1–4.6 are finished: extrapolate to a 180-day transit **with prediction intervals** and an explicit statement about going beyond the observed 119-day maximum | One heavily caveated backup slide |
| 4.8 | **Freeze** the results, tag `results-v1.0`, merge into `main` | Falk |

**Thresholds, agreed before the models run**

| Criterion | Target | If missed |
|---|---|---|
| LOCO-CV mean absolute error | ≤ 4 percentage points of muscle change | Report honestly — the dataset and framework are still the contribution |
| Best model vs the duration-only baseline | ≥ 15 % relative MAE improvement | **Report the null result.** It is a legitimate and genuinely interesting finding |
| SHAP top-3 feature stability | Same top three in ≥ 80 % of folds | Present importance as indicative only, and say so out loud |
| Leakage audit | No cohort split across folds; no preprocessing fitted outside a fold | **Blocking** |
| Reproducibility | `make all` regenerates every number and figure from the frozen dataset | **Blocking** |
| Physiological sign-off | Partner signs off | **Blocking** |

The first three are *deliberately allowed to fail*. A talk that says "four model families, honestly validated, and none of them beat a simple duration curve — here is what that tells us about how much signal the published literature contains" is a good talk. A talk reporting an inflated R² from a leaky split is a talk that ends badly in Q&A.

**Hard stop: Sep 21.** Whatever exists on the evening of Sep 21 is what goes in the report. P5 does not start late.

---

## 9. P5 — Report and Slides (7 days, Sep 22 – Sep 28)

Branch `feat/report-slides`, both people. Two deliverables from one body of work, in this order: the report first, because writing it forces every argument to become explicit, and the slides then become a compression of something that already holds together.

### The one sentence everything serves

> **We built a structured, documented dataset of lower-limb muscle loss during bed rest and a framework for modelling it — and it shows that unloading duration and muscle identity, not participant demographics, dominate atrophy. That is what a countermeasure planner for a Mars transit needs to know.**

Three supporting claims, ordered by how well the evidence backs them:

1. **The duration–response is consistent and quantifiable.** Strongest, and it survives every fallback.
2. **Antigravity muscles are selectively vulnerable.** Well supported — the soleus, gastrocnemius and triceps surae ranking reproduces across studies.
3. **A comparative framework with honest cross-validation can rank the drivers.** Most interesting, most attackable, and therefore last.

**Framing rule.** This is a *framework and dataset* contribution, not a *performance* contribution. With roughly a dozen independent cohorts, no cross-validated R² will impress a machine-learning audience, and it does not need to. This audience cares about physiological plausibility, honest uncertainty, and whether the approach could ever inform mission planning.

### Days 1–3 (Sep 22 – Sep 24) — The report

| # | Task | Owner |
|---|---|---|
| 5.1 | Methods section — largely a rewrite of `framework/DESIGN.md` and the screening log | Falk drafts, Partner reviews |
| 5.2 | Introduction and background — from `docs/background.md` | Partner |
| 5.3 | Results — every number generated by `make all`, none typed by hand | Falk |
| 5.4 | Discussion: what it means physiologically, how it positions against the Charité, NASA and MEDES work | Partner |
| 5.5 | Limitations — the complete list, not the polite half | Both |
| 5.6 | Reference list, generated from the shared library, checked against the screening log | Partner |

**Limitations must name at least six real ones:** small N, publication bias, heterogeneous imaging modalities, cohort non-independence, bed rest is not true microgravity, and extrapolation beyond the observed duration range.

### Days 4–6 (Sep 25 – Sep 27) — The slides

Twelve minutes inside a fifteen-minute slot. Never plan to the maximum.

| Clock | Slides | Content | Speaker |
|---|---|---|---|
| 0:00–1:00 | 1–2 | Hook: a crew arrives at Mars after six months in transit — what is left of the soleus? Title and affiliations | Partner |
| 1:00–2:30 | 3–4 | Why musculoskeletal deconditioning is mission-limiting; why bed rest is the terrestrial analogue | Partner |
| 2:30–3:30 | 5 | The gap: decades of individual studies, no pooled quantitative model. State the aim | Partner |
| 3:30–5:30 | 6–8 | Methods: corpus and screening, extraction schema, the cohort map, and why validation is Leave-One-**Cohort**-Out | Falk |
| 5:30–7:00 | 9–10 | Result 1: duration–response. Result 2: muscle vulnerability ranking | Partner |
| 7:00–8:30 | 11–12 | The framework diagram, then the model comparison against the duration-only baseline with confidence intervals | Falk |
| 8:30–9:30 | 13 | SHAP: what drives the prediction, and does physiology agree? | Falk |
| 9:30–10:30 | 14 | Implications: personalised countermeasure prescription, which muscles to protect first | Partner |
| 10:30–11:30 | 15 | Limitations, stated confidently and without apology | Partner |
| 11:30–12:00 | 16 | Conclusion, next steps, and the one sentence worth remembering | Partner |
| — | 17+ | Backup slides from the Q&A bank | Either |

**Figure set — five in the deck, maximum.** Each supports exactly one claim.

| Fig | Content | Supports | Owner |
|---|---|---|---|
| F1 | Corpus overview: screening flow (identified, screened, included) plus a timeline strip of each cohort's duration and sample size | Credibility of the dataset | Partner |
| F2 | Duration–response: `pct_change` against `duration_days`, coloured by muscle family, fitted curve with confidence band, control arms only | Claim 1 | Falk |
| F3 | Muscle vulnerability ranking: horizontal forest-style plot, mean percentage loss per muscle with CIs, sorted | Claim 2 | Falk |
| F4 | The framework diagram from P3 | The method itself | Falk |
| F5 | Model comparison with the baseline as a reference line, or the SHAP summary if P4 produced one | Claim 3 | Falk |

**Figure standards.** Colourblind-safe palette. Text in the exported figure at least as large as the slide body text. Every axis labelled with units. Sample size on the figure itself, not only in the caption — audiences read figures, not captions.

### Day 7 (Sep 28) — Freeze

| # | Task | Owner |
|---|---|---|
| 5.7 | Write the spoken script verbatim, then cut the slides down to what the script needs | Both |
| 5.8 | Build the backup slide pack from the ★ questions in Section 12 | Both |
| 5.9 | Legibility pass: body text ≥ 24 pt, readable from the back row | Falk |
| 5.10 | Add the disclosure, conflict and funding slide required by DGLRM | Partner |
| 5.11 | **Freeze** the deck, upload by the organiser's deadline, merge `feat/report-slides` into `main` | Both |

**Definition of success for P5.**

- The report is complete and internally consistent — every number in it comes from `results/`.
- The deck runs **11:00–12:30 spoken aloud** at a normal pace. Not 14:50.
- Every slide title is a claim, not a label. "Soleus loses twice as much as tibialis anterior," never "Results." If a title could sit above any other slide, rewrite it.
- No slide carries more than about 30 words of body text.
- Every number on a slide traces to a tagged commit and can be regenerated by `make all`.
- The deck is uploaded before the deadline, with a copy on a USB stick and a copy in cloud storage.

---

## 10. P6 — Rehearse, Submit, Present (4 days, Sep 29 – Oct 2)

| # | Task | Owner |
|---|---|---|
| 6.1 | Solo run-through ×3 each, timed | Each |
| 6.2 | Full joint run-through ×2 with clean handovers | Both |
| 6.3 | Hostile Q&A drill: a colleague asks the Section 12 bank cold, in random order | Both |
| 6.4 | Rehearse once in front of someone who does not work on this project | Both |
| 6.5 | Technical check: aspect ratio, embedded fonts, PDF fallback, laptop, adapter, clicker | Falk |
| 6.6 | Prepare the 30-second elevator version for hallway conversations | Both |
| 6.7 | One-page handout with a QR code to the repository | Falk |
| 6.8 | Present. Then write down every question asked, immediately afterwards | Both |
| 6.9 | Follow up within 48 hours with anyone who asked for the dataset | Falk |
| 6.10 | Archive the frozen dataset, code and deck; mint a Zenodo DOI if the dataset is released | Falk |

**Definition of success for P6.**

- Two consecutive full run-throughs land inside the time limit with no notes.
- Every question in the bank gets a confident answer in under 45 seconds. **"We do not know, and here is what it would take to find out" is a full-credit answer** — rehearse saying it without flinching.
- The handover between speakers is one rehearsed sentence, not an improvisation.
- Both speakers can deliver the *other* person's section at 80 % quality. Q&A does not respect the division of labour.
- The deck opens correctly on a machine that is not the authoring laptop.
- At least three substantive questions are asked. Silence means the talk did not land.
- Every question is written down. This is free peer review, and it shapes the manuscript.

---

## 11. The Extraction Schema

**Frozen. The schema now lives in [`data/schema.md`](data/schema.md), with the matching
empty table in [`data/extraction_template.csv`](data/extraction_template.csv) and an
executable validator in [`framework/validate_extraction.py`](framework/validate_extraction.py).**

That document supersedes the draft that used to sit here. What it defines:

- **One row is one comparison against baseline** — one study × one arm × one muscle × one
  measurement occasion, carrying both values and the percent change. There are no
  baseline-only rows; the draft asked for those *and* for a baseline column on every row,
  which contradicted itself and would have fed every model a fake zero.
- **60 columns in nine groups:** study identity and provenance, unloading design, arm and
  participants, what was measured, values, and quality control.
- **A controlled vocabulary for `muscle`**, extended by a commit to the schema rather than
  by typing a new name into a cell.
- **Ten rules**, of which the load-bearing ones are: never impute silently; `pct_change` is
  negative for atrophy; one `cohort_id` per campaign rather than per paper; composite and
  component muscles never enter a model together unpooled; `n_analysed` rather than `n_arm`
  is the weight; every row traceable via `source_file` + `page_ref` in under a minute.
- **Twelve validation checks** that run as a script, so a malformed table fails before it is
  committed instead of during P2.

Fields added beyond the draft, each because a real paper in `resources/` needs it:
`phase` and `days_from_unloading_end` (Dulac 2024 measures during bed rest *and* during
recovery), `n_analysed` (dropouts are routine), `population` (Dulac is the only older
cohort), `registry_id` (the cheapest reliable way to detect shared participants),
`is_composite` / `laterality` / `measurement_site` (Miokovic's within-muscle heterogeneity
makes site matter), split `variance_of` / `variance_type` / `variance_value`, and the
`unit_original` / `unit_si` pair.

Section 8 of `data/schema.md` lists every change against the draft with its reason.

Everything below still holds: the schema is the contract between the two literature tracks,
it is frozen before either track starts, and changing it after P0 costs both people an hour
of reconciliation each time.

---

## 12. Q&A Bank

The questions this audience will actually ask. Write a one-paragraph answer for each, and a backup slide for the ★ ones.

**On the data**

1. ★ How did you handle the fact that several of your papers report the same Berlin BedRest cohort? *(Answer with the cohort map. This turns the biggest weakness into a demonstration of rigour.)*
2. How did you deal with different imaging modalities — MRI volume against DXA lean mass?
3. What about publication bias? Do null-result bed-rest studies exist?
4. ★ What are your inclusion and exclusion criteria, exactly? *(Show the screening log.)*
5. Did you extract data from figures? How did you validate the digitisation?
6. Why fifteen studies rather than a full systematic review with PRISMA?

**On the modelling**

7. ★ At this sample size, is any machine-learning model justified over a simple regression? *(The honest answer is the baseline comparison.)*
8. What exactly is one observation in your model? *(Muscle × timepoint × arm. Have this crisp.)*
9. How do you avoid overfitting with more features than independent cohorts?
10. ★ Is SHAP meaningful at this sample size? *(Only as a stability-checked ranking. Show the fold-stability table.)*
11. Did you tune hyperparameters inside or outside the cross-validation loop?
12. ★ Why these four models rather than a mixed-effects meta-regression? *(The sharpest question this project faces. Task 1.11 in P1 exists to answer it in one confident paragraph.)*

**On physiology and application**

13. Bed rest is not microgravity. How far does this transfer to actual spaceflight?
14. ★ Can you predict an individual astronaut's atrophy, or only a group mean? *(Group level only. Say so plainly.)*
15. Your longest observation is 119 days; a Mars transit is roughly 180. How do you justify extrapolating?
16. What would this change about how countermeasures are currently prescribed?
17. Why is the soleus more affected? Fibre type, antigravity loading, or both?
18. Does the model account for the recovery and reconditioning phase?

**On what comes next**

19. Will the dataset be made public?
20. What would you need to make this clinically useful?
21. Have you contacted the Charité, DLR or MEDES groups about validating against individual-level data? *(If not: "not yet, and that is our next step" — then actually do it. This question is a collaboration offer in disguise.)*

**Rehearsal rule.** A colleague asks all twenty-one cold, in random order, with no warning. Any answer running over 45 seconds gets rewritten.

---

## 13. Fallback Ladder

Decide the fallbacks now, while nobody is panicking. Every rung is still a good talk.

| Rung | Trigger | The talk becomes |
|---|---|---|
| **A** | Everything works | Dataset, designed framework, four-model comparison, SHAP, and a caveated mission extrapolation |
| **B** | P4 runs, but the models fail to beat the duration-only baseline | "We built the dataset, designed the framework, ran the comparison honestly, and a simple saturating duration curve wins. Here is what that says about how much signal the published literature contains." **A genuinely strong talk, not a retreat** |
| **C** | P4 is cut or only partly done | Dataset, framework design, framework diagram, and the two descriptive results from P2. The framework is presented as designed and specified, which is exactly what the abstract promised |
| **D** | P2 delivers fewer than 60 rows | Pure quantitative synthesis: duration–response and muscle ranking, plus the framework design. No model results |

**The rule:** the decision point is the P4 hard stop on **Sep 21**. Whichever rung is true that evening is the talk. A rung-C talk delivered calmly beats a rung-A talk assembled at two in the morning.

Note that rungs C and D still satisfy the accepted abstract, which says a comparative framework "was designed" and that the analyses were "preliminary." The abstract was written honestly; the fallbacks are not a climb-down.

---

## 14. Risk Register

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| P1 does not find enough additional muscle studies | High | High | Decide by Sep 11 whether to restate the scope; both options are defensible if chosen deliberately | Partner |
| The two P1 tracks work for a week without talking | High | High | The mandatory Sep 8 call; the requirements note from task 1.14 | Both |
| Extraction is not finished when P2 starts | Medium | High | The schema is frozen in P0 so extraction is form-filling; P4's window absorbs the overrun | Partner |
| Cohort overlap missed, invalidating the validation | Medium | High | `cohorts.csv` is a P1 deliverable; the leakage assertion in P3 fails loudly | Both |
| P3 expands past one day into model fitting | High | Medium | P3 is design only. Model fitting is P4, and it starts on Sep 16, not earlier | Falk |
| The models do not beat the baseline | Medium | Low *if prepared* | Rung B is pre-written as a real talk | Falk |
| The scanned `15_1.pdf` cannot be identified | Low | Low | OCR it in P0, or drop it and adjust N | Falk |
| Report and slides compress into the final two days | Medium | High | P5 is seven days with the report first; the deck freezes Sep 28 | Both |
| One presenter is ill on the day | Low | High | Each rehearses the other's section to 80 % quality | Both |
| Technical failure in the room | Low | Medium | PDF export, USB stick, cloud copy, arrive early | Falk |
| Scope creep into a journal manuscript | Medium | Medium | Manuscript work is explicitly out of scope until after the talk | Both |

---

## 15. Master Success Definition

The project succeeds if all five hold on presentation day.

1. **Scientific integrity.** Every number on every slide and in the report traces to a frozen dataset and a tagged commit, and is reproducible with one command. No number exists that the team cannot defend.
2. **Honest validation.** Cross-validation is grouped by cohort, no cohort is split across folds, no preprocessing is fitted outside a fold, and the comparison against the duration-only baseline is shown regardless of how it turns out.
3. **The talk lands.** Delivered inside the time limit, with one memorable sentence and at least three substantive questions from the audience.
4. **Q&A holds.** Every question in the bank answered in under 45 seconds, including the hard ones about sample size, cohort overlap, and why not a mixed-effects model.
5. **It outlives the talk.** A frozen dataset, a runnable repository, a written report, a log of every question asked, and at least one follow-up conversation that could become a collaboration or a manuscript.

**Anti-goals — explicitly not what success means:** a high R², a large number of models, a large number of slides, or any claim of clinical readiness. At this dataset size, each of those is a symptom that something went wrong.

---

## 16. Today

Six things, in this order, before the literature week starts.

1. Confirm the real presentation date, slot length, language, and upload deadline. Every date in this plan shifts from that one.
2. Initialise the repository, create the four branches, push.
3. Freeze `data/schema.md` and generate the empty CSV template. The literature week cannot start correctly without it.
4. Decide what is committed — `resources/`, the dataset, this plan — and write the decision into `README.md`.
5. Resolve the corpus question from Finding 1 into a target for the week: how many additional studies is the scientific track looking for?
6. Put the Sep 8 mid-week call in both calendars. It is the only thing preventing the two parallel tracks from diverging.
