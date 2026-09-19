"""What the model leaned on, and whether it leaned on the same thing every fold.

`DESIGN.md` section 11 sets the two constraints this module exists to enforce. Importance is
recomputed inside every fold and reported as a stability table first and a magnitude second,
because at 31 campaigns a ranking that changes from fold to fold is the finding. And nothing
here is causal: a feature the model used is not a cause of atrophy, it is a feature the model
used.

SHAP is the requested method. When it is not installed the module falls back to permutation
importance and says so in the output, because the two are different claims and a figure must
never imply the one it did not compute.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

import numpy as np
import pandas as pd


def shap_available() -> bool:
    try:
        import shap  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def describe_method(config: dict[str, Any], used: str | None = None) -> dict[str, str]:
    """What was asked for, what was actually computed, and why they differ."""
    requested = config["explain"]["method"]
    if used is None:
        used = requested if (requested != "shap" or shap_available()) else "permutation_importance"
    if used == requested:
        return {"requested": requested, "used": used, "note": ""}
    if requested == "shap" and not shap_available():
        note = (
            "shap is not installed, so importance is permutation-based. Install the "
            "optional stack with `pip install -r requirements.txt` to compute SHAP values. "
            "Do not label a permutation plot as SHAP."
        )
    else:
        note = (
            "SHAP was computed where the model allows it cheaply - the tree ensembles - and "
            "permutation importance elsewhere. A kernel model needs a sampling explainer, "
            "which is a different and much slower computation, and the two must not be "
            "presented under one label."
        )
    return {"requested": requested, "used": used, "note": note}


def _is_tree_ensemble(model: Any) -> bool:
    """Tree ensembles have an exact, fast SHAP explainer; other models do not."""
    try:
        from sklearn.ensemble import (
            ExtraTreesRegressor,
            GradientBoostingRegressor,
            RandomForestRegressor,
        )
        from sklearn.tree import DecisionTreeRegressor
    except ModuleNotFoundError:
        return False
    return isinstance(
        model,
        (
            RandomForestRegressor,
            GradientBoostingRegressor,
            ExtraTreesRegressor,
            DecisionTreeRegressor,
        ),
    )


def shap_importance(
    model: Any, design: np.ndarray, feature_names: Sequence[str]
) -> dict[str, float]:
    """Mean absolute SHAP value per feature, in percentage points of muscle change."""
    import shap

    explainer = shap.TreeExplainer(model)
    values = np.asarray(explainer.shap_values(np.asarray(design, dtype=float)))
    magnitude = np.abs(values).mean(axis=0)
    return {name: float(magnitude[index]) for index, name in enumerate(feature_names)}


def importance(
    model: Any,
    design: np.ndarray,
    truth: np.ndarray,
    feature_names: Sequence[str],
    config: dict[str, Any],
) -> tuple[dict[str, float], str]:
    """Importance for one fitted model, and the name of the method that produced it."""
    if config["explain"]["method"] == "shap" and shap_available() and _is_tree_ensemble(model):
        return shap_importance(model, design, feature_names), "shap"
    return (
        permutation_importance(
            model, design, truth, feature_names, seed=int(config["seed"])
        ),
        "permutation_importance",
    )


def permutation_importance(
    model: Any,
    design: np.ndarray,
    truth: np.ndarray,
    feature_names: Sequence[str],
    seed: int = 0,
    repeats: int = 10,
    score: Callable[[np.ndarray, np.ndarray], float] | None = None,
    batch_rows: int = 65536,
) -> dict[str, float]:
    """How much worse the predictions get when one feature is shuffled.

    Reported as the increase in mean absolute error, in percentage points of muscle change,
    so the number means something on its own rather than only in a ranking.

    The shuffled designs are scored in batches rather than one `predict` call each: every
    family in this framework predicts a row independently of the rows around it, so one call
    over stacked rows is the same computation as many calls - and for the prior-fitted
    family, whose per-call overhead is seconds on CPU, it is the difference between minutes
    and hours.
    """
    design = np.asarray(design, dtype=float)
    truth = np.asarray(truth, dtype=float)
    score = score or (lambda a, b: float(np.mean(np.abs(a - b))))
    rng = np.random.default_rng(seed)

    reference = score(truth, model.predict(design))

    shuffled: list[np.ndarray] = []
    for column in range(design.shape[1]):
        for _ in range(repeats):
            copy = design.copy()
            copy[:, column] = rng.permutation(copy[:, column])
            shuffled.append(copy)

    rows = design.shape[0]
    per_call = max(1, batch_rows // rows) if rows else 1
    predictions: list[np.ndarray] = []
    for start in range(0, len(shuffled), per_call):
        stacked = np.vstack(shuffled[start : start + per_call])
        batch = np.asarray(model.predict(stacked), dtype=float).reshape(len(shuffled[start : start + per_call]), rows)
        predictions.extend(batch)

    importances: dict[str, float] = {}
    index = 0
    for name in feature_names:
        losses = [score(truth, predictions[index + r]) - reference for r in range(repeats)]
        index += repeats
        importances[name] = float(np.mean(losses))
    return importances


def stability_table(
    per_fold: Iterable[dict[str, float]], top_k: int = 3
) -> pd.DataFrame:
    """How often each feature reached the top `k` across folds.

    This table, not the average importance, is what may be shown when the ranking moves.
    """
    folds = list(per_fold)
    counts: dict[str, int] = {}
    for scores in folds:
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        for name, _ in ranked[:top_k]:
            counts[name] = counts.get(name, 0) + 1

    mean_importance = {
        name: float(np.mean([scores.get(name, np.nan) for scores in folds]))
        for name in {name for scores in folds for name in scores}
    }
    rows = [
        {
            "feature": name,
            "folds_in_top_k": counts.get(name, 0),
            "share": counts.get(name, 0) / len(folds),
            "mean_importance": mean_importance[name],
        }
        for name in mean_importance
    ]
    table = pd.DataFrame(rows)
    return table.sort_values(
        ["folds_in_top_k", "mean_importance"], ascending=False
    ).reset_index(drop=True)


def explain_folds(
    model_factory: Callable[[], Any],
    design: np.ndarray,
    truth: np.ndarray,
    folds: Iterable[tuple[np.ndarray, np.ndarray]],
    feature_names: Sequence[str],
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Refit inside every fold and return the stability table with the method used."""
    per_fold: list[dict[str, float]] = []
    used: set[str] = set()
    for train, test in folds:
        model = model_factory()
        model.fit(design[train], truth[train])
        scores, method_used = importance(
            model, design[test], truth[test], feature_names, config
        )
        per_fold.append(scores)
        used.add(method_used)
    table = stability_table(per_fold, top_k=int(config["explain"]["stability_top_k"]))
    return table, describe_method(config, used="+".join(sorted(used)))
