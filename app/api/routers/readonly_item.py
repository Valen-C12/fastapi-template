from app.api.router_factory import ReadOnlyRouter
from app.data import crud
from app.data.schemas import ItemCreate, ItemRead, ItemUpdate

router = ReadOnlyRouter(
    crud=crud.item,
    schema=ItemRead,
    create_schema=ItemCreate,
    update_schema=ItemUpdate,
    prefix="/readonly-items",
    tags=["items"],
).router
