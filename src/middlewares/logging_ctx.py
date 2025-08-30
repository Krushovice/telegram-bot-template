import time, contextvars, traceback

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update
from typing import Callable, Awaitable


request_id_var = contextvars.ContextVar("request_id", default=None)
logger = structlog.get_logger("aiogram")


def extract_ctx(event: TelegramObject) -> dict:
    chat_id = user_id = None
    upd_type = type(event).__name__
    if isinstance(event, Message):
        chat_id = event.chat.id if event.chat else None
        user_id = event.from_user.id if event.from_user else None
    elif isinstance(event, CallbackQuery):
        chat_id = (
            event.message.chat.id if event.message and event.message.chat else None
        )
        user_id = event.from_user.id if event.from_user else None
    elif isinstance(event, Update):
        # Aiogram сам кладёт Message/CallbackQuery в data, но на всякий
        pass
    return {
        "chat_id": chat_id,
        "user_id": user_id,
        "update_type": upd_type,
    }


class LoggingContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        start = time.perf_counter()
        ctx = extract_ctx(event)
        # request_id может быть положен в data["request_id"] в веб-хуке
        rid = data.get("request_id") or request_id_var.get()
        bind = logger.bind(
            request_id=rid, **{k: v for k, v in ctx.items() if v is not None}
        )
        try:
            bind.info("handler_start")
            result = await handler(event, data)
            dur_ms = round((time.perf_counter() - start) * 1000, 2)
            bind.info("handler_done", duration_ms=dur_ms)
            return result
        except Exception as e:
            dur_ms = round((time.perf_counter() - start) * 1000, 2)
            bind.error(
                "handler_error",
                duration_ms=dur_ms,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            # опционально: перекинуть в алерты (см. utils/alerts.py)
            data.get("alert_error", lambda *_args, **_kw: None)(
                "handler_error",
                e,
                ctx,
            )
            raise
