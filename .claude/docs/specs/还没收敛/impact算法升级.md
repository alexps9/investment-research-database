如果将来确实需要非线性，比较实际的升级路径是：

  1. Citation age decay — 同样 50 citations，2025 年的论文比 2019 年的含金量高得多。可以用 citations / 
  expected_citations_for_age 而不是 raw percentile
  2. Graph-based（PageRank 变体） — 用 builds_on 关系做引用图，被"高分论文"引用的权重更高。但需要 builds_on
  数据完善
  3. Pairwise learning to rank — 你给 20 组 "A > B" 的判断，算法自动学权重。但 20 组不够训练