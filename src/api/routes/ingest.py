import logging

from fastapi import APIRouter, BackgroundTasks, Depends

from src.api.schemas import IngestRequest, IngestResponse
from src.api.state import get_vector_store
from src.config import settings
from src.ingestion.run_ingest import run_crawl_and_ingest
from src.vectorstore.chroma_store import ChromaStore

router = APIRouter()
logger = logging.getLogger(__name__)


def _ingest_job(vector_store: ChromaStore, max_depth: int, max_pages: int) -> None:
    try:
        run_crawl_and_ingest(
            vector_store,
            persist_snapshots=True,
            max_depth=max_depth,
            max_pages=max_pages,
        )
    except Exception:
        logger.exception("Background ingest failed")


@router.post("/crawl", response_model=IngestResponse)
async def crawl_site(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    vector_store: ChromaStore = Depends(get_vector_store),
):
    """
    Full-site ingest: hub seeds + sitemap URLs + link discovery, JSON under `data/scraped/`,
    then chunk + embed into Chroma. `seed_url` on the body is ignored (kept for API compatibility).
    """
    max_depth = request.max_depth or settings.max_crawl_depth
    max_pages = request.max_pages or settings.max_pages

    background_tasks.add_task(_ingest_job, vector_store, max_depth, max_pages)

    return IngestResponse(
        status="started",
        message="Full-site crawl + JSON snapshots + vector ingest started (see data/scraped/).",
    )
