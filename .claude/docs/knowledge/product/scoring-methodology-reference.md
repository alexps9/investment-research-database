# 评分方法论参考 — 从 Intel Skills 学到的

> 来源：`~/Desktop/skills/` 项目（twitter-hypothesis-validator + intel-run-watch）

---

## 1. 核心思路

这套系统用**多维加权 + 动态阈值 + 分层信号**的方式做情报评分，不依赖单一指标。

---

## 2. Twitter 评分模型（score-tweets.py）

### 2.1 基础评分公式

```python
score = (likes×1 + retweets×3) × tier_weight × originality
```

- tier_weight：信源可信度权重（tier_1a=4, tier_1b=3, tier_2=2, tier_3=1）
- originality：原创=1.0，转推=0.3

**启示**：不只看绝对量（citation），还要看来源质量（venue tier）和原创贡献。

### 2.2 速度检测（engagement_rate）

```python
engagement_rate = score / age_hours
```

- 用百分位动态分档（前20% = surging，20-60% = steady，后40% = fading）
- age 最小钳位 0.5h，避免极新内容虚高

**启示**：对论文的 rising signal 检测 = citation_growth_rate / paper_age。新论文短时间被大量引用 = surging。

### 2.3 弱信号识别

```python
# Tier 1a 账号中，score 低于当天 tier_1a 中位数的 = 弱信号
median_1a = sorted(tier1a_scores)[len // 2]
weak = [t for t in tweets if t.tier == "tier_1a" and t.score < median_1a]
```

**启示**：顶级机构（DeepMind/OpenAI）发的低 citation 论文可能是"尚未被市场发现的早期信号"。

---

## 3. 多维分析框架（五维情报）

| 维度 | Twitter 实现 | 我们的论文对应 |
|------|-------------|---------------|
| 高速扩散 | engagement_rate 前 20% | citation 增速最快的论文 |
| 三角验证 | 多账号独立讨论同话题 | 多团队独立做同方向研究 |
| 级联根节点 | conversation_id 追踪话题源头 | builds_on 追溯原始架构 |
| 专家分歧 | Tier1 账号对立观点 | 顶级团队走不同路线（VLA vs RL） |
| 弱信号预警 | 顶级源+低传播 | 顶级机构+低citation+极新 |

---

## 4. 叙事聚类（TF-IDF + Jaccard）

- 对每条推文做 TF-IDF 提取关键词（top 8）
- Jaccard 相似度 >= 0.15 → 硬归属同一 cluster
- 软归属（0.10-0.15）→ 跨话题关联，供分析参考
- 按 engagement_score 排序选种子，高影响力优先做簇中心

**启示**：论文聚类可用类似方法——关键词/paradigm 重叠 + builds_on 图结构做聚类，识别"热门研究方向"。

---

## 5. 动态阈值（非固定分数线）

所有分档都用**当天数据的百分位**而非固定阈值：

```python
# 速度分档
rates = sorted(all_rates, reverse=True)
p20 = rates[int(len * 0.20)]  # 前 20% = surging
p60 = rates[int(len * 0.60)]  # 20-60% = steady

# 弱信号阈值
median_1a = sorted(tier1a_scores)[len // 2]  # 动态中位数
```

**启示**：我们的 impact score 分档也应该用百分位，不设固定线。这样数据量增加时不需要手动调参。

---

## 6. 信号特征沉淀（memory.md）

intel-run-watch 的 Step 9.5：

- 每次分析后提炼"高价值信号模式"和"低价值信号特征"
- 写入 watch 的 memory.md
- 超过 15 条归档，防止无限增长
- 下次分析时读取 memory，调整过滤权重

**启示**：我们的 impact_override 可以进化为类似机制——积累"什么样的论文应该被高估/低估"的 pattern，逐步减少手动覆盖。

---

## 7. 对我们 Impact Rubric 的具体改进建议

| 原 spec 设计 | 学到后的改进 |
|-------------|-------------|
| 固定权重 0.4/0.3/0.3 | 先跑百分位，看结果再调，权重可随数据量变化 |
| citation_score 按年份百分位 | 加入 **citation_rate**（citations / paper_age_months），检测 rising signal |
| venue_score 5档 | 加入**机构 tier**（类比 twitter tier_weight）：DeepMind=4, 顶校=3, 普通=2 |
| lineage_score = follower_count | 区分**级联深度**（被引论文又被引 = 深层影响）vs 单层 fan-out |
| 无弱信号检测 | 新增：顶级机构 + 低 citation + 发布 < 6月 = 弱信号候选 |
| 无速度维度 | 新增：citation_rate = cited_by_count / age_months，检测加速度 |

---

## 8. 总结公式（改进版）

```python
# 基础 impact
base_score = (
    0.35 × citation_percentile_in_year
  + 0.25 × venue_tier_score
  + 0.25 × lineage_depth_score
  + 0.15 × institution_tier_weight
)

# 动态信号（rising detection）
citation_rate = cited_by_count / max(age_months, 1)
is_rising = citation_rate > percentile_80(all_citation_rates)

# 弱信号检测
is_weak_signal = (institution_tier >= 3) and (citation_percentile < 50) and (age_months < 6)

# 最终 size
if impact_override: return override
elif is_rising: return "lg"  # rising signal 强制大圈
elif base_score >= P75: return "lg"
elif base_score >= P35: return "md"
else: return "sm"
```
