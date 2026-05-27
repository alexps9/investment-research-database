# 项目状态

> Claude 每次新会话先读这个文件。用户 review 后更新。
> **最后更新**: 2026-05-27

---

## 当前阶段

World Model 技术路线图 — 增量迭代期（大框架已成型，填充内容 + 打磨 + 响应团队反馈）

## 待做 Action Items

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 2 | 范式分类 taxonomy 重构 | P0 | 讨论中 | 见 `specs/还没收敛/taxonomy-重构讨论.md`；待 Thomas 对齐 |
| 4 | 补充论文数据量（自动驾驶/游戏 VR） | P1 | 待做 | knowledge/ 中有综述可提取 |
| 5 | 论文 Panel 完善：点击节点→机构/问题/insight | P1 | 待做 | 与叶律协作 |
| 6 | 接入论文分析 skill | P1 | 待做 | 琪琪已有 skill |
| 7 | 统一 entity taxonomy（对齐团队 network 数据库） | P1 | 待做 | 与 Thomas 协作 |
| 8 | Impact 动态追踪（citation 增长→节点大小变化） | P2 | 待做 | spec: `！impact scrolling rubric.md` |
| 9 | Citation 类型分析（继承/对比/借鉴） | P2 | 进行中 | video_gen lane 已标注；MVP 脚本可用；其他 lane 待做 |
| 10 | 参考 EEMTR 网站风格 | P2 | 已完成 | `knowledge/product/competitive-research.md` |
| 11 | Era 划分优化：倒推热度分布 | P2 | 待做 | |
| 12 | 图谱定期刷新机制 | P2 | 待做 | |
| 13 | 飞书多维表格双向同步 | P1 | 已完成 | `scripts/lark_sync.py` |
| 14 | Cluster 布局 Phase 1（引力井） | P1 | 已完成 | v2 页面已用聚类布局；Phase 2(Leiden) 待论文 300+ 时再做 |
| 15 | v2 页面溢出修复 | P1 | 已完成 | SVG 改 width:100% + viewBox；右边距增大 |
| 16 | 后端 API 接入前端 | P1 | 已完成 | 移除 JSON fallback，纯 API 驱动；Table CRUD 视图 |
| 17 | 论文数据扩展（snowball） | P1 | 已完成 | 177 篇；expand_from_seeds.py；小论文补充+impact算分 |
| 18 | Overview 投影 Detail 布局 | P1 | 已完成 | Overview Y 轴从 computeRowPositions 归一化映射 |
| 19 | 选中交互（黑色描边环） | P1 | 已完成 | 点击→黑边标识+侧边栏；Overview 点大点→跳 Detail+选中 |
