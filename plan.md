# Ergonomia — Projektplan
 
**Projekt:** Ergonomia — KI-Chatbot für das Immersive Reality Lab  
**Modul:** Software-Ergonomie (AIS-B-2-6.10)  
**Prüfungsform:** Projektbearbeitung mit Präsentation (15–45 Minuten)  
**Präsentationstermin:** 23.06.2026 oder 30.06.2026  
 
---
 
## Übersicht der Phasen
 
| Phase | Zeitraum | Inhalt |
|---|---|---|
| 0 — Setup | KW 18 (28.04) | Repo, Tools, Scraping-Test |
| 1 — User Research | KW 18–19 | Interviews, Personas, Anforderungen |
| 2 — Design | KW 20 | Gesprächsdesign, Flows, Prompt-Strategie |
| 3 — Build | KW 21–22 | RAG-Architektur, Vektordatenbank, UI |
| 4 — Evaluation | KW 23 | Nutzertests, SUS, Amershi-Evaluation |
| 5 — Präsentation | KW 24–26 | Slides, Feinschliff, Vortrag |
 
---
 
## Phase 0 — Projekt-Setup
**Zeitraum:** 28.04.2026 (KW 18)
 
### Ziele
- Repository `Ergonomia` anlegen
- Projektstruktur definieren
- Ersten Scraping-Test der Website durchführen
- Tech-Stack entscheiden
### Aufgaben
- [ ] GitHub Repo `Ergonomia` erstellen
- [ ] `README.md` und `EXPOSE.md` einchecken
- [ ] Ordnerstruktur anlegen (siehe unten)
- [ ] Scraping-Script schreiben (`/scraper/`)
- [ ] Alle Unterseiten von immersive-reality-lab.de inventarisieren
- [ ] Tech-Stack finalisieren
### Empfohlener Tech-Stack
```
Scraping:        Python + BeautifulSoup / Scrapy
Embeddings:      OpenAI text-embedding-3-small  ODER  sentence-transformers (lokal)
Vektordatenbank: ChromaDB (lokal, einfach) ODER Qdrant (Docker)
LLM:             Claude claude-sonnet-4-20250514 via Anthropic API  ODER  GPT-4o
Backend:         Python + FastAPI
Frontend:        React (Vite) ODER einfaches HTML/JS
```
 
### Empfohlene Ordnerstruktur
```
Ergonomia/
├── README.md
├── EXPOSE.md
├── PLAN.md
├── docs/
│   ├── user-research/
│   │   ├── interview-guide.md
│   │   ├── personas.md
│   │   └── findings.md
│   ├── design/
│   │   ├── conversation-flows.md
│   │   ├── prompt-design.md
│   │   └── ui-mockups/
│   └── evaluation/
│       ├── sus-results.md
│       ├── amershi-evaluation.md
│       └── usability-test-protocol.md
├── scraper/
│   ├── scrape.py
│   └── data/          ← gescrapte Rohdaten (JSON)
├── rag/
│   ├── ingest.py      ← Chunking + Embedding + DB-Import
│   ├── retriever.py   ← Semantic Search
│   └── vectordb/      ← ChromaDB-Daten (gitignore)
├── backend/
│   ├── main.py        ← FastAPI Server
│   └── chat.py        ← RAG + LLM Pipeline
├── frontend/
│   ├── index.html
│   └── chat.js
└── presentation/
    └── ergonomia-slides.pptx
```
 
---
 
## Phase 1 — User Research
**Zeitraum:** 28.04. – 09.05.2026 (KW 18–19)
 
> Dieser Teil ist der akademische Kern des Projekts aus Sicht der Software-Ergonomie.
> Ohne User Research gibt es keine Grundlage für Designentscheidungen.
 
### Ziele
- Verstehen, wer den Chatbot nutzen wird
- Verstehen, welche Fragen diese Nutzer haben
- Verstehen, was an der aktuellen Website frustriert
### Aufgaben
 
#### Nutzergruppen identifizieren
Mindestens 3 Personas definieren:
 
| Persona | Beschreibung |
|---|---|
| **Studierende/r** | Sucht nach Themen für Bachelorarbeit, Geräteausleihe, Lehrveranstaltungen |
| **Forschungsinteressierte/r** | Will Publikationen finden, Kooperationsmöglichkeiten erkunden |
| **Industriepartner** | Fragt nach konkreten Projekten, Transfer, Kontaktpersonen |
 
#### Mini-Interview durchführen
- 5–8 Personen befragen (Kommilitonen reichen!)
- Leitfaden (in `/docs/user-research/interview-guide.md`):
  1. "Was weißt du über das Immersive Reality Lab?"
  2. "Wenn du die Website besuchen würdest, was würdest du als erstes suchen?"
  3. "Was würde dich beim Suchen auf der Website frustrieren?"
  4. "Würdest du lieber suchen/klicken oder eine Frage stellen?"
#### Ergebnisse dokumentieren
- Top 10 häufigste Fragen/Informationsbedürfnisse → direkt Input für RAG-Inhalte
- Personas ausformulieren (`/docs/user-research/personas.md`)
- Findings zusammenfassen (`/docs/user-research/findings.md`)
---
 
## Phase 2 — Design
**Zeitraum:** 11.05. – 16.05.2026 (KW 20)**
 
### Ziele
- Gesprächsdesign auf Basis der User Research entwickeln
- Festlegen, welche Inhalte der Chatbot abdecken muss
- Prompt-Strategie definieren
### Aufgaben
 
#### Inhaltsumfang definieren (Information Architecture)
Was soll der Chatbot wissen? Priorisierte Liste:
- [ ] Alle Projekte (INFUSE, XRT-HuFuSa, ITT, XRwise, SilentBedMonitor, ARiadne, ...)
- [ ] Publikationen (Titel, Autoren, Abstract)
- [ ] Lehrangebote und Kurse
- [ ] Geräteausleihe (Bedingungen, verfügbare Geräte)
- [ ] Team / Kontakt
- [ ] Core Research Topics (XR, Digital Health, Biosensors)
#### Conversation Flow Design (`/docs/design/conversation-flows.md`)
Für jede Persona einen typischen Gesprächsverlauf skizzieren:
 
```
Beispiel: Studierende/r
User:  "Kann ich für meine Bachelorarbeit im Lab arbeiten?"
Bot:   "Ja! Das Lab bietet Themen in den Bereichen VR/AR, UX-Studien
        und Interaction Design. Du kannst auch Geräte wie VR-Headsets
        oder Biosensoren ausleihen. Soll ich dir mehr zu einem
        bestimmten Bereich zeigen?"
```
 
#### Ergonomische Designprinzipien für den Chatbot
Dokumentieren, welche Prinzipien angewendet werden:
 
- **DIN EN ISO 9241-110 — Aufgabenangemessenheit:** Antworten sind kurz und auf den Punkt
- **Fehlertoleranz:** Bei unbekannten Fragen klare Rückmeldung + Alternativangebot
- **Selbstbeschreibungsfähigkeit:** Der Chatbot erklärt beim Start, was er kann
- **Steuerbarkeit:** Nutzer kann Thema jederzeit wechseln
#### Prompt Design (`/docs/design/prompt-design.md`)
System-Prompt Vorlage:
```
Du bist Ergonomia, der offizielle Chatbot des Immersive Reality Lab
an der Hochschule Hamm-Lippstadt. Du beantwortest Fragen ausschließlich
auf Basis der folgenden Kontextinformationen aus der Lab-Website.
Antworte präzise, freundlich und auf Deutsch (oder der Sprache des Nutzers).
Wenn du eine Frage nicht beantworten kannst, sage es klar und verweise
auf die Website oder den direkten Kontakt.
 
Kontext:
{retrieved_chunks}
 
Frage: {user_question}
```
 
---
 
## Phase 3 — Build
**Zeitraum:** 18.05. – 30.05.2026 (KW 21–22)**
 
### Schritt 1: Scraping (`/scraper/scrape.py`)
- Alle Unterseiten scrapen: Homepage, Projects, Publications, Teaching, Methods, Team
- Output: JSON-Dateien pro Seite mit `{url, title, content, date_scraped}`
- Zu scrapen:
  - https://immersive-reality-lab.de
  - https://immersive-reality-lab.de/pages/projects-overview.html
  - https://immersive-reality-lab.de/pages/publications.html
  - https://immersive-reality-lab.de/pages/teaching.html
  - https://immersive-reality-lab.de/pages/methods-infrastructure.html
  - https://immersive-reality-lab.de/pages/core-topic-xr.html
  - https://immersive-reality-lab.de/pages/core-topic-ass-tech.html
  - https://immersive-reality-lab.de/pages/core-topic-biosensors.html
  - Alle einzelnen Projektseiten (projects.html?id=...)
  - Alle einzelnen Publikationsseiten (publicationDetail/?id=...)
### Schritt 2: Ingest (`/rag/ingest.py`)
- Text in Chunks aufteilen (empfohlen: 300–500 Token, 50 Token Overlap)
- Embeddings generieren
- In ChromaDB importieren mit Metadaten: `{source_url, page_title, chunk_id}`
### Schritt 3: Retriever (`/rag/retriever.py`)
- Funktion: `retrieve(query, top_k=5)` → gibt relevanteste Chunks zurück
- Semantic similarity search über ChromaDB
### Schritt 4: Backend (`/backend/main.py`)
```python
POST /chat
Body: { "message": "...", "history": [...] }
Response: { "reply": "..." }
```
 
### Schritt 5: Frontend (`/frontend/`)
- Minimales, sauberes Chat-Interface
- Wichtige ergonomische UI-Elemente:
  - [ ] Onboarding-Nachricht ("Ich bin Ergonomia, ich beantworte Fragen zum IRL...")
  - [ ] Vorgeschlagene Einstiegsfragen (Chips/Buttons)
  - [ ] Klare Fehlermeldung wenn keine Antwort gefunden
  - [ ] Ladeindikator während der Antwort generiert wird
  - [ ] Gesprächsverlauf scrollbar
---
 
## Phase 4 — Evaluation
**Zeitraum:** 02.06. – 14.06.2026 (KW 23–24)**
 
> Das ist der zweite akademische Kernpunkt. Ohne Evaluation ist es kein UX-Projekt.
 
### Nutzertests (5 Personen)
 
**Testprotokoll** (`/docs/evaluation/usability-test-protocol.md`):
1. Kurze Einführung (kein Erklären der Funktionen!)
2. 3–4 Aufgaben stellen:
   - "Finde heraus, welche VR-Projekte das Lab gerade betreibt"
   - "Kannst du herausfinden, ob du als Student Geräte ausleihen kannst?"
   - "Finde eine Publikation zum Thema EEG oder Biosensoren"
3. Think-Aloud Protokoll
4. SUS-Fragebogen danach ausfüllen lassen
### SUS-Auswertung (`/docs/evaluation/sus-results.md`)
- 10-Item Fragebogen, Score 0–100
- Benchmark: Score > 68 = überdurchschnittlich
### Amershi et al. 2019 Evaluation (`/docs/evaluation/amershi-evaluation.md`)
Bewertung des Chatbots gegen die 18 Guidelines for Human-AI Interaction:
 
| # | Guideline | Erfüllt? | Befund |
|---|---|---|---|
| G1 | Make clear what the system can do | ✅/⚠️/❌ | ... |
| G2 | Make clear how well the system can do what it can do | | |
| G3 | Time services based on context | | |
| G4 | Show contextually relevant information | | |
| G5 | Match relevant social norms | | |
| G6 | Mitigate social biases | | |
| G7 | Support efficient invocation | | |
| G8 | Support efficient dismissal | | |
| G9 | Support efficient correction | | |
| G10 | Scope services when in doubt | | |
| G11 | Make clear why the system did what it did | | |
| G12 | Remember recent interactions | | |
| G13 | Learn from user behavior | | |
| G14 | Update and adapt cautiously | | |
| G15 | Encourage granular feedback | | |
| G16 | Convey consequences of user actions | | |
| G17 | Provide global controls | | |
| G18 | Notify users about changes | | |
 
### Nielsen Heuristiken (adaptiert für Conversational UI)
| Heuristik | Anwendung auf Chatbot |
|---|---|
| #1 Visibility of system status | Ladeindikator, "Ich suche..." |
| #2 Match real world | Natürliche Sprache, kein Tech-Jargon |
| #4 Consistency | Einheitlicher Ton, Antwortformat |
| #5 Error prevention | Scope-Begrenzung durch RAG |
| #9 Help users recognize errors | Klare Fallback-Nachrichten |
 
---
 
## Phase 5 — Präsentation
**Zeitraum:** 16.06. – 23.06.2026 (KW 25–26)**
 
### Präsentationsstruktur (30 Minuten)
 
| Block | Zeit | Inhalt |
|---|---|---|
| Intro | 3 min | Problemstellung, Ziel, Projektname |
| User Research | 5 min | Personas, Interview-Findings, Top-Fragen |
| Design | 7 min | Conversation Flows, Designprinzipien, Architektur |
| Demo | 5 min | Live-Demo des Chatbots |
| Evaluation | 7 min | SUS-Ergebnisse, Amershi-Bewertung, Nutzerfeedback |
| Fazit | 3 min | Lessons Learned, Ausblick |
 
### Kernargument für die Präsentation
> *"Ergonomia ist kein Chatbot-Projekt mit UX-Verpackung — es ist ein UX-Projekt,
> das einen Chatbot als Interaktionsmedium nutzt. Jede Entscheidung im System,
> von der Chunk-Größe bis zum Fallback-Text, ist eine ergonomische Designentscheidung
> im Sinne der DIN EN ISO 9241 und der Amershi-Guidelines."*
 
---
 
## Literatur (direkt aus Modulliteratur)
 
- Amershi, S. et al. (2019): *Guidelines for Human-AI Interaction.* CHI 2019. → **Primärer Evaluationsrahmen**
- Nielsen, J. (1994): *10 Usability Heuristics for User Interface Design.* → **Adaptiert für Conversational UI**
- DIN EN ISO 9241-110: *Interaktionsprinzipien* → **Gestaltungsprinzipien**
- Richter, M. & Flückiger, M. (2016): *Usability und UX kompakt.* Springer. → **Methodengrundlage**
- Tullis, T. & Albert, B. (2008): *Measuring the User Experience.* → **SUS-Methodik**
---
 
## Risiken & Gegenmaßnahmen
 
| Risiko | Gegenmaßnahme |
|---|---|
| API-Kosten zu hoch | Lokales Modell (Ollama + Llama 3) als Fallback |
| Website-Scraping blockiert | Statisches HTML manuell exportieren |
| Zu wenig Testpersonen | Kommilitonen, WG-Mitbewohner, Familie reichen für 5 Tests |
| Technische Probleme bei Demo | Video-Recording als Backup |
| Zeitdruck | Phase 3 (Build) ist der flexibelste Block — Scope reduzieren wenn nötig |
 
---
 
*Letzte Aktualisierung: April 2026*
 