import re
from typing import Any, Dict, Optional


_CAPABILITY_RESPONSE_DE = """Ich kann dir Fragen zum **Immersive Reality Lab** an der HSHL beantworten – **nur auf Basis dessen**, was auf der Lab-Website steht und in meinem Wissensspeicher (RAG) dazu gespeichert ist.

Konkret z. B. zu:

- Forschungsprojekten und XR-/Digital-Health-Themen aus der Website  
- Veröffentlichungen (Themenüberblick über die dort gelisteten Publikationsseiten)  
- Lehre und praxisbezogenen Angeboten  
- Ausstattung, Methoden/Infrastruktur sowie Ausleihe oder Nutzungsbedingungen, **sofern** das auf den Seiten steht  
- Team, Kontakt und Impressum, **falls** dort genannt  

Wenn du **nichts Passendes** im Kontext findest oder die Website es nicht enthält, sage ich ehrlich, dass ich das nicht weiß – und empfehle die Lab-Website oder den direkten Kontakt dort.

Probier‘s z. B. mit einer konkreten Frage zu einem Projekt, einer Vorlesung oder einer Person aus dem Team."""


class QueryAnalyzer:
    def __init__(self):
        self.greetings_de = [r"\bhallo\b", r"\bmoin\b", r"\btag\b", r"\bguten tag\b", r"\bhi\b"]
        self.greetings_en = [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgood morning\b"]

        self.smalltalk_de = [
            "wer bist du",
            "wie geht es",
        ]
        self.smalltalk_en = [
            "who are you",
            "how are you",
        ]

    def _is_capability_question(self, query_lower: str) -> bool:
        """User asks what the bot can do / which topics / help — not a pure hello."""
        triggers = (
            "womit kann",
            "wobei kann",
            "was kannst du",
            "was darfst du",
            "was beantwortest",
            "welche fragen",
            "welche themen",
            "welche art von fragen",
            "worüber kannst",
            "worüber weißt",
            "über was kannst",
            "in welchen bereichen",
            "welche informationen",
            "was weißt du",
            "hilfst du mir",
            "wie hilfst du",
            "how can you help",
            "what can you do",
            "what can you answer",
            "what questions",
            "what do you know",
        )
        return any(t in query_lower for t in triggers)

    def _is_pure_greeting(self, query_lower: str) -> bool:
        """Short or greeting-only messages (no real question)."""
        q = query_lower.strip()
        if len(q) <= 18:
            return True
        if "?" not in q and len(q) <= 40:
            return True
        return False

    def analyze(self, query: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower().strip()

        # 1) Explicit "what can you do / which questions" — must win over "hallo …"
        if self._is_capability_question(query_lower):
            return {
                "type": "capabilities",
                "language": "de",
                "response": _CAPABILITY_RESPONSE_DE,
            }

        # 2) Smalltalk (short identity / how are you) — before generic greeting
        for p in self.smalltalk_de + self.smalltalk_en:
            if p in query_lower:
                return {
                    "type": "smalltalk",
                    "language": "de",
                    "response": (
                        "Ich bin Ergonomia, der Chatbot zum Immersive Reality Lab. "
                        "Ich beantworte Fragen zu Inhalten der Lab-Website – datenschutzfreundlich mit lokaler KI. "
                        "Frag mich gern zu Projekten, Lehre, Publikationen oder Kontakt, sofern das auf der Website steht."
                    ),
                }

        # 3) Pure hello/hi only — not "hallo, welche fragen …"
        patterns = self.greetings_de + self.greetings_en
        for p in patterns:
            if re.search(p, query_lower) and self._is_pure_greeting(query_lower):
                return {
                    "type": "greeting",
                    "language": "de",
                    "response": (
                        "Hallo! Ich bin Ergonomia, dein KI-Assistent für das Immersive Reality Lab. "
                        "Wie kann ich dir heute helfen?"
                    ),
                }

        return None
