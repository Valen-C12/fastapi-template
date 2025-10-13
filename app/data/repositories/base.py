"""
Base Repository Pattern Implementation

Following SOLID principles and clean architecture:
- Single Responsibility: Each repository handles one model
- Open/Closed: Easy to extend with new repositories
- Liskov Substitution: Repositories are interchangeable via interfaces
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depend on abstractions, not concrete implementations
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

# Type variables for generic repository
ModelType = TypeVar("ModelType")


# ============================================================================
# Repository Interface (Interface Segregation Principle)
# ============================================================================


class IRepository(ABC, Generic[ModelType]):
    """
    Abstract repository interface following Interface Segregation Principle.
    Each method has a single, clear responsibility.
    """

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, id: int) -> ModelType | None:
        """Retrieve entity by primary key."""
        pass

    @abstractmethod
    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Retrieve all entities with pagination."""
        pass

    @abstractmethod
    async def create(self, session: AsyncSession, entity: ModelType) -> ModelType:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, session: AsyncSession, entity: ModelType) -> ModelType:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, session: AsyncSession, id: int) -> bool:
        """Delete entity by id."""
        pass

    @abstractmethod
    async def exists(self, session: AsyncSession, id: int) -> bool:
        """Check if entity exists."""
        pass


# ============================================================================
# Specification Pattern (Open/Closed Principle)
# ============================================================================


class ISpecification(ABC, Generic[ModelType]):
    """
    Specification pattern for encapsulating query logic.
    Follows Open/Closed Principle - open for extension, closed for modification.
    """

    @abstractmethod
    def to_sqlalchemy_filter(self) -> ColumnElement[bool] | None:
        """Convert specification to SQLAlchemy filter condition."""
        pass

    def and_(self, other: "ISpecification[ModelType]") -> "ISpecification[ModelType]":
        """Combine specifications with AND logic."""
        return AndSpecification(self, other)

    def or_(self, other: "ISpecification[ModelType]") -> "ISpecification[ModelType]":
        """Combine specifications with OR logic."""
        return OrSpecification(self, other)

    def not_(self) -> "ISpecification[ModelType]":
        """Negate specification."""
        return NotSpecification(self)


class AndSpecification(ISpecification[ModelType]):
    """Composite specification for AND operations."""

    def __init__(self, left: ISpecification[ModelType], right: ISpecification[ModelType]):
        self.left = left
        self.right = right

    def to_sqlalchemy_filter(self) -> ColumnElement[bool] | None:
        left_filter = self.left.to_sqlalchemy_filter()
        right_filter = self.right.to_sqlalchemy_filter()
        if left_filter is None:
            return right_filter
        if right_filter is None:
            return left_filter
        return and_(left_filter, right_filter)


class OrSpecification(ISpecification[ModelType]):
    """Composite specification for OR operations."""

    def __init__(self, left: ISpecification[ModelType], right: ISpecification[ModelType]):
        self.left = left
        self.right = right

    def to_sqlalchemy_filter(self) -> ColumnElement[bool] | None:
        left_filter = self.left.to_sqlalchemy_filter()
        right_filter = self.right.to_sqlalchemy_filter()
        if left_filter is None and right_filter is None:
            return None
        if left_filter is None:
            return right_filter
        if right_filter is None:
            return left_filter
        return or_(left_filter, right_filter)


class NotSpecification(ISpecification[ModelType]):
    """Specification for NOT operations."""

    def __init__(self, spec: ISpecification[ModelType]):
        self.spec = spec

    def to_sqlalchemy_filter(self) -> ColumnElement[bool] | None:
        spec_filter = self.spec.to_sqlalchemy_filter()
        if spec_filter is None:
            return None
        return ~spec_filter


# ============================================================================
# Generic Repository Implementation (DRY Principle)
# ============================================================================


class SQLAlchemyRepository(IRepository[ModelType], Generic[ModelType]):
    """
    Generic SQLAlchemy repository implementation.
    Provides basic CRUD operations for any SQLAlchemy model.
    Follows DRY principle - single implementation used for all models.
    """

    def __init__(self, model_class: type[ModelType]):
        self.model_class = model_class

    async def get_by_id(self, session: AsyncSession, id: int) -> ModelType | None:
        """Get entity by ID with basic eager loading."""
        return await session.get(self.model_class, id)

    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get all entities with pagination."""
        query = select(self.model_class).offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, entity: ModelType) -> ModelType:
        """Create new entity."""
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return entity

    async def update(self, session: AsyncSession, entity: ModelType) -> ModelType:
        """Update existing entity."""
        merged = await session.merge(entity)
        await session.flush()
        await session.refresh(merged)
        return merged

    async def delete(self, session: AsyncSession, id: int) -> bool:
        """Delete entity by ID."""
        entity = await self.get_by_id(session, id)
        if entity:
            await session.delete(entity)
            await session.flush()
            return True
        return False

    async def exists(self, session: AsyncSession, id: int) -> bool:
        """Check if entity exists."""
        query = select(func.count()).select_from(self.model_class).where(getattr(self.model_class, "id") == id)
        result = await session.execute(query)
        count = result.scalar()
        return count is not None and count > 0

    async def find_by_specification(
        self, session: AsyncSession, specification: ISpecification[ModelType], skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Find entities matching specification."""
        query = select(self.model_class)
        spec_filter = specification.to_sqlalchemy_filter()
        if spec_filter is not None:
            query = query.where(spec_filter)
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_by_specification(self, session: AsyncSession, specification: ISpecification[ModelType]) -> int:
        """Count entities matching specification."""
        query = select(func.count(getattr(self.model_class, "id")))
        spec_filter = specification.to_sqlalchemy_filter()
        if spec_filter is not None:
            query = query.where(spec_filter)
        result = await session.execute(query)
        return result.scalar() or 0

    async def get_paginated_with_filters(
        self,
        session: AsyncSession,
        specification: ISpecification[ModelType] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[ModelType], int]:
        """Get paginated results with optional filters and ordering."""
        query = select(self.model_class)
        count_query = select(func.count(getattr(self.model_class, "id")))

        # Apply filters
        if specification:
            filter_condition = specification.to_sqlalchemy_filter()
            if filter_condition is not None:
                query = query.where(filter_condition)
                count_query = count_query.where(filter_condition)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute queries
        result = await session.execute(query)
        count_result = await session.execute(count_query)

        return list(result.scalars().all()), count_result.scalar() or 0
