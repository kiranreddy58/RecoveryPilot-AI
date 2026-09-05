from fastapi import APIRouter
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "recoverypilot-backend",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }
