from fastapi import APIRouter, Depends
from src.api.schemas import VectorStoreStats
from src.api.state import get_vector_store

router = APIRouter()

@router.get("/stats", response_model=VectorStoreStats)
async def get_stats(vector_store=Depends(get_vector_store)):
    stats = vector_store.get_collection_stats()
    return VectorStoreStats(count=stats["count"])

@router.post("/reset")
async def reset_store(vector_store=Depends(get_vector_store)):
    vector_store.reset()
    return {"status": "success", "message": "Vector store reset successfully"}
