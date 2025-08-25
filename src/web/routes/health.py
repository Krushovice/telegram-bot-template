from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["infra"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/version")
async def version():
    return {
        "service": "business-bot",
        "mode": "webhook",
        "base_url": settings.web.base_url,
    }
