# FastAPI 生产级模板

[English](README.md) | [简体中文](README_zh.md)

一个生产就绪的 FastAPI 模板，具有现代化架构模式、完善的错误处理和基础设施集成。

## 🌟 特性

### 核心架构
- **仓储模式 (Repository Pattern)** - 清晰的数据访问抽象
- **工作单元模式 (Unit of Work Pattern)** - 协调的事务管理
- **规格模式 (Specification Pattern)** - 灵活的查询组合
- **依赖注入 (Dependency Injection)** - 松耦合组件

### 数据库
- **PostgreSQL** 配合 SQLAlchemy 2.0
- 异步数据库操作
- Alembic 数据库迁移
- 连接池管理 & 健康检查
- 完善的错误处理

### 基础设施集成
- **Redis** - 缓存和会话管理
- **S3/MinIO** - 对象存储与预签名 URL
- 连接池管理和错误恢复

### 代码质量
- **SOLID 原则** - 可维护和可扩展的代码
- **类型提示** - 使用 mypy 和 pyright 的完整类型覆盖
- **代码格式化** - Black & Ruff
- **Pre-commit 钩子** - 自动化代码质量检查
- **约定式提交 (Conventional Commits)** - 标准化提交消息

### 错误处理
- 结构化异常层次
- 用户友好的错误消息
- 数据库错误转换
- 全局异常处理器

## 📋 系统要求

- Python 3.10+
- PostgreSQL 12+
- Redis (可选)
- S3 兼容存储 (可选)

## 🚀 快速开始

### 方式 1: Docker Compose (推荐) 🐳

使用所有服务 (PostgreSQL, Redis, MinIO) 的最快方式:

```bash
# 克隆仓库
git clone <repository-url>
cd template

# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 访问 API
# API: http://localhost:8000
# 文档: http://localhost:8000/docs
# MinIO 控制台: http://localhost:9001 (minioadmin/minioadmin)
```

### 方式 2: 本地开发

### 1. 克隆和设置

```bash
# 克隆仓库
git clone <repository-url>
cd template

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install poetry
poetry install

# 安装 pre-commit 钩子
pre-commit install
```

### 2. 配置

复制示例环境文件并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件设置你的配置：

```env
# 数据库配置
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DATABASE=your_database

# Redis 配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10

# S3 配置（可选）
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_REGION=us-east-1
S3_BUCKET_NAME=my-bucket

# 应用配置
APP_NAME="FastAPI Template"
APP_VERSION="1.0.0"
DEBUG=true
LOG_LEVEL=INFO
```

### 3. 数据库设置

```bash
# 运行迁移
alembic upgrade head

# 创建新的迁移（修改模型后）
alembic revision --autogenerate -m "description"
```

### 4. 运行应用

```bash
# 开发模式
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 将在以下地址可用：
- **API**: http://localhost:8000
- **接口文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 项目结构

```
template/
├── app/
│   ├── api/
│   │   ├── routers/          # API 路由处理器
│   │   │   ├── items.py      # 示例 CRUD 端点
│   │   │   └── users.py      # 用户端点
│   │   └── router_factory.py # 路由生成工具
│   ├── core/
│   │   ├── config.py         # 应用配置
│   │   ├── lifespan.py       # 启动/关闭逻辑
│   │   ├── logging.py        # 日志中间件
│   │   ├── exceptions.py     # 自定义异常类
│   │   └── exception_handlers.py  # 全局异常处理器
│   ├── data/
│   │   ├── database.py       # 数据库连接
│   │   ├── models.py         # SQLAlchemy 模型
│   │   ├── schemas.py        # Pydantic 模式
│   │   ├── crud.py           # CRUD 操作
│   │   ├── base_crud.py      # 基础 CRUD 类
│   │   ├── unit_of_work.py   # 工作单元实现
│   │   └── repositories/     # 仓储模式实现
│   │       ├── base.py       # 基础仓储 & 规格
│   │       └── __init__.py
│   ├── infrastructure/       # 外部服务集成
│   │   ├── redis_client.py   # Redis 连接 & 辅助工具
│   │   └── s3_client.py      # S3 客户端封装
│   └── main.py               # 应用入口点
├── alembic/                  # 数据库迁移
├── .pre-commit-config.yaml   # Pre-commit 钩子
├── pyproject.toml            # 项目配置
└── README.md                 # 本文件
```

## 💡 使用示例

### 使用仓储模式

```python
from app.data.models import Item
from app.data.unit_of_work import SQLAlchemyUnitOfWork

async def create_item_example():
    async with SQLAlchemyUnitOfWork() as uow:
        # 获取 Item 模型的仓储
        item_repo = uow.repository(Item)

        # 创建新项目
        item = Item(name="Example", description="Test item")
        created_item = await item_repo.create(uow.session, item)

        # 退出上下文时自动提交更改

    return created_item
```

### 使用规格模式查询

```python
from app.data.repositories.base import ISpecification
from sqlalchemy.sql.elements import ColumnElement

class ItemNameSpec(ISpecification):
    def __init__(self, name: str):
        self.name = name

    def to_sqlalchemy_filter(self) -> ColumnElement[bool]:
        return Item.name == self.name

# 在仓储中使用
async with SQLAlchemyUnitOfWork() as uow:
    repo = uow.repository(Item)
    spec = ItemNameSpec("test")
    items = await repo.find_by_specification(uow.session, spec)
```

### 使用 Redis

```python
from fastapi import Depends
from app.infrastructure.redis_client import get_redis, Redis

@router.get("/cache-example")
async def cache_example(redis: Redis = Depends(get_redis)):
    # 设置值
    await redis.set("key", "value", ex=3600)  # 1小时后过期

    # 获取值
    value = await redis.get("key")

    return {"value": value}
```

### 使用 S3

```python
from fastapi import Depends, UploadFile
from app.infrastructure.s3_client import get_s3, S3Client

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    s3: S3Client = Depends(get_s3)
):
    # 上传文件
    s3.upload_fileobj(file.file, f"uploads/{file.filename}")

    # 生成预签名 URL（1小时有效期）
    url = s3.generate_presigned_url(f"uploads/{file.filename}")

    return {"url": url}
```

## 🔧 开发

### 代码格式化

```bash
# 使用 Black 和 Ruff 格式化代码
black app/
ruff check app/ --fix
```

### 类型检查

```bash
# 运行类型检查
mypy app/
pyright app/
```

### 测试

```bash
# 运行测试
pytest

# 带覆盖率运行
pytest --cov=app --cov-report=html
```

### Pre-commit 钩子

Pre-commit 钩子会在每次提交前自动运行。手动运行：

```bash
pre-commit run --all-files
```

## 📝 架构原则

### SOLID 原则

- **单一职责原则 (Single Responsibility)**: 每个类只有一个改变的理由
- **开闭原则 (Open/Closed)**: 对扩展开放，对修改关闭
- **里氏替换原则 (Liskov Substitution)**: 子类型可以替换基类型
- **接口隔离原则 (Interface Segregation)**: 客户端特定的接口
- **依赖倒置原则 (Dependency Inversion)**: 依赖抽象而非具体实现

### 设计模式

- **仓储模式 (Repository Pattern)**: 抽象数据访问逻辑
- **工作单元 (Unit of Work)**: 协调多个仓储操作
- **规格模式 (Specification Pattern)**: 封装查询逻辑
- **工厂模式 (Factory Pattern)**: 创建对象而不指定具体类
- **单例模式 (Singleton Pattern)**: 确保单一实例（Redis、S3 客户端）

## 🔍 基础设施测试

测试所有基础设施服务 (数据库, Redis, S3):

```bash
# 运行测试脚本
python test_infrastructure.py

# 或通过 API 检查健康状态
curl http://localhost:8000/api/health/detailed
```

参见 [TESTING_INFRASTRUCTURE_zh.md](TESTING_INFRASTRUCTURE_zh.md) 获取详细测试指南。

## 🐳 Docker 和 CI/CD

### Docker

**生产就绪的多阶段 Dockerfile:**
- 基于 Python 3.12 Alpine
- 最终镜像大小约 250MB
- 以非 root 用户运行
- 包含健康检查

```bash
# 构建镜像
docker build -t fastapi-template .

# 使用 docker-compose 运行 (包含 PostgreSQL, Redis, MinIO)
docker-compose up -d

# 独立运行
docker run -p 8000:8000 --env-file .env fastapi-template
```

### GitHub Actions CI/CD

包含自动化工作流:

**持续集成 (`.github/workflows/ci.yml`)**
- ✅ 使用 Ruff 进行代码检查
- ✅ 使用 Pyright 进行类型检查
- ✅ 使用 pytest 进行测试
- ✅ 使用 Bandit 进行安全扫描
- ✅ 依赖漏洞检查

**Docker 构建 (`.github/workflows/docker-build.yml`)**
- ✅ 多平台构建 (amd64, arm64)
- ✅ 自动标记 (latest, branch, SHA)
- ✅ 使用 Trivy 进行安全扫描
- ✅ 推送到 GHCR, Docker Hub, 或 AWS ECR

参见 [docs/DOCKER_AND_CI_zh.md](docs/DOCKER_AND_CI_zh.md) 获取完整的 Docker 和 CI/CD 文档。

### 环境变量

所有配置通过环境变量完成。查看 `.env.example` 了解所有可用选项。

## 📚 文档

### API 文档
- **Swagger UI**: 访问 `/docs`
- **ReDoc**: 访问 `/redoc`
- **健康检查**: 访问 `/health` 和 `/api/health/detailed`

### 指南
- [TESTING_INFRASTRUCTURE_zh.md](TESTING_INFRASTRUCTURE_zh.md) - 测试数据库、Redis 和 S3
- [docs/DOCKER_AND_CI_zh.md](docs/DOCKER_AND_CI_zh.md) - Docker 设置和 CI/CD 工作流
- [docs/S3_ALTERNATIVES_zh.md](docs/S3_ALTERNATIVES_zh.md) - S3 兼容存储选项

## 🤝 贡献

1. Fork 本仓库
2. 创建功能分支
3. 进行你的修改
4. 运行测试和代码检查
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- FastAPI 框架
- SQLAlchemy ORM
- Pydantic 数据验证
- 所有贡献者和维护者

---

**使用 FastAPI 和现代 Python 实践构建 ❤️**
