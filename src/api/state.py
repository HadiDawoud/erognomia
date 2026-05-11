from typing import Optional
from src.rag.pipeline import RAGPipeline
from src.vectorstore.chroma_store import ChromaStore

class AppState:
    def __init__(self):
        self.rag_pipeline: Optional[RAGPipeline] = None
        self.vector_store: Optional[ChromaStore] = None

state = AppState()

def get_rag_pipeline() -> RAGPipeline:
    if state.rag_pipeline is None:
        raise RuntimeError("RAG Pipeline not initialized")
    return state.rag_pipeline

def get_vector_store() -> ChromaStore:
    if state.vector_store is None:
        raise RuntimeError("Vector Store not initialized")
    return state.vector_store
