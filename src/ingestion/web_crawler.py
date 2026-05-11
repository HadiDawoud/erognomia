import hashlib
import logging
import re
import time
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin, urlunparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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


class WebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ErgonomiaBot/1.1 (Academic RAG)",
                "Accept": "text/html,application/xhtml+xml",
            }
        )

    def clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")

        for element in soup(["nav", "footer", "script", "style", "aside", "form"]):
            element.decompose()

        for header in list(soup.find_all("header")):
            if header.find_parent("main") or header.find_parent("article"):
                continue
            header.decompose()

        for element in soup.find_all(class_=re.compile(r"cookie|banner|ad|social|share|sidebar", re.I)):
            element.decompose()
        for element in soup.find_all(id=re.compile(r"cookie|banner|ad|social|share|sidebar", re.I)):
            element.decompose()

        main_content = soup.find("article") or soup.find("main") or soup.find("div", {"id": "content"}) or soup.body

        if not main_content:
            return ""

        for h in main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading = h.get_text(" ", strip=True)
            level = int(h.name[1])
            h.clear()
            h.append(f"\n\n{'#' * level} {heading}\n")

        for li in main_content.find_all("li"):
            text = li.get_text(" ", strip=True)
            li.clear()
            li.append(f"\n- {text}\n")

        text = main_content.get_text(separator=" ")
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            ctype = response.headers.get("Content-Type", "")
            if "text/html" not in ctype:
                return None

            soup = BeautifulSoup(response.text, "lxml")
            title_el = soup.title.string if soup.title else None
            title = title_el.strip() if title_el else url
            content = self.clean_html(response.text)

            if not content:
                return None

            return {
                "url": url,
                "title": title,
                "content": content,
                "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "timestamp": time.time(),
            }
        except Exception as e:
            logger.error("Error scraping %s: %s", url, e)
            return None


class WebCrawler:
    def __init__(
        self,
        seeds: List[str],
        max_depth: int = 5,
        max_pages: int = 800,
        *,
        polite_delay_sec: float = 0.35,
    ):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.polite_delay_sec = polite_delay_sec
        norm_seeds = [normalize_url(u) for u in seeds if normalize_url(u)]
        if not norm_seeds:
            raise ValueError("WebCrawler requires at least one valid seed URL after normalization")
        self.domain = urlparse(norm_seeds[0]).netloc.lower()
        self.visited_norm: Set[str] = set()
        self.enqueued_norm: Set[str] = set()
        self.to_visit: List[Tuple[str, int]] = []
        for s in norm_seeds:
            if self._is_valid_normalized(s):
                self._enqueue(s, 0)

        self.scraper = WebScraper()

    def _enqueue(self, norm_url: str, depth: int) -> None:
        if norm_url in self.visited_norm or norm_url in self.enqueued_norm:
            return
        if not self._is_valid_normalized(norm_url):
            return
        self.enqueued_norm.add(norm_url)
        self.to_visit.append((norm_url, depth))

    def _is_valid_normalized(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc.lower() != self.domain:
            return False
        lower = url.lower()
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
                ".mp4",
                ".svg",
                ".ico",
            )
        ):
            return False
        if any(lower.startswith(p) for p in ("mailto:", "tel:", "javascript:")):
            return False
        return True

    def crawl(self) -> Iterator[Dict[str, Any]]:
        count = 0
        while self.to_visit and count < self.max_pages:
            url, depth = self.to_visit.pop(0)
            if url in self.visited_norm:
                continue
            if depth > self.max_depth:
                continue

            self.visited_norm.add(url)
            logger.info("Crawling: %s (depth %s)", url, depth)

            data = self.scraper.scrape(url)
            if data:
                count += 1
                yield data

                try:
                    response = self.scraper.session.get(url, timeout=20)
                    if "text/html" not in response.headers.get("Content-Type", ""):
                        continue
                    soup = BeautifulSoup(response.text, "lxml")
                    for a in soup.find_all("a", href=True):
                        full = urljoin(url, a["href"])
                        full = normalize_url(full.split("#")[0])
                        if not full:
                            continue
                        if self._is_valid_normalized(full) and full not in self.visited_norm:
                            self._enqueue(full, depth + 1)
                except Exception as e:
                    logger.warning("Link extraction failed for %s: %s", url, e)

            time.sleep(self.polite_delay_sec)
