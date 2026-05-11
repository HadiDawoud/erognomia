"""Fetch and parse sitemap.xml (+ nested sitemap indexes) for a site."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Set
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


def _same_host(url: str, allowed_host: str) -> bool:
    try:
        return urlparse(url).netloc.lower() == allowed_host.lower()
    except Exception:
        return False


def _extract_locs(xml_text: str) -> List[str]:
    """Regex first (robust to namespaces); fallback to ElementTree."""
    found = [u.strip() for u in _LOC_RE.findall(xml_text or "")]
    if found:
        return found
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    # strip namespace for child tag compare
    urls: List[str] = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "loc" and el.text:
            urls.append(el.text.strip())
    return urls


def discover_sitemap_urls(
    site_base: str,
    session: requests.Session,
    *,
    max_sitemaps: int = 25,
    timeout: int = 20,
) -> List[str]:
    """
    Return all page URLs from sitemap.xml reachable from site_base.
    Resolves sitemap indexes (multiple <sitemap><loc>…</loc>).
    """
    base_p = urlparse(site_base)
    host = base_p.netloc
    if not host:
        return []

    primary = urljoin(site_base.rstrip("/") + "/", "sitemap.xml")
    to_fetch: List[str] = [primary]
    seen_maps: Set[str] = set()
    page_urls: Set[str] = set()
    maps_fetched = 0

    while to_fetch and maps_fetched < max_sitemaps:
        sm_url = to_fetch.pop(0)
        sm_key = sm_url.split("#")[0]
        if sm_key in seen_maps:
            continue
        seen_maps.add(sm_key)
        maps_fetched += 1
        try:
            r = session.get(sm_key, timeout=timeout)
            if r.status_code != 200:
                logger.warning("Sitemap fetch failed %s — %s", sm_key, r.status_code)
                continue
            text = r.text
        except requests.RequestException as e:
            logger.warning("Sitemap request error for %s: %s", sm_key, e)
            continue

        lowered = (text or "").lower()
        is_index = "<sitemapindex" in lowered
        is_urlset = "<urlset" in lowered
        locs = _extract_locs(text)
        if not locs:
            continue

        if is_index:
            for loc in locs:
                low = loc.lower()
                if low.endswith(".xml") and _same_host(loc, host):
                    k = loc.split("#")[0]
                    if k not in seen_maps:
                        to_fetch.append(loc)
        elif is_urlset:
            for loc in locs:
                if _same_host(loc, host) and not loc.lower().endswith(".xml"):
                    page_urls.add(loc.split("#")[0])
        else:
            # Unknown shape: treat <loc> entries as pages if not .xml
            for loc in locs:
                low = loc.lower()
                if low.endswith(".xml") and _same_host(loc, host):
                    k = loc.split("#")[0]
                    if k not in seen_maps:
                        to_fetch.append(loc)
                elif _same_host(loc, host):
                    page_urls.add(loc.split("#")[0])

    return sorted(page_urls)
