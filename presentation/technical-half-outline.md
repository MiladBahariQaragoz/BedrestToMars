# Technical half: final slide plan (6 minutes, 5 slides)

Source: the final report on branch `feat/report`. Every number is copied from it.
The meta-regression (tier 1) is covered by the partner, so it is left out here.

Naming: call the model **"a newly released language model built for probabilistic classification"**. Figures F4 to F9 in `figures/` print "Jev" (F5 also prints "TypeSafe"), so relabel them before use.

---

## 1. How we test (~1 min)
**Figure:** F4_framework.svg (relabel)

- 346 measurements, but only **32 independent studies (campaigns)**. The study is the unit, not the row.
- Hold out one whole study, train on the other 31, predict the held-out one. Repeat 32 times.
- Code checks that no study is ever on both sides of the split.
- Everything is compared with one yardstick: **a curve that only knows the number of days in bed**.

## 2. Machine learning vs the curve (~1 min)
**Figure:** F5_models.svg (relabel)

- Ridge, random forest, SVR, gradient boosting, plus TabPFN (a network pretrained for small tables).
- Error on unseen studies: curve **3.16** points, best model (random forest) **3.18**, TabPFN **3.22**. Nobody beats the curve.
- They do learn the muscle pattern (R² goes from 0.14 to 0.27–0.39), but that doesn't lower the error on a new study.
- Why: 32 studies is too few. What makes one study differ from another isn't in any column.

## 3. The language model: what we built and what it got (~1.5 min)
**Figures:** F9_jev_example.svg (left), F6_jev_campaigns.svg or F8_jev_scatter.svg (right). Relabel both.

- **The idea:** ML only saw coded columns. This model reads the study described in words.
- **What it is shown:** who the participants were, what they did, which muscle, which scanner, the day, the days curve, and as many rows from the *other* studies as fit.
- **What it is asked:** never "give me a number". Instead: "which of these 2-point ranges will the result fall in?" It returns a probability for each range, and our code turns that into a number.
- **What it never sees:** the held-out study, or any paper, author or study name. Checked on every request.
- **Result:** error **2.71 vs 3.13** points for the curve (13% lower). It wins on **20 of 32** studies. The gain is 0.42 points (95% CI 0.13 to 0.73), the only method whose interval stays above zero.

## 4. How we know it's real (~1.5 min)
**Figure:** F7_jev_checks.svg (relabel)

Each check, and what it would mean if it failed:

| Worry | Check | Result |
|---|---|---|
| It recognised famous papers and remembered the answer | Remove everything that identifies a study | Still wins (0.30 point gain) |
| | Ask it outright which study this is | Of the 3 studies giving most of the gain, it names only 1 |
| It ignores the data we give it | Shuffle the other studies' numbers | Gain turns into a loss (−1.25) |
| | Give it no data at all | Much worse than the curve (5.85) |
| Wording luck | Reorder rows, shift the ranges | Error moves 1–3%, still wins |
| Randomness | Send the same requests again | Answers shift ~0.17, far below the 0.42 gain |

Small footnote line: *Added after the ML result; confidence ranges are too narrow, so we quote only the point forecast.*

## 5. Conclusions, limitations, next steps (~1 min)
- **Conclusions:** with 32 studies, ML can't beat a simple days curve. A language model reading the other studies' data beats it by a small, checked margin.
- **Limitations:** only 32 studies, no data past 119 days, mostly young men, group averages rather than individuals, bed rest isn't spaceflight.
- **Next:** fix the model's confidence ranges, check results without the largest study, extrapolate to 180 days.

## If asked
- **"Did it meet your target?"** We set a 15% target before running it. It got 13% on error and 17.7% on the probabilistic score (CRPS). So it's close, not a clear pass.
- **"Was this planned?"** No. It was added after the ML result, but every check and its pass rule was written down before we ran it.
