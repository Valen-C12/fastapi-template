"""
FastAPI dependency injection for services.

This module provides dependency functions that FastAPI will use
to inject services into route handlers.

Follows Dependency Inversion Principle:
- Routes depend on service abstractions
- Services are created and managed by FastAPI's DI system
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.database import get_db
from app.services.item_service import ItemService
from app.services.user_service import UserService

# Type aliases for cleaner route signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_item_service(db: DbSession) -> ItemService:
    """
    Create and return ItemService instance.

    FastAPI will:
    1. Call get_db() to get a database session
    2. Pass it to this function
    3. Inject the service into the route handler
    4. Clean up the session after the request

    Args:
        db: Database session from get_db dependency

    Returns:
        ItemService instance
    """
    return ItemService(db)


def get_user_service(db: DbSession) -> UserService:
    """
    Create and return UserService instance.

    Args:
        db: Database session from get_db dependency

    Returns:
        UserService instance
    """
    return UserService(db)


# Type aliases for service dependencies (cleaner route signatures)
ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
