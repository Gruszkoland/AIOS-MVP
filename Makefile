# ADRION 369 — System Control

.PHONY: test lint build docker-build run dev-db migrate-db

PYTHON := python
PIP := pip
VENV := .venv
PYTEST := $(VENV)/Scripts/pytest
RUFF := $(VENV)/Scripts/ruff

test:
	$(PYTEST) tests/test_oracle.py tests/test_quantum.py tests/test_database.py tests/test_mass_generator.py tests/test_smoke.py -v --cov=arbitrage

lint:
	$(RUFF) check arbitrage/

build:
	go build -v ./...

docker-build:
	docker compose -f docker-compose.prod.yml build

dev:
	$(PYTHON) -m arbitrage.main

install:
	$(PYTHON) -m pip install -r requirements-arbitrage.txt
	$(PYTHON) -m pip install pytest pytest-cov ruff
