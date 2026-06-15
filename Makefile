.PHONY: setup ingest api frontend test lint report slides

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

report:
	cd report && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex

slides:
	cd report && pdflatex -interaction=nonstopmode presentation.tex && pdflatex -interaction=nonstopmode presentation.tex
