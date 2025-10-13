# app/core/lifespan.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    在应用启动时执行 yield 之前的代码
    在应用关闭时执行 yield 之后的代码
    """
    logger.info("========== App Startup ==========")
    logger.info("应用开始启动...")

    # Initialize database connection and greenlet context
    try:
        # Import here to avoid circular dependency
        from sqlalchemy import text

        from app.data.database import engine, get_async_db_session

        # Create an async session to properly initialize the greenlet context
        session = get_async_db_session()
        async with session:
            # Test the connection to ensure proper greenlet spawning
            await session.execute(text("SELECT 1"))
            logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database connection: %s", e)
        raise

    # Initialize Redis connection (optional)
    try:
        from app.infrastructure.redis_client import redis_client

        await redis_client.connect()
    except Exception as e:
        logger.warning("Redis initialization failed (will continue without Redis): %s", e)

    # Initialize S3 client (optional)
    try:
        from app.infrastructure.s3_client import s3_client

        s3_client.connect()
    except Exception as e:
        logger.warning("S3 initialization failed (will continue without S3): %s", e)

    yield  # 应用在此处运行

    # Clean up resources on shutdown
    logger.info("应用正在关闭...")

    # Close Redis connection
    try:
        from app.infrastructure.redis_client import redis_client

        await redis_client.disconnect()
    except Exception as e:
        logger.error("Error closing Redis connection: %s", e)

    # Close S3 client
    try:
        from app.infrastructure.s3_client import s3_client

        s3_client.disconnect()
    except Exception as e:
        logger.error("Error closing S3 client: %s", e)

    # Close database connections
    try:
        # Import here to avoid circular dependency
        from app.data.database import engine

        # Properly dispose of the engine and close connections
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error("Error during database cleanup: %s", e)

    logger.info("========== App Shutdown ==========")
