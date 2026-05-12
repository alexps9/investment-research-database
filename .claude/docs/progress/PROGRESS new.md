# Project Progress - Tech-Path V2

> 当前工作状态和进度跟踪
> **最后更新**: 2026-04-30
> **当前阶段**: Phase A MVP - 种子论文 v2 修复中

---

## Current Status

### Phase A: MVP 种子论文 (10 篇 × 4 路径) 🔧 IN PROGRESS

#### 已完成
- [x] **Spec 编写**: `mvp-seed-papers-spec.md` 完成（含验收标准更新）
- [x] **OpenAlex ID 查找**: 10 篇论文全部找到 Work ID
- [x] **后端 v1**: 种子数据 + API 端点 + 报告生成
- [x] **前端 v1**: 种子模式切换 + 三件事报告面板
- [x] **v2 修复**: 手工引用边 + Griffin fallback + 泳道布局 + 报告面板

#### v2 修复内容（2026-04-30）
- **0 条引用 → 10+ 条**：OpenAlex 对 arXiv 预印本无引用数据，改为手工定义 SEED_CITATIONS
- **9 篇 → 10 篇**：Griffin (W6891815739) 在 batch filter 中查不到，加了 fallback 单独请求
- **散乱布局 → 泳道式**：ForceGraph 增加 swim lane 背景带 + 虚线分隔 + 左侧路径标签
- **报告面板不显示 → 可点击**：修复了因 0 引用导致的图例/报告链路问题
- **seed_network_service 重写**：不再走 Louvain，直接构建 GraphResponse
- [x] **后端实现**: 种子数据 + API 端点 + 报告生成
- [x] **前端实现**: 种子模式切换 + 三件事报告面板

#### 种子论文 ID 映射
| # | 论文 | OpenAlex ID | 路径 |
|---|------|-------------|------|
| 1 | FlashAttention-2 | W4384648639 | A |
| 2 | Ring Attention | W4387356039 | A |
| 3 | DeepSeek-V3 | W4405903187 | A |
| 4 | Mamba | W4389326242 | B |
| 5 | Jamba | W4393399080 | B |
| 6 | Griffin | W6891815739 | B |
| 7 | xLSTM | W4396815331 | C |
| 8 | RWKV (Eagle/Finch) | W4394708852 | C |
| 9 | TTT Layers | W4400435102 | C |
| 10 | Mixtral of Experts | W4390723197 | D |

#### 后端新增文件
| 文件 | 用途 |
|------|------|
| `app/data/seed_papers.py` | 种子论文配置（10 篇，4 路径） |
| `app/models/reports.py` | 三件事报告数据模型 |
| `app/services/seed_network_service.py` | 种子网络构建 + 路径标签覆盖 |
| `app/services/insight_report_service.py` | 硬编码三件事报告（A/B/C/D） |

#### 后端修改文件
| 文件 | 改动 |
|------|------|
| `app/models/schemas.py` | Paper 新增 abstract, institutions 字段 |
| `app/services/openalex_client.py` | 新增 fetch_works_by_ids, _parse_work 提取 abstract/institutions |
| `app/api/routes.py` | 新增 /seed-network, /seed-papers, /seed-report/{path} |

#### 前端新增文件
| 文件 | 用途 |
|------|------|
| `components/InsightReport.tsx` | 三件事报告面板组件 |
| `components/InsightReport.module.css` | 报告面板样式 |
| `hooks/useInsightReport.ts` | 报告数据获取 hook |

#### 前端修改文件
| 文件 | 改动 |
|------|------|
| `types/api.ts` | 新增 InsightReport 等类型 |
| `lib/api-client.ts` | 新增 fetchSeedNetwork, fetchSeedReport |
| `app/page.tsx` | 种子模式切换 + 报告面板集成 |
| `app/page.module.css` | 模式切换按钮 + 可点击图例样式 |

#### 待验证
- [ ] 启动后端，测试 /api/seed-network 端点
- [ ] 启动前端，测试种子模式 UI
- [ ] 验证力导向图 4 路径着色
- [ ] 验证三件事报告面板展示

---

### 技��决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 三件事报告 | 硬编码 | MVP 10 篇可控，Phase B 再动态生成 |
| 路径标签 | 手工覆盖 Louvain | 10 篇论文路径已知，不需要算法猜 |
| 种子模式入口 | 页面内切换 | 复用所有现有组件 |
| 批量获取 | filter 批量 | 1 次请求 vs 10 次 |

---

### 下一步

1. **集成测试**: 启动前后端，验证完整链路
2. **Phase B 准备**: 扩展到 100 篇，接入 LLM 标注
3. **趋势预测**: 在三件事报告基础上加预测模块
