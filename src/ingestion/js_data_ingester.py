"""Ingest structured data from IRL JavaScript asset files (publications, projects)."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from html import unescape
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import urljoin

import requests

from src.config import Settings, settings
from src.ingestion.js_data_parser import parse_js_window_array
from src.ingestion.snapshot_writer import SnapshotWriter
from src.ingestion.text_chunker import TextChunker, TokenTextChunker
from src.vectorstore.chroma_store import ChromaStore

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def infer_publication_category(pub_id: str) -> str:
    pid = (pub_id or "").upper()
    if pid.startswith("BC"):
        return "book_chapter"
    if pid.startswith("JC"):
        return "journal"
    if pid.startswith("CC"):
        return "conference"
    if pid.startswith("B"):
        return "book"
    if pid.startswith("J"):
        return "journal"
    if pid.startswith("C"):
        return "conference"
    if pid.startswith("P"):
        return "poster"
    return "other"


def strip_html(text: str) -> str:
    if not text:
        return ""
    return unescape(_TAG_RE.sub("", text)).strip()


def publication_detail_url(base_url: str, pub_id: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", f"pages/publicationDetail.html?id={pub_id}")


def project_detail_url(base_url: str, project_id: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", f"pages/projects.html?id={project_id}")


def publication_to_document(pub: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    pub_id = str(pub.get("id") or "").strip()
    title = strip_html(str(pub.get("title") or pub_id))
    authors = strip_html(str(pub.get("authors") or ""))
    published = strip_html(str(pub.get("published") or ""))
    abstract = strip_html(str(pub.get("abstract") or ""))
    citation = strip_html(str(pub.get("citation") or ""))
    download_link = str(pub.get("download_link") or "").strip()
    category = infer_publication_category(pub_id)
    url = publication_detail_url(base_url, pub_id)

    parts = [f"# {title}", ""]
    if authors:
        parts.extend([f"Authors: {authors}", ""])
    if published:
        parts.extend([published, ""])
    if abstract:
        parts.extend(["## Abstract", abstract, ""])
    if citation:
        parts.extend(["## Citation", citation, ""])
    if download_link:
        parts.extend(["## Download", download_link, ""])

    content = "\n".join(parts).strip()
    return {
        "url": url,
        "title": title,
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "timestamp": time.time(),
        "metadata": {
            "doc_type": "publication",
            "pub_id": pub_id,
            "authors": authors,
            "category": category,
            "download_link": download_link,
        },
    }


def _aspect_lines(aspects: Any) -> List[str]:
    lines: List[str] = []
    if not isinstance(aspects, list):
        return lines
    for item in aspects:
        if not isinstance(item, dict):
            continue
        label = strip_html(str(item.get("label") or ""))
        value = strip_html(str(item.get("value") or ""))
        if label and value:
            lines.append(f"- {label}: {value}")
        elif value:
            lines.append(f"- {value}")
    return lines


def _people_lines(label: str, people: Any) -> List[str]:
    lines: List[str] = []
    if not isinstance(people, list):
        return lines
    for person in people:
        if not isinstance(person, dict):
            continue
        name = strip_html(str(person.get("name") or ""))
        role = strip_html(str(person.get("role") or ""))
        if name and role:
            lines.append(f"- {name} ({role})")
        elif name:
            lines.append(f"- {name}")
    if lines:
        return [f"## {label}", ""] + lines + [""]
    return []


def project_to_document(project: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    project_id = str(project.get("id") or "").strip()
    name = strip_html(str(project.get("name") or project_id))
    description = strip_html(str(project.get("description") or ""))
    url = project_detail_url(base_url, project_id)

    parts = [f"# {name}", ""]
    aspect_lines = _aspect_lines(project.get("aspects"))
    if aspect_lines:
        parts.extend(["## Project details", ""] + aspect_lines + [""])
    if description:
        parts.extend(["## Description", description, ""])
    parts.extend(_people_lines("Team", project.get("team")))
    parts.extend(_people_lines("Partners", project.get("partners")))

    content = "\n".join(parts).strip()
    return {
        "url": url,
        "title": name,
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "timestamp": time.time(),
        "metadata": {
            "doc_type": "project",
            "project_id": project_id,
        },
    }


def fetch_js_asset(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def publication_detail_urls(publications: Iterable[Dict[str, Any]], base_url: str) -> Set[str]:
    return {publication_detail_url(base_url, str(p.get("id") or "").strip()) for p in publications if p.get("id")}


def ingest_js_assets(
    vector_store: ChromaStore,
    *,
    cfg: Settings | None = None,
    snapshot_writer: Optional[SnapshotWriter] = None,
    ingest_publications: bool = True,
    ingest_projects: bool = True,
) -> Dict[str, Any]:
    """Fetch reference.js / project.js, build documents, chunk, upsert."""
    cfg = cfg or settings
    base = cfg.target_site_url.rstrip("/")

    if cfg.chunker_type == "token":
        chunker = TokenTextChunker(
            max_tokens=cfg.chunker_max_tokens,
            overlap_tokens=cfg.chunker_overlap_tokens,
        )
    else:
        chunker = TextChunker(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ErgonomiaBot/1.1 (Academic RAG)",
            "Accept": "*/*",
        }
    )

    stats: Dict[str, Any] = {
        "publications": 0,
        "projects": 0,
        "chunks": 0,
        "publication_urls": [],
    }

    if ingest_publications:
        ref_url = f"{base}/assets/data/reference.js"
        logger.info("Fetching publications from %s", ref_url)
        ref_text = fetch_js_asset(session, ref_url)
        publications = parse_js_window_array(ref_text, "publications", relaxed=False)
        stats["publication_urls"] = sorted(publication_detail_urls(publications, base))

        for pub in publications:
            doc = publication_to_document(pub, base)
            if not doc["content"]:
                continue
            if snapshot_writer is not None:
                snapshot_writer.write_page(doc)
            chunks = chunker.chunk_document(doc)
            if chunks:
                vector_store.upsert_documents(chunks)
                stats["chunks"] += len(chunks)
            stats["publications"] += 1

        logger.info("Ingested %d publication(s)", stats["publications"])

    if ingest_projects:
        proj_url = f"{base}/assets/data/project.js"
        logger.info("Fetching projects from %s", proj_url)
        proj_text = fetch_js_asset(session, proj_url)
        projects = parse_js_window_array(proj_text, "projects", relaxed=True)

        for project in projects:
            doc = project_to_document(project, base)
            if not doc["content"]:
                continue
            if snapshot_writer is not None:
                snapshot_writer.write_page(doc)
            chunks = chunker.chunk_document(doc)
            if chunks:
                vector_store.upsert_documents(chunks)
                stats["chunks"] += len(chunks)
            stats["projects"] += 1

        logger.info("Ingested %d project(s)", stats["projects"])

    return stats
