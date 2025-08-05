from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.data.base_crud import CRUDBase
from app.data.models import Item, User
from app.data.schemas import ItemCreate, ItemUpdate, UserCreate, UserUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    async def get_by_title(self, db: AsyncSession, *, title: str) -> Item | None:
        """
        通过 title 精确查找一个 Item。
        这是一个 CRUDBase 中没有的自定义方法。
        """
        query = select(self.model).where(self.model.title == title)
        result = await db.execute(query)
        return result.scalars().first()


item = CRUDItem(Item)
user = CRUDBase[User, UserCreate, UserUpdate](User)
