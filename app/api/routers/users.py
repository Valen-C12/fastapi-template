from app.api.router_factory import CRUDRouter
from app.data import crud
from app.data.schemas import UserCreate, UserRead, UserUpdate

router = CRUDRouter(
    crud=crud.user,
    schema=UserRead,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    prefix="/users",
    tags=["users"],
    disabled_endpoints=["delete"],
).router
