# 基础设施测试指南

[English](TESTING_INFRASTRUCTURE.md) | [简体中文](TESTING_INFRASTRUCTURE_zh.md)

本指南帮助你验证所有基础设施服务（数据库、Redis、S3/MinIO）是否正确配置并正常工作。

## 🎯 快速测试方法

### 方法 1: 命令行测试脚本（推荐）

运行独立测试脚本：

```bash
# 基础使用
python test_infrastructure.py

# 获得更好的输出（先安装 rich）
pip install rich
python test_infrastructure.py
```

**测试内容：**
- ✅ PostgreSQL 数据库连接和查询
- ✅ Redis 连接和操作（SET/GET/DELETE）
- ✅ S3/MinIO 连接和存储桶访问

**示例输出：**
```
🔍 测试基础设施服务

PostgreSQL 数据库: ✅ 通过
  消息: 数据库连接成功
  详细信息:
    • 状态: ✅ 已连接
    • 版本: PostgreSQL 15.3

Redis: ✅ 通过
  消息: Redis 连接成功
  详细信息:
    • 状态: ✅ 已连接
    • 版本: 7.2.0
    • 操作: ✅ SET/GET/DELETE 正常工作

S3/MinIO: ✅ 通过
  消息: S3 连接成功
  详细信息:
    • 状态: ✅ 已连接
    • 存储桶: ✅ 'my-bucket' 存在
```

---

### 方法 2: API 健康检查端点

启动应用并使用健康检查端点：

```bash
# 启动应用
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload
```

然后使用 curl 或浏览器测试：

#### 1. **基础健康检查**
```bash
curl http://localhost:8000/health
```
返回简单状态，不检查服务。

#### 2. **详细健康检查**（所有服务）
```bash
curl http://localhost:8000/health/detailed
```
返回所有服务的完整状态。

**示例响应：**
```json
{
  "status": "healthy",
  "app": "FastAPI Template",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "message": "数据库连接成功",
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
      "message": "Redis 连接成功",
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
      "message": "S3 连接成功",
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

#### 3. **单独服务检查**
```bash
# 仅检查数据库
curl http://localhost:8000/health/database

# 仅检查 Redis
curl http://localhost:8000/health/redis

# 仅检查 S3
curl http://localhost:8000/health/s3
```

#### 4. **Kubernetes 探针**
```bash
# 存活探针（应用正在运行）
curl http://localhost:8000/health/liveness

# 就绪探针（关键服务就绪）
curl http://localhost:8000/health/readiness
```

---

### 方法 3: API 文档交互测试

1. 启动应用：
   ```bash
   python -m app.main
   ```

2. 在浏览器中打开 Swagger UI：
   ```
   http://localhost:8000/docs
   ```

3. 导航到 **health** 部分并交互式测试端点

---

## 🔍 手动服务测试

### PostgreSQL 数据库

```bash
# 使用 psql 测试连接
psql -h localhost -p 5432 -U postgres -d drawer -c "SELECT version();"

# 或使用 Python
python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg://postgres:password@localhost:5432/drawer')
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('数据库正常:', result.scalar())
"
```

### Redis

```bash
# 使用 redis-cli 测试
redis-cli -h localhost -p 6379 ping

# 设置和获取值
redis-cli -h localhost -p 6379 SET test_key "test_value"
redis-cli -h localhost -p 6379 GET test_key
redis-cli -h localhost -p 6379 DEL test_key

# 或使用 Python
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
# 使用 AWS CLI 测试（MinIO 需配置 endpoint）
aws s3 ls --endpoint-url http://localhost:9000

# 列出存储桶内容
aws s3 ls s3://my-bucket --endpoint-url http://localhost:9000

# 上传测试文件
echo "test" > test.txt
aws s3 cp test.txt s3://my-bucket/test.txt --endpoint-url http://localhost:9000

# 下载测试文件
aws s3 cp s3://my-bucket/test.txt downloaded.txt --endpoint-url http://localhost:9000

# 或使用 Python
python -c "
import boto3
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)
print('存储桶:', [b['Name'] for b in s3.list_buckets()['Buckets']])
"
```

---

## 🐛 故障排除

### 数据库连接问题

**问题：** `connection refused` 或 `timeout`

**解决方案：**
1. 检查 PostgreSQL 是否运行：
   ```bash
   # macOS
   brew services list | grep postgresql

   # Linux
   systemctl status postgresql

   # Docker
   docker ps | grep postgres
   ```

2. 验证 `.env` 中的连接详情：
   ```env
   PG_HOST=localhost
   PG_PORT=5432
   PG_USER=postgres
   PG_PASSWORD=your_password
   PG_DATABASE=drawer
   ```

3. 手动测试连接：
   ```bash
   psql -h localhost -p 5432 -U postgres -d drawer
   ```

### Redis 连接问题

**问题：** `Connection refused` 或 `not configured`

**解决方案：**
1. 检查 Redis 是否运行：
   ```bash
   # macOS
   brew services list | grep redis

   # Linux
   systemctl status redis

   # Docker
   docker ps | grep redis
   ```

2. 测试 Redis 连接：
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

3. 如果 Redis 是可选的，可以在没有它的情况下继续（应用会显示 "not_configured"）

### S3/MinIO 连接问题

**问题：** `Unable to locate credentials` 或 `connection refused`

**解决方案：**
1. 对于 MinIO，检查是否运行：
   ```bash
   # Docker
   docker ps | grep minio
   ```

2. 验证 `.env` 中的 S3 配置：
   ```env
   S3_ENDPOINT_URL=http://localhost:9000
   S3_ACCESS_KEY_ID=minioadmin
   S3_SECRET_ACCESS_KEY=minioadmin
   S3_BUCKET_NAME=my-bucket
   ```

3. 如果存储桶不存在，创建它：
   ```bash
   # 使用 AWS CLI 配合 MinIO
   aws s3 mb s3://my-bucket --endpoint-url http://localhost:9000

   # 或通过 MinIO 控制台
   # 在浏览器中打开 http://localhost:9001
   ```

4. 如果 S3 是可选的，可以在没有它的情况下继续（应用会显示 "not_configured"）

---

## 📊 理解状态码

| 状态 | 含义 | 需要的操作 |
|------|------|-----------|
| **healthy** | 服务正常工作 | ✅ 无需操作 |
| **unhealthy** | 服务已配置但无法访问 | ❌ 修复服务连接 |
| **not_configured** | 服务未配置（可选） | ⚠️  可选 - 如需要则配置 |
| **partial** | 服务工作但有问题（如缺少存储桶） | ⚠️  修复配置 |
| **degraded** | 部分服务故障但关键服务正常 | ⚠️  检查可选服务 |

---

## 🚀 Docker Compose 快速启动

如果你想快速启动所有服务进行测试：

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

启动服务：
```bash
docker-compose -f docker-compose.test.yml up -d
```

然后创建 MinIO 存储桶：
```bash
# 安装 mc（MinIO Client）
brew install minio/stable/mc  # macOS
# 或从 https://min.io/download 下载

# 配置
mc alias set local http://localhost:9000 minioadmin minioadmin

# 创建存储桶
mc mb local/my-bucket
```

---

## ✅ 推荐的测试流程

1. **开始开发前：**
   ```bash
   # 测试所有服务
   python test_infrastructure.py
   ```

2. **开发期间：**
   ```bash
   # 启动应用并检查健康端点
   python -m app.main
   curl http://localhost:8000/health/detailed
   ```

3. **生产环境中：**
   - 使用 `/health/readiness` 用于负载均衡器健康检查
   - 使用 `/health/liveness` 用于容器编排
   - 监控 `/health/detailed` 获取完整状态

---

**需要帮助？** 查看主 README.md 或提交 issue。
