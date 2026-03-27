from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from leek.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create tables. In production, use Alembic migrations instead."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Enable WAL mode for SQLite
    if "sqlite" in settings.database_url:
        async with engine.begin() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("PRAGMA journal_mode=WAL")
            )


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
