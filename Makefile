# SWAIF-MSG Makefile
.PHONY: help install install-dev test run-monitor run-pipe run-metrics run-display clean update-deps

help:
	@echo "SWAIF-MSG Commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install all dependencies (including dev)"
	@echo "  make test         - Run tests"
	@echo "  make run-monitor  - Start depths monitor"
	@echo "  make run-pipe     - Run depths pipeline"
	@echo "  make run-metrics  - Generate metrics"
	@echo "  make run-display  - Launch depths display"
	@echo "  make clean        - Clean cache files"
	@echo "  make update-deps  - Update requirements.txt"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 mypy pre-commit

test:
	pytest depths/tests/ -v --cov=depths

run-monitor:
	python depths/run_depths.py --monitor

run-pipe:
	python depths/run_depths.py --pipeline

run-metrics:
	python depths/run_depths.py --metrics

run-display:
	python depths/run_depths.py --display

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage

update-deps:
	pip freeze > requirements_current.txt
	@echo "Current dependencies saved to requirements_current.txt"
	@echo "Review and update requirements.txt manually"

# Desenvolvimento incremental
test-l1:
	pytest depths/tests/test_l1_ingestion.py -v

test-l2:
	pytest depths/tests/test_l2_grouping.py -v

test-l3:
	pytest depths/tests/test_l3_analysis.py -v

# Docker commands (surface layer)
docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down

docker-logs:
	cd docker && docker-compose logs -f

# Database commands
db-reset:
	rm -f data/swaif_msg.db
	python -c "from depths.core.database import SwaifDatabase; SwaifDatabase()"
	@echo "Database reset complete"

db-backup:
	cp data/swaif_msg.db data/backups/swaif_msg_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Database backed up"
