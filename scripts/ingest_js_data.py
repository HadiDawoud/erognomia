"""CLI: ingest publications + projects from IRL assets/data/*.js only."""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    from src.ingestion.js_data_ingester import ingest_js_assets
    from src.ingestion.snapshot_writer import SnapshotWriter
    from src.config import settings
    from src.vectorstore.chroma_store import get_vector_store

    vector_store = get_vector_store()
    with SnapshotWriter(settings.scraped_snapshot_dir, fresh_manifest=False) as writer:
        stats = ingest_js_assets(vector_store, snapshot_writer=writer)
    logger.info(
        "Done: %(publications)s publications, %(projects)s projects, %(chunks)s chunks",
        stats,
    )


if __name__ == "__main__":
    main()
