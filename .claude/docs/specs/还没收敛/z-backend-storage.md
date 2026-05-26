---
status: 已实现（前端未接入）
created: 2026-05-12
updated: 2026-05-26
complexity: 🟡中等
---

# 后端数据存储 & 论文 CRUD API

## 现状

- **SQLite 数据库**已上线（`backend/data/world_model.db`，~60KB）
- **8 个 CRUD endpoint** 通过 FastAPI 暴露
- **137 篇论文**已从 `world-model-data.json` 迁移入库
- **37 个测试**全部通过
- **前端仍用静态 JSON**（`import worldModelData from '@/data/world-model-data.json'`），未接通 API

---

## 架构

### 数据库 Schema（4 张表）

```sql
-- backend/app/db.py
lanes (id PK, title, subtitle, color)
rows  (id PK, lane FK, title, subtitle)
papers (
  id PK, title, full_title, year, quarter[1-4],
  lane FK, row FK, path, paradigm, layer, shape,
  org, authors[JSON], arxiv_id, doi,
  cited_by_count, venue_tier, institution_tier,
  impact_score, impact_override
)
connections (source_id FK, target_id FK, type, PK=(source,target,type))
  -- type: 'inherits' | 'competes' | 'borrows'
```

### 关键设计决策

| 决策 | 理由 |
|------|------|
| SQLite（非 Postgres） | 300-500 篇规模，单用户，无需 ORM |
| authors 存 JSON string | 不需要按作者查询，简化 schema |
| connections 三元组主键 | 同一对论文可有多种关系类型 |
| 删论文级联删 connections | 保持引用完整性 |
| `builds_on` 字段废弃 | 统一走 connections 表 type='inherits' |

---

## API 契约

**Base**: `/api/world-model`

| Method | Path | 功能 | Status |
|--------|------|------|--------|
| GET | `/` | 获取全部数据（lanes+rows+papers+connections） | 200 |
| GET | `/papers` | 列表（可选 ?lane=&row= 过滤） | 200 |
| GET | `/papers/{id}` | 单篇详情 | 200/404 |
| POST | `/papers` | 新建论文 | 201/409/422 |
| PUT | `/papers/{id}` | 更新（partial update） | 200/404 |
| DELETE | `/papers/{id}` | 删除（级联删 connections） | 200/404 |
| POST | `/connections` | 新建关系 | 201/404/409 |
| DELETE | `/connections` | 删除关系 | 200/404 |

### Response 格式（GET /）

```json
{
  "lanes": [{"id": "video_gen", "title": "Video-Generative", "color": "#2563EB", ...}],
  "rows": [{"id": "diffusion_video", "lane": "video_gen", "title": "Diffusion-based", ...}],
  "papers": [{
    "id": "sora", "title": "Sora", "year": 2024, "quarter": 1,
    "lane": "video_gen", "row": "diffusion_video",
    "impact_score": 78, "shape": "circle",
    "connections": [{"target": "drive_wm", "type": "inherits"}],
    ...
  }]
}
```

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `backend/app/db.py` | SQLite 连接 + schema init |
| `backend/app/api/world_model.py` | 8 个 CRUD endpoints |
| `backend/app/models/evolution.py` | Pydantic models (PaperCreate/Update/Connection/WorldModelResponse) |
| `backend/app/main.py` | 注册 router, startup 调 init_db() |
| `backend/scripts/migrate_json_to_sqlite.py` | JSON → SQLite 迁移（幂等） |
| `backend/tests/test_world_model_api.py` | 23 个端点测试 |
| `backend/data/world_model.db` | SQLite 文件（.gitignore） |

---

## 数据流

```
当前:
  world-model-data.json ──(静态 import)──→ 前端渲染
  world-model-data.json ──(migrate脚本)──→ SQLite DB ──(API)──→ 未接入

目标:
  飞书/日报/手动 ──→ API POST ──→ SQLite DB ──→ GET /api/world-model ──→ 前端 fetch
```

---

## 论文入库流程（规划中）

### 数据源优先级

1. **同事爬虫数据库**（最优，等他提供 export）
2. **解析日报 markdown**（`scripts/add_from_daily.py`，待实现）
3. **飞书多维表格同步**（`scripts/lark_sync.py`，已有字段映射）

### World Model 过滤关键词

```python
WM_KEYWORDS = [
    'world model', 'video generation', 'video prediction',
    'diffusion policy', 'VLA', 'vision-language-action',
    'embodied', 'dreamer', 'JEPA', 'latent dynamics',
    'robot control', 'action model', 'world simulator',
    'model-based RL',
]
```

### 与同事分工

```
他: 实体层（arxiv_id, title, authors, abstract, date, venue, institution）
我: 分析层（lane, row, impact_score, connections, is_rising）
```

---

## 待做

- [ ] **前端接入 API**：替换静态 JSON import → fetch GET /api/world-model
- [ ] **scripts/add_from_daily.py**：解析日报 → 过滤 WM → 调 POST /papers
- [ ] **scripts/update_impact.py**：批量刷新 cited_by_count + 重算 impact
- [ ] **前端 Table 视图**：看论文列表 / 审核 impact / 编辑字段
- [ ] 跟同事确认 export 格式
