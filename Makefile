.PHONY: setup ingest api frontend test lint

setup:
	pip install -r requirements.txt
	cp .env.example .env

ingest:
	python scripts/crawl_and_ingest.py

api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001

frontend:
	cd frontend && npm install && npm run dev

test:
	pytest

lint:
	ruff check .
