# Configuration and Environment Management Strategy

> 项目配置、环境变量、Docker环境的完整管理方案

**生成日期**: 2025-12-27
**负责人**: planner agent
**版本**: 1.0

---

## 目录

1. [.gitignore配置策略](#gitignore配置策略)
2. [环境变量管理](#环境变量管理)
3. [配置文件层次结构](#配置文件层次结构)
4. [Docker环境配置](#docker环境配置)
5. [.claude/目录保护](#claude目录保护)

---

## .gitignore配置策略

### 完整.gitignore规则

**位置**: `D:\University\Junior\1st\code\signal-paper-analysis\.gitignore`

```gitignore
# ==========================================
# Python (Backend)
# ==========================================
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# pyright
pyrightconfig.json

# ==========================================
# Node.js (Frontend)
# ==========================================
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Next.js
.next/
out/

# Production build
build/

# Testing
coverage/

# Misc
.DS_Store
*.pem

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Local env files
.env*.local

# Vercel
.vercel

# TypeScript
*.tsbuildinfo
next-env.d.ts

# ==========================================
# IDE / Editor
# ==========================================
# VSCode
.vscode/
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace

# PyCharm
.idea/
*.iml
*.iws

# Sublime Text
*.sublime-project
*.sublime-workspace

# Vim
*.swp
*.swo
*~

# Emacs
\#*\#
.\#*

# ==========================================
# Operating System
# ==========================================
# macOS
.DS_Store
.AppleDouble
.LSOverride
Icon
._*

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/

# Linux
*~
.directory

# ==========================================
# Docker
# ==========================================
# Docker volumes
docker-volumes/
*.dockerignore.bak

# ==========================================
# Logs and Temporary Files
# ==========================================
# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Temporary files
tmp/
temp/
*.tmp

# ==========================================
# Environment Variables and Secrets
# ==========================================
# CRITICAL: Never commit these files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Secret files
secrets/
*.secret
*.key
*.pem
credentials.json
service-account.json

# ==========================================
# Build Artifacts and Cache
# ==========================================
# Python
*.pyc
*.pyo
*.pyd

# Node.js
.npm
.eslintcache

# Docker
.dockerignore

# ==========================================
# .claude/ Directory Protection
# ==========================================
# Ignore temporary agent outputs
.claude/temp/
.claude/*.tmp

# Ignore large context dumps
.claude/context-dumps/

# Keep tracked files (commit these):
# .claude/CLAUDE.md
# .claude/commands/
# .claude/agents/
# .claude/docs/
# .claude/progress/

# ==========================================
# Project-Specific
# ==========================================
# Cached API responses (if implementing local cache)
cache/
*.cache

# Large test data files
test-data/large/

# Benchmark results
benchmarks/results/

# ==========================================
# Database (if added in future)
# ==========================================
*.db
*.sqlite
*.sqlite3

# ==========================================
# Miscellaneous
# ==========================================
# Backup files
*.bak
*.backup
```

### 关键说明

1. **环境变量保护**: `.env*` 文件全部忽略，但保留 `.env.example` 作为模板
2. **IDE配置**: 部分VSCode配置保留（settings.json等），方便团队协作
3. **.claude/目录**: 仅忽略临时文件，核心配置文件需要提交
4. **依赖目录**: `node_modules/`, `venv/` 等完全忽略
5. **构建产物**: `.next/`, `dist/`, `build/` 等忽略

---

## 环境变量管理

### .env.example模板

#### Backend (.env.example)

**位置**: `D:\University\Junior\1st\code\signal-paper-analysis\backend\.env.example`

```bash
# ==========================================
# Backend Environment Variables Template
# ==========================================

# ==========================================
# Application Configuration
# ==========================================
APP_NAME=Academic Paper Analysis Tool
APP_VERSION=0.1.0
APP_ENV=development  # Options: development, test, production

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # Set to false in production

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# ==========================================
# External APIs
# ==========================================
# OpenAlex API (no key required, but polite pooling recommended)
OPENALEX_EMAIL=your-email@example.com  # For polite pooling
OPENALEX_BASE_URL=https://api.openalex.org
OPENALEX_RATE_LIMIT=10  # requests per second
OPENALEX_TIMEOUT=30  # seconds

# ==========================================
# Logging
# ==========================================
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # Options: json, text
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# ==========================================
# Performance and Caching
# ==========================================
# Redis (for future caching implementation)
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=  # Leave empty if no password
# CACHE_TTL=3600  # seconds (1 hour)

# ==========================================
# Testing
# ==========================================
PYTEST_VERBOSE=true
PYTEST_COVERAGE_MIN=80  # Minimum coverage percentage

# ==========================================
# Security (Production Only)
# ==========================================
# SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
# API_KEY_HEADER=X-API-Key
# ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# ==========================================
# Database (if added in future)
# ==========================================
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# DATABASE_POOL_SIZE=10
# DATABASE_MAX_OVERFLOW=20

# ==========================================
# Monitoring and Observability
# ==========================================
# SENTRY_DSN=  # Sentry error tracking
# PROMETHEUS_ENABLED=true
# PROMETHEUS_PORT=9090
```

#### Frontend (.env.example)

**位置**: `D:\University\Junior\1st\code\signal-paper-analysis\frontend\.env.example`

```bash
# ==========================================
# Frontend Environment Variables Template
# ==========================================

# ==========================================
# Application Configuration
# ==========================================
NEXT_PUBLIC_APP_NAME=Academic Paper Analysis Tool
NEXT_PUBLIC_APP_VERSION=0.1.0
NODE_ENV=development  # Options: development, test, production

# ==========================================
# API Configuration
# ==========================================
# Backend API base URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000  # milliseconds

# ==========================================
# Feature Flags
# ==========================================
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_DEBUG_MODE=true

# ==========================================
# Graph Visualization Settings
# ==========================================
NEXT_PUBLIC_GRAPH_MAX_NODES=1000
NEXT_PUBLIC_GRAPH_COOLDOWN_TICKS=100
NEXT_PUBLIC_GRAPH_ENGINE_WARMUP_TICKS=0

# ==========================================
# Performance
# ==========================================
NEXT_PUBLIC_DEBOUNCE_DELAY=300  # milliseconds for search input

# ==========================================
# Monitoring (Production Only)
# ==========================================
# NEXT_PUBLIC_SENTRY_DSN=  # Sentry error tracking
# NEXT_PUBLIC_GA_TRACKING_ID=  # Google Analytics

# ==========================================
# Build Configuration
# ==========================================
NEXT_TELEMETRY_DISABLED=1  # Disable Next.js telemetry

# ==========================================
# Testing
# ==========================================
JEST_VERBOSE=true
JEST_COVERAGE_MIN=80
```

### 环境变量命名规范

#### 规则

1. **全大写字母**: `API_PORT`, `LOG_LEVEL`
2. **下划线分隔**: `OPENALEX_BASE_URL`
3. **前缀约定**:
   - `NEXT_PUBLIC_*`: Next.js公开变量（客户端可见）
   - `PYTEST_*`: 测试相关
   - `DATABASE_*`: 数据库相关
4. **敏感信息**: 始终使用 `.env`，永不提交

#### 12-Factor App原则应用

1. **配置与代码分离**: 所有环境特定配置通过环境变量
2. **明确声明依赖**: `.env.example` 记录所有必需变量
3. **无状态进程**: 不依赖本地文件系统存储状态
4. **环境一致性**: development/test/production使用相同代码，不同配置

---

## 配置文件层次结构

### Backend配置架构

#### 文件结构

```
backend/
├── app/
│   └── config/
│       ├── __init__.py
│       ├── base.py              # 基础配置类
│       ├── development.py       # 开发环境
│       ├── test.py              # 测试环境
│       └── production.py        # 生产环境
└── .env
```

#### base.py (基础配置)

```python
"""
基础配置类 - 所有环境共享的配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用基础配置"""

    # 应用信息
    app_name: str = "Academic Paper Analysis Tool"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # API服务器
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["*"]

    # OpenAlex API
    openalex_email: str = ""
    openalex_base_url: str = "https://api.openalex.org"
    openalex_rate_limit: int = 10
    openalex_timeout: int = 30

    # 日志
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/app.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5

    # 测试
    pytest_verbose: bool = True
    pytest_coverage_min: int = 80

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Parse list from comma-separated string
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name == 'cors_origins':
                return [x.strip() for x in raw_val.split(',')]
            return raw_val


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()
```

#### development.py (开发环境)

```python
"""
开发环境配置 - 高日志级别、热重载
"""
from .base import Settings


class DevelopmentSettings(Settings):
    """开发环境配置"""

    app_env: str = "development"
    api_reload: bool = True
    log_level: str = "DEBUG"

    # 开发环境允许所有CORS
    cors_origins: list[str] = ["*"]
```

#### test.py (测试环境)

```python
"""
测试环境配置 - 内存数据库、禁用外部API
"""
from .base import Settings


class TestSettings(Settings):
    """测试环境配置"""

    app_env: str = "test"

    # 测试使用mock，不实际调用外部API
    openalex_base_url: str = "http://mock-api"

    # 测试日志静默
    log_level: str = "ERROR"
```

#### production.py (生产环境)

```python
"""
生产环境配置 - 安全加固、性能优化
"""
from .base import Settings


class ProductionSettings(Settings):
    """生产环境配置"""

    app_env: str = "production"
    api_reload: bool = False

    # 生产环境严格CORS
    cors_origins: list[str] = []  # Must be set via .env

    # 生产日志级别
    log_level: str = "WARNING"

    # 安全配置
    secret_key: str  # 必须设置
    allowed_hosts: list[str] = []  # 必须设置
```

### Frontend配置架构

#### next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // 严格模式（React 18）
  reactStrictMode: true,

  // 输出模式
  output: 'standalone', // Docker优化

  // 环境变量
  env: {
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Academic Paper Analysis Tool',
  },

  // 编译优化
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // 图片优化
  images: {
    domains: [], // 如果需要外部图片
    formats: ['image/webp'],
  },

  // 性能优化
  swcMinify: true,

  // 实验性功能
  experimental: {
    // App Router优化
  },
};

module.exports = nextConfig;
```

---

## Docker环境配置

### 多环境Docker Compose策略

#### docker-compose.yml (开发环境)

**位置**: `D:\University\Junior\1st\code\signal-paper-analysis\docker-compose.yml`

```yaml
version: '3.8'

services:
  # Backend服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development  # 多阶段构建目标
    container_name: paper-analysis-backend-dev
    ports:
      - "8000:8000"
    volumes:
      # 挂载源代码实现热重载
      - ./backend/app:/app/app
      - ./backend/tests:/app/tests
      # 日志持久化
      - ./backend/logs:/app/logs
    environment:
      - APP_ENV=development
      - API_RELOAD=true
      - LOG_LEVEL=DEBUG
      # 从.env文件加载其他变量
    env_file:
      - ./backend/.env
    networks:
      - paper-analysis-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  # Frontend服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    container_name: paper-analysis-frontend-dev
    ports:
      - "3000:3000"
    volumes:
      # 挂载源代码实现热重载
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      # 持久化node_modules (性能优化)
      - frontend-node-modules:/app/node_modules
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    env_file:
      - ./frontend/.env
    networks:
      - paper-analysis-network
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

networks:
  paper-analysis-network:
    driver: bridge
    name: paper-analysis-net

volumes:
  frontend-node-modules:
    name: paper-analysis-frontend-node-modules
```

#### docker-compose.test.yml (CI测试环境)

```yaml
version: '3.8'

services:
  # Backend测试
  backend-test:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: test
    container_name: paper-analysis-backend-test
    environment:
      - APP_ENV=test
      - PYTEST_VERBOSE=true
      - PYTEST_COVERAGE_MIN=80
    volumes:
      - ./backend/coverage:/app/coverage
    networks:
      - test-network
    command: pytest tests/ -v --cov=app --cov-report=html --cov-report=xml

  # Frontend测试
  frontend-test:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: test
    container_name: paper-analysis-frontend-test
    environment:
      - NODE_ENV=test
      - JEST_COVERAGE_MIN=80
    volumes:
      - ./frontend/coverage:/app/coverage
    networks:
      - test-network
    command: npm test -- --coverage --ci

networks:
  test-network:
    driver: bridge
```

#### docker-compose.prod.yml (生产环境)

```yaml
version: '3.8'

services:
  # Backend生产服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: paper-analysis-backend-prod
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - API_RELOAD=false
      - LOG_LEVEL=WARNING
    env_file:
      - ./backend/.env.production
    networks:
      - paper-analysis-prod-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    restart: always
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Frontend生产服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    container_name: paper-analysis-frontend-prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
    env_file:
      - ./frontend/.env.production
    networks:
      - paper-analysis-prod-network
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  # Nginx反向代理（生产环境）
  nginx:
    image: nginx:alpine
    container_name: paper-analysis-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - paper-analysis-prod-network
    depends_on:
      - backend
      - frontend
    restart: always

networks:
  paper-analysis-prod-network:
    driver: bridge
    name: paper-analysis-prod-net
```

### 环境覆盖策略

#### 使用示例

```bash
# 开发环境
docker-compose up -d

# 测试环境
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 生产环境 + 自定义覆盖
docker-compose -f docker-compose.prod.yml -f docker-compose.override.yml up -d
```

---

## .claude/目录保护

### Git追踪策略

#### 应该提交的文件（核心配置）

```
.claude/
├── CLAUDE.md                    # ✅ 提交（项目宪法）
├── commands/                    # ✅ 提交（自定义命令）
│   ├── analyze.json
│   ├── catchup.json
│   ├── review.json
│   └── init-feature.json
├── agents/                      # ✅ 提交（Subagent配置）
│   ├── planner.json
│   ├── researcher.json
│   ├── backend-dev.json
│   ├── frontend-dev.json
│   └── reviewer.json
├── docs/                        # ✅ 提交（架构文档）
│   ├── specs/
│   ├── architecture/
│   └── research/
├── progress/                    # ✅ 提交（进度追踪）
│   └── PROGRESS.md
└── hooks.json                   # ✅ 提交（pre-commit配置）
```

#### 应该忽略的文件（临时/缓存）

```
.claude/
├── temp/                        # ❌ 忽略（临时agent输出）
├── *.tmp                        # ❌ 忽略（临时文件）
├── context-dumps/               # ❌ 忽略（上下文备份）
└── .cache/                      # ❌ 忽略（缓存）
```

### .gitignore规则（.claude/专用）

```gitignore
# .claude/目录保护
.claude/temp/
.claude/*.tmp
.claude/context-dumps/
.claude/.cache/

# 保留核心配置（明确不忽略）
!.claude/CLAUDE.md
!.claude/commands/
!.claude/agents/
!.claude/docs/
!.claude/progress/
!.claude/hooks.json
```

---

## 配置文件示例汇总

### 完整配置文件清单

| 文件路径 | 用途 | 是否提交 |
|---------|------|---------|
| `.gitignore` | Git忽略规则 | ✅ |
| `backend/.env.example` | Backend环境变量模板 | ✅ |
| `backend/.env` | Backend实际环境变量 | ❌ |
| `frontend/.env.example` | Frontend环境变量模板 | ✅ |
| `frontend/.env` | Frontend实际环境变量 | ❌ |
| `docker-compose.yml` | 开发环境Docker | ✅ |
| `docker-compose.test.yml` | 测试环境Docker | ✅ |
| `docker-compose.prod.yml` | 生产环境Docker | ✅ |
| `backend/app/config/` | Python配置模块 | ✅ |
| `frontend/next.config.js` | Next.js配置 | ✅ |

---

## 安全检查清单

### 配置安全验证

- [ ] 所有 `.env` 文件已添加到 `.gitignore`
- [ ] `.env.example` 不包含真实密钥
- [ ] 生产环境 `SECRET_KEY` 使用随机生成值
- [ ] CORS配置严格限制允许的域名
- [ ] 敏感文件（credentials.json, *.key）已忽略
- [ ] Docker镜像不包含 `.env` 文件
- [ ] 环境变量通过 `env_file` 或外部secrets注入

### 环境一致性验证

- [ ] development/test/production使用相同代码
- [ ] 环境差异仅通过配置文件控制
- [ ] 所有环境变量在 `.env.example` 中有文档
- [ ] CI/CD使用 `.env.example` 验证必需变量

---

## 故障排查指南

### 常见配置问题

#### 问题1: Docker Compose启动失败

**症状**: `ERROR: .env file not found`

**解决方案**:
```bash
# 复制示例文件
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 编辑实际值
nano backend/.env
```

#### 问题2: CORS错误

**症状**: Frontend请求被浏览器阻止

**解决方案**:
```bash
# backend/.env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### 问题3: 环境变量未生效

**症状**: 代码读取不到环境变量

**解决方案**:
```python
# 检查 .env 文件是否存在
# 检查 pydantic_settings 是否正确配置
from app.config import get_settings
settings = get_settings()
print(settings.dict())  # 调试输出
```

---

## 验收标准

### 配置管理完整性

- ✅ `.gitignore` 涵盖所有常见文件类型
- ✅ Backend和Frontend都有 `.env.example`
- ✅ 3个Docker Compose文件（dev/test/prod）
- ✅ 配置文件层次结构清晰
- ✅ .claude/目录保护规则明确
- ✅ 安全检查清单完整
- ✅ 故障排查指南可用

---

**记住**: 配置是代码的一部分，必须像代码一样严格管理！
