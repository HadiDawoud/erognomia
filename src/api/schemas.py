from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    session_id: Optional[str] = None

class Source(BaseModel):
    url: str
    title: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    message_id: Optional[str] = None
    session_id: Optional[str] = None

class SessionCreate(BaseModel):
    title: Optional[str] = None

class SessionInfo(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_summarized_at: Optional[str] = None
    user_edited: bool = False

class SessionRename(BaseModel):
    title: str

class SessionMessage(BaseModel):
    role: str
    content: str
    sources: List[Source] = []
    timestamp: Optional[str] = None

class IngestRequest(BaseModel):
    seed_url: Optional[str] = Field(
        default=None,
        description="Deprecated/ignored. Ingest always uses hub URLs + sitemap + EXTRA_SEED_URLS from settings.",
    )
    max_depth: Optional[int] = None
    max_pages: Optional[int] = None

class IngestResponse(BaseModel):
    status: str
    message: str

class VectorStoreStats(BaseModel):
    count: int
