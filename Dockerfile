# Multi-stage build for production optimization
FROM python:3.12-alpine AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    gcc \
    musl-dev \
    curl

# Install Poetry 2.x
RUN pip install poetry==2.1.4

# Configure Poetry to use in-project virtual environment
RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry config cache-dir /tmp/poetry_cache

# Set environment variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies - Poetry will create .venv in project directory
RUN poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.12-alpine AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies
RUN apk add --no-cache \
    postgresql-client \
    curl \
    bash \
    && addgroup -g 1001 -S appuser \
    && adduser -u 1001 -S appuser -G appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Create directories for logs and ensure proper permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
# Note: Override this in production with proper migration handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
