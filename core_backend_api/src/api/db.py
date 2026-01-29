import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_ENGINE: Optional[AsyncEngine] = None
_SESSION_MAKER: Optional[async_sessionmaker[AsyncSession]] = None


# PUBLIC_INTERFACE
def get_database_url() -> str:
    """
    Return the async SQLAlchemy database URL for PostgreSQL.

    Environment variables (set by orchestrator via .env):
    - POSTGRES_URL (recommended): e.g. "postgresql://localhost:5000/myapp"
      or "postgresql://appuser:password@localhost:5000/myapp"

    If POSTGRES_URL is missing, a safe local fallback is used that matches the
    database container template defaults (NOT for production).

    Returns:
        A SQLAlchemy async database URL (driver: asyncpg), e.g.:
        "postgresql+asyncpg://user:pass@host:port/db"
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        # Local template fallback for preview convenience.
        # IMPORTANT: do not use this in production; override via POSTGRES_URL.
        postgres_url = "postgresql://appuser:dbuser123@localhost:5000/myapp"

    # Ensure async driver for SQLAlchemy async engine.
    if postgres_url.startswith("postgresql+asyncpg://"):
        return postgres_url
    if postgres_url.startswith("postgresql://"):
        return postgres_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # If user provided something unexpected, still try to pass through.
    return postgres_url


def _get_engine() -> AsyncEngine:
    """Create (once) and return the SQLAlchemy async engine."""
    global _ENGINE, _SESSION_MAKER
    if _ENGINE is None:
        _ENGINE = create_async_engine(
            get_database_url(),
            echo=False,
            pool_pre_ping=True,
        )
        _SESSION_MAKER = async_sessionmaker(_ENGINE, expire_on_commit=False)
    return _ENGINE


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession.

    Yields:
        AsyncSession bound to the configured engine.
    """
    _get_engine()
    assert _SESSION_MAKER is not None
    async with _SESSION_MAKER() as session:
        yield session
