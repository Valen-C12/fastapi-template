from typing import Generic

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.base_crud import CreateSchemaType, CRUDBase, ModelType, UpdateSchemaType
from app.data.database import get_db


class CRUDRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(
        self,
        *,
        crud: CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType],
        schema: type[BaseModel],
        create_schema: type[CreateSchemaType],
        update_schema: type[UpdateSchemaType],
        prefix: str,
        tags: list[str],
        disabled_endpoints: list[str] | None = None,
    ):
        self.crud = crud
        self.schema = schema
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.router = APIRouter(prefix=prefix, tags=list(tags))
        self.disabled_endpoints = disabled_endpoints or []

        self._register_routes()

    def _register_routes(self):
        if "create" not in self.disabled_endpoints:

            @self.router.post(
                "/", response_model=self.schema, status_code=status.HTTP_201_CREATED
            )
            async def create(
                *,
                db: AsyncSession = Depends(get_db),
                # 在静态分析时无法理解这里的动态类型，但 FastAPI 在运行时需要它来生成正确的 API 文档和验证。
                obj_in: self.create_schema,  # type: ignore[misc] # WHY: Pylance sees a variable in a type hint. IMPACT: This is safe; FastAPI resolves the type at runtime.
            ):
                return await self.crud.create(db=db, obj_in=obj_in)

        if "read_multi" not in self.disabled_endpoints:

            @self.router.get("/", response_model=list[self.schema])
            async def read_multi(
                db: AsyncSession = Depends(get_db),
                skip: int = 0,
                limit: int = 100,
            ):
                return await self.crud.get_multi(db, skip=skip, limit=limit)

        if "read_one" not in self.disabled_endpoints:

            @self.router.get("/{id}", response_model=self.schema)
            async def read_one(*, db: AsyncSession = Depends(get_db), id: int):
                db_obj = await self.crud.get(db=db, id=id)
                if not db_obj:
                    raise HTTPException(status_code=404, detail="Resource not found")
                return db_obj

        if "update" not in self.disabled_endpoints:

            @self.router.put("/{id}", response_model=self.schema)
            async def update(
                *,
                db: AsyncSession = Depends(get_db),
                id: int,
                obj_in: self.update_schema,  # type: ignore[misc] # WHY: Pylance sees a variable in a type hint. IMPACT: This is safe; FastAPI resolves the type at runtime.
            ):
                db_obj = await self.crud.get(db=db, id=id)
                if not db_obj:
                    raise HTTPException(status_code=404, detail="Resource not found")
                return await self.crud.update(db=db, db_obj=db_obj, obj_in=obj_in)

        if "delete" not in self.disabled_endpoints:

            @self.router.delete("/{id}", response_model=self.schema)
            async def delete(*, db: AsyncSession = Depends(get_db), id: int):
                db_obj = await self.crud.remove(db=db, id=id)
                if not db_obj:
                    raise HTTPException(status_code=404, detail="Resource not found")
                return db_obj


class ReadOnlyRouter(CRUDRouter):
    def __init__(self, **kwargs):
        # 自动禁用所有写入操作
        super().__init__(disabled_endpoints=["create", "update", "delete"], **kwargs)
