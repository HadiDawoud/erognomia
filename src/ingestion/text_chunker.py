import hashlib
from typing import Any, Dict, List
from urllib.parse import urlparse


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
                chunks.append({
                    "id": f"{hashlib.sha256(url.encode()).hexdigest()}_{chunk_idx}",
                    "text": chunk_text,
                    "metadata": {
                        "source": url,
                        "title": title,
                        "path": path,
                        "chunk_id": chunk_idx,
                        "content_hash": content_hash,
                        "timestamp": doc["timestamp"],
                    }
                })
                chunk_idx += 1
            
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
            if end == len(text):
                break

        return chunks
