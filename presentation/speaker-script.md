# Speaker script: From Bed Rest to Mars

Taken from the speaker notes in the deck (bed-rest-to-mars-talk.pptx). Part 1 (slides 3 to 8) is Niloufar's; part 2 (slides 9 to 14) is Milad's. Backup slides 15 to 21 are for questions only.

### Slide 1: Title slide

Intro (Niloufar). Placeholder: add the opening sentence.

### Slide 2: Agenda

Agenda. Part 1 (Niloufar): why this matters and why bed rest, how we searched the literature, and what the dataset contains, including which muscles lose most. Part 2 (Milad): how we tested the models, the models and their results with the validity checks of the LLM, and the conclusion.

### Slide 3: Motivation: predicting lower-limb muscle atrophy (Niloufar)

Opening of part 1 (Niloufar), about forty-five seconds.

Muscle atrophy, especially in the legs, is one of the main problems of long-duration spaceflight. Our question, in the title, is whether the amount of atrophy can be predicted.

Why it matters: a prediction lets crews and planners act early, match exercise and nutrition to the expected loss, focus monitoring on the muscles that lose most, protect strength and function, and plan long missions where exercise equipment is limited.

On the right is the ground model we rely on: volunteers lie in bed tilted six degrees head-down for weeks to months. The circles show a calf cross-section before and after unloading; how much each muscle loses comes later, in the muscle section.

### Slide 4: From bed rest to Mars: analogue and application (Niloufar)

Part 1 (Niloufar), about forty-five seconds.

Direct spaceflight data on muscle are scarce, so we use head-down bed rest, the standard ground analogue: volunteers lie tilted six degrees head-down and their legs carry no weight, under controlled conditions. Bed rest is not the same as spaceflight, but it is a sound starting point to build and test prediction models.

Mars in our title stands for the long-term application. The panel compares the two missions on one time scale. A Moon mission lasted about twelve days, and the crew could be home in three. A Mars mission takes about two and a half years: six months to get there, about five hundred days on the surface, six months back. There is no early return in an emergency, and after six months in weightlessness the crew must leave the spacecraft and work on the surface. Mission figures: Apollo 17, and NASA's Mars Design Reference Architecture 5.0.

In the bottom row, atrophy prediction, together with strength and power testing, could one day help keep the crew ready for work on arrival. The dashed steps are future use, and applying the model on a real mission needs validation with spaceflight data first.

### Slide 5: Range of unloading durations and studies (Niloufar)

Part 1 (Niloufar), about forty-five seconds.

When we submitted the abstract, our dataset held 15 bed-rest studies, covering 14 to 119 days of unloading. After submission we extended it. The final dataset has 52 studies, published from 1992 to 2026, and covers 5 to 180 days. The orange part of the lower bar is not bed rest: the stretch beyond 119 days comes from spaceflight, where three studies measured crews after about 180 days.

The chart below shows how many of these studies were published each year, and the colours show how long the unloading lasted. Most of the literature is recent: 37 of the 52 studies are from 2016 or later. Short studies of up to two weeks are the most common; long campaigns of two to four months are rarer.

### Slide 6: Literature search and study selection (Niloufar)

Part 1 (Niloufar), about one minute.

We searched four databases, PubMed, Scopus, Web of Science and NASA's technical reports, and added older work we had collected before the search, nine studies from before 2013 and one campaign from NASA's open bed-rest data. In total, 5,741 records. After removing duplicates, 3,600 records remained, and 3,516 were excluded at this stage. If asked: 2,493 were excluded on title and abstract, mostly for no unloading model or no muscle outcome; the other 1,023 were not screened in the time available and did not go further.

We sought 84 full texts. Most were lost because 19 studies show their muscle results only as charts, without a baseline value, so we could not extract them; 4 full texts were not available and 11 were excluded. These full-text counts are as recorded in our screening log and are still being reconciled with the dataset, so do not claim they add up exactly. 52 studies were included.

Several papers often report the same bed-rest campaign, so we merged papers on the same cohort. The final dataset has 36 independent campaigns and 742 rows.

### Slide 7: Dataset composition (Niloufar)

Part 1 (Niloufar), about one minute.

The final dataset has 742 rows. Each row is one muscle outcome: one muscle, in one group, at one scan day. One campaign can therefore give many rows, for several muscles, time points or groups.

For each outcome we extracted the length of unloading, the day of the scan, the muscle, the participants (group size, share of women, age), whether the group had a countermeasure, the imaging method, and how muscle size was measured. Our prediction target is the percentage change in muscle size from baseline.

Left table: 742 rows from 52 studies and 36 independent campaigns, covering 51 muscles or muscle groups; 470 rows are control groups and 272 countermeasure groups; 478 were measured during bed rest and 264 in recovery. 742 rows does not mean 742 people: one campaign gives rows for several muscles, groups and scan days.

Right table: most rows are MRI volumes. CT gives cross-sectional area, DXA gives lean mass of the leg, and ultrasound gives thickness or area.

### Slide 8: Muscle atrophy by muscle group (Niloufar)

Part 1 (Niloufar), about one minute.

Muscles do not lose size equally. Each line shows how much a muscle group shrinks over the days of bed rest, for groups without a countermeasure. The dashed line reads the values at day 60.

The calf, the plantar flexors, loses most: about 16 percent at day 60, almost 6 percentage points more than the front thigh. The shin, the front thigh and the back thigh lose about 10 percent. Hip muscles lose least.

How the lines are drawn: the day-60 values are the estimates of our meta-regression for each muscle group. The shape over time is the one curve the model fits to all muscles, rising fast in the first weeks and levelling off; time constant 60 days. Hip rotators and outer hip rest on a single campaign each, so treat those two with care.

### Slide 9: Evaluation: leave-one-campaign-out validation (Milad)

About one minute.

Each row in our data is one measurement: a group of volunteers, one muscle, one day of bed rest. The inputs are the day of the scan, the muscle family, whether the group did a countermeasure, how the muscle was imaged, and whether the value covers a group of muscles. The output is the percentage change in muscle size from before bed rest.

We have 346 rows, but they come from 32 independent campaigns, because several papers report the same volunteers. So we test by holding out one whole campaign, training on the other 31 and predicting the held-out one, 32 times. The code checks that no campaign appears on both sides of a split.

The score is the mean absolute error in percentage points, averaged so that each campaign counts once. Every model is compared with a duration-only curve, which uses the number of days and nothing else.

### Slide 10: LLM-based probabilistic classifier: input and output (Milad)

About a minute and a half.

The ML models only saw coded columns. Here we gave each measurement, written out in words, to a newly released language model built for probabilistic classification. It is not a chat model that writes text: you give it a described situation and a fixed list of options, and it returns a probability for each option, nothing else.

On the left is a real request from our cache. It describes the volunteers, the protocol, the muscle and how it was scanned, and the day. It also contains the duration curve fitted on the other 31 campaigns and as many rows from those campaigns as fit, most similar first. The question asks which of 19 ranges the change will fall in.

On the right is what came back for this row: a probability for each range. We never ask the model for a number. Our code turns the probabilities into a prediction, here minus 6.6 percent against an observed minus 9.4. We chose this row because its error is the model's median error.

The request never contains the held-out campaign's own data or any name that could identify a paper, and the code checks that on every request. Every answer is cached, so all our numbers can be rebuilt without calling the model again.

### Slide 11: Model comparison on held-out campaigns (Milad)

About a minute and a half.

We compared four standard models, ridge regression, random forest, support vector regression and gradient boosting, tuned inside each training fold, and later TabPFN, a neural network pretrained for small tables. On the left is the error on the held-out campaign. The duration curve scores 3.16 percentage points and the best ML model, the random forest, 3.18: none of them is lower than the curve. On the right, the ML models explain two to three times more variance, because they learn that the calf loses more than the hip. Most of the error left is a shift that applies to a whole campaign, from its scanner, its volunteers or its protocol, and none of our columns describes it. We had committed in advance to report this result whichever way it came out.

The language model is at the bottom. Its error is 2.71 percentage points, the lowest of all models, and it explains the most variance, 0.43.

Compared with the curve on the same rows and scored the same way, the error falls from 3.13 to 2.71, a gain of 0.42 points. The 95 percent confidence interval runs from 0.13 to 0.73, so even the most pessimistic estimate is an improvement. It is closer than the curve in 20 of the 32 campaigns. No other method has a gain whose interval stays above zero.

If asked about a target: we had set a 15 percent improvement target. The error improvement is 13.3 percent and the probabilistic score improvement 17.7 percent.

### Slide 12: Robustness and validity checks of the LLM prediction (Milad)

About a minute and a quarter.

We wrote down each check and its pass rule, and committed them to the repository, before running it.

Language models have read many papers, so the model might recognise a published campaign and recall its result. With every identifying detail removed, the gain is 0.30 points and its interval stays above zero. When we asked the model to choose the campaign's name from a list of options, it was right 19 percent of the time, where guessing gives 8 percent. If asked: of the three campaigns behind most of the gain, it named only one.

When we shuffle the other campaigns' values, the gain turns into a loss of 1.25 points, and with no reference data the error rises to 5.85. The gain comes from reading those data.

Reordering the rows or shifting the range edges changes the error by 1 to 3 percent. Repeating 20 requests moves the predictions by 0.17 points on average, well under the 0.42 gain.

Three limitations: we added this model after the ML result; its 80 percent ranges contain the truth only 62 percent of the time, so we quote only point predictions; and when given a campaign's own earlier scans, it does not use them.

### Slide 13: Conclusions, limitations and further work (Milad)

About thirty seconds.

With 32 independent campaigns, standard ML models and TabPFN do not beat a curve that only knows the number of days. An LLM-based probabilistic classifier that reads each campaign's description and the other campaigns' data reduces the error from 3.13 to 2.71 points. The main limitation is the small sample of 32 campaigns, mostly young men, with no bed-rest data beyond day 119. Every row is a group average, so the model predicts the average loss of a group of volunteers. It cannot yet predict the risk for an individual astronaut.

Further work has three steps. First, estimate how susceptible each muscle is relative to a reference muscle, and combine those coefficients with baseline muscle volumes to estimate total lower-limb volume loss; the dataset has 30 group time points where three or more muscles were scanned together, across 14 campaigns, so this can be tested. Second, move from group averages to individuals with participant-level data over time, and link muscle loss to strength and function. Third, validate on independent campaigns and on spaceflight data before building any personal risk-assessment tool.

### Slide 14: Thank you for listening (Milad)

Close (Milad). Thank the audience and invite questions. The backup slides that follow answer the questions we expect: part 1 on slides 17 and 18, data and search on 15 and 16, part 2 on 19 to 21.

---

## Backup slides (only if asked)

### Slide 15: Backup: dataset coverage and limitations

Backup. Be direct that the three must-show sensitivity analyses (composite-first, without MEDES, MRI only) have not been run yet. Only the weighting check has, and it changed little.

### Slide 16: Backup: literature search sources and query

Backup. All four strings are in the report appendix, copied from docs/literature-review/search_log.md. PubMed uses the same two blocks with MeSH terms and the humans filter; Scopus and Web of Science exclude animal studies in the query. The 2013 limit is the main weakness: only two of ten known modelling papers fall inside the window, and the known-item test without the limit was not run. Embase was not searched for lack of access; it indexes conference abstracts the other databases miss.

### Slide 17: Backup: dataset expansion and composition

Backup, part 1 (Niloufar). Expansion: the eligibility criteria in the report's Table 2 were written before screening; dataset version 1.0 was frozen on 14 September and 1.1 on 19 September, and every result is fitted on 1.1. The rule for the curve: the saturating form is the headline unless another form beats it by at least 4 AIC points. Spaceflight: the dataset keeps the spaceflight rows, flagged, but they are post-flight measurements, so the during-unloading filter removes them. Weighting: inverse-variance weighting would need the spread of the change, which most papers do not print; the check that compares both weightings moved the duration effect by under 1 pp.

### Slide 18: Backup: certainty of the muscle-group curves

Backup, part 1 (Niloufar). Be precise about slide 8: the coloured dots at day 60 are the model's estimates for each muscle group, with the intervals shown here. The lines are drawn with one shared time course scaled to those values, so they show the shape the model assumes, not a separate fit per muscle. The intervals are 95% cluster-robust, which means they account for several rows coming from the same campaign. The calf-versus-shin contrast is reported on its own because it does not depend on which muscle is the reference.

### Slide 19: Backup: significance and relevance of the LLM gain

Backup. The two starred numbers are our own calculation from results/forecast_predictions.csv, not in the report. Without the three campaigns that carry most of the gain, the interval touches zero; say so if asked.

### Slide 20: Backup: ML results and fairness of the comparison

Backup. The honest gap here is the nearest-neighbour control: we cannot yet say whether a simple similarity method would match the LLM. The 271 men-only rows and 100 countermeasure rows are our count on the 346 modelling rows; the report gives the same point on the 425 lower-limb rows before duplicate composites were removed (347 men-only, 126 countermeasure).

### Slide 21: Backup: applicability to Mars mission planning

Backup. The supported planning statements, within 5 to 119 days and for groups: most loss happens in the first weeks, calf muscles need protecting first, and countermeasure groups lose less.
