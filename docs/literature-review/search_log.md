# Search Log

One entry per query actually run. Filled in as the search happens — a query written down
from memory afterwards is not a reproducible search. Query strings go in verbatim,
including the brackets and the typos that were actually executed.

> **Open action.** The four searches below were run and exported on 2026-09-04, but the
> query strings were not captured. Everything else in these entries was recovered from the
> export files themselves; a query string cannot be. **Paste each one in from the database's
> search history before the end of P1.** All four are still in the account history:
> PubMed → *Advanced* → History; Scopus → *Search history*; Web of Science → *Search History*;
> NTRS → browser history for the search URL.

---

## Q01 — PubMed

- **Database:** PubMed
- **Platform:** pubmed.ncbi.nlm.nih.gov
- **Date run:** 2026-09-04
- **Filters applied:** date limit 2013 onwards (inferred from the export — earliest record is 2013). Others unknown until the query is recovered
- **Hits:** 1412
- **Export file:** `docs/literature-review/exports/Pubmed.txt` (Send to → File → **Abstract (text)**; the CSV export carries no abstract)
- **Notes:** parsed by `framework/merge_search_exports.py`; all 1412 records recovered, 42 have no abstract in PubMed itself

```
(paste the query exactly as run)
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
- **Filters applied:** date limit 2013 onwards (inferred). Document types unknown until the query is recovered
- **Hits:** 1757
- **Export file:** `docs/literature-review/exports/Scopus.csv` (Export → CSV with *Abstract & keywords*)
- **Notes:** abstracts present for nearly every record; no EID column in this export, so DOI is the identifier

```
(paste the query exactly as run)
```

---

## Q04 — Web of Science

- **Database:** Web of Science Core Collection
- **Platform:** webofscience.com
- **Date run:** 2026-09-04
- **Filters applied:** date limit 2013 onwards (inferred)
- **Hits:** 1876, exported in two files because the export caps at 1000 records
- **Export file:** `docs/literature-review/exports/WebOfScience1.xls`, `WebOfScience2.xls` (Export → Excel → **Full Record**)
- **Notes:** legacy `.xls`, so reading it needs `xlrd`; carries Pubmed Id and UT accession alongside the DOI

```
(paste the query exactly as run)
```

---

## Q05 — NASA NTRS

- **Database:** NASA Technical Reports Server
- **Platform:** ntrs.nasa.gov
- **Date run:** 2026-09-04
- **Filters applied:** date limit 2013 onwards (inferred)
- **Hits:** 686
- **Export file:** `docs/literature-review/exports/NASA.csv`
- **Notes:** 68 records are abstract-less by document type (`ABSTRACT`, `PRESENTATION`, `VIDEO`, `POSTER`). Overlaps the other three databases by exactly one record, which is the argument for having run it

```
(paste the query exactly as run)
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
