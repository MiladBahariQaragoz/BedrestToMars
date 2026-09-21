# Start here next time

Written 2026-09-18 at the end of the P3/P4 modelling work, updated 2026-09-19 when tier 1
was implemented and again the same day when `dataset_v1.1` pooled a NASA campaign and every
result was refitted. Current state and every number so
far: [`STATUS.md`](STATUS.md). The plan itself has not changed: [`../PLAN.md`](../PLAN.md).

**Deadlines:** upload 10 October 2026, talk 15 or 16 October. Today's date when this was
written was 18 September, so the internal schedule has 10 days of buffer left in it.

---

## 0. First five minutes

```bash
cd ~/GoogleDrive/DGLRM
git status --short                # if files show as modified but look identical, it is CRLF
git checkout feat/nasa-integration && git pull   # the tip: feat/ai-framework plus v1.1
PYTHON=~/.venvs/dglrm/bin/python make test       # expect 185 checks in 17 files, all passing
```

If `make venv` has never run on this machine, run it first — the environment cannot live in
the Drive folder (see `STATUS.md` §5).

Also still sitting in the project folder from the venv attempt: `rm -rf .venv .venv2`.

---

## 1. Tier 1 — done, and what it left open

Implemented on 19 September: `framework/tier1.py`, `framework/run_tier1.py`, 27 checks, and
`results/tier1_curve.json` plus `results/tier1_muscle_ranking.csv`. It is fitted by maximum
likelihood rather than through `statsmodels`, for the reasons in `STATUS.md` §5. The numbers
it produced are in `STATUS.md` §3 and the headline is **−2.41 pp of muscle per doubling of
unloading duration** (95% CI −3.26 to −1.56 against `dataset_v1.1`), with the muscle ranking
now carrying intervals.

All three of the decisions it raised have been taken:

- **The tau grid stays as declared.** It ends at 90 days and the profile stops there, so the
  saturating curve is still falling at the longest observation and its **−19.9% asymptote is
  an extrapolation past 119 days**. Widening the grid after reading the result would have
  been re-declaring a pre-registration, so it was not done. Quote the curve inside the
  observed range, and if the report wants an asymptote, say what it is.
- **The reference muscle family is knee extensors**, chosen for having 86 rows across 22
  campaigns rather than dorsiflexors' 8 across 4. The antigravity comparison is emitted
  separately as `key_contrasts` so that the choice of reference cannot change it.
- **S6 is run.** Inverse-variance weighting needs a dispersion of the change, which only 161
  of 346 rows from 8 of 32 campaigns carry. `results/sensitivity.md` has the three-row table.
  It is not neutral and cannot be adjudicated on 8 campaigns.

## 1b. Three things waiting on a decision, not on work

None of them blocks the talk. The first two block making the repository public.

- **The repository has no `LICENSE` file.** Public and unlicensed means readable but not
  reusable — nobody may use the code or the dataset. Two licences are wanted, because the
  repository holds two kinds of thing: a permissive software licence for the code, CC BY 4.0
  for the dataset and the documentation. See [`licensing.md`](licensing.md) §5–6.
- **`data/search/fulltext_digests/` cannot go public as it stands.** The 68 committed files
  reproduce paper tables and sentences verbatim, and at least 30 of them come from closed,
  bronze or green open-access articles that grant no reuse right. The recommendation is to
  stop tracking the folder — nothing downstream depends on it, because the numbers it helped
  find are in the extraction tables with their own provenance. Note that dropping them from
  the working tree does not remove them from the history; if the history is published too,
  that is a separate decision and it is cheaper now than after the first clone.
  [`licensing.md`](licensing.md) §2.
- **The `repository` value added to `data_source` in v1.1 has one lead's signature.**
  `data/schema.md` is frozen and says a change needs both. It is README open question 1.1, and
  the reasoning is in `data/reconciliation_log.md` §v1.1.

Two smaller ones, for whoever is in the files anyway:

- **NASA asks to be acknowledged** as the source of the data in `data/nasa/`, and nothing in
  the repository does it yet. Draft text is in [`licensing.md`](licensing.md) §6.
- **`extraction_figures.csv` fails `validate_extraction.py` unless `--partial` is passed** —
  23 rows lack `sex` or an age. This is pre-existing and was not introduced by v1.1; it fails
  the same way on `feat/ai-framework`. Either the file is a partial table and the validator
  should recognise it the way it recognises `*_partial.csv`, or the rows want filling.

## 2. The five figures

`PLAN.md` §9 names them; none exist. In the order they earn their place:

| Fig | Content | Blocked by |
|---|---|---|
| F4 | The framework diagram: sources → screening → schema → dataset → folds → two tiers → evaluation | Nothing. **Do this first** — it carries the whole AI contribution and `PLAN.md` task 3.2 has been open since P3 |
| — | *(every figure is now unblocked: tier 1 was the only dependency)* | |
| F2 | Duration–response: `pct_change` against `duration_days`, coloured by muscle family, fitted curve with band, control arms only | Nothing — `results/tier1_curve.json` carries the curve and its band on a one-day grid |
| F3 | Muscle vulnerability ranking with confidence intervals, sorted | Nothing — `results/tier1_muscle_ranking.csv` is already sorted worst first, with intervals |
| F1 | Corpus overview: screening flow plus a timeline strip of each campaign | Nothing — the PRISMA counts exist |
| F5 | Model comparison against the baseline, or the stability table | Nothing — `results/model_comparison.csv` exists |

Colourblind-safe palette, sample size on the figure itself, text no smaller than slide body
text.

## 3. Close out P4

**The figures are now the critical path** — nothing else blocks them.

- Run the rest of the sensitivity analyses from `DESIGN.md` §12 — S6 is done and
  `framework/sensitivity.py` shows the shape the others take. S1 (composite-first),
  S2 (drop MEDES) and S4 (MRI volume only) are pre-registered as must-show.
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
PYTHON=~/.venvs/dglrm/bin/python make test       # 185 checks
PYTHON=~/.venvs/dglrm/bin/python make baseline   # results/baseline.json
PYTHON=~/.venvs/dglrm/bin/python make models     # results/model_comparison.*  (~2.5 min)
PYTHON=~/.venvs/dglrm/bin/python make tier1      # results/tier1_curve.json, results/tier1_muscle_ranking.csv
PYTHON=~/.venvs/dglrm/bin/python make all        # everything

python framework/muscle_map.py                   # print the muscle classification for review
python framework/measurement_site.py             # print the site mapping for review
python framework/data_loader.py                  # subset sizes and the class means
```

Conventions that have held so far and should keep holding: tests before code, one thing per
commit, `type: what and why` messages, push after every intentional commit, and nothing
touches a frozen dataset — a correction goes into the extraction tables and comes out as a
new version with its own tag. That path has now been walked once: `dataset-v1.1` on
2026-09-19, with v1.0 left intact and still rebuilding.
