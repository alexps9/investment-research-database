# 前端改造 + 交互增强（V2）

> status: apply
> created: 2026-04-21
> complexity: 🔴复杂

## 1. 背景与目标

**为什么做**：
将项目改造为"技术路线洞察系统"。当前问题：力导向图是一堆球，看不出技术演化路径，社区无语义名称，引用数滑块不好用。

**做完后的效果**（演示验收标准）：
1. 搜索 "transformer"，图中 X 轴 = 年份（左旧右新），一眼看到技术演化时间线
2. 同社区节点聚成团簇，不同社区之间有明显间距
3. 每个社区有自动生成的语义名称（如"Vision Transformer"、"Attention"），显示在图例和图上
4. 引用数滑块用对数刻度，低区间精细可调（0→10→50→200→1000→5000+）
5. 引用箭头方向：老论文 → 新论文（知识流动方向）
6. Hover 高亮关联节点，点击显示详情
7. 核心论文（Top 5）有橙色圆环
8. **深色 UI**（深蓝/黑背景，白色文字，橙色强调）
9. 所有 UI 中文

**搜索 "transformer" 必须包含的论文**（验收底线）：
- "Attention Is All You Need" (2017, ~120k citations)
- "BERT: Pre-training of Deep Bidirectional Transformers" (2018, ~90k)
- "An Image is Worth 16x16 Words" / ViT (2020, ~30k)
- "Swin Transformer" (2021, ~15k)
- 至少 1 篇 2023+ 论文

**搜索逻辑**：OpenAlex 按 `cited_by_count:desc` 排序，限定 `Computer Science` 概念 + 2015-2026 年份，取前 100 篇。只保留主论文之间的引用边（无 placeholder 节点）。

**验收标准（搜 "transformer" 后的图应该是）**：
- [ ] 节点数 100，边数 > 100（主论文间互引足够密）
- [ ] 能看到年份轴（2015→2025+），节点从左到右按年份排列
- [ ] 至少 3 个明显的社区色块（不是所有球一个颜色）
- [ ] 社区名有意义（如 Vision Transformer / Object Detection / Language），不是 "Good / Point"
- [ ] Hover 节点能看到 "Attention Is All You Need" 等标题
- [ ] 右侧有社区名标签
- [ ] 深色 UI，不能有白色背景

## 2. 代码现状（Research Findings）

### 2.1 已完成（V1）

| 功能 | 文件 | 状态 |
|------|------|------|
| 双栏布局 | `page.tsx`, `page.module.css` | ✅ |
| 年份/引用数滑块 | `FilterPanel.tsx`, `useGraphFilter.ts` | ✅ 但引用数是线性刻度，不好用 |
| 节点详情 | `NodeDetail.tsx` | ✅ |
| 社区着色 | `ForceGraph.tsx` COMMUNITY_COLORS | ✅ 低饱和度色 |
| Hover 高亮 | `ForceGraph.tsx` nodeCanvasObject | ✅ |
| 社区聚类力 | `ForceGraph.tsx` d3Force('cluster') | ✅ 但没有时间轴 |
| 有向箭头 | `ForceGraph.tsx` linkDirectionalArrow | ✅ |
| 社区图例 | `page.tsx` legendItems | ✅ 但标签是"社区 1/2/3"，无语义 |
| 中文 UI | 全部组件 | ✅ |

### 2.2 待改进

1. **看不出技术路线** → 需要 X 轴=年份的时间线布局，让演化方向可视化
2. **社区名称无意义** → 需要从社区内论文标题提取关键词作为社区名
3. **引用数滑块不好用** → 引用数分布是幂律分布，线性滑块导致前 1% 范围才有用

## 3. 功能点（V2 新增）

- [ ] **F7 时间线布局**：X 轴固定为年份，Y 轴仍由力导向计算。节点按发表年份水平分布，同年份的纵向散开。
- [ ] **F8 社区自动命名**：后端分析每个社区内论文标题，提取 TF-IDF 最高的关键词作为社区名。返回在 metadata 中。
- [ ] **F9 引用数对数滑块**：滑块值映射为对数刻度（0, 10, 50, 100, 500, 1000, 5000+），低区间可精细调节。

## 4. 技术方案

### F7 时间线布局
- 用 `d3Force('x')` 按 `publication_year` 设置 X 目标位置
- 保留 `d3Force('y')` 的社区聚类力（Y 轴按社区分组）
- 保留 `d3Force('charge')` 节点间斥力
- 效果：同年论文纵向排列，跨年论文横向展开 = 时间线

### F8 社区自动命名
- 后端：在 `citation_network.py` 的社区检测后，对每个社区的论文标题做词频分析
- 去掉停用词后取 Top 2 关键词拼接为社区名
- 返回格式：`metadata.community_names: { "0": "Attention Optimization", "1": "Vision Transformer", ... }`
- 前端：图例 + 图上标签使用后端返回的社区名

### F9 引用数对数滑块
- 定义刻度数组：`[0, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]`
- 滑块 position (0-11) 映射到对应值
- 显示实际值而非 position

## 5. 数据变更

| 操作 | 字段 | 说明 |
|------|------|------|
| 新增 | `GraphMetadata.community_names` | `Dict[str, str]` 社区 ID → 名称 |

## 6. 接口变更

| 接口 | 变更内容 |
|------|----------|
| `GET /api/search` | response.metadata 新增 `community_names` 字段 |

## 7. 影响范围

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/app/services/citation_network.py` | 修改 | 社区命名逻辑 |
| `backend/app/models/schemas.py` | 修改 | GraphMetadata 加 community_names |
| `frontend/src/types/api.ts` | 修改 | GraphMetadata 加 community_names |
| `frontend/src/components/ForceGraph.tsx` | 修改 | 时间线 X 轴布局 |
| `frontend/src/components/FilterPanel.tsx` | 修改 | 对数刻度滑块 |
| `frontend/src/hooks/useGraphFilter.ts` | 修改 | 对数值映射 |
| `frontend/src/app/page.tsx` | 修改 | 图例使用社区名 |

## 8. 风险与关注点

- **风险1**：社区命名质量差 → 用 bigram 而非 unigram，去掉通用词（"model", "learning"）
- **风险2**：时间线布局节点重叠 → 增加同年份节点间的 Y 轴斥力
- **风险3**：对数滑块用户不理解刻度 → 显示实际值标签

## 9. 待澄清

- [x] 不加 SPECTER2 → 已确认
- [x] 社区名用英文（论文标题是英文）→ 合理

## 10. 执行日志

| Task | 状态 | 实际改动文件 | 备注 |
|------|------|-------------|------|
| V1 F1-F6 | ✅ 完成 | page/ForceGraph/Filter/NodeDetail/SearchBar + hooks | 双栏+过滤+着色+高亮+详情 |
| V2 F7 时间线布局 | ✅ 完成 | ForceGraph.tsx | fx/fy 固定坐标方案 |
| V2 F8 社区命名 | ✅ 完成 | citation_network.py, schemas.py, api.ts, page.tsx | Louvain resolution=0.8 + 合并 singleton |
| V2 F9 对数滑块 | ✅ 完成 | FilterPanel.tsx | CITATION_TICKS 刻度数组 |
| V3 Top-N 常驻标签 | ✅ 完成 | ForceGraph.tsx | Top 5 节点橙色标签常驻，hover 节点白色标签 |

---

## 11. 数据质量问题讨论（2026-04-21）

### 11.1 现象

搜索 "transformer" 返回 100 篇论文，但**核心奠基论文缺失**：
- "Attention Is All You Need" (Vaswani 2017, ~120k citations) — **不在结果中**
- "BERT" (Devlin 2018) — **不在结果中**
- "An Image is Worth 16x16 Words" / ViT (Dosovitskiy 2020) — **不在结果中**

### 11.2 根本原因

OpenAlex `/works?search=transformer` 使用**全文关键词匹配**，不是语义搜索：
- "Attention Is All You Need" 标题里没有 "transformer" 这个词
- BERT 标题里没有 "transformer"
- ViT 标题里没有 "transformer"
- 排序是 `cited_by_count:desc`，但搜索过滤先于排序 → 高引用奠基论文被过滤掉了

### 11.3 可行解决方案（已讨论，待决策）

**方案 A：Concept-based 搜索（推荐，成本低）**
- OpenAlex 有 `concepts` 字段，"Transformer" 对应 concept ID `C119857082`
- 用 `filter=concepts.id:C119857082` 替换 `search=transformer`
- 优点：能抓到所有带 Transformer 概念的论文（包括奠基作）
- 缺点：concept 标注可能有噪声，用户输入和 concept ID 之间需要映射层

**方案 B：多查询合并**
- 对 query="transformer" 额外触发 query="attention mechanism"、"vision transformer" 等变体
- 合并去重后取 top 100
- 缺点：API 调用数 ×3，延迟增加

**方案 C：Seed Paper + Citation Snowball（最准确，成本高）**
- 允许用户输入 1-3 篇种子论文（DOI 或 OpenAlex ID）
- 系统从种子论文出发，抓取其引用树和被引树（2 跳）
- 这样能保证奠基论文在图里
- 缺点：需要新增 UI（种子输入框）+ 后端 citation crawl 逻辑

**方案 D：Hybrid（概念 + 关键词）**
- 先用 concept API 查 "transformer"→ concept ID
- 再用 `filter=concepts.id:xxx&sort=cited_by_count:desc` 取 top 100
- 对不常见查询（无匹配 concept）fallback 到关键词搜索

### 11.4 决策记录（2026-04-21）

**选择方案 A（Concept ID 过滤）**，已实现。

实现要点：
- `_resolve_concept_id(query)` 先调 `/concepts?search=<query>` 拿到 top concept ID
- 用 `concepts.id:<id>,concepts.id:C41008148` 过滤，**不加 `type:article`**（关键 ML 论文如 NeurIPS 在 OpenAlex 里是 `preprint` 类型）
- 取 2×limit 条结果，按 concept score ≥ 0.4 过滤噪声，再取 top `limit`
- 无匹配 concept 时 fallback 到关键词搜索

效果对比：

| 指标 | 改进前（关键词搜索） | 改进后（Concept 搜索）|
|------|---------------------|----------------------|
| Attention Is All You Need | ❌ 不在结果 | ✅ 在结果 |
| ViT (An Image is Worth 16x16) | ❌ 不在结果 | ✅ 在结果 |
| Links（100节点） | 111 | 323 |
| Communities | 11 | 4-5 |

已知遗留问题：
- OpenAlex 数据错误导致 2 篇无关论文出现在结果中（MizAR、AI-Assisted Pipeline），引用数虚高。
  这是 OpenAlex 上游数据质量问题，concept score 过滤无法区分（噪声论文 score 反而更高）。
  接受 2/100 的噪声率，不额外处理。
