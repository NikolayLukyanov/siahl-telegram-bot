"""Database connection management."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession

from src.config import settings
from .models import Base


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine.

    Returns:
        AsyncEngine instance
    """
    # Convert postgres:// to postgresql:// if needed (for compatibility)
    database_url = settings.database_url
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Add asyncpg driver if not present
    if "postgresql://" in database_url and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(
        database_url,
        echo=settings.log_level == "DEBUG",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    return engine


def create_session_pool(engine: AsyncEngine) -> async_sessionmaker:
    """
    Create async session pool.

    Args:
        engine: SQLAlchemy async engine

    Returns:
        async_sessionmaker instance
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def init_db(engine: AsyncEngine) -> None:
    """
    Initialize database tables.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
