"""Forecast muscle change as a probability distribution over declared ranges.

This is the machinery behind the forecast in `DESIGN.md` section 9.3, which puts a language
model - TypeSafe's Jev - to a question it can answer: given who the participants were, what
they did and how muscles like this one behaved elsewhere, which of these ranges will the
measurement fall in? The model returns a probability for every range. Everything numeric
happens here, in code: the point forecast, the most probable interval, and the scores.
TypeSafe's own documentation is plain that the model is not a calculator.

Two arms, declared in `config.yaml`:

* `without_history` - the model sees nothing of the held-out campaign, exactly like the
  tier-2 families, and forecasts the percent change from baseline.
* `with_history` - the model also sees the earlier scans of the same measurement and of the
  same campaign, strictly before the target day, and forecasts the change since the last
  scan. Only 84 rows from 5 campaigns have an earlier scan to show.

What the model is shown is built by `build_state`, and three rules hold there by assertion
rather than by care: no row of the held-out campaign enters the reference tables, nothing
that names a paper, author or campaign is sent, and the target's own outcome is never read.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd

import cv
import features
import models

LOG_FLOOR = 1e-6
MISSING = {"", "NA", "na", "nan", "NaN", "None"}
IDENTITY_COLUMNS = ("cohort_id", "campaign_name", "study_id", "first_author", "doi", "registry_id")
VARIANTS = ("full", "generic", "no_reference", "reordered")
GENERIC_MEASUREMENT = (
    "muscle", "muscle_family", "functional_role", "granularity", "made_up_of",
    "imaging_method", "quantity",
)

BACKGROUND = (
    "These records come from bed-rest studies, the ground-based model of the muscle loss "
    "astronauts suffer in weightlessness. Healthy volunteers stay in bed, often tilted "
    "head-down, for days to months, and their muscles are scanned before and during the "
    "bed rest. Every value is a group mean: the percent change in a muscle's size from the "
    "same participants' measurement before bed rest. Negative values are losses. A scan "
    "taken partway through a campaign reflects the days of bed rest up to that scan, not "
    "the campaign's planned total."
)

DESIGNS = {
    "HDBR_-6": "head-down tilt bed rest",
    "horizontal_BR": "horizontal bed rest",
    "ULLS": "unilateral lower limb suspension",
    "dry_immersion": "dry immersion",
}
SEXES = {"M": "men only", "F": "women only", "mixed": "men and women"}
ROLES = {
    "antigravity_extensor": "antigravity extensor: holds the body up against gravity when standing",
    "flexor": "flexor: does not bear body weight when standing",
    "mixed": "mixed: partly weight-bearing, partly not",
}
QUANTITIES = {
    "volume": "muscle volume",
    "CSA": "cross-sectional area",
    "lean_mass": "lean mass",
    "thickness": "muscle thickness",
}


# --- bins -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Bins:
    """Evenly spaced ranges with an open range at each end.

    `edges` are the interior boundaries. Every range is closed below and open above, so a
    value sitting on an edge belongs to the range that starts there.
    """

    edges: tuple[float, ...]
    step: float

    @property
    def count(self) -> int:
        return len(self.edges) + 1

    @property
    def lows(self) -> tuple[float, ...]:
        return (-math.inf, *self.edges)

    @property
    def highs(self) -> tuple[float, ...]:
        return (*self.edges, math.inf)

    @property
    def labels(self) -> tuple[str, ...]:
        first, last = self.edges[0], self.edges[-1]
        inner = [f"{_fmt(low)}_to_{_fmt(high)}" for low, high in zip(self.edges, self.edges[1:])]
        return (f"below_{_fmt(first)}", *inner, f"{_fmt(last)}_and_above")

    @property
    def representatives(self) -> np.ndarray:
        """The value each range stands for: its midpoint, or half a step beyond an open end."""
        edges = np.asarray(self.edges, dtype=float)
        middles = (edges[:-1] + edges[1:]) / 2.0
        return np.concatenate(
            [[edges[0] - self.step / 2.0], middles, [edges[-1] + self.step / 2.0]]
        )


def _fmt(value: float) -> str:
    return f"{value:g}"


def make_bins(edges: Sequence[float]) -> Bins:
    values = np.asarray(edges, dtype=float)
    if len(values) < 2:
        raise ValueError("at least two edges are needed")
    gaps = np.diff(values)
    if np.any(gaps <= 0):
        raise ValueError(f"edges must be strictly increasing, got {list(edges)}")
    if not np.allclose(gaps, gaps[0]):
        raise ValueError(
            f"edges must be evenly spaced, got {list(edges)}: the scores read a range's "
            "width off the step"
        )
    return Bins(edges=tuple(float(value) for value in values), step=float(gaps[0]))


def shift_bins(bins: Bins) -> Bins:
    """The same ranges moved half a step up: a check that answers do not hang on where edges fall."""
    return make_bins([edge + bins.step / 2 for edge in bins.edges])


def arm_bins(config: dict[str, Any], arm: str) -> Bins:
    return make_bins(config["forecast"]["arms"][arm]["edges"])


def bin_index(bins: Bins, value: float) -> int:
    return int(np.searchsorted(np.asarray(bins.edges), float(value), side="right"))


# --- turning a distribution into a forecast --------------------------------------------


def point(bins: Bins, probs: np.ndarray) -> float:
    """The probability-weighted mean of the ranges' representative values."""
    return float(np.asarray(probs, dtype=float) @ bins.representatives)


def interval(bins: Bins, probs: np.ndarray, level: float) -> tuple[float, float]:
    """The shortest run of adjacent ranges whose probability reaches `level`.

    This is the "most probable range" the forecast reports. Among runs of equal length the
    one carrying more probability wins, then the lower one.
    """
    probs = np.asarray(probs, dtype=float)
    best: tuple[int, float, int, int] | None = None
    for start in range(bins.count):
        mass = 0.0
        for stop in range(start, bins.count):
            mass += probs[stop]
            if mass >= level - 1e-12:
                candidate = (stop - start + 1, -mass, start, stop)
                if best is None or candidate < best:
                    best = candidate
                break
    if best is None:
        raise ValueError(f"the probabilities sum to {probs.sum():.3f}, below {level}")
    _, _, start, stop = best
    return bins.lows[start], bins.highs[stop]


def covered(bounds: tuple[float, float], value: float) -> bool:
    low, high = bounds
    return low <= float(value) < high


def interval_width(bins: Bins, bounds: tuple[float, float]) -> float:
    """Width in the target's units, counting an open range as one step wide."""
    low, high = bounds
    low = max(low, bins.edges[0] - bins.step)
    high = min(high, bins.edges[-1] + bins.step)
    return float(high - low)


# --- proper scores ----------------------------------------------------------------------


def crps(bins: Bins, probs: np.ndarray, truth: float) -> float:
    """The ranked probability score scaled by the step, so it reads in the target's units.

    For a forecast that puts all its probability on one range this is the distance, in
    steps times the step, between that range and the true one - the binned version of the
    absolute error - which is what makes it comparable with the MAE the tier-2 table reports.
    """
    cumulative = np.cumsum(np.asarray(probs, dtype=float))[:-1]
    observed = (np.arange(bins.count - 1) >= bin_index(bins, truth)).astype(float)
    return float(bins.step * np.sum((cumulative - observed) ** 2))


def log_score(bins: Bins, probs: np.ndarray, truth: float) -> float:
    """Minus the log of the probability given to the true range, floored at 1e-6."""
    given = float(np.asarray(probs, dtype=float)[bin_index(bins, truth)])
    return float(-math.log(max(given, LOG_FLOOR)))


def score_row(
    bins: Bins, probs: np.ndarray, truth: float, levels: Sequence[float]
) -> dict[str, float]:
    forecast_value = point(bins, probs)
    scores: dict[str, float] = {
        "point": forecast_value,
        "abs_error": abs(float(truth) - forecast_value),
        "crps": crps(bins, probs, truth),
        "log_score": log_score(bins, probs, truth),
    }
    for level in levels:
        suffix = int(round(level * 100))
        bounds = interval(bins, probs, level)
        scores[f"low_{suffix}"] = bounds[0]
        scores[f"high_{suffix}"] = bounds[1]
        scores[f"covered_{suffix}"] = float(covered(bounds, truth))
        scores[f"width_{suffix}"] = interval_width(bins, bounds)
    return scores


# --- distributions ----------------------------------------------------------------------


def empirical_distribution(bins: Bins, centre: float, residuals: np.ndarray) -> np.ndarray:
    """A baseline's forecast distribution: its point plus the residuals it made in training.

    Giving the baselines a distribution built this way is what lets them be scored on the
    same intervals and proper scores as the model, rather than on the MAE alone.
    """
    residuals = np.asarray(residuals, dtype=float)
    probs = np.zeros(bins.count, dtype=float)
    if len(residuals) == 0:
        probs[bin_index(bins, centre)] = 1.0
        return probs
    indices = np.searchsorted(np.asarray(bins.edges), centre + residuals, side="right")
    return np.bincount(indices, minlength=bins.count).astype(float) / len(residuals)


def probabilities_from_answer(bins: Bins, answer: dict[str, Any]) -> np.ndarray:
    """The model's probabilities in range order. A range it did not return gets zero."""
    given = answer["probabilities"]
    probs = np.array([float(given.get(label, 0.0)) for label in bins.labels], dtype=float)
    total = probs.sum()
    if total <= 0:
        raise ValueError("the answer carries no probability for any declared range")
    return probs / total


# --- earlier scans of the same measurement ---------------------------------------------


def with_history(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """The rows that have an earlier scan of the same measurement, with that scan attached.

    A measurement is one muscle followed in one arm of one campaign by one method
    (`forecast.series` in the config). Scans on the same day are averaged, and a scan never
    counts as earlier than one taken the same day.
    """
    series = config["forecast"]["series"]
    time = config["forecast"]["time_column"]
    kept: list[pd.Series] = []
    for _, group in frame.groupby(series, dropna=False, sort=False):
        by_day = group.groupby(time)["pct_change"].mean().sort_index()
        for index, row in group.iterrows():
            earlier = by_day[by_day.index < row[time]]
            if earlier.empty:
                continue
            row = row.copy()
            row["prev_time"] = float(earlier.index[-1])
            row["prev_value"] = float(earlier.iloc[-1])
            row["history"] = [(float(day), float(value)) for day, value in earlier.items()]
            row.name = index
            kept.append(row)
    if not kept:
        return frame.iloc[0:0].assign(prev_time=[], prev_value=[], history=[])
    return pd.DataFrame(kept).sort_index()


# --- the reference curve ----------------------------------------------------------------


def reference_curve(train: pd.DataFrame, config: dict[str, Any]) -> models.DurationOnlyBaseline:
    """The duration-only curve on the day of the scan, fitted to the training campaigns."""
    time = config["forecast"]["time_column"]
    return models.DurationOnlyBaseline(form="log").fit(
        train[time].to_numpy(dtype=float),
        train[config["target"]["column"]].to_numpy(dtype=float),
        features.weights(train, config).to_numpy(dtype=float),
    )


def curve_at(curve: models.DurationOnlyBaseline, day: float) -> float:
    return float(curve.predict(np.array([float(day)]))[0])


# --- what the model is shown ------------------------------------------------------------


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return str(value).strip() not in MISSING


def _num(value: Any) -> float | int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return int(number) if number.is_integer() else round(number, 1)


def _words(value: Any) -> str:
    return str(value).replace("_", " ")


def _pct(value: float) -> str:
    return f"{value:+.1f}%"


def _pp(value: float) -> str:
    return f"{value:+.1f} percentage points"


def _drop_missing(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if _present(value)}


def _group(row: pd.Series) -> str:
    if row.get("arm_type") != "countermeasure":
        return "control, no countermeasure"
    return f"countermeasure: {_words(row.get('cm_modality', 'unspecified'))}"


def describe_participants(row: pd.Series) -> dict[str, Any]:
    age_range = None
    if _present(row.get("age_min")) and _present(row.get("age_max")):
        age_range = f"{_num(row['age_min'])} to {_num(row['age_max'])}"
    return _drop_missing(
        {
            "sex": SEXES.get(str(row.get("sex")), None),
            "percent_female": _num(row.get("pct_female")),
            "mean_age_years": _num(row.get("age_mean")),
            "age_sd_years": _num(row.get("age_sd")),
            "age_range_years": age_range,
            "population": _words(row.get("population", "")).replace("healthy ", "healthy, ")
            .replace("young", "young adults").replace("older", "older adults"),
            "mean_body_mass_kg": _num(row.get("body_mass_mean_kg")),
            "mean_bmi": _num(row.get("bmi_mean")),
            "participants_measured": _num(row.get("n_analysed")),
        }
    )


def describe_protocol(row: pd.Series) -> dict[str, Any]:
    countermeasure = row.get("arm_type") == "countermeasure"
    return _drop_missing(
        {
            "unloading": DESIGNS.get(str(row.get("design")), _words(row.get("design", ""))),
            "head_down_tilt_degrees": _num(row.get("hdt_angle_deg")),
            "planned_total_days": _num(row.get("duration_days")),
            "nutrition_controlled": row.get("nutrition_controlled"),
            "group": _group(row),
            "countermeasure_protocol": row.get("cm_dose") if countermeasure else None,
        }
    )


def describe_measurement(row: pd.Series, config: dict[str, Any]) -> dict[str, Any]:
    whole = row.get("muscle") in set(config["subset"]["whole_segment_muscles"])
    if whole:
        granularity = "a whole limb segment"
    elif row.get("is_composite") == "TRUE":
        granularity = "a muscle group measured together"
    else:
        granularity = "a single muscle"
    return _drop_missing(
        {
            "muscle": _words(row.get("muscle", "")),
            "muscle_family": _words(row.get("muscle_family", "")),
            "functional_role": ROLES.get(
                str(row.get("muscle_function_class")), _words(row.get("muscle_function_class", ""))
            ),
            "granularity": granularity,
            "made_up_of": _words(row.get("composite_of", "")) if not whole else None,
            "side": row.get("laterality"),
            "imaging_method": row.get("modality"),
            "quantity": QUANTITIES.get(str(row.get("outcome_type")), row.get("outcome_type")),
            "measurement_site": row.get("measurement_site"),
            "site_kind": _words(row.get("site_kind", "")),
        }
    )


def _observation(row: pd.Series, time: str) -> dict[str, Any]:
    method = f"{row.get('modality')} {QUANTITIES.get(str(row.get('outcome_type')), '')}"
    return _drop_missing(
        {
            "muscle": _words(row.get("muscle", "")),
            "family": _words(row.get("muscle_family", "")),
            "group": _group(row),
            "unloading": DESIGNS.get(str(row.get("design")), None),
            "sex": SEXES.get(str(row.get("sex")), None),
            "method": method.strip(),
            "day": _num(row[time]),
            "planned_total_days": _num(row.get("duration_days")),
            "change": _pct(float(row["pct_change"])),
        }
    )


def _transition(row: pd.Series, time: str) -> dict[str, Any]:
    record = _observation(row, time)
    record.pop("change", None)
    record.pop("day", None)
    record.update(
        {
            "from_day": _num(row["prev_time"]),
            "to_day": _num(row[time]),
            "change_at_first_scan": _pct(float(row["prev_value"])),
            "change_at_second_scan": _pct(float(row["pct_change"])),
            "further_change": _pp(float(row["pct_change"]) - float(row["prev_value"])),
        }
    )
    return record


def _by_relevance(rows: pd.DataFrame, target: pd.Series, day: float, time: str) -> pd.DataFrame:
    """Same muscle first, then the same family, then the same kind of group, then nearest day."""
    if rows.empty:
        return rows
    order = pd.DataFrame(
        {
            "muscle": (rows["muscle"] != target["muscle"]).astype(int),
            "family": (rows["muscle_family"] != target["muscle_family"]).astype(int),
            "group": (rows["arm_type"] != target["arm_type"]).astype(int),
            "distance": (rows[time].astype(float) - day).abs(),
        },
        index=rows.index,
    )
    return rows.loc[order.sort_values(["muscle", "family", "group", "distance"], kind="stable").index]


def _assert_no_identity(state: dict[str, Any], target: pd.Series) -> None:
    text = json.dumps(state)
    for column in IDENTITY_COLUMNS:
        value = str(target.get(column, ""))
        if len(value) >= 5 and value.upper() != "NA" and value in text:
            raise cv.LeakageError(f"the state names the source through {column}: {value}")


def _fit_to_budget(
    state: dict[str, Any], budget_chars: float, trimmable: Sequence[str]
) -> dict[str, int]:
    """Keep the leading, most relevant records of each list that fit in the budget."""
    lists = {key: state[key] for key in trimmable if key in state}
    for key in lists:
        state[key] = []
    remaining = budget_chars - len(json.dumps(state))
    if remaining < 0:
        raise ValueError(
            f"the state is {len(json.dumps(state))} characters before any reference rows, "
            f"over the budget of {budget_chars:.0f}"
        )
    kept: dict[str, int] = {}
    for key, records in lists.items():
        count = 0
        for record in records:
            cost = len(json.dumps(record)) + 2
            if cost > remaining:
                break
            remaining -= cost
            count += 1
        state[key] = records[:count]
        kept[key] = count
    return kept


def build_state(
    target: pd.Series,
    train: pd.DataFrame,
    held_out: pd.DataFrame,
    arm: str,
    config: dict[str, Any],
    token_budget: int | None = None,
    curve: models.DurationOnlyBaseline | None = None,
    train_transitions: pd.DataFrame | None = None,
    variant: str = "full",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Everything the model is told about one forecast, and how much of it fitted.

    `train` is the training campaigns' rows, `held_out` the rows of the target's own
    campaign. Only the `with_history` arm reads `held_out`, and only scans taken strictly
    before the target day.

    `variant` is one of the ablations of `DESIGN.md` sections 9.3.2 and 9.3.4. `generic`
    describes the target only by what identifies no study - muscle, role, method, kind of
    group and day. `no_reference` drops everything taken from the other campaigns.
    `reordered` shows exactly the rows the full state shows, in a shuffled order.
    """
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; declared: {VARIANTS}")
    settings = config["forecast"]
    time = settings["time_column"]
    cohort = str(target["cohort_id"])
    if (train["cohort_id"].astype(str) == cohort).any():
        raise cv.LeakageError(f"the reference rows include the held-out campaign {cohort}")
    if (held_out["cohort_id"].astype(str) != cohort).any():
        raise cv.LeakageError("rows of another campaign were passed as the held-out campaign")

    day = float(target[time])
    planned = float(target["duration_days"])
    curve = curve or reference_curve(train, config)

    if variant == "generic":
        measurement = describe_measurement(target, config)
        state: dict[str, Any] = {
            "background": BACKGROUND,
            "protocol": _drop_missing(
                {
                    "unloading": describe_protocol(target).get("unloading"),
                    "group": "countermeasure"
                    if target.get("arm_type") == "countermeasure"
                    else "control, no countermeasure",
                }
            ),
            "measurement": {
                key: measurement[key] for key in GENERIC_MEASUREMENT if key in measurement
            },
            "target": {"day_of_bed_rest": _num(day)},
        }
    else:
        state = {
            "background": BACKGROUND,
            "participants": describe_participants(target),
            "protocol": describe_protocol(target),
            "measurement": describe_measurement(target, config),
            "target": {
                "day_of_bed_rest": _num(day),
                "planned_total_days": _num(planned),
                "days_before_bed_rest_ends": _num(max(planned - day, 0.0)),
            },
        }
    references = variant != "no_reference"

    curve_days = sorted({float(value) for value in settings["reference_curve_days"]} | {day})
    if arm == "with_history":
        previous_day = float(target["prev_time"])
        previous_value = float(target["prev_value"])
        curve_days = sorted(set(curve_days) | {previous_day})
        state["this_measurement"] = {
            "scans_so_far": [
                {"day": _num(scan_day), "change": _pct(value)}
                for scan_day, value in target["history"]
            ],
            "last_scan": {"day": _num(previous_day), "change": _pct(previous_value)},
            "days_from_last_scan_to_target": _num(day - previous_day),
            "average_change_per_day_so_far": (
                f"{previous_value / previous_day:+.2f} percentage points per day"
            ),
        }
        if references:
            state["this_measurement"]["further_change_the_typical_curve_expects"] = _pp(
                curve_at(curve, day) - curve_at(curve, previous_day)
            )
        earlier = held_out[held_out[time].astype(float) < day]
        earlier = _by_relevance(earlier, target, day, time)
        state["earlier_scans_in_this_campaign"] = [
            _observation(row, time) for _, row in earlier.iterrows()
        ]

    if references:
        state["typical_curve_other_campaigns"] = {
            "what_it_is": (
                "A duration-only curve fitted to every muscle and group in the other "
                "campaigns. It ignores which muscle, which group and which method."
            ),
            "values": [
                {"day": _num(curve_day), "change": _pct(curve_at(curve, curve_day))}
                for curve_day in curve_days
            ],
        }

    trimmable = ["observations_other_campaigns"]
    if arm == "with_history" and references:
        transitions = train_transitions if train_transitions is not None else with_history(train, config)
        transitions = _by_relevance(transitions, target, day, time)
        state["scan_to_scan_changes_other_campaigns"] = [
            _transition(row, time) for _, row in transitions.iterrows()
        ]
        trimmable = [
            "earlier_scans_in_this_campaign",
            "scan_to_scan_changes_other_campaigns",
            "observations_other_campaigns",
        ]

    if arm == "with_history" and not references:
        trimmable = ["earlier_scans_in_this_campaign"]

    observations = _by_relevance(train, target, day, time)
    available = len(observations) if references else 0
    if references:
        state["observations_other_campaigns"] = [
            _observation(row, time) for _, row in observations.iterrows()
        ]

    budget = token_budget or int(settings["state_token_budget"])
    chars_per_token = float(settings["chars_per_token"])
    kept = _fit_to_budget(state, budget * chars_per_token, trimmable)
    if variant == "reordered":
        seed = int(hashlib.sha256(str(target.get("row_id", "")).encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        for key in trimmable:
            if key in state:
                state[key] = [state[key][i] for i in rng.permutation(len(state[key]))]
    _assert_no_identity(state, target)

    info = {
        "estimated_tokens": int(math.ceil(len(json.dumps(state)) / chars_per_token)),
        "observations_kept": kept.get("observations_other_campaigns", 0),
        "observations_available": available,
        "transitions_kept": kept.get("scan_to_scan_changes_other_campaigns", 0),
    }
    return state, info


def scramble(train: pd.DataFrame, seed: int) -> pd.DataFrame:
    """The training rows with their outcome shuffled among them, and nothing else changed.

    The `scrambled_reference` ablation shows the model these rows in place of the real ones:
    every description is intact, but no value belongs to its row any more.
    """
    shuffled = train.copy()
    rng = np.random.default_rng(int(seed))
    shuffled["pct_change"] = rng.permutation(train["pct_change"].to_numpy())
    return shuffled


# --- the recognition probe --------------------------------------------------------------


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def recognition_state(target: pd.Series, config: dict[str, Any]) -> dict[str, Any]:
    """The description of the target exactly as the full forecast sends it, and no more."""
    planned = float(target["duration_days"])
    day = float(target[config["forecast"]["time_column"]])
    state = {
        "participants": describe_participants(target),
        "protocol": describe_protocol(target),
        "measurement": describe_measurement(target, config),
        "target": {
            "day_of_bed_rest": _num(day),
            "planned_total_days": _num(planned),
            "days_before_bed_rest_ends": _num(max(planned - day, 0.0)),
        },
    }
    _assert_no_identity(state, target)
    return state


def recognition_label(cohort: str, config: dict[str, Any]) -> str | None:
    """The option naming this campaign, or None when the probe does not cover it."""
    name = config["forecast"]["ablation"]["recognition"]["campaigns"].get(cohort)
    return _slug(name) if name else None


def recognition_question(config: dict[str, Any]) -> dict[str, Any]:
    """One Choice question: which named campaign does this description come from?"""
    settings = config["forecast"]["ablation"]["recognition"]
    names = list(dict.fromkeys(settings["campaigns"].values()))
    criteria = {_slug(name): name for name in names}
    criteria[_slug(settings["none_label"])] = settings["none_label"]
    return {
        "type": "choice",
        "instructions": (
            "These participants, this protocol and this measurement come from one published "
            "bed-rest campaign. Which campaign is it? Choose none of these campaigns if the "
            "description fits none of them or you cannot tell."
        ),
        "criteria": criteria,
    }


# --- the question -----------------------------------------------------------------------


def _describe_range(low: float, high: float, arm: str) -> str:
    if arm == "without_history":
        if math.isinf(low):
            return f"more than {_fmt(-high)} percent smaller than before bed rest"
        if math.isinf(high):
            return f"more than {_fmt(low)} percent larger than before bed rest"
        if high <= 0:
            return f"between {_fmt(-high)} and {_fmt(-low)} percent smaller than before bed rest"
        return f"between {_fmt(low)} and {_fmt(high)} percent larger than before bed rest"
    if math.isinf(low):
        return f"a further loss of more than {_fmt(-high)} percentage points"
    if math.isinf(high):
        return f"a regain of more than {_fmt(low)} percentage points"
    if high <= 0:
        return f"a further loss of between {_fmt(-high)} and {_fmt(-low)} percentage points"
    return f"a regain of between {_fmt(low)} and {_fmt(high)} percentage points"


def question(bins: Bins, arm: str) -> dict[str, Any]:
    """One Choice question: one option per declared range."""
    context = [
        "who the participants are (`participants`) and what protocol and countermeasure "
        "they followed (`protocol`)",
        "which muscle is measured, and how (`measurement`)",
        "how muscles like this one changed at similar days in other campaigns "
        "(`observations_other_campaigns`)",
        "the typical curve across other campaigns (`typical_curve_other_campaigns`)",
    ]
    if arm == "without_history":
        instructions = {
            "task": (
                "Predict the group-mean percent change in this muscle's size from its "
                "pre-bed-rest baseline on day `target.day_of_bed_rest` of bed rest."
            ),
            "consider": context,
            "sign": "Negative means the muscle is smaller than before bed rest.",
        }
    else:
        instructions = {
            "task": (
                "Predict how much this muscle's size will change between its most recent "
                "scan (`this_measurement.last_scan`) and day `target.day_of_bed_rest` of bed "
                "rest, in percentage points of its size before bed rest."
            ),
            "consider": [
                "how this measurement has changed so far (`this_measurement`)",
                "what other muscles and groups in the same campaign showed before the target "
                "day (`earlier_scans_in_this_campaign`)",
                "how similar muscles changed between two scans in other campaigns "
                "(`scan_to_scan_changes_other_campaigns`)",
                *context,
            ],
            "sign": "Negative means further loss; positive means the muscle grew back.",
        }
    criteria = {
        label: _describe_range(low, high, arm)
        for label, low, high in zip(bins.labels, bins.lows, bins.highs)
    }
    return {"type": "choice", "instructions": instructions, "criteria": criteria}
