# The fifth family: TabPFN

Added on `feat/tabpfn` (stacked on `feat/ai-framework`, based at `caa2812`). One page: why
it is here, what it is allowed to claim, and how it behaves on a machine without it.

## Why this family, and only this one

Tier 2's null result (`results/model_comparison.csv`, 2026-09-18) says the four comparative
families do not beat a duration-only curve at 31 campaigns. A fair question from the floor is
whether *any* learner could — including the ones pretrained on millions of datasets. TabPFN
(Hollmann et al., *Nature* 2025; open source, PriorLabs) is the strongest available answer to
that question: a tabular foundation model fitted **in-context** off its own pretraining,
explicitly built for small-N regression, with no hyperparameter search to leak across folds.
Adding it is cheap, and its result — whichever way it goes — sharpens the ceiling claim
rather than muddying it.

## What was declared

| Choice | Where | Value |
|---|---|---|
| Family name | `config.yaml` → `models.families` | `tabpfn` |
| Grid | `config.yaml` → `models.grids.tabpfn` | `{}` — fixed declared defaults, nothing to tune |
| Device | `config.yaml` → `models.tabpfn_device` | `cpu` (342 rows; keeps runs reproducible) |
| Seed | `config.yaml` → `seed` | passed as `random_state` |
| Search wrapper | `run_models.FixedSearch` | the fold loop and `chosen_parameters` stay uniform |

Validation is unchanged: the same leave-one-cohort-out folds, the same leakage assertions,
the same campaign-weighted aggregation and bootstrap as every other family. There is no inner
search because there is nothing to search — a prior-fitted network used in-context has no
hyperparameters chosen against our campaigns, so the one unrecoverable mistake in
`PLAN.md` §8 cannot occur for this family.

Importance for this family, if it is ever the best, is permutation-based: it is not a tree
ensemble, so SHAP's exact tree explainer does not apply (`explain.py` handles this already).

## Honest expectation

The out-of-cohort residual is dominated by between-campaign differences no feature in the
dataset carries (see the noise decomposition in the 2026-09-19 feasibility note). A better
prior over tabular functions does not create that information. The realistic outcomes are:
TabPFN lands with the other families (the ceiling claim gets stronger), or it edges slightly
ahead (still reported against the 15% bar). Either way the pre-registered rule decides what
may be said.

## Machines without it

`tabpfn` needs `pip install "tabpfn==2.0.9"` (it pulls torch, ~200 MB CPU wheel). Pin
2.0.9 deliberately: from the later major versions the checkpoint sits behind a one-time
browser license login against Prior-Labs' auth server, which cannot be completed from a
non-interactive session — we tried — while 2.0.9 downloads the same v2 regressor checkpoint
from Hugging Face directly and is the version this family was validated on. Without the
package, `models.available()` silently omits the family, `make models` runs the original
four, and every other result is unchanged. The optional section of `requirements.txt`
documents this. Tests that need the package return early when it is absent, so the suite
passes everywhere.

## Run it

```bash
pip install "tabpfn==2.0.9"                          # in the project venv
PYTHON=<venv>/bin/python make models                 # regenerates model_comparison.*
# provenance in results/model_comparison.json records the tabpfn version used
```
