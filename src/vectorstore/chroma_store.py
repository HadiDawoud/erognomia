import chromadb
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from typing import List, Dict, Any, Optional
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class ChromaStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.embedding_model = SentenceTransformer(settings.embedding_model_name)
        self.collection = self.client.get_or_create_collection(
            name="website_content",
            metadata={"hnsw:space": "cosine"}
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_model.encode(texts).tolist()

    def upsert_documents(self, documents: List[Dict[str, Any]]):
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        embeddings = self.embed_texts(texts)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def similarity_search(self, query: str, k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        query_embedding = self.embed_texts([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_metadata
        )

        formatted_results = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            if distance <= settings.retrieval_max_distance:
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": distance
                })
        return formatted_results

    def keyword_search(self, keyword: str, k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        # Pure substring filter via `get()` — avoids triggering the default
        # embedding function (which would mismatch our custom 768-d model).
        results = self.collection.get(
            where=filter_metadata,
            where_document={"$contains": keyword},
            limit=k,
        )

        formatted_results = []
        for i in range(len(results["ids"])):
            formatted_results.append({
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": 0.0,
            })
        return formatted_results

    def get_collection_stats(self) -> Dict[str, Any]:
        return {
            "count": self.collection.count()
        }

    def reset(self):
        self.client.delete_collection("website_content")
        self.collection = self.client.get_or_create_collection(
            name="website_content",
            metadata={"hnsw:space": "cosine"}
        )

@lru_cache(maxsize=1)
def get_vector_store() -> ChromaStore:
    return ChromaStore()
