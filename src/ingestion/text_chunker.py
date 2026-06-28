import hashlib
import logging
from typing import Any, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = doc["content"]
        url = doc["url"]
        title = doc["title"]
        content_hash = doc["content_hash"]
        path = urlparse(url).path or "/"
        extra_metadata = doc.get("metadata") or {}
        chunks = []
        
        # Simple recursive character splitting logic
        start = 0
        chunk_idx = 0
        while start < len(text):
            end = start + self.chunk_size
            if end > len(text):
                end = len(text)
            else:
                # Try to find a good split point (newline or sentence end)
                last_newline = text.rfind("\n", start, end)
                if last_newline != -1 and last_newline > start + (self.chunk_size // 2):
                    end = last_newline
                else:
                    last_period = text.rfind(". ", start, end)
                    if last_period != -1 and last_period > start + (self.chunk_size // 2):
                        end = last_period + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                metadata = {
                    "source": url,
                    "title": title,
                    "path": path,
                    "chunk_id": chunk_idx,
                    "content_hash": content_hash,
                    "timestamp": doc["timestamp"],
                }
                metadata.update(extra_metadata)
                chunks.append({
                    "id": f"{hashlib.sha256(url.encode()).hexdigest()}_{chunk_idx}",
                    "text": chunk_text,
                    "metadata": metadata,
                })
                chunk_idx += 1
            
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
            if end == len(text):
                break

        return chunks


class TokenTextChunker:
    """Token-aware text chunker using tiktoken for more precise splits."""

    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 50, encoding: str = "cl100k_base"):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding(encoding)
        except ImportError:
            logger.warning("tiktoken not installed, falling back to character-based chunking")
            self.encoder = None

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.encoder:
            fallback = TextChunker(self.max_tokens * 4, self.overlap_tokens * 4)
            return fallback.chunk_document(doc)

        text = doc["content"]
        url = doc["url"]
        title = doc["title"]
        content_hash = doc["content_hash"]
        path = urlparse(url).path or "/"
        extra_metadata = doc.get("metadata") or {}
        tokens = self.encoder.encode(text)
        chunks = []
        chunk_idx = 0
        start = 0

        while start < len(tokens):
            end = start + self.max_tokens
            if end > len(tokens):
                end = len(tokens)

            chunk_tokens = tokens[start:end]
            chunk_text = self.encoder.decode(chunk_tokens).strip()
            if chunk_text:
                metadata = {
                    "source": url,
                    "title": title,
                    "path": path,
                    "chunk_id": chunk_idx,
                    "content_hash": content_hash,
                    "timestamp": doc["timestamp"],
                }
                metadata.update(extra_metadata)
                chunks.append({
                    "id": f"{hashlib.sha256(url.encode()).hexdigest()}_t{chunk_idx}",
                    "text": chunk_text,
                    "metadata": metadata,
                })
                chunk_idx += 1

            start = end - self.overlap_tokens
            if start <= 0:
                start = 0
            if end >= len(tokens):
                break

        return chunks
