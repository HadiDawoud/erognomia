import json
import re
from typing import Dict, Any
from src.llm.ollama_client import get_ollama_client
import logging

logger = logging.getLogger(__name__)

class QueryClassifier:
    def __init__(self):
        self.llm = get_ollama_client()
        self.system_prompt = """You are a query classifier for a RAG system.
Your task is to analyze the user's query and return a JSON object with the following fields:
- query_type: one of ["person", "topic", "aggregate", "general", "unanswerable"]
- entity_name: extracted name or null
- topic_name: extracted topic or null
- category: one of ["project", "publication", "teaching", "team", "other"] or null
- search_keywords: list of important keywords for search
- needs_keyword_search: boolean
- language: "de" or "en"

Return ONLY the JSON object. Do not include any explanations.

Example:
Query: "Who is Prof. Dr. Christian Kohls?"
Response: {"query_type": "person", "entity_name": "Christian Kohls", "topic_name": null, "category": "team", "search_keywords": ["Christian Kohls"], "needs_keyword_search": true, "language": "de"}
"""

    def _heal_json(self, text: str) -> str:
        # Remove markdown code blocks if present
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        return text.strip()

    def classify(self, query: str) -> Dict[str, Any]:
        try:
            response = self.llm.generate(query, system_prompt=self.system_prompt, temperature=0.0)
            healed_response = self._heal_json(response)
            return json.loads(healed_response)
        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            return {
                "query_type": "general",
                "entity_name": None,
                "topic_name": None,
                "category": None,
                "search_keywords": [query],
                "needs_keyword_search": True,
                "language": "de"
            }
