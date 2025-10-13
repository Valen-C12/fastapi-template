from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router_factory import CRUDRouter
from app.data import crud
from app.data.database import get_db
from app.data.schemas import ItemCreate, ItemRead, ItemUpdate


async def check_item_deletable(id: int, db: AsyncSession = Depends(get_db)):
    """
    一个依赖项，用于在删除 Item 前执行特殊校验。
    如果校验失败，它会抛出 HTTP 异常。
    如果成功，它什么也不做，请求会继续向下执行。
    """
    print(f"Executing special delete check for item {id}...")

    # 示例校验逻辑 1: 从数据库获取 item
    item = await crud.item.get(db, id=id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 示例校验逻辑 2: 假设我们不允许删除标题为 "default" 的项目
    if item.title == "default":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Default items cannot be deleted.")

    return item


router = CRUDRouter(
    crud=crud.item,
    schema=ItemRead,
    create_schema=ItemCreate,
    update_schema=ItemUpdate,
    prefix="/items",
    tags=["items"],
    dependencies={"delete": [Depends(check_item_deletable)]},
).router


@router.post("/{item_id}/publish", response_model=ItemRead)
async def publish_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    print(f"Publishing item {item_id}...")
    db_item = await crud.item.get(db=db, id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    # ... 在这里执行发布的逻辑 ...
    return db_item
