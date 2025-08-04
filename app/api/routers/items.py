from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router_factory import CRUDRouter
from app.data import crud
from app.data.database import get_db
from app.data.schemas import ItemCreate, ItemRead, ItemUpdate

router = CRUDRouter(
    crud=crud.item,
    schema=ItemRead,
    create_schema=ItemCreate,
    update_schema=ItemUpdate,
    prefix="/items",
    tags=["items"],
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
