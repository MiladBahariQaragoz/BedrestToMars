"""The post-hoc fifth family: TabPFN, scored exactly as the four tier-2 families were.

    python framework/run_tabpfn.py        # writes results/tabpfn_comparison.{csv,json}

TabPFN (Hollmann et al., Nature 2025) is a tabular foundation model fitted in-context off its
own pretraining, built for small-N regression. It was added on 19 September, after the
tier-2 null result was known, to answer the question that result invites: could a learner
pretrained on millions of datasets do what the four tuned families could not at 32 campaigns?

It is kept apart from `make models` on purpose. It was not declared before tier 2 ran, and
tabpfn 2.0.9 - the version whose checkpoint downloads without an interactive licence login -
needs scikit-learn below 1.7, so it runs in its own environment. Running it inside
`run_models.py` would either change the four families' numbers or mix two environments in one
file. Here it gets the same subset, the same leave-one-campaign-out folds and leakage
assertions, the same campaign-weighted scoring and bootstrap, and the same baseline, and
writes its own results file with its own provenance.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

import data_loader
import models
import run_baseline
import run_models

REPO_ROOT = Path(__file__).resolve().parent.parent
FAMILY = "tabpfn"
ADDED = "2026-09-19"


def _version(package: str) -> str:
    try:
        return str(__import__(package).__version__)
    except ModuleNotFoundError:
        return "absent"


def run(config: dict[str, Any] | None = None, subset: str = "A") -> dict[str, Any]:
    """TabPFN under leave-one-campaign-out, against the duration curve tier 2 was held to."""
    config = config or data_loader.load_config()
    frame = data_loader.subset(data_loader.load(config), config)

    baseline = run_baseline.run(config, subset=subset)
    form = baseline["best_form_by_out_of_cohort_mae"]
    baseline_mae = baseline["forms"][form]["mae"]

    entry = run_models.compare(FAMILY, frame, config, subset=subset, baseline_mae=baseline_mae)
    return {
        "baseline": {"form": form, "mae": baseline_mae},
        "models": {FAMILY: entry},
        "status": {
            "post_hoc": True,
            "added": ADDED,
            "note": "added after the tier-2 null result; fixed declared defaults, no tuning",
        },
        "provenance": {
            **baseline["provenance"],
            "sklearn": _version("sklearn"),
            "tabpfn": _version("tabpfn"),
            "torch": _version("torch"),
            "device": str(config["models"].get("tabpfn_device", "cpu")),
            "python": platform.python_version(),
        },
    }


def write(result: dict[str, Any], results_dir: Path) -> None:
    """Write the one-family table, laid out like `model_comparison.csv`, and the full record."""
    results_dir.mkdir(parents=True, exist_ok=True)
    run_models.table(result).to_csv(results_dir / "tabpfn_comparison.csv", index=False)
    (results_dir / "tabpfn_comparison.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )


def main() -> int:
    if not models.tabpfn_available():
        print("tabpfn is not installed here. Create a separate environment and run "
              "`pip install tabpfn==2.0.9` - see the optional section of requirements.txt.")
        return 1
    result = run()
    write(result, REPO_ROOT / "results")
    entry = result["models"][FAMILY]
    print(f"baseline: duration-only ({result['baseline']['form']}) {result['baseline']['mae']:.2f} pp")
    print(f"tabpfn:   {entry['mae']:.2f} pp (95% CI {entry['ci95']['low']:.2f} to "
          f"{entry['ci95']['high']:.2f}), {entry['relative_improvement']:+.1%} vs baseline, "
          f"pooled R2 {entry['r2_pooled']:.2f}, worst {entry['worst_fold']['cohort']} "
          f"({entry['worst_fold']['mae']:.2f} pp)")
    verdict = "beats" if entry["beats_baseline"] else "does not beat"
    print(f"tabpfn {verdict} the duration curve by the 15% agreed in PLAN.md section 8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
