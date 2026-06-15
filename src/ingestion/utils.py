"""Shared utility functions for ingestion modules."""

from urllib.parse import urlparse, urlunparse


def normalize_url(raw: str, default_scheme: str = "https") -> str:
    """Canonical form for deduplication: lowercase host, drop fragment, trim trailing slash on path (keep query)."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    scheme = (parsed.scheme or default_scheme).lower()
    netloc = (parsed.netloc or "").lower()
    path = parsed.path or "/"
    query = parsed.query
    if not netloc and parsed.path:
        p2 = urlparse(f"{scheme}:{raw}" if raw.startswith("//") else raw)
        scheme = (p2.scheme or default_scheme).lower()
        netloc = (p2.netloc or "").lower()
        path = p2.path or "/"
        query = p2.query
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", query, ""))
