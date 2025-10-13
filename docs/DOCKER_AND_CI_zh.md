# Docker 和 CI/CD 设置指南

本指南解释了 FastAPI 模板的 Docker 设置和 GitHub Actions 工作流。

## 📋 目录

- [Docker 设置](#docker-设置)
- [GitHub Actions 工作流](#github-actions-工作流)
- [注册表配置](#注册表配置)
- [本地开发](#本地开发)
- [生产部署](#生产部署)

---

## 🐳 Docker 设置

### 多阶段构建架构

`Dockerfile` 使用多阶段构建模式进行优化:

**阶段 1: 构建器**
- 基础镜像: `python:3.12-alpine`
- 安装构建依赖和 Poetry
- 创建带有生产依赖的虚拟环境
- 通过缓存优化构建速度

**阶段 2: 生产环境**
- 基础镜像: `python:3.12-alpine`
- 只复制虚拟环境和应用代码
- 以非 root 用户 (`appuser`) 运行，确保安全
- 包含健康检查端点
- 最小化运行时依赖

### 本地构建镜像

```bash
# 构建用于本地测试
docker build -t fastapi-template:local .

# 使用缓存优化构建
DOCKER_BUILDKIT=1 docker build -t fastapi-template:local .

# 为特定平台构建
docker build --platform linux/amd64 -t fastapi-template:local .
```

### 本地运行容器

```bash
# 使用环境变量运行
docker run -p 8000:8000 \
  -e PG_HOST=host.docker.internal \
  -e PG_PORT=5432 \
  -e PG_USER=postgres \
  -e PG_PASSWORD=postgres \
  -e PG_DATABASE=template_db \
  -e REDIS_HOST=host.docker.internal \
  -e REDIS_PORT=6379 \
  fastapi-template:local

# 使用 env 文件运行
docker run -p 8000:8000 --env-file .env fastapi-template:local
```

### Docker 镜像优化

镜像经过以下优化:
- **大小**: 多阶段构建减少最终镜像大小约 60%
- **安全**: 以非 root 用户运行，使用 Trivy 扫描
- **性能**: 使用 Alpine Linux 和 Poetry 实现快速构建
- **缓存**: BuildKit 缓存加速重建

**镜像大小对比:**
- 构建阶段: ~800MB (被丢弃)
- 生产阶段: ~250MB (最终镜像)

---

## 🔄 GitHub Actions 工作流

### 1. 持续集成 (`ci.yml`)

在每次推送和拉取请求到 `main` 和 `develop` 分支时运行。

**作业:**

#### **Lint 作业**
- 安装 Poetry 和依赖
- 运行 Ruff 代码检查
- 运行 Ruff 格式检查
- 运行 Pyright 类型检查
- 使用依赖缓存加速

#### **Test 作业**
- 启动 PostgreSQL 和 Redis 服务
- 运行带覆盖率的 pytest
- 测试数据库和 Redis 连接
- 包含健康检查测试

#### **Security Scan 作业**
- 运行 Bandit 安全扫描器
- 上传结果到 GitHub Security 标签
- 识别代码中的安全漏洞

#### **Dependency Check 作业**
- 运行 Safety 检查易受攻击的依赖
- 运行 pip-audit 进行额外的依赖扫描
- 出错时继续，不阻塞构建

**使用方法:**
```yaml
# 自动触发于:
- 推送到 main/develop
- 拉取请求到 main/develop

# 查看结果:
- GitHub Actions 标签
- Pull Request 检查
- Security 标签 (安全扫描)
```

### 2. Docker 构建 (`docker-build.yml`)

在推送到 `main` 和 `develop` 分支时构建和推送 Docker 镜像。

**特性:**
- 多平台构建 (amd64, arm64)
- 支持多个注册表 (GHCR, Docker Hub, AWS ECR)
- 基于分支和提交 SHA 自动标记
- 使用 Trivy 进行安全扫描
- 构建缓存加速构建

**创建的标签:**
```
# main 分支:
- latest
- main
- main-<sha>

# develop 分支:
- develop
- develop-<sha>

# 拉取请求:
- pr-<number>
```

**工作流步骤:**
1. 检出仓库
2. 设置 Docker Buildx
3. 登录容器注册表
4. 提取元数据 (标签, 标签)
5. 构建并推送镜像
6. 运行 Trivy 安全扫描
7. 上传扫描结果到 GitHub Security

---

## 🔐 注册表配置

模板支持多个容器注册表。根据需求选择:

### 选项 1: GitHub Container Registry (GHCR) ⭐ **默认**

**优点:**
- ✅ 公共仓库免费
- ✅ 与 GitHub 集成
- ✅ 无需额外设置
- ✅ 工作流中自动认证

**设置:**
```yaml
# 已在 docker-build.yml 中配置
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

# 镜像将被推送到:
# ghcr.io/your-username/your-repo:latest
```

**所需密钥:** 无 (自动使用 `GITHUB_TOKEN`)

**访问镜像:**
```bash
# 拉取镜像
docker pull ghcr.io/your-username/your-repo:latest

# 登录到 GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
```

---

### 选项 2: Docker Hub

**优点:**
- ✅ 最受欢迎的注册表
- ✅ 易于分享镜像
- ✅ 提供免费层级

**设置:**

1. **创建 Docker Hub 账户** https://hub.docker.com

2. **创建访问令牌:**
   - 进入 Account Settings → Security → New Access Token
   - 复制令牌

3. **添加密钥到 GitHub:**
   - Repository → Settings → Secrets → Actions
   - 添加 `DOCKERHUB_USERNAME` (你的 Docker Hub 用户名)
   - 添加 `DOCKERHUB_TOKEN` (你的访问令牌)

4. **更新 `docker-build.yml`:**
   ```yaml
   # 注释 GHCR 部分，取消注释 Docker Hub 部分:
   - name: Log in to Docker Hub
     if: github.event_name != 'pull_request'
     uses: docker/login-action@v3
     with:
       username: ${{ secrets.DOCKERHUB_USERNAME }}
       password: ${{ secrets.DOCKERHUB_TOKEN }}

   # 更新 env 部分:
   env:
     REGISTRY: docker.io
     IMAGE_NAME: your-dockerhub-username/your-repo-name
   ```

**访问镜像:**
```bash
# 拉取镜像 (公共镜像无需登录)
docker pull your-username/your-repo:latest

# 登录到 Docker Hub
docker login -u your-username
```

---

### 选项 3: AWS ECR (Elastic Container Registry)

**优点:**
- ✅ 与 AWS 服务集成
- ✅ AWS 区域内高性能
- ✅ 细粒度 IAM 权限

**设置:**

1. **创建 ECR 仓库:**
   ```bash
   aws ecr create-repository \
     --repository-name your-repo-name \
     --region us-east-1
   ```

2. **创建具有 ECR 权限的 IAM 用户:**
   - 创建具有 `AmazonEC2ContainerRegistryFullAccess` 策略的用户
   - 生成访问密钥

3. **添加密钥到 GitHub:**
   - Repository → Settings → Secrets → Actions
   - 添加 `AWS_ACCESS_KEY_ID`
   - 添加 `AWS_SECRET_ACCESS_KEY`
   - 添加 `AWS_REGION` (如 `us-east-1`)
   - 添加 `ECR_REPOSITORY` (你的仓库名称)

4. **更新 `docker-build.yml`:**
   ```yaml
   # 注释 GHCR 部分，取消注释 AWS ECR 部分:
   - name: Configure AWS credentials
     if: github.event_name != 'pull_request'
     uses: aws-actions/configure-aws-credentials@v1
     with:
       aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
       aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
       aws-region: ${{ secrets.AWS_REGION }}

   - name: Login to Amazon ECR
     if: github.event_name != 'pull_request'
     id: login-ecr
     uses: aws-actions/amazon-ecr-login@v1

   # 更新 metadata 步骤:
   - name: Extract metadata
     id: meta
     uses: docker/metadata-action@v5
     with:
       images: ${{ steps.login-ecr.outputs.registry }}/${{ secrets.ECR_REPOSITORY }}
   ```

**访问镜像:**
```bash
# 登录到 ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# 拉取镜像
docker pull <account-id>.dkr.ecr.us-east-1.amazonaws.com/your-repo:latest
```

---

## 💻 本地开发

### 使用 Docker Compose (推荐)

为本地开发创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PG_HOST=postgres
      - PG_PORT=5432
      - PG_USER=postgres
      - PG_PASSWORD=postgres
      - PG_DATABASE=template_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app  # 开发期间热重载

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: template_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**命令:**
```bash
# 启动所有服务
docker-compose up

# 重新构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止所有服务
docker-compose down

# 清理卷
docker-compose down -v
```

### 本地测试 Docker 镜像

```bash
# 构建镜像
docker build -t fastapi-template:test .

# 使用 docker-compose 运行
docker-compose up

# 测试健康端点
curl http://localhost:8000/health

# 测试详细健康
curl http://localhost:8000/api/health/detailed
```

---

## 🚀 生产部署

### 前置条件

1. ✅ 选择容器注册表 (GHCR, Docker Hub, 或 AWS ECR)
2. ✅ 设置所需的 GitHub 密钥
3. ✅ 配置环境变量
4. ✅ 设置数据库和 Redis 实例

### 部署步骤

#### 1. 推送到 GitHub

```bash
# 提交更改
git add .
git commit -m "feat: 添加 Docker 和 CI/CD 设置"
git push origin main
```

#### 2. GitHub Actions 自动运行

- 运行 CI 工作流 (lint, test, security scan)
- 构建 Docker 镜像
- 推送到配置的注册表
- 使用 Trivy 扫描镜像

#### 3. 拉取并部署

**使用 Docker:**
```bash
# 拉取最新镜像
docker pull ghcr.io/your-username/your-repo:latest

# 运行容器
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --name fastapi-app \
  ghcr.io/your-username/your-repo:latest
```

**使用 Docker Compose:**
```bash
# 创建生产环境 docker-compose.yml
# 更新 image 使用注册表镜像而不是 build

# 部署
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🎯 最佳实践

### 安全

✅ **以非 root 用户运行** - 已在 Dockerfile 中配置
✅ **扫描镜像** - 工作流中集成了 Trivy 扫描
✅ **使用密钥** - 永不提交凭证
✅ **更新依赖** - 定期安全更新

### 性能

✅ **多阶段构建** - 减少镜像大小
✅ **层缓存** - 加速构建
✅ **健康检查** - 支持容器编排
✅ **资源限制** - 防止资源耗尽

### 可维护性

✅ **版本固定** - Poetry lock 文件
✅ **语义化版本** - 正确标记镜像
✅ **文档** - 保持本指南更新
✅ **CI/CD** - 自动化一切

---

## 📚 其他资源

- [Docker 文档](https://docs.docker.com/)
- [GitHub Actions 文档](https://docs.github.com/zh/actions)
- [Poetry 文档](https://python-poetry.org/docs/)
- [FastAPI 部署](https://fastapi.tiangolo.com/zh/deployment/)

---

**下一步:**
- ✅ 选择容器注册表
- ✅ 配置 GitHub 密钥
- ✅ 推送到 main 分支
- ✅ 验证工作流成功运行
- ✅ 拉取并测试生产镜像
