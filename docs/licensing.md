# What may be published, and what may not

Reviewed 2026-09-19 against the tree at `feat/nasa-integration`. The question this answers:
if this repository is made public — or the dataset is released as open access alongside the
talk — which of the files in it carry a right to be redistributed, and which do not.

**This is an engineering review of provenance and stated terms, not legal advice.** Where a
file's terms are unknown it is written down as unknown rather than assumed to be permissive.

**The short version.** The dataset and the code are the artefacts intended for release and
they are clean. Two things block a public release as it stands:

1. `data/search/fulltext_digests/` holds **68 files of text copied verbatim out of
   published papers**, and at least 30 of them come from papers that grant no reuse right.
2. The repository has **no `LICENSE` file**, so nothing in it is open source yet, whatever
   the README says about sharing.

Neither is hard to fix, and neither touches the dataset.

---

## 1. The dataset is the safe artefact

`data/dataset_v1.1.csv`, the four tables in `data/raw/`, `data/cohorts.csv`,
`data/muscle_map.csv`, `data/measurement_site_map.csv` and `data/schema.md` can be released.

Every row is a measured value plus the bibliographic coordinates needed to trace it — a DOI,
a file name, a page and table number. Extracting the numeric results of a study and
redistributing them as a structured dataset is what every systematic review and meta-analysis
does, and it is the basis on which this project was planned (`PLAN.md` §10, `README.md`
decisions log). Facts are not the part of a paper that copyright protects; the prose, the
figures and the typesetting are.

Two things were checked rather than assumed:

- **No verbatim prose rides along in the data.** Of the 752 rows across the four extraction
  tables, none has a `notes` field containing quoted text; the long notes are the extractors'
  own descriptions of what the paper did. `page_ref` carries a location, not a quotation.
- **No figure images were committed.** The 19 figure-derived rows were read off charts
  rendered into `resources/figures/`, which is gitignored along with the rest of `resources/`.
  Only the numbers read off them are in the repository.

One caveat worth recording rather than discovering later: in the EU a *sui generis* database
right can protect a substantial extraction from someone else's database even where the
individual facts are free. A journal's results table is not normally the kind of database that
right was written for, and this dataset is assembled from many sources rather than lifted from
one, but if the dataset is ever published with a formal licence the question belongs in front
of whoever signs it off.

## 2. What cannot be published as it stands — the full-text digests

`data/search/fulltext_digests/` holds 68 committed Markdown files, one per screened paper,
written by `framework/scan_fulltexts.py`. Each one reproduces, **verbatim**, the full text of
every table in the paper that mentions a muscle outcome, plus every sentence carrying a muscle
term and a number. That is copied expression, not extracted fact, and it is exactly the part
of a paper that is protected.

The papers behind them, by open-access status as recorded during screening:

| `oa_status` | Digests | What the status means for redistribution |
|---|---|---|
| `closed` | 13 | Paywalled. No reuse right of any kind. |
| `bronze` | 8 | Free to read on the publisher's site, **no licence attached**. Reading is permitted; redistribution is not granted. |
| `green` | 9 | An author manuscript in a repository. The deposit licence varies by publisher and is usually not a reuse licence. |
| `hybrid` | 7 | Open access in a subscription journal, normally CC BY or CC BY-NC — needs checking per paper. |
| `epmc_open` | 30 | In the Europe PMC open subset. Most are CC BY, CC BY-NC or CC BY-NC-ND. |
| `gold` | 1 | Fully open-access journal, normally CC BY. |

**At least 30 digests — the closed, bronze and green ones — carry no redistribution right on
their face.** For the remaining 38 the licence is probably permissive but is *not recorded
anywhere in this repository*: the screening table stores `is_oa`, `oa_status` and `oa_url`,
and never stores the licence itself. A CC BY-NC-ND paper in particular allows redistribution
of the article but not of derivative works, and a digest that reorganises its tables is
arguably one.

The full per-digest list is in the appendix at the end of this document.

**This does not affect the dataset.** The digests were a working aid for reading papers
quickly; nothing downstream depends on them, because the numbers they helped find are in the
extraction tables with their own provenance.

## 3. The NASA archive

`data/nasa/` holds 470 committed files, 2.7 MB, downloaded from the NASA Life Sciences Portal
by `framework/fetch_nasa_nlsp.py`.

**The copyright position is good.** NASA states that NASA content "generally are not subject
to copyright in the United States" and asks to be acknowledged as the source. Works of the US
federal government are not copyrightable under 17 U.S.C. §105.

**Two things are nonetheless unresolved, and both are worth a decision rather than an
assumption:**

- **NASA's own catalogue entry for NLSP records "License not specified".** That is the absence
  of a stated grant rather than a grant. It is the normal state of US federal open data and is
  very unlikely to be a problem, but the basis on which the files are redistributed here
  should be written down, because right now nothing in the repository states it.
- **These are individual-participant human-subject records.** Across the folder, 449 files
  carry a `SUBJECT` identifier, 318 carry `SEX`, 317 `ETHNICITY`, 242 `WEIGHT` and `HEIGHT`,
  60 `AGE`, 387 an exact `SCAN_DATE`, and 126 a scanner `PATIENT_KEY`. NASA published them
  openly, so the de-identification judgement is NASA's and has already been made. Re-hosting
  470 files of it in a public repository is a second, separate decision — and the archive's
  own stated remit is protecting participants' privacy and implementing their consent
  decisions.

There is a middle option that keeps the science reproducible without re-hosting anything: the
fetcher and `data/nasa/MANIFEST.json` are committed, and the manifest records every file's
UUID and SHA-256, so anyone can reproduce the download and verify they got the same bytes.
The five rows the dataset actually uses are in `data/raw/extraction_nasa.csv` either way.

**Attribution is currently missing.** NASA asks to be credited; `data/nasa/CARD.md` names the
archive and the experiment UUID, which is most of the way there, but nothing in the repository
states the acknowledgement in the form NASA asks for.

## 4. What was already kept out, and why it was right

These decisions predate this review and hold up. They are listed so nobody reopens them.

| Excluded | Mechanism | Why |
|---|---|---|
| `resources/` — the source PDFs | `.gitignore` | Copyrighted publisher material. The reference list and the extraction table carry the information that matters |
| `resources/figures/` — rendered figure pages | `.gitignore` | Images of published figures; the values read off them are in the dataset instead |
| `docs/literature-review/exports/`, `data/search/all_records.csv`, `data/search/screening.csv` | `.gitignore` | Scopus and Web of Science licence terms restrict redistributing exported records. The merge script and the derived counts are committed, so the tables rebuild from anyone's own exports |
| `*.xlsx` working spreadsheets | `.gitignore` | Superseded by the frozen CSV |
| `docs/recieved from coauthor/` | `.gitignore` | Correspondence and QC workbooks; the findings are in `data/reconciliation_log.md` |

Two committed files were checked against the same standard and are clean:

- `docs/literature-review/screen_decisions_*.csv` carry only a record id, a decision, a reason
  and a note — no titles and no abstracts, so none of the licensed export text travels with them.
- `data/search/fulltext_scan.csv` carries titles, DOIs and **counts** of what the scan found.
  Titles and DOIs are bibliographic metadata, which is how every reference list works.

## 5. The repository has no licence

There is no `LICENSE` file. In the absence of one, default copyright applies and a reader has
no right to use, modify or redistribute anything here — including the code and the dataset
that were always meant to be shareable. A public repository without a licence is readable, not
open source.

This is the one item on this page that blocks the stated goal by itself, and it is a file.

## 6. Decisions needed

| # | Decision | Owner | Recommendation |
|---|---|---|---|
| L1 | Add a `LICENSE` file | Both leads | Two licences, because the repository holds two kinds of thing: code under a permissive software licence (MIT or Apache-2.0), dataset and documentation under CC BY 4.0. State which covers which in `README.md` |
| L2 | What happens to `data/search/fulltext_digests/` before the repository goes public | Both leads | Stop tracking them and add the folder to `.gitignore`. They are a reading aid, nothing depends on them, and 30 of the 68 have no reuse right. Keeping only the OA ones means checking 38 licences by hand for a file nobody reads twice |
| L3 | Whether removing them from the working tree is enough | Qaragoz | It is not, if the history is published: the files stay in every earlier commit. Either accept that, or rewrite the history before the repository is made public — which is cheap now and expensive after anyone clones it |
| L4 | Whether `data/nasa/` is re-hosted or fetched | Both leads | Either is defensible. If it stays, record the basis (US government work, not subject to copyright) and add NASA's acknowledgement. If it goes, the fetcher and the manifest already make it reproducible |
| L5 | The NASA acknowledgement text | Qaragoz | Add to `README.md` and the dataset card: data courtesy of the NASA Life Sciences Data Archive / NASA Life Sciences Portal, naming experiment `4469ebdc-0a65-55e8-bbff-3cf6b044c4c6` and the principal investigators on its experiment page |
| L6 | Whether the released dataset needs the EU database-right question answered | Both leads | Only if it is published under a formal licence with an institution's name on it. Worth one email to whoever does research data management |

None of these blocks the talk. L1 and L2 block making the repository public, and L5 is owed to
NASA either way.

## Appendix — the 68 digests by open-access status

Recorded from `data/search/screening.csv` at the time of the search. `oa_status` is what the
OA lookup reported; it is **not** the article's licence, which this project never stored.

| oa_status | record | author | year | doi | title |
|---|---|---|---|---|---|
| closed | `pubmed_00095` |  | 2014 | 10.1152/japplphysiol.00590.2013 | WISE-2005: Countermeasures to prevent muscle deconditioning during bed |
| closed | `pubmed_00149` |  | 2014 | 10.1249/mss.0b013e3182a62f85 | Integrated resistance and aerobic exercise protects fitness during bed |
| closed | `pubmed_00194` |  | 2026 | 10.1113/jp290722 | Different effects of 3-week disuse on phenotype and gene expression in |
| closed | `pubmed_00227` |  | 2013 | 10.1002/mus.23644 | Muscle X-ray attenuation is not decreased during experimental bed rest |
| closed | `pubmed_00240` |  | 2014 | 10.1007/s00421-014-2864-3 | Neuromuscular function following muscular unloading and blood flow res |
| closed | `pubmed_00250` |  | 2016 | 10.1007/s00586-015-4311-5 | Changes in multifidus and abdominal muscle size in response to microgr |
| closed | `pubmed_00348` |  | 2019 | 10.1113/ep087482 | The LunHab project: Muscle and bone alterations in male participants f |
| closed | `pubmed_00362` |  | 2013 | 10.1016/j.clnu.2013.02.011 | Effect of β-hydroxy-β-methylbutyrate (HMB) on lean body mass during 10 |
| closed | `pubmed_00369` |  | 2014 | 10.1152/japplphysiol.00803.2013 | The effect of rowing ergometry and resistive exercise on skeletal musc |
| closed | `pubmed_00472` |  | 2016 | 10.3357/amhp.4566.2016 | Blood Flow Restricted Exercise Compared to High Load Resistance Exerci |
| closed | `scopus_00598` |  | 2020 | 10.1016/j.actaastro.2019.12.002 | Systemic redox biomarkers suggest non-redox mediated processes in the  |
| closed | `scopus_00915` |  | 2021 | 10.1134/s0362119721030178 | Dynamics of Body Composition Indices and Biochemical Parameters in Par |
| closed | `wos_00614` |  | 2015 | 10.1249/01.mss.0000478309.26945.3d | WISE 2005: Aerobic and Resistive Exercises Protect Lumbar Paraspinal L |
| bronze | `pubmed_00109` |  | 2016 | 10.3945/ajcn.115.112359 | Leucine partially protects muscle mass and function during bed rest in |
| bronze | `pubmed_00280` |  | 2017 | 10.1016/j.clnu.2016.09.019 | Anabolic resistance assessed by oral stable isotope ingestion followin |
| bronze | `pubmed_00310` |  | 2016 | 10.1152/japplphysiol.00532.2015 | WISE 2005: Aerobic and resistive countermeasures prevent paraspinal mu |
| bronze | `pubmed_00342` |  | 2021 | 10.1113/ep087834 | Do females and males exhibit a similar sarcopenic response as a conseq |
| bronze | `pubmed_00379` |  | 2018 | 10.1113/jp274772 | Loss of maximal explosive power of lower limbs after 2 weeks of disuse |
| bronze | `pubmed_00392` |  | 2016 | 10.1152/japplphysiol.00858.2015 | Greater loss in muscle mass and function but smaller metabolic alterat |
| bronze | `pubmed_00440` |  | 2019 | 10.1093/gerona/glz003 | Improving Dietary Protein Quality Reduces the Negative Effects of Phys |
| bronze | `pubmed_00935` |  | 2021 | 10.1016/j.spinee.2020.09.006 | The effects of exposure to microgravity and reconditioning of the lumb |
| green | `pubmed_00047` |  | 2020 | 10.1152/japplphysiol.00847.2019 | Countering disuse atrophy in older adults with low-volume leucine supp |
| green | `pubmed_00100` |  | 2015 | 10.1093/gerona/glu123 | Bed rest promotes reductions in walking speed, functional parameters,  |
| green | `pubmed_00152` |  | 2023 | 10.1152/japplphysiol.00412.2023 | Microgravity-induced skeletal muscle atrophy in women and men: implica |
| green | `pubmed_00153` |  | 2014 | 10.1249/mss.0000000000000279 | Muscle atrophy, pain, and damage in bed rest reduced by resistive (vib |
| green | `pubmed_00216` |  | 2013 | 10.1152/ajpregu.00072.2013 | Short-term bed rest increases TLR4 and IL-6 expression in skeletal mus |
| green | `pubmed_00337` |  | 2017 | 10.1089/rej.2017.1942 | Neuromuscular Electrical Stimulation Combined with Protein Ingestion P |
| green | `pubmed_00384` |  | 2019 | 10.1152/ajpendo.00378.2018 | Dietary feeding pattern does not modulate the loss of muscle mass or t |
| green | `pubmed_00386` |  | 2015 | 10.1113/jp270699 | Age-related differences in lean mass, protein synthesis and skeletal m |
| green | `pubmed_00416` |  | 2015 | 10.1007/s00421-014-3024-5 | Maximal explosive power of the lower limbs before and after 35 days of |
| hybrid | `pubmed_00026` |  | 2025 | 10.1152/japplphysiol.00483.2025 | Muscle-specific atrophy of the lower limb musculature in response to s |
| hybrid | `pubmed_00130` |  | 2020 | 10.1016/j.cca.2020.06.003 | Serum biomarkers that predict lean mass loss over bed rest in older ad |
| hybrid | `pubmed_00343` |  | 2021 | 10.1152/japplphysiol.00990.2020 | Lumbar muscle atrophy and increased relative intramuscular lipid conce |
| hybrid | `pubmed_00880` |  | 2022 | 10.1249/mss.0000000000002922 | Early Changes of Hamstrings Morphology and Contractile Properties duri |
| hybrid | `pubmed_00900` |  | 2026 | 10.1152/japplphysiol.00481.2025 | Five days of physical inactivity induced by dry immersion alter skelet |
| hybrid | `scopus_00063` |  | 2025 | 10.1016/j.actaastro.2025.03.029 | Effect of resistive exercise combined with vibration on body compositi |
| hybrid | `scopus_00594` |  | 2020 | 10.1002/tsm2.122 | Response of thigh muscle cross-sectional area to 21-days of bed rest w |
| epmc_open | `pubmed_00024` |  | 2023 | 10.1159/000534063 | Impact of 14 Days of Bed Rest in Older Adults and an Exercise Counterm |
| epmc_open | `pubmed_00155` |  | 2025 | 10.1002/ejsc.12299 | Quantifying Leg Muscle Disuse Atrophy During Bed Rest Using DXA, CT, a |
| epmc_open | `pubmed_00189` |  | 2024 | 10.14814/phy2.16166 | Five days of bed rest in young and old adults: Retainment of skeletal  |
| epmc_open | `pubmed_00193` |  | 2015 | 10.1007/s00421-014-3045-0 | Musculoskeletal effects of 5 days of bed rest with and without locomot |
| epmc_open | `pubmed_00238` |  | 2026 | 10.1113/ep093145 | Limited musculoskeletal benefits of artificial gravity combined with c |
| epmc_open | `pubmed_00249` |  | 2020 | 10.1007/s00421-020-04333-5 | Effects of 21 days of bed rest and whey protein supplementation on pla |
| epmc_open | `pubmed_00268` |  | 2023 | 10.1002/jcsm.13146 | Plasma proteome profiling of healthy subjects undergoing bed rest reve |
| epmc_open | `pubmed_00326` |  | 2025 | 10.1113/jp286065 | Daily blood flow restriction does not preserve muscle mass and strengt |
| epmc_open | `pubmed_00344` |  | 2021 | 10.1002/jcsm.12661 | The effect of short-term exercise prehabilitation on skeletal muscle p |
| epmc_open | `pubmed_00352` |  | 2017 | 10.1038/s41598-017-13659-8 | How to prevent the detrimental effects of two months of bed-rest on mu |
| epmc_open | `pubmed_00360` |  | 2025 | 10.1113/jp285897 | A multimodal exercise countermeasure prevents the negative impact of h |
| epmc_open | `pubmed_00389` |  | 2026 | 10.1249/mss.0000000000003986 | Alterations in Muscle Contractile Properties, Structure, and Function  |
| epmc_open | `pubmed_00421` |  | 2025 | 10.1113/jp285130 | A single bout of prior resistance exercise attenuates muscle atrophy a |
| epmc_open | `pubmed_00425` |  | 2016 | 10.14814/phy2.12892 | Treadmill exercise within lower body negative pressure protects leg le |
| epmc_open | `pubmed_00662` |  | 2022 | 10.1113/jp283381 | Effects of short-term unloading and active recovery on human motor uni |
| epmc_open | `pubmed_00866` |  | 2024 | 10.1002/jcsm.13431 | Bed-rest and exercise remobilization: Concurrent adaptations in muscle |
| epmc_open | `scopus_00312` |  | 2026 | 10.1113/ep093524 | Impact of 14 days of head-down bed rest and an exercise countermeasure |
| epmc_open | `scopus_00324` |  | 2026 | 10.1038/s41526-026-00611-2 | Comparison of musculoskeletal responses and its variability after long |
| epmc_open | `scopus_00351` |  | 2026 | 10.1113/ep093398 | Exercise during 14 days of head down tilt bedrest attenuates motor uni |
| epmc_open | `scopus_00458` |  | 2024 | 10.3389/fphys.2024.1482860 | Exercise combined with artificial gravity and exercise only countermea |
| epmc_open | `scopus_00516` |  | 2022 | 10.3389/fphys.2022.862793 | The Effects of Reconditioning Exercises Following Prolonged Bed Rest o |
| epmc_open | `scopus_00673` |  | 2021 | 10.3389/fphys.2021.745811 | Gluteal Muscle Atrophy and Increased Intramuscular Lipid Concentration |
| epmc_open | `scopus_00694` |  | 2022 | 10.3389/fphys.2021.743876 | Between-Subject and Within-Subject Variaton of Muscle Atrophy and Bone |
| epmc_open | `scopus_00738` |  | 2020 | 10.1097/cce.0000000000000269 | Disuse-Induced Muscle Loss and Rehabilitation: The National Aeronautic |
| epmc_open | `scopus_00787` |  | 2022 | 10.3389/fphys.2022.902983 | Running vs. resistance exercise to counteract deconditioning induced b |
| epmc_open | `scopus_00954` |  | 2022 | 10.3389/fnut.2022.976818 | Early lean mass sparing effect of high-protein diet with excess leucin |
| epmc_open | `scopus_00973` |  | 2020 | 10.3389/fphys.2020.573581 | Fetuin-A as a Potential Biomarker of Metabolic Variability Following 6 |
| epmc_open | `scopus_01121` |  | 2016 | 10.1016/j.bonr.2016.10.001 | Replacement of daily load attenuates but does not prevent changes to t |
| epmc_open | `scopus_01130` |  | 2017 | 10.1136/bmjsem-2016-000196 | High-intensity flywheel exercise and recovery of atrophy after 90 days |
| epmc_open | `scopus_01419` |  | 2018 | 10.3389/fphys.2018.00494 | Hypoxia aggravates inactivity-Related muscle wasting |
| gold | `pubmed_00243` |  | 2026 | 10.1016/j.exger.2026.113090 | Changes in human multifidus muscle size with aging and short-term disu |
