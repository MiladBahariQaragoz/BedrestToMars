# Screening Decisions

Every source currently in `resources/`, with an include/exclude decision and one line of
reasoning. This closes tasks 0.6 and 0.7 of the kickoff phase.

**Decision categories**

| Category | Meaning |
|---|---|
| `modelling` | Contributes rows to the extraction table and therefore to the models |
| `context` | Cited in the introduction, discussion or limitations; contributes no rows |
| `methods` | Cited for a measurement or analysis method only |
| `excluded` | Not cited |

---

## 1. Decisions

| File | Identification | Decision | Reasoning |
|---|---|---|---|
| `1.pdf` | Greenleaf et al., NASA TM-4580 — leg muscle volume, 30-day 6° HDBR, isotonic/isokinetic training | `modelling` | Muscle volume outcome, defined unloading duration, two exercise arms |
| `6.pdf` | LeBlanc et al. — regional muscle mass after 17 weeks of bed rest | `modelling` | Longest duration in the corpus; anchors the upper end of the duration range |
| `7.pdf` | Alkner & Tesch — knee extensor and plantar flexor size, 90-day bed rest ± resistance exercise | `modelling` | Muscle size outcome with a countermeasure arm |
| `8.pdf` | Berg et al. — hip, thigh and calf muscle atrophy after 5-week bed rest | `modelling` | Muscle-group-resolved outcomes at an intermediate duration |
| `9.pdf` | Trappe et al. — thigh and calf muscle size, 60-day bed rest in women ± exercise/nutrition | `modelling` | The only all-female cohort identified so far; essential for the sex covariate |
| `11 (2).pdf` | Zange et al. — 20 Hz whole-body vibration, 14-day 6° HDT, leg muscle volume | `modelling` | Short duration plus an unusual countermeasure modality (WBV) |
| `12.pdf` | Belavý et al. — differential atrophy of the lower-limb musculature, prolonged bed rest | `modelling` | Muscle-by-muscle resolution; this is the evidence behind the second supporting claim |
| `13.pdf` | Belavý et al. — MRI estimation of individual lower-limb muscle volume change | `modelling` + `methods` | Both an outcome source and the measurement-error reference for MRI volumetry |
| `14.pdf` | Miokovic et al. — heterogeneous atrophy within individual muscles, 60-day bed rest | `modelling` | Within-muscle heterogeneity; also the strongest argument for the `measurement_site` field |
| `15_1.pdf` | **Dulac M, Hajj-Boutros G, et al. (2024).** *A multimodal exercise countermeasure prevents the negative impact of head-down tilt bed rest on muscle volume and mitochondrial health in older adults.* J Physiol 603.13. DOI 10.1113/JP285897 | `modelling` | See section 2 |
| `2.pdf` | Louisy et al. — leg vein filling/emptying and leg volumes, long-term HDBR | `context` | See section 3 |
| `3.pdf` | Belin de Chantemèle et al. — calf venous volume, 90-day bed rest ± countermeasure | `context` | See section 3 |
| `4.pdf` | Bleeker et al. — leg and arm venous properties, 18-day bed rest | `context` | See section 3 |
| `5.pdf` | van Duijnhoven et al. — bed rest and exercise countermeasure on leg venous function | `context` | See section 3 |
| `10.pdf` | Akima et al. — thigh muscle tissue in boys with Duchenne muscular dystrophy | `excluded` | See section 4 |

**Resulting counts:** 10 modelling candidates, 4 context, 1 excluded.

---

## 2. `15_1.pdf` is identified, and it is a core study (task 0.6)

The file is a 24-page scan with no text layer. Rendered and read visually, it is:

> Dulac M, Hajj-Boutros G, Sonjak V, Faust A, Hussain SNA, Chevalier S, Dionne IJ,
> Morais JA, Gouspillou G. *A multimodal exercise countermeasure prevents the negative
> impact of head-down tilt bed rest on muscle volume and mitochondrial health in older
> adults.* The Journal of Physiology 603.13 (2024/2025). DOI 10.1113/JP285897.
> Open access, CC BY-NC.

**Design:** 14 days of 6° head-down tilt bed rest; 23 enrolled, 22 completed;
11 control (5 female, age 58.4 ± 3.9, BMI 24.5 ± 2.4) and 11 exercise (6 female,
age 58.4 ± 3.4, BMI 26.1 ± 1.5). Registered as **NCT04964999**. The countermeasure is
three in-bed sessions per day totalling 60–62 minutes: HIIT, continuous and progressive
aerobic training, and upper- and lower-body resistance training.

**Measurement, in schema terms:** upper quadriceps volume from 3 T MRI of the **right**
thigh (`laterality = right`, not `mean`), from axial slices located at 33% of the distance
between the superior border of the acetabulum and the tibial plateau
(`measurement_site = upper 33% of thigh`). Three occasions: day 1 baseline, day 13 of
HDBR, day 6 of recovery — so this study contributes both `bed_rest` and `recovery` rows.

**Why it matters more than a fifteenth data point:**

- It is the **only cohort of older adults** (55–65) in the corpus. Every other study is
  young, mostly male. It is the single source that lets the analysis say anything at all
  about age, and it is a direct answer to the obvious question about whether astronaut-age
  physiology generalises.
- It is **recent (2024/2025)**, which moves the corpus's upper bound most of the way to
  the "1992–2025" range printed in the abstract.
- It has a **clean two-arm countermeasure design** with a well-documented dose.
- It contributes **recovery-phase rows**, which is why `phase` exists in the schema.

**Two consequences for the work:**

1. **No OCR was needed.** The article is open access, so the publisher's own full text was
   fetched instead of running character recognition over a scan: it is now in
   `resources/15_1_dulac2024_fulltext.xml` (Europe PMC, PMC12306415), searchable and with
   all six tables intact. The scan stays for page references. Downloading the text-layer
   PDF from the publisher is still worth five minutes, but nothing is blocked on it.
   (`resources/` is gitignored, so these are local files, not commits.)
2. **The muscle volume values are in a figure (Fig. 2D), not a table.** The full text
   confirms it — Table 4 is baseline characteristics and every volume result lives in
   Fig. 2. Those rows will be
   `data_source = figure_digitized`, double-extracted per the schema, and worth an email to
   the corresponding author asking for the underlying values — an open-access group with a
   registered trial is likely to answer, and printed values would upgrade the best cohort
   in the corpus from `medium` to `high` confidence.

**Cohort warning.** The same McGill 14-day HDBR campaign appears to have produced several
further papers (motor-unit properties, executive function, insulin resistance and
α-klotho). If any of them enters the corpus during P1, it shares `cohort_id`
`mcgill_hdbr14` — matched on **NCT04964999**, not on the author list.

---

## 3. The four vascular papers: `context`, not `modelling` (task 0.7)

`2.pdf`, `3.pdf`, `4.pdf` and `5.pdf` measure venous compliance, venous filling and total
leg volume by plethysmography and ultrasound. None reports a muscle volume, cross-sectional
area or lean-mass outcome, so none can produce a `pct_change` under the schema. They cannot
be in the modelling set; there is no target variable to extract.

They are kept and cited, for three reasons that each earn a specific place in the output:

1. **They are the evidence for a methodological choice.** Total leg volume falls during bed
   rest partly because of fluid shift, not only because of muscle loss. That is precisely
   why the modelling set is restricted to MRI, CT and DXA muscle-tissue outcomes and
   excludes anthropometric limb volume. Without these papers that restriction looks
   arbitrary; with them it is a defended decision, and a good backup slide for the question
   "why did you throw away all the anthropometry?"
2. **They carry cohort metadata.** `4.pdf` and `5.pdf` come from the Nijmegen group and
   plausibly share participants; `3.pdf` describes a 90-day campaign that may be the same
   programme as `7.pdf`. They are direct evidence for the cohort map in `data/cohorts.csv`,
   which is what makes Leave-One-Cohort-Out honest.
3. **They broaden the deconditioning story by one sentence in the introduction:** unloading
   degrades muscle and vasculature together, and exercise countermeasures act on both.

**Re-screening rule:** if any of the four turns out to report a muscle-tissue outcome
incidentally — a calf muscle CSA in a supplement, for example — it moves to `modelling`,
and the move is recorded here rather than made silently.

---

## 4. The DMD paper: `excluded` (task 0.7)

`10.pdf` (Akima et al.) measures thigh muscle tissue in boys with Duchenne muscular
dystrophy. The atrophy mechanism is dystrophin deficiency, not mechanical unloading; the
population is children; there is no unloading duration to put on the x-axis. Including it
would put a different disease on the same regression line as bed rest, which is the sort of
thing an audience notices.

It is excluded from the corpus and from the reference list. The one case for keeping it is
narrow: if its MRI segmentation protocol is needed as a methods citation, it moves to
`methods` and is cited for that alone. Decide in P1; the default is exclusion.

---

## 5. What this means for the abstract's "15 studies"

The corpus supports **10 modelling candidates**, not 15. The abstract is the contract and
is not edited, so the P1 scientific track has a concrete target: find **five or more
additional bed-rest, HDBR or dry-immersion studies with muscle-morphology outcomes**,
preferably recent campaigns (AGBRESA, dry immersion, recent NASA and ESA 30- and 60-day
studies) so that the date range is honest too.

If the target is not met by the end of P1, the spoken framing is corrected rather than the
number defended: *"fifteen unloading studies were screened, of which N contributed
muscle-morphology outcomes to the modelling set"* is entirely defensible. A printed
abstract that does not match the talk is not.
