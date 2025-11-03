"""Item service for business logic operations."""

from fastapi import HTTPException, status

from app.data.models import Item
from app.data.schemas import ItemCreate, ItemUpdate
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.services.base import BaseService


class ItemService(BaseService):
    """
    Service for Item business logic.

    Responsibilities:
    - Coordinate item operations across repositories
    - Enforce business rules
    - Manage transactions

    Follows SOLID principles:
    - Single Responsibility: Item-related business logic only
    - Open/Closed: Extensible for new item operations
    - Dependency Inversion: Depends on base service and repositories
    """

    @property
    def items(self) -> ItemRepository:
        """Lazy-load item repository."""
        if not hasattr(self, "_items"):
            self._items = ItemRepository(self.db)
        return self._items

    @property
    def users(self) -> UserRepository:
        """Lazy-load user repository for relationship operations."""
        if not hasattr(self, "_users"):
            self._users = UserRepository(self.db)
        return self._users

    async def get_item(self, item_id: int) -> Item:
        """
        Get item by ID with error handling.

        Args:
            item_id: Item ID

        Returns:
            Item instance

        Raises:
            HTTPException: If item not found
        """
        item = await self.items.get(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found",
            )
        return item

    async def get_items(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Item]:
        """
        Get multiple items with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, return only active items

        Returns:
            List of items
        """
        if active_only:
            return await self.items.get_active_items(skip=skip, limit=limit)
        return await self.items.get_multi(skip=skip, limit=limit)

    async def create_item(self, item_data: ItemCreate) -> Item:
        """
        Create a new item with business validation.

        Business rules:
        - Title must be unique (enforced here)

        Args:
            item_data: Item creation data

        Returns:
            Created item

        Raises:
            HTTPException: If title already exists
        """
        # Business rule: Check title uniqueness
        existing_item = await self.items.get_by_title(item_data.title)
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item with title '{item_data.title}' already exists",
            )

        # Create and commit
        item = await self.items.create(obj_in=item_data)
        await self.commit()
        await self.refresh(item)
        return item

    async def update_item(
        self,
        item_id: int,
        item_data: ItemUpdate,
    ) -> Item:
        """
        Update an existing item.

        Business rules:
        - If title is being changed, ensure uniqueness

        Args:
            item_id: Item ID
            item_data: Update data

        Returns:
            Updated item

        Raises:
            HTTPException: If item not found or title conflict
        """
        # Get existing item
        db_item = await self.get_item(item_id)

        # Business rule: If title is changing, check uniqueness
        if item_data.title and item_data.title != db_item.title:
            existing = await self.items.get_by_title(item_data.title)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item with title '{item_data.title}' already exists",
                )

        # Update and commit
        updated_item = await self.items.update(db_obj=db_item, obj_in=item_data)
        await self.commit()
        await self.refresh(updated_item)
        return updated_item

    async def delete_item(self, item_id: int) -> Item:
        """
        Delete an item with business validation.

        Business rules:
        - Cannot delete items with title 'default' (example rule)

        Args:
            item_id: Item ID

        Returns:
            Deleted item

        Raises:
            HTTPException: If item not found or cannot be deleted
        """
        # Get item to delete
        db_item = await self.get_item(item_id)

        # Business rule: Cannot delete default items
        if db_item.title == "default":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Default items cannot be deleted",
            )

        # Delete and commit
        deleted_item = await self.items.delete(id=item_id)
        await self.commit()
        return deleted_item  # type: ignore[return-value]

    async def publish_item(self, item_id: int) -> Item:
        """
        Publish an item (example business operation).

        This demonstrates a business operation that might involve
        multiple steps or validations.

        Args:
            item_id: Item ID

        Returns:
            Published item

        Raises:
            HTTPException: If item not found or already published
        """
        db_item = await self.get_item(item_id)

        # Business logic: Item must be inactive to be published
        if db_item.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item is already published",
            )

        # Mark as active (published)
        db_item.is_active = True
        await self.commit()
        await self.refresh(db_item)
        return db_item

    async def get_items_by_owner(
        self,
        owner_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        """
        Get all items owned by a user.

        Demonstrates cross-repository operation.

        Args:
            owner_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of items owned by the user

        Raises:
            HTTPException: If user not found
        """
        # Validate user exists (cross-repository validation)
        user = await self.users.get(owner_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {owner_id} not found",
            )

        return await self.items.get_by_owner(owner_id, skip=skip, limit=limit)
