"""User repository for data access operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import User
from app.data.schemas import UserCreate, UserUpdate
from app.repositories.base import Repository


class UserRepository(Repository[User, UserCreate, UserUpdate]):
    """
    Repository for User entity operations.

    Currently uses only base repository methods.
    Add custom queries here as needed.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize User repository.

        Args:
            session: Async database session
        """
        super().__init__(User, session)

    # Add custom user-specific queries here as needed
    # Example:
    # async def get_by_email(self, email: str) -> User | None:
    #     query = select(self.model).where(self.model.email == email)
    #     result = await self.session.execute(query)
    #     return result.scalars().first()
