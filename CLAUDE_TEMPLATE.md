# {项目名称} - Claude Code Configuration

> 项目宪法 - 所有 Agents 必须遵守的核心规范

---

## 🎯 项目概述

**目标**: {一句话描述项目目标}

**核心功能**:
- {功能1}
- {功能2}
- {功能3}

---

## 🚨 核心规则：强制执行

### 软件工程原则

#### 1. DRY (Don't Repeat Yourself)
- ✅ 零代码重复容忍度
- ✅ 每个功能必须只存在于一个地方

#### 2. KISS (Keep It Simple, Stupid)
- ✅ 实现能工作的最简单方案
- ❌ 禁止过度工程或不必要的复杂性

#### 3. 透明错误处理（极其重要！）

**❌ 禁止做的事**:
- 隐藏错误或使用掩盖问题的 fallback 机制
- 通用的 "something went wrong" 消息

**✅ 必须做的事**:
- 所有错误必须正确显示给用户
- 错误信息必须清晰、可操作、诚实
- 包含上下文：什么失败了、为什么、如何修复

---

## 🛠️ 技术栈

### Backend
- **框架**: {如 FastAPI / Express / Django}
- **语言**: {如 Python 3.10+ / Node.js}
- **数据库**: {如 PostgreSQL / MongoDB}
- **测试**: {如 pytest / Jest}

### Frontend
- **框架**: {如 Next.js / React / Vue}
- **语言**: {如 TypeScript}
- **样式**: {如 Tailwind / CSS Modules}

### DevOps
- **容器化**: Docker, Docker Compose
- **CI/CD**: {如 GitHub Actions}

---

## 🔄 开发流程（强制）

### 1. Planning Mode（必须）
- 所有新功能必须先进入 Planning Mode
- 生成详细设计方案到 `.claude/docs/specs/`
- 定义检查点和验收标准

### 2. TDD 开发（强制）
```
🔴 Red → 🟢 Green → 🔵 Refactor
```

**测试要求**:
- 单元测试覆盖率 > 80%
- 集成测试覆盖核心流程

### 3. 代码审查（强制）
- 所有代码必须通过 reviewer agent 审查

### 4. 文档化（强制）
- API 端点必须有完整文档
- 复杂算法必须有注释说明

---

## 🤖 Subagent 强制规则

| 任务类型 | 必须使用 | 输出位置 |
|---------|---------|---------|
| 架构设计 | planner | `.claude/docs/specs/` |
| Backend 代码 | backend-dev | `backend/` |
| Frontend 代码 | frontend-dev | `frontend/` |
| 代码审查 | reviewer | `.claude/docs/reviews/` |

---

## 📁 文件结构

```
{项目名称}/
├── .claude/                      # Claude Code 配置
│   ├── CLAUDE.md                # 本文件
│   ├── agents/                  # Subagent 配置
│   └── docs/                    # 文档
│       ├── specs/               # 设计规范
│       └── reviews/             # 代码审查
├── backend/                     # 后端代码
├── frontend/                    # 前端代码
├── docs/                        # 项目文档
├── docker-compose.yml
└── README.md
```

---

## 🎯 验收标准

### 每个功能必须满足
- ✅ 有完整的 TDD 测试（覆盖率 > 80%）
- ✅ 通过代码审查
- ✅ 有完整文档
- ✅ 代码格式化通过

---

## 🚀 快速参考

### Backend 命令
```bash
# 运行测试
pytest tests/ -v

# 启动服务
uvicorn app.main:app --reload
```

### Frontend 命令
```bash
# 运行测试
npm test

# 开发服务器
npm run dev

# 构建
npm run build
```

### Docker
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## ⚠️ 重要提醒

1. **所有新功能必须先进入 Planning Mode**
2. **严格遵守 TDD 流程**
3. **不要隐藏错误 - 透明化所有问题**
4. **使用 Subagent 完成专业任务**
5. **上下文过长时记录进度到 PROGRESS.md**

---

**记住**: 这个文件是项目的宪法。所有 Agent 必须遵守这些规则。
