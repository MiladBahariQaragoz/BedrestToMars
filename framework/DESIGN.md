# Framework Design — v1.0

**Status:** P3 deliverable (`PLAN.md` §7, task 3.1), first written against `dataset_v1.0`.
Updated on 2026-09-21 for `dataset_v1.1` (tag `dataset-v1.1`, SHA-256 `dd214c6a…`), for the
day-of-scan correction (§9.4) and for tier 3 (§9.3). The first-run sections, §9.1 and §9.2,
keep their v1.0 numbers as the record of what ran then.
**Branch:** `feat/ai-framework`, continued on `feat/nasa-integration` and the branches stacked
on it (`docs/STATUS.md` §7).
**Supersedes:** nothing. This is the first version, amended in place.

This document specifies what is modelled, how it is validated, and what may be claimed from
the result. It is written to be complete enough that someone outside the team could implement
it from this file and the frozen dataset alone. It is also the source text for the methods
section of the report and the methods slides.

---

## 1. The question

> Given how long a person has been unloaded and which muscle is being asked about, how much
> of that muscle is gone, and how much of the answer depends on anything else?

Two things follow from the way that sentence is written. The prediction is about a group, not
a person, because the underlying literature reports group means. And the framework is judged
on whether it estimates the duration–muscle relationship honestly, not on whether a flexible
model can be made to fit tightly.

## 2. Two tiers, and why

The abstract promises a comparative framework of four model families with
leave-one-study-out validation and SHAP interpretation. That promise is kept in tier 2. But
with 32 independent campaigns in the modelling subset, a flexible learner is being asked to
work at roughly a tenth of the sample size where it starts to behave well
([van der Ploeg et al. 2014](https://doi.org/10.1186/1471-2288-14-137)), so tier 2 cannot be
the primary evidence for anything.

| | Tier 1 — estimation | Tier 2 — comparison |
|---|---|---|
| Question | What is the duration–response, and which muscles deviate from it? | Does a flexible learner find structure the curve misses? |
| Method | Three-level meta-regression, nonlinear in duration | Linear regression, random forest, SVR, gradient boosting |
| Validation | Cluster-robust inference at cohort level | Leave-one-cohort-out cross-validation |
| Reports | Coefficients with confidence intervals | Out-of-cohort MAE, RMSE, R² against the tier-1 curve |
| Status in the talk | The result | The honest test of whether the result needs more machinery |

Tier 1 is the scientific answer and survives every rung of the fallback ladder in `PLAN.md`
§13. Tier 2 is allowed to produce a null result; `PLAN.md` §8 pre-commits to reporting it
either way.

A third tier was added on 21 September, after tier 2's null result: a language model,
TypeSafe's Jev, that reads a description of each held-out campaign alongside the other
campaigns' data and gives a probability for every range of outcome (§9.3). It was not part of
this design as first written, it is reported as a post-hoc addition, and every rule it was
held to was committed before the answer it governs.

## 3. The modelling subset

The frozen dataset holds every row that was extracted, marked but unfiltered, so the subset
is chosen here rather than baked into the file. Three predicates define it, applied in this
order:

| # | Predicate | Rows kept | Reason |
|---|---|---|---|
| 0 | All rows in `dataset_v1.1.csv` | 742 | |
| 1 | `phase == "bed_rest"` | 478 | Recovery answers a different question and enters only the reconditioning sensitivity analysis (schema rule 7) |
| 2 | Lower-limb muscles only — drops `multifidus`, `lumbar_erector_spinae`, `quadratus_lumborum`, `psoas`, `iliopsoas` | 425 | The abstract is about lower-limb atrophy; trunk muscles unload differently and would be answering another question inside the same coefficient |
| 3 | One tissue per measurement occasion (§5) | 346 | A model given both `quadriceps` and its four heads fits the same tissue twice (schema rule 4) |

After predicates 1 and 2: **425 rows, 42 studies, 32 independent cohorts, 13 planned
durations and scans on 24 distinct days (5–119), 299 control and 126 countermeasure rows.**
369 rows are MRI, 29 DXA, 15 CT, 12 ultrasound; 314 are MRI volume specifically.

**The sample size is 32, not 425.** Every design decision below follows from that. The
largest single campaign, the 90-day MEDES study, contributes 103 rows — 24% of the subset —
and the two Berlin campaigns another 106 between them.

### 3.1 Two subsets, because two claims

The talk makes two quantitative claims, and they do not want the same rows.

| | Subset A — duration–response | Subset B — muscle ranking |
|---|---|---|
| Supports | Claim 1: how much is lost by day *t* | Claim 2: which muscles are selectively vulnerable |
| Rows | 346 | 304 |
| Cohorts | **32** | 25 |
| Contents | Everything after predicate 3, including the 42 whole-segment rows (`whole_thigh`, `whole_lower_limb`, `whole_calf`) carried as their own muscle family | Named muscles only |

The difference is worth stating because it is not cosmetic. Seven campaigns — `drummond_br7`,
`imbp_br21`, `lunhab_br10`, `nasa_utmb_c3`, `planhab_br10`, `planhab_br21`, `tanner_br5` —
report *only* whole-segment measurements, and six of them sit at 5 to 21 days, which is
exactly where the duration curve bends hardest. Excluding whole-segment rows to get a cleaner muscle
vocabulary would cost a fifth of the campaigns and the short-duration evidence with them. So
subset A keeps them, with `whole_limb` as an explicit level of `muscle_family`, and subset B —
which is about telling muscles apart — drops them and says so.

Nothing about either subset is hard-coded. `config.yaml` declares each predicate, and every
alternative in §12 is the same pipeline run with one predicate changed.


## 4. The target

`pct_change` — percentage change in muscle size from that arm's own baseline, negative for
loss. Range in the subset: −30.0% to +24.3%. The positive values are real: some
countermeasure arms gain tissue, and a few small muscles grow under compensatory loading.

Two properties of this column matter for the model and must be stated in the methods section
rather than discovered by a reviewer.

**It holds two different estimators.** Where a paper prints the mean of the individual
participants' percentage changes, that is the value. Where it does not, the value is
recomputed from the group mean baseline and follow-up. These are not the same quantity when
the change correlates with baseline size, and each row records which one it carries
(`pct_of_individual_means`, `pct_recomputed_from_group_means`). The estimator therefore
enters the model as a covariate and gets its own sensitivity analysis (§12).

**Its dispersion is heterogeneous and sometimes absent.** 289 rows carry an SD, 88 an SE,
6 a 95% CI, 2 an IQR, and 36 carry nothing. Variance is converted to a common SD scale where
the conversion is exact, and rows without any dispersion keep a missing variance and are
weighted by `n_analysed` alone (§7).

No transformation is applied to the target. Working on the percentage scale keeps the
coefficients directly interpretable as percentage points of muscle lost, which is the unit
the audience thinks in. The nonlinearity goes into the duration term instead (§7).

## 5. One tissue, one row

The dataset deliberately keeps both composite muscles and their components: 189 composite
rows (`quadriceps`, `triceps_surae`, `vasti`, `anterior_tibial_group`, …) and 236 component
rows. On 20 of the 93 measurement occasions in the subset, both are present —
the paper reported the quadriceps *and* its four heads, and a model handed both is fitting
the same tissue twice, inflating its own precision.

`composite_of` is populated on only 50 of the 189 composite rows, so the mapping cannot come
from the data. It lives in [`data/muscle_map.csv`](../data/muscle_map.csv): one line per
muscle giving its family, its functional class, its components where it is a composite, and
a written reason for the assignment. `framework/muscle_map.py` joins it onto the rows at load
time, and refuses to run if the dataset names a muscle the table does not cover.

```
muscle,muscle_family,muscle_function_class,components,fibre_profile,rationale
quadriceps,knee_extensors,antigravity_extensor,rectus_femoris|vastus_lateralis|…,mixed,Principal knee extensor group; resists knee collapse under body weight
soleus,plantar_flexors,antigravity_extensor,,slow_dominant,Monoarticular plantarflexor carrying continuous postural load in stance; roughly 80% type I fibres
rectus_femoris,knee_extensors,mixed,,mixed,Crosses two joints - extends the knee but flexes the hip; loses less than the vasti in bed rest
```

**Resolution rule, applied per measurement occasion** (`cohort_id` × `arm_id` ×
`timepoint_days` × `modality` × `outcome_type`):

1. If components covering a composite are present, keep the components and drop that
   composite. Components carry more information, and 214 of 236 of them carry a baseline
   value, so a composite can be reconstructed from them but not the reverse.
2. Otherwise keep the composite, and record `muscle_grain = "composite"`.
3. Whole-segment rows (`whole_lower_limb`, `whole_thigh`, `whole_calf`) are never decomposed
   and never suppressed by a named muscle in the same occasion. They carry
   `muscle_family = whole_limb`, which keeps them in subset A and out of subset B (§3.1).

Preferring components in step 1 is the aggressive direction: it means the primary model runs
at mixed granularity, since only 12 of the 32 cohorts report components at all. The muscle
random effect in §7 is what makes that legitimate, and §12 runs the opposite preference
(composite-first) to show the conclusion does not depend on the choice.

## 6. Features

The covariate budget is set by the number of cohorts, not the number of rows. Cochrane's
guidance is ten studies per study-level covariate
([Handbook §9.6.4](https://handbook-5-1.cochrane.org/chapter_9/9_6_4_meta_regression.htm));
at 32 cohorts that permits **three study-level terms**. Variables that vary *within* a
cohort — muscle, arm, timepoint, modality — are far cheaper, because each cohort contributes
its own internal contrast, and those are where most of the interesting variation lives.

### 6.1 Modelled

| Feature | Level | Encoding | Why it earns a slot |
|---|---|---|---|
| Days of unloading at the scan - `timepoint_days` since 21 September (§9.4) | row | Nonlinear, three candidate forms (§7) | The primary exposure. Every claim in the talk rests on it |
| `muscle_family` | within-cohort | Categorical, from `config.yaml` | Claim 2 of the talk. Antigravity selectivity is the second-strongest finding in the corpus |
| `arm_type` | within-cohort | Binary, `control` / `countermeasure` | 126 countermeasure rows. Binary because at this N a dose ordinal would be fitting noise (`PLAN.md` task 2.8) |
| `is_composite` / `muscle_grain` | row | Binary | Composite measurements are systematically less extreme than their most affected component; without this the mixed granularity of §5 leaks into the muscle coefficients |
| `modality` + `outcome_type` | study | Categorical pair, collapsed to `MRI_volume` / `CT_CSA` / `DXA_lean_mass` / `ultrasound_thickness` | DXA lean mass and MRI volume do not measure the same thing (`PLAN.md` task 2.4). 314 of 425 rows are MRI volume, so this is mostly a correction term for a minority |
| `pct_estimator` | row | Binary | Which of the two estimators in §4 the row carries |

That is two of the three study-level slots (duration, modality-outcome). The third is held in
reserve for the age term below.

### 6.2 Stratification and sensitivity variables — recorded, not in the primary model

| Variable | Why not a feature | Where it is used instead |
|---|---|---|
| `age_mean`, `population` | 38 of 425 rows are older adults, from six campaigns. The contrast rides on those campaigns and cannot be separated from them at this N | Sensitivity analysis; the third study-level slot if the reviewer asks |
| `sex`, `pct_female` | 347 rows men only, 34 women only, 26 mixed, 18 unstated. The confound with campaign is nearly total | Sex-stratified sensitivity analysis if N allows (`PLAN.md` task 4.5) |
| `cm_modality` | Nine named categories across 126 rows, four with under ten; two countermeasure rows carry `none`, a QC item | Descriptive table and a secondary model restricted to countermeasure arms |
| `measurement_site` | 520 of 742 rows say nothing, and the rest were free text until normalised into `site_kind` and `site_position_pct` (`framework/measurement_site.py`) | Within-muscle heterogeneity sensitivity analysis (S11) |
| `hdt_angle_deg`, `design` | 419 of 425 rows are bed rest, head-down or horizontal; near-constant | Reported in the corpus description |
| `nutrition_controlled`, `bmi_mean`, `body_mass_mean_kg` | Sparse and collinear with campaign | Recorded only |
| `extraction_confidence`, `data_source` | Quality markers, not physiology | Sensitivity analysis excluding figure-derived and low-confidence rows |

### 6.3 Never modelled

`row_id`, `study_id`, `doi`, `source_file`, `page_ref`, `extractor`, `extraction_date`,
`notes`, `campaign_name`, `registry_id`. Provenance, not signal. `cohort_id` is not a feature
either — it is the grouping variable, and any model that uses it as an input has already
failed the validation in §8.

## 7. Tier 1 — the primary model

Fitted twice: on subset A for the duration–response, and on subset B for the muscle ranking
(§3.1). Same specification both times, so the two results are read off one model family
rather than two competing ones.

A three-level model, because the data have three levels: measurements sit inside studies,
studies sit inside campaigns, and two papers from the Berlin campaign are not two independent
observations of anything.

```
pct_change_ijk = f(duration) + β·muscle_family + γ·arm_type + δ·covariates
                 + u_cohort_i + u_study_ij + u_muscle(cohort)_ik + ε_ijk
```

Random intercepts for cohort, for study within cohort, and for muscle within cohort. The
last one is what allows the mixed granularity of §5: repeated measurements of the same muscle
in the same campaign are correlated, and the model is told so rather than left to treat them
as independent replicates.

This is the standard structure for pooled aggregate data with several effect sizes per study
([Assink & Wibbelink 2016](https://www.tqmp.org/RegularArticles/vol12-3/p154/p154.pdf);
[Harrer et al., *Doing Meta-Analysis in R*, ch. 12](https://bookdown.org/MathiasHarrer/Doing_Meta_Analysis_in_R/fitting-a-three-level-model.html)).
Its practical advantage here is decisive: it does not require the within-study covariances
between muscles, which no bed-rest paper reports and which cannot be recovered from published
tables.

### 7.1 The duration term

Three candidate forms, fitted and reported side by side. The choice between them is a result,
not a preprocessing step, and the comparison table goes in the report.

| Form | Expression | What it assumes | Why it is a candidate |
|---|---|---|---|
| **Logarithmic** | `a + b·ln(t)` | Loss accelerates with the logarithm of time, no plateau | The form [Marusic et al. 2021](https://doi.org/10.1152/japplphysiol.00363.2020) fitted to 40 studies. Fitting it makes our curve directly comparable to a published one — a comparison the talk should show |
| **Saturating exponential** | `A·(1 − exp(−t/τ))` | Loss approaches an asymptote `A` with time constant `τ` | Both parameters are physiologically meaningful. `τ` is how fast the muscle gives up and `A` is how much it will eventually lose — the two numbers a countermeasure planner actually wants |
| **Restricted cubic spline** | 3 knots at the 10th, 50th, 90th percentiles of duration | Nothing about the shape | Shape check. Published dose–response practice ([Crippa et al. 2019](https://doi.org/10.1177/0962280218773122)) |

Selection rule, declared before fitting: report all three; choose the saturating exponential
as the headline curve unless the spline shows a shape it cannot follow, or unless AIC favours
another form by more than 4 points. The spline is never the headline curve — it is the
diagnostic that says whether the parametric forms are lying.

**The asymptote is not extrapolation-safe.** `A` is an estimate of the plateau of a curve
observed to 119 days. §10 governs what may be said about day 180.

### 7.2 Weights and inference

Rows are weighted by `n_analysed`, the number of participants actually measured, not by
`n_arm`. Inverse-variance weighting is used only in the sensitivity analysis restricted to
the 289 rows carrying an SD, because 36 rows carry no dispersion at all and dropping them
would silently discard whole cohorts.

Confidence intervals and tests use **cluster-robust standard errors clustered on
`cohort_id`**, on top of the random-effects structure. The random effects model the
correlation; the robust sandwich protects the inference if that model is misspecified, which
at 31 clusters it may well be. Small-sample corrections apply, and degrees of freedom are
computed rather than assumed.

### 7.3 What tier 1 outputs

`results/tier1_curve.json` — coefficients, confidence intervals, the three duration fits with
their AIC, variance components, and the fitted curve on a dense duration grid with a
confidence band. `results/tier1_muscle_ranking.csv` — the muscle-family contrasts with
intervals, sorted. Those two files are figures F2 and F3 in `PLAN.md` §9.

## 8. Tier 2 — the comparative models

Subset A, 346 rows from 32 campaigns. Four families, exactly as the abstract states: linear regression (penalised - ridge, with the
penalty chosen inside the fold), random forest, support vector regression with an RBF kernel,
and gradient boosting.

### 8.1 Validation: leave-one-cohort-out

`cohort_id` is the fold unit. Not `study_id`, and never a random split. Two papers from the
Berlin campaign report the same participants; a random split puts those participants on both
sides of the fold boundary, and the reported error then measures memorisation
(`PLAN.md` §2, finding 3). Grouped cross-validation is the standard response to clustered
data, and leave-one-study-out is its established form in pooled analyses.

32 cohorts means 32 folds. Each fold trains on 31 campaigns and predicts one held-out
campaign it has never seen.

**The leakage guard is an assertion, not a convention.** `cv.py` asserts, for every fold,
that the intersection of training and test `cohort_id` sets is empty, and that every
preprocessing object — imputer, scaler, encoder, penalty selection, hyperparameter choice —
was fitted on the training fold alone. The assertion is tested by deliberately feeding it a
random split and confirming it fails (`PLAN.md` task 3.5). A framework whose leakage guard
has never fired has not been tested.

### 8.2 Hyperparameters

Nested: an inner grouped cross-validation *within* the training fold selects
hyperparameters, and the outer fold sees none of that. Where the inner loop is not affordable
it is replaced by fixed, declared defaults written in `config.yaml` — never by a value chosen
after seeing the outer score. Tuning against the outer fold is the one mistake in this
project that cannot be repaired after the fact.

### 8.3 Metrics

Mean absolute error in percentage points, RMSE, and R², each computed across held-out
cohorts and reported as a distribution over folds rather than a single mean. A model that is
excellent on 28 campaigns and catastrophic on 3 is not a good model, and an average conceals
that. The per-fold table goes in the report; the deck shows the distribution.

**R² is reported pooled, not per fold, and the reason is structural rather than cosmetic.**
Most campaigns ran a single duration, so inside one held-out fold a duration-only model
predicts one value for every row. Compared against that fold's own mean it loses by
construction, and its per-fold R² is negative however good the curve is - the first baseline
run returned about -8.5 per fold and +0.06 pooled from the same predictions. So every
out-of-fold prediction is collected first and R² computed once over all of them, and the
per-fold R² column stays in the results file with this caveat attached rather than on a
slide. MAE and RMSE do not have this problem and are reported per fold.

Every metric is additionally reported **weighted by cohort rather than by row**, so the MEDES
campaign's 99 rows do not dominate the number that appears on a slide.

## 9. The baseline and the comparison

The baseline is the tier-1 curve with duration alone and no other covariate — the simplest
honest answer to "how much muscle is gone after *t* days". It is fitted inside the same
leave-one-cohort-out loop, so its error is measured the same way as everything else.

The thresholds below were agreed in `PLAN.md` §8 before any model was fitted. They are
repeated here because a threshold that can be revised after seeing the result is not a
threshold.

| Criterion | Target | If missed |
|---|---|---|
| Out-of-cohort MAE | ≤ 4 percentage points | Report honestly; the dataset and the framework remain the contribution |
| Best model vs duration-only baseline | ≥ 15% relative MAE improvement | **Report the null result.** It is a finding about how much signal the published literature contains, not a failure |
| SHAP top-3 stability | Same top three in ≥ 80% of folds | Present importance as indicative only, and say so out loud |
| Leakage audit | No cohort split across folds; no preprocessing fitted outside a fold | **Blocking** |
| Reproducibility | `make all` regenerates every number and figure from the frozen dataset | **Blocking** |
| Physiological sign-off | The partner signs off on the fitted relationships | **Blocking** |

The first three are allowed to fail. The last three are not.

### 9.1 The baseline as first run

Run on 2026-09-18 against `dataset_v1.0`, subset A (342 rows, 31 campaigns, 40 studies),
leave-one-cohort-out, weighted by campaign. `results/baseline.json` carries the full output
and `make baseline` regenerates it.

| Form | Out-of-cohort MAE | 95% CI | Pooled R² |
|---|---|---|---|
| Linear in days | 3.57 pp | 2.84 – 4.38 | −0.09 |
| Logarithmic | **3.14 pp** | 2.35 – 4.02 | 0.02 |
| Saturating exponential | 3.24 pp | 2.46 – 4.11 | 0.06 |

Three things follow, and none of them is a disappointment.

1. **All three forms already sit inside the 4-percentage-point target** set in `PLAN.md` §8,
   before any model family has been fitted. That is the bar tier 2 has to clear.
2. **The straight line is the worst of the three**, which is the evidence that the
   relationship is genuinely nonlinear rather than assumed to be.
3. **Pooled R² is near zero.** Duration alone predicts the average loss at a given day well
   enough, but it explains almost none of the row-to-row variation - because that variation
   is mostly *which muscle* is being measured. That is not a failure of the baseline; it is
   the quantitative case for claim 2 of the talk, and it is why muscle family enters the
   tier-1 model rather than being left as a footnote.

The fitted saturating curve gives a time constant of 10 days and an eventual loss of about
9.3% averaged over all muscles in the subset - the whole-limb and composite rows pull that
average up towards the less affected tissue, which is exactly why the muscle-specific model
in subset B is the one that answers "how much soleus is left".

### 9.2 Tier 2 as first run — the null result

Run on 2026-09-18, subset A, leave-one-cohort-out with hyperparameters tuned by a
campaign-grouped search inside each training fold. `results/model_comparison.csv`.

| Model | Out-of-cohort MAE | 95% CI | vs baseline | Pooled R² |
|---|---|---|---|---|
| Duration-only curve (log) | **3.14 pp** | 2.35 – 4.02 | — | 0.02 |
| Support vector regression | 3.21 pp | 2.47 – 4.09 | −2.3% | 0.20 |
| Random forest | 3.25 pp | 2.51 – 4.06 | −3.8% | 0.20 |
| Gradient boosting | 3.26 pp | 2.59 – 4.03 | −4.0% | 0.18 |
| Ridge regression | 3.45 pp | 2.70 – 4.28 | −10.0% | 0.16 |

**No family beats the duration curve, and three of the four are within a tenth of a
percentage point of it.** Under `PLAN.md` §8 that is rung B of the fallback ladder, and it was
pre-committed to before anything was fitted. It is reported as a finding, not softened.

The interesting part is the last column. Pooled R² rises from 0.02 to about 0.20 the moment
muscle identity enters the model, so the flexible families *are* finding real structure - they
are simply not converting it into a lower absolute error, because the residual is dominated by
between-campaign differences that no feature in this dataset explains. That is a statement
about the published literature rather than about the algorithms: aggregate means from 31
campaigns, each with its own imaging protocol and population, carry about this much signal and
no more.

The worst fold for every family is `wise2005` (MAE 8.5-9.4 pp) - 60 days of bed rest in women
only, the corpus's largest single departure from the average campaign, and a clean
illustration of why error is reported per fold rather than as one mean.

**Importance.** SHAP is computed exactly for the tree ensembles. The best-scoring family here
is SVR, where no exact explainer exists and a sampling explainer is a different and far slower
computation, so its importance is permutation-based and every output says which was used. Only
`duration` reaches the top three in more than two-thirds of folds; nothing else is stable,
which under §11 means importance is presented as indicative and the stability table is shown
instead of a tidy bar chart.

### 9.2.1 A fifth family, post hoc: TabPFN

**Added on 2026-09-19, after the tier-2 null result was known. It is not pre-registered.** The
question the null result invites is whether *any* learner could do better at 32 campaigns,
including one pretrained for small tables. TabPFN (Hollmann et al., *Nature* 2025,
[doi:10.1038/s41586-024-08328-6](https://doi.org/10.1038/s41586-024-08328-6)) is the strongest
available answer: a transformer pretrained on millions of synthetic tabular datasets that
predicts in context, with no hyperparameters chosen against our campaigns.

| Choice | Value |
|---|---|
| Declared in | `config.yaml` → `models.post_hoc_families`, `models.grids.tabpfn: {}`, `models.tabpfn_device: cpu` |
| Version | `tabpfn==2.0.9` - later versions put the checkpoint behind an interactive licence login |
| Tuning | None: an empty grid means fixed declared defaults, wrapped by `run_models.FixedSearch` |
| Folds, scoring, baseline | Identical to §8 and §9: the same design matrix, leave-one-campaign-out folds, leakage assertions, campaign weighting and bootstrap, against the logarithmic duration curve |
| Runner and results | `framework/run_tabpfn.py`, `make tabpfn`, `results/tabpfn_comparison.*` |
| Environment | Separate: tabpfn 2.0.9 needs scikit-learn below 1.7 and the four families were fitted with 1.8. Run with scikit-learn 1.6.1, PyTorch 2.14 (CPU) |

It is kept out of `make models` so that the four declared families' numbers do not move and one
results file never mixes two environments.

**As run on 2026-09-21** against `dataset_v1.1`, on the day of the scan:

| Model | Out-of-cohort MAE | 95% CI | vs baseline | Pooled R² | Worst fold |
|---|---|---|---|---|---|
| Duration-only curve (log) | 3.16 pp | 2.44 – 3.93 | — | 0.14 | `wise2005` (9.3) |
| Random forest | 3.18 pp | 2.50 – 3.91 | −0.7% | 0.34 | `liphardt_br21` (7.8) |
| **TabPFN** | **3.22 pp** | 2.51 – 3.97 | −2.1% | **0.39** | `liphardt_br21` (7.6) |

**TabPFN does not beat the curve by the 15% bar either.** It is second of the five families and
has the highest pooled R² of any of them: the pretrained network finds the muscle structure the
tuned families found and, like them, cannot turn it into lower error on a campaign it has not
seen. The null result now rests on five families of very different kinds. A first run on
2026-09-19, against `dataset_v1.0` and the planned-length axis (`feat/tabpfn`), scored 3.25 pp
with a pooled R² of 0.03; it is superseded by the run above.

### 9.3 Tier 3 — a language model forecasting ranges

**Added 2026-09-21, after the tier-2 null result was known. It is not pre-registered, and the
report must say so.** What this section can do is declare the method and the bars before the
first answer is requested, and it was committed before any was.

The question tier 2 leaves open is whether something that reads the *description* of a
campaign - who the participants were, what they did, which muscle, which scanner - can do what
eleven numeric columns could not. TypeSafe's Jev (`jev-1.13.0`, pinned in `config.yaml`) is a
model built for exactly one kind of answer: given a state and a fixed set of options, it
returns a calibrated probability for every option. It is not asked for a number. For each row
it is asked one Choice question - *which of these ranges will the measurement fall in?* - and
everything numeric is computed in `forecast.py` from the probabilities it returns. TypeSafe's
own documentation is plain that the model is not a calculator.

**Two arms.**

| Arm | What the model forecasts | Ranges | Rows | Campaigns | Reference baseline |
|---|---|---|---|---|---|
| `without_history` | Percent change from baseline | 2 pp wide, −30 to +4, open at both ends | 346 | 32 | Duration curve |
| `with_history` | Change since the previous scan of the same measurement | 1 pp wide, −14 to +4, open at both ends | 84 | 5 | Last scan plus the curve's step |

The first arm sees nothing of the held-out campaign, as the tier-2 families do. The second
also sees that campaign's earlier scans - the same measurement's history and every other
muscle and group scanned **strictly before** the target day - so it answers a forecasting
question: given the day-28 scan, where is the day-56 scan? Only 84 rows have an earlier scan
to show, and the five campaigns are not equal: `berlin_bbr1` alone carries 39 of them.

**What the model is shown** (`forecast.build_state`): a short background paragraph; the
participants, protocol, countermeasure and measurement of the target row, in words; the target
day and how far it sits from the planned end; the duration curve fitted to the training
campaigns; and as many of the training campaigns' observations - and, in the second arm, their
scan-to-scan changes - as fit a declared budget of 26,000 tokens, most relevant first
(same muscle, then same family, then same kind of group, then nearest day). TypeSafe's input
is cheap, so the state is as full as the budget allows. The budget is estimated at 2.3
characters per token, the rate two full states were measured at on 21 September, which
keeps the state and the question inside the model's 32,000-token limit.

**What it is never shown, by assertion rather than by care:** any row of the held-out campaign
in the reference tables; any scan of the held-out campaign on or after the target day; the
target's own outcome; and anything that names a paper, an author, a campaign or a registry.
The last rule is the §6.3 rule applied to text, and it also keeps the model from recognising a
published study and recalling its number.

**The baselines get distributions too.** Each baseline's forecast is its point plus the
residuals it made on the training campaigns, binned into the same ranges. That puts the model
and the baselines on identical footing for every metric below, rather than comparing a
distribution with a point.

| Arm | Baseline | Point |
|---|---|---|
| `without_history` | `duration_curve` | The log duration curve, fitted to the training campaigns |
| `with_history` | `last_scan` | No further change |
| `with_history` | `last_scan_plus_curve` | The curve's step from the last scan's day to the target day |

**The time axis is the day of the scan**, `timepoint_days`, for the model and for every tier-3
baseline. Tiers 1 and 2 use `duration_days`, the campaign's *planned* length. For 200 of the
346 rows in subset A the scan came before the end of bed rest, and for about 120 of them more
than a week before - a day-14 scan in a 56-day campaign enters tiers 1 and 2 as 56 days. The
tier-3 numbers are therefore compared with baselines refitted on the scan day, never with the
§9.2 table. Whether tiers 1 and 2 should move to the scan day is recorded as an open question
in `docs/STATUS.md`, not decided here. *Update, 21 September: they moved the same day - §9.4.*

**Metrics**, each averaged within a held-out campaign and then across campaigns, with the
campaign bootstrap of §8.3:

- **MAE** of the probability-weighted mean - the same kind of number as §9.2.
- **CRPS** in percentage points. It is the proper score for a forecast distribution, and for a
  forecast with no spread at all it reduces to the absolute error, so it reads on the MAE's
  scale.
- **Log score** of the range holding the truth.
- **Coverage and width of the most probable range** at 50% and 80% - the shortest run of
  adjacent ranges whose probability reaches the level. This is the "most probable range" the
  forecast reports, and a range is only worth quoting if its coverage matches its level.

**Bars, declared before the first answer.**

| Criterion | Target | If missed |
|---|---|---|
| Model vs the arm's reference baseline, MAE | ≥ 15% relative improvement | Report the null result, as in §9.2 |
| Model vs the arm's reference baseline, CRPS | ≥ 15% relative improvement | Reported alongside the MAE, never instead of it |
| Coverage of the 80% range | Between 70% and 90% | The ranges are miscalibrated: show coverage and width, and do not call them 80% ranges |
| Leakage | The three assertions above hold for every request | **Blocking** |
| Reproducibility | `make forecast` rebuilds every number from the committed answer cache without calling the API | **Blocking** |

**What this tier cannot rule out.** Jev was pretrained on text that may include some of these
papers. Withholding every name is the strongest guard available here, but a model that has
read a paper could still recognise it from a description plus a set of numbers, and no
cross-validation can see that. A win in the arm without history should be read with that in
mind. The second arm is less exposed, because the answer it needs is a change between two
scans, which papers rarely print.

### 9.3.1 Tier 3 as first run

Run on 2026-09-21 against `dataset_v1.1`, subset A, with `jev-1.13.0`: 430 requests, the
largest 26,390 input tokens. `results/forecast_comparison.csv` carries the table and
`make forecast` rebuilds it from the committed answers.

**Without history** - 346 rows, 32 campaigns:

| Model | MAE | 95% CI | CRPS | 80% range covers | 80% range width | Pooled R² |
|---|---|---|---|---|---|---|
| Jev | **2.71 pp** | 2.12 – 3.33 | **2.05 pp** | 62% | 5.4 pp | 0.43 |
| Duration curve, scan day | 3.13 pp | 2.37 – 3.92 | 2.49 pp | 90% | 15.5 pp | 0.14 |

**With history** - 84 rows, 5 campaigns, forecasting the change since the last scan:

| Model | MAE | 95% CI | CRPS | 80% range covers | 80% range width | Pooled R² |
|---|---|---|---|---|---|---|
| Jev | **2.84 pp** | 2.19 – 3.50 | 2.21 pp | 38% | 2.8 pp | 0.19 |
| Last scan | 3.66 pp | 2.91 – 4.42 | 2.44 pp | 69% | 9.0 pp | −0.22 |
| Last scan plus the curve's step | 3.21 pp | 2.58 – 3.87 | **2.16 pp** | 77% | 8.8 pp | 0.02 |

**Against the bars declared above:**

- **MAE: missed in both arms**, by 13.3% and 11.5% against the 15% asked for. Under the rule of
  §9 that is a null result, and it is reported as one.
- **CRPS: met without history** (17.7%), **missed with history** (2.2% worse than the reference).
- **80% ranges: miscalibrated in both arms.** They hold the truth 62% and 38% of the time, so
  they may not be called 80% ranges. The log score says the same thing from the other side:
  without history it is worse than the curve's (2.84 against 2.29) despite the better CRPS,
  because when the model is wrong it has put almost no probability where the truth landed.
- **The paired difference**, which is the quantity a comparison claims: without history the
  model's error is lower by **0.42 pp (95% CI 0.13 to 0.73)** and it wins in 20 of 32 campaigns;
  with history, by 0.37 pp (0.03 to 0.75) in 4 of 5.

**What it means.** This is the first model in the project whose advantage over the duration
curve has a paired interval that excludes zero, and its pooled R² of 0.43 is about twice what
the tier-2 families reached. Something in the written description carries signal that the
eleven numeric columns of tier 2 did not. Three things keep that from being a headline:

1. **It misses its own bar** on the metric declared first, and it was not pre-registered.
2. **The gain is concentrated.** Three campaigns - `nasa_sprint_br70`, `berlin_bbr2` and
   `medes_ltbr90` - carry more than half of it. They are long, multi-muscle MRI campaigns, where
   knowing the muscle matters most; they are also among the most published campaigns in the
   field, where recognition is most likely. This run cannot tell the two apart. The one
   campaign no paper reports, `nasa_utmb_c3`, computed from NASA's raw archive, points
   against pure recognition: the model beats the curve there by 0.67 pp without history. It
   is one campaign and four rows, so it is an observation, not a test.
3. **The model is overconfident**, badly so once it sees the history, where its 80% ranges are
   2.8 pp wide and hold the truth 38% of the time. Its point forecasts can be quoted; its ranges
   cannot, until they are recalibrated or widened by a rule declared in advance.

### 9.3.2 Is the gain signal or recognition? The ablations

**Declared on 2026-09-21, after §9.3.1 and before the first ablation answer.** Everything here
runs on the arm without history, where the concern sits. `framework/run_ablation.py`,
`make ablation`.

Three ablations change one thing each about what the model is shown, and are scored exactly
as the first run was, against the same duration curve:

| Variant | What changes | What it tests |
|---|---|---|
| `generic` | The target is described only by muscle, role, method, kind of group and day. No participants, no countermeasure protocol, no planned length, no measurement site | Whether the gain needs anything that could identify a study. This is roughly the information tier 2 had |
| `scrambled_reference` | The other campaigns' values are shuffled among their rows, and the curve shown is fitted to the shuffled rows. The baseline keeps the real curve | Whether the model reads the reference numbers at all |
| `no_reference` | No curve and no observations from other campaigns | What the model manages on its own knowledge |

**The recognition probe** shows the model the target's description exactly as the full
forecast sends it - participants, protocol, measurement, day - with one question: which of
these campaigns does it come from? The options are the 11 campaigns in subset A that have a
proper name (AGBRESA, BBR1, BBR2-2, BRACE, LunHab, MEDES LTBR, NASA SPRINT, UTMB Campaign 3,
PlanHab, VBR, WISE-2005) and "none of these". Descriptive names such as "30-day unilateral
lower limb suspension" are left out because the name would give the answer away. Chance is
one in twelve. Every row of those 11 campaigns is probed.

**Reading rules, declared before any answer.**

- A campaign is **recognised** when the model's top choice is its true name on at least half
  of its rows.
- Recognition is a **live explanation** for the gain if two or more of the three campaigns that
  carry most of it (`nasa_sprint_br70`, `berlin_bbr2`, `medes_ltbr90`) are recognised, or if
  the Spearman correlation between a campaign's recognition (mean probability on its true name)
  and its gain is 0.5 or more. With 11 campaigns only a strong association counts.
- `generic` **keeps the gain** if its paired gain over the curve has a 95% interval above zero
  and is at least half the full run's (0.21 pp or more).
- `scrambled_reference` **shows the model uses the reference data** if its paired gain over
  the curve has an interval that reaches zero or falls below it.
- `no_reference` is descriptive.

| `generic` keeps the gain | Recognition live | Reading |
|---|---|---|
| Yes | No | The gain needs nothing that identifies a study. Tier 3's point forecasts may be quoted as a result, with the §9.3.1 caveats |
| Yes | Yes | The gain survives without identifying details, but the model can name campaigns. Quote it, and name the concern next to it |
| No | No | The participant and protocol details carry the gain, yet the model cannot name the campaigns: the likelier reading is that those details carry physiology - sex, age, countermeasure dose. Quote it with that stated |
| No | Yes | The gain cannot be separated from recognition. It is reported as exploratory and not quoted as a result |

### 9.3.3 The ablations as run

Run on 2026-09-21: 1,280 new answers, with the full variant answered from the first run's
cache. `results/forecast_ablation.csv`, `results/forecast_ablation_campaigns.csv` and
`results/forecast_recognition.csv`; `make ablation` rebuilds them.

*Corrected on 2026-09-21.* The first version of this section quoted the live run's printout.
Where two rows produced the same request, the client asked the model twice, received two
slightly different answers, and cached one; the printout used both, the rebuild from the
cache uses one. The numbers below are the rebuilt ones, the ones `make ablation` reproduces.
The differences are in the second decimal and change no reading. The client now asks each
distinct request once per batch, so the two can no longer disagree.

| Variant | MAE | Paired gain over the curve (95% CI) | Change from the full run (95% CI) |
|---|---|---|---|
| Full | 2.71 pp | **+0.42** (+0.13 to +0.73) | — |
| Generic | 2.82 pp | **+0.30** (+0.01 to +0.62) | −0.11 (−0.24 to +0.02) |
| Scrambled reference | 4.37 pp | −1.25 (−1.94 to −0.59) | −1.66 (−2.32 to −1.07) |
| No reference | 5.85 pp | −2.72 (−3.58 to −1.76) | −3.14 (−3.92 to −2.29) |
| Duration curve | 3.13 pp | | |

**The recognition probe.** The model puts a mean probability of 0.14 on the true campaign,
against 0.08 by chance, and names it first on 19% of rows. Three campaigns pass the
recognition bar: NASA SPRINT and AGBRESA (named first on 67% of their rows) and VBR (50%). Of
the three that carry most of the gain, only SPRINT is recognised; for BBR2-2 and MEDES LTBR the
model's commonest answer is "none of these campaigns". Recognition and gain correlate at
ρ = 0.37 (p = 0.26, 11 campaigns).

**Against the rules:**

- `generic` **keeps the gain**: 0.30 pp, at least half of 0.42, with an interval above zero.
  Its difference from the full run, −0.11 pp, has an interval that includes zero.
- **Recognition is not a live explanation**: one of the three campaigns, not two, and a
  correlation below 0.5.
- `scrambled_reference` **shows the model reads the reference data**: shuffle the values and
  the gain becomes a loss of 1.25 pp.
- `no_reference`: on its own knowledge the model is far worse than the curve, 5.85 pp against
  3.13.

That is the first row of the reading table. **Tier 3's point forecasts may be quoted as a
result, with the caveats of §9.3.1** - not pre-registered, below its 15% MAE bar, and
overconfident ranges.

**What the campaign-level errors add** (`forecast_ablation_campaigns.csv`). If the model were
recalling published numbers, it would do best without reference data on the campaigns it can
name. It does not: without reference data it is worse than the curve on AGBRESA (6.13 pp
against 2.95) and VBR (5.73 against 0.95). SPRINT is the exception, 4.80 against 5.92, and
the one place recognition may contribute. But the generic variant, which gives the model
nothing to recognise SPRINT by, still beats the curve there, 3.79 against 5.92, so most of
SPRINT's gain does not depend on recognition either.

**What the gain is, then.** Without identifying details the model still does better than the
curve, and it does so only when it can read the other campaigns' values. The likeliest reading
is that the model does a kind of reasoning tier 2 could not: it picks out the reference rows
that match the target - same muscle, same kind of group, a nearby day - and weighs them, where
tier 2's families were given the same kind of information as one-hot columns and a
duration basis. That is an interpretation, not a test. The ablations establish what the gain
does not need; they do not establish its mechanism.

### 9.3.4 Does it hold up? The validation battery

**Declared on 2026-09-21, before the first validation answer.** `framework/run_validation.py`,
`make validation`. Every run holds out one campaign at a time and shows the model only the
other campaigns' data - and, on the history arm, the held-out campaign's scans from before the
target day - exactly as §9.3 did. What changes between runs is one thing each.

**On the history arm** (84 rows, 5 campaigns; reference: last scan plus the curve's step):

| Run | What changes | What it tests |
|---|---|---|
| `generic` | No participants, protocol text or planned length | Whether the gain needs anything that identifies a study |
| `scrambled_reference` | The other campaigns' values shuffled among their rows | Whether the model reads the other campaigns |
| `no_reference` | No other campaigns at all - the earlier scans only | What the history alone is worth |
| `scrambled_history` | The held-out campaign's earlier values shuffled among its earlier scans - never a value from the target day or later | Whether the model reads the earlier scans at all |

**On both arms:** `reordered` shows the same reference rows in a different order, and
`shifted_bins` moves every range edge by half a step. Neither changes what the model knows, so
a result that moves under them depends on how the question was put. **The repeat check** sends
the first 20 requests of the arm without history again, past the cache. **What the earlier
scans buy** compares the history arm with the arm without history on the same 84 rows: a
forecast of the change plus the last scan is a forecast of the level, with the same absolute
error.

**Reading rules, declared before any answer:**

- `generic` keeps the history arm's gain if its paired gain over the reference has an interval
  above zero and is at least half the full run's (0.19 pp or more).
- The model **reads the earlier scans** if `scrambled_history` is worse than the full run with
  an interval below zero; it **reads the other campaigns** if `scrambled_reference` or
  `no_reference` is.
- **The earlier scans help** if the history arm's paired gain over the arm without history,
  on the same rows, has an interval above zero. The same comparison is made for the baselines,
  so the model's gain from history can be set beside the gain any method gets from it.
- A result is **robust to presentation** if, under both `reordered` and `shifted_bins`, its MAE
  moves by less than 10% of the full run's and its paired gain over the reference keeps its
  sign - with an interval above zero on the arm without history, the result §9.3.3 allows to be
  quoted.
- The model is **consistent** if all 20 repeated requests return the same probabilities. If
  they do not, the spread is reported and every difference between runs is read against it.

**Tier 3 is working rather than lucky** if the arm without history is robust to presentation
and consistent, and the history arm reads what it is given. Short of that, the report states
which of the three failed. With five campaigns, every interval on the history arm rests on a
bootstrap over five values and is indicative, not decisive; that is said wherever one is
quoted.

### 9.3.5 The validation battery as run

Run on 2026-09-21: 1,195 new answers, 20 repeats past the cache. `results/forecast_validation.csv`
and `results/forecast_repeats.json`; `make validation` rebuilds them.

**The arm without history** (346 rows, 32 campaigns; the duration curve scores 3.13 pp):

| Run | MAE | Paired gain over the curve (95% CI) | Change from the full run (95% CI) |
|---|---|---|---|
| Full | 2.71 pp | +0.42 (+0.13 to +0.73) | — |
| Reordered | 2.79 pp | +0.34 (+0.07 to +0.62) | −0.08 (−0.20 to +0.05) |
| Shifted ranges | 2.68 pp | +0.45 (+0.15 to +0.78) | +0.03 (−0.03 to +0.09) |

**The history arm** (84 rows, 5 campaigns; last scan plus the curve's step scores 3.21 pp):

| Run | MAE | Paired gain over the reference (95% CI) | Change from the full run (95% CI) |
|---|---|---|---|
| Full | 2.84 pp | +0.37 (+0.03 to +0.75) | — |
| Generic | 2.87 pp | +0.34 (+0.10 to +0.59) | −0.02 (−0.23 to +0.14) |
| Scrambled reference | 2.98 pp | +0.24 (−0.22 to +0.77) | −0.13 (−0.43 to +0.10) |
| No reference | 3.37 pp | −0.16 (−1.48 to +0.94) | −0.52 (−1.57 to +0.48) |
| Scrambled history | 2.78 pp | +0.43 (+0.08 to +0.78) | +0.06 (−0.14 to +0.29) |
| Reordered | 2.78 pp | +0.44 (+0.07 to +0.90) | +0.07 (−0.06 to +0.17) |
| Shifted ranges | 2.90 pp | +0.31 (+0.04 to +0.58) | −0.05 (−0.27 to +0.10) |

**What the earlier scans buy**, on the same 84 rows: the model's error falls from 5.83 to
2.84 pp (paired +2.98, 95% CI +1.54 to +5.51), and the baselines' from 7.27 to 3.21 pp
(+4.06, +2.52 to +5.99).

**The repeats:** none of the 20 came back identical. The probabilities moved by 0.034 on
average and 0.09 at most; the forecasts by 0.17 pp on average and 0.48 at most; the most likely
range held in 18 of 20; the error on those rows went from 2.456 to 2.479 pp.

**Against the rules:**

- **Robust to presentation - yes, on both arms.** Without history, the MAE moves by 3% under
  reordering and 1% under shifted ranges, and the gain over the curve keeps an interval above
  zero under both. On the history arm both moves are 2% and the gain keeps its sign.
- **`generic` keeps the history arm's gain - yes**: +0.34 pp, interval above zero.
- **Reads the earlier scans - no.** Shuffling the held-out campaign's earlier values leaves the
  error where it was (+0.06 pp, interval across zero). The model does not use them to forecast
  the change.
- **Reads the other campaigns, on the history arm - not shown.** Both reference ablations are
  worse in their point estimates, by 0.13 and 0.52 pp, but on five campaigns neither interval
  clears zero.
- **The earlier scans help - yes, strongly, and not because of the model.** The baselines gain
  more from them than the model does. What the earlier scans supply is the anchor - where the
  muscle already is - and the code supplies it, by adding the forecast change to the last scan.
  The model's own edge on the history arm is forecasting the change better than the curve's
  step, and that edge does not come from the earlier values.
- **Consistent - no, by the letter of the rule.** Read against the spread it measured: a single
  forecast moves by about 0.17 pp between askings and the error on the repeated rows by 0.02 pp.
  The differences between presentation runs, 0.03 to 0.08 pp, are of that order; the gain over
  the curve, 0.42 pp, is not.

**The verdict the rules give.** Of the three conditions for calling tier 3 working rather than
lucky, the one that carries the quoted number holds: the result without history survives both
presentation checks, and the model's run-to-run variation is far smaller than the gain. The
other two fail and are reported as failing: the model's answers are not reproducible bit for
bit, and on the history arm it does not read what it is given. Two consequences for the
report: the tier-3 number is quoted from the arm without history, with its caveats and the
note that repeated runs differ slightly; and nothing may be said about the model using a
campaign's earlier scans, because the test for exactly that came back empty.

### 9.4 The time axis, corrected

**Found and fixed on 2026-09-21.** Tiers 1 and 2 read `duration_days` as the exposure. The
schema defines it as the campaign's *planned* total length; the day a muscle was scanned is
`timepoint_days`. For 200 of the 346 rows in subset A the scan came before bed rest ended -
for about 120 of them more than a week before - and every one of them entered the models at
the full planned length: a day-14 scan of a 56-day campaign was fitted as 56 days of
unloading. §6 already named the timepoint as a within-campaign variable; the code never used
it. This is a correction of the implementation, not a new analysis choice, and it applies to
every result from §9.1 onwards.

The exposure is now declared once, as `features.time_column: timepoint_days`, and read through
one function by the design matrix, the baseline, the fold loop and tier 1. Every result file
records which axis it was fitted on. The §9.1 and §9.2 tables above are the first runs as they
were, and are superseded by these:

| Result | Planned length | Day of the scan |
|---|---|---|
| Tier 1 fit, saturating form, AIC on the same 346 rows | 2152.3 | **2085.9** |
| Residual variance | 17.7 | **13.8** |
| Per doubling of days, logarithmic form | −2.41 pp (−3.26 to −1.56) | **−2.99 pp** (−3.44 to −2.53) |
| Saturating time constant | 90 days, at the edge of the grid | **60 days**, inside it |
| Eventual loss, saturating form | −19.9% (−24.8 to −15.0) | **−17.3%** (−20.9 to −13.7) |
| Share of variance between muscles within a campaign | 23% | **30%** |
| Baseline, logarithmic, out-of-campaign MAE | 3.21 pp | **3.16 pp** |
| Baseline pooled R² | 0.03 | **0.14** |
| Best tier-2 family against the baseline | SVR, −0.4% | **Random forest, −0.7%** |
| Tier-2 pooled R² | 0.10–0.22 | **0.27–0.36** |
| Stable in the top three of importance (≥ 80% of folds) | duration only, at 69% | **duration (91%) and plantar flexors (88%)** |

The fit is better by about 65 AIC points on identical rows, which is the plainest evidence
that the scan day is the right exposure. What does not change is what matters for the talk:
the duration forms remain indistinguishable, the muscle ranking keeps its order with plantar
flexors worst and hip rotators least affected, and no tier-2 family beats the duration curve
by the 15% `PLAN.md` §8 asks for. Tier 3 was already on the scan day and is unaffected.

---

## 10. Uncertainty, and the 180-day question

Confidence intervals on every reported metric come from a **bootstrap over cohorts**, not
over rows: campaigns are resampled with replacement and the whole pipeline is refitted. That
is the resampling unit that matches the dependence structure, and it produces the wider,
honest interval.

Extrapolation beyond 119 days is governed by three rules:

1. It is computed from the tier-1 saturating curve only, never from a tree-based model. A
   random forest cannot predict outside the range of its training data; it will return the
   edge value and look confident doing it.
2. It is always reported as a **prediction interval**, not a confidence interval, and the
   interval is drawn on the same axes as the observed data so the audience can see where the
   evidence stops.
3. The slide and the report both state, in words, that the longest observation is 119 days
   and that a Mars transit is roughly 180, and that the gap is filled by an assumption about
   curve shape rather than by data.

This is `PLAN.md` task 4.7, and it stays a backup slide.

## 11. Interpretation

SHAP values on the best-performing tier-2 model, with two constraints that decide what may be
said about them.

**Stability first, magnitude second.** SHAP is recomputed inside every fold, and the top-three
feature ranking is tabulated across folds. If the ranking is unstable, the ranking is the
finding, and the importance plot is presented as indicative only.

**Nothing causal.** A SHAP value says the model leaned on a variable, not that the variable
causes atrophy. Every feature here is at least partly a marker of which campaign a row came
from, and the strongest ones — duration, muscle family — are exactly the ones the tier-1
model estimates properly with intervals. SHAP's job in this project is to show whether the
flexible models agree with the physiology; it is a consistency check, not evidence.

If tier 2 fails to beat the baseline, the SHAP slide still runs, because "the flexible models
also concluded the answer is duration and muscle identity" is the cleanest possible support
for the talk's one sentence.

## 12. Sensitivity analyses

Each is the same pipeline with one declared change, and each produces a row in
`results/sensitivity.md` with the headline coefficient and the out-of-cohort MAE next to the
primary result.

| # | Change | What it tests |
|---|---|---|
| S1 | Composite-first resolution instead of component-first (§5) | Whether the muscle ranking is an artefact of granularity |
| S2 | Drop the MEDES 90-day campaign (103 rows, 24%) | Whether one campaign is carrying the duration–response |
| S3 | Drop the two Berlin campaigns | The same question for the other dominant group |
| S4 | MRI volume only (314 rows) | Whether mixing modalities changed the answer |
| S5 | Exclude figure-derived and low-confidence rows | Whether digitisation is load-bearing |
| S6 | Inverse-variance weights on the 289 rows carrying an SD | Whether the weighting scheme matters |
| S7 | Recomputed-percentage rows only, then printed-percentage rows only | Whether the two estimators of §4 agree |
| S8 | Add `age_mean` as the third study-level covariate | Whether the older cohort shifts anything |
| S9 | Sex-stratified, if the fold structure survives it | Honest answer to a question that will be asked |
| S10 | Recovery rows included with a phase term | Whether reconditioning can be modelled at all with this corpus |
| S11 | Restricted to rows with a stated `site_kind`, then split by `site_position_pct` | Whether where the slice was taken moved the estimate |

S1, S2 and S4 are pre-registered as the three that must be shown in the report whatever they
say. The rest are reported if they change a conclusion, and listed as run-and-unremarkable if
they do not.

## 13. Modules

One job per module, each with a typed signature. No module reads a file that is not
declared in `config.yaml`, and no module contains a number that is not in `config.yaml`.

| Module | Responsibility | Key interface |
|---|---|---|
| `data_loader.py` | Read the frozen CSV, verify its SHA-256 against the file the config names (`dataset_v1.1.sha256`), apply the §3 predicates | `load(config) -> pd.DataFrame` |
| `features.py` | The §5 resolution rule, encodings, the duration basis functions | `build(df, config) -> X, y, groups` |
| `muscle_map.py` | Muscle family and functional class from `data/muscle_map.csv`; fails loudly on an unmapped muscle | `annotate(rows) -> rows` |
| `measurement_site.py` | `site_kind` and `site_position_pct` from `data/measurement_site_map.csv` | `annotate(rows) -> rows` |
| `cv.py` | Leave-one-cohort-out splitter and the leakage assertions of §8.1 | `loco_split(groups) -> Iterator[train_idx, test_idx]` |
| `models.py` | The tier-1 estimator and the four tier-2 families, each behind one fit/predict interface | `build_estimators(config) -> dict[str, Estimator]` |
| `evaluate.py` | Fold metrics, cohort-weighted aggregates, the cohort bootstrap, the baseline comparison | `evaluate(estimators, splits, config) -> Results` |
| `explain.py` | Per-fold SHAP and the stability table | `explain(model, folds, config) -> ShapReport` |
| `forecast.py` | Tier 3: the ranges, the state the model is shown and its assertions, the point, interval and proper scores | `build_state(target, train, held_out, arm, config) -> state, info` |
| `typesafe_client.py` | One POST per request to TypeSafe, retried with backoff, every answer cached on disk by a hash of its request | `CachedAnswerer(cache_dir, model)(requests) -> answers` |
| `run_forecast.py` | Tier 3's two arms under leave-one-cohort-out, with baselines scored on the same metrics | `run(config, answerer) -> result` |
| `tier1.py`, `run_tier1.py` | The three-level meta-regression of §7, and the run that writes the curve and the ranking | `fit_form(resolved, config, form) -> Tier1Fit` |
| `sensitivity.py` | The declared sensitivity analyses of §12 | `run(config) -> result` |
| `run_baseline.py`, `run_models.py` | The duration-only baseline in three forms, and the four families of §8 | `run(config) -> result` |
| `run_ablation.py` | Tier 3's ablations and recognition probe, §9.3.2 | `run(config, answerer) -> result` |
| `run_validation.py` | Tier 3's validation battery, §9.3.4 | `run(config, answerer) -> result` |
| `plot_figures.py` | Every figure, drawn from the results files | `render_all(directory, config) -> paths` |

`config.yaml` holds the subset predicates, the feature lists,
the duration forms, model families and their grids, the number of bootstrap replicates, and
the random seed. Changing an analysis means editing that file, and the file is committed with
the result it produced.

The framework diagram (`PLAN.md` task 3.2, `figures/F4_framework.svg`) draws this chain:
search → screening and extraction → frozen dataset → modelling subset → leave-one-campaign-out
folds → tiers 1, 2 and 3.

## 14. Reproducibility

`make all` regenerates every number and every figure from `data/dataset_v1.1.csv` and
`config.yaml`, on a clean checkout, with no manual step. Tier 3 is rebuilt from the model's
answers committed in `results/forecast_cache/`, never by calling the service again. This is blocking, not aspirational:
a number that cannot be regenerated cannot go on a slide (`PLAN.md` §15).

- The loader refuses to run if the dataset SHA-256 does not match, so a silent edit cannot
  reach a result.
- One seed, declared in `config.yaml`, set for every stochastic component.
- Package versions pinned in `requirements.txt`; the versions used are written into each
  results file.
- Every file in `results/` records the dataset version and the git commit it came from. The
  figures carry neither: they are drawn from those files by `make figures`, and a figure is
  only as current as the results it was last drawn from.

## 15. Assumptions, stated plainly

1. **Group means, not people.** Every row is an arm mean. The framework predicts what a group
   of similar people would lose on average, and cannot say what one astronaut will lose.
2. **Percentage change is comparable across modalities after adjustment.** A 10% MRI volume
   loss and a 10% DXA lean-mass loss are treated as the same target value with a modality
   term separating them. This is an assumption, and S4 is its test.
3. **Cohorts are independent of one another.** Within-cohort dependence is modelled; the
   assumption that two different campaigns share nothing is untested and untestable here.
4. **Published means are unbiased estimates of what happened.** Publication bias in this
   literature is plausible and unquantifiable with 32 campaigns; it is a limitation, not a
   correction term.
5. **Bed rest is an analogue.** Nothing in this framework establishes that its coefficients
   transfer to actual microgravity. The 14 spaceflight rows in the dataset are far too few to
   test it, and 8 of them are lumbar multifidus.
6. **Missingness is not informative.** Rows lacking a dispersion or an age are assumed to be
   missing for reasons unrelated to the size of the effect.

## 16. What this framework will not claim

- No clinical or operational readiness.
- No individual-level prediction.
- No causal statement from SHAP or from any model coefficient.
- No accuracy claim that was not produced by leave-one-cohort-out validation.
- No result whose number cannot be regenerated by `make all` from the frozen dataset.
- No implied study count beyond what the screening log supports.

## 17. Before the first run

Two of the three blockers are cleared. Both were cleared by building a reviewable table
rather than by editing the frozen dataset, so the assignment can be argued with, changed, and
re-run without a new dataset version.

| # | Blocker | State |
|---|---|---|
| 1 | `muscle_function_class` was `NA` on all 737 rows | **Cleared.** [`data/muscle_map.csv`](../data/muscle_map.csv) classifies all 51 muscles — 19 antigravity extensors, 8 flexors, 24 mixed — each with a written reason. Assigned from mechanical role first and fibre-type composition second ([Johnson et al. 1973](https://doi.org/10.1016/0022-510X(73)90023-3)). **Needs the partner's physiological sign-off before a coefficient is quoted**, and that review is a line edit in one CSV, not a re-extraction |
| 2 | `measurement_site` carried both `NA` and `na` plus 38 free-text strings | **Cleared.** [`data/measurement_site_map.csv`](../data/measurement_site_map.csv) resolves every string into `site_kind` and, where the paper gave one, a position along the segment |
| 3 | Both tables reviewed against the schema's controlled vocabulary | Open — Both |

The two judgement calls in the muscle map that a physiologist may well overturn, and which
are therefore flagged here rather than buried in a CSV:

- **`rectus_femoris` is `mixed`, not an antigravity extensor.** It extends the knee but flexes
  the hip, and it consistently atrophies less than the monoarticular vasti. Classifying it
  with them would blunt exactly the contrast claim 2 rests on.
- **`tibialis_anterior` is a `flexor` despite being slow-fibre dominant.** Roughly 73% type I,
  but it lifts the foot rather than carrying body weight. It is the cleanest test in the
  corpus of whether unloading atrophy tracks mechanical role or fibre type — and the answer
  the literature gives is mechanical role, which is why the classification is built on role.

The deep posterior compartment is classified the same way: `flexor_digitorum_longus`,
`flexor_hallucis_longus` and `tibialis_posterior` are named for what they do to the toes, but
what they do to the ankle is plantarflexion, so they sit with the antigravity extensors.

## 18. References

- Marusic U, Narici M, Šimunič B, Pišot R, Ritzmann R. Nonuniform loss of muscle strength and
  atrophy during bed rest: a systematic review. *J Appl Physiol* 2021;131(1):194–206.
  [doi:10.1152/japplphysiol.00363.2020](https://doi.org/10.1152/japplphysiol.00363.2020)
- Assink M, Wibbelink CJM. Fitting three-level meta-analytic models in R: a step-by-step
  tutorial. *Quant Methods Psychol* 2016;12(3):154–174.
  [doi:10.20982/tqmp.12.3.p154](https://doi.org/10.20982/tqmp.12.3.p154)
- Harrer M, Cuijpers P, Furukawa TA, Ebert DD. *Doing Meta-Analysis with R: A Hands-On Guide.*
  Chapman & Hall/CRC, 2021, ch. 12.
- Viechtbauer W. Conducting meta-analyses in R with the metafor package. *J Stat Softw*
  2010;36(3):1–48. [doi:10.18637/jss.v036.i03](https://doi.org/10.18637/jss.v036.i03)
- Crippa A, Discacciati A, Bottai M, Spiegelman D, Orsini N. One-stage dose–response
  meta-analysis for aggregated data. *Stat Methods Med Res* 2019;28(5):1579–1596.
  [doi:10.1177/0962280218773122](https://doi.org/10.1177/0962280218773122)
- van der Ploeg T, Austin PC, Steyerberg EW. Modern modelling techniques are data hungry: a
  simulation study for predicting dichotomous endpoints. *BMC Med Res Methodol* 2014;14:137.
  [doi:10.1186/1471-2288-14-137](https://doi.org/10.1186/1471-2288-14-137)
- Higgins JPT et al., eds. *Cochrane Handbook for Systematic Reviews of Interventions*, §9.6.4
  (meta-regression) and ch. 10.
- Geissbühler M, Hincapié CA, Aghlmandi S, Zwahlen M, Jüni P, da Costa BR. Most published
  meta-regression analyses based on aggregate data suffer from methodological pitfalls.
  *BMC Med Res Methodol* 2021;21:123.
  [doi:10.1186/s12874-021-01310-0](https://doi.org/10.1186/s12874-021-01310-0)
- Lundberg SM, Lee S-I. A unified approach to interpreting model predictions. *NeurIPS* 2017.
