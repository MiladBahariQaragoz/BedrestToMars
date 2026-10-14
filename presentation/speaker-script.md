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

Each row in the dataset is one measurement: the mean change of one muscle, in one group of volunteers, on one day of bed rest. The inputs are the day of the scan, the muscle group, whether the group received a countermeasure, the imaging method, and whether the value refers to one muscle or several combined. The output is the percentage change in muscle size from baseline.

The 346 modelling rows come from 32 independent campaigns. Rows from the same campaign share volunteers, so they are not independent. We therefore used leave-one-campaign-out validation. We trained on 31 campaigns, predicted the held-out campaign, and repeated this 32 times. The code verifies that no campaign appears in both the training and the test set.

The metric is the mean absolute error in percentage points, with each campaign weighted equally. The reference is a duration curve that uses only the number of days.

### Slide 10: LLM-based probabilistic classifier: input and output (Milad)

About a minute and a half.

The standard models receive coded columns. For the LLM, we described each measurement in text and passed it to an LLM-based probabilistic classifier. This model does not generate text. It receives a description and a fixed list of options and returns a probability for each option.

The left panel shows an actual request. It contains the participants, the protocol, the muscle, the imaging method and the target day. It also contains the duration curve fitted on the other 31 campaigns and the most similar rows from those campaigns. The model is asked in which of 19 ranges the change will fall.

The right panel shows the returned probabilities. We do not ask the model for a number. The prediction is the probability-weighted mean of the range midpoints, here −6.6 percent. The measured value was −9.4 percent. The error of this example equals the median error of the model.

The request never contains data from the held-out campaign or any paper, author or campaign name. This is checked automatically for every request. All 430 responses are stored, so every result can be reproduced without querying the model again.

### Slide 11: Model comparison on held-out campaigns (Milad)

About a minute and a half.

We compared four standard models, ridge regression, random forest, support vector regression and gradient boosting, each tuned within the training folds. We also tested TabPFN, a network pretrained for small tabular data.

The left figure shows the error on the held-out campaigns. The duration curve has an error of 3.16 percentage points. The best machine learning model, the random forest, has 3.18. No machine learning model has a lower error than the curve. The right figure shows that these models explain two to three times more variance, because they learn the differences between muscles. Most of the remaining error is a shift that affects a whole campaign, for example through the scanner, the volunteers or the protocol. None of our inputs describes this shift. We had committed in advance to report this result regardless of the outcome.

The LLM has an error of 2.71 percentage points and the highest R², 0.43. In a paired comparison on the same rows, the error decreases from 3.13 to 2.71, a reduction of 0.42 percentage points. The 95 percent confidence interval is 0.13 to 0.73, so it excludes zero. The LLM is closer than the curve in 20 of 32 campaigns. No other model has an improvement with a confidence interval that excludes zero.

If asked about the target: we had set a 15 percent improvement in advance. The error improved by 13.3 percent and the probabilistic score by 17.7 percent.

### Slide 12: Robustness and validity checks of the LLM prediction (Milad)

About a minute and a quarter.

Each check and its pass criterion were defined and committed to the repository before the check was run.

First, recognition. The model may have seen the published studies during training. With all identifying details removed, the improvement is 0.30 percentage points, and the confidence interval still excludes zero. When asked to select the campaign name from a list, the model was correct in 19 percent of cases, against 8 percent by chance.

If asked about recognition: of the three campaigns that contribute most of the improvement, the model identified only one.

Second, use of the reference data. When the values of the other campaigns are shuffled, the model is 1.25 percentage points worse than the curve. Without reference data, the error rises to 5.85. The improvement therefore depends on these data.

Third, presentation. Changing the row order or shifting the range boundaries changes the error by 1 to 3 percent. Fourth, reproducibility. Repeating 20 requests changes the predictions by 0.17 percentage points on average, less than the 0.42 improvement.

There are three limitations. The model was added after the machine learning results were known. Its 80 percent ranges contain the measured value in only 62 percent of cases, so we report only point predictions. It also ignores a campaign's own earlier measurements.

### Slide 13: Conclusions, limitations and further work (Milad)

About forty-five seconds.

With 32 independent campaigns, standard machine learning models and TabPFN do not outperform a curve based on duration alone. The LLM-based classifier uses the description of each campaign and the data of the other campaigns, and it reduces the error from 3.13 to 2.71 percentage points.

The main limitations are the small number of campaigns, mostly with young men, and the lack of bed-rest data beyond day 119. Each row is a group mean. The model therefore predicts the average loss of a group, not the risk of an individual astronaut.

Further work has three steps. First, we will estimate the relative susceptibility of each muscle and combine it with baseline volumes to estimate the total volume loss of the lower limb. Second, we will use individual participant data over time and relate muscle loss to strength and function. Third, we will validate the model on independent campaigns and spaceflight data before developing an individual risk assessment.

If asked about the first step: the dataset contains 30 group time points with three or more muscles measured together, across 14 campaigns.

### Slide 14: Thank you for listening (Milad)

Closing.

Thank you for your attention. We are happy to take your questions.

Backup slides: 15 and 16 on the data and the search, 17 and 18 on part 1, 19 to 21 on part 2.

---

## Backup slides (only if asked)

### Slide 15: Backup: dataset coverage and limitations

If asked about sensitivity analyses: three planned analyses have not been run yet. These are the composite-first analysis, the analysis without the MEDES campaign, and the MRI-only analysis. Only the weighting check has been run, and it changed the results little.

### Slide 16: Backup: literature search sources and query

All four search strings are in the appendix of the report and in docs/literature-review/search_log.md. PubMed uses the same two blocks with MeSH terms and a humans filter. Scopus and Web of Science exclude animal studies in the query.

The main weakness is the limit to publications from 2013 onwards. Only two of ten known modelling papers fall inside this window, and the search without the limit was not tested. Embase was not searched because we had no access. It indexes conference abstracts that the other databases miss.

### Slide 17: Backup: dataset expansion and composition

Part 1 (Niloufar).

The eligibility criteria in Table 2 of the report were defined before screening. Dataset version 1.0 was frozen on 14 September and version 1.1 on 19 September. All results use version 1.1.

The saturating curve is used unless another form is better by at least 4 AIC points.

The spaceflight rows remain in the dataset and are flagged. They were measured after landing, so the filter for measurements during unloading removes them.

Inverse-variance weighting would need the variance of the change, which most papers do not report. Comparing both weightings changed the duration effect by less than 1 percentage point.

### Slide 18: Backup: certainty of the muscle-group curves

Part 1 (Niloufar).

The dots at day 60 on slide 8 are the meta-regression estimates for each muscle group, with the intervals shown here. The lines use one shared time course scaled to these values. They show the assumed shape, not a separate fit for each muscle.

The intervals are 95 percent cluster-robust intervals, which account for several rows coming from the same campaign. The calf versus shin contrast is reported separately because it does not depend on the choice of reference muscle.

### Slide 19: Backup: significance and relevance of the LLM gain

The two numbers marked with an asterisk are our own calculation from results/forecast_predictions.csv. They are not in the report.

Without the three campaigns that contribute most of the improvement, the confidence interval includes zero. State this directly if asked.

### Slide 20: Backup: ML results and fairness of the comparison

The open point is the nearest-neighbour control. We cannot yet say whether a simple similarity method would perform as well as the LLM.

The counts of 271 men-only rows and 100 countermeasure rows refer to the 346 modelling rows. The report gives the same point for the 425 lower-limb rows before duplicate composites were removed: 347 men-only and 126 countermeasure rows.

### Slide 21: Backup: applicability to Mars mission planning

Within 5 to 119 days and at group level, the data support three statements for mission planning. Most of the loss occurs in the first weeks. The calf muscles need protection first. Groups with a countermeasure lose less muscle.
