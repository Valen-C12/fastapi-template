# FastAPI Production Template

[English](README.md) | [简体中文](README_zh.md)

A production-ready FastAPI template with modern architecture patterns, comprehensive error handling, and infrastructure integrations.

## 🌟 Features

### Core Architecture
- **Service Layer Pattern** - Business logic coordination and transaction management
- **Repository Pattern** - Clean data access abstraction
- **Dependency Injection** - Loosely coupled components via FastAPI DI
- **SOLID Principles** - Maintainable, testable, and extensible code

### Database
- **PostgreSQL** with SQLAlchemy 2.0
- Async database operations
- Alembic migrations
- Connection pooling & health checks
- Comprehensive error handling

### Infrastructure Integrations
- **Redis** - Caching and session management
- **S3/MinIO** - Object storage with presigned URLs
- Connection pooling and error recovery

### Code Quality
- **SOLID Principles** - Maintainable and extensible code
- **Type Hints** - Full type coverage with mypy & pyright
- **Code Formatting** - Black & Ruff
- **Pre-commit Hooks** - Automated code quality checks
- **Conventional Commits** - Standardized commit messages

### Error Handling
- Structured exception hierarchy
- User-friendly error messages
- Database error translation
- Global exception handlers

## 📋 Requirements

- Python 3.10+
- PostgreSQL 12+
- Redis (optional)
- S3-compatible storage (optional)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended) 🐳

The fastest way to get started with all services (PostgreSQL, Redis, MinIO):

```bash
# Clone the repository
git clone <repository-url>
cd template

# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Access the API
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
```

### Option 2: Local Development

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd template

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install

# Install pre-commit hooks
pre-commit install
```

### 2. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database Configuration
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DATABASE=your_database

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10

# S3 Configuration (Optional)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_REGION=us-east-1
S3_BUCKET_NAME=my-bucket

# Application Configuration
APP_NAME="FastAPI Template"
APP_VERSION="1.0.0"
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Database Setup

```bash
# Run migrations
alembic upgrade head

# Create a new migration (after model changes)
alembic revision --autogenerate -m "description"
```

### 4. Run the Application

```bash
# Development mode
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
template/
├── app/
│   ├── api/
│   │   ├── routers/          # API route handlers (thin controllers)
│   │   │   ├── items.py      # Item endpoints
│   │   │   ├── users.py      # User endpoints
│   │   │   └── health.py     # Health check endpoints
│   │   └── dependencies.py   # Service dependency injection
│   ├── core/
│   │   ├── config.py         # Application configuration
│   │   ├── lifespan.py       # Startup/shutdown logic
│   │   ├── logging.py        # Logging middleware
│   │   ├── exceptions.py     # Custom exception classes
│   │   └── exception_handlers.py  # Global exception handlers
│   ├── services/             # Service Layer (business logic)
│   │   ├── base.py           # Base service with transaction management
│   │   ├── item_service.py   # Item business logic
│   │   └── user_service.py   # User business logic
│   ├── repositories/         # Repository Layer (data access)
│   │   ├── base.py           # Generic repository base class
│   │   ├── item.py           # Item repository
│   │   └── user.py           # User repository
│   ├── data/
│   │   ├── database.py       # Database connection & session
│   │   ├── models.py         # SQLAlchemy models
│   │   └── schemas.py        # Pydantic schemas (Create/Update/Read)
│   ├── infrastructure/       # External service integrations
│   │   ├── redis_client.py   # Redis connection & helpers
│   │   └── s3_client.py      # S3 client wrapper
│   └── main.py               # Application entry point
├── alembic/                  # Database migrations
├── .pre-commit-config.yaml   # Pre-commit hooks
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## 💡 Usage Examples

### Architecture Overview

This template follows the **Service Layer Pattern** for clean separation of concerns:

```
┌─────────────────────────────────────────┐
│         Routes (HTTP Layer)             │
│  - Thin controllers                     │
│  - HTTP concerns only                   │
│  - Depend on services via DI            │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Service Layer                      │
│  - Business logic                       │
│  - Transaction management               │
│  - Coordinates repositories             │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Repository Layer                   │
│  - Data access abstraction              │
│  - No commits (delegated to services)   │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Database (SQLAlchemy)              │
└─────────────────────────────────────────┘
```

### Creating a New Route

```python
# app/api/routers/items.py
from fastapi import APIRouter
from app.api.dependencies import ItemServiceDep
from app.data.schemas import ItemCreate, ItemRead

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemRead, status_code=201)
async def create_item(
    item_data: ItemCreate,
    service: ItemServiceDep,  # Service injected via FastAPI DI
):
    """Create a new item with business validation."""
    return await service.create_item(item_data)

@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, service: ItemServiceDep):
    """Get item by ID."""
    return await service.get_item(item_id)
```

### Creating a Service

```python
# app/services/item_service.py
from app.services.base import BaseService
from app.repositories.item import ItemRepository

class ItemService(BaseService):
    @property
    def items(self) -> ItemRepository:
        """Lazy-load item repository."""
        if not hasattr(self, "_items"):
            self._items = ItemRepository(self.db)
        return self._items

    async def create_item(self, item_data: ItemCreate) -> Item:
        """Create item with business validation."""
        # Business rule: Check title uniqueness
        existing = await self.items.get_by_title(item_data.title)
        if existing:
            raise HTTPException(400, "Title already exists")

        # Create and commit
        item = await self.items.create(obj_in=item_data)
        await self.commit()
        await self.refresh(item)
        return item
```

### Creating a Repository

```python
# app/repositories/item.py
from app.repositories.base import Repository
from app.data.models import Item
from app.data.schemas import ItemCreate, ItemUpdate

class ItemRepository(Repository[Item, ItemCreate, ItemUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Item, session)

    # Add custom queries
    async def get_by_title(self, title: str) -> Item | None:
        query = select(self.model).where(self.model.title == title)
        result = await self.session.execute(query)
        return result.scalars().first()
```

### Cross-Repository Operations

```python
# app/services/item_service.py
class ItemService(BaseService):
    @property
    def items(self) -> ItemRepository:
        if not hasattr(self, "_items"):
            self._items = ItemRepository(self.db)
        return self._items

    @property
    def users(self) -> UserRepository:
        if not hasattr(self, "_users"):
            self._users = UserRepository(self.db)
        return self._users

    async def create_item_with_owner(
        self,
        item_data: ItemCreate,
        user_id: int
    ) -> Item:
        """Create item with owner validation (cross-repository)."""
        # Validate user exists
        user = await self.users.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        # Create item
        item_data_dict = item_data.model_dump()
        item_data_dict["owner_id"] = user_id
        item = await self.items.create(ItemCreate(**item_data_dict))

        # Atomic commit
        await self.commit()
        await self.refresh(item)
        return item
```

### Using Redis

```python
from fastapi import Depends
from app.infrastructure.redis_client import get_redis, Redis

@router.get("/cache-example")
async def cache_example(redis: Redis = Depends(get_redis)):
    # Set value
    await redis.set("key", "value", ex=3600)  # Expires in 1 hour

    # Get value
    value = await redis.get("key")

    return {"value": value}
```

### Using S3

```python
from fastapi import Depends, UploadFile
from app.infrastructure.s3_client import get_s3, S3Client

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    s3: S3Client = Depends(get_s3)
):
    # Upload file
    s3.upload_fileobj(file.file, f"uploads/{file.filename}")

    # Generate presigned URL (valid for 1 hour)
    url = s3.generate_presigned_url(f"uploads/{file.filename}")

    return {"url": url}
```

## 🔧 Development

### Code Formatting

```bash
# Format code with Black and Ruff
black app/
ruff check app/ --fix
```

### Type Checking

```bash
# Run type checking
mypy app/
pyright app/
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit. To run manually:

```bash
pre-commit run --all-files
```

## 📝 Architecture Principles

### SOLID Principles

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes are substitutable for base types
- **Interface Segregation**: Client-specific interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

### Design Patterns

- **Service Layer Pattern**: Coordinates business logic and transaction boundaries
- **Repository Pattern**: Abstracts data access logic
- **Dependency Injection**: FastAPI's built-in DI for loose coupling
- **Factory Pattern**: Creates objects without specifying exact classes (e.g., schema factory)
- **Singleton Pattern**: Ensures single instance (Redis, S3 clients)

## 🔍 Infrastructure Testing

Test all infrastructure services (Database, Redis, S3):

```bash
# Run the test script
python test_infrastructure.py

# Or check health via API
curl http://localhost:8000/api/health/detailed
```

See [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) for detailed testing guide.

## 🐳 Docker & CI/CD

### Docker

**Multi-stage production-ready Dockerfile:**
- Based on Python 3.12 Alpine
- ~250MB final image size
- Runs as non-root user
- Includes health checks

```bash
# Build image
docker build -t fastapi-template .

# Run with docker-compose (includes PostgreSQL, Redis, MinIO)
docker-compose up -d

# Run standalone
docker run -p 8000:8000 --env-file .env fastapi-template
```

### GitHub Actions CI/CD

Automated workflows included:

**Continuous Integration (`.github/workflows/ci.yml`)**
- ✅ Linting with Ruff
- ✅ Type checking with Pyright
- ✅ Testing with pytest
- ✅ Security scanning with Bandit
- ✅ Dependency vulnerability checks

**Docker Build (`.github/workflows/docker-build.yml`)**
- ✅ Multi-platform builds (amd64, arm64)
- ✅ Automatic tagging (latest, branch, SHA)
- ✅ Security scanning with Trivy
- ✅ Push to GHCR, Docker Hub, or AWS ECR

See [docs/DOCKER_AND_CI.md](docs/DOCKER_AND_CI.md) for complete Docker and CI/CD documentation.

### Environment Variables

All configuration is done via environment variables. See `.env.example` for all available options.

## 📚 Documentation

### API Documentation
- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **Health Check**: Available at `/health` and `/api/health/detailed`

### Guides
- [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) - Testing database, Redis, and S3
- [docs/DOCKER_AND_CI.md](docs/DOCKER_AND_CI.md) - Docker setup and CI/CD workflows
- [docs/S3_ALTERNATIVES.md](docs/S3_ALTERNATIVES.md) - S3-compatible storage options

### Architecture

**Service Layer Architecture**
- Modern pattern following FastAPI best practices
- Clear separation: Routes → Services → Repositories → Database
- Explicit transaction management in services
- Easy to test and maintain
- SOLID principles throughout

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- FastAPI framework
- SQLAlchemy ORM
- Pydantic for data validation
- All contributors and maintainers

---

**Built with ❤️ using FastAPI and modern Python practices**
