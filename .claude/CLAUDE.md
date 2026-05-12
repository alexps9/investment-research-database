# LLM Systems Evolution Map — 项目宪法

> AI 技术演化地铁图。让研究者一眼看出"面对同一瓶颈，人们产生了哪些不同技术哲学，以及谁赢了"。

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

## 开发 SOP

1. **Plan**: 新功能先产出 Spec 至 `.claude/docs/specs/`
2. **Prototype**: 视觉类需求先出 HTML 原型到 `prototypes/`，截图确认效果
3. **Code**: 遵循 TDD（Red → Green → Refactor）
4. **Review**: 阶段完成更新 `.claude/progress/PROGRESS.md`

## 治理分级

- **T0 (核心数据/API)**: Spec + 高覆盖率 + 审查
- **T2 (UI 原型/脚本)**: 逻辑通顺 + 关键路径 review

## 视觉设计规范

### Rams 原则正确解读

核心是**每个视觉元素必须编码信息**，不是"尽量少视觉元素"。

- 无功能的装饰 → 删除
- 编码信息的视觉手段（blur 压力场、glow momentum、形状编码）→ 保留

### 颜色体系

| 用途 | 色值 |
|------|------|
| 背景 | #FFFFFF |
| 面板背景 | #FAFAFA |
| 文本 | #18181B / #3F3F46 / #71717A / #A1A1AA |
| 边框 | #E4E4E7（仅 1px） |
| NOW 线 | #FF4400 |
| Paradigm 5色 | 灰蓝 #475569 / 蓝 #2563EB / 青绿 #0D9488 / 红 #DC2626 / 橙 #EA580C |
| Lane 3色 | 蓝 #2563EB / 绿 #059669 / 橙 #EA580C |

### 允许与禁止

| ✅ 允许 | ❌ 禁止 |
|---------|---------|
| Gaussian blur 压力场（信息编码） | 装饰性渐变 |
| box-shadow momentum 发光（信息编码） | 装饰性阴影 |
| 5种几何形状编码 Layer | 自动布局 |
| opacity 变化编码活跃度 | 超过 1px 的边框 |

### 节点编码

- **颜色** = Paradigm（5 色，世界观）
- **形状** = Layer（circle/square/diamond/triangle/hexagon）
- **大小** = Impact（log citations → sm/md/lg）
- **连线** = 关系（实线 builds_on / 短虚线 competes / 长虚线 lineage）

## 核心 Ontology（四层因果）

```
Era（时代背景）→ Bottleneck/Lane（问题压力）→ Paradigm（技术哲学）→ Paper（具体实现）
```

关键约束：Pressure Field 挂在 **Lane** 上，不是 Paradigm 上（Lane 是稳定 partition）。

## 四个视图

| 视图 | 核心问题 | 布局 |
|------|---------|------|
| Global | 为什么时代转向 | 地铁图 hierarchical swimlane |
| Topic | 为什么路线分叉 | lineage tree |
| Iteration | 为什么路线持续进化 | vertical mutation timeline |
| Arena | 为什么有的路线赢了 | parallel race tracks |

## 编码规范

- 错误必须透明显示（禁止 silent failure / 空 fallback）
- 零代码重复
- 不加无用注释、不过度工程

## 规则索引（按需读取）

- 视觉编码: `.claude/docs/design/visual-encoding.md`
- Era 框架: `.claude/docs/design/era-framework.md`
- Global View spec: `.claude/docs/design/global-view-spec.md`
- PRD v2: `.claude/docs/design/prd-v2.md`
- 论文分类: `docs/paper-taxonomy.md`

## 常用命令

```bash
# 原型截图
cd .claude/docs/design/prototypes && python screenshot.py <file.html>
# Backend
cd backend && pytest tests/ -v && uvicorn app.main:app --reload
# Frontend
cd frontend && npm run dev && npm test
```
