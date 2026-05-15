#  Tech trajectory — 项目宪法

> AI 技术演化地铁图。让研究者一眼看出"面对同一瓶颈，人们产生了哪些不同技术哲学，以及谁赢了"。

---

## 协作工作流（每次会话必读）

### 进入会话时

1. 先读`goal.md`了解我们在做什么； `.claude/docs/STATUS.md` — 了解当前阶段、待做事项、最近完成的工作；
2. 用户给了会议纪要 → 处理流程：
   - 按 `z-meetings/prompt.md` 提取 Tian 视角摘要 → 加在原始记录前面
   - 存入 `z-meetings/YYYY-MM-DD-主题.md`
   - 让用户 review 后：
     - 方向性校准（赛道变更、taxonomy 调整）→ 更新 `goal.md`
     - 具体任务 → 更新 `STATUS.md` 的 Action Items
3. 用户给了论文综述/数据 → 提取论文信息 → **先列出结果让用户确认** → 再写入后端

### 文档导航

| 要找什么 | 去哪里 |
|---------|--------|
| 当前状态 / TODO | `.claude/docs/STATUS.md` |
| 项目目标 + 赛道框架 | `.claude/docs/goal.md` |
| 功能规格（含 backlog） | `.claude/docs/specs/` |
| 设计规范（视觉编码/Era/视图） | `.claude/docs/design/` |
| 论文知识库（综述/数据） | `.claude/docs/knowledge/` |
| 会议记录 | `.claude/docs/z-meetings/` |
| 变更日志 / 踩坑 | `.claude/docs/logs/` |
| HTML 原型 | `.claude/docs/design/prototypes/` |
| 归档（已完成/过时的 spec） | `specs/归档/`、`design/归档/` |

---

## 技术栈（严禁偏离）

- **Frontend**: Next.js 14 (App Router) | TypeScript | D3.js 手动布局 / 纯 SVG + React
- **Backend**: FastAPI | Python 3.10+ | NetworkX | httpx
- **数据源**: OpenAlex API + 人工标注 taxonomy
- **Infrastructure**: Docker Compose | GitHub Actions
- **字体**: IBM Plex Sans

注：禁止 react-force-graph / 任何自动布局库。布局完全人为编排。

## 目录约定

```
backend/app/api/        路由
backend/app/services/   业务逻辑
backend/app/models/     数据模型
frontend/src/app/       Next.js pages
frontend/src/components/ React 组件
.claude/docs/design/    设计规范（权威来源）
.claude/docs/specs/     功能 spec
.claude/docs/design/prototypes/  HTML 原型
```

## 规则（按上下文自动加载）

位于 `.claude/rules/`，按 `paths:` frontmatter 条件加载：

| 规则文件 | 生效范围 | 内容 |
|---------|---------|------|
| `visual-encoding.md` | frontend/、design/、specs/ | 颜色体系、节点编码、允许/禁止清单 |
| `coding-standards.md` | backend/、frontend/ | 错误透明、零重复、无冗余注释 |
| `spec-workflow.md` | specs/、logs/、backend/、frontend/、scripts/ | Spec→Code 流程、开发 SOP、Log 触发时机 |

## 多终端协作规则

- **完成一个大需求后**，主动提醒用户 commit + push（防止其他终端覆盖）
- **world-model-data.json 有 `_schema_version` 字段** — 如果读到的版本和当前 taxonomy 不匹配，先确认再改，不要直接覆盖
- **改 taxonomy（lane/row 结构）前**，先检查 `world-model-data.json` 当前结构是否和 spec 一致，不一致说明被其他终端改过
- **禁止在未 commit 的状态下大面积重写数据文件** — 先 commit 当前状态作为 checkpoint

## 收尾检查（每次实现后）

实现了 spec 里的功能 → 问自己：
1. **有决策/踩坑？** → 写 `docs/logs/<topic>.md`（选了什么、放弃了什么、为什么）
2. **改了已有功能？** → 回去更新对应 spec
3. **STATUS.md 需要更新？** → 标完成 / 加新待做
4. **大需求完成？** → 提醒用户 commit + push 保存

## 常用命令

```bash
# 原型截图
cd .claude/docs/design/prototypes && python screenshot.py <file.html>
# Backend
cd backend && pytest tests/ -v && uvicorn app.main:app --reload
# Frontend
cd frontend && npm run dev && npm test
```
