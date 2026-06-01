# AI 智能知识库

> 面向 AI 研究者的信号收集与知识管理系统。

**知识链：** Source → Signal → Entity → Relation → Wiki / Search

---

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        浏览器                               │
│              Next.js 14  (localhost:3000)                   │
│   /dashboard  /sources  /signals  /entities  /wiki  /graph  │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP  /api/*  (rewrite 代理)
┌────────────────────────▼────────────────────────────────────┐
│                  FastAPI 后端                               │
│                   (localhost:8000)                          │
│                                                             │
│  Routers → Repositories → SQLAlchemy 2.x (async)           │
│                                                             │
│  /sources   /signals   /entities   /search                  │
│  /wiki      /graph     /dashboard  /runs                    │
└────────────────────────┬────────────────────────────────────┘
                         │  asyncpg
┌────────────────────────▼────────────────────────────────────┐
│                   PostgreSQL 16                             │
│                                                             │
│  organizations   sources   source_accounts   tags           │
│  signals   signal_analysis   signal_entities                │
│  entities   entity_aliases   entity_relations               │
│  embeddings (pgvector-ready)   pipeline_runs                │
└─────────────────────────────────────────────────────────────┘

  其他 agent（Claude / Cursor / 自建）──MCP──► mcp_server
  （stdio 或 streamable-http）                    │ HTTP /api/*
                                                 ▼
                                          FastAPI 后端
```

```
数据流
──────
外部来源 ──► Signal（证据）──► Entity（知识节点）
                                     │
                               EntityRelation
                                     │
                               Wiki / Graph
```

---

## 快速启动

### Docker Compose（推荐）

```bash
cp .env.example backend/.env
docker compose up --build
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| 交互式 API 文档 | http://localhost:8000/docs |

首次启动会自动执行：数据库迁移 → 写入 Seed 数据 → 启动服务器。

---

### 本地开发

**前置条件：** Python 3.12+、Node.js 20+、PostgreSQL 16

```bash
# 后端
cd backend
pip install -r requirements.txt
cp ../.env.example .env          # 按需修改数据库连接
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## 目录结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口，CORS，路由注册
│   │   ├── database.py        # 引擎 & Session
│   │   ├── models/            # SQLAlchemy ORM（13 张表）
│   │   ├── schemas/           # Pydantic v2 请求/响应
│   │   ├── repositories/      # 数据访问层（Router 不直接写 SQL）
│   │   ├── routers/           # 路由处理器
│   │   └── core/config.py     # 环境变量配置
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # pytest 测试
│   ├── seed.py                # Seed 脚本
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/               # Next.js App Router 页面
│       ├── components/        # Sidebar + UI 组件
│       └── lib/               # API 客户端 & TypeScript 类型
├── mcp_server/                # MCP 服务，把知识库能力开放给其他 agent
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
├── docker-compose.yml
└── .env.example
```

---

## API 端点

| 资源 | 端点 |
|------|------|
| Sources | `GET/POST /api/sources` · `PATCH/DELETE /api/sources/{id}` · `POST .../accounts` · `POST .../tags` |
| Signals | `GET/POST /api/signals` · `PATCH /api/signals/{id}` · `POST .../analysis` · `GET .../related` |
| Entities | `GET/POST /api/entities` · `PATCH /api/entities/{id}` · `POST .../aliases` · `GET/POST .../relations` |
| Search | `GET /api/search?q=` |
| Wiki | `GET /api/wiki/entities/{id}` |
| Graph | `GET /api/graph/relations` |
| Dashboard | `GET /api/dashboard/stats` · `GET .../latest-signals` · `GET .../latest-runs` |
| Runs | `GET /api/runs` · `POST /api/runs/mock` |

完整交互文档：http://localhost:8000/docs

---

## 前端页面

| 路径 | 说明 |
|------|------|
| `/dashboard` | 统计卡片 + 最新 Signal + Pipeline 记录 |
| `/sources` | 来源管理表格，支持新建 |
| `/signals` | Signal 卡片列表，支持新建 |
| `/entities` | 实体表格，支持新建 |
| `/wiki` | 全局搜索（实体 / Signal / 来源分组） |
| `/wiki/entities/[id]` | 实体 Wiki 详情（关系、Signal、别名） |
| `/graph-lite` | 关系图（节点 + 边表格，基于 PostgreSQL） |

---

## 测试

```bash
cd backend

# 单元测试（无需数据库）
pytest tests/test_models.py -v

# API 冒烟测试（需要运行中的后端）
pytest tests/test_api.py -v
```

---

## MCP 服务（开放给其他 agent）

知识库同时通过 **Model Context Protocol** 对外开放，其他 agent（Claude Desktop、
Cursor、自建 agent）可以搜索、读取实体 Wiki、写入 Signal/实体。它封装的是同一个
FastAPI 后端（通过 HTTP 调用）。

```bash
cd mcp_server
pip install -r requirements.txt

# stdio（本地客户端）
python server.py

# streamable-http（远程 / 多 agent）→ http://localhost:8765/mcp
MCP_TRANSPORT=streamable-http python server.py
```

工具包含 `search_knowledge`、`get_entity_wiki`、`list_signals`、`create_signal`、
`add_entity_relation` 等。完整工具列表与客户端配置见
[mcp_server/README.md](./mcp_server/README.md)。

---

## 数据库 Schema（13 张表）

```
organizations ──< sources ──< source_accounts
                    │
                    └──< source_tags >── tags

signals ──< signal_analysis
   │
   └──< signal_entities >── entities ──< entity_aliases
                                │
                         entity_relations（主体 → 关系类型 → 客体）

embeddings   pipeline_runs
```

English documentation: [README.md](./README.md)
