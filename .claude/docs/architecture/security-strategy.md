# Security Strategy

> 全面的安全加固方案：认证、CORS、速率限制、依赖安全、HTTPS配置

**生成日期**: 2025-12-27
**负责人**: planner agent
**版本**: 1.0

---

## 目录

1. [API安全](#api安全)
2. [数据安全](#数据安全)
3. [依赖安全](#依赖安全)
4. [网络安全](#网络安全)
5. [安全审计和合规](#安全审计和合规)

---

## API安全

### 认证方案（Phase 4+实施）

#### 方案1: API Key认证（简单场景）

**适用场景**: 内部工具、无需用户账户系统

**实现**:

**位置**: `backend/app/middleware/auth_middleware.py`

```python
"""
API Key认证中间件
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

# API Key Header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    验证API Key

    Raises:
        HTTPException: 如果API Key无效或缺失
    """
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is required. Please include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 验证API Key（生产环境应从数据库或环境变量读取）
    valid_keys = settings.api_keys.split(",")  # 示例: "key1,key2,key3"

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key. Please check your credentials.",
        )

    return api_key


# 使用示例
from fastapi import Depends

@router.get("/api/search", dependencies=[Depends(verify_api_key)])
async def search_papers(query: str):
    """受保护的端点 - 需要API Key"""
    # ...
```

**API Key生成工具**:

```python
import secrets

def generate_api_key(prefix: str = "pak", length: int = 32) -> str:
    """
    生成安全的API Key

    Args:
        prefix: API Key前缀（便于识别）
        length: 密钥长度（字节数）

    Returns:
        格式化的API Key: pak_<random_hex>
    """
    random_bytes = secrets.token_hex(length)
    return f"{prefix}_{random_bytes}"

# 示例
# pak_7f3b4c8e9a1d2f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
```

#### 方案2: JWT Token认证（复杂场景）

**适用场景**: 需要用户账户、会话管理

**实现**:

**位置**: `backend/app/auth/jwt.py`

```python
"""
JWT Token认证
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# 配置
SECRET_KEY = "your-secret-key-here"  # 生产环境从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class TokenData(BaseModel):
    """Token payload数据"""
    username: Optional[str] = None
    exp: Optional[datetime] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT access token

    Args:
        data: 要编码的数据（通常包含用户ID/username）
        expires_delta: 过期时间（可选）

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    从JWT token获取当前用户

    Args:
        token: JWT token

    Returns:
        TokenData: 用户信息

    Raises:
        HTTPException: 如果token无效或过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, exp=payload.get("exp"))

    except JWTError:
        raise credentials_exception

    return token_data


# 使用示例
@router.get("/api/protected")
async def protected_route(current_user: TokenData = Depends(get_current_user)):
    """受JWT保护的端点"""
    return {"message": f"Hello {current_user.username}"}
```

---

### CORS配置细化

#### 动态CORS配置

**位置**: `backend/app/main.py`

```python
"""
FastAPI应用主文件 - 严格CORS配置
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

app = FastAPI(title="Academic Paper Analysis API")
settings = get_settings()


def configure_cors(app: FastAPI):
    """
    配置CORS中间件

    开发环境: 允许localhost
    生产环境: 严格限制到指定域名
    """
    # 从环境变量读取允许的origins
    origins = settings.cors_origins

    # 开发环境特殊处理
    if settings.app_env == "development":
        origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 生产环境严格验证
    elif settings.app_env == "production":
        if not origins or origins == ["*"]:
            raise ValueError(
                "CORS_ORIGINS must be explicitly set in production! "
                "Wildcard '*' is not allowed."
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
        max_age=600,  # 预检请求缓存时间（秒）
    )


configure_cors(app)
```

#### 预检请求优化

```python
from fastapi import Request, Response


@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    """
    优化预检请求处理

    返回快速响应，减少OPTIONS请求延迟
    """
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": request.headers.get(
                "access-control-request-headers", "*"
            ),
            "Access-Control-Max-Age": "600",
        },
    )
```

---

### 速率限制

#### 基于IP的请求限流

**位置**: `backend/app/middleware/rate_limit_middleware.py`

```python
"""
速率限制中间件 - 防止滥用和DDoS
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单的内存速率限制器

    生产环境建议使用Redis实现分布式限流
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)  # {ip: [timestamp, ...]}
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查端点
        if request.url.path in ["/api/health", "/api/health/ready", "/api/health/live"]:
            return await call_next(request)

        # 获取客户端IP
        client_ip = request.client.host

        # 检查速率限制
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)

        # 清理过期记录
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if timestamp > one_minute_ago
        ]

        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute. "
                       f"Please try again in {60 - (now - self.requests[client_ip][0]).seconds} seconds.",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((self.requests[client_ip][0] + timedelta(minutes=1)).timestamp())),
                }
            )

        # 记录请求
        self.requests[client_ip].append(now)

        # 添加速率限制响应头
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_ip])
        )

        return response

    async def _cleanup_loop(self):
        """定期清理过期数据"""
        while True:
            await asyncio.sleep(300)  # 每5分钟清理一次
            now = datetime.utcnow()
            one_minute_ago = now - timedelta(minutes=1)

            for ip in list(self.requests.keys()):
                self.requests[ip] = [
                    timestamp for timestamp in self.requests[ip]
                    if timestamp > one_minute_ago
                ]
                if not self.requests[ip]:
                    del self.requests[ip]


# 添加到FastAPI应用
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
```

#### Redis分布式限流（生产级）

```python
"""
基于Redis的分布式速率限制
"""
import redis.asyncio as aioredis
from fastapi import Request, HTTPException, status


class RedisRateLimiter:
    """Redis滑动窗口速率限制器"""

    def __init__(self, redis_url: str, requests_per_minute: int = 60):
        self.redis = aioredis.from_url(redis_url)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 秒

    async def check_rate_limit(self, client_ip: str) -> bool:
        """
        检查是否超过速率限制

        Returns:
            True: 允许请求
            False: 超过限制
        """
        key = f"rate_limit:{client_ip}"
        now = int(datetime.utcnow().timestamp())

        # 使用Redis sorted set实现滑动窗口
        async with self.redis.pipeline() as pipe:
            # 移除过期记录
            pipe.zremrangebyscore(key, 0, now - self.window_size)
            # 统计当前窗口内请求数
            pipe.zcard(key)
            # 添加当前请求
            pipe.zadd(key, {str(now): now})
            # 设置过期时间
            pipe.expire(key, self.window_size)

            results = await pipe.execute()

        current_requests = results[1]

        return current_requests < self.requests_per_minute

    async def get_remaining(self, client_ip: str) -> int:
        """获取剩余请求配额"""
        key = f"rate_limit:{client_ip}"
        now = int(datetime.utcnow().timestamp())

        await self.redis.zremrangebyscore(key, 0, now - self.window_size)
        current = await self.redis.zcard(key)

        return max(0, self.requests_per_minute - current)
```

---

## 数据安全

### 敏感信息保护

#### 环境变量加密

**使用dotenv-vault（推荐）**:

```bash
# 安装
npm install -g dotenv-vault

# 初始化
dotenv-vault new

# 加密环境变量
dotenv-vault encrypt

# 生成.env.vault文件（可安全提交到git）
# 实际密钥存储在DOTENV_KEY中（不提交）
```

#### Secrets管理（Docker/Kubernetes）

**Docker Secrets**:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: paper-analysis-backend:latest
    secrets:
      - openalex_api_key
      - secret_key
    environment:
      - OPENALEX_API_KEY_FILE=/run/secrets/openalex_api_key
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  openalex_api_key:
    file: ./secrets/openalex_api_key.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

**读取Docker Secrets**:

```python
def load_secret(secret_name: str, default: str = "") -> str:
    """
    从Docker Secret或环境变量加载密钥

    Args:
        secret_name: Secret名称
        default: 默认值

    Returns:
        Secret值
    """
    import os

    # 尝试从Docker Secret文件读取
    secret_file = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_file):
        with open(secret_file) as f:
            return f.read().strip()

    # 回退到环境变量
    env_var = secret_name.upper()
    return os.getenv(env_var, default)


# 使用
openalex_key = load_secret("openalex_api_key")
```

---

### HTTPS强制

#### Nginx HTTPS配置

**nginx/nginx.conf**:

```nginx
# HTTP -> HTTPS重定向
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 强制HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS配置
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL证书
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # SSL协议和密码套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    # HSTS (强制HTTPS, 1年)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # 其他安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # 代理到Backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 代理到Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Let's Encrypt自动证书

**certbot自动续期**:

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期（添加到crontab）
0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 依赖安全

### 漏洞扫描

#### Backend: pip-audit

**安装**:
```bash
pip install pip-audit
```

**使用**:
```bash
# 扫描当前环境
pip-audit

# 扫描requirements.txt
pip-audit -r requirements.txt

# 自动修复
pip-audit --fix
```

**CI集成** (`.github/workflows/security.yml`):

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  backend-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pip-audit

      - name: Run pip-audit
        run: pip-audit -r backend/requirements.txt --format json --output audit-report.json

      - name: Upload audit report
        uses: actions/upload-artifact@v3
        with:
          name: backend-audit-report
          path: audit-report.json
```

#### Frontend: npm audit

**使用**:
```bash
# 扫描漏洞
npm audit

# 自动修复（仅修复兼容更新）
npm audit fix

# 强制修复（可能破坏兼容性）
npm audit fix --force
```

**CI集成**:

```yaml
frontend-security:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run npm audit
      run: npm audit --audit-level=moderate
```

#### Docker镜像扫描（Trivy）

**安装Trivy**:
```bash
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
```

**使用**:
```bash
# 扫描Docker镜像
trivy image paper-analysis-backend:latest

# 输出为JSON
trivy image --format json --output trivy-report.json paper-analysis-backend:latest

# 仅显示HIGH和CRITICAL漏洞
trivy image --severity HIGH,CRITICAL paper-analysis-backend:latest
```

**CI集成**:

```yaml
docker-security:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: docker build -t paper-analysis-backend:latest backend/

    - name: Run Trivy scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: paper-analysis-backend:latest
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

---

### 依赖更新策略

#### Dependabot配置

**.github/dependabot.yml**:

```yaml
version: 2
updates:
  # Backend Python依赖
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "your-username"
    labels:
      - "dependencies"
      - "backend"
    commit-message:
      prefix: "chore(deps)"

  # Frontend npm依赖
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "your-username"
    labels:
      - "dependencies"
      - "frontend"
    commit-message:
      prefix: "chore(deps)"

  # Docker基础镜像
  - package-ecosystem: "docker"
    directory: "/backend"
    schedule:
      interval: "weekly"
    reviewers:
      - "your-username"
    labels:
      - "dependencies"
      - "docker"
```

---

## 网络安全

### DDoS防护策略

#### Cloudflare集成（推荐）

**配置步骤**:
1. 添加域名到Cloudflare
2. 启用"Under Attack Mode"（受到攻击时）
3. 配置Rate Limiting规则
4. 启用Bot Fight Mode

**Cloudflare Rate Limiting规则**:
```json
{
  "description": "API rate limit",
  "match": {
    "request": {
      "url": {
        "path": {
          "contains": "/api/"
        }
      }
    }
  },
  "action": {
    "mode": "challenge",
    "timeout": 86400
  },
  "threshold": 100,
  "period": 60
}
```

#### 应用层DDoS防护

**Nginx限流配置**:

```nginx
# 限制连接数
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
limit_conn conn_limit_per_ip 10;

# 限制请求速率
limit_req_zone $binary_remote_addr zone=req_limit_per_ip:10m rate=10r/s;
limit_req zone=req_limit_per_ip burst=20 nodelay;

server {
    location /api/ {
        # 应用限流
        limit_conn conn_limit_per_ip 10;
        limit_req zone=req_limit_per_ip burst=20 nodelay;

        # 超过限制返回429
        limit_req_status 429;
        limit_conn_status 429;

        proxy_pass http://backend:8000;
    }
}
```

---

## 安全审计和合规

### OWASP Top 10检查清单

| 漏洞类型 | 缓解措施 | 实施状态 |
|---------|---------|---------|
| **A01: Broken Access Control** | JWT/API Key认证, RBAC | Phase 4 |
| **A02: Cryptographic Failures** | HTTPS强制, 密钥加密存储 | ✅ 已规划 |
| **A03: Injection** | Pydantic验证, 参数化查询 | ✅ 已实施 |
| **A04: Insecure Design** | 安全架构审查 | ✅ 已规划 |
| **A05: Security Misconfiguration** | 严格CORS, 安全headers | ✅ 已规划 |
| **A06: Vulnerable Components** | pip-audit, npm audit, Trivy | ✅ 已规划 |
| **A07: Authentication Failures** | JWT过期, 速率限制 | Phase 4 |
| **A08: Software/Data Integrity** | 依赖锁定, Docker镜像签名 | Phase 4 |
| **A09: Logging Failures** | 结构化日志, 审计日志 | ✅ 已实施 |
| **A10: SSRF** | 输入验证, 白名单 | ✅ 已实施 |

### 安全审计日志

**位置**: `backend/app/middleware/audit_middleware.py`

```python
"""
安全审计日志中间件
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

audit_logger = logging.getLogger("security_audit")


class AuditMiddleware(BaseHTTPMiddleware):
    """记录所有敏感操作的审计日志"""

    async def dispatch(self, request: Request, call_next):
        # 记录敏感操作
        if self._is_sensitive_operation(request):
            audit_logger.info(
                "Sensitive operation",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                    "user_id": getattr(request.state, "user_id", None),
                }
            )

        response = await call_next(request)
        return response

    def _is_sensitive_operation(self, request: Request) -> bool:
        """判断是否为敏感操作"""
        sensitive_paths = ["/api/admin", "/api/auth"]
        return any(request.url.path.startswith(path) for path in sensitive_paths)
```

---

## 验收标准

### 安全完整性检查

- ✅ 认证方案设计完成（API Key + JWT）
- ✅ CORS配置严格限制
- ✅ 速率限制实现（内存 + Redis）
- ✅ 环境变量加密方案
- ✅ HTTPS强制配置
- ✅ Let's Encrypt自动续期
- ✅ pip-audit/npm audit集成
- ✅ Trivy Docker扫描
- ✅ Dependabot配置
- ✅ DDoS防护策略
- ✅ OWASP Top 10缓解措施
- ✅ 安全审计日志

---

**记住**: 安全是持续的过程，不是一次性的任务！定期审查和更新安全措施。
