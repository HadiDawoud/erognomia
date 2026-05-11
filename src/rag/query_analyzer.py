import re
from typing import Dict, Any, Optional

class QueryAnalyzer:
    def __init__(self):
        self.greetings_de = [r"\bhallo\b", r"\bmoin\b", r"\btag\b", r"\bguten tag\b", r"\bhi\b"]
        self.greetings_en = [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgood morning\b"]
        
        self.smalltalk_de = [r"wer bist du", r"wie geht es", r"was kannst du"]
        self.smalltalk_en = [r"who are you", r"how are you", r"what can you do"]

    def analyze(self, query: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower()

        # Check greetings
        patterns = self.greetings_de + self.greetings_en
        for p in patterns:
            if re.search(p, query_lower):
                return {
                    "type": "greeting",
                    "language": "de",
                    "response": (
                        "Hallo! Ich bin Ergonomia, dein KI-Assistent für das Immersive Reality Lab. "
                        "Wie kann ich dir heute helfen?"
                    ),
                }

        # Check smalltalk
        for p in self.smalltalk_de + self.smalltalk_en:
            if p in query_lower:
                return {
                    "type": "smalltalk",
                    "language": "de",
                    "response": (
                        "Ich bin ein spezialisierter Chatbot, der Fragen zur Website des Immersive Reality Lab "
                        "beantworten kann. Ich nutze lokale KI-Modelle, um deine Privatsphäre zu schützen."
                    ),
                }

        return None
