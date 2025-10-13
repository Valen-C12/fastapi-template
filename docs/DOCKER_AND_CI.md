# Docker and CI/CD Setup Guide

This guide explains the Docker setup and GitHub Actions workflows for the FastAPI template.

## 📋 Table of Contents

- [Docker Setup](#docker-setup)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Registry Configuration](#registry-configuration)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)

---

## 🐳 Docker Setup

### Multi-Stage Build Architecture

The `Dockerfile` uses a multi-stage build pattern for optimization:

**Stage 1: Builder**
- Base image: `python:3.12-alpine`
- Installs build dependencies and Poetry
- Creates virtual environment with production dependencies
- Optimized for build speed with caching

**Stage 2: Production**
- Base image: `python:3.12-alpine`
- Copies only the virtual environment and application code
- Runs as non-root user (`appuser`) for security
- Includes health check endpoint
- Minimal runtime dependencies

### Build the Image Locally

```bash
# Build for local testing
docker build -t fastapi-template:local .

# Build with cache optimization
DOCKER_BUILDKIT=1 docker build -t fastapi-template:local .

# Build for specific platform
docker build --platform linux/amd64 -t fastapi-template:local .
```

### Run the Container Locally

```bash
# Run with environment variables
docker run -p 8000:8000 \
  -e PG_HOST=host.docker.internal \
  -e PG_PORT=5432 \
  -e PG_USER=postgres \
  -e PG_PASSWORD=postgres \
  -e PG_DATABASE=template_db \
  -e REDIS_HOST=host.docker.internal \
  -e REDIS_PORT=6379 \
  fastapi-template:local

# Run with env file
docker run -p 8000:8000 --env-file .env fastapi-template:local
```

### Docker Image Optimization

The image is optimized for:
- **Size**: Multi-stage build reduces final image size by ~60%
- **Security**: Runs as non-root user, scans with Trivy
- **Performance**: Uses Alpine Linux and Poetry for fast builds
- **Cache**: BuildKit caching for faster rebuilds

**Image size comparison:**
- Builder stage: ~800MB (discarded)
- Production stage: ~250MB (final image)

---

## 🔄 GitHub Actions Workflows

### 1. Continuous Integration (`ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**

#### **Lint Job**
- Installs Poetry and dependencies
- Runs Ruff linter
- Runs Ruff formatter check
- Runs Pyright type checker
- Uses dependency caching for speed

#### **Test Job**
- Spins up PostgreSQL and Redis services
- Runs pytest with coverage
- Tests database and Redis connectivity
- Includes health check tests

#### **Security Scan Job**
- Runs Bandit security scanner
- Uploads results to GitHub Security tab
- Identifies security vulnerabilities in code

#### **Dependency Check Job**
- Runs Safety to check for vulnerable dependencies
- Runs pip-audit for additional dependency scanning
- Continues on error to not block builds

**Usage:**
```yaml
# Triggered automatically on:
- push to main/develop
- pull request to main/develop

# View results in:
- GitHub Actions tab
- Pull Request checks
- Security tab (for security scans)
```

### 2. Docker Build (`docker-build.yml`)

Builds and pushes Docker images on push to `main` and `develop` branches.

**Features:**
- Multi-platform builds (amd64, arm64)
- Multiple registry support (GHCR, Docker Hub, AWS ECR)
- Automatic tagging based on branch and commit SHA
- Security scanning with Trivy
- Build caching for faster builds

**Tags Created:**
```
# For main branch:
- latest
- main
- main-<sha>

# For develop branch:
- develop
- develop-<sha>

# For pull requests:
- pr-<number>
```

**Workflow Steps:**
1. Checkout repository
2. Set up Docker Buildx
3. Log in to container registry
4. Extract metadata (tags, labels)
5. Build and push image
6. Run Trivy security scan
7. Upload scan results to GitHub Security

---

## 🔐 Registry Configuration

The template supports multiple container registries. Choose based on your needs:

### Option 1: GitHub Container Registry (GHCR) ⭐ **Default**

**Pros:**
- ✅ Free for public repositories
- ✅ Integrated with GitHub
- ✅ No additional setup needed
- ✅ Automatic authentication in workflows

**Setup:**
```yaml
# Already configured in docker-build.yml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

# Images will be pushed to:
# ghcr.io/your-username/your-repo:latest
```

**Required Secrets:** None (uses `GITHUB_TOKEN` automatically)

**Access Images:**
```bash
# Pull image
docker pull ghcr.io/your-username/your-repo:latest

# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
```

---

### Option 2: Docker Hub

**Pros:**
- ✅ Most popular registry
- ✅ Easy to share images
- ✅ Free tier available

**Setup:**

1. **Create Docker Hub account** at https://hub.docker.com

2. **Create access token:**
   - Go to Account Settings → Security → New Access Token
   - Copy the token

3. **Add secrets to GitHub:**
   - Repository → Settings → Secrets → Actions
   - Add `DOCKERHUB_USERNAME` (your Docker Hub username)
   - Add `DOCKERHUB_TOKEN` (your access token)

4. **Update `docker-build.yml`:**
   ```yaml
   # Comment out GHCR section and uncomment Docker Hub section:
   - name: Log in to Docker Hub
     if: github.event_name != 'pull_request'
     uses: docker/login-action@v3
     with:
       username: ${{ secrets.DOCKERHUB_USERNAME }}
       password: ${{ secrets.DOCKERHUB_TOKEN }}

   # Update env section:
   env:
     REGISTRY: docker.io
     IMAGE_NAME: your-dockerhub-username/your-repo-name
   ```

**Access Images:**
```bash
# Pull image (public images don't need login)
docker pull your-username/your-repo:latest

# Login to Docker Hub
docker login -u your-username
```

---

### Option 3: AWS ECR (Elastic Container Registry)

**Pros:**
- ✅ Integrated with AWS services
- ✅ High performance in AWS regions
- ✅ Fine-grained IAM permissions

**Setup:**

1. **Create ECR repository:**
   ```bash
   aws ecr create-repository \
     --repository-name your-repo-name \
     --region us-east-1
   ```

2. **Create IAM user with ECR permissions:**
   - Create user with `AmazonEC2ContainerRegistryFullAccess` policy
   - Generate access keys

3. **Add secrets to GitHub:**
   - Repository → Settings → Secrets → Actions
   - Add `AWS_ACCESS_KEY_ID`
   - Add `AWS_SECRET_ACCESS_KEY`
   - Add `AWS_REGION` (e.g., `us-east-1`)
   - Add `ECR_REPOSITORY` (your repository name)

4. **Update `docker-build.yml`:**
   ```yaml
   # Comment out GHCR section and uncomment AWS ECR section:
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

   # Update metadata step:
   - name: Extract metadata
     id: meta
     uses: docker/metadata-action@v5
     with:
       images: ${{ steps.login-ecr.outputs.registry }}/${{ secrets.ECR_REPOSITORY }}
   ```

**Access Images:**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Pull image
docker pull <account-id>.dkr.ecr.us-east-1.amazonaws.com/your-repo:latest
```

---

## 💻 Local Development

### Using Docker Compose (Recommended)

Create a `docker-compose.yml` for local development:

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
      - ./app:/app/app  # Hot reload during development

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

**Commands:**
```bash
# Start all services
docker-compose up

# Rebuild and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### Testing Docker Image Locally

```bash
# Build image
docker build -t fastapi-template:test .

# Run with docker-compose
docker-compose up

# Test health endpoint
curl http://localhost:8000/health

# Test detailed health
curl http://localhost:8000/api/health/detailed
```

---

## 🚀 Production Deployment

### Prerequisites

1. ✅ Choose your container registry (GHCR, Docker Hub, or AWS ECR)
2. ✅ Set up required GitHub secrets
3. ✅ Configure environment variables
4. ✅ Set up database and Redis instances

### Deployment Steps

#### 1. Push to GitHub

```bash
# Commit your changes
git add .
git commit -m "feat: add Docker and CI/CD setup"
git push origin main
```

#### 2. GitHub Actions Automatically

- Runs CI workflow (lint, test, security scan)
- Builds Docker image
- Pushes to configured registry
- Scans image with Trivy

#### 3. Pull and Deploy

**Using Docker:**
```bash
# Pull latest image
docker pull ghcr.io/your-username/your-repo:latest

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --name fastapi-app \
  ghcr.io/your-username/your-repo:latest
```

**Using Docker Compose:**
```bash
# Create production docker-compose.yml
# Update image to use registry image instead of build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

**Using Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: ghcr.io/your-username/your-repo:latest
        ports:
        - containerPort: 8000
        env:
        - name: PG_HOST
          value: postgres-service
        # Add other environment variables
```

---

## 🔍 Monitoring and Debugging

### View Workflow Runs

1. Go to **Actions** tab in GitHub
2. Click on a workflow run
3. View logs for each job

### Common Issues

**Issue: Build fails with Poetry error**
```
Solution: Ensure poetry.lock is committed to repository
Command: git add poetry.lock && git commit -m "chore: add poetry.lock"
```

**Issue: Docker build is slow**
```
Solution: Use BuildKit caching
Command: DOCKER_BUILDKIT=1 docker build .
```

**Issue: Security scan finds vulnerabilities**
```
Solution: Update dependencies
Commands:
  poetry update
  poetry show --outdated
  poetry add package@latest
```

**Issue: Image push fails with permission error**
```
Solution: Check registry authentication
- GHCR: Ensure GITHUB_TOKEN has package write permission
- Docker Hub: Verify DOCKERHUB_TOKEN is correct
- ECR: Check AWS IAM permissions
```

### Health Checks

```bash
# Container health
docker ps

# Application health
curl http://localhost:8000/health

# Detailed service health
curl http://localhost:8000/api/health/detailed

# View logs
docker logs <container-id>

# Execute commands in container
docker exec -it <container-id> /bin/bash
```

---

## 📊 Workflow Optimization

### Speed Up Builds

1. **Use Dependency Caching:**
   - GitHub Actions caches Poetry dependencies
   - Docker uses BuildKit layer caching

2. **Parallel Jobs:**
   - CI workflow runs lint, test, and security in parallel
   - Reduces total workflow time

3. **Conditional Execution:**
   - Tests only run on pull requests
   - Docker push only on main/develop branches

### Reduce Costs

1. **GitHub Actions:**
   - Free for public repositories
   - 2,000 minutes/month for private repos

2. **Registry Storage:**
   - GHCR: Free for public
   - Clean up old images regularly

```bash
# Delete old images (GitHub API)
gh api -X DELETE /user/packages/container/your-repo/versions/<version-id>
```

---

## 🎯 Best Practices

### Security

✅ **Run as non-root user** - Already configured in Dockerfile
✅ **Scan images** - Trivy scans integrated in workflow
✅ **Use secrets** - Never commit credentials
✅ **Update dependencies** - Regular security updates

### Performance

✅ **Multi-stage builds** - Reduce image size
✅ **Layer caching** - Speed up builds
✅ **Health checks** - Enable container orchestration
✅ **Resource limits** - Prevent resource exhaustion

### Maintainability

✅ **Version pinning** - Poetry lock file
✅ **Semantic versioning** - Tag images properly
✅ **Documentation** - Keep this guide updated
✅ **CI/CD** - Automate everything

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)

---

## 🆘 Support

If you encounter issues:

1. Check [GitHub Actions logs](../../actions)
2. Review [Security alerts](../../security)
3. Test locally with `docker build` and `docker run`
4. Verify all required secrets are set
5. Check registry-specific documentation

---

**Next Steps:**
- ✅ Choose your container registry
- ✅ Configure GitHub secrets
- ✅ Push to main branch
- ✅ Verify workflows run successfully
- ✅ Pull and test production image
