"""Checks on the tier-3 ablations and the recognition probe. The model is replaced by a fake.

    python framework/tests/test_run_ablation.py
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import features
import run_ablation
import run_forecast
import typesafe_client

CONFIG = data_loader.load_config()
RESOLVED = features.resolve(data_loader.subset(data_loader.load(CONFIG), CONFIG), CONFIG, "A")
ARM = CONFIG["forecast"]["ablation"]["arm"]
PROBED = set(CONFIG["forecast"]["ablation"]["recognition"]["campaigns"])


def uniform(requests: list[dict]) -> list[dict]:
    """Every option of the request's one question equally likely."""
    out = []
    for request in requests:
        (name, question), = request["questions"].items()
        labels = list(question["criteria"])
        probabilities = {label: 1.0 / len(labels) for label in labels}
        out.append(
            {
                "model": "fake",
                "answers": {
                    name: {"type": "choice", "choice": labels[0], "confidence": 0.0,
                           "probabilities": probabilities}
                },
                "usage": {"input_tokens": 10},
                "from_cache": False,
            }
        )
    return out


RESULT = run_ablation.run(CONFIG, answerer=uniform)
FULL = run_forecast.fold_plan(CONFIG, RESOLVED, ARM)
SCRAMBLED = run_forecast.fold_plan(CONFIG, RESOLVED, ARM, variant="scrambled_reference")


def _keys(plan: list[dict]) -> list[str]:
    model = CONFIG["forecast"]["model"]
    return [typesafe_client.request_key(model, e["state"], e["questions"]) for e in plan]


def test_every_variant_is_scored_on_every_row_and_campaign() -> None:
    wanted = {"full", *CONFIG["forecast"]["ablation"]["variants"]}
    assert set(RESULT["variants"]) == wanted
    for variant, block in RESULT["variants"].items():
        assert block["rows"] == 346 and block["folds"] == 32, variant


def test_the_full_variant_is_answered_entirely_from_the_first_runs_cache() -> None:
    """The ablation must compare against the first run itself, not a re-asked copy of it."""
    cache = REPO_ROOT / CONFIG["forecast"]["cache_dir"]
    missing = [key for key in _keys(FULL) if not (cache / f"{key}.json").exists()]
    assert not missing, f"{len(missing)} full-variant requests are not in the committed cache"


def test_scrambling_changes_what_the_model_sees_but_not_the_baseline() -> None:
    for full, scrambled in zip(FULL[:25], SCRAMBLED[:25]):
        assert np.array_equal(full["baselines"]["duration_curve"], scrambled["baselines"]["duration_curve"])
        assert full["truth"] == scrambled["truth"]
    shown = [e["state"]["observations_other_campaigns"] for e in (FULL[0], SCRAMBLED[0])]
    assert [r["change"] for r in shown[0]] != [r["change"] for r in shown[1]]


def test_each_variant_reports_its_gain_over_the_curve_and_its_gap_to_full() -> None:
    for variant, block in RESULT["variants"].items():
        for name in ("paired_mae_gain_vs_curve_pp", "paired_mae_change_vs_full_pp"):
            interval = block[name]
            assert interval["low"] <= interval["point"] <= interval["high"], (variant, name)
    assert RESULT["variants"]["full"]["paired_mae_change_vs_full_pp"]["point"] == 0.0


def test_the_probe_covers_every_row_of_the_named_campaigns() -> None:
    probe = RESULT["recognition"]
    expected = RESOLVED[RESOLVED["cohort_id"].isin(PROBED)]
    assert probe["rows"] == len(expected)
    assert set(probe["campaigns"]) == set(expected["cohort_id"])
    options = len(set(CONFIG["forecast"]["ablation"]["recognition"]["campaigns"].values())) + 1
    assert abs(probe["chance"] - 1.0 / options) < 1e-12
    assert abs(probe["mean_p_true"] - 1.0 / options) < 1e-9


def test_a_constant_recognition_has_no_correlation_to_report() -> None:
    link = RESULT["recognition"]["spearman_with_gain"]
    assert link["n"] == len(RESULT["recognition"]["campaigns"])
    assert link["rho"] is None


def test_writing_produces_the_ablation_json_and_both_tables() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_ablation.write(RESULT, Path(tmp))
        text = (Path(tmp) / "forecast_ablation.json").read_text(encoding="utf-8")
        json.loads(text, parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))
        table = pd.read_csv(Path(tmp) / "forecast_ablation.csv")
        assert set(table["variant"]) == set(RESULT["variants"]) | {"duration_curve"}
        probe = pd.read_csv(Path(tmp) / "forecast_recognition.csv")
        assert len(probe) == len(RESULT["recognition"]["campaigns"])


def test_the_per_campaign_errors_of_every_variant_are_written() -> None:
    """The recognition reading rests on campaign-level errors, so they are a result file."""
    with tempfile.TemporaryDirectory() as tmp:
        run_ablation.write(RESULT, Path(tmp))
        table = pd.read_csv(Path(tmp) / "forecast_ablation_campaigns.csv")
        expected = {"cohort", "duration_curve", *(f"jev_{v}" for v in RESULT["variants"])}
        assert set(table.columns) == expected
        assert len(table) == 32


def test_an_offline_ablation_with_an_empty_cache_never_reaches_the_network() -> None:
    config = copy.deepcopy(CONFIG)
    with tempfile.TemporaryDirectory() as tmp:
        config["forecast"]["cache_dir"] = tmp
        try:
            run_ablation.run(config, offline=True)
        except typesafe_client.CacheMiss:
            return
    raise AssertionError("an offline ablation with an empty cache did not refuse")


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as error:
            failures += 1
            print(f"FAIL {test.__name__}: {type(error).__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
