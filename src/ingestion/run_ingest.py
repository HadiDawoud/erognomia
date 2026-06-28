"""Shared crawl → JSON snapshot → chunk → Chroma upsert (CLI + API)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.config import settings
from src.ingestion.crawl_seeds import build_crawl_seeds
from src.ingestion.js_data_ingester import ingest_js_assets
from src.ingestion.snapshot_writer import SnapshotWriter
from src.ingestion.text_chunker import TextChunker, TokenTextChunker
from src.ingestion.web_crawler import WebCrawler
from src.vectorstore.chroma_store import ChromaStore

logger = logging.getLogger(__name__)


def run_crawl_and_ingest(
    vector_store: ChromaStore,
    *,
    persist_snapshots: bool = True,
    snapshot_dir: Optional[str] = None,
    max_depth: Optional[int] = None,
    max_pages: Optional[int] = None,
    ingest_js_data: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Full site ingest: discover seeds (hubs + sitemap + extras), crawl, write JSON
    snapshots under `data/scraped/`, chunk, embed, upsert into Chroma.
    """
    seeds = build_crawl_seeds(settings)
    if not seeds:
        raise RuntimeError("No crawl seeds resolved — check TARGET_SITE_URL / network.")

    md = settings.max_crawl_depth if max_depth is None else max_depth
    mp = settings.max_pages if max_pages is None else max_pages

    logger.info(
        "Resolved %d seed URL(s); starting crawl (max_pages=%s, depth=%s)",
        len(seeds),
        mp,
        md,
    )

    crawler = WebCrawler(
        seeds,
        max_depth=md,
        max_pages=mp,
        polite_delay_sec=settings.crawl_polite_delay_sec,
    )
    if settings.chunker_type == "token":
        chunker = TokenTextChunker(
            max_tokens=settings.chunker_max_tokens,
            overlap_tokens=settings.chunker_overlap_tokens,
        )
    else:
        chunker = TextChunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)

    snap_dir = snapshot_dir or settings.scraped_snapshot_dir

    pages = 0
    chunks_total = 0

    def ingest_with_optional_writer(writer: Optional[SnapshotWriter]) -> None:
        nonlocal pages, chunks_total
        for page_data in crawler.crawl():
            pages += 1
            if writer is not None:
                writer.write_page(page_data)

            chunks = chunker.chunk_document(page_data)
            if chunks:
                vector_store.upsert_documents(chunks)
                chunks_total += len(chunks)
                logger.info("Page %s → %d chunk(s)", page_data["url"], len(chunks))

    do_js = settings.ingest_js_data if ingest_js_data is None else ingest_js_data
    js_stats: Dict[str, Any] = {}

    if persist_snapshots:
        with SnapshotWriter(snap_dir, fresh_manifest=True) as writer:
            ingest_with_optional_writer(writer)
            if do_js:
                js_stats = ingest_js_assets(vector_store, snapshot_writer=writer)
                chunks_total += int(js_stats.get("chunks", 0))
    else:
        ingest_with_optional_writer(None)
        if do_js:
            js_stats = ingest_js_assets(vector_store, snapshot_writer=None)
            chunks_total += int(js_stats.get("chunks", 0))

    logger.info("Ingest finished: %d page(s), %d chunk(s) upserted", pages, chunks_total)
    result: Dict[str, Any] = {"pages": pages, "chunks": chunks_total, "seeds": len(seeds)}
    if js_stats:
        result["js_data"] = js_stats
    return result

