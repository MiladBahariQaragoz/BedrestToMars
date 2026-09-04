# Search Log

One entry per query actually run. Filled in as the search happens — a query written down
from memory afterwards is not a reproducible search. Query strings go in verbatim,
including the brackets and the typos that were actually executed.

> **Queries recorded 2026-09-04.** The searches were run using the concept-block queries
> written in `PLAN.md` §4, with a date limit of 2013 onwards applied in each interface. Each
> query is reproduced verbatim below so this log stands on its own; if `PLAN.md` §4 is ever
> edited, these copies are the record of what was actually executed.

---

## Q01 — PubMed

- **Database:** PubMed
- **Platform:** pubmed.ncbi.nlm.nih.gov
- **Date run:** 2026-09-04
- **Filters applied:** humans; date limit 2013 onwards
- **Hits:** 1412
- **Export file:** `docs/literature-review/exports/Pubmed.txt` (Send to → File → **Abstract (text)**; the CSV export carries no abstract)
- **Notes:** parsed by `framework/merge_search_exports.py`; all 1412 records recovered, 42 have no abstract in PubMed itself

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

---

## Q02 — Embase

**Not run.** No institutional access. Record it as a gap in the methods section: Embase
indexes conference abstracts that the other databases do not, so its absence is a known
limitation rather than an oversight.

---

## Q03 — Scopus

- **Database:** Scopus
- **Platform:** scopus.com
- **Date run:** 2026-09-04
- **Filters applied:** date limit 2013 onwards; document types as written in the query
- **Hits:** 1757
- **Export file:** `docs/literature-review/exports/Scopus.csv` (Export → CSV with *Abstract & keywords*)
- **Notes:** abstracts present for nearly every record; no EID column in this export, so DOI is the identifier

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

---

## Q04 — Web of Science

- **Database:** Web of Science Core Collection
- **Platform:** webofscience.com
- **Date run:** 2026-09-04
- **Filters applied:** date limit 2013 onwards
- **Hits:** 1876, exported in two files because the export caps at 1000 records
- **Export file:** `docs/literature-review/exports/WebOfScience1.xls`, `WebOfScience2.xls` (Export → Excel → **Full Record**)
- **Notes:** legacy `.xls`, so reading it needs `xlrd`; carries Pubmed Id and UT accession alongside the DOI

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

---

## Q05 — NASA NTRS

- **Database:** NASA Technical Reports Server
- **Platform:** ntrs.nasa.gov
- **Date run:** 2026-09-04
- **Filters applied:** date limit 2013 onwards
- **Hits:** 686
- **Export file:** `docs/literature-review/exports/NASA.csv`
- **Notes:** 68 records are abstract-less by document type (`ABSTRACT`, `PRESENTATION`, `VIDEO`, `POSTER`). Overlaps the other three databases by exactly one record, which is the argument for having run it

```
"bed rest" "muscle volume"
"bed rest" muscle atrophy
"head-down tilt" muscle
"antiorthostatic" muscle
bed rest countermeasure exercise muscle
```

---

## Sanity check: the known-item test

Before any query is frozen, it must return the papers already in the corpus. A miss is a
defect in the query, not in the database.

**This test could not be run as designed**, because every search was limited to 2013 onwards
and eight of the ten known items are older. The two that fall inside the window were checked
against `data/search/screening.csv`:

| Known item | Year | PubMed | Scopus | WoS | NTRS |
|---|---|---|---|---|---|
| Dulac, multimodal exercise in older adults | 2024/25 | ✅ | ✅ | ✅ | — |
| Miokovic, resistive vibration exercise in bed rest | 2014 | ✅ | ✅ | ✅ | — |
| Greenleaf, NASA TM-4580 | 1992 | out of window | out of window | out of window | out of window |
| LeBlanc, 17-week bed rest | 1992 | out of window | out of window | out of window | out of window |
| Alkner & Tesch, 90-day | 2004 | out of window | out of window | out of window | out of window |
| Berg, 5-week | 1991 | out of window | out of window | out of window | out of window |
| Trappe, 60-day women | 2007 | out of window | out of window | out of window | out of window |
| Zange, WBV 14-day | 2008/09 | out of window | out of window | out of window | out of window |
| Belavý, differential atrophy | 2009 | out of window | out of window | out of window | out of window |
| Belavý, MRI volume methods | 2011 | out of window | out of window | out of window | out of window |

Both in-window items were retrieved by all three journal databases, which is real evidence
that the concept blocks work. To close the test properly, re-run one query — PubMed is
free and takes two minutes — with the date limit removed, and check the eight remaining rows.

A technical report like NASA TM-4580 is not expected in PubMed or Scopus at all. That
absence is the argument for running NTRS, and it belongs in the report's methods section.
