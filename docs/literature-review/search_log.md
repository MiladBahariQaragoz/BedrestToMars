# Search Log

One entry per query actually run. Filled in as the search happens — a query written down
from memory afterwards is not a reproducible search. Query strings go in verbatim,
including the brackets and the typos that were actually executed.

The template for the first entry is below. Copy it for each query.

---

## Q01 — PubMed, first pass

- **Database:** PubMed
- **Platform:** pubmed.ncbi.nlm.nih.gov, no institutional login required
- **Date run:**
- **Filters applied:** humans
- **Hits:**
- **Export file:** `data/search/raw_exports/pubmed_YYYY-MM-DD.csv`
- **Notes:** sanity check — did the query return Belavy, Miokovic, Trappe, Alkner and Dulac?

```
(paste the query exactly as run)
```

---

## Q02 — ...

---

## Sanity check: the known-item test

Before any query is frozen, it must return the papers already in the corpus. Record which
of them each database query actually found; a miss is a defect in the query, not in the
database.

| Known item | PubMed | Embase | Scopus | WoS |
|---|---|---|---|---|
| Greenleaf, NASA TM-4580 | | | | |
| LeBlanc, 17-week bed rest | | | | |
| Alkner & Tesch, 90-day | | | | |
| Berg, 5-week | | | | |
| Trappe, 60-day women | | | | |
| Zange, WBV 14-day | | | | |
| Belavy, differential atrophy | | | | |
| Belavy, MRI volume methods | | | | |
| Miokovic, heterogeneous atrophy | | | | |
| Dulac 2024, older adults | | | | |

A technical report like NASA TM-4580 is not expected in PubMed or Embase — that absence is
the argument for running NTRS at all, and it belongs in the report's methods section.
