"""
Unit of Work Pattern Implementation

The Unit of Work pattern maintains a list of objects affected by a business transaction
and coordinates the writing out of changes and the resolution of concurrency problems.

Benefits:
- Centralizes transaction management
- Ensures consistency across multiple repository operations
- Simplifies error handling and rollback logic
"""

from contextlib import asynccontextmanager
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.data.database import AsyncSessionLocal
from app.data.repositories.base import SQLAlchemyRepository

T = TypeVar("T")


# ============================================================================
# Unit of Work Interface
# ============================================================================


class IUnitOfWork:
    """
    Unit of Work interface.
    Defines contract for transaction management.
    """

    async def __aenter__(self):
        """Begin transaction."""
        raise NotImplementedError

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End transaction with commit or rollback."""
        raise NotImplementedError

    async def commit(self):
        """Commit transaction."""
        raise NotImplementedError

    async def rollback(self):
        """Rollback transaction."""
        raise NotImplementedError

    def repository(self, model_class: type[T]) -> Any:
        """Get repository for model class."""
        raise NotImplementedError


# ============================================================================
# SQLAlchemy Unit of Work Implementation
# ============================================================================


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work.
    Manages database transactions and repository lifecycle.

    Usage:
        async with SQLAlchemyUnitOfWork() as uow:
            # Get repository for a model
            user_repo = uow.repository(User)

            # Perform operations
            user = await user_repo.get_by_id(session=uow.session, id=1)
            user.name = "New Name"
            await user_repo.update(session=uow.session, entity=user)

            # Commit (automatic on context exit if no exception)
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        self.session_factory = session_factory or AsyncSessionLocal
        self._repositories: dict[Any, Any] = {}
        self.session: AsyncSession | None = None

    async def __aenter__(self):
        """
        Begin unit of work.
        Creates session and starts transaction.
        """
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        End unit of work.
        Commits on success, rolls back on exception.
        """
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

        if self.session:
            await self.session.close()
        self.session = None
        self._repositories.clear()

    async def commit(self):
        """Commit current transaction."""
        if self.session:
            await self.session.commit()

    async def rollback(self):
        """Rollback current transaction."""
        if self.session:
            await self.session.rollback()

    def repository(self, model_class: type[T]) -> SQLAlchemyRepository[T]:
        """
        Get repository for model class.
        Returns cached repository or creates new one.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            Repository instance for the model
        """
        if model_class not in self._repositories:
            self._repositories[model_class] = SQLAlchemyRepository(model_class)
        return self._repositories[model_class]

    @asynccontextmanager
    async def transaction(self):
        """
        Nested transaction context manager.
        Useful for explicit transaction boundaries within a unit of work.

        Usage:
            async with uow.transaction():
                # Operations within nested transaction
                pass
        """
        if self.session:
            async with self.session.begin_nested():
                yield self.session
        else:
            raise RuntimeError("No active session")


# ============================================================================
# Unit of Work Factory
# ============================================================================


class UnitOfWorkFactory:
    """
    Factory for creating Unit of Work instances.
    Allows dependency injection of session factory.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        self.session_factory = session_factory or AsyncSessionLocal

    def create(self) -> SQLAlchemyUnitOfWork:
        """Create new Unit of Work instance."""
        return SQLAlchemyUnitOfWork(self.session_factory)

    @asynccontextmanager
    async def create_async(self):
        """
        Create Unit of Work in async context.

        Usage:
            factory = UnitOfWorkFactory()
            async with factory.create_async() as uow:
                # Use uow
                pass
        """
        uow = self.create()
        async with uow:
            yield uow
