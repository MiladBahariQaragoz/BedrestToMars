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
PYTHON=~/.venvs/dglrm/bin/python make test       # expect 223 checks in 19 files, all passing
```

If `make venv` has never run on this machine, run it first — the environment cannot live in
the Drive folder (see `STATUS.md` §5).

Also still sitting in the project folder from the venv attempt: `rm -rf .venv .venv2`.

---

## 1. Tier 1 — done, and what it left open

Implemented on 19 September: `framework/tier1.py`, `framework/run_tier1.py`, 27 checks, and
`results/tier1_curve.json` plus `results/tier1_muscle_ranking.csv`. It is fitted by maximum
likelihood rather than through `statsmodels`, for the reasons in `STATUS.md` §5. The numbers
it produced are in `STATUS.md` §3 and the headline is **−2.99 pp of muscle per doubling of
days of bed rest** (95% CI −3.44 to −2.53 against `dataset_v1.1`), with the muscle ranking
carrying intervals. That is the figure since 21 September, when every tier moved from the
campaign's planned length to the day of the scan (`DESIGN.md` §9.4); before it, interim scans
entered at the end of their campaign and the headline read −2.41 pp.

All three of the decisions it raised have been taken:

- **The tau grid stays as declared.** Widening it after reading a result would have been
  re-declaring a pre-registration. The question has since gone away: on the day of the scan
  the profile turns over at 60 days, inside the grid, and the eventual loss is −17.3%
  (−20.9 to −13.7), which the curve is 86% of the way to by day 119.
- **The reference muscle family is knee extensors**, chosen for having 86 rows across 22
  campaigns rather than dorsiflexors' 8 across 4. The antigravity comparison is emitted
  separately as `key_contrasts` so that the choice of reference cannot change it.
- **S6 is run.** Inverse-variance weighting needs a dispersion of the change, which only 161
  of 346 rows from 8 of 32 campaigns carry. `results/sensitivity.md` has the three-row table.
  On the day of the scan it barely moves the coefficient, and 8 campaigns could not settle it
  either way.

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

## 2. The five figures — drawn

Drawn on 21 September by `framework/plot_figures.py`, from the results files, and rebuilt by
`make figures`. Each is a full 16:9 slide in `figures/`, SVG for the deck and PNG for anything
else, with no text under the 24 pt slide body and every title computed from the numbers it
states.

| Fig | File | What it shows |
|---|---|---|
| F1 | `figures/F1_corpus` | Screening flow counted from the search tables, and the 742 dataset rows walked down to the 346 modelled - 264 recovery scans, 53 trunk muscles, 79 counted twice |
| F1b | `figures/F1b_campaigns` | One bar per campaign with its scan days - backup |
| F2 | `figures/F2_duration` | Control-arm measurements on the day of the scan, by functional class, with the tier-1 curve and its band |
| F3 | `figures/F3_muscles` | The muscle ranking at day 60 with intervals, and each family's rows and campaigns |
| F4 | `figures/F4_framework` | The framework: search to dataset to folds to the three tiers (`PLAN.md` task 3.2) |
| F5 | `figures/F5_models` | Every model's out-of-campaign error against the duration curve |
| F6 | `figures/F6_jev_campaigns` | Jev's gain in each held-out campaign: better in 20 of 32 |
| F7 | `figures/F7_jev_checks` | The gain under every check - it holds when only the presentation changes and collapses when the data is taken away |
| F8 | `figures/F8_jev_scatter` | Forecast against actual for the curve and for Jev, all 346 rows |
| F9 | `figures/F9_jev_example` | One forecast as Jev gives it: a probability per range. The row is chosen by rule - Jev's median error - not by hand |

What is left for them is judgement, not work. `PLAN.md` §9 caps the deck at five figures and
there are now ten: which five carry the talk and which become backup slides is a decision for
both of us. And whether the partner wants F2 coloured by class or by family.

## 3. Close out P4

**The figures are done; the report is now the critical path.**

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
PYTHON=~/.venvs/dglrm/bin/python make test       # 223 checks
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
