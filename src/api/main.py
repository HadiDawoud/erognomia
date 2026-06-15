from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api.state import state
from src.config import settings
from src.rag.pipeline import get_rag_pipeline
from src.vectorstore.chroma_store import get_vector_store
from src.chat.history import get_chat_history
from src.chat.summarizer import run_summarizer_loop
from src.api.routes import chat, ingest, vectorstore
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize singletons
    logger.info("Initializing application state...")
    state.rag_pipeline = get_rag_pipeline()
    state.vector_store = get_vector_store()
    get_chat_history()
    summarizer_task = asyncio.create_task(run_summarizer_loop())
    yield
    # Cleanup if needed
    logger.info("Shutting down...")
    summarizer_task.cancel()
    try:
        await summarizer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Ergonomia API", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
