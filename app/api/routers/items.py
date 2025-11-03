"""
Item routes using Service Layer pattern.

This module demonstrates the new architecture:
- Thin controllers (routes only handle HTTP concerns)
- Business logic in services
- Data access in repositories

Migration from old CRUD factory pattern to Service Layer.
"""

from fastapi import APIRouter, status

from app.api.dependencies import ItemServiceDep
from app.data.schemas import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=list[ItemRead])
async def get_items(
    service: ItemServiceDep,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
):
    """
    Get all items with optional filtering.

    Query params:
    - skip: Number of items to skip (pagination)
    - limit: Maximum number of items to return
    - active_only: If true, return only active items
    """
    return await service.get_items(skip=skip, limit=limit, active_only=active_only)


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int,
    service: ItemServiceDep,
):
    """Get a single item by ID."""
    return await service.get_item(item_id)


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    service: ItemServiceDep,
):
    """
    Create a new item.

    Business rules (enforced in service layer):
    - Title must be unique
    """
    return await service.create_item(item_data)


@router.put("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    service: ItemServiceDep,
):
    """
    Update an existing item.

    Business rules (enforced in service layer):
    - If title is changed, must be unique
    """
    return await service.update_item(item_id, item_data)


@router.delete("/{item_id}", response_model=ItemRead)
async def delete_item(
    item_id: int,
    service: ItemServiceDep,
):
    """
    Delete an item.

    Business rules (enforced in service layer):
    - Cannot delete items with title 'default'
    """
    return await service.delete_item(item_id)


@router.post("/{item_id}/publish", response_model=ItemRead)
async def publish_item(
    item_id: int,
    service: ItemServiceDep,
):
    """
    Publish an item (mark as active).

    This demonstrates a custom business operation beyond basic CRUD.
    """
    return await service.publish_item(item_id)


@router.get("/owner/{owner_id}", response_model=list[ItemRead])
async def get_items_by_owner(
    owner_id: int,
    service: ItemServiceDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all items owned by a specific user.

    This demonstrates cross-entity operations coordinated by the service layer.
    """
    return await service.get_items_by_owner(owner_id, skip=skip, limit=limit)
