PY := $(CURDIR)/.venv/bin/python

.PHONY: venv install dev test lint infra-up infra-down frontend-install frontend-dev frontend-check

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

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-check:
	cd frontend && npm run lint && npm run typecheck && npm run build
