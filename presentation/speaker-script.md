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

Each row in our data is one measurement. It tells us how much one muscle shrank, on average, in one group of volunteers, on one day of bed rest. For every row, the models get five facts: the day of the scan, which muscle it is, whether the group did exercise or not, how the muscle was scanned, and whether it is one muscle or several together. The models must predict how many percent the muscle shrank compared with before bed rest.

We have 346 rows, but they come from only 32 separate studies, which we call campaigns. Rows from the same campaign come from the same people, so they are not truly separate. If a model trains on some rows of a campaign and is tested on others, it can cheat. So we hide one whole campaign, train on the other 31, and predict the hidden one. We repeat this 32 times, once for every campaign. The code checks that no campaign is ever on both sides.

We score each model by its average error in percentage points. Each campaign counts the same. As the simplest reference, we use a duration curve: it only knows how many days the bed rest lasted.

### Slide 10: LLM-based probabilistic classifier: input and output (Milad)

About a minute and a half.

The normal models only see numbers in a table. For the LLM, we wrote each measurement out in words. We used a special kind of LLM. It does not chat or write text. It gets a description and a fixed list of answers, and it gives back a probability for each answer.

On the left is a real request. It describes the volunteers, the bed-rest study, the muscle, how it was scanned, and the day. It also includes the duration curve and the most similar rows from the other 31 campaigns. Then it asks: in which of these 19 ranges will the change fall?

On the right is the answer: a probability for each range. We never ask the model for a number. We turn the probabilities into one number by taking a weighted average of the middle of each range. Here that gives −6.6 percent. The real value was −9.4 percent. This example has a typical error for this model.

The request never includes any data from the hidden campaign, and never the name of a paper, author or campaign. The code checks this for every request. We saved all 430 answers, so anyone can check our results without running the model again.

### Slide 11: Model comparison on held-out campaigns (Milad)

About a minute and a half.

We tested four standard machine learning models: ridge regression, random forest, support vector regression and gradient boosting. We also tested TabPFN, a network that was trained in advance on many small tables.

The left chart shows the error on the hidden campaigns. Lower is better. The simple duration curve is off by 3.16 percentage points. The best machine learning model, the random forest, is off by 3.18. So none of them beats the simple curve. The right chart shows R², which is how much of the differences between rows a model explains. Here the machine learning models do better, because they learn that some muscles shrink more than others. But most of the error comes from differences between whole campaigns, such as the scanner, the people or the study design. None of our inputs captures that. We had decided in advance to report this result either way.

The LLM is at the top. Its error is 2.71 percentage points, the lowest of all, and it also explains the most, with an R² of 0.43. When we compare it with the curve on exactly the same rows, the error drops from 3.13 to 2.71. That is 0.42 points better. The 95 percent confidence interval goes from 0.13 to 0.73. Even the low end is above zero, so the improvement is real. The LLM beats the curve in 20 of the 32 campaigns. No other model has a clear improvement like this.

If asked about the target: we had set a goal of 15 percent improvement in advance. The error improved by 13.3 percent and the probability score by 17.7 percent.

### Slide 12: Robustness and validity checks of the LLM prediction (Milad)

About a minute and a quarter.

We wrote down every check and its pass rule before running it. First, does the model just remember the studies? It may have read these papers during training. When we remove every detail that could identify a campaign, the LLM is still clearly better, by 0.30 points. We also asked it to pick the campaign name from a list. It was right 19 percent of the time, while random guessing gives 8 percent.

If asked about recognition: of the three campaigns behind most of the improvement, it recognised only one.

Second, does it really use the data from the other campaigns? When we mix up those values, it becomes 1.25 points worse than the curve. With no data at all, the error jumps to 5.85. So the improvement comes from reading that data.

Third, does the format matter? Changing the order of the rows or moving the ranges changes the error by only 1 to 3 percent. Fourth, is it stable? Sending the same 20 requests again changes the predictions by 0.17 points on average, smaller than the 0.42 improvement.

There are three limits. We added the LLM after we had seen the machine learning results. Its 80 percent ranges contain the real value only 62 percent of the time, so it is too confident and we only use its single number. And when we give it earlier scans from the same campaign, it ignores them.

### Slide 13: Conclusions, limitations and further work (Milad)

About forty-five seconds.

To sum up: with only 32 campaigns, standard machine learning models do not beat a simple curve that only knows the number of days. The LLM classifier, which reads the description of each campaign and the data of the others, lowers the error from 3.13 to 2.71 percentage points.

The main limits: we have only 32 campaigns, mostly young men, and no bed-rest data after day 119. Every row is a group average. So we predict how much a group loses on average, not the risk for one astronaut.

Next steps. First, find out how strongly each muscle reacts, and use that with normal muscle sizes to estimate the total loss in the legs. Second, use data from individual people over time, and link muscle loss to strength and function. Third, test everything on new campaigns and on real spaceflight data before building any personal risk tool.

If asked about the first step: the dataset has 30 group time points where three or more muscles were measured together, across 14 campaigns.

### Slide 14: Thank you for listening (Milad)

Closing.

Thank you for listening. We are happy to answer your questions.

Backup slides: 15 and 16 on the data and the search, 17 and 18 on part 1, 19 to 21 on part 2.

---

## Backup slides (only if asked)

### Slide 15: Backup: dataset coverage and limitations

If asked about extra checks: three planned checks have not been run yet. These are the composite-first analysis, the analysis without the MEDES campaign, and the analysis with MRI only. Only the weighting check has been run, and it changed the results very little.

### Slide 16: Backup: literature search sources and query

All four search strings are in the appendix of the report and in docs/literature-review/search_log.md. PubMed uses the same two blocks, with MeSH terms and a filter for human studies. Scopus and Web of Science remove animal studies in the search itself.

The main weakness is that we only searched papers from 2013 onwards. Only two of ten known modelling papers fall in that period, and we did not test the search without this limit. We could not search Embase because we had no access. Embase includes conference abstracts that the other databases miss.

### Slide 17: Backup: dataset expansion and composition

Part 1 (Niloufar).

We set the rules for which studies to include, in Table 2 of the report, before we started screening. Version 1.0 of the dataset was frozen on 14 September and version 1.1 on 19 September. All results use version 1.1.

We use the saturating curve unless another shape fits better by at least 4 AIC points.

The spaceflight rows are still in the dataset, marked as spaceflight. They were measured after landing, so the filter for measurements during unloading leaves them out.

Weighting rows by their uncertainty would need the spread of each change, and most papers do not report it. When we compared both ways of weighting, the effect of duration changed by less than 1 percentage point.

### Slide 18: Backup: certainty of the muscle-group curves

Part 1 (Niloufar).

The dots at day 60 on slide 8 are the estimates for each muscle group, with the ranges shown here. All lines use the same curve shape, scaled to these dots. So they show the shape we assume, not a separate fit for each muscle.

The ranges are 95 percent intervals that take into account that several rows come from the same campaign. We show the calf versus shin comparison on its own because it does not depend on which muscle we use as the reference.

### Slide 19: Backup: significance and relevance of the LLM gain

The two numbers with an asterisk are our own calculation from results/forecast_predictions.csv. They are not in the report.

If we remove the three campaigns that give most of the improvement, the interval touches zero. Say this openly if asked.

### Slide 20: Backup: ML results and fairness of the comparison

The open question is the nearest-neighbour test. We do not yet know whether a simple method that just picks similar rows would do as well as the LLM.

The 271 men-only rows and 100 countermeasure rows are counted on the 346 modelling rows. The report makes the same point with the 425 leg rows before duplicates were removed: 347 men-only and 126 countermeasure rows.

### Slide 21: Backup: applicability to Mars mission planning

Within 5 to 119 days, and for groups, the data support three points for mission planning. Most of the loss happens in the first weeks. The calf muscles need protection first. Groups with a countermeasure, such as exercise, lose less muscle.
