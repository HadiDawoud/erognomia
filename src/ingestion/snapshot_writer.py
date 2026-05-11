"""Persist scraped HTML pages as normalized JSON snapshots for reproducible ingest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from pydantic import BaseModel, ConfigDict, Field


class SnapshotRecord(BaseModel):
    """One scraped page, ready for chunking and audit."""

    model_config = ConfigDict(extra="ignore")

    url: str
    title: str
    content: str
    content_hash: str
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_type: str = "text/html"


class SnapshotWriter:
    def __init__(self, base_dir: str = "./data/scraped", *, fresh_manifest: bool = True):
        self.base = Path(base_dir)
        self.pages_dir = self.base / "pages"
        self.manifest_path = self.base / "manifest.jsonl"
        self.run_meta_path = self.base / "last_run.json"
        self.fresh_manifest = fresh_manifest
        self._manifest_fh: Optional[TextIO] = None
        self.run_urls: List[str] = []

    def __enter__(self) -> "SnapshotWriter":
        self.base.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        mode = "w" if self.fresh_manifest else "a"
        self._manifest_fh = self.manifest_path.open(mode, encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._manifest_fh:
            self._manifest_fh.close()
            self._manifest_fh = None
        self.run_meta_path.write_text(
            json.dumps(
                {
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "page_count": len(self.run_urls),
                    "urls": self.run_urls,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def write_page(self, page: Dict[str, Any]) -> None:
        rec = SnapshotRecord(
            url=page["url"],
            title=page["title"],
            content=page["content"],
            content_hash=page["content_hash"],
        )
        url_key = hashlib.sha256(rec.url.encode("utf-8")).hexdigest()[:24]
        out_file = self.pages_dir / f"{url_key}.json"
        payload = rec.model_dump()
        out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if self._manifest_fh:
            self._manifest_fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._manifest_fh.flush()
        self.run_urls.append(rec.url)

