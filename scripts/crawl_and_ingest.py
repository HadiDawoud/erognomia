"""CLI: exhaustive crawl → JSON snapshots → embeddings → ChromaDB."""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    from src.ingestion.run_ingest import run_crawl_and_ingest
    from src.vectorstore.chroma_store import get_vector_store

    stats = run_crawl_and_ingest(get_vector_store(), persist_snapshots=True)
    logger.info("Done: %(pages)s pages, %(chunks)s chunks, %(seeds)s seeds", stats)


if __name__ == "__main__":
    main()
