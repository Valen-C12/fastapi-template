"""
Pydantic schemas for request/response validation.

Explicit schema classes for better type checking and IDE support.
"""

from pydantic import BaseModel, ConfigDict

# ============================================================================
# Item Schemas
# ============================================================================


class ItemBase(BaseModel):
    """Base schema with common Item attributes."""

    title: str
    description: str | None = None
    is_active: bool = True


class ItemCreate(ItemBase):
    """Schema for creating a new Item."""

    pass


class ItemUpdate(BaseModel):
    """
    Schema for updating an Item.

    All fields are optional to support partial updates.
    """

    title: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ItemRead(ItemBase):
    """
    Schema for reading an Item.

    Includes the ID and all base fields.
    """

    id: int
    owner_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# User Schemas
# ============================================================================


class UserBase(BaseModel):
    """Base schema with common User attributes."""

    pass


class UserCreate(UserBase):
    """Schema for creating a new User."""

    pass


class UserUpdate(BaseModel):
    """
    Schema for updating a User.

    All fields are optional to support partial updates.
    """

    pass


class UserRead(UserBase):
    """
    Schema for reading a User.

    Includes the ID and all base fields.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
