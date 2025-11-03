"""
User routes using Service Layer pattern.

This module demonstrates the new architecture with clean separation
of concerns between routes (HTTP), services (business logic), and
repositories (data access).
"""

from fastapi import APIRouter, status

from app.api.dependencies import UserServiceDep
from app.data.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def get_users(
    service: UserServiceDep,
    skip: int = 0,
    limit: int = 100,
):
    """Get all users with pagination."""
    return await service.get_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserServiceDep,
):
    """Get a single user by ID."""
    return await service.get_user(user_id)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserServiceDep,
):
    """Create a new user."""
    return await service.create_user(user_data)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserServiceDep,
):
    """Update an existing user."""
    return await service.update_user(user_id, user_data)


# Note: Delete endpoint intentionally not implemented
# This demonstrates selective endpoint exposure
