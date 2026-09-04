# Extraction Queue

Regenerated 2026-09-04 by `framework/extraction_queue.py`. This is the
resume point: if work stops here, start again at the top of the pending table.

- **25 extracted**, 513 rows in `data/raw/extraction_falk.csv`
- **29 pending** with a full text on disk
- 9 blocked because their numbers exist only in figures
- 1 have no full text on disk
- 10 were excluded at full text and must not be re-read

## How to continue

1. Take the top row of the pending table.
2. Read `data/search/fulltext_digests/<record_id>.md` - it holds the study-level facts,
   the tables that mention a muscle outcome, and every sentence with a muscle term and a
   number. If the numbers are not in there, open the file named in the Source column.
3. Add the study to `framework/extractors/typed_rows.py`, or give it its own parser in
   `framework/extractors/` if it has a large results table.
4. Run the extractor, then `python framework/validate_extraction.py data/raw/extraction_falk.csv`.
5. Run `python framework/extraction_report.py` and `python framework/extraction_queue.py`.
6. Commit. One commit per batch, naming the studies.

If a paper turns out to have no usable numbers, it is a full-text exclusion: add a row to
`screen_decisions_fulltext.csv` with the reason instead of leaving it pending forever.

## Pending

| # | Year | Source | Record | Study |
|---|---|---|---|---|
| 1 | 2021 | pdf | `pubmed_00935` | The effects of exposure to microgravity and reconditioning of the lumbar multi |
| 2 | 2021 | pdf | `scopus_00915` | Dynamics of Body Composition Indices and Biochemical Parameters in Participant |
| 3 | 2021 | pdf | `pubmed_00342` | Do females and males exhibit a similar sarcopenic response as a consequence of |
| 4 | 2020 | pdf | `scopus_00598` | Systemic redox biomarkers suggest non-redox mediated processes in the preventi |
| 5 | 2020 | pdf | `pubmed_00130` | Serum biomarkers that predict lean mass loss over bed rest in older adults: An |
| 6 | 2020 | pdf | `scopus_00594` | Response of thigh muscle cross-sectional area to 21-days of bed rest with exer |
| 7 | 2020 | pdf | `pubmed_00047` | Countering disuse atrophy in older adults with low-volume leucine supplementat |
| 8 | 2019 | pdf | `pubmed_00440` | Improving Dietary Protein Quality Reduces the Negative Effects of Physical Ina |
| 9 | 2019 | pdf | `pubmed_00384` | Dietary feeding pattern does not modulate the loss of muscle mass or the decli |
| 10 | 2018 | pdf | `pubmed_00379` | Loss of maximal explosive power of lower limbs after 2 weeks of disuse and inc |
| 11 | 2018 | pdf | `pubmed_00079` | Efficacy of Testosterone plus NASA Exercise Countermeasures during Head-Down B |
| 12 | 2017 | pdf | `pubmed_00337` | Neuromuscular Electrical Stimulation Combined with Protein Ingestion Preserves |
| 13 | 2017 | pdf | `pubmed_00280` | Anabolic resistance assessed by oral stable isotope ingestion following bed re |
| 14 | 2016 | pdf | `pubmed_00310` | WISE 2005: Aerobic and resistive countermeasures prevent paraspinal muscle dec |
| 15 | 2016 | pdf | `pubmed_00109` | Leucine partially protects muscle mass and function during bed rest in middle- |
| 16 | 2016 | pdf | `pubmed_00250` | Changes in multifidus and abdominal muscle size in response to microgravity: p |
| 17 | 2016 | pdf | `pubmed_00472` | Blood Flow Restricted Exercise Compared to High Load Resistance Exercise Durin |
| 18 | 2015 | pdf | `wos_00614` | WISE 2005: Aerobic and Resistive Exercises Protect Lumbar Paraspinal Lean Musc |
| 19 | 2015 | pdf | `pubmed_00416` | Maximal explosive power of the lower limbs before and after 35 days of bed res |
| 20 | 2015 | pdf | `pubmed_00100` | Bed rest promotes reductions in walking speed, functional parameters, and aero |
| 21 | 2015 | pdf | `pubmed_00386` | Age-related differences in lean mass, protein synthesis and skeletal muscle ma |
| 22 | 2014 | pdf | `pubmed_00095` | WISE-2005: Countermeasures to prevent muscle deconditioning during bed rest in |
| 23 | 2014 | pdf | `pubmed_00369` | The effect of rowing ergometry and resistive exercise on skeletal muscle struc |
| 24 | 2014 | pdf | `pubmed_00240` | Neuromuscular function following muscular unloading and blood flow restricted  |
| 25 | 2014 | pdf | `pubmed_00153` | Muscle atrophy, pain, and damage in bed rest reduced by resistive (vibration)  |
| 26 | 2014 | pdf | `pubmed_00149` | Integrated resistance and aerobic exercise protects fitness during bed rest. |
| 27 | 2013 | pdf | `pubmed_00216` | Short-term bed rest increases TLR4 and IL-6 expression in skeletal muscle of o |
| 28 | 2013 | pdf | `pubmed_00227` | Muscle X-ray attenuation is not decreased during experimental bed rest. |
| 29 | 2013 | pdf | `pubmed_00362` | Effect of β-hydroxy-β-methylbutyrate (HMB) on lean body mass during 10 days of |

## Blocked - values only in figures

These need WebPlotDigitizer or a request to the corresponding author, so they
are not part of the ordinary extraction queue.

| Record | Study |
|---|---|
| `pubmed_00900` | Five days of physical inactivity induced by dry immersion alter skeletal muscle  |
| `pubmed_00243` | Changes in human multifidus muscle size with aging and short-term disuse. |
| `scopus_00063` | Effect of resistive exercise combined with vibration on body composition and ene |
| `pubmed_00360` | A multimodal exercise countermeasure prevents the negative impact of head-down t |
| `pubmed_00249` | Effects of 21 days of bed rest and whey protein supplementation on plantar flexo |
| `scopus_00738` | Disuse-Induced Muscle Loss and Rehabilitation: The National Aeronautics and Spac |
| `scopus_01419` | Hypoxia aggravates inactivity-Related muscle wasting |
| `pubmed_00425` | Treadmill exercise within lower body negative pressure protects leg lean tissue  |
| `scopus_01121` | Replacement of daily load attenuates but does not prevent changes to the musculo |

## Extracted

| Study | Record | Rows |
|---|---|---|
| `mandic2026` | `pubmed_00238` | 15 |
| `lagace2026` | `scopus_00312` | 2 |
| `orlova2026` | `pubmed_00194` | 2 |
| `bocker2026` | `scopus_00324` | 12 |
| `simunic2026` | `pubmed_00389` | 4 |
| `fuchs2025` | `pubmed_00155` | 5 |
| `rogers2025` | `pubmed_00026` | 17 |
| `fuchs2025bfr` | `pubmed_00326` | 2 |
| `smeuninx2025` | `pubmed_00421` | 8 |
| `trappe2024sprint` | `pubmed_00293` | 9 |
| `hansen2024` | `pubmed_00189` | 12 |
| `arbeille2024` | `scopus_00458` | 3 |
| `trappe2023` | `pubmed_00152` | 8 |
| `hajjboutros2023` | `pubmed_00024` | 2 |
| `demartino2022` | `scopus_00516` | 72 |
| `ulls2022` | `pubmed_00662` | 1 |
| `franchi2022` | `pubmed_00880` | 5 |
| `smeuninx2021` | `pubmed_00344` | 16 |
| `demartino2021` | `pubmed_00343` | 6 |
| `tran2021` | `scopus_00673` | 9 |
| `mcdonnell2019` | `pubmed_00348` | 4 |
| `kramer2017` | `pubmed_00352` | 2 |
| `belavy2017` | `scopus_01130` | 288 |
| `pisot2016` | `pubmed_00392` | 2 |
| `mulder2015` | `pubmed_00193` | 6 |

## No full text on disk

| Record | Study |
|---|---|
| `pubmed_00039` | One Week of Bed Rest Leads to Substantial Muscle Atrophy and Induces Whole-Body  |