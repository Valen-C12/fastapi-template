# Infrastructure Testing Guide

[English](TESTING_INFRASTRUCTURE.md) | [简体中文](TESTING_INFRASTRUCTURE_zh.md)

This guide helps you verify that all infrastructure services (Database, Redis, S3/MinIO) are correctly configured and working.

## 🎯 Quick Test Methods

### Method 1: Command-Line Test Script (Recommended)

Run the standalone test script:

```bash
# Basic usage
python test_infrastructure.py

# With better output (install rich first)
pip install rich
python test_infrastructure.py
```

**What it tests:**
- ✅ PostgreSQL database connection and queries
- ✅ Redis connection and operations (SET/GET/DELETE)
- ✅ S3/MinIO connection and bucket access

**Example Output:**
```
🔍 Testing Infrastructure Services

PostgreSQL Database: ✅ PASS
  Message: Database connection successful
  Details:
    • Status: ✅ Connected
    • Version: PostgreSQL 15.3

Redis: ✅ PASS
  Message: Redis connection successful
  Details:
    • Status: ✅ Connected
    • Version: 7.2.0
    • Operations: ✅ SET/GET/DELETE working

S3/MinIO: ✅ PASS
  Message: S3 connection successful
  Details:
    • Status: ✅ Connected
    • Bucket: ✅ 'my-bucket' exists
```

---

### Method 2: API Health Check Endpoints

Start the application and use the health check endpoints:

```bash
# Start the application
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload
```

Then test using curl or your browser:

#### 1. **Basic Health Check**
```bash
curl http://localhost:8000/health
```
Returns simple status without checking services.

#### 2. **Detailed Health Check** (All Services)
```bash
curl http://localhost:8000/health/detailed
```
Returns comprehensive status of all services.

**Example Response:**
```json
{
  "status": "healthy",
  "app": "FastAPI Template",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful",
      "details": {
        "health_check": true,
        "version": "PostgreSQL 15.3",
        "host": "localhost",
        "port": 5432,
        "database": "drawer"
      }
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful",
      "details": {
        "ping": true,
        "set_get": true,
        "redis_version": "7.2.0",
        "host": "localhost",
        "port": 6379
      }
    },
    "s3": {
      "status": "healthy",
      "message": "S3 connection successful",
      "details": {
        "connection": true,
        "bucket_exists": true,
        "configured_bucket": "my-bucket",
        "available_buckets": ["my-bucket", "test-bucket"]
      }
    }
  }
}
```

#### 3. **Individual Service Checks**
```bash
# Check database only
curl http://localhost:8000/health/database

# Check Redis only
curl http://localhost:8000/health/redis

# Check S3 only
curl http://localhost:8000/health/s3
```

#### 4. **Kubernetes Probes**
```bash
# Liveness probe (app is running)
curl http://localhost:8000/health/liveness

# Readiness probe (critical services are ready)
curl http://localhost:8000/health/readiness
```

---

### Method 3: Interactive Testing with API Docs

1. Start the application:
   ```bash
   python -m app.main
   ```

2. Open Swagger UI in your browser:
   ```
   http://localhost:8000/docs
   ```

3. Navigate to the **health** section and try the endpoints interactively

---

## 🔍 Manual Service Testing

### PostgreSQL Database

```bash
# Test connection with psql
psql -h localhost -p 5432 -U postgres -d drawer -c "SELECT version();"

# Or with Python
python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg://postgres:password@localhost:5432/drawer')
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK:', result.scalar())
"
```

### Redis

```bash
# Test with redis-cli
redis-cli -h localhost -p 6379 ping

# Set and get a value
redis-cli -h localhost -p 6379 SET test_key "test_value"
redis-cli -h localhost -p 6379 GET test_key
redis-cli -h localhost -p 6379 DEL test_key

# Or with Python
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print('Redis PING:', r.ping())
r.set('test', 'value')
print('Redis GET:', r.get('test'))
"
```

### S3/MinIO

```bash
# Test with AWS CLI (for MinIO, configure endpoint)
aws s3 ls --endpoint-url http://localhost:9000

# List bucket contents
aws s3 ls s3://my-bucket --endpoint-url http://localhost:9000

# Upload test file
echo "test" > test.txt
aws s3 cp test.txt s3://my-bucket/test.txt --endpoint-url http://localhost:9000

# Download test file
aws s3 cp s3://my-bucket/test.txt downloaded.txt --endpoint-url http://localhost:9000

# Or with Python
python -c "
import boto3
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)
print('Buckets:', [b['Name'] for b in s3.list_buckets()['Buckets']])
"
```

---

## 🐛 Troubleshooting

### Database Connection Issues

**Problem:** `connection refused` or `timeout`

**Solutions:**
1. Check if PostgreSQL is running:
   ```bash
   # macOS
   brew services list | grep postgresql

   # Linux
   systemctl status postgresql

   # Docker
   docker ps | grep postgres
   ```

2. Verify connection details in `.env`:
   ```env
   PG_HOST=localhost
   PG_PORT=5432
   PG_USER=postgres
   PG_PASSWORD=your_password
   PG_DATABASE=drawer
   ```

3. Test connection manually:
   ```bash
   psql -h localhost -p 5432 -U postgres -d drawer
   ```

### Redis Connection Issues

**Problem:** `Connection refused` or `not configured`

**Solutions:**
1. Check if Redis is running:
   ```bash
   # macOS
   brew services list | grep redis

   # Linux
   systemctl status redis

   # Docker
   docker ps | grep redis
   ```

2. Test Redis connection:
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

3. If Redis is optional, you can continue without it (app will show "not_configured")

### S3/MinIO Connection Issues

**Problem:** `Unable to locate credentials` or `connection refused`

**Solutions:**
1. For MinIO, check if it's running:
   ```bash
   # Docker
   docker ps | grep minio
   ```

2. Verify S3 configuration in `.env`:
   ```env
   S3_ENDPOINT_URL=http://localhost:9000
   S3_ACCESS_KEY_ID=minioadmin
   S3_SECRET_ACCESS_KEY=minioadmin
   S3_BUCKET_NAME=my-bucket
   ```

3. Create bucket if it doesn't exist:
   ```bash
   # Using AWS CLI with MinIO
   aws s3 mb s3://my-bucket --endpoint-url http://localhost:9000

   # Or via MinIO Console
   # Open http://localhost:9001 in browser
   ```

4. If S3 is optional, you can continue without it (app will show "not_configured")

---

## 📊 Understanding Status Codes

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| **healthy** | Service is working correctly | ✅ None |
| **unhealthy** | Service is configured but not accessible | ❌ Fix service connection |
| **not_configured** | Service is not configured (optional) | ⚠️  Optional - configure if needed |
| **partial** | Service works but has issues (e.g., missing bucket) | ⚠️  Fix configuration |
| **degraded** | Some services are down but critical ones work | ⚠️  Check optional services |

---

## 🚀 Docker Compose Quick Start

If you want to quickly start all services for testing:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: drawer
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
```

Start services:
```bash
docker-compose -f docker-compose.test.yml up -d
```

Then create MinIO bucket:
```bash
# Install mc (MinIO Client)
brew install minio/stable/mc  # macOS
# or download from https://min.io/download

# Configure
mc alias set local http://localhost:9000 minioadmin minioadmin

# Create bucket
mc mb local/my-bucket
```

---

## ✅ Recommended Testing Flow

1. **Before starting development:**
   ```bash
   # Test all services
   python test_infrastructure.py
   ```

2. **During development:**
   ```bash
   # Start app and check health endpoint
   python -m app.main
   curl http://localhost:8000/health/detailed
   ```

3. **In production:**
   - Use `/health/readiness` for load balancer health checks
   - Use `/health/liveness` for container orchestration
   - Monitor `/health/detailed` for comprehensive status

---

**Need help?** Check the main README.md or open an issue.
