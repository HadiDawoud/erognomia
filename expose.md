# Ergonomia — Exposé
 
**Projekt:** Ergonomia  
**Modul:** Software-Ergonomie (AIS-B-2-6.10)  
**Modulverantwortlicher:** Prof. Dr.-Ing. Jan-Niklas Voigt-Antons  
**Hochschule:** Hamm-Lippstadt University of Applied Sciences  
**Studiengang:** Angewandte Informatik und Soziale Medien  
 
---
 
## 1. Problemstellung
 
Das Immersive Reality Lab (immersive-reality-lab.de) betreibt Forschung in den Bereichen Extended Reality (XR), Digital Health und psychophysiologische Qualitätsmessung. Die Website richtet sich an ein heterogenes Publikum: Studierende, Forschende, Industriepartner und Interessierte. Die aktuelle Informationsarchitektur erfordert es, dass Nutzer aktiv durch mehrere Unterseiten navigieren, um relevante Informationen zu Projekten, Publikationen, Lehrangeboten und Geräteausleihe zu finden.
 
Aus Sicht der Software-Ergonomie entstehen dabei mehrere Probleme:
 
- **Erhöhter kognitiver Aufwand** durch tiefe Navigationsstrukturen
- **Fehlende Direktheit** — Nutzer mit konkreten Fragen müssen selbst suchen
- **Kein adaptives Verhalten** — die Website antwortet nicht auf den individuellen Informationsbedarf
---
 
## 2. Projektziel
 
Ziel des Projekts **Ergonomia** ist die Konzeption, der Aufbau und die Evaluation eines **ergonomisch gestalteten KI-Chatbots** für das Immersive Reality Lab. Der Chatbot ermöglicht es Nutzern, in natürlicher Sprache Fragen zur Forschung, den Projekten, Publikationen, Lehrveranstaltungen und der Geräteausleihe des Labs zu stellen und direkte, kontextbezogene Antworten zu erhalten.
 
Der Chatbot basiert auf einer **RAG-Architektur (Retrieval-Augmented Generation)**: Inhalte der Website werden gescrapt, in eine Vektordatenbank überführt und zur Laufzeit als Kontext an ein Large Language Model (LLM) übergeben. Dadurch sind alle Antworten faktisch an die tatsächlichen Inhalte des Labs gebunden — Halluzinationen werden minimiert, Vertrauen und Zuverlässigkeit maximiert.
 
---
 
## 3. Relevanz für die Software-Ergonomie
 
Das Projekt adressiert zentrale Themen des Moduls:
 
| Modulthema | Umsetzung im Projekt |
|---|---|
| Usability & User Experience | Der Chatbot wird nach UX-Prinzipien gestaltet und mit echten Nutzern evaluiert |
| Gestaltungsprinzipien / DIN EN ISO 9241 | Gesprächsdesign folgt Interaktionsprinzipien (Aufgabenangemessenheit, Fehlertoleranz) |
| Menschliche Informationsverarbeitung | Reduktion kognitiver Last durch natürlichsprachliche Interaktion |
| Evaluation von Benutzerschnittstellen | Nutzerstudie mit SUS-Fragebogen, Amershi-Guidelines |
| Human-AI Interaction | Direkter Anwendungsfall; Amershi et al. 2019 als Evaluationsrahmen |
| User Research | Nutzerinterviews und Personas als Grundlage der Designentscheidungen |
 
Der Chatbot ist selbst ein **Benutzerschnittstellen-Designprojekt** — jede technische Entscheidung (welche Daten werden eingebunden, wie werden Fehler kommuniziert, welcher Ton wird gewählt) ist gleichzeitig eine ergonomische Designentscheidung.
 
---
 
## 4. Theoretischer Rahmen
 
Die Evaluation des Chatbots stützt sich auf zwei zentrale Referenzen aus der Modulliteratur:
 
- **Amershi et al. (2019):** *Guidelines for Human-AI Interaction* — 18 Richtlinien für die Gestaltung von KI-Schnittstellen, direkt anwendbar auf das Konversationsdesign
- **Nielsen (1994):** *10 Usability Heuristics* — adaptiert für konversationelle Benutzeroberflächen
Ergänzend wird **DIN EN ISO 9241-110** (Interaktionsprinzipien) als Bewertungsgrundlage herangezogen.
 
---
 
## 5. Technischer Ansatz (im Dienst der Ergonomie)
 
```
Website (immersive-reality-lab.de)
        ↓  Scraping
  Rohdaten (Text, Metadaten)
        ↓  Chunking + Embedding
  Vektordatenbank (z.B. ChromaDB / Qdrant)
        ↓  Semantic Search (RAG)
  LLM (z.B. Claude / GPT-4o)
        ↓
  Chatbot-Interface (Web-UI)
        ↓
       Nutzer
```
 
Jede Schicht dieser Architektur hat eine ergonomische Funktion:
 
- **Scraping & Chunking:** Informationsarchitektur — was soll auffindbar sein?
- **Vektordatenbank:** Präzision — passt die Antwort zur Frage?
- **LLM-Prompt-Design:** Ton, Länge, Sprache — passt die Antwort zur Zielgruppe?
- **UI-Design:** Gesprächsflow, Fehlerbehandlung, Onboarding
---
 
## 6. Erwartete Ergebnisse
 
1. **Nutzerstudie (User Research):** Personas und priorisierte Informationsbedürfnisse
2. **Funktionierender Chatbot-Prototyp** mit RAG-Architektur
3. **Evaluation:** Nutzertests mit SUS-Score und Bewertung nach Amershi-Guidelines
4. **Redesign-Empfehlungen** auf Basis der Evaluationsergebnisse
5. **Präsentation** (15–45 Minuten) mit vollständiger Dokumentation des UX-Prozesses
---
 
## 7. Abgrenzung
 
Das Projekt ist **kein reines Softwareentwicklungsprojekt**. Der Fokus liegt auf dem ergonomischen Designprozess: Nutzerforschung → Konzeption → Implementierung → Evaluation → Iteration. Die technische Umsetzung dient als Mittel zur Realisierung eines nutzerorientierten Interaktionskonzepts.
 
---
 
*Hamm-Lippstadt, April 2026*
 