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
  LLM (Claude / GPT-4o)
        ↓
  Chat Interface (React / HTML)
        ↓
       User
```
 
---
 
## Project Structure
 
```
Ergonomia/
├── README.md
├── EXPOSE.md           ← Project exposé (German)
├── PLAN.md             ← Full project plan with timeline
├── docs/
│   ├── user-research/  ← Personas, interviews, findings
│   ├── design/         ← Conversation flows, prompt design
│   └── evaluation/     ← SUS results, Amershi evaluation
├── scraper/            ← Website scraping scripts
├── rag/                ← Ingestion, embedding, retrieval
├── backend/            ← FastAPI server
├── frontend/           ← Chat UI
└── presentation/       ← Final slides
```
 
---
 
## Evaluation Framework
 
The chatbot is evaluated against:
- **Amershi et al. (2019)** — 18 Guidelines for Human-AI Interaction
- **Nielsen's 10 Usability Heuristics** — adapted for conversational UI
- **SUS (System Usability Scale)** — with 5 real user tests
- **DIN EN ISO 9241-110** — Interaction Principles
---
 
## Getting Started
 
```bash
# 1. Clone the repo
git clone https://github.com/your-username/Ergonomia.git
cd Ergonomia
 
# 2. Install dependencies
pip install -r requirements.txt
 
# 3. Scrape the website
python scraper/scrape.py
 
# 4. Ingest into vector database
python rag/ingest.py
 
# 5. Start the backend
uvicorn backend.main:app --reload
 
# 6. Open frontend/index.html in your browser
```
 
---
 
## Documentation
 
- [Exposé](./EXPOSE.md) — Project rationale and academic framing
- [Project Plan](./PLAN.md) — Full timeline, tasks, and evaluation protocols
- [User Research](./docs/user-research/) — Personas and interview findings
- [Design](./docs/design/) — Conversation flows and prompt strategy
- [Evaluation](./docs/evaluation/) — Test results and heuristic analysis
 
