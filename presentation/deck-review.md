# Deck review, 6 October 2026

Full read of all 19 slides against the no-ai-slop guide (github.com/petergyang/no-ai-slop), plus a check for text load and repetition.

## Changed

| Slide | Before | After | Why |
|---|---|---|---|
| 9–14, 17–19 | "study" / "32 independent studies" for the unit we hold out | "campaign" / "32 independent campaigns" | Slides 6–7 define 52 studies and 36 campaigns. Calling campaigns "studies" in part 2 cycled synonyms and made 32 clash with 52. |
| 9 | "the 346 measurements come from only 32 independent studies, because several papers report the same volunteers" | "the 346 rows used for modelling come from 32 of the 36 campaigns, and rows of one campaign share volunteers" | Links part 2 to the 36 campaigns from slide 6 instead of repeating the cohort-merge point. |
| 11 | Note "campaign means study" | Removed | No longer needed once both halves use "campaign". |
| 4 | "A Mars mission lasts years, not days: …" | "A Mars mission lasts about 2.5 years, with about 6 months of transit each way" | Binary contrast. |
| 12 | "… unlikely to be luck. No other model achieves this." | Last sentence cut | Puffery kicker; the chart already shows it. |
| 14 | "… and this holds under every check." | "… the gain remains when everything identifying a campaign is hidden." | Overclaim: slide 13 lists checks the LLM fails (ranges, earlier scans). |
| 13 | Limitations block, 3 long bullets | Same 3 points, about 30 fewer words | Slide 13 was the densest main slide. |
| 15 (backup) | Search details and 5,731 records | Points to the search backup slide; "One campaign dominates" | Repeated slide 16 and used the old count. |
| 17, 18 (backup) | "finding, not the headline", "The size of the wins matters:", "the obvious next control" | Plain statements | Binary contrast, interpretive metadiscourse, telling the reader what is obvious. |

## Text load (main slides, words on the slide)

| Slide | Words | Verdict |
|---|---|---|
| 1, 2, 5, 6, 8 | 33–95 | Fine; mostly labels on graphics |
| 7 | ~120 | Fine; tables |
| 3 | ~110 in bullets | Heavy for 45 s: 8 bullets. Your wording; could drop to 3 "why" bullets |
| 4 | ~80 in bullets plus graphics | Borderline; three visuals on one slide |
| 9 | ~150 | Heavy, but most words are the input/model/output boxes |
| 11 | ~160 | Heavy by design: the request box is the real example |
| 13 | ~180 after trimming | Still the heaviest; four question blocks plus limitations |
| 14 | ~135 | Borderline for 30 s; conclusions column is two long bullets |

## Repetition

Items 1 to 3 were applied on 6 October after milad's go-ahead.

1. **Calf −16% at day 60** appears on slide 3 (circles) and is the main result of slide 8. Option: keep the circles on slide 3 but drop the number.
2. **Bed rest as the ground analogue** is explained twice: slide 3's right panel title and slide 4's first bullet block. Option: retitle slide 3's panel (e.g. "Unloading shrinks leg muscles").
3. **742 rows, 52 studies, 36 campaigns** are on slide 6 (last two boxes) and in the first three rows of slide 7's table. Option: drop those three rows from slide 7.
4. **Reproducibility** (430 saved answers, 0.17 pp) is on slides 11 and 13 and backup 19. Backup only; fine to leave.
5. Slide 14 repeats the headline numbers of slides 10 and 12. Expected for conclusions.
