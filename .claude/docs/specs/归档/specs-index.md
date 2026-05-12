# Specs 文档索引

> 本目录包含项目所有技术规格文档，按以下结构组织

---

## � Phase 0-4 完整规格

| 文件 | 说明 | 状态 |
|------|------|------|
| [`phase-all-index.md`](./phase-all-index.md) | Phase 0-4 完整技术规格 (合并版) | 📖 必读 |

**包含内容**:
- Phase 0: 项目初始化 (Docker、Backend/Frontend骨架)
- Phase 1: 核心后端开发 (OpenAlex API、NetworkX、FastAPI)
- Phase 2: 前端可视化 (Rams UI、力导向图)
- Phase 3: 集成与部署 (Docker Compose、E2E测试)
- Phase 4: 高级特性 (性能优化、Redis缓存、图谱导出)

---

## 🆕 编号文档 (按序号排序)

### 1. 立即执行计划
**文件**: [`1-immediate-execution-plan.md`](./1-immediate-execution-plan.md)

- **目的**: 连接当前状态与 Phase 1 就绪之间的gap
- **内容**: 5个任务的详细分解表 (T1-T5)
- **执行者**: backend-dev, frontend-dev, reviewer, planner
- **预计时间**: 4小时

---

### 2. ErrorMessage 组件设计合规报告
**文件**: [`2-ErrorMessage-design-compliance.md`](./2-ErrorMessage-design-compliance.md)

- **目的**: ErrorMessage组件的Rams设计原则验证
- **验证结果**: ✅ 10/10项通过
- **测试覆盖**: 100%

---

### 3. Phase 1-2 执行编排计划
**文件**: [`3-phase1-2-execution-orchestration.md`](./3-phase1-2-execution-orchestration.md)

- **目的**: Phase 1-2的项目管理框架
- **内容**: 执行策略、任务分配、质量门禁
- **时长**: 4-6周

---

### 4. 前端改造 + 交互增强 (V2)
**文件**: [`4-frontend-revamp-spec.md`](./4-frontend-revamp-spec.md)

- **目的**: 将项目改造为"技术路线洞察系统"
- **复杂度**: 🔴 复杂
- **核心功能**: 时间线布局、社区自动命名、对数滑块

---

### 5. MVP2: 语义相似度验证
**文件**: [`5-mvp2-semantic-similarity-spec.md`](./5-mvp2-semantic-similarity-spec.md)

- **目的**: 验证MVP1引用关系的假设
- **方法**: 语义相似度 + 引用关系对比

---

### 6. Phase 4 快速参考
**文件**: [`6-phase4-quick-reference.md`](./6-phase4-quick-reference.md)

- **目的**: Phase 4功能快速参考清单
- **内容**: 功能优先级、验收标准、技术要点

---

### 7. Phase 4 侧边栏设置规格
**文件**: [`7-phase4-sidebar-settings-spec.md`](./7-phase4-sidebar-settings-spec.md)

- **目的**: Phase 4侧边栏设计详细规格
- **设计原则**: Rams-compliant

---

## � 目录结构

```
specs/
├── phase-all-index.md                    # Phase 0-4 完整规格 (主文档)
├── specs-index.md                        # 本索引文件
│
├── 1-immediate-execution-plan.md         # 立即执行计划
├── 2-ErrorMessage-design-compliance.md   # ErrorMessage设计合规报告
├── 3-phase1-2-execution-orchestration.md # Phase 1-2执行编排
├── 4-frontend-revamp-spec.md            # 前端改造V2规格
├── 5-mvp2-semantic-similarity-spec.md   # MVP2语义相似度验证
├── 6-phase4-quick-reference.md          # Phase 4快速参考
└── 7-phase4-sidebar-settings-spec.md    # Phase 4侧边栏设置
```

---

## � 快速开始

### 新团队成员
1. 先读 [`phase-all-index.md`](./phase-all-index.md) 了解项目全貌
2. 根据角色查看对应Phase章节
3. 参考编号文档了解具体实现细节

### 开发人员
- **Backend**: Phase 0 (Task 0.3) → Phase 1 → Phase 3
- **Frontend**: Phase 0 (Task 0.4) → Phase 2 → Phase 4
- **DevOps**: Phase 3 (Docker部署)

---

> **注意**: 原始分散的Phase文件 (phase-0-completion-and-phase-1-plan.md, phase-1-implementation-guide.md等) 已合并到 phase-all-index.md 并删除。
