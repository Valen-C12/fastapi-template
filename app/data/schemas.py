from pydantic import BaseModel

from app.data.schema_factory import create_dynamic_schemas


class ItemBase(BaseModel):
    title: str
    description: str | None = None
    is_active: bool = True


ItemCreate, ItemUpdate, ItemRead = create_dynamic_schemas(ItemBase)


class UserBase(BaseModel):
    pass


UserCreate, UserUpdate, UserRead = create_dynamic_schemas(UserBase)
