# app/main.py

import logging
from importlib import import_module
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.lifespan import lifespan
from app.core.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


# --- 动态路由加载函数 ---
def include_all_routers(app: FastAPI):
    """
    自动包含在 app/api/routers/ 目录下的所有路由。
    """
    router_dir = Path(__file__).parent / "api" / "routers"
    logger.info(f"Searching for routers in: {router_dir}")

    for module_file in router_dir.glob("*.py"):
        if module_file.name == "__init__.py":
            continue

        module_name = f"app.api.routers.{module_file.stem}"
        try:
            module = import_module(module_name)
            if hasattr(module, "router"):
                logger.info(f"Including router from {module_name}")
                app.include_router(
                    module.router,
                    tags=[module_file.stem],
                )
        except Exception as e:
            logger.error(
                f"Failed to import or include router from {module_name}. Error: {e}",
            )


app = FastAPI(
    title="My Production-Ready API",
    description="一个集成了CORS、动态路由和生命周期管理的API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求
    allow_credentials=True,  # 允许携带 cookies
    allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, etc.)
    allow_headers=["*"],  # 允许所有请求头
)
app.add_middleware(LoggingMiddleware)
include_all_routers(app)


@app.get("/")
def read_root():
    """一个简单的根端点，用于健康检查或欢迎信息"""
    return {"status": "ok", "message": "Welcome to the API!"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info",
    )
