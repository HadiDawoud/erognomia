from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.api.schemas import ChatRequest, ChatResponse
from src.api.state import get_rag_pipeline
import json
import asyncio

router = APIRouter()

@router.post("/message")
async def chat_message(request: ChatRequest, pipeline=Depends(get_rag_pipeline)):
    history = [{"role": m.role, "content": m.content} for m in request.history]
    result = await asyncio.to_thread(pipeline.query, request.message, history)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"]
    )

@router.get("/stream")
async def chat_stream(message: str, pipeline=Depends(get_rag_pipeline)):
    async def event_generator():
        # Using to_thread for the sync generator
        # Note: In a real scenario, we might want a queue if the generator is complex
        loop = asyncio.get_event_loop()
        gen = pipeline.stream_query(message)
        
        while True:
            try:
                item = await loop.run_in_executor(None, next, gen)
                t = item.get("type")
                if t == "answer" and item.get("content") is not None:
                    payload = item["content"]
                elif t == "sources" and item.get("content") is not None:
                    payload = item["content"]
                else:
                    continue
                yield f"event: {t}\ndata: {json.dumps(payload)}\n\n"
            except StopIteration:
                break
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                break
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")
