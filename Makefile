PY := $(CURDIR)/.venv/bin/python

.PHONY: venv install dev test lint infra-up infra-down

venv:
	python3 -m venv .venv

install:
	$(PY) -m pip install -r backend/requirements.txt

dev:
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000

test:
	cd backend && $(PY) -m pytest

lint:
	cd backend && $(PY) -m ruff check .

infra-up:
	docker compose up -d

infra-down:
	docker compose down
