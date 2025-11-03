"""User service for business logic operations."""

from fastapi import HTTPException, status

from app.data.models import User
from app.data.schemas import UserCreate, UserUpdate
from app.repositories.user import UserRepository
from app.services.base import BaseService


class UserService(BaseService):
    """
    Service for User business logic.

    Responsibilities:
    - Coordinate user operations
    - Enforce user-related business rules
    - Manage transactions

    Follows SOLID principles:
    - Single Responsibility: User-related business logic only
    - Open/Closed: Extensible for new user operations
    """

    @property
    def users(self) -> UserRepository:
        """Lazy-load user repository."""
        if not hasattr(self, "_users"):
            self._users = UserRepository(self.db)
        return self._users

    async def get_user(self, user_id: int) -> User:
        """
        Get user by ID with error handling.

        Args:
            user_id: User ID

        Returns:
            User instance

        Raises:
            HTTPException: If user not found
        """
        user = await self.users.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )
        return user

    async def get_users(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get multiple users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of users
        """
        return await self.users.get_multi(skip=skip, limit=limit)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Add business validation here as needed.

        Args:
            user_data: User creation data

        Returns:
            Created user
        """
        user = await self.users.create(obj_in=user_data)
        await self.commit()
        await self.refresh(user)
        return user

    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
    ) -> User:
        """
        Update an existing user.

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user

        Raises:
            HTTPException: If user not found
        """
        db_user = await self.get_user(user_id)
        updated_user = await self.users.update(db_obj=db_user, obj_in=user_data)
        await self.commit()
        await self.refresh(updated_user)
        return updated_user
