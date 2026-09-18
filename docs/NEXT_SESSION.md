# Start here next time

Written 2026-09-18 at the end of the P3/P4 modelling work. Current state and every number so
far: [`STATUS.md`](STATUS.md). The plan itself has not changed: [`../PLAN.md`](../PLAN.md).

**Deadlines:** upload 10 October 2026, talk 15 or 16 October. Today's date when this was
written was 18 September, so the internal schedule has 10 days of buffer left in it.

---

## 0. First five minutes

```bash
cd ~/GoogleDrive/DGLRM
git status --short                # if files show as modified but look identical, it is CRLF
git checkout feat/ai-framework && git pull
PYTHON=~/.venvs/dglrm/bin/python make test     # expect 73 checks in 10 files, all passing
```

If `make venv` has never run on this machine, run it first — the environment cannot live in
the Drive folder (see `STATUS.md` §5).

Also still sitting in the project folder from the venv attempt: `rm -rf .venv .venv2`.

---

## 1. Tier 1 — the three-level meta-regression *(the big one)*

This is the project's primary scientific result and the only substantial piece of
`framework/DESIGN.md` that has no code behind it. Everything below is specified in §7 of that
document; it needs implementing, not designing.

- Fit `pct_change ~ f(duration) + muscle_family + arm_type + covariates` with random
  intercepts for cohort, study within cohort, and muscle within cohort.
- Weight by `n_analysed`; cluster-robust standard errors on `cohort_id`.
- Fit all three duration forms and report them side by side with AIC. The saturating form is
  the headline unless the spline shows a shape it cannot follow.
- Run it twice: subset A for the duration curve, subset B for the muscle ranking.
- Write `results/tier1_curve.json` and `results/tier1_muscle_ranking.csv`.

`statsmodels` is installed in the venv (`MixedLM` gives two levels; the third level and the
cluster-robust sandwich need to be built on top, or the model fitted by maximum likelihood
directly). Write the test first, as with every other module — `framework/tests/` shows the
pattern, and a synthetic dataset with known variance components is the right first test.

**Why it matters:** right now the project can say how *wrong* its predictions are, but not
how much muscle is lost per day with a confidence interval. Claims 1 and 2 of the talk both
need that number.

## 2. The five figures

`PLAN.md` §9 names them; none exist. In the order they earn their place:

| Fig | Content | Blocked by |
|---|---|---|
| F4 | The framework diagram: sources → screening → schema → dataset → folds → two tiers → evaluation | Nothing. **Do this first** — it carries the whole AI contribution and `PLAN.md` task 3.2 has been open since P3 |
| F2 | Duration–response: `pct_change` against `duration_days`, coloured by muscle family, fitted curve with band, control arms only | Tier 1 |
| F3 | Muscle vulnerability ranking with confidence intervals, sorted | Tier 1 on subset B |
| F1 | Corpus overview: screening flow plus a timeline strip of each campaign | Nothing — the PRISMA counts exist |
| F5 | Model comparison against the baseline, or the stability table | Nothing — `results/model_comparison.csv` exists |

Colourblind-safe palette, sample size on the figure itself, text no smaller than slide body
text.

## 3. Close out P4

- Run sensitivity analyses S1–S11 from `DESIGN.md` §12. S1 (composite-first), S2 (drop MEDES)
  and S4 (MRI volume only) are pre-registered as must-show.
- Extrapolate the saturating curve to 180 days with a **prediction** interval and the explicit
  statement that the longest observation is 119 days (`PLAN.md` task 4.7). Backup slide only.
- Ask the partner for the physiological sign-off on `data/muscle_map.csv` — it is a line edit
  in one CSV, and until it happens the coefficients can be computed but not quoted.
- Tag `results-v1.0` and merge `feat/ai-framework` into `main`. That formally closes P3 and P4.

## 4. Then P5 — report and slides

Seven days in the plan, report first. Two things are already written and should be lifted
rather than rewritten:

- **The methods section is `framework/DESIGN.md`.** It was written to be lifted.
- **The limitations section is `data/DATASET_CARD.md` §"Known limitations"** plus §15 of
  `DESIGN.md`. Between them they already name nine real limitations; `PLAN.md` asks for six.

The one thing the deck now needs that it did not need in September: **the null result is the
story, not a footnote.** Four model families, honestly validated, none beating a simple
duration curve — and the reason (31 campaigns, not 421 rows) is a better answer to "why not
just use machine learning?" than any accuracy number would have been. `STATUS.md` §4 has the
three claims in the order the evidence supports them.

## 5. Still unanswered from kickoff

`PLAN.md` task 0.2 — the DGLRM author instructions: slide format, aspect ratio, time limit,
disclosure slide, language, and which of the two days we present on. Open since 4 September.
Everything in P5 and P6 is built on assumptions until that arrives.

---

## Quick reference

```bash
PYTHON=~/.venvs/dglrm/bin/python make test       # 73 checks
PYTHON=~/.venvs/dglrm/bin/python make baseline   # results/baseline.json
PYTHON=~/.venvs/dglrm/bin/python make models     # results/model_comparison.*  (~2.5 min)
PYTHON=~/.venvs/dglrm/bin/python make all        # everything

python framework/muscle_map.py                   # print the muscle classification for review
python framework/measurement_site.py             # print the site mapping for review
python framework/data_loader.py                  # subset sizes and the class means
```

Conventions that have held so far and should keep holding: tests before code, one thing per
commit, `type: what and why` messages, push after every intentional commit, and nothing
touches `dataset_v1.0.csv` — a correction goes into the extraction tables and comes out as
v1.1 with its own tag.
