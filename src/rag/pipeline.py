from functools import lru_cache
from typing import Any, Dict, Iterator, List

import logging

from src.config import settings
from src.llm.ollama_client import get_ollama_client
from src.rag.query_analyzer import QueryAnalyzer
from src.rag.query_classifier import QueryClassifier
from src.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self.vector_store = get_vector_store()
        self.llm = get_ollama_client()
        self.analyzer = QueryAnalyzer()
        self.classifier = QueryClassifier()
        
    def format_context(self, results: List[Dict[str, Any]]) -> str:
        context_parts = []
        for i, res in enumerate(results):
            source = res["metadata"].get("source", "Unknown")
            title = res["metadata"].get("title", "Unknown")
            text = res["text"]
            context_parts.append(f"Source [{i+1}]: {title} ({source})\nContent: {text}")
        return "\n\n---\n\n".join(context_parts)

    def retrieve_context(self, query: str, classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        
        # 1. Semantic search
        semantic_results = self.vector_store.similarity_search(query, k=settings.retrieval_k)
        results.extend(semantic_results)

        ent = classification.get("entity_name")
        if isinstance(ent, str):
            cleaned = ent.strip()
            if cleaned:
                results.extend(self.vector_store.similarity_search(cleaned, k=min(5, settings.retrieval_k)))
        
        # 2. Keyword search if needed
        if classification.get("needs_keyword_search") and classification.get("search_keywords"):
            for kw in classification["search_keywords"]:
                kw_results = self.vector_store.keyword_search(kw, k=2)
                results.extend(kw_results)

        # Person queries: boost lexical hits on full name and name parts (helps once profile pages exist in store).
        if classification.get("query_type") == "person":
            kws_person: List[str] = []
            ent2 = classification.get("entity_name")
            if isinstance(ent2, str) and ent2.strip():
                kws_person.append(ent2.strip())
                for part in ent2.replace("-", " ").replace(",", " ").split():
                    p = part.strip().strip(";.:\"'")
                    if len(p) >= 3:
                        kws_person.append(p)
            for kw in kws_person:
                results.extend(self.vector_store.keyword_search(kw, k=8))

        # Deduplicate
        seen_ids = set()
        deduped = []
        for r in results:
            if r["id"] not in seen_ids:
                deduped.append(r)
                seen_ids.add(r["id"])
                
        return deduped[:settings.retrieval_k + 2]

    def query(self, user_query: str, history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        # Fast path
        analysis = self.analyzer.analyze(user_query)
        if analysis:
            return {
                "answer": analysis["response"],
                "sources": [],
                "type": analysis["type"]
            }
            
        # Classify
        classification = self.classifier.classify(user_query)
        
        # Retrieve
        context_docs = self.retrieve_context(user_query, classification)
        context_text = self.format_context(context_docs)
        
        # Generate
        system_prompt = self._get_system_prompt("de")
        prompt = f"Context:\n{context_text}\n\nUser Question: {user_query}"

        answer = self.llm.generate(prompt, system_prompt=system_prompt)

        return {
            "answer": answer,
            "sources": [{"url": d["metadata"]["source"], "title": d["metadata"]["title"]} for d in context_docs],
            "classification": classification
        }

    def stream_query(self, user_query: str, history: List[Dict[str, str]] = []) -> Iterator[Dict[str, Any]]:
        # Fast path
        analysis = self.analyzer.analyze(user_query)
        if analysis:
            yield {"type": "answer", "content": analysis["response"]}
            yield {"type": "done", "sources": []}
            return
            
        # Classify
        classification = self.classifier.classify(user_query)
        
        # Retrieve
        context_docs = self.retrieve_context(user_query, classification)
        context_text = self.format_context(context_docs)
        
        # Send sources first
        yield {"type": "sources", "content": [{"url": d["metadata"]["source"], "title": d["metadata"]["title"]} for d in context_docs]}
        
        # Generate
        system_prompt = self._get_system_prompt("de")
        prompt = f"Context:\n{context_text}\n\nUser Question: {user_query}"

        full_answer = ""
        for chunk in self.llm.stream_generate(prompt, system_prompt=system_prompt):
            full_answer += chunk
            yield {"type": "answer", "content": chunk}

        yield {"type": "done", "answer": full_answer}

    def _get_system_prompt(self, lang: str) -> str:
        if lang == "de":
            return """Du bist Ergonomia, der offizielle Chatbot des Immersive Reality Lab.
Beantworte die Frage NUR basierend auf dem bereitgestellten Kontext.
Wenn die Antwort nicht im Kontext steht, sage höflich, dass du es nicht weißt.
Zitiere deine Quellen (URL oder Titel).
Antworte auf Deutsch."""
        else:
            return """You are Ergonomia, the official chatbot of the Immersive Reality Lab.
Answer the question ONLY based on the provided context.
If the answer is not in the context, politely say you don't know.
Cite your sources (URL or title).
Answer in English."""


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline()
