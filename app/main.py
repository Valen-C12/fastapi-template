# app/main.py

"""
FastAPI Application Entry Point

This module creates and configures the FastAPI application following best practices:
- Centralized configuration
- Auto-discovery of routers
- Global exception handling
- CORS middleware
- Request logging
- Lifecycle management
"""

import logging
from importlib import import_module
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import add_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


# ============================================================================
# Router Auto-Discovery
# ============================================================================


def include_all_routers(app: FastAPI) -> None:
    """
    Auto-discover and include all routers in app/api/routers/ directory.

    This function follows the Convention over Configuration principle,
    automatically registering all route modules without manual configuration.

    Args:
        app: FastAPI application instance
    """
    router_dir = Path(__file__).parent / "api" / "routers"
    logger.info("Searching for routers in: %s", router_dir)

    if not router_dir.exists():
        logger.warning("Router directory does not exist: %s", router_dir)
        return

    for module_file in router_dir.glob("*.py"):
        if module_file.name == "__init__.py":
            continue

        module_name = f"app.api.routers.{module_file.stem}"
        try:
            module = import_module(module_name)
            if hasattr(module, "router"):
                logger.info("Including router from %s", module_name)
                app.include_router(
                    module.router,
                    tags=[module_file.stem],
                )
            else:
                logger.debug("Module %s has no 'router' attribute, skipping", module_name)
        except Exception as e:
            logger.error("Failed to import or include router from %s: %s", module_name, e, exc_info=True)


# ============================================================================
# Application Factory
# ============================================================================


def create_app() -> FastAPI:
    """
    Application factory function.

    Creates and configures the FastAPI application with all necessary
    middleware, exception handlers, and routes.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="FastAPI template with CRUD, authentication, and infrastructure integrations",
        version=settings.app_version,
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源的请求 (生产环境应该限制)
        allow_credentials=True,  # 允许携带 cookies
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Add exception handlers
    add_exception_handlers(app)

    # Include all routers
    include_all_routers(app)

    # Health check endpoint
    @app.get("/", tags=["health"])
    def read_root():
        """Root endpoint for health check."""
        return {
            "status": "ok",
            "message": f"Welcome to {settings.app_name}!",
            "version": settings.app_version,
        }

    @app.get("/health", tags=["health"])
    def health_check():
        """Detailed health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    return app


# ============================================================================
# Application Instance
# ============================================================================

app = create_app()

# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # noqa: S104  # Binding to all interfaces is intentional for development
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
