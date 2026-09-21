# Every number and figure in the report is regenerated from the frozen dataset by `make all`.
# A number that cannot be regenerated cannot go on a slide (PLAN.md section 15).

PYTHON ?= python3

.PHONY: all test tier1 sensitivity baseline models forecast forecast-live ablation ablation-live figures venv clean help

help:
	@echo "make test      - run every test in framework/tests"
	@echo "make tier1     - fit the meta-regression, write results/tier1_*"
	@echo "make sensitivity - run the declared sensitivity analyses, write results/sensitivity.md"
	@echo "make baseline  - fit the duration-only baseline, write results/baseline.json"
	@echo "make models    - fit the four comparative families, write results/model_comparison.*"
	@echo "make forecast  - score the TypeSafe forecast from the answer cache, write results/forecast*"
	@echo "make forecast-live - as forecast, asking TypeSafe for any uncached answer (needs TYPESAFE_API_KEY)"
	@echo "make ablation  - score the tier-3 ablations and recognition probe from the cache"
	@echo "make ablation-live - as ablation, asking TypeSafe for any uncached answer"
	@echo "make figures   - draw F1-F5 from the results, write figures/*.svg and *.png"
	@echo "make venv      - create the virtual environment this project needs"
	@echo "make all       - regenerate every result from data/dataset_v1.1.csv"

test:
	$(PYTHON) framework/tests/run_all.py

# Tier 1 is the primary result and needs neither scikit-learn nor SHAP: a machine with
# numpy, pandas, scipy and PyYAML can reproduce every coefficient in the report.
tier1: results/tier1_curve.json

results/tier1_curve.json: data/dataset_v1.1.csv data/muscle_map.csv \
                          data/measurement_site_map.csv framework/config.yaml \
                          framework/run_tier1.py framework/tier1.py \
                          framework/features.py framework/data_loader.py
	$(PYTHON) framework/run_tier1.py

sensitivity: results/sensitivity.md

results/sensitivity.md: results/tier1_curve.json framework/sensitivity.py
	$(PYTHON) framework/sensitivity.py

baseline: results/baseline.json

results/baseline.json: data/dataset_v1.1.csv data/muscle_map.csv \
                       data/measurement_site_map.csv framework/config.yaml \
                       framework/run_baseline.py framework/models.py \
                       framework/features.py framework/data_loader.py framework/cv.py \
                       framework/evaluate.py
	$(PYTHON) framework/run_baseline.py

models: results/model_comparison.csv

results/model_comparison.csv: results/baseline.json framework/run_models.py \
                              framework/explain.py framework/models.py
	$(PYTHON) framework/run_models.py

# Tier 3 depends on a service outside the repository, so `make forecast` never calls it: every
# answer is read from results/forecast_cache/, keyed by a hash of the exact request. Filling the
# cache is a deliberate step, `make forecast-live`, and needs TYPESAFE_API_KEY (DESIGN.md 9.3).
FORECAST_DEPS = data/dataset_v1.1.csv data/muscle_map.csv data/measurement_site_map.csv \
                framework/config.yaml framework/run_forecast.py framework/forecast.py \
                framework/typesafe_client.py framework/features.py framework/data_loader.py \
                framework/models.py

forecast: results/forecast.json

results/forecast.json: $(FORECAST_DEPS)
	$(PYTHON) framework/run_forecast.py --offline

forecast-live: $(FORECAST_DEPS)
	$(PYTHON) framework/run_forecast.py

ablation: results/forecast_ablation.json

results/forecast_ablation.json: $(FORECAST_DEPS) framework/run_ablation.py
	$(PYTHON) framework/run_ablation.py --offline

ablation-live: $(FORECAST_DEPS) framework/run_ablation.py
	$(PYTHON) framework/run_ablation.py

# The five figures of PLAN.md section 9, drawn from the results files - never by hand.
figures: figures/F5_models.svg

figures/F5_models.svg: results/tier1_curve.json results/tier1_muscle_ranking.csv \
                       results/baseline.json results/model_comparison.csv \
                       results/forecast.json framework/plot_figures.py
	$(PYTHON) framework/plot_figures.py

# The environment cannot live in the Google Drive folder: the mount refuses the symlinks
# venv creates. It is recreated per machine instead, which is also the only thing that
# travels - a virtual environment carries absolute paths and compiled binaries.
VENV ?= $(HOME)/.venvs/dglrm

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "created $(VENV) - run the framework with PYTHON=$(VENV)/bin/python make all"

all: test tier1 sensitivity baseline models forecast ablation figures

clean:
	rm -f results/baseline.json results/model_comparison.csv results/model_comparison.json \
	      results/importance_stability.csv results/tier1_curve.json \
	      results/tier1_muscle_ranking.csv results/sensitivity.md \
	      results/forecast.json results/forecast_comparison.csv results/forecast_predictions.csv \
	      results/forecast_ablation.json results/forecast_ablation.csv results/forecast_recognition.csv \
	      results/forecast_ablation_campaigns.csv
	find framework -name '__pycache__' -type d -exec rm -rf {} +
