from fastapi import APIRouter, Request, HTTPException
from aiogram.types import Update
from web.runtime import runtime
from core.config import settings

router = APIRouter(tags=["telegram"])


@router.post(settings.web.main_path)
async def telegram_webhook(request: Request):
    # Проверяем секрет (если задан)
    expected = getattr(settings.web, "secret", None)
    if expected:
        got = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if got != expected:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    rid = request.headers.get("X-Request-ID")
    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": runtime.bot})
    await runtime.dp.feed_update(
        bot=runtime.bot,
        update=update,
        request_id=rid,
    )
    return {"ok": True}
