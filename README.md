# FastAPI Production Template

[English](README.md) | [简体中文](README_zh.md)

A production-ready FastAPI template with modern architecture patterns, comprehensive error handling, and infrastructure integrations.

## 🌟 Features

### Core Architecture
- **Repository Pattern** - Clean data access abstraction
- **Unit of Work Pattern** - Coordinated transaction management
- **Specification Pattern** - Flexible query composition
- **Dependency Injection** - Loosely coupled components

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
│   │   ├── routers/          # API route handlers
│   │   │   ├── items.py      # Example CRUD endpoints
│   │   │   └── users.py      # User endpoints
│   │   └── router_factory.py # Router generation utilities
│   ├── core/
│   │   ├── config.py         # Application configuration
│   │   ├── lifespan.py       # Startup/shutdown logic
│   │   ├── logging.py        # Logging middleware
│   │   ├── exceptions.py     # Custom exception classes
│   │   └── exception_handlers.py  # Global exception handlers
│   ├── data/
│   │   ├── database.py       # Database connection
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── crud.py           # CRUD operations
│   │   ├── base_crud.py      # Base CRUD class
│   │   ├── unit_of_work.py   # Unit of Work implementation
│   │   └── repositories/     # Repository pattern implementations
│   │       ├── base.py       # Base repository & specifications
│   │       └── __init__.py
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

### Using Repository Pattern

```python
from app.data.models import Item
from app.data.unit_of_work import SQLAlchemyUnitOfWork

async def create_item_example():
    async with SQLAlchemyUnitOfWork() as uow:
        # Get repository for Item model
        item_repo = uow.repository(Item)

        # Create new item
        item = Item(name="Example", description="Test item")
        created_item = await item_repo.create(uow.session, item)

        # Changes committed automatically on context exit

    return created_item
```

### Using Specifications for Queries

```python
from app.data.repositories.base import ISpecification
from sqlalchemy.sql.elements import ColumnElement

class ItemNameSpec(ISpecification):
    def __init__(self, name: str):
        self.name = name

    def to_sqlalchemy_filter(self) -> ColumnElement[bool]:
        return Item.name == self.name

# Use in repository
async with SQLAlchemyUnitOfWork() as uow:
    repo = uow.repository(Item)
    spec = ItemNameSpec("test")
    items = await repo.find_by_specification(uow.session, spec)
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

- **Repository Pattern**: Abstracts data access logic
- **Unit of Work**: Coordinates multiple repository operations
- **Specification Pattern**: Encapsulates query logic
- **Factory Pattern**: Creates objects without specifying exact classes
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
