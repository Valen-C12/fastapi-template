"""
Base repository class for data access operations.

Repositories provide an abstraction over database operations, implementing
the Repository pattern to separate data access logic from business logic.

Adheres to:
- Single Responsibility Principle: Only handles data access
- Open/Closed Principle: Extensible through inheritance
- Dependency Inversion Principle: Depends on abstractions (AsyncSession)
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.database import Base

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Repository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic repository for database operations.

    Key principles:
    - No direct commits (managed by service layer)
    - Pure data access logic
    - Type-safe operations

    Usage:
        class ItemRepository(Repository[Item, ItemCreate, ItemUpdate]):
            async def get_by_title(self, title: str) -> Item | None:
                query = select(self.model).where(self.model.title == title)
                result = await self.session.execute(query)
                return result.scalars().first()
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """
        Initialize repository with model and session.

        Args:
            model: SQLAlchemy model class
            session: Async database session (managed by caller)
        """
        self.model = model
        self.session = session

    async def get(self, id: Any) -> ModelType | None:
        """
        Retrieve a single entity by primary key.

        Args:
            id: Primary key value

        Returns:
            Entity if found, None otherwise
        """
        return await self.session.get(self.model, id)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Retrieve multiple entities with pagination.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            List of entities
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new entity.

        Note: Does not commit - caller (service layer) manages transaction.

        Args:
            obj_in: Validated creation schema

        Returns:
            Newly created entity (not yet persisted to DB)
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        self.session.add(db_obj)
        await self.session.flush()  # Flush to get ID without committing
        return db_obj

    async def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        Update an existing entity.

        Note: Does not commit - caller (service layer) manages transaction.

        Args:
            db_obj: Existing entity to update
            obj_in: Update schema or dict with new values (None values excluded)

        Returns:
            Updated entity (not yet persisted to DB)
        """
        # Convert to dict, excluding unset and None values (KISS principle)
        update_data = (
            obj_in.model_dump(exclude_unset=True, exclude_none=True)
            if isinstance(obj_in, BaseModel)
            else {k: v for k, v in obj_in.items() if v is not None}
        )

        # Update only provided fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, *, id: Any) -> ModelType | None:
        """
        Delete an entity by primary key.

        Note: Does not commit - caller (service layer) manages transaction.

        Args:
            id: Primary key value

        Returns:
            Deleted entity if found, None otherwise
        """
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()
        return obj

    async def refresh(self, db_obj: ModelType) -> ModelType:
        """
        Refresh entity from database to get latest state.

        Useful after flush() to get computed values.

        Args:
            db_obj: Entity to refresh

        Returns:
            Refreshed entity
        """
        await self.session.refresh(db_obj)
        return db_obj
