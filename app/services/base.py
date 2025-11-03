"""
Base service class for business logic layer.

Services coordinate repositories and manage transactions, implementing
the Service Layer pattern for clean separation of concerns.

Adheres to:
- Single Responsibility Principle: Business logic coordination only
- Dependency Inversion Principle: Depends on abstractions (session, repos)
- Open/Closed Principle: Extensible through inheritance
"""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """
    Base service providing common functionality.

    Responsibilities:
    - Manage database session
    - Coordinate repository operations
    - Handle transaction boundaries (commit/rollback)

    Usage:
        class ItemService(BaseService):
            @property
            def items(self) -> ItemRepository:
                if not hasattr(self, '_items'):
                    self._items = ItemRepository(self.db)
                return self._items

            async def create_item_with_validation(self, data: ItemCreate):
                # Custom business logic
                item = await self.items.create(data)
                await self.commit()
                return item
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async database session (managed by FastAPI dependency)
        """
        self.db = db

    async def commit(self) -> None:
        """
        Commit the current transaction.

        Call this after all repository operations are complete
        to persist changes to the database.
        """
        await self.db.commit()

    async def rollback(self) -> None:
        """
        Rollback the current transaction.

        Use in error handling to revert uncommitted changes.
        """
        await self.db.rollback()

    async def refresh(self, obj) -> None:
        """
        Refresh an object from the database.

        Useful after commit to get server-generated values.

        Args:
            obj: Database model instance to refresh
        """
        await self.db.refresh(obj)
