# Every number and figure in the report is regenerated from the frozen dataset by `make all`.
# A number that cannot be regenerated cannot go on a slide (PLAN.md section 15).

PYTHON ?= python3

.PHONY: all test tier1 sensitivity baseline models venv clean help

help:
	@echo "make test      - run every test in framework/tests"
	@echo "make tier1     - fit the meta-regression, write results/tier1_*"
	@echo "make sensitivity - run the declared sensitivity analyses, write results/sensitivity.md"
	@echo "make baseline  - fit the duration-only baseline, write results/baseline.json"
	@echo "make models    - fit the four comparative families, write results/model_comparison.*"
	@echo "make venv      - create the virtual environment this project needs"
	@echo "make all       - regenerate every result from data/dataset_v1.0.csv"

test:
	$(PYTHON) framework/tests/run_all.py

# Tier 1 is the primary result and needs neither scikit-learn nor SHAP: a machine with
# numpy, pandas, scipy and PyYAML can reproduce every coefficient in the report.
tier1: results/tier1_curve.json

results/tier1_curve.json: data/dataset_v1.0.csv data/muscle_map.csv \
                          data/measurement_site_map.csv framework/config.yaml \
                          framework/run_tier1.py framework/tier1.py \
                          framework/features.py framework/data_loader.py
	$(PYTHON) framework/run_tier1.py

sensitivity: results/sensitivity.md

results/sensitivity.md: results/tier1_curve.json framework/sensitivity.py
	$(PYTHON) framework/sensitivity.py

baseline: results/baseline.json

results/baseline.json: data/dataset_v1.0.csv data/muscle_map.csv \
                       data/measurement_site_map.csv framework/config.yaml \
                       framework/run_baseline.py framework/models.py \
                       framework/features.py framework/data_loader.py framework/cv.py \
                       framework/evaluate.py
	$(PYTHON) framework/run_baseline.py

models: results/model_comparison.csv

results/model_comparison.csv: results/baseline.json framework/run_models.py \
                              framework/explain.py framework/models.py
	$(PYTHON) framework/run_models.py

# The environment cannot live in the Google Drive folder: the mount refuses the symlinks
# venv creates. It is recreated per machine instead, which is also the only thing that
# travels - a virtual environment carries absolute paths and compiled binaries.
VENV ?= $(HOME)/.venvs/dglrm

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "created $(VENV) - run the framework with PYTHON=$(VENV)/bin/python make all"

all: test tier1 sensitivity baseline models

clean:
	rm -f results/baseline.json results/model_comparison.csv results/model_comparison.json \
	      results/importance_stability.csv results/tier1_curve.json \
	      results/tier1_muscle_ranking.csv results/sensitivity.md
	find framework -name '__pycache__' -type d -exec rm -rf {} +
