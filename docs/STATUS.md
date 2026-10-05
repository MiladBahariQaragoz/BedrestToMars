# Project status — 2026-09-21

Where "From Bed Rest to Mars" stands, what exists on disk, and what every number currently
says. Written at the end of the P3/P4 modelling work so the next person to open the
repository — including a future version of either of us — can start without re-deriving
anything. Updated on 19 September, when tier 1 was implemented and fitted, and again the
same day when `dataset_v1.1` pooled one campaign from NASA's open bed-rest archive and every
result below was refitted against it. Updated again on 21 September, when tier 3 - a
TypeSafe language-model forecast - was added and run on its own branch,
`feat/typesafe-forecast`; the same day tiers 1 and 2 were refitted on the day of the scan,
tier 3 was ablated and validated, figures F1–F9 were drawn, the written report's first draft
was built, and TabPFN was ported from `feat/tabpfn` and rerun as a post-hoc fifth tier-2 family.

**Next actions live in [`NEXT_SESSION.md`](NEXT_SESSION.md).**

---

## 1. Phase status against the plan

| Phase | Planned | State |
|---|---|---|
| P0 Kickoff | Sep 4 | **Done.** Repository, branches, frozen schema, screening decisions |
| P1 Literature research | Sep 5–11 | **Done.** 5731 records identified, screened, extracted; merged into `main` |
| P2 Integration | Sep 12–14 | **Done.** Reconciled, QC'd, `dataset_v1.0` frozen and tagged; merged into `main`. `dataset_v1.1` followed on Sep 19 |
| P3 Framework design | Sep 15 | **Done** (late, completed Sep 18). `framework/DESIGN.md`, config, six modules, baseline |
| P4 Run the framework | Sep 16–21 | **Mostly done.** Tier 1 fitted (Sep 19) and refitted on the day of the scan (Sep 21); tier 2 a null result; tier 3, a TypeSafe forecast, run, ablated and validated (Sep 21, §3); TabPFN run as a post-hoc fifth tier-2 family, also a null result (Sep 21). Sensitivity analyses S1–S5 and S7–S11 and the extrapolation not yet run |
| P5 Report and slides | Sep 22–28 | **Started early.** Figures F1–F9 are drawn from the results (Sep 21); the written report's first full draft is `report/main.pdf` (Sep 21), on `feat/report`, PR #1. The deck is not started |
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
| `framework/run_tabpfn.py` | **New.** The post-hoc fifth family, TabPFN, on the same folds and baseline, in its own environment. Writes `results/tabpfn_comparison.*` |
| `framework/forecast.py` | **New.** Tier 3: the ranges, what the model is shown and the assertions guarding it, the point, interval and proper scores |
| `framework/typesafe_client.py` | **New.** Calls TypeSafe, retried with backoff, and caches every answer under a hash of its request |
| `framework/run_forecast.py` | **New.** Runs tier 3's two arms against matched baselines, writes `results/forecast*` |
| `framework/run_ablation.py` | **New.** Tier 3's three ablations and the recognition probe, writes `results/forecast_ablation*` and `results/forecast_recognition.csv` |
| `framework/run_validation.py` | **New.** Tier 3's validation battery: history-arm ablations, presentation checks, repeats. Writes `results/forecast_validation*` and `results/forecast_repeats.json` |
| `framework/plot_figures.py` | **New.** Draws F1–F9 from the results files, writes `figures/*.svg` and `*.png` |
| `framework/tests/` | 234 checks in 20 files, run by `make test` |
| `framework/DESIGN.md` | The design document: what is modelled, how it is validated, what may be claimed |

### Results

`results/tier1_curve.json`, `results/tier1_muscle_ranking.csv`, `results/sensitivity.md`,
`results/baseline.json`,
`results/model_comparison.csv`, `results/model_comparison.json`,
`results/importance_stability.csv`, and for tier 3 `results/forecast.json`,
`results/forecast_comparison.csv`, `results/forecast_predictions.csv`, and for its ablations
`results/forecast_ablation.json`, `results/forecast_ablation.csv`,
`results/forecast_ablation_campaigns.csv`, `results/forecast_recognition.csv`, and for its
validation `results/forecast_validation.json`, `results/forecast_validation.csv`,
`results/forecast_repeats.json`, and for the post-hoc TabPFN family
`results/tabpfn_comparison.csv` and `results/tabpfn_comparison.json`. The figures are in `figures/`. All regenerated by
`make all` from the frozen dataset, except TabPFN, which `make tabpfn` rebuilds in its own environment; tier 3 is rebuilt from the answers committed in
`results/forecast_cache/`, never by calling the API.

## 3. Every number the project currently has

### The modelling subsets

Unloading-phase, lower-limb rows only: **425 rows, 42 studies, 32 campaigns, scans on 24
distinct days (5–119)**. Since 21 September every tier measures unloading at the **day of the
scan**, `timepoint_days`, not at the campaign's planned length (`DESIGN.md` §9.4). After the
one-tissue-one-row rule:

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
| Logarithmic | 2087.0 | −4.31 pp per e-fold of duration (95% CI −4.96 to −3.65), i.e. **−2.99 pp per doubling** (−3.44 to −2.53) |
| **Saturating exponential** | **2085.9** | tau **60 days**, eventual loss **−17.3%** (−20.9 to −13.7) |
| Restricted cubic spline | 2085.7 | Shape check only |

**The three forms land within 1.3 AIC points of each other**, so the data still do not
distinguish between them. The declared rule (DESIGN.md §7.1) keeps the saturating form as the
headline, and the spline shows no shape the parametric forms miss. Measured on the day of the
scan, the fit is better by about 65 AIC points on the same rows (2152 against 2086 for the
saturating form), and the time constant now lands at 60 days, inside the declared grid rather
than at its edge. By day 119 the curve is 86% of the way to its eventual loss, so the −17.3% is
an estimate at the edge of the data, not far beyond it. The curve is drawn for one scenario —
a control arm, the reference muscle family, the reference modality, not a composite.

The fitted curve at the reference scenario:

| Day | 5 | 14 | 30 | 60 | 90 | 119 |
|---|---|---|---|---|---|---|
| Loss | −4.2% | −6.0% | −8.6% | −12.0% | −14.1% | −15.3% |
| 95% CI | −7.3 to −1.0 | −9.1 to −2.9 | −11.8 to −5.5 | −15.3 to −8.8 | −17.5 to −10.7 | −18.8 to −11.9 |

**Where the variance sits**, which is the number that explains the whole validation design:
54% residual, **30% between muscles within a campaign**, 11% between campaigns, 4% between the
papers inside one.

### The muscle ranking, with intervals

Subset B, 304 rows, 25 campaigns, same specification. Contrasts are against **knee
extensors** — chosen, not inherited: 86 rows across 22 campaigns make it the tightest anchor
in the table, and every contrast inherits the reference's uncertainty. The predicted column is
the model's fitted change at 60 days for a control arm.

| Family | Rows | Campaigns | At 60 days (95% CI) | vs knee extensors | p |
|---|---|---|---|---|---|
| Plantar flexors | 78 | 13 | **−15.8%** (−18.9 to −12.7) | −5.69 pp | 0.001 |
| Dorsiflexors | 8 | 4 | −10.2% (−13.2 to −7.1) | −0.09 pp | 0.95 |
| Knee extensors | 86 | 22 | −10.1% (−13.6 to −6.6) | reference | — |
| Knee flexors | 54 | 7 | −9.8% (−12.1 to −7.6) | +0.28 pp | 0.83 |
| Hip abductors | 6 | 1 | −9.1% (−11.2 to −6.9) | +1.01 pp | 0.44 |
| Hip flexors | 13 | 4 | −6.8% (−9.9 to −3.6) | +3.33 pp | 0.06 |
| Hip extensors | 8 | 3 | −6.1% (−10.1 to −2.0) | +4.03 pp | 0.02 |
| Hip adductors | 39 | 4 | −5.4% (−7.9 to −2.9) | +4.70 pp | 0.001 |
| Hip rotators | 12 | 1 | −1.9% (−4.0 to +0.2) | +8.22 pp | <0.001 |

**The antigravity comparison is reported independently of the reference:** plantar flexors
against dorsiflexors is **−5.60 pp** (95% CI −9.13 to −2.07, p = 0.003), computed from the
coefficient difference so that changing the reference cannot change it.

This is claim 2 as a coefficient rather than an unadjusted mean: plantar flexors lose
significantly more than the quadriceps, hip rotators significantly less, and the whole
ordering survives adjustment for duration, arm and modality. Two rows rest on a single
campaign each — hip abductors and hip rotators — and the campaign column is there so nobody
quotes them as if they did not.

Countermeasure arms lose **3.73 pp less** than control arms (95% CI 1.54 to 5.93, p = 0.002),
which is the first countermeasure effect the project has estimated rather than described.

### S6 — does the weighting scheme matter?

`DESIGN.md` §7.2 weights rows by `n_analysed`. The classical alternative weights by the
inverse of each estimate's variance, and it needs a dispersion **of the change** — which only
**161 of 346 rows, from 8 of 32 campaigns**, carry. Most papers print the spread of the
baseline, or nothing.

| Analysis | Weights | Rows | Campaigns | Duration coefficient (95% CI) | LOCO MAE |
|---|---|---|---|---|---|
| Primary | `n_analysed` | 346 | 32 | −14.25 (−16.40 to −12.11) | 3.34 pp |
| Restricted to rows with a change dispersion | `n_analysed` | 161 | 8 | −14.51 (−15.61 to −13.42) | 2.67 pp |
| **S6** — the same rows | inverse variance | 161 | 8 | −13.60 (−16.69 to −10.50) | 2.82 pp |

The middle row exists so the comparison is fair. On the day of the scan the restriction moves
the coefficient by 0.3 pp and the weighting by another 0.9 pp, with the intervals overlapping
throughout: here the scheme barely matters. The sentence for the report is still that
inverse-variance weighting is unavailable as a primary scheme on this literature - eight
campaigns carry what it needs - not that it was tried and chosen against.

### The baseline — muscle loss against duration, nothing else

Leave-one-cohort-out, weighted by campaign.

| Curve shape | Out-of-cohort MAE | 95% CI | Pooled R² |
|---|---|---|---|
| Linear in days | 3.40 pp | 2.66–4.19 | 0.07 |
| **Logarithmic** | **3.16 pp** | 2.44–3.93 | 0.14 |
| Saturating exponential | 3.19 pp | 2.46–3.98 | 0.12 |

Fitted saturating curve: time constant 35 days, eventual loss −13.0% averaged across all
muscles in subset A.

### The four comparative families

Hyperparameters tuned by a campaign-grouped search inside each training fold.

| Model | Out-of-cohort MAE | 95% CI | vs baseline | Pooled R² |
|---|---|---|---|---|
| Duration-only curve | 3.16 pp | 2.44–3.93 | — | 0.14 |
| Random forest | 3.18 pp | 2.50–3.91 | −0.7% | 0.34 |
| Support vector regression | 3.28 pp | 2.67–3.92 | −3.7% | 0.36 |
| Ridge regression | 3.28 pp | 2.59–4.02 | −3.8% | 0.27 |
| Gradient boosting | 3.34 pp | 2.68–4.07 | −5.9% | 0.30 |
| *TabPFN, post hoc* | *3.22 pp* | *2.51–3.97* | *−2.1%* | *0.39* |

**No family beats the curve.** `PLAN.md` §8 set the bar at a 15% relative improvement and
pre-committed to reporting the outcome either way. This is rung B of the fallback ladder.

Worst fold: `liphardt_br21` for three families (MAE 7.8–7.9 pp), `wise2005` for ridge (8.6 pp).

**TabPFN, the post-hoc fifth family** (`DESIGN.md` §9.2.1), is a transformer pretrained for small tables, run on fixed
defaults on the same folds and baseline in its own environment (tabpfn 2.0.9 needs scikit-learn below 1.7; the four
families were fitted with 1.8), writing `results/tabpfn_comparison.*`. It lands second of five, 2.1% worse than the
curve, with the highest pooled R² of any family (0.39) and the same worst fold, `liphardt_br21` (7.6 pp). The null
result now has a fifth, very different witness. The first run on `feat/tabpfn`, against v1.0 and the planned-length
axis (3.25 pp, R² 0.03), is superseded.

### Tier 3 — the TypeSafe forecast *(added 21 Sep, after the null result; not pre-registered)*

TypeSafe's Jev (`jev-1.13.0`) is shown each row's participants, protocol, countermeasure and
measurement in words, the curve fitted to the other campaigns, and as many of their
observations as fit 26,000 tokens, and gives a probability for every declared range. Code
turns that into a point, a most probable range and scores. Names of papers, authors and
campaigns are never sent. `DESIGN.md` §9.3 has the method and §9.3.1 the full reading.

Both arms run on the **day of the scan**, as tiers 1 and 2 now do too. The curve reads
3.13 pp here and 3.16 pp in the tier-2 table because here its point is the mean of its forecast
distribution, the same definition the model's point uses.

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
| Generic - no participants, protocol text or planned length | 2.82 pp | **+0.30 (0.01 to 0.62)** |
| Reference values shuffled | 4.37 pp | −1.25 (−1.94 to −0.59) |
| No reference data | 5.85 pp | −2.72 (−3.58 to −1.76) |

The gain survives without anything that identifies a study, disappears when the reference
values are shuffled, and the model cannot name two of the three campaigns carrying it (only
NASA SPRINT; ρ = 0.37 between recognition and gain). By the declared rules, **tier 3's point
forecasts may be quoted as a result**, with the caveats above.

**Does it hold up?** A validation battery was declared (`DESIGN.md` §9.3.4) and run the same
day (§9.3.5), leave-one-campaign-out throughout:

- The result without history **survives both presentation checks**: reordered reference rows
  keep a gain of 0.34 pp (0.07 to 0.62), ranges shifted half a step 0.45 pp (0.15 to 0.78).
- **Answers are not identical between runs** - none of 20 repeats matched - but a forecast
  moves by about 0.17 pp and the error on the repeated rows by 0.02 pp, far below the 0.42 pp
  gain.
- On the history arm the model **does not read the earlier scans**: shuffling them leaves the
  error unchanged. The earlier scans help every method a great deal (Jev 5.83 → 2.84 pp on the
  same rows, the baselines 7.27 → 3.21), but through the anchor the code adds, not through the
  model.

Quote tier 3 from the arm without history, say that repeated runs differ slightly, and say
nothing about the model using a campaign's history.

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

Importance is SHAP on the random forest, the best-scoring family. Two features are stable
across the 32 folds: `duration` reaches the top three in 91% of them and plantar flexors in
88%. The third place moves between the countermeasure arm (59%) and `is_composite` (53%), so
the `PLAN.md` §8 bar - the same top three in 80% of folds - is missed. The stability table is
shown rather than a bar chart, and the top two can be stated.

## 4. What the numbers mean

Four claims the evidence currently supports, in order of how well it supports them.

1. **Muscle loss follows a curved, not linear, path against days of bed rest, at about
   −3.0 pp per doubling of days** (95% CI −3.4 to −2.5); at day 60 the curve for the reference
   scenario sits at −12%. The straight line is the worst of the baseline's three
   forms. What tier 1 also shows is that the corpus cannot say *which* curve: log, saturating
   and spline sit within 1.3 AIC points of each other.
2. **Which muscle you ask about matters more than anything else in the dataset.** Pooled R²
   goes from 0.14 with duration alone to 0.27–0.36 once muscle identity enters, and tier 1
   turns that into coefficients: plantar flexors −5.7 pp against the reference family
   (p = 0.001), hip rotators +8.2 pp (p < 0.001), 30% of all variance sitting between muscles
   within a campaign. Antigravity extensors lose roughly twice what flexors lose.
3. **At 32 campaigns, tabular learners add nothing to a simple curve** - not the four declared families,
   and not TabPFN, a network pretrained for small tables, added post hoc. They find the same
   structure and do not convert it into lower error, because the residual is dominated by
   between-campaign differences no column in this dataset explains. That is a statement about
   the published literature, not about the algorithms.
4. **A model that reads the other campaigns' data in context does add a little** (tier 3):
   0.42 pp less error than the curve (95% CI 0.13 to 0.73), surviving the removal of anything
   that identifies a study. It is below its declared bar, it was not pre-registered, and its
   ranges are overconfident - so it is a finding to report, not the headline.

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
| The tau grid stays as declared, confirmed 19 September | It is a declared choice from P3, and re-declaring it after reading the answer is how a pre-registration becomes decoration. On the day of the scan (21 September) the profile turns over at 60 days, inside the grid, so the question no longer arises |
| Unloading is measured at the day of the scan, decided 21 September | `duration_days` is the campaign's planned length. It placed 200 of 346 rows - every scan taken before bed rest ended - at the end of their campaign. The fix is a correction of the implementation, not a new analysis choice: `DESIGN.md` already named the timepoint as a within-campaign variable. It is declared as `features.time_column`, and the fit improves by about 65 AIC points |
| The virtual environment lives outside the Drive folder | The mount refuses the symlinks `venv` needs (`Errno 5` on `lib64`). A venv also carries absolute paths and compiled binaries, so it would not travel between machines regardless. `requirements.txt` and `make venv` are what travel |

## 6. How to run it

```bash
make venv                                   # creates ~/.venvs/dglrm from requirements.txt
PYTHON=~/.venvs/dglrm/bin/python make all   # tests, tier 1, S6, baseline, four models
```

`make test` alone runs the 234 checks. `PYTHON_TABPFN=<its venv> make tabpfn` reruns the post-hoc TabPFN family in its own environment. `make figures` redraws F1–F9 and `make validation` rebuilds tier 3's validation battery. `make forecast` and `make ablation` rebuild tier 3 from the answer cache;
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
| `feat/tabpfn` | superseded | TabPFN fitted against `dataset_v1.0` before tier 1. Ported onto `feat/report` on 21 Sep and rerun on v1.1 and the day of the scan; leave unmerged |
| `feat/typesafe-forecast` | tip | `feat/nasa-integration` plus tier 3, its ablations and its answer cache |
| `fix/scan-day-exposure` | tip | `feat/typesafe-forecast` plus the day-of-scan correction and tiers 1 and 2 refitted |
| `feat/figures` | tip | `fix/scan-day-exposure` plus figures F1–F5 |
| `feat/jev-validation` | tip | `feat/figures` plus tier 3's validation battery |
| `feat/jev-figures` | tip | `feat/jev-validation` plus the F1 row funnel and figures F1b and F6–F9 |
| `feat/report` | tip | `feat/jev-figures` plus the written report and the post-hoc TabPFN family. **The tip of the stack; PR #1 into `main`, open** |
| `feat/literature-review` | merged | Closed by the P1 merge |
| `feat/integration` | merged | Closed by the P2 merge |
| `chore/line-endings` | merged | Line-ending pin and the handoff packager |
| `feat/report-slides` | at old `main` | Untouched, for P5 |

The branches from `feat/ai-framework` to `feat/report` form one stack, each built on
the one before, so merging `feat/report` into `main` (PR #1, as a merge commit) closes P3 and P4 in one step.
`feat/tabpfn` sits outside the stack and is superseded.

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
| Tier 3's ranges are overconfident | Its 80% ranges hold the truth 62% (without history) and 38% (with) of the time. Quote its point forecasts, not its ranges, until a recalibration rule is declared and run |
| Tier 3's gain has no tested mechanism | The ablations show what it does not need - anything identifying a study - and that it reads the reference values. Why that beats tier 2 is an interpretation (`DESIGN.md` §9.3.3), not a result |
| Sensitivity analyses S1–S5 and S7–S11 not run | S1, S2 and S4 are pre-registered as must-show in the report. S6 is done |
| The muscle map has no physiological sign-off | Numbers can be computed but not yet quoted. Partner review is a line edit in one CSV |
| The stack ending at `feat/jev-figures` is not merged into `main` | P3 and P4 are not formally closed, and there is no results tag yet |
| Jev's answers are not reproducible bit for bit | Identical requests return slightly different probabilities. The committed cache pins one answer per request and `make` rebuilds from it; a fresh run would move a forecast by about 0.17 pp (`DESIGN.md` §9.3.5) |
| Ten figures against the deck's cap of five | `PLAN.md` §9 allows five in the deck. Which carry the talk and which become backup slides is a decision for both leads |
| Two countermeasure-arm rows carry `cm_modality = none` | Likely an extraction slip. Check before any analysis by countermeasure type |
| The muscle ranking is not sex-stratified (S9) and carries no age term (S8) | Two questions the audience is likely to ask |
| No extrapolation to 180 days | `PLAN.md` task 4.7, a backup slide. Tier 1 makes it computable, and §10 of `DESIGN.md` governs what may be said about it |
| DGLRM author instructions still unknown | `PLAN.md` task 0.2, outstanding since kickoff |
| **No `LICENSE` file** | The repository is public but not open source: without one, a reader has no right to use the code or the dataset. `docs/licensing.md` §5 |
| **`data/search/fulltext_digests/` reproduces paper text verbatim** | 68 committed files of tables and sentences copied from papers; at least 30 come from closed, bronze or green-OA articles that grant no reuse right. Blocks making the repository public. `docs/licensing.md` §2 |
| NASA is not acknowledged as a data source | NASA asks to be credited and nothing in the repository does it yet. `docs/licensing.md` §3 |
| The `repository` value added to `data_source` has one lead's signature, not two | `data/schema.md` is frozen and says a change needs both. README open question 1.1 |
| `extraction_figures.csv` fails `validate_extraction.py` without `--partial` | Pre-existing, not caused by v1.1: 23 rows lack `sex` or an age. It validates cleanly in partial mode, so either the file is a partial table and the runner should say so, or the rows need filling |
