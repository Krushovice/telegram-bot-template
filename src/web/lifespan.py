from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Dispatcher
from app.core.runtime import runtime
from app.core.config import settings
from app.core.logging import setup_logger
from app.storage.db import session_factory, test_connection
from app.middlewares.db_session import DbSessionMiddleware

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await runtime.build()
    bot, dp = runtime.bot, runtime.dp

    # Redis ping (если включён)
    if runtime.redis:
        try:
            pong = await runtime.redis.ping()
            logger.info(f"Redis PING: {pong}")
        except Exception as e:
            logger.exception("Redis unavailable")
            raise

    # Webhook register (с секретом, если задан)
    secret = getattr(settings.web, "secret", None)
    await bot.set_webhook(
        url=settings.web.get_webhook_url(),
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
        secret_token=secret if secret else None,
    )

    # DB ping
    async with session_factory() as s:
        await test_connection(s)

    # Aiogram DB middleware
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=session_factory))

    # Планировщик
    runtime.scheduler.start()

    # Уведомление админу
    try:
        await bot.send_message(settings.main.admin_id, "🤖 Бот запущен (webhook).")
    except Exception:
        logger.warning("Admin notify failed", exc_info=True)

    yield

    # --- Shutdown ---
    try:
        await bot.send_message(settings.main.admin_id, "🛑 Бот остановлен.")
    except Exception:
        pass

    await bot.delete_webhook()

    await runtime.close()
