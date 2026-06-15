# Ergonomia — Amershi et al. 2019 Evaluation

Bewertung des Chatbots gegen die 18 Guidelines for Human-AI Interaction.

---

## Initial Phase

| # | Guideline | Status | Befund |
|---|---|---|---|
| G1 | Make clear what the system can do | ✅ | Onboarding-Nachricht + Capability-Response |
| G2 | Make clear how well the system can do what it can do | ✅ | ``Ergonomia kann Fehler machen''-Disclaimer |
| G3 | Time services based on context | ✅ | Streaming-Antworten, Ladeindikator |

## During Interaction

| # | Guideline | Status | Befund |
|---|---|---|---|
| G4 | Show contextually relevant information | ✅ | RAG liefert nur relevanten Kontext |
| G5 | Match relevant social norms | ✅ | Formelle, höfliche Antworten auf Deutsch |
| G6 | Mitigate social biases | ❌ | Nicht adressiert (keine Bias-Prüfung) |
| G7 | Support efficient invocation | ✅ | Einfache Texteingabe, keine Registrierung nötig |
| G8 | Support efficient dismissal | ✅ | Session kann durch neuen Chat geschlossen werden |
| G9 | Support efficient correction | ❌ | Keine Editierfunktion für gesendete Nachrichten |
| G10 | Scope services when in doubt | ✅ | Fallback bei Wissenslücken |
| G11 | Make clear why the system did what it did | ✅ | Quellenangaben in jeder Antwort |
| G12 | Remember recent interactions | ✅ | Chat-Verlauf in Session |

## When Wrong

| # | Guideline | Status | Befund |
|---|---|---|---|
| G13 | Learn from user behavior | ❌ | Keine automatische Anpassung |
| G14 | Update and adapt cautiously | ❌ | Kein adaptives Lernen |
| G15 | Encourage granular feedback | ❌ | Kein Feedback-Mechanismus |
| G16 | Convey consequences of user actions | ❌ | Keine Bestätigung von Aktionen |

## Over Time

| # | Guideline | Status | Befund |
|---|---|---|---|
| G17 | Provide global controls | ❌ | Keine Einstellungsmöglichkeiten |
| G18 | Notify users about changes | ❌ | Keine Update-Benachrichtigungen |

---

## Zusammenfassung

- **Erfüllt:** 9 von 18 Guidelines
- **Teilweise/nicht relevant:** Die nicht erfüllten Guidelines (G6, G9, G13–G18) adressieren überwiegend fortgeschrittene KI-Interaktionsmuster (adaptives Lernen, Feedback, globale Kontrollen), die für den definierten Use Case (Informations-Chatbot mit lokalem RAG) nicht im Scope lagen.
- **Kernerfüllung:** Alle Guidelines der Initial-Phase (G1–G3) und die wichtigsten Interaktions-Guidelines (G4, G5, G7, G10, G11, G12) sind erfüllt.
