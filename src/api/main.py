from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api.state import state
from src.rag.pipeline import get_rag_pipeline
from src.vectorstore.chroma_store import get_vector_store
from src.api.routes import chat, ingest, vectorstore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize singletons
    logger.info("Initializing application state...")
    state.rag_pipeline = get_rag_pipeline()
    state.vector_store = get_vector_store()
    yield
    # Cleanup if needed
    logger.info("Shutting down...")

app = FastAPI(title="Ergonomia API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingestion"])
app.include_router(vectorstore.router, prefix="/api/vectorstore", tags=["vectorstore"])

@app.get("/health")
async def health():
    return {"status": "ok"}
