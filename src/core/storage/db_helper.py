from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)


from core.models import Base

from core.config import settings


class DataBaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        poll_size: int = 5,
        max_overflow: int = 10,
    ):
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=poll_size,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )


db_helper = DataBaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    poll_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)


async def create_tables():
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def test_connection(session: AsyncSession):
    """
    Проверка соединения с СУБД
    :param session: объект AsyncSession
    """
    stmt = select(1)
    return await session.scalar(stmt)