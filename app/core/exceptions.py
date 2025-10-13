"""
Custom exception classes for the application.

This module defines application-specific exceptions following SOLID principles.
Each exception has a single, clear purpose and is easy to extend.
"""

from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel

# ============================================================================
# Base Exception Classes
# ============================================================================


class ApplicationError(Exception):
    """Base class for all application errors."""

    pass


class DatabaseError(ApplicationError):
    """Base class for database-related errors."""

    pass


# ============================================================================
# Database Exception Classes
# ============================================================================


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class DatabaseTimeoutError(DatabaseError):
    """Raised when database operation times out."""

    pass


class DatabaseConstraintError(DatabaseError):
    """Raised when database constraint is violated."""

    pass


class DatabaseDataError(DatabaseError):
    """Raised when data validation fails in database."""

    pass


class DatabaseOperationError(DatabaseError):
    """Raised when general database operation fails."""

    pass


class DeletionValidationError(DatabaseError):
    """Raised when deletion is prevented due to referential integrity."""

    def __init__(
        self,
        message: str,
        entity_type: str,
        entity_name: str,
        reason: str,
        dependencies: list[dict[str, Any]],
    ):
        super().__init__(message)
        self.entity_type = entity_type
        self.entity_name = entity_name
        self.reason = reason
        self.dependencies = dependencies


# ============================================================================
# Error Response Model
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response model for API responses."""

    error: str
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


# ============================================================================
# HTTP Exception Factory Functions (Following Factory Pattern)
# ============================================================================


def create_http_exception(
    status_code: int,
    error: str,
    message: str,
    field: str | None = None,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """
    Factory function to create HTTP exceptions with standardized error responses.

    Args:
        status_code: HTTP status code
        error: Error code/identifier
        message: Human-readable error message
        field: Optional field name related to the error
        details: Optional additional error details

    Returns:
        HTTPException with structured error response
    """
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            error=error,
            message=message,
            field=field,
            details=details,
        ).model_dump(),
    )


def database_connection_error(message: str | None = None, details: dict[str, Any] | None = None) -> HTTPException:
    """Create HTTP exception for database connection errors."""
    return create_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error="database_connection_error",
        message=message or "Unable to connect to the database. Please try again later.",
        details=details,
    )


def database_timeout_error(message: str | None = None, details: dict[str, Any] | None = None) -> HTTPException:
    """Create HTTP exception for database timeout errors."""
    return create_http_exception(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        error="database_timeout",
        message=message or "Database operation timed out. Please try again.",
        details=details,
    )


def database_constraint_error(
    message: str | None = None,
    field: str | None = None,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """Create HTTP exception for database constraint violations."""
    return create_http_exception(
        status_code=status.HTTP_409_CONFLICT,
        error="constraint_violation",
        message=message or "The operation violates database constraints.",
        field=field,
        details=details,
    )


def database_data_error(
    message: str | None = None,
    field: str | None = None,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """Create HTTP exception for database data errors."""
    return create_http_exception(
        status_code=status.HTTP_400_BAD_REQUEST,
        error="invalid_data",
        message=message or "The provided data is invalid or in the wrong format.",
        field=field,
        details=details,
    )


def database_operation_error(message: str | None = None, details: dict[str, Any] | None = None) -> HTTPException:
    """Create HTTP exception for general database operation errors."""
    return create_http_exception(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="database_error",
        message=message or "An error occurred while processing your request.",
        details=details,
    )


def deletion_validation_error(error: DeletionValidationError) -> HTTPException:
    """Create HTTP exception for deletion validation errors."""
    return create_http_exception(
        status_code=status.HTTP_409_CONFLICT,
        error="deletion_prevented",
        message=str(error),
        field=error.entity_type,
        details={
            "entity_type": error.entity_type,
            "entity_name": error.entity_name,
            "reason": error.reason,
            "dependencies": error.dependencies,
        },
    )


# ============================================================================
# Exception Translation Function (Following Single Responsibility Principle)
# ============================================================================


def translate_db_error_to_http(error: DatabaseError) -> HTTPException:
    """
    Translate database error to HTTP exception.

    This function follows the Open/Closed Principle - open for extension
    by adding new error types, closed for modification of existing logic.

    Args:
        error: Database error to translate

    Returns:
        HTTPException with appropriate status code and error details
    """
    if isinstance(error, DatabaseConnectionError):
        return database_connection_error(details={"original_error": str(error)})

    elif isinstance(error, DatabaseTimeoutError):
        return database_timeout_error(details={"original_error": str(error)})

    elif isinstance(error, DeletionValidationError):
        return deletion_validation_error(error)

    elif isinstance(error, DatabaseConstraintError):
        error_msg = str(error).lower()

        # Handle unique constraint violations
        if "unique constraint" in error_msg or "duplicate key" in error_msg:
            return database_constraint_error(
                message="This item already exists. Please use a different value.",
                details={"original_error": str(error)},
            )

        # Handle foreign key violations
        elif "foreign key constraint" in error_msg:
            return create_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="foreign_key_violation",
                message="This operation references data that doesn't exist.",
                details={"original_error": str(error)},
            )

        # Handle not null constraints
        elif "not null constraint" in error_msg:
            return create_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="required_field_missing",
                message="A required field is missing.",
                details={"original_error": str(error)},
            )

        else:
            return database_constraint_error(details={"original_error": str(error)})

    elif isinstance(error, DatabaseDataError):
        return database_data_error(details={"original_error": str(error)})

    else:  # DatabaseOperationError or unknown
        return database_operation_error(details={"original_error": str(error)})
