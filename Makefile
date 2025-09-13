# SWAIF-MSG Makefile
.PHONY: help install install-dev test clean update-deps run-monitor run-pipe run-metrics

help:
	@echo "SWAIF-MSG Commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install all dependencies (including dev)"
	@echo "  make test        - Run tests"
	@echo "  make coverage    - Run tests with coverage report"
	@echo "  make run-monitor - Start L1 monitor"
	@echo "  make run-pipe    - Run full pipeline (L1 -> L2)"
	@echo "  make run-metrics - Show all metrics"
	@echo "  make clean       - Clean cache files"
	@echo "  make update-deps - Update requirements.txt"
	@echo "  make lint        - Run flake8 linter"
	@echo "  make fmt         - Run black formatter"
	@echo "  make typecheck   - Run mypy type checker"
	@echo "  make pre-commit-install - Install git hooks"
	@echo "  make pre-commit-run     - Run all pre-commit hooks"
	@echo "  make test-e2e    - Run end-to-end pipeline test"
	@echo "  make test-l2-additional - Run additional L2 tests"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 mypy pre-commit

test:
	pytest depths/tests/ -v --cov=depths

coverage:
	pytest depths/tests/ -v --cov=depths --cov-report=term-missing

run-monitor:
	python depths/run_depths.py --monitor

run-pipe:
	python depths/run_depths.py --pipeline

run-metrics:
	python depths/run_depths.py --metrics

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
	pytest depths/tests/test_l3_ai.py -v

test-l2-additional:
	pytest depths/tests/test_l2_additional.py -v

test-e2e:
	pytest depths/tests/test_end_to_end.py -v

lint:
	flake8 depths

fmt:
	black depths

typecheck:
	mypy depths

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

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
