# app/core/lifespan.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    在应用启动时执行 yield 之前的代码
    在应用关闭时执行 yield 之后的代码
    """
    logger.info("========== App Startup ==========")
    logger.info("应用开始启动...")

    # 这里是放置启动时逻辑的理想位置，例如：
    # - 初始化数据库连接池
    # - 加载机器学习模型
    # - 连接到消息队列

    yield  # 应用在此处运行

    # 这里是放置关闭时逻辑的理想位置，例如：
    # - 关闭数据库连接池
    # - 清理资源

    logger.info("应用正在关闭...")
    logger.info("========== App Shutdown ==========")
