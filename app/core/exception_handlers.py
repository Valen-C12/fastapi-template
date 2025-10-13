"""
Global exception handlers for the FastAPI application.

This module provides centralized exception handling middleware and handlers
following the Single Responsibility Principle.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    DataError,
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
)
from sqlalchemy.exc import (
    TimeoutError as SQLTimeoutError,
)
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
    DatabaseDataError,
    DatabaseError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    DeletionValidationError,
    translate_db_error_to_http,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Database Error Middleware
# ============================================================================


class DatabaseErrorMiddleware(BaseHTTPMiddleware):
    """Middleware to handle database errors globally."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except DatabaseError as e:
            # Log the error
            logger.error("Database error occurred: %s: %s", type(e).__name__, str(e))

            # Translate to HTTP exception
            http_exception = translate_db_error_to_http(e)

            return JSONResponse(
                status_code=http_exception.status_code,
                content=http_exception.detail,
                headers={"X-Error-Type": "database_error"},
            )


# ============================================================================
# SQLAlchemy Error Mapping
# ============================================================================

# Mapping of SQLAlchemy error types to custom exceptions
ERROR_MAPPING = {
    IntegrityError: DatabaseConstraintError,
    OperationalError: DatabaseConnectionError,
    InterfaceError: DatabaseConnectionError,
    ProgrammingError: DatabaseOperationError,
    DataError: DatabaseDataError,
    SQLTimeoutError: DatabaseTimeoutError,
}


def convert_sqlalchemy_error(error: Exception) -> DatabaseError:
    """
    Convert SQLAlchemy errors to custom database errors.

    Args:
        error: SQLAlchemy exception

    Returns:
        Custom database error
    """
    for error_type, custom_error in ERROR_MAPPING.items():
        if isinstance(error, error_type):
            return custom_error(str(error))

    # If it's already a custom database error, return as-is
    if isinstance(error, DatabaseError):
        return error

    # For unknown errors, wrap as generic database operation error
    return DatabaseOperationError(f"Unexpected database error: {error!s}")


# ============================================================================
# Exception Handler Registration
# ============================================================================


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add global exception handlers to the FastAPI app.

    This function registers handlers for various exception types,
    providing consistent error responses across the application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handler for ValueError exceptions (business logic validation)."""
        logger.warning("Validation error in %s: %s", request.url, str(exc))
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
            headers={"X-Error-Type": "validation_error"},
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        """Handler for all database errors."""
        logger.error("Database error in %s: %s: %s", request.url, type(exc).__name__, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "database_error"},
        )

    @app.exception_handler(DatabaseConnectionError)
    async def database_connection_error_handler(request: Request, exc: DatabaseConnectionError):
        """Handler for database connection errors."""
        logger.error("Database connection error in %s: %s", request.url, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "database_connection_error"},
        )

    @app.exception_handler(DatabaseTimeoutError)
    async def database_timeout_error_handler(request: Request, exc: DatabaseTimeoutError):
        """Handler for database timeout errors."""
        logger.warning("Database timeout in %s: %s", request.url, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "database_timeout_error"},
        )

    @app.exception_handler(DatabaseConstraintError)
    async def database_constraint_error_handler(request: Request, exc: DatabaseConstraintError):
        """Handler for database constraint errors."""
        logger.warning("Database constraint error in %s: %s", request.url, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "database_constraint_error"},
        )

    @app.exception_handler(DatabaseDataError)
    async def database_data_error_handler(request: Request, exc: DatabaseDataError):
        """Handler for database data errors."""
        logger.warning("Database data error in %s: %s", request.url, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "database_data_error"},
        )

    @app.exception_handler(DatabaseOperationError)
    async def database_operation_error_handler(request: Request, exc: DatabaseOperationError):
        """Handler for database operation errors."""
        logger.error("Database operation error in %s: %s", request.url, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "database_operation_error"},
        )

    @app.exception_handler(DeletionValidationError)
    async def deletion_validation_error_handler(request: Request, exc: DeletionValidationError):
        """Handler for deletion validation errors."""
        logger.warning("Deletion validation error in %s: %s", request.url, str(exc))
        http_exception = translate_db_error_to_http(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail,
            headers={"X-Error-Type": "deletion_validation_error"},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        """Handler for Pydantic request validation errors with user-friendly messages."""
        logger.warning("Request validation error in %s: %s", request.url, str(exc))

        # Extract user-friendly error messages
        errors = []
        for error in exc.errors():
            field_name = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
            error_type = error["type"]

            # Provide user-friendly messages for common validation errors
            if error_type == "missing":
                errors.append(f"{field_name} is required")
            elif error_type == "string_type":
                errors.append(f"{field_name} must be a valid string")
            elif error_type == "int_type":
                errors.append(f"{field_name} must be a valid integer")
            elif error_type == "value_error":
                errors.append(f"{field_name} has an invalid value")
            else:
                # Fallback to the original error message
                errors.append(error.get("msg", f"Invalid value for {field_name}"))

        # Return user-friendly error message
        detail = "; ".join(errors) if errors else "Invalid input data"
        return JSONResponse(
            status_code=422,
            content={"detail": detail},
            headers={"X-Error-Type": "validation_error"},
        )
