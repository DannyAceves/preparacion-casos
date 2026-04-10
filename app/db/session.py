from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "search_path": f"{settings.db_schema},public",
        }
    },
)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def configure_db_session(session: AsyncSession) -> None:
    await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.db_schema}"'))
    await session.execute(text(f'SET search_path TO "{settings.db_schema}", public'))


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        await configure_db_session(session)
        yield session
