from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionInfo,
    SessionMessage,
    SessionRename,
)
from src.api.state import get_rag_pipeline
from src.chat.history import get_chat_history
import json
import asyncio
import uuid

router = APIRouter()


def _new_session_id() -> str:
    return uuid.uuid4().hex


@router.post("/message")
async def chat_message(request: ChatRequest, pipeline=Depends(get_rag_pipeline)):
    history_store = get_chat_history()
    session_id = request.session_id or _new_session_id()
    history_store.create_session(session_id)

    history = [{"role": m.role, "content": m.content} for m in request.history]
    history_store.add_message(session_id, "user", request.message)

    result = await asyncio.to_thread(pipeline.query, request.message, history)

    history_store.add_message(
        session_id, "assistant", result["answer"], result.get("sources")
    )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session_id,
    )


@router.get("/stream")
async def chat_stream(message: str, session_id: str = None, pipeline=Depends(get_rag_pipeline)):
    history_store = get_chat_history()
    sid = session_id or _new_session_id()
    history_store.create_session(sid)
    history_store.add_message(sid, "user", message)

    async def event_generator():
        gen = pipeline.stream_query(message)
        answer_parts: list[str] = []
        collected_sources = None

        yield f"event: session\ndata: {json.dumps(sid)}\n\n"

        while True:
            try:
                item = await asyncio.to_thread(next, gen)
                t = item.get("type")
                if t == "answer" and item.get("content") is not None:
                    payload = item["content"]
                    answer_parts.append(payload)
                elif t == "sources" and item.get("content") is not None:
                    payload = item["content"]
                    collected_sources = payload
                else:
                    continue
                yield f"event: {t}\ndata: {json.dumps(payload)}\n\n"
            except StopIteration:
                break
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                break

        history_store.add_message(
            sid, "assistant", "".join(answer_parts), collected_sources
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/sessions", response_model=SessionInfo)
async def create_session(payload: SessionCreate = SessionCreate()):
    history_store = get_chat_history()
    session_id = _new_session_id()
    history_store.create_session(session_id, payload.title or "New Chat")
    session = history_store.get_session(session_id)
    return _to_session_info(session)


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions():
    history_store = get_chat_history()
    return [_to_session_info(s) for s in history_store.get_sessions()]


@router.get("/sessions/{session_id}/messages", response_model=list[SessionMessage])
async def get_session_messages(session_id: str):
    history_store = get_chat_history()
    if history_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = history_store.get_messages(session_id)
    result = []
    for m in messages:
        sources = json.loads(m["sources"]) if m.get("sources") else []
        result.append(
            SessionMessage(
                role=m["role"],
                content=m["content"],
                sources=sources,
                timestamp=m.get("timestamp"),
            )
        )
    return result


@router.patch("/sessions/{session_id}", response_model=SessionInfo)
async def rename_session(session_id: str, payload: SessionRename):
    history_store = get_chat_history()
    if history_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    history_store.update_title(session_id, payload.title.strip(), user_edited=True)
    return _to_session_info(history_store.get_session(session_id))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    history_store = get_chat_history()
    if history_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    history_store.delete_session(session_id)
    return {"status": "deleted", "id": session_id}


def _to_session_info(session: dict) -> SessionInfo:
    return SessionInfo(
        id=session["id"],
        title=session.get("title"),
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        last_summarized_at=session.get("last_summarized_at"),
        user_edited=bool(session.get("user_edited")),
    )
