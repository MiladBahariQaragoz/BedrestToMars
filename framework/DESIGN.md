# Framework Design — v1.0

**Status:** P3 deliverable (`PLAN.md` §7, task 3.1). Written against frozen dataset
`dataset_v1.0` (tag `dataset-v1.0`, SHA-256 `a253cbec…c02f7`).
**Branch:** `feat/ai-framework`
**Supersedes:** nothing. This is the first version.

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
with 31 independent campaigns in the modelling subset, a flexible learner is being asked to
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

## 3. The modelling subset

The frozen dataset holds every row that was extracted, marked but unfiltered, so the subset
is chosen here rather than baked into the file. Three predicates define it, applied in this
order:

| # | Predicate | Rows kept | Reason |
|---|---|---|---|
| 0 | All rows in `dataset_v1.0.csv` | 737 | |
| 1 | `phase == "bed_rest"` | 474 | Recovery answers a different question and enters only the reconditioning sensitivity analysis (schema rule 7) |
| 2 | Lower-limb muscles only — drops `multifidus`, `lumbar_erector_spinae`, `quadratus_lumborum`, `psoas`, `iliopsoas` | 421 | The abstract is about lower-limb atrophy; trunk muscles unload differently and would be answering another question inside the same coefficient |
| 3 | One tissue per measurement occasion (§5) | 342 | A model given both `quadriceps` and its four heads fits the same tissue twice (schema rule 4) |

After predicates 1 and 2: **421 rows, 41 studies, 31 independent cohorts, 13 distinct
unloading durations (5–119 days), 295 control and 126 countermeasure rows.** 369 rows are
MRI, 25 DXA, 15 CT, 12 ultrasound; 314 are MRI volume specifically.

**The sample size is 31, not 421.** Every design decision below follows from that. The
largest single campaign, the 90-day MEDES study, contributes 103 rows — 24% of the subset —
and the two Berlin campaigns another 106 between them.

### 3.1 Two subsets, because two claims

The talk makes two quantitative claims, and they do not want the same rows.

| | Subset A — duration–response | Subset B — muscle ranking |
|---|---|---|
| Supports | Claim 1: how much is lost by day *t* | Claim 2: which muscles are selectively vulnerable |
| Rows | 342 | 304 |
| Cohorts | **31** | 25 |
| Contents | Everything after predicate 3, including the 38 whole-segment rows (`whole_thigh`, `whole_lower_limb`, `whole_calf`) carried as their own muscle family | Named muscles only |

The difference is worth stating because it is not cosmetic. Six campaigns — `drummond_br7`,
`imbp_br21`, `lunhab_br10`, `planhab_br10`, `planhab_br21`, `tanner_br5` — report *only*
whole-segment measurements, and they are concentrated at 5 to 21 days, which is exactly where
the duration curve bends hardest. Excluding whole-segment rows to get a cleaner muscle
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

The dataset deliberately keeps both composite muscles and their components: 185 composite
rows (`quadriceps`, `triceps_surae`, `vasti`, `anterior_tibial_group`, …) and 236 component
rows. On 20 of the 89 measurement occasions in the subset, both are present —
the paper reported the quadriceps *and* its four heads, and a model handed both is fitting
the same tissue twice, inflating its own precision.

`composite_of` is populated on only 50 of the 185 composite rows, so the mapping cannot come
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
at mixed granularity, since only 12 of the 31 cohorts report components at all. The muscle
random effect in §7 is what makes that legitimate, and §12 runs the opposite preference
(composite-first) to show the conclusion does not depend on the choice.

## 6. Features

The covariate budget is set by the number of cohorts, not the number of rows. Cochrane's
guidance is ten studies per study-level covariate
([Handbook §9.6.4](https://handbook-5-1.cochrane.org/chapter_9/9_6_4_meta_regression.htm));
at 31 cohorts that permits **three study-level terms**. Variables that vary *within* a
cohort — muscle, arm, timepoint, modality — are far cheaper, because each cohort contributes
its own internal contrast, and those are where most of the interesting variation lives.

### 6.1 Modelled

| Feature | Level | Encoding | Why it earns a slot |
|---|---|---|---|
| `duration_days` | study | Nonlinear, three candidate forms (§7) | The primary exposure. Every claim in the talk rests on it |
| `muscle_family` | within-cohort | Categorical, from `config.yaml` | Claim 2 of the talk. Antigravity selectivity is the second-strongest finding in the corpus |
| `arm_type` | within-cohort | Binary, `control` / `countermeasure` | 126 countermeasure rows. Binary because at this N a dose ordinal would be fitting noise (`PLAN.md` task 2.8) |
| `is_composite` / `muscle_grain` | row | Binary | Composite measurements are systematically less extreme than their most affected component; without this the mixed granularity of §5 leaks into the muscle coefficients |
| `modality` + `outcome_type` | study | Categorical pair, collapsed to `MRI_volume` / `CT_CSA` / `DXA_lean_mass` / `ultrasound_thickness` | DXA lean mass and MRI volume do not measure the same thing (`PLAN.md` task 2.4). 314 of 421 rows are MRI volume, so this is mostly a correction term for a minority |
| `pct_estimator` | row | Binary | Which of the two estimators in §4 the row carries |

That is two of the three study-level slots (duration, modality-outcome). The third is held in
reserve for the age term below.

### 6.2 Stratification and sensitivity variables — recorded, not in the primary model

| Variable | Why not a feature | Where it is used instead |
|---|---|---|
| `age_mean`, `population` | 38 of 421 rows are older adults, all from one campaign. A coefficient would be a coefficient for that campaign | Sensitivity analysis; the third study-level slot if the reviewer asks |
| `sex`, `pct_female` | 347 rows men only, 31 women only, 25 mixed, 18 unstated. The confound with campaign is nearly total | Sex-stratified sensitivity analysis if N allows (`PLAN.md` task 4.5) |
| `cm_modality` | Eight categories across 126 rows, several with under ten | Descriptive table and a secondary model restricted to countermeasure arms |
| `measurement_site` | 515 of 737 rows say nothing, and the rest were free text until normalised into `site_kind` and `site_position_pct` (`framework/measurement_site.py`) | Within-muscle heterogeneity sensitivity analysis (S11) |
| `hdt_angle_deg`, `design` | 420 of 421 rows are the same analogue family; near-constant | Reported in the corpus description |
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

Subset A, 342 rows from 31 campaigns. Four families, exactly as the abstract states: linear regression (penalised - ridge, with the
penalty chosen inside the fold), random forest, support vector regression with an RBF kernel,
and gradient boosting.

### 8.1 Validation: leave-one-cohort-out

`cohort_id` is the fold unit. Not `study_id`, and never a random split. Two papers from the
Berlin campaign report the same participants; a random split puts those participants on both
sides of the fold boundary, and the reported error then measures memorisation
(`PLAN.md` §2, finding 3). Grouped cross-validation is the standard response to clustered
data, and leave-one-study-out is its established form in pooled analyses.

31 cohorts means 31 folds. Each fold trains on 30 campaigns and predicts one held-out
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
in `docs/STATUS.md`, not decided here.

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

Six modules, each with one job and a typed signature. No module reads a file that is not
declared in `config.yaml`, and no module contains a number that is not in `config.yaml`.

| Module | Responsibility | Key interface |
|---|---|---|
| `data_loader.py` | Read the frozen CSV, verify its SHA-256 against `dataset_v1.0.sha256`, apply the §3 predicates | `load(config) -> pd.DataFrame` |
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

`config.yaml` holds the subset predicates, the feature lists,
the duration forms, model families and their grids, the number of bootstrap replicates, and
the random seed. Changing an analysis means editing that file, and the file is committed with
the result it produced.

The framework diagram (`PLAN.md` task 3.2, `figures/framework.svg`) draws exactly this chain:
sources → screening → schema → frozen dataset → subset → features → LOCO folds → tier 1 and
tier 2 → evaluation → SHAP.

## 14. Reproducibility

`make all` regenerates every number and every figure from `data/dataset_v1.0.csv` and
`config.yaml`, on a clean checkout, with no manual step. This is blocking, not aspirational:
a number that cannot be regenerated cannot go on a slide (`PLAN.md` §15).

- The loader refuses to run if the dataset SHA-256 does not match, so a silent edit cannot
  reach a result.
- One seed, declared in `config.yaml`, set for every stochastic component.
- Package versions pinned in `requirements.txt`; the versions used are written into each
  results file.
- Every file in `results/` and `figures/` records the dataset tag and the git commit it came
  from.

## 15. Assumptions, stated plainly

1. **Group means, not people.** Every row is an arm mean. The framework predicts what a group
   of similar people would lose on average, and cannot say what one astronaut will lose.
2. **Percentage change is comparable across modalities after adjustment.** A 10% MRI volume
   loss and a 10% DXA lean-mass loss are treated as the same target value with a modality
   term separating them. This is an assumption, and S4 is its test.
3. **Cohorts are independent of one another.** Within-cohort dependence is modelled; the
   assumption that two different campaigns share nothing is untested and untestable here.
4. **Published means are unbiased estimates of what happened.** Publication bias in this
   literature is plausible and unquantifiable with 31 campaigns; it is a limitation, not a
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
