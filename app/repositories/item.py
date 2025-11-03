"""Item repository for data access operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Item
from app.data.schemas import ItemCreate, ItemUpdate
from app.repositories.base import Repository


class ItemRepository(Repository[Item, ItemCreate, ItemUpdate]):
    """
    Repository for Item entity operations.

    Extends base repository with Item-specific queries.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize Item repository.

        Args:
            session: Async database session
        """
        super().__init__(Item, session)

    async def get_by_title(self, title: str) -> Item | None:
        """
        Find an item by exact title match.

        Custom query not available in base repository.

        Args:
            title: Item title to search for

        Returns:
            Item if found, None otherwise
        """
        query = select(self.model).where(self.model.title == title)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_active_items(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        """
        Get all active items with pagination.

        Business rule: Only return items where is_active=True.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active items
        """
        query = (
            select(self.model)
            .where(self.model.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        """
        Get all items owned by a specific user.

        Args:
            owner_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of items owned by the user
        """
        query = select(self.model).where(self.model.owner_id == owner_id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
