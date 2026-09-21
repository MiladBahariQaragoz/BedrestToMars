# Project status — 2026-09-19

Where "From Bed Rest to Mars" stands, what exists on disk, and what every number currently
says. Written at the end of the P3/P4 modelling work so the next person to open the
repository — including a future version of either of us — can start without re-deriving
anything. Updated on 19 September, when tier 1 was implemented and fitted, and again the
same day when `dataset_v1.1` pooled one campaign from NASA's open bed-rest archive and every
result below was refitted against it. Updated again on 21 September, when tier 3 - a
TypeSafe language-model forecast - was added and run on its own branch,
`feat/typesafe-forecast`.

**Next actions live in [`NEXT_SESSION.md`](NEXT_SESSION.md).**

---

## 1. Phase status against the plan

| Phase | Planned | State |
|---|---|---|
| P0 Kickoff | Sep 4 | **Done.** Repository, branches, frozen schema, screening decisions |
| P1 Literature research | Sep 5–11 | **Done.** 5731 records identified, screened, extracted; merged into `main` |
| P2 Integration | Sep 12–14 | **Done.** Reconciled, QC'd, `dataset_v1.0` frozen and tagged; merged into `main`. `dataset_v1.1` followed on Sep 19 |
| P3 Framework design | Sep 15 | **Done** (late, completed Sep 18). `framework/DESIGN.md`, config, six modules, baseline |
| P4 Run the framework | Sep 16–21 | **Partly done.** Tier 1 fitted (Sep 19) and tier 2 complete with a null result. Tier 3, a TypeSafe forecast, run Sep 21 (§3). Sensitivity analyses not yet run |
| P5 Report and slides | Sep 22–28 | Not started |
| P6 Rehearse and present | Sep 29–Oct 2 | Not started. Talk is 15/16 Oct, upload 10 Oct |

## 2. What exists

### Data

| Artefact | What it is |
|---|---|
| `data/dataset_v1.1.csv` | The frozen dataset. 742 rows, 52 studies, 36 campaigns. SHA-256 verified on every load; tag `dataset-v1.1`. `dataset_v1.0.csv` stays in the repository and still rebuilds |
| `data/raw/extraction_nasa.csv` | **New.** The five rows v1.1 added, computed from NASA's archive by `framework/extract_nasa.py` rather than typed from a paper |
| `data/nasa/` | **New.** Seven folders of open NASA NLSP bed-rest files with a manifest and a card. Six of them are a companion set that must never be pooled — four are campaigns the dataset already holds |
| `data/DATASET_CARD.md` | What is in it, where it came from, and its limits |
| `data/muscle_map.csv` | **New.** All 51 muscles classified by mechanical function and family, one written reason each |
| `data/measurement_site_map.csv` | **New.** The 40 free-text site strings resolved into a kind and a position |
| `data/cohorts.csv` | The campaign map — which papers share participants |
| `data/schema.md` | The frozen extraction schema |

Neither new map edits the frozen dataset. Both are joined on at load time, so the assignments
can be argued with and re-run without a new dataset version.

### Framework

| Module | Job |
|---|---|
| `framework/config.yaml` | Every declared choice: subsets, features, model families, grids, folds, bootstrap, seed |
| `framework/data_loader.py` | Verify the dataset hash, load, join the two maps, apply the subset predicates |
| `framework/features.py` | The one-tissue-one-row rule, subsets A and B, duration basis functions, the design matrix |
| `framework/cv.py` | Leave-one-cohort-out splitting and the leakage guard |
| `framework/tier1.py` | **New.** The three-level meta-regression: marginal likelihood, GLS, cluster-robust sandwich |
| `framework/sensitivity.py` | **New.** The declared sensitivity analyses; S6 is implemented |
| `framework/models.py` | The duration-only baseline in three forms, plus the four comparative families |
| `framework/evaluate.py` | Fold metrics, campaign-weighted aggregates, the campaign bootstrap, pooled R² |
| `framework/explain.py` | SHAP for tree models, permutation importance elsewhere, fold-stability table |
| `framework/fetch_nasa_nlsp.py` | **New.** Downloads the open NASA NLSP bed-rest folders and records every file's UUID and SHA-256 |
| `framework/extract_nasa.py` | **New.** Turns the one poolable NASA campaign into schema rows, and refuses the rest by name |
| `framework/run_tier1.py` | **New.** Fits both subsets, writes `results/tier1_curve.json` and `results/tier1_muscle_ranking.csv` |
| `framework/run_baseline.py` | Fits the baseline, writes `results/baseline.json` |
| `framework/run_models.py` | Runs the four families with nested tuning, writes `results/model_comparison.*` |
| `framework/forecast.py` | **New.** Tier 3: the ranges, what the model is shown and the assertions guarding it, the point, interval and proper scores |
| `framework/typesafe_client.py` | **New.** Calls TypeSafe, retried with backoff, and caches every answer under a hash of its request |
| `framework/run_forecast.py` | **New.** Runs tier 3's two arms against matched baselines, writes `results/forecast*` |
| `framework/run_ablation.py` | **New.** Tier 3's three ablations and the recognition probe, writes `results/forecast_ablation*` and `results/forecast_recognition.csv` |
| `framework/tests/` | 185 checks in 17 files, run by `make test` |
| `framework/DESIGN.md` | The design document: what is modelled, how it is validated, what may be claimed |

### Results

`results/tier1_curve.json`, `results/tier1_muscle_ranking.csv`, `results/sensitivity.md`,
`results/baseline.json`,
`results/model_comparison.csv`, `results/model_comparison.json`,
`results/importance_stability.csv`, and for tier 3 `results/forecast.json`,
`results/forecast_comparison.csv`, `results/forecast_predictions.csv`, and for its ablations
`results/forecast_ablation.json`, `results/forecast_ablation.csv`,
`results/forecast_ablation_campaigns.csv`, `results/forecast_recognition.csv`. All regenerated by
`make all` from the frozen dataset; tier 3 is rebuilt from the answers committed in
`results/forecast_cache/`, never by calling the API.

## 3. Every number the project currently has

### The modelling subsets

Unloading-phase, lower-limb rows only: **425 rows, 42 studies, 32 campaigns, 13 durations
(5–119 days)**. After the one-tissue-one-row rule:

| Subset | Rows | Campaigns | Used for |
|---|---|---|---|
| A | 346 | 32 | Duration–response. Keeps the 42 whole-segment rows, because seven campaigns report nothing else and they sit at the short durations |
| B | 304 | 25 | Muscle ranking. Named muscles only |

### Tier 1 — the meta-regression *(the primary result)*

Three random intercepts (campaign, study within campaign, muscle within campaign), weighted
by `n_analysed`, fitted by maximum likelihood, intervals cluster-robust on `cohort_id` with
31 degrees of freedom. Subset A, 346 rows, 32 campaigns.

| Duration form | AIC | What it estimates |
|---|---|---|
| **Logarithmic** | **2151.5** | −3.48 pp per e-fold of duration (95% CI −4.70 to −2.25), i.e. **−2.41 pp per doubling** (−3.26 to −1.56) |
| Saturating exponential | 2152.3 | tau 90 days, eventual loss −19.9% (−24.8 to −15.0) |
| Restricted cubic spline | 2152.2 | Shape check only |

**All three land within one AIC point of each other**, so the data do not distinguish between
them. The declared rule (DESIGN.md §7.1) keeps the saturating form as the headline, and the
spline shows no shape the parametric forms miss. Two things to say out loud when quoting it:
the profiled tau stopped at the **top of the declared grid**, so the curve is still falling at
the longest observation and the −19.9% asymptote is an extrapolation past 119 days rather than
a plateau in the data; and the curve is drawn for one scenario — a control arm, the reference
muscle family, the reference modality, not a composite.

The fitted curve at the reference scenario:

| Day | 5 | 14 | 30 | 60 | 90 | 119 |
|---|---|---|---|---|---|---|
| Loss | −4.3% | −5.8% | −8.1% | −11.4% | −13.8% | −15.5% |
| 95% CI | −7.9 to −0.7 | −9.3 to −2.2 | −11.7 to −4.5 | −15.2 to −7.6 | −17.8 to −9.8 | −19.7 to −11.3 |

**Where the variance sits**, which is the number that explains the whole validation design:
59% residual, **23% between muscles within a campaign**, 9% between campaigns, 9% between the
papers inside one.

### The muscle ranking, with intervals

Subset B, 304 rows, 25 campaigns, same specification. Contrasts are against **knee
extensors** — chosen, not inherited: 86 rows across 22 campaigns make it the tightest anchor
in the table, and every contrast inherits the reference's uncertainty. The predicted column is
the model's fitted change at 60 days for a control arm.

| Family | Rows | Campaigns | At 60 days (95% CI) | vs knee extensors | p |
|---|---|---|---|---|---|
| Plantar flexors | 78 | 13 | **−15.2%** (−19.1 to −11.3) | −5.82 pp | 0.002 |
| Dorsiflexors | 8 | 4 | −9.5% (−13.9 to −5.1) | −0.16 pp | 0.90 |
| Knee extensors | 86 | 22 | −9.3% (−14.2 to −4.5) | reference | — |
| Knee flexors | 54 | 7 | −9.3% (−12.7 to −5.9) | +0.08 pp | 0.95 |
| Hip abductors | 6 | 1 | −9.0% (−11.4 to −6.6) | +0.34 pp | 0.83 |
| Hip flexors | 13 | 4 | −6.1% (−10.5 to −1.7) | +3.25 pp | 0.07 |
| Hip extensors | 8 | 3 | −5.6% (−10.6 to −0.5) | +3.77 pp | 0.04 |
| Hip adductors | 39 | 4 | −4.7% (−8.5 to −0.9) | +4.65 pp | 0.002 |
| Hip rotators | 12 | 1 | −1.1% (−4.2 to +2.0) | +8.24 pp | <0.001 |

**The antigravity comparison is reported independently of the reference:** plantar flexors
against dorsiflexors is **−5.66 pp** (95% CI −9.04 to −2.28, p = 0.002), computed from the
coefficient difference so that changing the reference cannot change it.

This is claim 2 as a coefficient rather than an unadjusted mean: plantar flexors lose
significantly more than the quadriceps, hip rotators significantly less, and the whole
ordering survives adjustment for duration, arm and modality. Two rows rest on a single
campaign each — hip abductors and hip rotators — and the campaign column is there so nobody
quotes them as if they did not.

Countermeasure arms lose **3.34 pp less** than control arms (95% CI 1.52 to 5.15, p = 0.001),
which is the first countermeasure effect the project has estimated rather than described.

### S6 — does the weighting scheme matter?

`DESIGN.md` §7.2 weights rows by `n_analysed`. The classical alternative weights by the
inverse of each estimate's variance, and it needs a dispersion **of the change** — which only
**161 of 346 rows, from 8 of 32 campaigns**, carry. Most papers print the spread of the
baseline, or nothing.

| Analysis | Weights | Rows | Campaigns | Duration coefficient (95% CI) | LOCO MAE |
|---|---|---|---|---|---|
| Primary | `n_analysed` | 346 | 32 | −16.49 (−20.49 to −12.49) | 3.47 pp |
| Restricted to rows with a change dispersion | `n_analysed` | 161 | 8 | −13.94 (−18.62 to −9.26) | 2.81 pp |
| **S6** — the same rows | inverse variance | 161 | 8 | −11.57 (−14.18 to −8.97) | 2.88 pp |

The middle row exists so the comparison is fair: the restriction alone moves the coefficient
by 2.6 pp, and the weighting moves it another 2.4 pp. **The scheme is not neutral, and eight
campaigns cannot adjudicate between the two** — the intervals overlap throughout. The sentence
for the report is that inverse-variance weighting is unavailable as a primary scheme on this
literature, not that it was tried and made no difference.

### The baseline — muscle loss against duration, nothing else

Leave-one-cohort-out, weighted by campaign.

| Curve shape | Out-of-cohort MAE | 95% CI | Pooled R² |
|---|---|---|---|
| Linear in days | 3.62 pp | 2.89–4.39 | −0.08 |
| **Logarithmic** | **3.21 pp** | 2.45–4.05 | 0.03 |
| Saturating exponential | 3.32 pp | 2.54–4.14 | 0.06 |

Fitted saturating curve: time constant 10 days, eventual loss −9.3% averaged across all
muscles in subset A.

### The four comparative families

Hyperparameters tuned by a campaign-grouped search inside each training fold.

| Model | Out-of-cohort MAE | 95% CI | vs baseline | Pooled R² |
|---|---|---|---|---|
| Duration-only curve | 3.21 pp | 2.45–4.05 | — | 0.03 |
| Support vector regression | 3.22 pp | 2.48–3.98 | −0.4% | 0.22 |
| Random forest | 3.34 pp | 2.59–4.13 | −4.1% | 0.19 |
| Gradient boosting | 3.38 pp | 2.67–4.14 | −5.3% | 0.10 |
| Ridge regression | 3.56 pp | 2.86–4.35 | −11.0% | 0.18 |

**No family beats the curve.** `PLAN.md` §8 set the bar at a 15% relative improvement and
pre-committed to reporting the outcome either way. This is rung B of the fallback ladder.

Worst fold for every family: `wise2005` (MAE 9.0–9.4 pp) — 60 days, women only.

### Tier 3 — the TypeSafe forecast *(added 21 Sep, after the null result; not pre-registered)*

TypeSafe's Jev (`jev-1.13.0`) is shown each row's participants, protocol, countermeasure and
measurement in words, the curve fitted to the other campaigns, and as many of their
observations as fit 26,000 tokens, and gives a probability for every declared range. Code
turns that into a point, a most probable range and scores. Names of papers, authors and
campaigns are never sent. `DESIGN.md` §9.3 has the method and §9.3.1 the full reading.

Both arms run on the **day of the scan**, and so do their baselines - see §8 for why that
matters for tiers 1 and 2.

| Arm | Model | MAE | 95% CI | CRPS | 80% range covers | Pooled R² |
|---|---|---|---|---|---|---|
| Without history (346 rows, 32 campaigns) | **Jev** | **2.71 pp** | 2.12–3.33 | **2.05** | 62% | 0.43 |
| | Duration curve | 3.13 pp | 2.37–3.92 | 2.49 | 90% | 0.14 |
| With history (84 rows, 5 campaigns) | **Jev** | **2.84 pp** | 2.19–3.50 | 2.21 | 38% | 0.19 |
| | Last scan plus the curve's step | 3.21 pp | 2.58–3.87 | **2.16** | 77% | 0.02 |

Paired against the curve, Jev's error is lower by **0.42 pp (95% CI 0.13 to 0.73)**, in 20 of
32 campaigns - the first advantage in the project whose paired interval excludes zero. It
still **misses the declared 15% MAE bar** (13.3% and 11.5%), meets the CRPS bar only without
history, and its ranges are **overconfident** in both arms.

**Is it signal or recognition?** More than half the gain came from three much-published
campaigns, so ablations were declared (`DESIGN.md` §9.3.2) and run the same day (§9.3.3):

| Variant | MAE | Paired gain over the curve |
|---|---|---|
| Full | 2.71 pp | +0.42 (0.13 to 0.73) |
| Generic - no participants, protocol text or planned length | 2.83 pp | **+0.30 (0.02 to 0.61)** |
| Reference values shuffled | 4.37 pp | −1.24 (−1.94 to −0.58) |
| No reference data | 5.83 pp | −2.71 (−3.57 to −1.73) |

The gain survives without anything that identifies a study, disappears when the reference
values are shuffled, and the model cannot name two of the three campaigns carrying it (only
NASA SPRINT; ρ = 0.38 between recognition and gain). By the declared rules, **tier 3's point
forecasts may be quoted as a result**, with the caveats above.

### The classification sanity check

Unadjusted control-arm means by functional class, which is why the muscle map is believable
before anyone signs it off:

| Class | Rows | Mean change |
|---|---|---|
| Antigravity extensors | 129 | −12.0% |
| Mixed | 137 | −6.7% |
| Flexors | 33 | −6.1% |

By family, worst first: plantar flexors −14.7%, evertors −12.2%, knee extensors −8.7%,
knee flexors −7.8%, dorsiflexors −7.5%, hip adductors −4.1%, hip rotators −1.3%.

### Feature stability

Across the 32 folds, only `duration` reaches the top three in more than two-thirds of them
(69%). Nothing else is stable. Importance is therefore presented as indicative, with the
stability table shown rather than a bar chart.

## 4. What the numbers mean

Three claims the evidence currently supports, in order of how well it supports them.

1. **Muscle loss follows a curved, not linear, path against unloading duration, at about
   −2.4 pp per doubling of days** (95% CI −3.3 to −1.6). The straight line is the worst of the
   baseline's three forms, and tier 1 now attaches an interval to the curve. What tier 1 also
   shows is that the corpus cannot say *which* curve: log, saturating and spline sit within
   one AIC point of each other.
2. **Which muscle you ask about matters more than anything else in the dataset.** Pooled R²
   goes from 0.03 with duration alone to about 0.20 once muscle identity enters, and tier 1
   turns that into coefficients: plantar flexors −5.7 pp against the reference family
   (p = 0.002), hip rotators +8.4 pp (p < 0.001), 23% of all variance sitting between muscles
   within a campaign. Antigravity extensors lose roughly twice what flexors lose.
3. **At 32 campaigns, flexible models add nothing to a simple curve.** They find the same
   structure and do not convert it into lower error, because the residual is dominated by
   between-campaign differences no feature in this dataset explains. That is a statement about
   the published literature, not about the algorithms.

## 5. Decisions taken in this phase, and why

| Decision | Reason |
|---|---|
| Muscle function assigned by mechanical role first, fibre type second | Tibialis anterior is ~73% slow fibres but does not bear weight; the corpus says role, not fibre type, predicts atrophy. Assignment is in a reviewable CSV, not in code |
| Two subsets rather than one | Excluding whole-segment rows for a cleaner muscle vocabulary would cost six campaigns *and* the short-duration end of the curve, where it bends hardest |
| Components beat composites within a measurement occasion | Schema rule 4 — the same tissue must not enter a model twice. `is_composite` stays as a feature so mixed granularity is visible to the model |
| R² pooled across folds, not averaged over them | Most campaigns ran one duration, so a duration-only model predicts one value inside a fold and loses to that fold's own mean by construction: −8.5 per fold against +0.06 pooled, from identical predictions |
| Hyperparameters tuned inside the training fold, grouped by campaign | Tuning against the outer fold is the one mistake here that cannot be repaired afterwards |
| The reference muscle family is knee extensors, chosen rather than alphabetical | Every contrast inherits the reference's uncertainty, and dorsiflexors carried 8 rows from 4 campaigns against the quadriceps' 86 from 22. The antigravity comparison is reported as its own contrast so that the choice cannot change it |
| Inverse-variance weighting is a sensitivity analysis, not the primary scheme | Only 160 of 342 rows carry a dispersion of the change. Making it primary would trade 24 campaigns for a textbook weighting |
| SHAP only where it is exact | Tree ensembles get real SHAP values; SVR and ridge get permutation importance, and every output names which was used. A permutation plot must never be labelled SHAP |
| Tier 1 written out and fitted by maximum likelihood, not by `statsmodels` | `MixedLM` carries two levels; the third and the cluster-robust sandwich would have been built on top of it anyway. Every random effect nests inside a campaign, so the covariance is block diagonal and the likelihood is a sum over 31 small blocks. It also keeps the primary result on numpy, pandas and scipy |
| Maximum likelihood, not REML | The three duration forms do not share a design matrix, and restricted likelihoods cannot be compared across them. The price is a mild downward bias in the variance components at 31 campaigns; the alternative is an AIC table that means nothing |
| The tau grid stays as declared, confirmed 19 September | It is a declared choice from P3, and re-declaring it after reading the answer is how a pre-registration becomes decoration. The result file flags the edge instead, and widening the grid is a decision to take deliberately |
| The virtual environment lives outside the Drive folder | The mount refuses the symlinks `venv` needs (`Errno 5` on `lib64`). A venv also carries absolute paths and compiled binaries, so it would not travel between machines regardless. `requirements.txt` and `make venv` are what travel |

## 6. How to run it

```bash
make venv                                   # creates ~/.venvs/dglrm from requirements.txt
PYTHON=~/.venvs/dglrm/bin/python make all   # tests, tier 1, S6, baseline, four models
```

`make test` alone runs the 185 checks. `make forecast` and `make ablation` rebuild tier 3 from the answer cache;
`make forecast-live` asks TypeSafe for any answer the cache lacks and needs `TYPESAFE_API_KEY`. `make tier1`, `make sensitivity`, `make baseline`
and `make models` regenerate one set of results each. The loader refuses to run if `dataset_v1.1.csv` no longer matches its
recorded hash, so no result can quietly come from an edited dataset.

The core — loading, features, folds, baseline, evaluation and **tier 1** — needs only numpy,
pandas, scipy and PyYAML. Only the four comparative families and SHAP need the optional
stack, which is deliberate: the primary result must not depend on the part of the project
that produced a null one.

## 7. Repository state

| Branch | Commit | State |
|---|---|---|
| `main` | `f8e42e6` | P1 and P2 merged. Carries the frozen dataset and the whole literature record |
| `feat/ai-framework` | tip | 25 commits ahead of `main` — the entire P3/P4 framework, tier 1 included. **Not yet merged** |
| `feat/nasa-open-data` | tip | The NLSP fetcher and the downloaded archive with its card. **Not yet merged** |
| `feat/nasa-integration` | tip | `feat/ai-framework` plus the NASA archive, `dataset_v1.1`, and every result refitted. **Not yet merged** |
| `feat/tabpfn` | tip | TabPFN as a fifth tier-2 family, fitted against `dataset_v1.0` before tier 1. **Not merged**, and not in `feat/nasa-integration` |
| `feat/typesafe-forecast` | tip | `feat/nasa-integration` plus tier 3, its results and its answer cache. **Not yet merged** |
| `feat/literature-review` | merged | Closed by the P1 merge |
| `feat/integration` | merged | Closed by the P2 merge |
| `chore/line-endings` | merged | Line-ending pin and the handoff packager |
| `feat/report-slides` | at old `main` | Untouched, for P5 |

Tags `dataset-v1.0` and `dataset-v1.1` mark the two frozen datasets. No `results-v1.1` tag yet — see
`NEXT_SESSION.md` item 3. One more thing this mount does: a stale, empty
`.git/packed-refs.lock` appears now and then and makes every commit print a scary message
after it has already succeeded. Delete it when no git process is running.

Two housekeeping notes. The working tree keeps reverting text files to CRLF when the Drive
folder syncs from a Windows machine; `.gitattributes` now pins LF, so `git checkout -- .`
clears the noise if it reappears. And git occasionally reports `short read while indexing` on
this mount — that is Drive sync, not corruption; `git fsck` has come back clean each time.

## 8. What is not done

| Gap | Consequence |
|---|---|
| **Tiers 1 and 2 use the campaign's planned length, not the day of the scan** | `duration_days` is the planned total; `timepoint_days` is when the scan was taken. 200 of the 346 rows in subset A were scanned before bed rest ended, about 120 of them more than a week early, and all of them enter tiers 1 and 2 at the full planned length. Refitting the baseline on the scan day moves pooled R² from 0.03 to 0.14, the loss at 90 days from −9.9% to −11.9% and the saturating time constant from 10 to 35 days. The headline curve probably moves too. Undecided; tier 3 already uses the scan day |
| Tier 3's ranges are overconfident | Its 80% ranges hold the truth 62% (without history) and 38% (with) of the time. Quote its point forecasts, not its ranges, until a recalibration rule is declared and run |
| Tier 3's gain has no tested mechanism | The ablations show what it does not need - anything identifying a study - and that it reads the reference values. Why that beats tier 2 is an interpretation (`DESIGN.md` §9.3.3), not a result |
| **No figures exist** | F1–F5 in `PLAN.md` §9 are all outstanding, including the framework diagram (task 3.2), which is the slide carrying the whole AI contribution |
| Sensitivity analyses S1–S5 and S7–S11 not run | S1, S2 and S4 are pre-registered as must-show in the report. S6 is done |
| The muscle map has no physiological sign-off | Numbers can be computed but not yet quoted. Partner review is a line edit in one CSV |
| `feat/ai-framework` is not merged into `main` | P3 and P4 are not formally closed |
| The muscle ranking is not sex-stratified (S9) and carries no age term (S8) | Two questions the audience is likely to ask |
| No extrapolation to 180 days | `PLAN.md` task 4.7, a backup slide. Tier 1 makes it computable, and §10 of `DESIGN.md` governs what may be said about it |
| The tau profile stops at the top of its grid | The saturating asymptote is an extrapolation past 119 days, not a plateau. Either widen the grid deliberately or quote the curve only inside the observed range |
| DGLRM author instructions still unknown | `PLAN.md` task 0.2, outstanding since kickoff |
| **No `LICENSE` file** | The repository is public but not open source: without one, a reader has no right to use the code or the dataset. `docs/licensing.md` §5 |
| **`data/search/fulltext_digests/` reproduces paper text verbatim** | 68 committed files of tables and sentences copied from papers; at least 30 come from closed, bronze or green-OA articles that grant no reuse right. Blocks making the repository public. `docs/licensing.md` §2 |
| NASA is not acknowledged as a data source | NASA asks to be credited and nothing in the repository does it yet. `docs/licensing.md` §3 |
| The `repository` value added to `data_source` has one lead's signature, not two | `data/schema.md` is frozen and says a change needs both. README open question 1.1 |
| `extraction_figures.csv` fails `validate_extraction.py` without `--partial` | Pre-existing, not caused by v1.1: 23 rows lack `sex` or an age. It validates cleanly in partial mode, so either the file is a partial table and the runner should say so, or the rows need filling |
