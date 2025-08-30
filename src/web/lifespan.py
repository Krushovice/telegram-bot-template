from contextlib import asynccontextmanager
from fastapi import FastAPI

from web.runtime import runtime
from core.config import settings
from utils.logger import setup_logging
from core.storage.db_helper import db_helper, test_connection
from middlewares import DbSessionMiddleware, LoggingContextMiddleware

logger = setup_logging(__name__)


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
    async with db_helper.session_factory() as s:
        await test_connection(s)

    # Aiogram DB middleware
    dp.update.outer_middleware(
        DbSessionMiddleware(session_pool=db_helper.session_factory)
    )

    # loging_ctx
    dp.update.outer_middleware(LoggingContextMiddleware())

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
