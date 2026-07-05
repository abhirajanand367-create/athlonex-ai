from fastapi import APIRouter
import time

router = APIRouter()
start_time = time.time()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "athlonex-ai-service",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - start_time),
        "timestamp": time.time(),
    }
