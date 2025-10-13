"""
Health check endpoints for monitoring service availability.

Provides detailed health status for:
- Database (PostgreSQL)
- Redis
- S3/MinIO
- Application
"""

import logging
from typing import Any

from fastapi import APIRouter, status
from sqlalchemy import text

from app.core.config import settings
from app.data.database import get_async_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


# ============================================================================
# Individual Service Health Checks
# ============================================================================


async def check_database() -> dict[str, Any]:
    """
    Check database connectivity and basic query execution.

    Returns:
        dict: Status and details
    """
    try:
        session = get_async_db_session()
        async with session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as health_check"))
            value = result.scalar()

            # Test database version
            version_result = await session.execute(text("SELECT version()"))
            version = version_result.scalar()

            return {
                "status": "healthy",
                "message": "Database connection successful",
                "details": {
                    "health_check": value == 1,
                    "version": version.split(",")[0] if version else "unknown",
                    "host": settings.pg_host,
                    "port": settings.pg_port,
                    "database": settings.pg_database,
                },
            }
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "details": {
                "host": settings.pg_host,
                "port": settings.pg_port,
                "database": settings.pg_database,
            },
        }


async def check_redis() -> dict[str, Any]:
    """
    Check Redis connectivity and basic operations.

    Returns:
        dict: Status and details
    """
    try:
        from app.infrastructure.redis_client import redis_client

        client = redis_client.get_client()

        # Test ping
        await client.ping()

        # Test set/get
        test_key = "__health_check__"
        await client.set(test_key, "ok", ex=10)
        test_value = await client.get(test_key)
        await client.delete(test_key)

        # Get server info
        info = await client.info("server")

        return {
            "status": "healthy",
            "message": "Redis connection successful",
            "details": {
                "ping": True,
                "set_get": test_value == "ok",
                "redis_version": info.get("redis_version", "unknown"),
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
            },
        }
    except RuntimeError as e:
        # Redis not initialized
        logger.warning("Redis not initialized: %s", e)
        return {
            "status": "not_configured",
            "message": "Redis is not configured or enabled",
            "details": {
                "host": settings.redis_host,
                "port": settings.redis_port,
            },
        }
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
            "details": {
                "host": settings.redis_host,
                "port": settings.redis_port,
            },
        }


def check_s3() -> dict[str, Any]:
    """
    Check S3/MinIO connectivity and bucket access.

    Returns:
        dict: Status and details
    """
    try:
        from app.infrastructure.s3_client import s3_client

        client = s3_client.get_client()

        # List buckets to test connection
        response = client.list_buckets()
        buckets = [bucket.get("Name", "") for bucket in response.get("Buckets", []) if "Name" in bucket]

        # Check if configured bucket exists
        bucket_exists = settings.s3_bucket_name in buckets

        return {
            "status": "healthy" if bucket_exists else "partial",
            "message": "S3 connection successful"
            if bucket_exists
            else f"S3 connected but bucket '{settings.s3_bucket_name}' not found",
            "details": {
                "connection": True,
                "bucket_exists": bucket_exists,
                "configured_bucket": settings.s3_bucket_name,
                "available_buckets": buckets[:10],  # Limit to first 10
                "endpoint": settings.s3_endpoint_url or "AWS S3",
                "region": settings.s3_region,
            },
        }
    except RuntimeError as e:
        # S3 not initialized
        logger.warning("S3 not initialized: %s", e)
        return {
            "status": "not_configured",
            "message": "S3 is not configured or enabled",
            "details": {
                "endpoint": settings.s3_endpoint_url or "AWS S3",
                "bucket": settings.s3_bucket_name,
            },
        }
    except Exception as e:
        logger.error("S3 health check failed: %s", e)
        return {
            "status": "unhealthy",
            "message": f"S3 connection failed: {str(e)}",
            "details": {
                "endpoint": settings.s3_endpoint_url or "AWS S3",
                "bucket": settings.s3_bucket_name,
            },
        }


# ============================================================================
# Health Check Endpoints
# ============================================================================


@router.get("/", summary="Basic health check")
async def health_check():
    """
    Basic health check endpoint.
    Returns simple status without checking external services.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/detailed", summary="Detailed health check")
async def detailed_health_check():
    """
    Detailed health check for all services.
    Checks database, Redis, and S3 connectivity.
    """
    db_health = await check_database()
    redis_health = await check_redis()
    s3_health = check_s3()

    # Determine overall status
    critical_services = [db_health]  # Database is critical
    optional_services = [redis_health, s3_health]

    # Check if any critical service is unhealthy
    overall_healthy = all(svc["status"] == "healthy" for svc in critical_services)

    # Count service statuses
    services_status = {
        "healthy": 0,
        "unhealthy": 0,
        "not_configured": 0,
        "partial": 0,
    }

    for svc in critical_services + optional_services:
        services_status[svc["status"]] = services_status.get(svc["status"], 0) + 1

    response = {
        "status": "healthy" if overall_healthy else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "services": {
            "database": db_health,
            "redis": redis_health,
            "s3": s3_health,
        },
        "summary": {
            "total_services": len(critical_services) + len(optional_services),
            "critical_services": len(critical_services),
            "optional_services": len(optional_services),
            "services_status": services_status,
        },
    }

    # Return appropriate status code
    if overall_healthy:
        return response
    elif db_health["status"] == "unhealthy":
        return response, status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        return response


@router.get("/database", summary="Database health check")
async def database_health():
    """Check database connectivity and status."""
    db_health = await check_database()

    if db_health["status"] == "healthy":
        return db_health
    else:
        return db_health, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/redis", summary="Redis health check")
async def redis_health():
    """Check Redis connectivity and status."""
    redis_health = await check_redis()

    if redis_health["status"] in ["healthy", "not_configured"]:
        return redis_health
    else:
        return redis_health, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/s3", summary="S3/MinIO health check")
def s3_health():
    """Check S3/MinIO connectivity and status."""
    s3_health_status = check_s3()

    if s3_health_status["status"] in ["healthy", "partial", "not_configured"]:
        return s3_health_status
    else:
        return s3_health_status, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/liveness", summary="Kubernetes liveness probe")
async def liveness():
    """
    Liveness probe for Kubernetes.
    Returns 200 if application is running.
    """
    return {"status": "alive"}


@router.get("/readiness", summary="Kubernetes readiness probe")
async def readiness():
    """
    Readiness probe for Kubernetes.
    Returns 200 only if critical services (database) are healthy.
    """
    db_health = await check_database()

    if db_health["status"] == "healthy":
        return {"status": "ready", "database": "connected"}
    else:
        return (
            {"status": "not_ready", "reason": "database_unavailable"},
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
