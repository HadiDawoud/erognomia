"""Build the full crawler seed URL list (hubs + sitemap + user extras)."""

from __future__ import annotations

from typing import List, Set

import requests

from src.config import Settings
from src.ingestion.web_crawler import normalize_url
from src.ingestion.site_seeds import default_seed_paths
from src.ingestion.sitemap_fetch import discover_sitemap_urls


def build_crawl_seeds(cfg: Settings) -> List[str]:

    seeds: Set[str] = {normalize_url(cfg.target_site_url.rstrip("/"))}


    for u in default_seed_paths(cfg.target_site_url):
        nu = normalize_url(u.strip())
        if nu:
            seeds.add(nu)

    for raw in cfg.extra_seed_urls_list:
        nu = normalize_url(raw.strip())
        if nu:
            seeds.add(nu)

    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": "ErgonomiaBot/1.1 (Academic RAG)",
            "Accept": "application/xml,text/xml,*/*",
        }
    )

    for u in discover_sitemap_urls(cfg.target_site_url, sess):
        nu = normalize_url(u)
        if nu:
            seeds.add(nu)

    return sorted(s for s in seeds if s)


