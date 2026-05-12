# MVP：10 篇种子论文 × 4 条技术路径

> status: apply
> created: 2026-04-29
> complexity: 🟡中等

## 1. 背景与目标

**为什么做**：
用 10 篇手选论文验证"技术路线发现"的核心逻辑。不靠 OpenAlex 搜索 100 篇再筛，
而是从已知的 4 条演化路径出发，验证系统能否：
1. 正确展示路径聚类和演化关系
2. 自动生成三件事报告（时空定位 / 人才图谱 / 瓶颈分析）

**做完后的效果**（验收标准）：
1. **泳道式布局**：X 轴 = 年份（2023-2024），Y 轴 = 4 条路径泳道（A/B/C/D），每条泳道有标签和视觉分隔
2. **10 个节点全部显示**：每个节点有标题标签，按路径着色
3. **引用边可见**：10+ 条手工定义的引用边，跨泳道连线体现架构杂交（如 Jamba 连向 Mamba 和 FlashAttention）
4. **三件事报告面板**：点击左侧路径图例 → 侧边栏展开报告（时空定位 / 人才图谱 / 瓶颈分析）
5. **报告内容准确**：每条路径的报告与论文实际贡献一致（人工验证）
6. **模式切换**：搜索模式 ↔ 种子 Demo 模式，互斥切换

**MVP 不做的事**：
- 不做 2500 篇 Scaling
- 不做趋势预测（先验证描述性分析）
- 不做 LLM 批量标注（10 篇手工标注）
- 不做标注管理后台
- 不做数据库持久化

## 2. 代码现状（Research Findings）

### 2.1 相关入口与链路

当前搜索链路：
```
用户输入 query → GET /api/search
  → OpenAlexClient.fetch_papers(query, limit)  # 按 cited_by_count:desc 排序
  → CitationNetworkBuilder.build_network(papers)  # Louvain 社区检测
  → GraphResponse(nodes, links, metadata)
  → 前端 ForceGraph 渲染
```

### 2.2 现有实现

| 能力 | 文件 | 状态 |
|------|------|------|
| OpenAlex 论文获取 | `backend/app/services/openalex_client.py` | ✅ 可复用 |
| 引用网络构建 | `backend/app/services/citation_network.py` | ✅ 可复用 |
| Louvain 社区检测 | `citation_network.py:calculate_communities()` | ✅ 可复用 |
| 社区命名（TF-IDF） | `citation_network.py:_generate_community_names()` | ⚠️ 需升级为路径标签 |
| 力导向图渲染 | `frontend/src/components/ForceGraph.tsx` | ✅ 可复用 |
| 节点详情面板 | `frontend/src/components/NodeDetail.tsx` | ⚠️ 需扩展为报告面板 |
| 数据模型 | `backend/app/models/schemas.py` | ⚠️ 需扩展 |
| API 路由 | `backend/app/api/routes.py` | ⚠️ 需新增端点 |

### 2.3 发现与风险

1. **现有 Paper model ���有 author_names 字段**（`schemas.py:64`），人才图谱可直接利用
2. **OpenAlexClient 已支持按 Work ID 获取单篇论文**（`fetch_references` 方法），
   但没有"按 Work ID 批量获取完整元数据"的方法——需要新增
3. **社区检测是自动的**（Louvain），但 MVP 的 4 条路径是手工定义的，
   需要决定：用手工标签覆盖 Louvain 结果，还是两者并存？
   → **决策：手工标签优先**，Louvain 作为验证参考
4. **前端 NodeDetail 只展示单篇论文**，三件事报告是路径级别的聚合——需要新组件

## 3. 功能点

### F1：种子数据获取与标注
- [ ] **F1.1 种子论文 ID 查找**：通过 OpenAlex API 查找 10 篇论文的 Work ID
  - 输入：论文标题列表
  - 处理：调用 OpenAlex `/works?search=<title>` 匹配
  - 输出：10 个 Work ID + 完整元数据（标题、年份、引用数、作者、机构、摘要）

- [ ] **F1.2 种子数据定义**：硬编码种子论文配置
  - 输入：F1.1 查到的 Work ID
  - 处理：定义 `SeedPaper` 数据结构，包含 work_id + 手工路径标签 + tech_tags
  - 输出：`backend/app/data/seed_papers.py`，包含 10 篇论文的完整配置
  - 数据结构：
    ```python
    class SeedPaper(BaseModel):
        work_id: str                    # OpenAlex Work ID, e.g. "W4388726703"
        path: Literal["A", "B", "C", "D"]  # 手工路径标签
        tech_tags: List[str]            # e.g. ["Attention-Optimization"]
        primary_tag: str                # 主标签
    ```

- [ ] **F1.3 批量元数据获取**：新增 OpenAlexClient 方法，按 Work ID 批量获取完整元数据
  - 输入：10 个 Work ID
  - 处理：新增 `fetch_works_by_ids(work_ids: List[str]) -> List[Paper]`
    - 复用现有 `_retry_request` + `_parse_work`（`openalex_client.py:306`、`376`）
    - 调用 `GET /works?filter=openalex_id:{id1}|{id2}|...&select=...&per-page=50`
    - OpenAlex 支持 pipe-separated filter 批量查询，一次请求拿全部
  - 输出：10 个 `Paper` 对象，含 author_names（已有字段，`schemas.py:64`）
  - 扩展 Paper model：新增 `abstract` 和 `institutions` 字段（见 §5 数据变更）

### F2：种子论文引用网络构建

- [ ] **F2.1 种子论文间引用关系构建**
  - 输入：10 个 Paper 对象（含 reference_ids）
  - 处理：复用 `CitationNetworkBuilder.build_network()`（`citation_network.py:49`）
    - 现有逻辑已只在 main_ids 之间建边（`citation_network.py:95-99`），完全适用
  - 输出：10 节点有向图，边 = 论文间引用关系

- [ ] **F2.2 路径标签覆盖社区检测**
  - 输入：build_network 输出的 GraphResponse + 种子数据的 path 标签
  - 处理：用手工 path 标签（A=0, B=1, C=2, D=3）覆盖 Louvain 社区编号
    - 在 `build_network` 之后、返回之前，替换每个节点的 `community` 值
    - 替换 `metadata.community_names` 为路径名称映射
  - 输出：GraphResponse，community 字段 = 路径编号，community_names = 路径语义名
  - 决策：**手工标签优先**，Louvain 结果仅作为验证参考（见 §2.3 决策）

### F3：种子论文 API 端点

- [ ] **F3.1 GET /api/seed-network**：返回种子论文的引用网络
  - 输入：无参数（种子数据硬编码）
  - 处理：
    1. 读取种子配置 → 调用 `fetch_works_by_ids` 获取元数据
    2. 调用 `build_network` 构建引用网络
    3. 用路径标签覆盖社区编号（F2.2）
  - 输出：`GraphResponse`，与现有 `/api/search` 返回格式完全一致
  - 前端可直接复用 ForceGraph 渲染，零改动

- [ ] **F3.2 GET /api/seed-papers**：返回种子论文详情列表
  - 输入：可选 `path` 参数过滤路径（A/B/C/D）
  - 处理：获取种子论文元数据 + 合并路径标签信息
  - 输出：`List[SeedPaperDetail]`，包含 Paper 全部字段 + path + tech_tags
  - 用途：供三件事报告和前端详情面板使用

### F4：三件事报告生成

- [ ] **F4.1 时空定位报告**
  - 输入：某路径下的论文列表（含 publication_year, cited_by_count）
  - 处理：
    - 统计该路径论文的年份分布
    - 计算引用增速（按年聚合 cited_by_count）
    - 判断技术生命周期阶段（基于论文产出趋势：递增=成长期，平稳=成熟期）
    - 生成时间线描述（最早论文 → 最新论文的演进脉络）
  - 输出：`TemporalReport`（阶段判断 + 时间线描述 + 关键时间节点）

- [ ] **F4.2 人才图谱报告**
  - 输入：某路径下的论文列表（含 author_names, institutions）
  - 处理：
    - 按作者聚合论文数和引用数，排名
    - 按机构聚合，区分学术/工业
    - 提取核心团队（论文数 ≥ 2 或引用数 top-3）
  - 输出：`TalentReport`（核心作者排名 + 机构分布）

- [ ] **F4.3 瓶颈分析报告**
  - 输入：某路径下的论文列表（含 title, abstract, tech_tags）
  - 处理：
    - 从标题/摘要提取高频关键词（TF-IDF 或简单词频统计）
    - 识别该路径解决的核心问题（基于关键词聚类）
    - MVP 阶段：基于手工标签 + 论文标题生成结构化描述
    - 不调用 LLM（10 篇规模手工可控，Phase B 再接入 LLM）
  - 输出：`BottleneckReport`（当前瓶颈 + 已有方案 + 可能方向）

- [ ] **F4.4 GET /api/seed-report/{path}**：返回指定路径的三件事报告
  - 输入：path 参数（A/B/C/D）
  - 处理：调用 F4.1 + F4.2 + F4.3，聚合为完整报告
  - 输出：`InsightReport`（temporal + talent + bottleneck + generated_at）
  - 缓存策略：种子数据不变，报告可内存缓存

### F5：前端 - 种子��络展示

- [ ] **F5.1 种子模式入口**
  - 输入：用户点击"种子论文 Demo"按钮（或 URL 参数 `?mode=seed`）
  - 处理：调用 `GET /api/seed-network` 替代 `GET /api/search`
  - 输出：ForceGraph 渲染种子论文网络
  - 实现：在 `page.tsx` 新增 `mode: 'search' | 'seed'` 状态
    - seed 模式下隐藏 SearchBar，显示种子模式标题
    - 复用现有 ForceGraph + FilterPanel + 社区图例

- [ ] **F5.2 路径图例升级**
  - 输入：`metadata.community_names`（已被 F2.2 替换为路径语义名）
  - 处理：现有社区图例（`page.tsx` 底部 community legend）已读取 `community_names`
    - 只需确保 community_names 值为路径名（如 "Attention 优化"）而非 TF-IDF 生成的名称
  - 输出：图例显示 4 条路径名称 + 对应颜色
  - 改动量：**零前端改动**，后端返回正确的 community_names 即可

### F6：前端 - 三件事报告面板

- [ ] **F6.1 InsightReport 组件**
  - 输入：`InsightReport` 数据（从 API 获取）
  - 处理：渲染三个折叠/展开的报告区块
    - 时空定位：阶段标签 + 时间线描述
    - 人才图谱：作者列表 + 机构标签
    - 瓶颈分析：问题描述 + 方向建议
  - 输出：侧边栏新面板，位于 NodeDetail 下方
  - 样式：遵循现有 `.panel` 模式（`padding: 16px 0; border-bottom: 1px solid #2A2A3E`）
  - 交互：点击社区图例中的路径 → 加载该路径报告 → 展示在侧边栏

- [ ] **F6.2 报告加载与状态管理**
  - 输入：用户点击路径图例
  - 处理：
    - 新增 `useInsightReport(path)` hook
    - 调用 `GET /api/seed-report/{path}`
    - 管理 loading / error / data 状态
  - 输出：报告数据传入 InsightReport 组件
  - API client 新增：`fetchSeedReport(path: string) -> InsightReport`

## 4. 业务规则

1. **种子数据不可变**：10 篇论文 + 4 条路径标签硬编码，MVP 阶段不提供编辑能力
2. **路径标签优先于 Louvain**：社区编号 = 路径编号（A=0, B=1, C=2, D=3），Louvain 结果不展示
3. **混合架构节点**：Jamba（路径 B）同时引用路径 A 和路径 B 的论文，在力导向图中自然悬浮在两个社区之间——不需要特殊处理，引力模型会自动实现
4. **报告生成不调用 LLM**：MVP 阶段基于元数据聚合 + 规则模板生成，Phase B 再接入 LLM
5. **Paper model 向后兼容**：新增字段（abstract, institutions）均为 Optional，不影响现有 `/api/search` 链路
6. **种子模式与搜索模式互斥**：同一时刻只展示一种数据源，切换时清空前一种的状态

## 5. 数据变更

| 操作 | 模型/文件 | 字段/结构 | 说明 |
|------|-----------|-----------|------|
| 新增 | `Paper` (`schemas.py`) | `abstract: Optional[str] = None` | 论文摘要，瓶颈分析用 |
| 新增 | `Paper` (`schemas.py`) | `institutions: List[str] = []` | 作者机构列表，人才图谱用 |
| 新增 | `SeedPaper` (`data/seed_papers.py`) | 完整结构见 F1.2 | 种子论文配置 |
| 新增 | `TemporalReport` (`models/reports.py`) | `stage, timeline_desc, key_milestones` | 时空定位报告 |
| 新增 | `TalentReport` (`models/reports.py`) | `top_authors, institutions, core_teams` | 人才图谱报告 |
| 新增 | `BottleneckReport` (`models/reports.py`) | `current_bottleneck, solutions, next_directions` | 瓶颈分析报告 |
| 新增 | `InsightReport` (`models/reports.py`) | `path, temporal, talent, bottleneck, generated_at` | 聚合报告 |
| 新增 | 前端 `types/api.ts` | `InsightReport` + 子类型 | 与后端对齐 |

## 6. 接口变更

| 操作 | 接口 | 方法 | 变更内容 |
|------|------|------|----------|
| 新增 | `/api/seed-network` | GET | 返回种子论文引用网络 `GraphResponse` |
| 新增 | `/api/seed-papers` | GET | 返回种子论文详情，可选 `?path=A` 过滤 |
| 新增 | `/api/seed-report/{path}` | GET | 返回指定路径的三件事报告 `InsightReport` |
| 扩展 | `OpenAlexClient` | — | 新增 `fetch_works_by_ids(work_ids)` 方法 |
| 不变 | `/api/search` | GET | 现有搜索链路完全不动 |
| 不变 | `/api/health` | GET | 不变 |

## 7. 影响范围

### 后端改动
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `app/models/schemas.py` | 扩展 | Paper 新增 abstract, institutions 字段 |
| `app/models/reports.py` | **新建** | 三件事报告数据模型 |
| `app/data/seed_papers.py` | **新建** | 种子论文配置 |
| `app/services/openalex_client.py` | 扩展 | 新增 `fetch_works_by_ids`，`_parse_work` 提取 abstract + institutions |
| `app/services/seed_network_service.py` | **新建** | 种子网络构建 + 路径标签覆盖 |
| `app/services/insight_report_service.py` | **新建** | 三件事报告生成逻辑 |
| `app/api/routes.py` | 扩展 | 新增 3 个端点 |

### 前端改动
| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/types/api.ts` | 扩展 | 新增 InsightReport 等类型 |
| `src/lib/api-client.ts` | 扩展 | 新增 `fetchSeedNetwork`, `fetchSeedReport` |
| `src/components/InsightReport.tsx` | **新建** | 三件事报告面板组件 |
| `src/components/InsightReport.module.css` | **新建** | 报告面板样式 |
| `src/hooks/useInsightReport.ts` | **新建** | 报告数据获取 hook |
| `src/app/page.tsx` | 扩展 | 新增 seed 模式切换 + 报告面板集成 |

### 不动的文件
- `ForceGraph.tsx` — 零改动，接收 GraphResponse 即可
- `FilterPanel.tsx` — 零改动
- `NodeDetail.tsx` — 零改动
- `citation_network.py` — 零改动（build_network 直接复用）
- 所有现有测试 — 不受影响

## 8. 风险与关注点

1. **OpenAlex 批量查询限制**：pipe-separated filter 有 URL 长度限制，10 个 ID 约 200 字符，安全范围内。Phase B 扩展到 100+ 时需改为分页请求
2. **种子论文间引用关系可能稀疏**：10 篇论文来自 4 条不同路径，跨路径引用可能很少。力导向图中可能出现 4 个孤立簇——这是正确的视觉表达，不是 bug
3. **abstract 字段可能为空**：OpenAlex 部分论文无摘要（`abstract_inverted_index` 为 null）。瓶颈分析需要 fallback 到仅用标题
4. **institutions 数据质量**：OpenAlex 的机构数据可能不完整或有重复（如 "Google" vs "Google DeepMind"）。MVP 阶段不做去重，Phase B 再处理

## 8.5 测试策略

- **测试范围**：
  - 种子数据配置完整性（10 篇论文、4 条路径、所有字段非空）
  - `fetch_works_by_ids` 单元测试（mock HTTP）+ 集成测试（真实 API）
  - 路径标签覆盖逻辑（community 编号正确替换）
  - 三件事报告生成（每个子报告的输入→输出验证）
  - 3 个新 API 端点的请求/响应测试
  - InsightReport 组件渲染测试
- **覆盖率目标**：新增代码 > 80%
- **独立 Test Spec**：否（测试随功能实现，不单独出 spec）

## 9. 待澄清

- [x] 手工标签 vs Louvain：**决策已定**，手工标签优先
- [ ] 瓶颈分析的深度：MVP 是纯规则模板还是需要简单 NLP（TF-IDF）？
  → 建议：MVP 用规则模板（基于 tech_tags + 论文标题关键词），Phase B 加 TF-IDF
- [ ] 种子模式的入口形式：独立页面 vs 当前页面内切换？
  → 建议：当前页面内切换（`?mode=seed`），复用所有现有组件

## 10. 技术决策

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 种子数据存储 | JSON 文件 / Python 模块 / DB | Python 模块 | 类型安全，IDE 补全，10 篇不需要 DB |
| 批量获取方式 | 逐个请求 / filter 批量 | filter 批量 + fallback | 1 次请求拿大部分，个别 ID 不支持 filter 的单独请求 |
| 引用边来源 | OpenAlex refs / 手工定义 | **手工定义** | OpenAlex 对 arXiv 预印本无引用数据，手工定义已知演化关系 |
| 路径标签实现 | 修改 build_network / 直接构建 | **直接构建** | 跳过 Louvain，直接用手工路径构建 GraphResponse |
| 报告生成方式 | LLM / 规则模板 / 硬编码 | **硬编码** | MVP 10 篇，报告内容手写确保准确 |
| 前端报告触发 | 自动加载 / 点击加载 | 点击加载 | 按需请求，不浪费带宽 |
| 可视化布局 | 力导向 / 泳道式 | **泳道式** | X=年份 Y=路径泳道，清晰展示技术演进 |
| abstract 获取 | inverted_index 重建 / 额外 API | inverted_index 重建 | OpenAlex 免费提供，无需额外请求 |

## 11. 执行日志

| Task | 状态 | 实际改动文件 | 备注 |
|------|------|-------------|------|
| F1.1 种子论文 ID 查找 | 待开始 | — | 需要先手动查 OpenAlex |
| F1.2 种子数据定义 | 待开始 | `app/data/seed_papers.py` | — |
| F1.3 批量元数据获取 | 待开始 | `openalex_client.py`, `schemas.py` | — |
| F2.1 引用网络构建 | 待开始 | — | 复用现有代码 |
| F2.2 路径标签覆盖 | 待开始 | `seed_network_service.py` | — |
| F3.1 seed-network 端点 | 待开始 | `routes.py` | — |
| F3.2 seed-papers 端点 | 待开始 | `routes.py` | — |
| F4.1-4.3 报告生成 | 待开始 | `insight_report_service.py` | — |
| F4.4 seed-report 端点 | 待开始 | `routes.py` | — |
| F5.1 种子模式入口 | 待开始 | `page.tsx` | — |
| F5.2 路径图例升级 | 待开始 | — | 可能零改动 |
| F6.1 InsightReport 组件 | 待开始 | `InsightReport.tsx` | — |
| F6.2 报告加载 hook | 待开始 | `useInsightReport.ts`, `api-client.ts` | — |

## 12. 审查结论

（待 reviewer agent 审查后填写）

## 13. 确认记录（HARD-GATE）

- **确认时间**：
- **确认人**：
