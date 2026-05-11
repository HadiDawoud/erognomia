"""Extract internal URLs and text signals embedded in JavaScript on static HTML pages.

Many IRL pages (e.g. team overview) expose member profiles only via JS objects rather than <a href>,
so naive link crawling never reaches /pages/team/*.html chunks for RAG.
"""

from __future__ import annotations

import re
from typing import Iterable, Set
from urllib.parse import urljoin, urlparse

_NAME_RE = re.compile(r"name\s*:\s*['\"]([^'\"]{2,200})['\"]")
_LINK_RE = re.compile(r"""link\s*:\s*['\"]([^'\"]+)['\"]""", re.IGNORECASE)
_STRING_PATH_RE = re.compile(r"""['\"](/pages/[a-zA-Z0-9_./\-]+(?:\.html)?)['\"]""")


def supplemental_text_from_scripts(html: str, page_url: str) -> str:
    """
    Add human-readable snippets derived from inline JS so RAG retains team names etc.
    even before child profile pages are crawled.
    """
    if not html:
        return ""

    names = sorted({m.group(1).strip() for m in _NAME_RE.finditer(html)})
    if not names:
        return ""

    lowered = page_url.lower()
    if "/team" not in lowered and len(names) < 4:
        return ""

    lines = ["## Namen aus eingebetteter Seitenkonfiguration (JavaScript)", ""]
    for n in names:
        lines.append(f"- {n}")
    return "\n".join(lines) + "\n"


def discover_urls_from_html(html: str, page_url: str, domain_lower: str) -> Set[str]:
    """Combine visible <a href> URLs and literal /pages paths found inside scripts."""
    if not html:
        return set()

    from bs4 import BeautifulSoup

    out: Set[str] = set()
    soup = BeautifulSoup(html, "lxml")
    domain_lower = domain_lower.lower()

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        full = urljoin(page_url, href).split("#")[0]
        parsed = urlparse(full)
        if parsed.netloc.lower() == domain_lower and parsed.scheme in {"http", "https"}:
            base = f"{parsed.scheme}://{parsed.netloc.lower()}"
            path = (parsed.path or "/").rstrip("/")
            if path and path != "/":
                out.add(f"{base}{path}")

    # Late import avoids circular import while web_crawler loads this module.
    from src.ingestion.web_crawler import normalize_url
    for rx in (_LINK_RE,):
        for m in rx.finditer(html):
            raw = m.group(1).strip()
            if "@" in raw:
                continue
            if raw.startswith(("mailto:", "tel:", "javascript:")):
                continue
            cand = raw if raw.startswith(("http://", "https://")) else urljoin(page_url, raw)
            cand = cand.split("#")[0]
            pu = urlparse(cand)
            if pu.scheme in {"http", "https"} and pu.netloc.lower() == domain_lower:
                pth = pu.path or "/"
                if pth != "/":
                    out.add(f"{pu.scheme}://{pu.netloc.lower()}{pth}".rstrip("/"))

    for m in _STRING_PATH_RE.finditer(html):
        raw_path = m.group(1).strip()
        if not raw_path.startswith("/"):
            continue
        joined = urljoin(page_url, raw_path).split("#")[0].rstrip("/")
        pu = urlparse(joined)
        if pu.netloc.lower() == domain_lower and (pu.path or "") != "/":
            out.add(f"{pu.scheme}://{pu.netloc.lower()}{(pu.path or '').rstrip('/')}")

    normed: Set[str] = set()
    for u in _filter_html_urls(out):
        nu = normalize_url(u.split("#")[0])
        p = urlparse(nu)
        if p.netloc.lower() == domain_lower and (p.path or "/").rstrip("/") not in {"", "/"}:
            normed.add(nu)
    return normed


def _filter_html_urls(urls: Iterable[str]) -> Set[str]:
    keep: Set[str] = set()
    for full in urls:
        lower = full.lower()
        if any(
            lower.endswith(ext)
            for ext in (
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".zip",
                ".docx",
                ".svg",
                ".ico",
                ".mp4",
            )
        ):
            continue
        keep.add(full)
    return keep
