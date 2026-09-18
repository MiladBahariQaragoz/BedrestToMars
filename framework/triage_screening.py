"""Stage 1 of the title/abstract screen: deterministic triage.

Usage:
    python framework/triage_screening.py

Reads data/search/screening.csv, applies the eligibility criteria from
docs/literature-review/PLAN.md section 2 as explicit rules, and writes back:

    triage          auto_exclude | priority | maybe
    screen_ta       filled in only for auto_exclude; a human fills in the rest
    exclusion_reason  one of the fixed codes, for auto-excluded records only
    notes           which signals fired, so every decision can be argued with

Nothing is deleted and no record is ever auto-*included*. A machine can rule a paper out on
species or publication type; deciding a paper is in requires reading it.

The bias is deliberate and matches the plan: `maybe` is cheap, `exclude` is expensive. A
record is only auto-excluded on a high-confidence signal, and every auto-exclusion carries
the phrase that triggered it.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENING_CSV = REPO_ROOT / "data" / "search" / "screening.csv"
REPORT_MD = REPO_ROOT / "data" / "search" / "screening_report.md"

csv.field_size_limit(10_000_000)


def patterns(*fragments) -> re.Pattern:
    return re.compile("|".join(fragments), re.IGNORECASE)


# --- high-confidence exclusions ------------------------------------------------------

ANIMAL = patterns(
    r"\bmice\b", r"\bmouse\b", r"\bmurine\b", r"\brats?\b", r"\brodents?\b",
    r"hindlimb", r"hind limb", r"hind-limb", r"\bC2C12\b", r"\bL6 myotubes?\b",
    r"zebrafish", r"drosophila", r"\bxenopus\b", r"\bcanine\b", r"\bporcine\b",
    r"\bbovine\b", r"\bequine\b", r"\bmonkeys?\b", r"\brhesus\b", r"\brabbits?\b",
    r"\bnematode", r"\bc\. elegans\b", r"\bcaenorhabditis\b", r"\bsheep\b",
    r"tail suspension", r"tail-suspension", r"\bhindlimb unloading\b",
)

IN_VITRO = patterns(
    r"\bin vitro\b", r"\bcell culture\b", r"\bcultured (?:human )?(?:myotubes|myoblasts|cells)\b",
    r"\bmyotube", r"\bmyoblast", r"\borganoid", r"\bcell line\b", r"\bsatellite cells?\b",
    r"random positioning machine", r"\bclinostat", r"\brotating wall vessel\b",
)

REVIEW = patterns(
    r"^a? ?(?:systematic|scoping|narrative|umbrella|rapid) review",
    r"\bsystematic review\b", r"\bmeta-analys", r"\bmetaanalys", r"\bnarrative review\b",
    r"\bscoping review\b", r"\bthis review\b", r"\bwe review\b", r"\breview of the literature\b",
    r"\beditorial\b", r"\bcommentary\b", r"\bletter to the editor\b", r"\bbook chapter\b",
    r"\bstudy protocol\b", r"\bprotocol for a\b", r"\bstudy design and protocol\b",
)

# --- eligibility signals -------------------------------------------------------------

UNLOADING = patterns(
    r"\bbed ?rest\b", r"\bbed-rest\b", r"head[- ]down", r"\bHDBR\b", r"\bHDT\b",
    r"\bHDTBR\b", r"antiorthostatic", r"anti-orthostatic", r"\bhypokinesia\b",
    r"\bhypodynamia\b", r"dry immersion", r"\bDI\b(?= |,|\.)", r"limb suspension",
    r"\bULLS\b", r"unilateral lower limb", r"simulated microgravity",
    r"microgravity analog", r"spaceflight analog", r"ground[- ]based analog",
    r"mechanical unloading", r"muscle unloading", r"\bdisuse\b", r"\bimmobili[sz]ation\b",
    r"\bunloading\b", r"\bspaceflight\b", r"\bmicrogravity\b", r"\bweightlessness\b",
    r"\bISS mission", r"\bastronauts?\b", r"\bcosmonauts?\b",
    # Artificial-gravity work in this literature is almost always a bed-rest campaign
    # (AGBRESA and its relatives), and the abstract often names the centrifuge, not the bed.
    r"artificial gravity", r"\bAGBRESA\b", r"short[- ]arm centrifug", r"centrifugation",
)

# The exposures that are real unloading models for this dataset, as opposed to any
# mention of disuse. Used to separate `priority` from `maybe`.
CORE_MODEL = patterns(
    r"\bbed ?rest\b", r"\bbed-rest\b", r"head[- ]down", r"\bHDBR\b", r"\bHDTBR\b",
    r"antiorthostatic", r"anti-orthostatic", r"\bhypokinesia\b", r"dry immersion",
    r"limb suspension", r"\bULLS\b", r"unilateral lower limb suspension",
)

MUSCLE_OUTCOME = patterns(
    r"muscle volume", r"muscle mass", r"muscle size", r"muscle cross[- ]sectional",
    r"cross[- ]sectional area", r"\bCSA\b", r"\bPCSA\b", r"lean mass", r"lean tissue",
    r"muscle thickness", r"muscle atroph", r"muscular atroph", r"muscle wasting",
    r"muscle loss", r"\batroph\w*\b", r"muscle morpholog", r"fat[- ]free mass",
    r"muscle volume loss", r"thigh volume", r"calf volume", r"quadriceps volume",
)

IMAGING = patterns(
    r"\bMRI\b", r"magnetic resonance", r"\bCT\b", r"computed tomography", r"\bpQCT\b",
    r"\bDXA\b", r"\bDEXA\b", r"dual[- ]energy x[- ]ray", r"ultrasound", r"ultrasonograph",
    r"\bBIA\b", r"bioelectrical impedance",
)

LOWER_LIMB = patterns(
    r"\bsoleus\b", r"gastrocnemi", r"triceps surae", r"plantar ?flexor", r"\bquadriceps\b",
    r"vastus", r"knee extensor", r"\bhamstring", r"\bgluteus\b", r"\bpsoas\b",
    r"\bthigh\b", r"\bcalf\b", r"lower limb", r"lower extremit", r"\bleg muscle",
    r"tibialis anterior", r"\bshank\b", r"\bankle\b",
)

UPPER_LIMB_ONLY = patterns(r"\bforearm\b", r"\bbiceps brachii\b", r"\bhandgrip\b", r"\bwrist\b")

DURATION = re.compile(
    r"\b(\d{1,3})[\s-]*(day|days|d|week|weeks|wk|wks|month|months)\b(?=[^.]{0,60}"
    r"(bed ?rest|head[- ]down|immersion|unloading|suspension|immobili|disuse|spaceflight))",
    re.IGNORECASE,
)

CLINICAL_WASTING = patterns(
    r"\bcancer cachexia\b", r"\bcachexia\b", r"\bmuscular dystroph", r"\bDuchenne\b",
    r"\bALS\b", r"amyotrophic lateral", r"\bstroke\b", r"spinal cord injur",
    r"\bCOPD\b", r"\bh(a)?emodialysis\b", r"chronic kidney disease", r"\bcirrhosis\b",
    r"\bICU[- ]acquired weakness\b", r"critical(?:ly)? ill", r"\bsepsis\b",
    r"\bhip fracture\b", r"\bACL reconstruction\b", r"anterior cruciate",
    r"\bsarcopenia in\b", r"\bcerebral palsy\b", r"\bmyopath",
)


def has(pattern: re.Pattern, text: str) -> str:
    match = pattern.search(text or "")
    return match.group(0) if match else ""


def triage_record(row: dict) -> tuple:
    """Return (triage, screen_ta, exclusion_reason, note)."""
    title = row["title"] or ""
    abstract = row["abstract"] or ""
    text = f"{title} {abstract}"
    signals = []

    animal = has(ANIMAL, text)
    in_vitro = has(IN_VITRO, text)
    review = has(REVIEW, text)
    unloading = has(UNLOADING, text)
    core_model = has(CORE_MODEL, text)
    outcome = has(MUSCLE_OUTCOME, text)
    imaging = has(IMAGING, text)
    lower_limb = has(LOWER_LIMB, text)
    clinical = has(CLINICAL_WASTING, text)
    duration = DURATION.search(text)

    # --- auto-exclusions, highest confidence first
    human_context = re.search(
        r"\b(participants?|volunteers?|subjects?|men|women|humans?|patients?|astronauts?|cosmonauts?)\b",
        text, re.IGNORECASE)
    if animal and not human_context:
        return "auto_exclude", "exclude", "not_human", f"animal model: {animal}"
    if in_vitro and not core_model:
        return "auto_exclude", "exclude", "not_human", f"in vitro: {in_vitro}"
    if review and not core_model:
        return "auto_exclude", "exclude", "review_or_editorial", f"publication type: {review}"
    if not unloading:
        return "auto_exclude", "exclude", "not_unloading_model", "no unloading exposure in title or abstract"
    if not outcome:
        # A real unloading study whose abstract reports something else entirely - gait,
        # motor units, cardiovascular - contributes no rows, but it does identify a
        # campaign, and campaigns are what the cohort map is made of. Kept in its own
        # bucket rather than discarded with the rest.
        if core_model:
            return ("campaign_lead", "exclude", "no_muscle_outcome",
                    f"unloading campaign without a muscle outcome ({core_model}) - "
                    "no rows, but a lead for data/cohorts.csv")
        return "auto_exclude", "exclude", "no_muscle_outcome", "no muscle-tissue outcome term"

    # --- everything below is kept for a human to read
    if animal:
        signals.append(f"animal term present ({animal}) alongside human context")
    if review:
        signals.append(f"possible review ({review})")
    if clinical:
        signals.append(f"clinical wasting context ({clinical})")
    if duration:
        signals.append(f"duration: {duration.group(0)}")
    if imaging:
        signals.append(f"imaging: {imaging}")
    if not lower_limb:
        signals.append("no lower-limb term")
    if has(UPPER_LIMB_ONLY, text) and not lower_limb:
        signals.append("upper limb only?")
    if not abstract:
        signals.append("no abstract - title-only screen")

    priority = bool(core_model and outcome and lower_limb and not clinical)
    note = "; ".join(signals)
    return ("priority" if priority else "maybe"), "", "", note


def main() -> int:
    if not SCREENING_CSV.exists():
        print(f"missing {SCREENING_CSV} - run framework/merge_search_exports.py first")
        return 1

    with SCREENING_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    if "triage" not in columns:
        columns.insert(columns.index("screen_ta"), "triage")

    counts = Counter()
    reasons = Counter()
    for row in rows:
        triage, screen_ta, reason, note = triage_record(row)
        row["triage"] = triage
        row["screen_ta"] = screen_ta
        row["exclusion_reason"] = reason
        row["notes"] = "; ".join(part for part in (row.get("notes", ""), note) if part)
        if screen_ta == "exclude":
            row["screener"] = "triage_script"
            row["screen_date"] = "2026-09-04"
        counts[triage] += 1
        if reason:
            reasons[reason] += 1

    with SCREENING_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    write_report(rows, counts, reasons)

    print(f"{len(rows)} records triaged")
    for name, count in counts.most_common():
        print(f"  {name:14s} {count:5d}")
    print("auto-exclusion reasons:")
    for reason, count in reasons.most_common():
        print(f"  {reason:24s} {count:5d}")
    return 0


def write_report(rows: list, counts: Counter, reasons: Counter) -> None:
    priority = [r for r in rows if r["triage"] == "priority"]
    years = Counter(r["year"] for r in priority)
    lines = [
        "# Screening Report — stage 1 triage",
        "",
        "Produced by `framework/triage_screening.py` on 2026-09-04, applying the eligibility",
        "criteria in `docs/literature-review/PLAN.md` §2. No record is auto-*included*: the",
        "script only rules records out, and only on high-confidence signals.",
        "",
        "## Triage outcome",
        "",
        "| Bucket | Records | Meaning |",
        "|---|---|---|",
        f"| `priority` | {counts['priority']} | Core unloading model, a muscle outcome and a lower-limb term. Read these first |",
        f"| `maybe` | {counts['maybe']} | Passed the exclusions but is missing one signal. Read after the priority set |",
        f"| `campaign_lead` | {counts['campaign_lead']} | A real unloading campaign reporting something other than muscle. No rows, but a lead for the cohort map |",
        f"| `auto_exclude` | {counts['auto_exclude']} | Ruled out by rule, with the triggering phrase recorded in `notes` |",
        f"| **Total** | **{len(rows)}** | |",
        "",
        "## Auto-exclusions, by reason",
        "",
        "| Reason | Records |",
        "|---|---|",
    ]
    for reason, count in reasons.most_common():
        lines.append(f"| `{reason}` | {count} |")
    lines += [
        "",
        "## Priority set, by year",
        "",
        "| Year | Records |",
        "|---|---|",
    ]
    for year, count in sorted(years.items(), reverse=True):
        lines.append(f"| {year} | {count} |")
    lines += [
        "",
        "Every auto-exclusion is reversible: the reason and the phrase that triggered it are",
        "in `exclusion_reason` and `notes`, so a rule that turns out to be too aggressive can",
        "be found and undone by filtering one column.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
