# Ergonomia 

> An ergonomically designed AI chatbot for the Immersive Reality Lab at Hamm-Lippstadt University of Applied Sciences.

**Module:** Software-Ergonomie (AIS-B-2-6.10)  
**Professor:** Prof. Dr.-Ing. Jan-Niklas Voigt-Antons  
**Target:** [immersive-reality-lab.de](https://immersive-reality-lab.de)

---

## What is Ergonomia?

Ergonomia is a RAG-based (Retrieval-Augmented Generation) chatbot that lets users ask questions about the Immersive Reality Lab in natural language — and get answers grounded in the lab's actual website content.

It is designed as a **software ergonomics project**: every architectural decision (what to scrape, how to chunk, how to respond, how to handle errors) is treated as a UX and ergonomic design decision evaluated against established frameworks (Amershi et al. 2019, Nielsen's Heuristics, DIN EN ISO 9241-110).

---

## Architecture

```
Website (immersive-reality-lab.de)
        ↓  Scraping (Python + BeautifulSoup)
  Raw content (JSON)
        ↓  Chunking + Embedding
  Vector Database (ChromaDB)
        ↓  Semantic Search (RAG)
  LLM (Ollama + Qwen 2.5)
        ↓
  Chat Interface (Next.js)
        ↓
       User
```

---

## Project Structure

```
Ergonomia/
├── README.md
├── EXPOSE.md              ← Project exposé (German)
├── PLAN.md                ← Full project plan with timeline
├── Makefile               ← Build automation
├── run.sh                 ← Launch script (API + frontend)
├── requirements.txt       ← Python dependencies
├── .env.example           ← Configuration template
├── src/                   ← Python source code
│   ├── config.py          ← Central settings (pydantic-settings)
│   ├── api/               ← FastAPI server
│   ├── chat/              ← SQLite chat history
│   ├── ingestion/         ← Crawling, chunking, embedding
│   ├── llm/               ← Ollama client
│   ├── rag/               ← RAG pipeline, query analysis
│   └── vectorstore/       ← ChromaDB wrapper
├── scripts/               ← CLI entry points
│   └── crawl_and_ingest.py
├── frontend/              ← Next.js 15 chat UI
├── docs/                  ← Project documentation
│   ├── user-research/     ← Personas, interviews, findings
│   ├── design/            ← Conversation flows, prompt design
│   └── evaluation/        ← SUS results, Amershi evaluation
├── report/                ← LaTeX project report + presentation
│   ├── main.tex           ← Report (10 pages)
│   ├── presentation.tex   ← Beamer slides (12 slides)
│   └── chapters/          ← Individual report chapters
└── data/                  ← Scraped data + vector store
```

---

## Quick Start

```bash
# 1. Install Python dependencies
make setup

# 2. Scrape the website and ingest into vector DB
make ingest

# 3. Start the API + frontend
./run.sh
```

Or manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

---

## Build LaTeX Documents

```bash
make report    # Project report (PDF)
make slides    # Presentation slides (PDF)
```

---

## Makefile Targets

| Target     | Description                        |
|------------|------------------------------------|
| `setup`    | Install Python deps + copy .env    |
| `ingest`   | Crawl website + populate ChromaDB  |
| `api`      | Start FastAPI server               |
| `frontend` | Start Next.js dev server           |
| `test`     | Run pytest (WIP)                   |
| `lint`     | Run ruff linter                    |
| `report`   | Build LaTeX project report (PDF)   |
| `slides`   | Build Beamer presentation (PDF)    |

---

## Evaluation Framework

The chatbot is evaluated against:
- **Amershi et al. (2019)** — 18 Guidelines for Human-AI Interaction
- **Nielsen's 10 Usability Heuristics** — adapted for conversational UI
- **SUS (System Usability Scale)** — 5 real user tests (Score: 73.5)
- **DIN EN ISO 9241-110** — Interaction Principles

---

## Documentation

- [Exposé](./EXPOSE.md) — Project rationale and academic framing
- [Project Plan](./PLAN.md) — Full timeline, tasks, and evaluation protocols
- [User Research](./docs/user-research/) — Personas and interview findings
- [Design](./docs/design/) — Conversation flows and prompt strategy
- [Evaluation](./docs/evaluation/) — Test results and heuristic analysis
- [Report](./report/main.pdf) — Final project report (PDF)
- [Presentation](./report/presentation.pdf) — Final presentation slides (PDF)
