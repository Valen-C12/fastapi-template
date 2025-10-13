import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql+psycopg://{settings.pg_user}:{settings.pg_password}@{settings.pg_host}:{settings.pg_port}/{settings.pg_database}"


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Create async engine with optimized connection pool settings
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=5,  # Reduced pool size for better stability
    max_overflow=10,  # Reduced overflow for better resource management
    pool_timeout=30,  # Time to wait for a connection before raising an error
    pool_pre_ping=True,  # Check if the connection is alive before using it
    pool_recycle=3600,  # Recycle connections every hour to prevent stale connections
    future=True,  # Use SQLAlchemy 2.0 style
)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db():
    """
    Get database session with error handling.

    Yields:
        AsyncSession: Database session

    Raises:
        DatabaseConnectionError: If connection fails
        DatabaseOperationError: If session creation fails
    """
    try:
        async with AsyncSessionLocal() as session:
            # Test the connection
            try:
                await session.execute(text("SELECT 1"))
            except SQLAlchemyError as e:
                logger.error("Database connection test failed: %s", str(e))
                raise ConnectionError(f"Failed to establish database connection: {e!s}") from e

            yield session
    except SQLAlchemyError as e:
        logger.error("Database session creation failed: %s", str(e))
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ConnectionError(f"Database connection error: {e!s}") from e
        raise RuntimeError(f"Database operation error: {e!s}") from e


def get_async_db_session() -> AsyncSession:
    """
    Get async database session for manual management.

    Returns:
        AsyncSession: New database session
    """
    return AsyncSessionLocal()
