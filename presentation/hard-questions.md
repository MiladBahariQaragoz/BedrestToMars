# Hard questions for the talk, with answers

Source of truth: the final report on branch `feat/report` and `results/` there. Two numbers marked **(our check)** are not in the report. I computed them from `results/forecast_predictions.csv` for this list. Backup slides B1 to B4 are at the end of `bed-rest-to-mars-talk.pptx`.

## The five most dangerous questions

1. **"Without the three biggest studies, does the LLM gain survive?"** Barely. NASA SPRINT, Berlin BBR2-2 and MEDES LTBR give 56% of the total gain. Without them the gain is 0.20 pp, 95% CI −0.01 to 0.43 **(our check)**, so the interval touches zero. Defence: the model recognises only SPRINT of the three, and with all study details removed it still beats the curve on SPRINT (3.79 vs 5.92 pp). *(B2)*
2. **"20 of 32 is close to a coin flip."** Counting wins alone, a sign test gives p = 0.22 **(our check)**. The size of the wins matters more than the count. The mean gain is 0.42 pp, 95% CI 0.13 to 0.73. *(B2)*
3. **"Your must-show sensitivity analyses haven't been run."** True. S1 (composite-first), S2 (without MEDES LTBR) and S4 (MRI only) are listed as outstanding in the report. Only S6 (weighting) has been run, and it changed little. Say so directly. Don't claim the results are robust to these. *(B1)*
4. **"You added the LLM after ML failed. Isn't that p-hacking?"** It was added after the ML result, so it is not pre-registered. The method, every target and every check were committed to the repository before the first answer was requested. We present it as a finding, not the headline. *(B2)*
5. **"Could the LLM have read these papers during training?"** It can't be ruled out by any test. The strongest checks available are removing every identifying detail (the gain stays at 0.30 pp) and asking it to name the study (it was right 19% of the time, where guessing gives 8%). *(B2)*

## Data

6. **"Did you miss studies?"** The search covered PubMed, Scopus, Web of Science and NASA NTRS from 2013 on (5,731 records), plus 9 older studies. Embase wasn't searched because there was no institutional access, and 1,023 records weren't screened in the time available. *(B1; search strings on the search backup slide)*
7. **"One campaign dominates."** MEDES 90-day supplies 40% of all rows and a quarter of the modelling data. Scoring gives every study one vote, but the check without it (S2) is still to run. *(B1)*
8. **"You mix MRI, CT, DXA and ultrasound."** Each method gets its own term. DXA lean mass and ultrasound thickness show about 5 to 6 pp less loss than CT area, and MRI volume is within 0.5 pp of CT. The MRI-only check (S4) is still to run. *(B1)*
9. **"Who checked the extraction?"** Every value is traced to its DOI and to a page, table or figure. 674 of 742 rows are high confidence, and 19 were read off figures. No second person extracted the data independently. *(B1)*
10. **"Your muscle groups: who decided which muscle is which?"** The muscle classification still awaits sign-off by the scientific lead, which the report lists as a blocking item. This affects the co-author's muscle slide.
11. **"Why percent change? Papers report it differently."** Some papers print the mean of individual changes, others only group means, from which we recompute it. Both sit in one column. The check comparing them (S7) is still to run.

## Models and evaluation

12. **"Was the ML comparison fair?"** Hyperparameters were tuned inside each training fold, grouped by study. TabPFN needs no tuning and is built for small tables. All models saw the same inputs and folds. *(B3)*
13. **"Why not add age, sex or countermeasure type?"** With 32 studies there is room for about three study-level inputs. Age and sex barely vary within a study (271 of the 346 modelling rows come from men-only groups, our count), so they act as a study label. The 100 countermeasure rows are spread over 9 types. *(B3)*
14. **"Isn't a duration-only curve a straw man?"** Ridge regression uses duration plus muscle and the other inputs, and scores 3.28 vs 3.16 pp. Adding the muscle raises R² but not the error on a new study. *(B3)*
15. **"Would a nearest-neighbour method match the LLM?"** Not tested. If the gain comes from picking similar rows, a nearest-neighbour baseline is the obvious control, and it is a fair item for further work. *(B3)*
16. **"Why does muscle identity explain 30% of variance but not reduce error?"** R² is pooled over all rows, while error is averaged per study. Most of the remaining error is a shift shared by a whole study, and no input describes it. *(slide 10)*
17. **"Bootstrap intervals over 32 studies, are they reliable?"** They are approximate and wide on purpose. On the history arm there are only 5 studies, so we don't quote those intervals as results.
18. **"Why not the meta-regression with muscle terms as the baseline?"** It estimates rather than predicts, and isn't cross-validated. Ridge is the closest predictive equivalent and doesn't beat the curve.

## The LLM

19. **"You missed your own 15% target."** The error improvement is 13.3%. The probabilistic score (CRPS) improves by 17.7%, which meets its target. *(notes, slide 11)*
20. **"Its ranges are overconfident, so why trust it?"** We don't quote its ranges, only its single-number forecast. Recalibration is in further work.
21. **"Is it reproducible? LLMs change."** The model version is fixed, and all 430 answers are saved, so every number rebuilds without calling it. Identical requests differ by 0.17 pp on average. *(B4)*
22. **"Why does it work?"** Our interpretation is that it picks similar rows (same muscle, group, day) and weighs them. That is not a tested mechanism. *(B3)*
23. **"It ignores a study's own earlier scans. Doesn't that show it isn't reasoning?"** On that arm the help from earlier scans comes from the anchor our code adds, not from the model. We report this as a failed check.

## Use for missions

24. **"A Mars transit is about 180 days, and your data stop at 119."** Only one campaign reaches 119 days. The 180-day extrapolation is planned from the duration curve only, with a prediction interval, and labelled as an assumption. *(B4)*
25. **"Bed rest isn't spaceflight."** There are only 14 spaceflight rows, and 8 of them are one back muscle. That is too few to test whether results transfer. *(B4)*
26. **"Which countermeasure works?"** Countermeasure groups lose 3.7 pp less (95% CI 1.5 to 5.9), but this pools all types. *(B4)*
27. **"Can I predict my astronaut's loss?"** No. Every row is a group average. *(B4)*

## Referee questions on part 1 (backup slides 17 and 18; questions 28 to 31 have no slide, answer them orally)

28. **"Why were 1,023 records not screened?"** Search and screening were time-boxed to one week. They are the rest of the "maybe" set and 80 records waiting for a full text. Slide 6 counts them with the exclusions (3,516 = 2,493 excluded on title and abstract + 1,023 not screened in time). If asked, say plainly that the 1,023 were not read. *(oral)*
29. **"Who screened, and was it done twice?"** Criteria were written before screening. A rule-based triage sorted the records, then one person read the priority set and the top of the "maybe" set. There was no second screener. *(oral)*
30. **"84 full texts but 52 studies?"** 19 report muscle results only as charts without a baseline, 4 full texts were not available (one conference abstract is still used), 11 were excluded at full text. The report's own full-text counts are still being reconciled (draft note), so don't claim they add up exactly. *(oral)*
31. **"Why only from 2013?"** The search was time-boxed to one week. Older work enters through the 9 studies held before the search; 6 of their campaigns would otherwise be missing. Both known modelling papers published after 2013 were found by all three journal databases. *(oral)*
32. **"You grew from 15 to 52 studies after the abstract. Did the analysis change after seeing the data?"** Eligibility criteria were fixed before screening, the dataset was frozen (14 and 19 September) before the final models, and the curve shape was chosen by a rule declared before fitting. *(slide 17)*
33. **"Slide 5 shows 180 days, but the model stops at day 119."** The 14 spaceflight rows are post-flight measurements, so the during-unloading filter removes them with the 264 recovery rows. 8 of the 14 are lumbar multifidus. *(slide 17)*
34. **"Mostly young men?"** Rows, not people: men only 567, mixed 113, women only 40 (35 of them WISE-2005), not reported 22; healthy young 692, middle-aged 8, older 42. The results describe young men. *(slide 17)*
35. **"What is one row's percentage change?"** Follow-up against the same group's baseline, negative for loss, recomputed from printed values; a printed mean of individual changes is kept and labelled. Rows are weighted by participants because only 8 of 32 campaigns report the spread of the change. *(slide 17)*
36. **"Is each muscle line fitted separately?"** No. The day-60 values are fitted per group (subset B, 25 campaigns); the lines share one time course (τ = 60 days). Six of nine groups rest on four campaigns or fewer. *(slide 18)*
37. **"Why a saturating curve?"** Logarithmic, saturating and spline forms are within 1.3 AIC points. The data show the loss slows, not which curve. By day 119 the curve is at 86% of its plateau, −17.3% (95% CI −20.9 to −13.7). *(slide 18)*
38. **"How certain are the day-60 values?"** Calf −15.8% (−18.9 to −12.7), front thigh −10.1% (−13.6 to −6.6), hip rotators −1.9% (−3.9 to 0.2). Calf vs shin: 5.6 pp more loss (2.1 to 9.1), p = 0.003. Hip rotators and outer hip rest on one campaign each. *(slide 18)*
39. **"Is the calf result an artefact of scanning frequency?"** The order holds after adjusting for duration, countermeasure group and imaging method. The calf has 78 rows from 13 campaigns, second only to the front thigh. *(slide 18)*

## How the LLM's answer becomes one number (slide 10)

40. **"How do you turn 19 probabilities into one prediction?"** The probability-weighted mean of each range's midpoint (`framework/forecast.py`, `Bins.representatives` and `point`). The two open ranges count as half a step beyond their edge: below −30% counts as −31%, +4% and above as +5%. Recomputing the example on slide 10 from its cached answer gives −6.6%.
