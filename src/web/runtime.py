from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from typing import Optional

from core.config import settings
from utils.logging import setup_logger
from routers import register_routers
from utils.scheduler import schedule_tasks

logger = setup_logger(__name__)


class Runtime:
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.redis: Optional[Redis] = None
        self.scheduler = None

    async def build(self) -> "Runtime":
        # Bot
        self.bot = Bot(
            token=settings.bot.token,
            default=DefaultBotProperties(parse_mode=settings.bot.parse_mode),
        )

        # Storage: Redis → предпочтительно; иначе Memory
        if getattr(settings, "redis", None):
            self.redis = Redis.from_url(
                settings.redis.url,
                decode_responses=settings.redis.decode_responses,
            )
            storage = RedisStorage(
                redis=self.redis,
                state_ttl=172800,
                data_ttl=172800,
            )
        else:
            storage = MemoryStorage()

        # Dispatcher
        self.dp = Dispatcher(storage=storage)

        # Подключаем твои aiogram-роутеры тут (команды/сцены/прочее)
        register_routers(self.dp)

        # Планировщик задач
        self.scheduler = schedule_tasks(self.bot)

        return self

    async def close(self):
        if self.scheduler and getattr(self.scheduler, "running", False):
            self.scheduler.shutdown()

        if self.bot:
            await self.bot.session.close()

        if self.redis:
            await self.redis.close()


runtime = Runtime()
