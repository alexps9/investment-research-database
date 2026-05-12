# Monitoring and Logging Strategy

> 全面的应用日志、性能监控、健康检查和可观测性方案

**生成日期**: 2025-12-27
**负责人**: planner agent
**版本**: 1.0

---

## 目录

1. [应用日志设计](#应用日志设计)
2. [性能监控](#性能监控)
3. [健康检查和可观测性](#健康检查和可观测性)
4. [日志聚合和可视化](#日志聚合和可视化)
5. [告警和通知](#告警和通知)

---

## 应用日志设计

### Backend日志（Python logging）

#### 日志级别策略

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| **DEBUG** | 开发调试信息 | 函数参数、中间变量值 |
| **INFO** | 正常业务流程 | API请求成功、任务完成 |
| **WARNING** | 潜在问题，但不影响运行 | OpenAlex API慢响应、缓存未命中 |
| **ERROR** | 错误但可恢复 | API调用失败、数据解析错误 |
| **CRITICAL** | 严重错误，系统不可用 | 数据库连接失败、核心服务崩溃 |

#### 结构化日志（JSON格式）

**位置**: `backend/app/utils/logger.py`

```python
"""
结构化日志工具 - JSON格式输出
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义JSON日志格式化器"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """添加自定义字段到日志记录"""
        super().add_fields(log_record, record, message_dict)

        # 添加时间戳（ISO 8601格式）
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # 添加日志级别
        log_record['level'] = record.levelname

        # 添加服务名称
        log_record['service'] = 'paper-analysis-backend'

        # 添加请求上下文（如果存在）
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id


def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> logging.Logger:
    """
    配置应用日志

    Args:
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        log_file: 日志文件路径（可选，默认仅输出到stdout）

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger("paper_analysis")
    logger.setLevel(log_level)

    # 清除现有handlers（避免重复）
    logger.handlers.clear()

    # JSON格式化器
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler（如果指定）
    if log_file:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局logger实例
logger = setup_logging()
```

#### 日志上下文（请求追踪）

**位置**: `backend/app/middleware/logging_middleware.py`

```python
"""
日志中间件 - 为每个请求添加追踪ID
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging
import time


class LoggingMiddleware(BaseHTTPMiddleware):
    """添加请求ID和性能追踪的日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始
        logger = logging.getLogger("paper_analysis")
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host,
            }
        )

        # 记录开始时间
        start_time = time.time()

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            # 记录未捕获异常
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "exception": str(e),
                    "exception_type": type(e).__name__,
                },
                exc_info=True
            )
            raise

        # 计算响应时间
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

        return response
```

#### 业务日志示例

**位置**: `backend/app/services/openalex_client.py`

```python
import logging
from typing import List
from app.models.schemas import Paper

logger = logging.getLogger("paper_analysis")


async def fetch_papers(query: str, limit: int = 50) -> List[Paper]:
    """
    从OpenAlex API获取论文

    透明日志记录所有关键步骤
    """
    logger.info(
        "Fetching papers from OpenAlex",
        extra={"query": query, "limit": limit}
    )

    try:
        # API调用
        response = await client.get(...)

        if response.status_code != 200:
            logger.error(
                "OpenAlex API returned error",
                extra={
                    "query": query,
                    "status_code": response.status_code,
                    "response_body": response.text[:500],  # 截断避免日志过大
                }
            )
            raise OpenAlexAPIError(f"API returned {response.status_code}")

        # 解析数据
        papers = parse_response(response.json())

        logger.info(
            "Successfully fetched papers",
            extra={
                "query": query,
                "papers_count": len(papers),
                "api_response_time_ms": response.elapsed.total_seconds() * 1000,
            }
        )

        return papers

    except Exception as e:
        logger.error(
            "Failed to fetch papers",
            extra={
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True  # 包含完整异常堆栈
        )
        raise
```

#### 日志轮转和归档

**配置**: `backend/app/config/logging_config.yaml`

```yaml
version: 1
disable_existing_loggers: false

formatters:
  json:
    class: app.utils.logger.CustomJsonFormatter
    format: '%(timestamp)s %(level)s %(name)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: json
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    encoding: utf8

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: logs/error.log
    maxBytes: 10485760
    backupCount: 10
    encoding: utf8

loggers:
  paper_analysis:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false

root:
  level: INFO
  handlers: [console]
```

---

### Frontend日志（浏览器）

#### 错误跟踪（Sentry集成）

**位置**: `frontend/src/utils/sentry.ts`

```typescript
import * as Sentry from "@sentry/nextjs";

/**
 * Sentry错误跟踪初始化
 */
export function initSentry() {
  if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      environment: process.env.NODE_ENV,

      // 追踪配置
      tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

      // 性能监控
      integrations: [
        new Sentry.BrowserTracing({
          tracePropagationTargets: ["localhost", process.env.NEXT_PUBLIC_API_BASE_URL],
        }),
      ],

      // 错误过滤
      beforeSend(event, hint) {
        // 过滤非关键错误
        if (event.exception?.values?.[0]?.type === 'ResizeObserver loop limit exceeded') {
          return null;
        }
        return event;
      },
    });
  }
}

/**
 * 记录自定义错误
 */
export function logError(error: Error, context?: Record<string, any>) {
  console.error(error);

  if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
    Sentry.captureException(error, {
      extra: context,
    });
  }
}

/**
 * 记录自定义消息
 */
export function logMessage(message: string, level: Sentry.SeverityLevel = 'info', context?: Record<string, any>) {
  console.log(message, context);

  if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
    Sentry.captureMessage(message, {
      level,
      extra: context,
    });
  }
}
```

#### 性能监控（Web Vitals）

**位置**: `frontend/src/app/layout.tsx`

```typescript
import { useReportWebVitals } from 'next/web-vitals';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  useReportWebVitals((metric) => {
    // 发送到分析服务
    console.log(metric);

    // 发送到Sentry（生产环境）
    if (process.env.NODE_ENV === 'production') {
      Sentry.captureMessage(`Web Vital: ${metric.name}`, {
        level: 'info',
        extra: {
          value: metric.value,
          id: metric.id,
          label: metric.label,
        },
      });
    }

    // 或发送到自定义分析端点
    if (process.env.NEXT_PUBLIC_ENABLE_ANALYTICS) {
      fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metric),
      });
    }
  });

  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

#### 用户行为跟踪（可选）

**位置**: `frontend/src/utils/analytics.ts`

```typescript
/**
 * 简单的用户行为跟踪工具
 */
export class Analytics {
  /**
   * 追踪页面浏览
   */
  static trackPageView(path: string) {
    if (!process.env.NEXT_PUBLIC_ENABLE_ANALYTICS) return;

    console.log('[Analytics] Page view:', path);

    // 发送到后端或第三方服务
    this.sendEvent('page_view', { path });
  }

  /**
   * 追踪用户操作
   */
  static trackEvent(category: string, action: string, label?: string, value?: number) {
    if (!process.env.NEXT_PUBLIC_ENABLE_ANALYTICS) return;

    console.log('[Analytics] Event:', { category, action, label, value });

    this.sendEvent('user_action', { category, action, label, value });
  }

  /**
   * 追踪搜索查询
   */
  static trackSearch(query: string, resultsCount: number) {
    this.trackEvent('search', 'perform_search', query, resultsCount);
  }

  /**
   * 追踪图交互
   */
  static trackGraphInteraction(action: 'node_click' | 'zoom' | 'pan', nodeId?: string) {
    this.trackEvent('graph', action, nodeId);
  }

  /**
   * 发送事件到后端
   */
  private static sendEvent(eventType: string, data: Record<string, any>) {
    // 异步发送，不阻塞UI
    fetch('/api/analytics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        timestamp: new Date().toISOString(),
        ...data,
      }),
      keepalive: true,  // 确保页面卸载时也能发送
    }).catch(err => console.error('[Analytics] Failed to send event:', err));
  }
}
```

---

## 性能监控

### Backend性能指标

#### API响应时间追踪

**位置**: `backend/app/middleware/metrics_middleware.py`

```python
"""
Prometheus metrics中间件
"""
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time


# 定义metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

OPENALEX_API_DURATION = Histogram(
    'openalex_api_duration_seconds',
    'OpenAlex API call duration',
    ['operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

GRAPH_BUILD_DURATION = Histogram(
    'graph_build_duration_seconds',
    'Citation network build duration',
    ['nodes_count_bucket'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics收集中间件"""

    async def dispatch(self, request: Request, call_next):
        # 跳过metrics端点本身
        if request.url.path == "/metrics":
            return await call_next(request)

        # 增加活跃请求计数
        ACTIVE_REQUESTS.inc()

        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            # 记录响应时间
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

            # 记录请求计数
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()

            # 减少活跃请求计数
            ACTIVE_REQUESTS.dec()

        return response
```

#### 性能监控仪表板数据

**位置**: `backend/app/api/routes.py`

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response


@router.get("/metrics", include_in_schema=False)
async def metrics():
    """
    Prometheus metrics端点

    返回所有性能指标，供Prometheus抓取
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/api/performance")
async def get_performance_stats():
    """
    获取性能统计摘要

    返回人类可读的性能数据（用于内部监控仪表板）
    """
    from prometheus_client import REGISTRY

    # 收集所有metrics
    metrics_data = {}
    for collector in REGISTRY._collector_to_names.keys():
        for metric in collector.collect():
            metrics_data[metric.name] = {
                'type': metric.type,
                'documentation': metric.documentation,
                'samples': [
                    {
                        'labels': dict(sample.labels),
                        'value': sample.value,
                    }
                    for sample in metric.samples
                ]
            }

    return metrics_data
```

### Frontend性能指标

#### Web Vitals追踪

**关键指标**:

| 指标 | 说明 | 目标值 | 测量方法 |
|------|------|--------|---------|
| **FCP** (First Contentful Paint) | 首次内容绘制 | < 1.8s | Web Vitals API |
| **LCP** (Largest Contentful Paint) | 最大内容绘制 | < 2.5s | Web Vitals API |
| **FID** (First Input Delay) | 首次输入延迟 | < 100ms | Web Vitals API |
| **CLS** (Cumulative Layout Shift) | 累积布局偏移 | < 0.1 | Web Vitals API |
| **TTFB** (Time to First Byte) | 首字节时间 | < 600ms | Performance API |

#### 自定义性能追踪

**位置**: `frontend/src/utils/performance.ts`

```typescript
/**
 * 自定义性能测量工具
 */
export class PerformanceTracker {
  /**
   * 测量API请求时间
   */
  static async measureApiCall<T>(
    name: string,
    apiCall: () => Promise<T>
  ): Promise<T> {
    const startMark = `${name}-start`;
    const endMark = `${name}-end`;
    const measureName = `${name}-duration`;

    performance.mark(startMark);

    try {
      const result = await apiCall();
      return result;
    } finally {
      performance.mark(endMark);
      performance.measure(measureName, startMark, endMark);

      const measure = performance.getEntriesByName(measureName)[0];
      console.log(`[Performance] ${name}: ${measure.duration.toFixed(2)}ms`);

      // 发送到分析
      if (process.env.NEXT_PUBLIC_ENABLE_ANALYTICS) {
        fetch('/api/analytics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event_type: 'performance',
            metric_name: name,
            duration_ms: measure.duration,
            timestamp: new Date().toISOString(),
          }),
        });
      }

      // 清理marks
      performance.clearMarks(startMark);
      performance.clearMarks(endMark);
      performance.clearMeasures(measureName);
    }
  }

  /**
   * 测量组件渲染时间
   */
  static measureRender(componentName: string, callback: () => void) {
    const startMark = `render-${componentName}-start`;
    const endMark = `render-${componentName}-end`;
    const measureName = `render-${componentName}`;

    performance.mark(startMark);
    callback();
    performance.mark(endMark);

    performance.measure(measureName, startMark, endMark);
    const measure = performance.getEntriesByName(measureName)[0];

    console.log(`[Render] ${componentName}: ${measure.duration.toFixed(2)}ms`);

    performance.clearMarks(startMark);
    performance.clearMarks(endMark);
    performance.clearMeasures(measureName);
  }
}
```

---

## 健康检查和可观测性

### /health端点增强

#### 详细健康检查

**位置**: `backend/app/api/health.py`

```python
"""
增强的健康检查端点
"""
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from typing import Dict, Literal
import httpx
import time

router = APIRouter()


class HealthCheck(BaseModel):
    """健康检查响应模型"""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: str
    version: str
    checks: Dict[str, Dict[str, any]]


class ReadinessCheck(BaseModel):
    """就绪检查响应模型"""
    ready: bool
    checks: Dict[str, bool]


@router.get("/api/health", response_model=HealthCheck)
async def health_check(response: Response):
    """
    详细健康检查

    检查所有关键依赖的健康状态
    """
    from datetime import datetime
    from app.config import get_settings

    settings = get_settings()
    checks = {}
    overall_status = "healthy"

    # 1. 检查OpenAlex API
    openalex_check = await check_openalex_api()
    checks["openalex_api"] = openalex_check
    if not openalex_check["healthy"]:
        overall_status = "degraded"

    # 2. 检查内存使用
    memory_check = check_memory()
    checks["memory"] = memory_check
    if not memory_check["healthy"]:
        overall_status = "degraded"

    # 3. 检查磁盘空间
    disk_check = check_disk_space()
    checks["disk"] = disk_check
    if not disk_check["healthy"]:
        overall_status = "unhealthy"

    # 设置HTTP状态码
    if overall_status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif overall_status == "degraded":
        response.status_code = status.HTTP_200_OK  # 仍可服务，但有警告

    return HealthCheck(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=settings.app_version,
        checks=checks
    )


@router.get("/api/health/ready", response_model=ReadinessCheck)
async def readiness_check(response: Response):
    """
    就绪检查（Kubernetes readiness probe）

    仅检查服务是否准备好接受流量
    """
    checks = {
        "openalex_api": (await check_openalex_api())["healthy"],
    }

    ready = all(checks.values())

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessCheck(ready=ready, checks=checks)


@router.get("/api/health/live")
async def liveness_check():
    """
    存活检查（Kubernetes liveness probe）

    仅检查进程是否存活（始终返回200）
    """
    return {"alive": True}


async def check_openalex_api() -> Dict[str, any]:
    """检查OpenAlex API可达性"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get("https://api.openalex.org/works?filter=publication_year:2024&per-page=1")
            duration = time.time() - start

            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": round(duration * 1000, 2),
            }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }


def check_memory() -> Dict[str, any]:
    """检查内存使用"""
    import psutil

    memory = psutil.virtual_memory()
    percent_used = memory.percent

    return {
        "healthy": percent_used < 90,
        "percent_used": percent_used,
        "available_gb": round(memory.available / (1024**3), 2),
    }


def check_disk_space() -> Dict[str, any]:
    """检查磁盘空间"""
    import psutil

    disk = psutil.disk_usage('/')
    percent_used = disk.percent

    return {
        "healthy": percent_used < 95,
        "percent_used": percent_used,
        "free_gb": round(disk.free / (1024**3), 2),
    }
```

### Kubernetes健康检查配置

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paper-analysis-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: paper-analysis-backend:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
```

---

## 日志聚合和可视化

### 技术栈选择

#### 方案1: ELK Stack (推荐开源方案)

**组件**:
- **Elasticsearch**: 日志存储和搜索引擎
- **Logstash**: 日志收集和处理
- **Kibana**: 可视化仪表板

**docker-compose.logging.yml**:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: paper-analysis-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - logging-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: paper-analysis-logstash
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./backend/logs:/logs
    ports:
      - "5044:5044"
    networks:
      - logging-network
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: paper-analysis-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - logging-network
    depends_on:
      - elasticsearch

networks:
  logging-network:
    driver: bridge

volumes:
  elasticsearch-data:
```

**Logstash配置** (`logstash/pipeline/logstash.conf`):

```conf
input {
  file {
    path => "/logs/app.log"
    codec => "json"
    type => "backend"
  }
}

filter {
  # 解析JSON日志
  json {
    source => "message"
  }

  # 添加地理位置（如果有IP）
  if [client_ip] {
    geoip {
      source => "client_ip"
    }
  }

  # 添加时间戳
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "paper-analysis-logs-%{+YYYY.MM.dd}"
  }

  # 调试输出
  stdout {
    codec => rubydebug
  }
}
```

#### 方案2: Grafana + Loki (轻量级方案)

**docker-compose.loki.yml**:

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:latest
    container_name: paper-analysis-loki
    ports:
      - "3100:3100"
    volumes:
      - ./loki/config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki
    networks:
      - logging-network

  promtail:
    image: grafana/promtail:latest
    container_name: paper-analysis-promtail
    volumes:
      - ./promtail/config.yaml:/etc/promtail/config.yaml
      - ./backend/logs:/var/log
    networks:
      - logging-network
    depends_on:
      - loki

  grafana:
    image: grafana/grafana:latest
    container_name: paper-analysis-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - logging-network
    depends_on:
      - loki

networks:
  logging-network:
    driver: bridge

volumes:
  loki-data:
  grafana-data:
```

---

## 告警和通知

### 告警规则

#### Prometheus告警规则

**prometheus/alert_rules.yml**:

```yaml
groups:
  - name: paper-analysis-alerts
    interval: 30s
    rules:
      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (>5%) for the last 5 minutes"

      # 慢API告警
      - alert: SlowAPIResponse
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API response time is slow"
          description: "95th percentile response time is {{ $value }}s (>10s)"

      # OpenAlex API异常
      - alert: OpenAlexAPIDown
        expr: |
          rate(openalex_api_duration_seconds_count[5m]) == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "OpenAlex API is not responding"
          description: "No successful OpenAlex API calls in the last 10 minutes"

      # 内存使用告警
      - alert: HighMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% (>90%)"
```

### 通知渠道

#### Slack通知（示例）

**alertmanager/config.yml**:

```yaml
global:
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#paper-analysis-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

---

## 验收标准

### 监控和日志完整性

- ✅ Backend结构化JSON日志实现
- ✅ Frontend Sentry错误追踪集成
- ✅ Prometheus metrics端点实现
- ✅ 详细健康检查端点（/health, /ready, /live）
- ✅ Web Vitals追踪
- ✅ ELK或Loki日志聚合方案
- ✅ Grafana可视化仪表板
- ✅ Prometheus告警规则
- ✅ 日志轮转和归档策略

---

**记住**: 可观测性不是可选项，是生产就绪的必需品！
