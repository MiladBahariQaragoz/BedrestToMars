# Sensitivity analyses

Each row is the primary pipeline with one declared change. The headline coefficient
is the duration term of the headline form; the error is out-of-cohort, campaign-
weighted, from the same leave-one-cohort-out design as everything else.

S6 needs a dispersion *of the change*, which only **161 of 346 rows** carry, across **8 of 32 campaigns**. That is the finding as much as the coefficient is:
the literature mostly does not publish what inverse-variance weighting needs, which
is why `n_analysed` is the primary weight rather than a compromise.

| # | Analysis | Weights | Rows | Campaigns | Duration coefficient (95% CI) | LOCO MAE |
|---|---|---|---|---|---|---|
| — | Primary - every row, weighted by participants analysed | n_analysed | 346 | 32 | -16.49 (-20.49 to -12.49) | 3.47 pp |
| — | Restricted to rows carrying a dispersion of the change, weighted by participants | n_analysed | 161 | 8 | -13.94 (-18.62 to -9.26) | 2.81 pp |
| S6 | S6 - the same rows, weighted by the inverse of each estimate's variance | inverse variance | 161 | 8 | -11.57 (-14.18 to -8.97) | 2.88 pp |

