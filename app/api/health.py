"""Health and readiness endpoints."""
from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import get_db, get_cache

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness probe - always returns healthy."""
    return {"status": "healthy"}


@router.get("/ready")
async def ready(
    response: Response,
    db = Depends(get_db),
    cache = Depends(get_cache),
) -> dict:
    """Readiness probe - checks database and cache connectivity."""
    db_healthy = await db.health_check()
    cache_healthy = await cache.health_check()
    
    if db_healthy and cache_healthy:
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected"
        }
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not ready",
            "database": "connected" if db_healthy else "disconnected",
            "redis": "connected" if cache_healthy else "disconnected"
        }
