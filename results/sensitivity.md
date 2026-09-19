# Sensitivity analyses

Each row is the primary pipeline with one declared change. The headline coefficient
is the duration term of the headline form; the error is out-of-cohort, campaign-
weighted, from the same leave-one-cohort-out design as everything else.

S6 needs a dispersion *of the change*, which only **160 of 342 rows** carry, across **7 of 31 campaigns**. That is the finding as much as the coefficient is:
the literature mostly does not publish what inverse-variance weighting needs, which
is why `n_analysed` is the primary weight rather than a compromise.

| # | Analysis | Weights | Rows | Campaigns | Duration coefficient (95% CI) | LOCO MAE |
|---|---|---|---|---|---|---|
| — | Primary - every row, weighted by participants analysed | n_analysed | 342 | 31 | -16.59 (-20.93 to -12.26) | 3.45 pp |
| — | Restricted to rows carrying a dispersion of the change, weighted by participants | n_analysed | 160 | 7 | -14.12 (-19.85 to -8.38) | 3.18 pp |
| S6 | S6 - the same rows, weighted by the inverse of each estimate's variance | inverse variance | 160 | 7 | -11.57 (-14.30 to -8.85) | 3.24 pp |

