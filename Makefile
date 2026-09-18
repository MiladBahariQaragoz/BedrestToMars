# Every number and figure in the report is regenerated from the frozen dataset by `make all`.
# A number that cannot be regenerated cannot go on a slide (PLAN.md section 15).

PYTHON ?= python3

.PHONY: all test baseline clean help

help:
	@echo "make test      - run every test in framework/tests"
	@echo "make baseline  - fit the duration-only baseline, write results/baseline.json"
	@echo "make all       - regenerate every result from data/dataset_v1.0.csv"

test:
	$(PYTHON) framework/tests/run_all.py

baseline: results/baseline.json

results/baseline.json: data/dataset_v1.0.csv data/muscle_map.csv \
                       data/measurement_site_map.csv framework/config.yaml \
                       framework/run_baseline.py framework/models.py \
                       framework/features.py framework/data_loader.py framework/cv.py \
                       framework/evaluate.py
	$(PYTHON) framework/run_baseline.py

all: test baseline

clean:
	rm -f results/baseline.json
	find framework -name '__pycache__' -type d -exec rm -rf {} +
