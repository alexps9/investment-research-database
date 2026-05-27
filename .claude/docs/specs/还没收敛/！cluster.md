# Cluster 布局

## Problem

当前 v2 全局视图中，同一 Row 内节点位置是随机散射的，不反映引用关系。导致：
- 有强继承关系的论文可能离得很远
- 无关的论文可能凑在一起
- 用户无法从空间位置获取"谁跟谁一伙"的直觉

论文持续增长（当前 ~150，预计到 300+），手工管理越来越难。

## 目标

空间距离 = 引用关系强度。让用户一眼看出：
1. 每个大节点（Foundation）周围哪些小节点（Adaptation）在跟进它
2. 哪些 Foundation 之间存在传承链（如 Dreamer V1→V2→V3 应该靠近）
3. 哪条技术路线最近很活跃（密度高）、哪条已经断流（稀疏）

## 约束

- X 轴 = 时间为主，允许 ±半季度内游走（不能完全锁死，否则同季度竖排）
- Y 轴 = 关系维度，由算法决定
- 同季度多个大节点必须错位，不能重叠
- 节点不能超出 Row 的 Y 边界
- 保持现有颜色体系（lane color）不变
- 时间窗口外的论文不渲染（避免 clamp 到边界导致堆叠）

## 已实现：Phase 1 引力井（v2 页面）

- Union-find 按引用链分组 Foundation（`shape !== 'square'`）
- Y band 按 cluster 大小比例分配
- X = time + ±40% 季度宽度 jitter
- Y = band center + 随机偏移
- 径向碰撞推开（30 次迭代）
- Adaptation（`shape === 'square'`）分两类布局：
  - 有 connection → 围绕目标 Foundation 散布（angle+dist）
  - 无 connection → stratified Y 均匀分布（避免底部堆积）
- 行高动态：≤6 篇 120px，≤15 篇 160px，>15 篇每多一篇 +8px
- 小论文（impact < 20）施加 Gaussian blur 滤镜（stdDeviation=1.8）+ 降低 opacity（0.18）
- Overview 视图从 Detail 的 `computeRowPositions` 投影而来，不再独立随机

### 选中交互

- 点击论文 → 黑色粗描边环（2.5px #18181B）标识选中
- 侧边栏展示详情 + 引用关系
- 不淡化其他论文（避免视觉干扰）
- Overview 中点击大点 → 切 Detail + 选中该论文

## 未来：Phase 2 Leiden 聚类

- 后端用 Leiden/Louvain 算法做社区发现，输出 cluster_id
- 前端按 cluster 分 Y 区间，组内用碰撞斥力排布
- 边的粗细反映引用权重（inherits > borrows > competes）
- 触发条件：论文到 300+ 时，手工 row 跟不上

### 已有可复用代码

`backend/app/services/citation_network.py` 中 `CitationNetworkBuilder.calculate_communities()`:
- 算法：Louvain（resolution=0.8，生成更少更大的社区）
- 有向图转无向后做社区发现
- Singleton 合并：大小为 1 的社区合并到邻居社区，避免碎片化
- 社区自动命名：从标题提取 bigram/unigram 关键词
- 性能目标：500 节点 < 5 秒

Phase 2 可直接复用这套逻辑，输入换成 world-model-data.json 每个 lane 的论文即可。如需更稳定的社区划分可替换为 Leiden（`leidenalg` 包）。

## 验收标准

- [x] 有引用关系的节点在视觉上明显聚集
- [x] 同季度大节点不重叠（径向碰撞）
- [x] Overview 与 Detail 空间位置一致（投影映射）
- [x] 小论文虚化，不干扰大论文的可读性
- [x] 选中论文有明确视觉反馈（黑色描边）
- [ ] 切换时间筛选器后布局仍然稳定（不跳动）
- [ ] 性能：300 节点内布局计算 < 100ms

## 待确认

- [ ] Phase 2 的 cluster 结果是替代手工 row，还是作为 row 内的子分组？
- [ ] 边权重数据来源？当前 connections.type 够用吗？
- [ ] 是否需要"聚类 vs 手工"切换开关？
