# P1 — Literature Search Plan

Branch `feat/literature-review`. Owner: scientific lead. Seven days, Sep 5 – Sep 11.

This is the working document for the search itself. The project plan is [`../../PLAN.md`](../../PLAN.md);
the extraction contract is [`../../data/schema.md`](../../data/schema.md); what is already
in or out of the corpus is [`../screening_decisions.md`](../screening_decisions.md).

---

## 1. What this week has to deliver

| # | Deliverable | Where it lands |
|---|---|---|
| 1 | **Five or more new studies** with lower-limb muscle-morphology outcomes under unloading | `data/search/screening.csv`, decision `include` |
| 2 | Priority on **2013–2023**, the decade the corpus is missing | same |
| 3 | A **search log** reproducible by a stranger: every query verbatim, with date and hit count | `docs/literature-review/search_log.md` |
| 4 | A **cohort map** — which papers share participants, matched on trial registry ID | `data/cohorts.csv` |
| 5 | PRISMA-style counts: identified → deduplicated → screened → full text → included | `docs/literature-review/prisma_counts.md` |

**The corpus today:** ten modelling candidates, four context papers, one exclusion. The
abstract promises fifteen studies. Five new muscle-outcome studies closes that honestly;
anything less means the *spoken* framing changes, not the printed abstract.

**What "new" excludes.** A second paper from a campaign already in the corpus is not a new
study — it is a second report of a cohort we already have. It is still worth including for
extra muscles or timepoints, but it shares a `cohort_id` and it does **not** count towards
the five. See §7.

---

## 2. Eligibility criteria

Decided now, in writing, because a criterion invented halfway through a screen is a
criterion applied inconsistently.

**Include when all of these hold**

| Axis | Requirement |
|---|---|
| Population | Humans, adults (≥18), any sex, healthy or without a disease that itself causes muscle wasting |
| Exposure | A ground-based unloading model with a stated duration: bed rest (horizontal or head-down), dry immersion, unilateral lower limb suspension. Actual spaceflight is eligible but flagged separately |
| Duration | ≥ 5 days of continuous unloading |
| Outcome | At least one **lower-limb muscle-tissue** measure at baseline and at ≥ 1 later timepoint: muscle volume, cross-sectional area, PCSA, thickness, or lean/muscle mass by MRI, CT, DXA, pQCT or ultrasound |
| Reporting | Enough to compute a percent change: either baseline and follow-up values, or a printed percent change, per arm |
| Type | Primary study. Reviews and meta-analyses are mined for references, never extracted |
| Language | English or German. Other languages are recorded, not silently dropped — see below |

**Exclude, with the reason recorded from this fixed list** (these become the PRISMA
exclusion tallies, so use the exact codes):

`not_human` · `not_unloading_model` · `duration_too_short` · `no_muscle_outcome` ·
`upper_limb_only` · `no_baseline_or_followup` · `disease_causes_wasting` ·
`review_or_editorial` · `duplicate_report` · `no_full_text` · `language`

**Two judgement calls, settled in advance.** Total limb volume by anthropometry or
plethysmography is **not** a muscle outcome — fluid shift confounds it, which is exactly
what the four vascular papers in the corpus demonstrate. And a study of cast immobilisation
or step reduction is `not_unloading_model` for this dataset: the mechanical and postural
picture differs from bed rest, and mixing them would put two exposures on one axis.

**Non-English studies.** The Russian and French bed-rest literature is real and old, and
some of it is the only report of a long campaign. Anything promising in another language
gets a row with `language` and a note, so the limitations section can state how much was
left on the table rather than pretending the search was complete.

---

## 3. The concept blocks

Every query below is built from these four blocks. Keeping them separate is what makes a
query portable between databases: only the syntax changes, never the concepts.

### Block A — the unloading model (always required)

Bed rest · bedrest · bed-rest · head-down tilt · head-down bed rest · HDBR · HDT ·
antiorthostatic · anti-orthostatic · hypokinesia · hypodynamia · dry immersion ·
immersion · unilateral lower limb suspension · ULLS · limb suspension ·
simulated microgravity · microgravity analogue/analog · spaceflight analogue/analog ·
ground-based analogue · weightlessness simulation · unloading · disuse · deconditioning ·
immobilisation/immobilization *(broad only — pairs badly with clinical immobilisation)*

Campaign names are keyphrases in their own right, and often the fastest route to a paper
whose title says nothing useful: **AGBRESA** · **WISE-2005** · **Berlin BedRest** ·
**BBR2-2003** · **MEDES** · **:envihab** · **Toulouse bed rest** · **NEK** ·
**Institute of Biomedical Problems** · **artificial gravity bed rest** ·
**60-day bed rest** · **70-day bed rest** · **dry immersion**.

### Block B — the muscle outcome (always required)

muscle atrophy · muscular atrophy · muscle volume · muscle mass · muscle size ·
cross-sectional area · CSA · anatomical cross-sectional area · physiological
cross-sectional area · PCSA · lean mass · lean tissue · muscle thickness ·
muscle wasting · atrophy · deconditioning · sarcopenia *(rarely right, but cheap to add)*

Muscle names pull in the papers whose abstracts never say "atrophy": soleus ·
gastrocnemius · triceps surae · plantar flexor · quadriceps · vastus lateralis ·
knee extensor · hamstring · gluteus · psoas · thigh · calf · lower limb · lower extremity.

### Block C — imaging modality (narrowing only, never in the first pass)

MRI · magnetic resonance · computed tomography · CT · pQCT · DXA · DEXA ·
dual-energy X-ray absorptiometry · ultrasound · ultrasonography

### Block D — countermeasure (never a requirement; used to enrich, and for arm metadata)

exercise · resistance training · resistive exercise · flywheel · reactive jumps ·
whole-body vibration · vibration · aerobic · cycling · lower body negative pressure ·
artificial gravity · centrifugation · nutrition · protein supplementation · countermeasure

**Rule for the first pass in every database: A AND B only.** Adding C or D to the first
search is how systematic reviews lose the papers they most needed. Blocks C and D are for
the narrowing pass when A AND B returns more than roughly 800 records.

---

## 4. The databases, in the order they should be run

Each section gives the syntax quirks that actually change results in that system, a
copy-paste query, and how to export title + abstract. Paste every query into
`search_log.md` **verbatim** as it was run, including the date — a query reconstructed from
memory a fortnight later is not a reproducible search.

### 4.1 PubMed — run first

The cheapest to iterate, and its MeSH indexing does work the other databases cannot.

**Syntax that matters here**

- MeSH terms explode automatically; `[Mesh]` includes narrower terms unless you write `[Mesh:NoExp]`.
- `[tiab]` is title + abstract. It does **not** search keywords — that is `[tw]`, which also reaches MeSH and is noisier.
- Truncation `*` needs at least four characters, and a truncated term is **not** MeSH-mapped and **not** phrase-matched. `"muscle atroph*"` does not behave as a phrase.
- Quoted strings are matched literally. `"bed rest"` and `bedrest` are different terms — both are needed.
- Proximity exists as `"muscle volume"[tiab:~3]`, useful when a phrase is too rigid.

**First-pass query (A AND B, humans)**

```
("Bed Rest"[Mesh] OR "Head-Down Tilt"[Mesh] OR "Weightlessness Simulation"[Mesh]
 OR "Immobilization"[Mesh] OR "bed rest"[tiab] OR bedrest[tiab] OR "bed-rest"[tiab]
 OR "head-down tilt"[tiab] OR "head down tilt"[tiab] OR "head-down bed rest"[tiab]
 OR HDBR[tiab] OR "6 degrees head-down"[tiab] OR antiorthostatic[tiab]
 OR "anti-orthostatic"[tiab] OR hypokinesia[tiab] OR hypodynamia[tiab]
 OR "dry immersion"[tiab] OR "unilateral lower limb suspension"[tiab] OR ULLS[tiab]
 OR "limb suspension"[tiab] OR "simulated microgravity"[tiab]
 OR "microgravity analogue"[tiab] OR "microgravity analog"[tiab]
 OR "spaceflight analogue"[tiab] OR "spaceflight analog"[tiab]
 OR "ground-based analogue"[tiab] OR "mechanical unloading"[tiab]
 OR "muscle unloading"[tiab] OR disuse[tiab])
AND
("Muscular Atrophy"[Mesh] OR "Muscle, Skeletal"[Mesh] OR atroph*[tiab]
 OR "muscle volume"[tiab] OR "muscle mass"[tiab] OR "muscle size"[tiab]
 OR "cross-sectional area"[tiab] OR CSA[tiab] OR PCSA[tiab] OR "lean mass"[tiab]
 OR "lean tissue"[tiab] OR "muscle thickness"[tiab] OR "muscle wasting"[tiab]
 OR deconditioning[tiab] OR soleus[tiab] OR gastrocnemius[tiab]
 OR "triceps surae"[tiab] OR "plantar flexor"[tiab] OR quadriceps[tiab]
 OR "vastus lateralis"[tiab] OR "knee extensor"[tiab])
AND humans[Filter]
```

**Gap-filling variant** — append `AND 2013:2026[dp]`. Run it as a *separate* logged search,
not as a replacement; the counts belong in the PRISMA table separately.

**Campaign variant** — cheap, and finds papers the concept query misses:

```
(AGBRESA[tw] OR "WISE-2005"[tw] OR "Berlin BedRest"[tw] OR "artificial gravity"[tiab]
 OR "dry immersion"[tiab] OR envihab[tw] OR MEDES[tw]) AND humans[Filter]
```

**Export:** Send to → File → format **CSV** (title, authors, journal, year, DOI, PMID) or
**PubMed** format for a full RIS-style record. The CSV export does *not* include abstracts —
for those use the Europe PMC API in §4.6, or Send to → File → **Abstract (text)**.

### 4.2 Embase — the one that finds what PubMed misses

Different indexing (Emtree), and it holds conference abstracts, which is where recent
bed-rest campaigns surface first.

**Syntax that matters here**

- `/exp` explodes an Emtree term, `/de` does not, `/mj` restricts to major focus.
- `:ti,ab,kw` is the field set to use — Embase keywords are worth having, unlike PubMed's.
- Proximity is `NEAR/n` (any order) and `NEXT/n` (in order). There is no `ADJ`.
- Truncation `*` for multiple characters, `?` for exactly one.
- Limits are appended as `AND [humans]/lim AND [english]/lim AND [2013-2026]/py`.
- **De-duplication trick:** `AND [embase]/lim NOT [medline]/lim` returns only the records PubMed will not give you.

**First-pass query**

```
('bed rest'/exp OR 'head down tilt'/exp OR 'weightlessness simulation'/exp
 OR 'immobilization'/exp OR 'bed rest':ti,ab,kw OR bedrest:ti,ab,kw
 OR 'head down tilt':ti,ab,kw OR 'head down bed rest':ti,ab,kw OR hdbr:ti,ab,kw
 OR antiorthostatic:ti,ab,kw OR hypokinesia:ti,ab,kw OR hypodynamia:ti,ab,kw
 OR 'dry immersion':ti,ab,kw OR 'limb suspension':ti,ab,kw OR ulls:ti,ab,kw
 OR 'simulated microgravity':ti,ab,kw OR 'microgravity analog*':ti,ab,kw
 OR 'spaceflight analog*':ti,ab,kw OR 'mechanical unloading':ti,ab,kw
 OR 'muscle unloading':ti,ab,kw OR disuse:ti,ab,kw)
AND
('muscle atrophy'/exp OR 'skeletal muscle mass'/exp OR atroph*:ti,ab,kw
 OR 'muscle volume':ti,ab,kw OR 'muscle mass':ti,ab,kw OR 'muscle size':ti,ab,kw
 OR 'cross sectional area':ti,ab,kw OR csa:ti,ab,kw OR pcsa:ti,ab,kw
 OR 'lean mass':ti,ab,kw OR 'muscle thickness':ti,ab,kw OR 'muscle wasting':ti,ab,kw
 OR deconditioning:ti,ab,kw OR soleus:ti,ab,kw OR gastrocnemius:ti,ab,kw
 OR 'triceps surae':ti,ab,kw OR quadriceps:ti,ab,kw OR 'vastus lateralis':ti,ab,kw
 OR 'knee extensor':ti,ab,kw)
AND [humans]/lim
```

**Export:** Results → Export → **CSV**, choosing the *Full record* or a custom field set that
includes **Abstract**, DOI, PMID and Accession number. Embase's CSV is the single best raw
input for the screening table because it carries abstracts natively.

### 4.3 Scopus — the widest net, and the best citation chasing

**Syntax that matters here**

- `TITLE-ABS-KEY( … )` is the workhorse field. A whole boolean expression goes inside one pair of brackets.
- Proximity is `W/n` (within n words, any order) and `PRE/n` (first term precedes the second by n).
- Truncation `*` (any number of characters) and `?` (exactly one).
- `AND NOT`, never a bare `NOT`.
- Date and type limits are part of the query: `AND PUBYEAR > 2012`, `AND DOCTYPE(ar OR cp OR re)`, `AND LANGUAGE(english OR german)`.

**First-pass query**

```
TITLE-ABS-KEY(
  ("bed rest" OR bedrest OR "head-down tilt" OR "head down bed rest" OR HDBR
   OR antiorthostatic OR hypokinesia OR hypodynamia OR "dry immersion"
   OR "limb suspension" OR ULLS OR "simulated microgravity" OR "microgravity analog*"
   OR "spaceflight analog*" OR "mechanical unloading" OR "muscle unloading" OR disuse)
  AND
  (atroph* OR "muscle volume" OR "muscle mass" OR "muscle size"
   OR "cross-sectional area" OR PCSA OR "lean mass" OR "muscle thickness"
   OR "muscle wasting" OR deconditioning OR soleus OR gastrocnemius
   OR "triceps surae" OR quadriceps OR "vastus lateralis" OR "knee extensor")
)
AND NOT TITLE-ABS-KEY(rodent OR mice OR mouse OR rat OR hindlimb OR "hind limb")
AND DOCTYPE(ar OR cp OR re)
```

The `AND NOT` block matters here more than in PubMed: Scopus has no humans filter, and the
hindlimb-unloading rodent literature is enormous and shares every keyword.

**Export:** Export → **CSV**, and tick **Abstract & keywords** plus **DOI** and **EID** in the
field selector. Scopus exports at most 2000 records per file.

### 4.4 Web of Science Core Collection

**Syntax that matters here**

- `TS=( … )` is topic: title, abstract, author keywords and Keywords Plus.
- Proximity is `NEAR/n`; `SAME` restricts to the same sentence in some indexes.
- Wildcards: `*` any number, `?` exactly one, `$` zero or one — `$` is how you catch British and American spellings in one term, e.g. `analog$ue`.
- WoS lemmatises by default, so `atrophy` already reaches `atrophied`. Truncate anyway; it costs nothing.
- Year limit as a separate clause: `AND PY=(2013-2026)`.

**First-pass query**

```
TS=(("bed rest" OR bedrest OR "head-down tilt" OR "head down bed rest" OR HDBR
     OR antiorthostatic OR hypokinesia OR hypodynamia OR "dry immersion"
     OR "limb suspension" OR ULLS OR "simulated microgravity"
     OR "microgravity analog*" OR "spaceflight analog*" OR "mechanical unloading"
     OR "muscle unloading" OR disuse)
    AND
    (atroph* OR "muscle volume" OR "muscle mass" OR "muscle size"
     OR "cross-sectional area" OR PCSA OR "lean mass" OR "muscle thickness"
     OR "muscle wasting" OR deconditioning OR soleus OR gastrocnemius
     OR "triceps surae" OR quadriceps OR "vastus lateralis" OR "knee extensor"))
NOT TS=(rat OR rats OR mice OR mouse OR rodent OR hindlimb OR "hind limb")
```

**Export:** Export → **Excel** or **Tab delimited**, record content **Full Record**, which
includes the abstract. 1000 records per export.

### 4.5 Cochrane CENTRAL

Small yield expected, but it indexes trial registrations and conference abstracts that the
others miss, and bed-rest countermeasure studies are frequently registered trials.

Use the **Search Manager**, one concept per numbered line, then combine:

```
#1  MeSH descriptor: [Bed Rest] explode all trees
#2  MeSH descriptor: [Head-Down Tilt] explode all trees
#3  ("bed rest" OR bedrest OR "head down tilt" OR HDBR OR "dry immersion"
     OR "limb suspension" OR "simulated microgravity" OR antiorthostatic):ti,ab,kw
#4  #1 OR #2 OR #3
#5  MeSH descriptor: [Muscular Atrophy] explode all trees
#6  (atroph* OR "muscle volume" OR "muscle mass" OR "cross-sectional area"
     OR "lean mass" OR "muscle thickness" OR deconditioning):ti,ab,kw
#7  #5 OR #6
#8  #4 AND #7
```

**Export:** Select all → Export → **CSV**, with abstracts included.

### 4.6 Europe PMC — the one that searches full text, and the one with a usable API

Two things no other database here gives. First, it searches **inside the full text**, so it
finds studies whose muscle volume is a secondary outcome never mentioned in the abstract —
exactly the kind of paper this corpus is short of. Second, its API returns title and
abstract as structured data, so the screening table can be built without hand-copying.

**Syntax that matters here**

- Field prefixes: `TITLE:`, `ABSTRACT:`, `AUTH:`, `JOURNAL:`, and the full-text fields `METHODS:` and `RESULTS:`.
- Booleans must be uppercase. Wildcard `*` works; phrases go in double quotes.
- `SRC:MED` restricts to MEDLINE-indexed records; leave it off to keep preprints and agency reports.
- Date filter: `FIRST_PDATE:[2013-01-01 TO 2026-12-31]`. If a range errors out in the UI, use the date facet instead and log that you did.

**Full-text query — the one that earns its place**

```
(ABSTRACT:"bed rest" OR TITLE:"bed rest" OR ABSTRACT:"head-down tilt"
 OR ABSTRACT:"dry immersion" OR ABSTRACT:HDBR OR ABSTRACT:"limb suspension"
 OR ABSTRACT:"simulated microgravity")
AND
(METHODS:"muscle volume" OR METHODS:"cross-sectional area" OR RESULTS:"muscle volume"
 OR ABSTRACT:atroph* OR ABSTRACT:"muscle volume" OR ABSTRACT:"lean mass")
AND FIRST_PDATE:[2013-01-01 TO 2026-12-31]
```

**Export, straight to a screening table.** The REST API returns title and abstract in one
call — `resultType=core`, up to 1000 records per page:

```bash
curl -s -G "https://www.ebi.ac.uk/europepmc/webservices/rest/search" \
  --data-urlencode 'query=(ABSTRACT:"bed rest" OR ABSTRACT:"head-down tilt" OR ABSTRACT:"dry immersion") AND (ABSTRACT:atroph* OR ABSTRACT:"muscle volume" OR ABSTRACT:"lean mass")' \
  --data-urlencode 'resultType=core' \
  --data-urlencode 'pageSize=1000' \
  --data-urlencode 'format=json' \
  -o data/search/raw_exports/europepmc_$(date +%F).json
```

Page beyond the first 1000 with `cursorMark=*`, then feed each response's `nextCursorMark`
back in. The same endpoint is how `resources/15_1_dulac2024_fulltext.xml` was retrieved.

### 4.7 NASA NTRS — grey literature, and where a third of this field lives

`https://ntrs.nasa.gov`. NASA technical memoranda are primary sources for the older
campaigns and are indexed nowhere else — `1.pdf` in the corpus is NASA TM-4580. Expect the
search to be blunt: quoted phrases work, boolean support is limited, and there is no
truncation or proximity worth relying on. Run several short queries rather than one long one.

```
"bed rest" "muscle volume"
"bed rest" muscle atrophy
"head-down tilt" muscle
"antiorthostatic" muscle
bed rest countermeasure exercise muscle
```

Then filter by document type (Technical Report, Conference Paper) in the sidebar. The API
mirrors the UI: `https://ntrs.nasa.gov/api/citations/search?q=%22bed+rest%22+muscle`.

Two neighbours worth thirty minutes each, for campaign metadata rather than papers:
**NASA Task Book** (`taskbook.nasaprs.com`) for funded bed-rest projects and their outputs,
and the **Life Sciences Data Archive** (`lsda.jsc.nasa.gov`) for campaign documentation.

### 4.8 Trial registries — this is how the cohort map gets built

Registry IDs are the only reliable way to tell that two papers report the same participants,
which is what Leave-One-Cohort-Out depends on. Search these for campaigns, not for papers.

- **ClinicalTrials.gov** — `https://clinicaltrials.gov/search?term=bed%20rest%20muscle`, or the API: `https://clinicaltrials.gov/api/v2/studies?query.cond=Bed+Rest&query.term=muscle&pageSize=100`
- **DRKS** (German register) — where DLR campaigns including AGBRESA are registered
- **ISRCTN** and the **WHO ICTRP** portal for anything European that appears in neither

For every campaign found, record the registry ID, the site, the duration and the arms, then
put it in `data/cohorts.csv`. When a paper is later screened in, match it to a campaign by
**registry ID first**, and only by author group and dates when no ID exists.

### 4.9 Google Scholar — verification only

Not a primary source: no reproducible query syntax, no stable result counts, no usable
export. It is good for exactly two jobs, and both belong at the end of the week.

- **Forward citation chasing:** open "Cited by" on each of the ten corpus papers, and on Belavý 2009, Miokovic 2012 and Dulac 2024 in particular. Recent bed-rest work almost always cites the Berlin group.
- **Finding the one paper you know exists but cannot name.** Use quoted phrases, `intitle:`, and `AROUND(3)` for proximity. Queries are capped at roughly 256 characters.

### 4.10 Citation chasing and hand-searching

Two hours here beats another database.

- **Backward:** the reference lists of the ten corpus papers, plus two or three recent reviews of bed-rest countermeasures and disuse atrophy.
- **Forward:** Scopus and Web of Science "cited by" on the same ten.
- **Hand-search** the tables of contents of the journals this literature concentrates in: *Journal of Applied Physiology*, *European Journal of Applied Physiology*, *The Journal of Physiology*, *Frontiers in Physiology*, *npj Microgravity*, *Acta Astronautica*, *Medicine & Science in Sports & Exercise*, *Experimental Physiology*.
- **Chase the campaign, not the paper.** Once a campaign is identified — AGBRESA, a MEDES dry-immersion study, a recent :envihab bed rest — search the campaign name directly. Campaigns publish in clusters, and a cluster is where the muscle-outcome paper hides.

---

## 5. The search log

`docs/literature-review/search_log.md`, one row per query run. Filled in as you go, never
reconstructed afterwards.

| Field | Example |
|---|---|
| `query_id` | `Q03` |
| `database` | Embase |
| `platform` | embase.com, institutional access |
| `date_run` | 2026-09-06 |
| `query` | the complete string, verbatim, in a fenced code block |
| `filters` | humans, no date limit |
| `hits` | 412 |
| `export_file` | `data/search/raw_exports/embase_2026-09-06.csv` |
| `notes` | ran the `[embase]/lim NOT [medline]/lim` variant as Q04 |

`query_id` is the join key: every row in the screening table records which query found it.

---

## 6. Raw exports and the screening table

**Raw exports live in `docs/literature-review/exports/`**, committed unmodified, exactly as
the database produced them. They are the evidence that the counts are real. (The first batch
arrived there rather than in `data/search/raw_exports/`; the folder that has the files is the
folder that wins, and the merge script reads from it.)

**Everything is then merged into one file: `data/search/screening.csv`**, with these columns:

| Column | Notes |
|---|---|
| `record_id` | `<db>_<n>`, stable, assigned at merge |
| `query_id` | Which search found it; a record found by three queries keeps all three, semicolon-separated |
| `database` | pubmed, embase, scopus, wos, central, europepmc, ntrs, citation_chase, handsearch |
| `retrieved_date` | ISO date |
| `title`, `abstract` | The two fields the screen actually runs on |
| `authors`, `journal`, `year` | For the reference list |
| `doi`, `pmid`, `other_id` | Identifiers, lower-cased and stripped of any URL prefix |
| `url` | Direct link, for the full-text step |
| `dedup_key` | DOI if present, else PMID, else a normalised `firstauthor_year_first5titlewords` |
| `screen_ta` | Title/abstract screen: `include`, `exclude`, `maybe` |
| `screen_ft` | Full-text screen: `include`, `exclude`, blank if not reached |
| `exclusion_reason` | One code from the fixed list in §2. Required whenever a screen says `exclude` |
| `campaign_guess`, `registry_id` | Filled the moment either is visible; this is what feeds `data/cohorts.csv` |
| `screener`, `screen_date`, `notes` | Provenance |

**Deduplication, in this order:** exact DOI → PMID → normalised title plus year. Two records
one year apart with the same title are usually an epub-ahead-of-print and its issue version:
keep the issue version, and record the other in `notes`. Never delete a duplicate row —
mark it, so the PRISMA "duplicates removed" count is a fact rather than an estimate.

**When the exports exist, the merge is a script, not an afternoon of copying.** Write it
into `framework/merge_search_exports.py`, one reader per database format, so re-running a
search in October costs minutes.

**Screening rule that saves the week:** at title/abstract, `maybe` is cheap and `exclude` is
expensive. Anything where the abstract does not clearly rule out a lower-limb muscle outcome
goes to `maybe` and gets a full-text look. The corpus is small enough that a generous screen
costs an hour and a strict one costs a study.

---

## 7. Feeding the cohort map

This is the part that is easy to leave until it is too late, and it is what the
methodological slide is built on.

For every record that reaches full text, fill `registry_id` and `campaign_guess` before
extraction begins, then reconcile them into `data/cohorts.csv`. Rules:

- **A campaign, not a paper, is a cohort.** Two papers reporting the same bed-rest campaign share one `cohort_id`, whatever their author lists say.
- **Match on registry ID first.** The McGill campaign behind Dulac 2024 (NCT04964999) has produced several further papers on motor units, cognition and insulin resistance; nothing in their titles says they share participants.
- **Suspect a shared cohort whenever** the site, the duration, the year and the sample size all line up. Then go looking for the registration or the campaign name in the methods.
- **When it cannot be resolved, merge rather than split.** Treating two papers as one cohort costs a little statistical power. Treating one cohort as two leaks participants across validation folds and makes every reported number optimistic.

Any new study also needs its `cohort_id` recorded in `data/cohorts.csv` before its rows are
extracted — the schema validator rejects rows whose cohort it has never seen.

---

## 8. The week, day by day

| Day | Date | Work |
|---|---|---|
| 1 | Sep 5 | Pilot PubMed and Embase. Check that all ten known corpus papers are actually returned — a query that misses Belavý or Trappe is broken, and finding that out now costs an hour instead of a week. Refine, then freeze the queries |
| 2 | Sep 6 | Run PubMed, Embase, Scopus, Web of Science. Export everything. Log every query |
| 3 | Sep 7 | Run CENTRAL, Europe PMC full-text, NTRS, the registries. Merge and deduplicate. PRISMA count of what came in |
| 4 | Sep 8 | Title/abstract screen, first pass. **Mid-week call with the AI track** — this is the only thing preventing the two parallel tracks from diverging |
| 5 | Sep 9 | Finish the title/abstract screen. Pull full texts for everything that survived |
| 6 | Sep 10 | Full-text screen. Start extraction into `data/raw/extraction_partner.csv` against `data/schema.md`. Run the validator before committing |
| 7 | Sep 11 | Cohort map into `data/cohorts.csv`. PRISMA counts finalised. Merge `feat/literature-review` into `main` |

**A working definition of done for the week:** a stranger could re-run the search from
`search_log.md` and land within a handful of records of the same set; every included study
has a `cohort_id`; and the answer to "how many studies are in the modelling set, and why?"
is the same sentence from both people.

---

## 9. What is decided, and what is not

Decided and not to be relitigated mid-week: the eligibility criteria in §2, the fixed
exclusion codes, the schema in `data/schema.md`, and the rule that anthropometric limb
volume is not a muscle outcome.

Genuinely open, and to be settled with evidence rather than preference: whether spaceflight
studies enter the modelling set or stay as external validation, and whether dry immersion
belongs on the same duration axis as bed rest or needs its own `design` term in the model.
Both are P2 questions. Collect the studies either way; do not let the modelling question
narrow the search.

---

## 10. Run log — 4 September 2026

Four databases were searched and exported. **5731 records in, 3590 unique after
deduplication.** Full counts in [`../../data/search/merge_report.md`](../../data/search/merge_report.md).

| Database | Export file | Format | Records |
|---|---|---|---|
| PubMed | `exports/Pubmed.txt` | plain-text "Abstract (text)" | 1412 |
| Scopus | `exports/Scopus.csv` | CSV with abstracts | 1757 |
| Web of Science | `exports/WebOfScience1.xls`, `WebOfScience2.xls` | legacy BIFF `.xls`, 1000-record cap per file | 1876 |
| NASA NTRS | `exports/NASA.csv` | CSV, JSON inside three of its columns | 686 |

Merged by [`../../framework/merge_search_exports.py`](../../framework/merge_search_exports.py)
into `data/search/screening.csv` (3590 unique rows, ready to screen) and
`data/search/all_records.csv` (all 5731, duplicates marked with `duplicate_of` rather than
deleted). Re-running the script is idempotent: `python framework/merge_search_exports.py`.

### The PubMed problem, and how it was solved

PubMed's CSV export contains no abstract, so the export is the plain-text *Abstract (text)*
format — 3.8 MB of wrapped, human-readable records. It is parsed record by record. Three
things in that format bite, and all three were found by checking the output rather than by
trusting the parser:

1. **A wrapped citation line looks exactly like a record header.** `... Epub 2019 Sep \n24.`
   starts a line with a number and a dot, so a naive split cuts a record in half and shifts
   every field of the next one by a paragraph. The split now requires a blank line before
   the header, and any fragment that does not open with something citation-shaped is glued
   back onto the record before it.
2. **A record can open with a status banner** — `593. RETRACTED ARTICLE` — before its
   citation. Those banners are now kept as a screening flag in `notes`. One retracted
   article is flagged in this batch.
3. **Some journal titles contain a year.** `J Appl Physiol (1985)` and
   `Spine (Phila Pa 1976)` made 91 records look like they were published in 1985 or 1976.
   Parenthesised years are stripped before the publication year is read.

After the fixes: all 1412 PubMed records parsed, none missing a title, year or author list,
42 with no abstract because PubMed holds none.

### What the merged table looks like

- **313 of 3590 records have no abstract** (mostly NASA presentations and conference items). They are screened on title alone, and the ones that survive go to full text.
- **46 records carry a trial registry ID** in the abstract, extracted automatically into `registry_id`. That column is the seed of the cohort map.
- **Overlap is smaller than expected:** 732 records were found by all three of PubMed, Scopus and Web of Science; 386 by Scopus and WoS; and NASA NTRS overlaps the others by exactly one record. Each database earned its place, and NTRS is very nearly disjoint from the rest.

### The finding that matters most: every search was date-limited to 2013+

Every one of the four exports starts at 2013. Nothing older is in any of them. That is a
property of how the searches were run, not of the literature — and it is **the right half of
the problem to have solved**, because 2013–2023 is exactly the decade the existing corpus is
missing (`../screening_decisions.md` §5). The pre-2013 classics are already in `resources/`.

Two consequences, both of which have to be handled rather than remembered:

1. **The known-item test in `search_log.md` cannot be run as written**, since eight of its ten items are pre-2013. Of the two that can be checked, **Dulac 2024 was retrieved by PubMed, Scopus and Web of Science** — the queries do find the right kind of paper. Verify the remaining items by re-running one query without the date limit, or accept the limit and say so.
2. **The report's methods section must state the date limit explicitly**, and the limitations section must say that pre-2013 coverage comes from a convenience corpus rather than a systematic search. That sentence costs nothing to write now and is very expensive to be caught without.

### Title/abstract screening, same day

Screened in two stages, because 3590 records is too many to read and far too few to trust a
classifier with.

**Stage 1 — deterministic triage** (`framework/triage_screening.py`). The §2 criteria as
explicit rules. It only ever rules records *out*, and only on high-confidence signals; a
machine can tell that a paper is about mice, a machine cannot tell that a paper belongs in
the dataset. Every auto-exclusion records the phrase that triggered it, so a rule that turns
out to be too aggressive can be found by filtering one column.

| Bucket | Records | What it means |
|---|---|---|
| `priority` | 183 | Core unloading model, muscle outcome, lower-limb term — read first |
| `maybe` | 979 | Survived the exclusions, missing one signal |
| `campaign_lead` | 481 | A real unloading campaign reporting gait, motor units or cardiovascular outcomes. No rows, but each one names a campaign for `data/cohorts.csv` |
| `auto_exclude` | 1947 | Ruled out by rule |

Two rule defects were found by checking the output rather than trusting it: artificial-gravity
studies were not recognised as unloading at all (AGBRESA and its relatives name the centrifuge,
not the bed), and 473 records with a genuine bed-rest exposure were being discarded for lacking
a muscle outcome, which is what created the `campaign_lead` bucket.

**Stage 2 — access and data enrichment** (`framework/enrich_access.py`). For every survivor,
Europe PMC and OpenAlex were asked whether the full text is open and whether it is
machine-readable. This is the difference between a paper that can be mined as XML with its
tables intact and one that has to be read by hand — the same route that produced the Dulac
full text in P0. Of the 183 priority records, 102 have full text in Europe PMC.

**Stage 3 — read by hand.** All 183 priority records and the top 49 of the `maybe` bucket
were read as title plus abstract and decided one at a time. The decisions live in
`screen_decisions_priority.csv` and `screen_decisions_maybe_top.csv` — small enough to argue
with in a diff, and separate from the screening table, which is regenerated by the merge
script and would overwrite them.

| Outcome | Records |
|---|---|
| **Included at title/abstract** | **74** — of which 39 have machine-readable full text and 58 are open access |
| Excluded at title/abstract | 2493, each with one of the fixed codes |
| Still to screen | 1023 |

The included list is [`included_studies.md`](included_studies.md), ordered by how cheap each
paper is to extract. Full counts are in
[`../../data/search/screening_report.md`](../../data/search/screening_report.md) and
[`prisma_counts.md`](prisma_counts.md).

**What the 74 look like.** The corpus problem from `../screening_decisions.md` §5 is solved
several times over: the target was five new studies and there are 74 candidates before full
text, spread evenly across 2013–2026, including the 60-day artificial-gravity campaigns, the
WISE-2005 paraspinal papers, three papers from the McGill 14-day cohort, a study reporting
MRI volumes of 17 individual lower-limb muscles in women, and one that measures the same
atrophy by DXA, CT *and* MRI in the same participants — which is the sensitivity analysis for
the `modality` feature, handed over ready-made.

**What is not done.** 1023 records remain unscreened: the rest of the `maybe` bucket, plus 80
priority records that cannot be decided without a full text. They are not excluded, and must
never be reported as excluded. Two things would close them out: reading the remaining
`maybe` records at title level, which is a few hours, and pulling full texts for the 80.

### Full texts, same day

**68 of the 74 included studies are on disk** in `resources/fulltext/` (gitignored; they live
in the shared Drive folder). 30 arrived as Europe PMC XML carrying 157 tables between them,
which is the cheap extraction path; 38 are PDFs downloaded by hand from the list the fetch
script produced.

Filing the manual downloads is automated too
([`../../framework/ingest_downloads.py`](../../framework/ingest_downloads.py)): publisher
filenames are meaningless, so each PDF is identified by the DOI printed inside it, and only
by a fuzzy title match when there is no DOI. Anything below the match threshold is reported
rather than guessed - attaching one paper's numbers to another paper's row is the single
worst error available here. Of 39 downloads, 37 matched on DOI automatically; the two that
did not were a conference-abstract page whose first page belongs to a neighbouring abstract,
and a supplement file, both placed by hand.

Six studies are still missing and are listed with save-as filenames in
[`fulltext_todo.md`](fulltext_todo.md). Two of them are conference abstracts that may never
exist as a full paper - if so, they are `no_full_text` exclusions, not gaps.

### Extraction, first batches

**426 rows from 11 studies across 9 cohorts and 39 muscles**, all passing the schema
validator. Regenerated summary: [`../../data/raw/extraction_report.md`](../../data/raw/extraction_report.md).

Two ways of getting numbers out, chosen per paper:

- **A parser per paper** where the results are a large table — `belavy2017_ltbr.py` (24
  muscles x 2 arms x 6 timepoints = 288 rows) and `demartino2022_agbresa_spine.py` (4
  lumbopelvic muscles x up to 5 disc levels x 2 arms x 2 timepoints = 72 rows). Typed by
  hand these would be two days of work and a dozen silent transcription errors; parsed, the
  mistakes are systematic and therefore findable.
- **`typed_rows.py`** for papers whose numbers live in prose or a small table, one block per
  study with the table or page it came from.

Both write into `data/raw/extraction_falk.csv` and both are idempotent: re-running replaces
that study's rows, so a correction is an edit and a re-run rather than a hunt through the CSV.

**What the data already shows.** Ranking mean percent change across unloading rows puts
soleus (-20.3%), medial gastrocnemius (-18.3%) and peroneals (-17.3%) at the top and
multifidus (-6.3%) at the bottom. That is the talk's second claim appearing in our own
numbers rather than being quoted from someone else's paper.

**Four schema corrections, each forced by a real paper rather than by taste:**

| Change | The paper that forced it |
|---|---|
| `outcome_type` and `modality` joined the primary key | Fuchs 2025 measures the same thighs by DXA, CT and MRI on the same day and gets three different answers |
| `measurement_site` joined the key too | Smeuninx measures quadriceps CSA at 20, 40, 60 and 80% of thigh length; the 20% site shows no loss while the 60% site does |
| Age may be a mean **or** a range | Smeuninx reports "10 healthy older men aged 65-80" and never prints a mean; inventing a midpoint would be imputation |
| Percent change printed by a paper is kept, flagged, not corrected | It is the mean of individual changes, which is not the change of the means - they differ by 2.5 percentage points in Tran's gluteus medius |

**Cohorts proven, not guessed.** Three cases where two papers turned out to be one cohort:
Belavy 2017 and Alkner & Tesch are both the MEDES Toulouse LTBR campaign; Smeuninx 2021 and
2025 share registry NCT04422665; De Martino 2022 is the same 24 AGBRESA participants as
Tran 2021, regrouped for the reconditioning phase. Each is recorded in `data/cohorts.csv`
with the evidence.

**Two studies fell at full text**, both for the same reason and both consistent with the
rule set in P0: their only muscle outcomes were whole-body lean mass and limb circumference.
Anthropometry is not a muscle measurement, and the second of them derives "volume" from
circumference squared, which is a calculation rather than an observation.

**Extraction run, 4 September: 27 studies extracted, 537 rows, 20 cohorts.** The queue is
now empty of papers that can be extracted from their text; what remains is 36 studies whose
muscle numbers exist only inside figures, plus one with no full text.

That ratio is the finding of the run. Roughly half of this literature does not print its
muscle outcomes as numbers at all - the values live in a bar chart, and the text says
"decreased significantly" beside a figure reference. Every one of the 36 is recorded in
`screen_decisions_fulltext.csv` with what was found and what is missing, so none of them is
a mystery to whoever picks them up.

Three routes out, and they are a decision for the team rather than for a script:

1. **Digitise the figures.** WebPlotDigitizer on a bar chart with visible error bars is
   about ten minutes per paper, and the schema already carries `data_source =
   figure_digitized` plus a `digitizer_tool` field for exactly this. Thirty-six papers is
   roughly a day and a half of work, and it would roughly double the dataset.
2. **Write to the authors.** Slower, better data, and for the open-access groups with
   registered trials the odds are decent. Worth doing for the handful that matter most -
   Dulac, the WISE-2005 pair, the 89-day Rittweger paper.
3. **Stop here and say so.** 537 rows from 27 studies and 20 cohorts is already a real
   dataset, and the limitation is honest: "we extracted every study that published its
   numbers as numbers".

A dozen of the 36 are near-misses rather than figure-only: the value is printed but the PDF
text extraction mangled it, or the percentage is there and the group size is not. Those are
minutes each with the paper open.

### The partial table

**29 rows from 12 of the 36 parked studies** were recovered anyway, into
[`../../data/raw/extraction_partial.csv`](../../data/raw/extraction_partial.csv).

Most papers that hide their results in figures still print one headline number, usually in
the abstract: "calf muscle CSA decreased 26.6%", "total lumbar paraspinal CSA decreased
10.9% in controls against 4.3% in exercisers". A percent change with a known duration,
exposure and muscle is a usable row even when the group size or the baseline value is
missing - and for the longest campaigns those headline numbers are the largest effects in
the whole dataset.

**They live in a separate file on purpose.** Every row carries `partial_record` in `qc_flag`
plus a note naming exactly what is absent - `group_size_not_in_abstract`,
`no_dispersion_in_abstract`, `sign_inferred_from_wording`, `female_arm_only`. The main table
stays the one where every row has a full record behind it. Merging the two is a modelling
decision for P2, not a default, and the flags make the sensitivity analysis trivial: fit
with and without the partial rows and report both.

What the partial table adds:

- **Rittweger 2013** — calf muscle CSA down **26.6%** after 89 days, the largest single loss anywhere in the dataset, and it belongs to the MEDES LTBR cohort we already hold.
- **PlanHab** — the hypoxia arms, at 10 and 21 days, showing bed rest under hypoxia costs more muscle than bed rest alone (−9.9% against −8.0% at ten days; −9.7% against −6.9% at twenty-one).
- **WISE-2005 paraspinal muscles**, twice - the full paper and its conference abstract disagree slightly (10.9% against 12%), which is recorded rather than smoothed over.
- **Two more spaceflight studies**, including the multifidus falling from 9.86 to 6.99 cm² at L5.
- **Krainski and Cook**, giving quadriceps and plantar flexor losses for both a bed rest and a suspension model with countermeasure arms.

**Twenty-four studies remain genuinely unreadable without digitising their figures.** Every
one was checked twice - once against its abstract, once against its full text for a
flattened results table - and neither yielded a number. That is the floor of what text
mining can do here.

**Still to extract by hand: 24 studies, all figure-only.** The queue is ordered
in `included_studies.md`; the table-rich ones go fastest.

### Outstanding — one thing only, and it needs the person who ran the searches

**The four query strings are not recorded.** `search_log.md` has the slots; the queries have
to be pasted in verbatim, with the filters that were applied. Without them the search is not
reproducible and the PRISMA diagram cannot be defended. Everything else in this section was
recovered from the exports themselves; a query string cannot be.
