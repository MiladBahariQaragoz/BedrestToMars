"""Checks on feature importance and its fold stability.

    python framework/tests/test_explain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import explain

CONFIG = data_loader.load_config()


class _SumsFirstColumn:
    """A model that uses one feature and ignores the other."""

    def predict(self, design: np.ndarray) -> np.ndarray:
        return np.asarray(design, dtype=float)[:, 0] * 3.0


def test_permutation_importance_finds_the_used_feature() -> None:
    rng = np.random.default_rng(0)
    design = rng.normal(size=(200, 2))
    truth = design[:, 0] * 3.0
    scores = explain.permutation_importance(
        _SumsFirstColumn(), design, truth, ["signal", "noise"], seed=CONFIG["seed"]
    )
    assert scores["signal"] > scores["noise"]
    assert scores["noise"] < 0.1


def test_batched_permutation_gives_the_same_answer_as_one_call_per_shuffle() -> None:
    """Batching is a speed device: same shuffles, same predictions, same importances."""
    rng = np.random.default_rng(3)
    design = rng.normal(size=(60, 3))
    truth = design[:, 0] * 2.0
    direct = explain.permutation_importance(
        _SumsFirstColumn(), design, truth, ["a", "b", "c"], seed=5
    )
    batched = explain.permutation_importance(
        _SumsFirstColumn(), design, truth, ["a", "b", "c"], seed=5, batch_rows=13
    )
    assert direct == batched


def test_stability_counts_how_often_a_feature_stays_in_the_top_k() -> None:
    per_fold = [
        {"duration": 1.0, "muscle": 0.5, "modality": 0.1},
        {"duration": 0.9, "muscle": 0.6, "modality": 0.2},
        {"muscle": 0.8, "duration": 0.7, "modality": 0.3},
        {"modality": 0.9, "duration": 0.4, "muscle": 0.2},
    ]
    table = explain.stability_table(per_fold, top_k=2)
    duration = table.loc[table["feature"] == "duration"].iloc[0]
    assert duration["folds_in_top_k"] == 4
    assert abs(duration["share"] - 1.0) < 1e-12
    modality = table.loc[table["feature"] == "modality"].iloc[0]
    assert modality["folds_in_top_k"] == 1


def test_shap_is_used_for_a_tree_model_and_named_honestly() -> None:
    """If the report says SHAP, SHAP must be what was computed."""
    if not explain.shap_available():
        return
    from sklearn.ensemble import RandomForestRegressor

    rng = np.random.default_rng(1)
    design = rng.normal(size=(120, 2))
    truth = design[:, 0] * 3.0
    model = RandomForestRegressor(n_estimators=40, random_state=0).fit(design, truth)
    scores, method = explain.importance(model, design, truth, ["signal", "noise"], CONFIG)
    assert method == "shap"
    assert scores["signal"] > scores["noise"]


def test_a_non_tree_model_falls_back_and_says_so() -> None:
    """SHAP on a kernel model is a different and far slower computation; do not pretend."""
    try:
        from sklearn.svm import SVR
    except ModuleNotFoundError:
        return
    rng = np.random.default_rng(2)
    design = rng.normal(size=(80, 2))
    truth = design[:, 0] * 2.0
    model = SVR().fit(design, truth)
    _, method = explain.importance(model, design, truth, ["signal", "noise"], CONFIG)
    assert method == "permutation_importance"


def test_the_method_actually_used_is_recorded() -> None:
    """A SHAP plot and a permutation plot are different claims and must not be confused."""
    report = explain.describe_method(CONFIG)
    assert report["requested"] == "shap"
    assert report["used"] in {"shap", "permutation_importance"}
    if not explain.shap_available():
        assert report["used"] == "permutation_importance"
        assert "requirements.txt" in report["note"]


def test_stability_table_is_sorted_by_how_often_a_feature_survives() -> None:
    per_fold = [{"a": 1.0, "b": 0.1}, {"a": 0.9, "b": 0.2}, {"b": 0.9, "a": 0.1}]
    table = explain.stability_table(per_fold, top_k=1)
    assert isinstance(table, pd.DataFrame)
    assert table.iloc[0]["feature"] == "a"


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
