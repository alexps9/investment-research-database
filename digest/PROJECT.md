# HH Research

> AI 投融资团队的研究操作系统 — 让 5-10 人团队每天比同行多一手信息，每周多一个判断，每月多一个候选项目或人才。

**Status：** v0.2（2026-05-21）｜内部文档｜作者：郭昊霖 + Claude

---

## 目录

0. [TL;DR — 一分钟读完](#0-tldr--一分钟读完)
1. [项目愿景与差异化](#1-项目愿景与差异化)
2. [产品架构](#2-产品架构)
3. [系统架构（5 层）](#3-系统架构5-层)
4. [数据模型](#4-数据模型)
5. [核心机制](#5-核心机制)
6. [技术栈与决策](#6-技术栈与决策)
7. [当前实施状态](#7-当前实施状态)
8. [路线图 V1-V4](#8-路线图-v1-v4)
9. [评分体系详解（Researcher Mapping）](#9-评分体系详解researcher-mapping)
10. [关键风险与对策](#10-关键风险与对策)
11. [资源索引](#11-资源索引)
12. [Onboarding 速查](#12-onboarding-速查)

---

## 0. TL;DR — 一分钟读完

**HH Research 是什么：** 服务于 HH 5-10 人投融资团队（最终扩展到全公司订阅）的研究系统。每天从 X、arXiv 等信号源 + 专家访谈中提取信号，沉淀到知识图谱（含 paper / researcher / insight / landscape），最终输出三类资产辅助"研究方向决策"和"触达决策"。

**对标与差异化：** 对标奇绩 alpha sight。差异点：alpha sight 只做 paper 摘要的日汇总；HH Research 要做 actionable insight + 三资产协同 + 反馈学习闭环。

**当前状态（2026-05-21）：** 全链路已生产化 — 4 源采集（arXiv + X + OpenAlex + RSS）+ 5 赛道 LLM 抽取（Bedrock Sonnet 4.6 并发 10 workers，~10x 加速）+ 飞书 wiki docx 自动发布（v4 XML 格式）+ 锚点跳转两阶段注入 + author lookup post-process 自动填 RM 表 + launchd 三 job（pipeline / 健检 / 09:30 企业群广播）已上线。下一阶段焦点：3 通道推送（飞书企业群 ✅ / 飞书 1-on-1 bot 等 leader / H Link 等 IT）+ 20+ 投前同事白名单测试 + Insights 内容质量迭代（详见 [docs/roadmap/2026-05-21-product-roadmap.md](docs/roadmap/2026-05-21-product-roadmap.md)）。

**主要使用方：** 第一阶段 5-10 人 active 用户（含 5 人维护团队），第二阶段全公司飞书订阅推送。

---

## 1. 项目愿景与差异化

### 1.1 核心问题

奇绩 alpha sight 等同类产品只做 paper work 每日汇总，**无法高效凝聚为辅助投融资决策的 insight**。日报与知识库等资产协同性不足，每天产出大量 paper 摘要后，团队没有可被复用的认知资产。

### 1.2 HH Research 的差异化定位

把"信号 → 认知 → 决策"做成一个**有学习闭环**的研究操作系统：

- **不止做日报**：日报只是知识库的呈现形式之一，知识库才是底座
- **insight 必须经人审**：避免"自动生成的金句"污染知识库
- **决策反馈回路**：HH 每次的研究方向选择 / 触达决策都回流到系统，让信号源、landscape 权重随决策迭代

### 1.3 服务的决策类型（明确边界）

按优先级：

1. **研究方向决策**（季级）：HH 接下来 6 个月主投哪个研究方向
2. **触达决策**（周级）：本周该约谁聊
3. ~~投资决策~~（不主要服务，有需求时另起 brief）

**重要：** 评分体系不学 a16z / 红杉那套"founder potential"，因为 HH 不投资。HH 评分侧重 **research direction signal + contact value**。

### 1.4 受众与边界

| 阶段 | 用户群 | 接入方式 | 状态 |
|---|---|---|---|
| V0（已过） | 5-10 人 active 用户（含维护团队） | 飞书 Bitable + 飞书云文档 | ✅ |
| **V1 当前** | **20+ 投前同事白名单测试** | 飞书企业群广播 ✅ / 飞书 1-on-1 bot ⏳ / H Link 1-on-1 🛠️ | 🚀 5.22 跑通 5 人 → 5.23-24 扩 20+ |
| V2 下一阶段 | 全公司飞书订阅推送 | 飞书群 bot push | 远期 |
| 未来 | 不对外卖（不是泛 AI 资讯产品） | — | — |

---

## 2. 产品架构

### 2.1 信号 + 专家 → 三资产 → 决策（含反馈环）

```
[输入]              [中间资产]                              [输出]

信号 ──→  日报  ──→  知识库 (landscape/paper/insight) ←辅助/查询→ 决策
专家 ──→         ──→
  ↑                       ↓
  └─ 推荐/筛选 ──── Researcher mapping ──→ 决策
                      │
                      └─ 迭代 ──→ 信号
```

### 2.2 两条输入

| 输入 | 性质 | 数据源 |
|---|---|---|
| **信号** | 高频、广覆盖、噪声多 | 当前：X + arXiv；V4：公众号 + 小红书 |
| **专家** | 低频、高密度、信号外 | 推荐 / 内部访谈 / 一手交流；由 Mapping 反馈推荐 |

### 2.3 三类资产

| 资产 | 形态 | 使用模式 |
|---|---|---|
| **日报** | 时间轴 markdown | push（每日 09:30 推送飞书群 + 云文档） |
| **知识库** | landscape ontology + paper / insight 卡片 | pull（按需检索） + RAG query |
| **Researcher Mapping** | 人物档案 + 关系图 + 4 维评分 | (a) 静态档案 / (b) 周一推荐 / (c) NL query |

### 2.4 反馈环（最重要的设计）

系统不是单向 pipeline。三条反馈环让系统能自我迭代：

1. **Mapping → 信号**：评分高的 researcher 自动加入信号源白名单
2. **Mapping → 专家**：推荐谁可以触达，访谈后产物喂回知识库
3. **决策 → landscape / 信号源**：HH 每次的研究方向决策 / pass 决策回流，调整 landscape 权重和白名单优先级

> ⚠ 没有反馈环这个项目就是个 ETL pipeline；有反馈环它才是研究操作系统。

---

## 3. 系统架构（5 层）

### 3.1 分层图

```
┌────────────────────────────────────────────────────────────┐
│ Layer 5  Surface Views（产品形态）                          │
│ 日报(push)  知识库浏览  Mapping(a/b/c)  RAG bot              │
└────────────────────────────────────────────────────────────┘
                          ↑
┌────────────────────────────────────────────────────────────┐
│ Layer 4  Query API(4-tool 抽象,借鉴 MiroFish)               │
│ quick_lookup  panorama_view  deep_query  interview_researcher │
└────────────────────────────────────────────────────────────┘
                          ↑
┌────────────────────────────────────────────────────────────┐
│ Layer 3  Knowledge Graph(系统核心)                          │
│ 节点:Paper / Researcher / Org / Insight / Concept(label)    │
│ 边:AUTHORED / AFFILIATED / CITES / DISCUSSED_IN_DAILY 等    │
│ 存储:Bitable 双向链接(V1-V2) → Kuzu(V3) → Neo4j(V4 if 需)   │
│ Vault:本地 git markdown (single source of truth) + 飞书镜像 │
└────────────────────────────────────────────────────────────┘
                          ↑
┌────────────────────────────────────────────────────────────┐
│ Layer 2  Extract & Enrich                                   │
│ signal_extractor  paper_pdf_reader  researcher_card_builder │
│ insight_proposer  multi_agent_scorer (V3)                   │
└────────────────────────────────────────────────────────────┘
                          ↑
┌────────────────────────────────────────────────────────────┐
│ Layer 1  Ingest                                             │
│ arxiv_collector  x_collector  (V4: 公众号 + 小红书)          │
│ expert_interview_uploader (新)                              │
└────────────────────────────────────────────────────────────┘
```

### 3.2 心智模型切换：从 ETL 到知识图谱中心

**容易误入的歧途：** 把项目当成 "信号 → 日报" 的线性 ETL。

**正确的视角：** 知识图谱是中心，日报、Mapping、RAG 都是它的 view。这个切换决定了 schema 设计、技术选型、路线优先级。

### 3.3 关键设计原则

1. **三类资产是同一底层数据库的三个 view**，不是三个独立系统
2. **人在环里**（human-in-the-loop）是质量唯一保证（insight 入库、月度 landscape 复核、决策反馈）
3. **决策反馈是迭代信号源和 landscape 权重的唯一依据**

---

## 4. 数据模型

### 4.1 节点

| 节点 | 字段数 | 关键字段 |
|---|---|---|
| **Paper** | 25 | 一作 / 通讯 / 共作（双向链接到 Researcher）、主单位、主方向、子标签、引用数、Twitter 热度、关键 takeaway、与我们关注的关联 |
| **Researcher** | 33 | 中英文名、当前阶段（13 档：博一 → 教授 → 创业者）、当前机构、导师、全平台联系（X / 知乎 / 小红书 / GitHub / Google Scholar）、4 维评分、触达路径 L0/L1/L2、触达状态 6 档 |
| **Org** | TBD | 名称、tier、HH 内部联系人 |
| **Insight** | TBD | source_type（tweet / interview / synthesis）、status（candidate / approved / rejected）、evidence、reviewer |
| **Concept**（landscape） | 5 | 方向名、中英文、类型（主方向 / 子标签）、热度趋势 |
| **Decision** | 6 | 日期、type（research_focus / meet / pass）、target、reflection_md |

### 4.2 边

```
Paper ──AUTHORED_BY──→ Researcher
Paper ──FROM_ORG──→ Org
Paper ──IN_DIRECTION──→ Concept
Researcher ──AFFILIATED_WITH──→ Org
Researcher ──ADVISED_BY──→ Researcher
Researcher ──FOCUSES_ON──→ Concept
Insight ──CITES──→ Paper
Insight ──ABOUT──→ Researcher / Concept
Decision ──TARGETS──→ Paper / Researcher / Concept / Insight
DailyDigest ──INCLUDES──→ Paper / Insight
```

### 4.3 已设计 schema（mapping 文件夹）

`/Users/haolinguo/claude code/HH researcher mapping/feishu/` 下：

| 文件 | 内容 |
|---|---|
| `researchers_fields.json` | Researcher 表 33 字段定义 |
| `papers_fields.json` | Paper 表 25 字段定义 |
| `directions_fields.json` | Direction 表 5 字段定义 |
| `researchers_seed.json` | 13 位种子 researcher（RUC GSAI 体系，博二-博后） |
| `researchers_verified.json` | 13 位精校版（修正 5 处中文名误写、补充实习经历） |
| `papers_seed.json` | 11 篇种子论文（2023-2026，主单位 RUC GSAI + 大厂合作） |

**主方向枚举（聚焦定位）：** Reasoning Training / Agent Framework / RAG / KG Reasoning / Multimodal Reasoning / User Simulation / Slow Thinking — 高度聚焦 LLM reasoning + agent 方向。

**导师枚举：** 6 位（赵鑫 / 窦志成 / 宋睿华 / 严睿 / 陈旭 / 卢志武）— 全部 RUC GSAI 体系。

---

## 5. 核心机制

### 5.1 Insight 流程（候选 → 人审 → 入库）

| 类型 | 来源 | 自动化 | 是否需人审 |
|---|---|---|---|
| **Paper work** | arXiv / blog / report（有 source 文档） | LLM 抽取直入 | 否 |
| **Insight 候选** | tweet / 访谈金句 | 进日报"观点折叠区"，标记 `candidate=true` | **是**（每周人审 + 至少一条交叉验证） |

**为什么必须人审：** 完全自动化的 insight 入库 6-8 周内一定被 LLM 漂移污染。**人审节点不是 bug 而是 feature** — 强迫团队定期 reflect，本身就是产出。

### 5.2 4 维度 Multi-agent 评分（详见 §9）

| 维度 | 单 agent 负责 | 默认权重 |
|---|---|---|
| 学术影响力 | `bibliometric_agent` | 0.20 |
| 方向匹配 | `topic_fit_agent` | 0.30（HH 最重视） |
| 接触可行性 | `contact_agent` | 0.25 |
| 时间窗口 | `timing_agent`（HH 独创） | 0.25 |

合成用 weighted geometric mean（任一维度 = 0 整体熄火）。

### 5.3 触达路径自动推荐（L0 / L1 / L2）

由"接触可行性分"自动决定：
- ≥ 4 星 → **L1 直接式**
- 2-3 星 → **L0 介绍式**（自动推荐 mutual connection 最强的 HH 网络成员）
- 1 星 → **L2 间接式**（先听 talk / 看博客）

### 5.4 决策反馈环（Decision Table）

5 人维护团队每次做完决策点击 Bitable 的 `+ 决策` 按钮，30 秒填一行 reflection。月度 30-50 条。`feedback_loop.py` 每月跑一次：

- `research_focus` 决策对应的 concept → landscape saliency ↑
- `meet` 决策的 researcher → 信号源白名单 ↑
- `pass` 决策的 researcher / paper → 类似项目降权

**没有这张表，画板里两条反馈环就只是图，不是真行为。**

### 5.5 Vault 同步策略

```
本地 git vault (single source of truth)  ──同步──→  飞书知识库（团队可看可评）
        ↑                                              ↓
        └────────── 评论反向回流 (yaml frontmatter) ──┘
```

- 本地 vault：LLM agent 可直接读写、可 git diff、可脚本化做 RAG
- 飞书知识库：5-10 人协作、评论、推送、移动端
- 单向 markdown → 飞书；评论反向 sync 回 yaml `comments` 字段

**不用 Obsidian Sync 的理由：** Karpathy 的 Obsidian 是 N=1 个人 vault，不适用 5-10 人团队。本地 git + 飞书镜像才是平衡点。

---

## 6. 技术栈与决策

### 6.1 当前 + 规划

| 层 | 工具 | 状态 |
|---|---|---|
| Python | 3.11+ | 在用 |
| LLM | Claude on AWS Bedrock（Opus 4.6 写 digest + Sonnet 4.6 抽信号），bearer token；并发 10 workers + prompt caching | 在用 |
| X 采集 | socialdata.tools（$0.0002/条） | 在用 |
| arXiv 采集 | `arxiv` 2.x | 在用 |
| 飞书 | `lark-oapi` SDK + `lark-cli` 1.0.17 | 在用（user 身份 personal profile） |
| 去重 | SQLite local seen-set | 在用 |
| 图存储 V1-V2 | Bitable 双向链接字段 | 在用（schema 已设计） |
| 图存储 V3 | **Kuzu**（嵌入式单文件图 DB，类比 SQLite 之于 Postgres） | 计划 |
| 图存储 V4+ | Neo4j（如团队 30+ 才考虑） | 视情况 |
| 向量库 | **ChromaDB**（本地单文件，pip install） | V3 引入 |
| Embedding | OpenAI `text-embedding-3-small` 或 BGE-M3 | V3 引入 |
| PDF 阅读 | **Claude 直接吃 PDF**（$0.10-0.30/篇） | V2 引入 |
| 调度 | GitHub Actions（免 VPN） | V1 收尾 |

### 6.2 已敲定决策（D1-D5）

| ID | 决策 | 选择 |
|---|---|---|
| D1 | 图数据库选型 | Bitable → Kuzu (V3) → Neo4j (V4+ if needed) |
| D2 | 向量库 | ChromaDB（本地单文件） |
| D3 | PDF 阅读方案 | Claude 直接吃 PDF（每周 30-50 篇 ≈ $5-10/周） |
| D4 | 评分维度 | 用户 4 维度 schema（学术影响 / 方向匹配 / 接触可行 / 时间窗口） |
| D5 | 决策表填写 | 5 人团队愿意 30 秒填一条 reflection |

---

## 7. 当前实施状态

### 7.1 项目目录分布

| 目录 | 用途 | git |
|---|---|---|
| `/Users/haolinguo/claude code/HH research/` | **HH-Research GitHub 仓库根**（多子项目，本地 = 远程同步） | 绑 GitHub remote |
| `/Users/haolinguo/claude code/HH research/daily-digest/` | **daily-digest 子项目根**（pipeline + 推送代码全部在此） | 本子项目位置 |
| `/Users/haolinguo/claude code/HH research.bak/` | 5.22 重构前的老仓库 + 救援内容（rescued-untracked/） | 兜底用，可随时删 |
| `/Users/haolinguo/claude code/HH researcher mapping/` | Mapping schema + seed 数据 | 独立目录，无 git |

### 7.2 已完成（worktree 中，可执行 / 已测试）

**采集（4 源 + 并发）：**
- ✅ 347 人 whitelist 在飞书 Bitable（含 4 类 URL enrich）
- ✅ `arxiv_collector`：3 通道（author query + category-wide + affiliation regex），category 模式快 40 倍
- ✅ `x_collector`：socialdata.tools，60s per-user 超时
- ✅ `openalex_collector`：24 个 verified 作者
- ✅ `rss_collector`：14 个公司+实验室 feed

**抽取（Bedrock + 并发）：**
- ✅ LLM 切换到 AWS Bedrock（Sonnet 4.6 抽信号 + Opus 4.6 写 digest），bearer token
- ✅ 并发 LLM 抽取（ThreadPool 10 workers，~10x 加速；200 篇 arxiv day 从 95 min → 10 min）
- ✅ HH 5 赛道 schema（认知模型 / 多模态智能 / 世界模型 / AI infra / ai4s）+ tool_use
- ✅ cost tracking with threading.Lock

**写日报（v4 XML pipeline）：**
- ✅ Daily digest v4 XML 输出（MAX_TOKENS=32K，含 callout/table/hr 标签）
- ✅ 双桶路由（papers / news），arxiv→前沿研究 / 推文→行业应用
- ✅ 锚点跳转两阶段注入（`publish_with_anchors.py`：发 + fetch + str_replace anchor URL）
- ✅ Author lookup post-process（自动填 RM 表 4 列：姓名 / 现状 / GitHub / 邮箱）
- ✅ 图片提取（ar5iv 首图 + PyMuPDF PDF 首页 fallback）
- ✅ 日报格式 spec v6.3（头条规则 + 缩写格式 `中文释义（英文缩写）` + 三类卡片）
- ✅ Our Insights v1 prompt（5.19 验证版）

**发布（飞书）：**
- ✅ 飞书 wiki docx 自动发布（`lark_doc_publisher.py`，自动 XML/markdown 检测 + 剥代码栅栏）
- ✅ Media-insert 图片上传 + IM 通知

**生产化定时（launchd 3 job）：**
- ✅ `com.hh-research.pipeline` 00:00 CST 跑 pipeline
- ✅ `com.hh-research.healthcheck` 00:30 健检
- ✅ `com.hh-research.broadcast` 09:30 企业群广播
- ✅ `pmset repeat wakeorpoweron MTWRFSU 09:25:00`（休眠时自动唤醒）

**HRes' aha moment 推送链路：**
- ✅ A 飞书企业群：`broadcast_today.sh` + `send_digest_to_enterprise.py` + 飞书群 webhook + HMAC 签名
- 🛠️ C H Link 1-on-1：`hlink_publisher.py` + `send_digest_to_hlink.py` 代码就绪（dry-run 通过，等凭证）
- ⏳ B 飞书 1-on-1：待 leader 完成企业自建应用创建

**其他：**
- ✅ `regenerate_digest.py`：从 Bitable 复用信号重出 digest（省 $1.7 + 50 min）
- ✅ `run_for_date_cst.py`：CST 语义跑 pipeline
- ✅ ops_metrics 写入

### 7.3 已完成（mapping 文件夹，schema 层）

- ✅ Researchers / Papers / Directions 三表 schema
- ✅ 13 位 verified researcher seed（RUC GSAI 体系，博二-博后）
- ✅ 11 篇 paper seed（2023-2026）

### 7.4 未完成

**V1 当前任务（5.21 产品会议路线图，详见 [docs/roadmap/2026-05-21-product-roadmap.md](docs/roadmap/2026-05-21-product-roadmap.md)）：**

短期（本周 ~ 周末）：
- ❌ TODO-01 (P0 5.22) 3 推送通道跑通 5 人白名单
- ❌ TODO-02 H Link 锚点期望提交给 Max/Leon
- ❌ TODO-03 20+ 同事名单 + open_id 收集
- ❌ TODO-04 扩 20+ 全员 (5.23-24)

中期（下周 ~ 一个月）：
- ❌ TODO-05 (中期 P0) Alert 实时推送系统
- ❌ TODO-06 推送时间窗口切换（BJT 8:00 cutoff + 12:00 broadcast）
- ❌ TODO-07 头条规则 + 实体白名单 boost
- ❌ TODO-08 日报内 hover 释义（Wiki 强绑定）
- ❌ TODO-09 阅读监控埋点
- ❌ TODO-10 Insights 改写（公众号体 + 论文/X 路由）
- ❌ TODO-11 问卷反馈机制（待定）

远期（一个月以上）：
- ❌ TODO-12 个性化推送
- ❌ TODO-13 视频嵌入
- ❌ TODO-14 飞书知识问答接入

**原 V2-V4 未完成（与 5.21 路线图独立）：**
- ❌ mapping 三表的 Bitable 创建脚本（fields JSON 还没 push 到飞书）
- ❌ paper PDF 深读 + markdown vault
- ❌ Insight 候选 / 人审 / 入库流程（与 TODO-10 部分重叠）
- ❌ Researcher 4 维度自动评分（schema 字段已建，逻辑未写）
- ❌ 决策反馈表 (`decisions` 表)
- ❌ Query API 4-tool 抽象
- ❌ RAG bot
- ❌ 中文信号源（公众号 / 小红书）
- ❌ 关系图谱前端接入

---

## 8. 路线图 V1-V4

| 阶段 | 周 | 焦点 | 关键产物 | 月成本 |
|---|---|---|---|---|
| **V1: 日报底座收尾** | 1-3 | 飞书云文档发布 + bot 群通知 + mapping 三表上线 | digest 落地飞书；Bitable 三表创建；vault 目录骨架 | $210 |
| **V2: 知识库 + Mapping(a) + Insight** | 4-9 | PDF 深读 agent；Researcher 静态档案；Insight 候选→人审；landscape 手画导入；Decision 表 | paper md vault；researcher 卡片 200+；insight 表;decision 表 | $260-330 |
| **V3: Multi-agent + RAG + Mapping(b)** | 10-15 | 4 agent 并发评分；ChromaDB embedding；4-tool query API；周一推荐 5 人；feedback_loop.py | weekly_meeting_brief；NL query MVP；月度反馈环 | $330-450 |
| **V4: NL query + 中文源 + 关系图谱** | 16-22 | Mapping(c) NL find；公众号 / 小红书；图谱前端接入；Kuzu 迁移 | query-driven mapping；中文 pipeline；图谱可视化 | $400-700 |

**关键依赖锁：**
- V2 完成前不引入图数据库（Bitable 关系字段够）
- V3 完成前不做 multi-agent（先把数据基底建对）
- V4 完成前不投入中文源（中文反爬工程量是英文 5-10 倍）

---

## 9. 评分体系详解（Researcher Mapping）

### 9.1 维度 1：学术影响力分（1-5 星）

| Feature | 数据源 | 权重 |
|---|---|---|
| **h-frac**（fractional h-index，抗 hyperauthorship） | OpenAlex | 0.35 |
| 顶会一作 / 通讯论文数（最近 3 年） | papers 表 | 0.25 |
| Highly Influential Citations | Semantic Scholar API | 0.20 |
| Citation velocity（最近 2 年 avg/yr） | Semantic Scholar | 0.10 |
| Q-proxy（前 N 篇 paper 引用方差） | OpenAlex | 0.10 |

**关键：** 不用原始 h-index（百人作者 paper 让 h-index 在 2010-2019 与学术奖相关性从 0.34 降至 0.00）。生涯 < 5 年用 advisor lineage 加权。

### 9.2 维度 2：方向匹配分（1-5 星）

| Feature | 数据源 | 权重 |
|---|---|---|
| 最近 12 个月 paper 与 HH thesis vector cosine similarity | embedding（ChromaDB） | 0.50 |
| 主方向枚举命中（7 主方向） | papers 表 | 0.30 |
| 子标签枚举命中（8 子标签） | papers 表 | 0.20 |

**关键：** HH thesis vector = HH 团队**最近 30 天读过的 paper 集合的 mean embedding**（动态滚动，每周重算）。**不能用静态 thesis** — 您的研究焦点本身在变。

### 9.3 维度 3：接触可行性分（1-5 星）

| Feature | 数据源 | 权重 |
|---|---|---|
| 公开 email | researchers 表 | 0.20 |
| X DM 开放 / 知乎私信权限 | 各平台 API | 0.10 |
| mutual connection 数（HH 网络与候选合著重叠） | 合著者图 | 0.30 |
| 公开 talk / 会议出席 | YouTube / 会议 schedule | 0.10 |
| 过往邀请回应率（如有） | decisions 表 | 0.20 |
| 导师 / 实验室 HH 已建立联系 | researchers 表 | 0.10 |

直接驱动 L0 / L1 / L2 触达路径推荐。

### 9.4 维度 4：时间窗口分（1-5 星）★ HH 独创

| 信号 | 时间窗口分 |
|---|---|
| 博四 / 博五 / 应届毕业（找工作窗口） | ★★★★★ |
| 最近 30 天大新闻（融资 / 跳槽 / 毕业 / 论文 X 热搜） | ★★★★★ |
| 博后 1-2 年内（要 faculty 决定） | ★★★★ |
| 刚加入新公司 6 个月内（蜜月期不愿动） | ★★（降权） |
| 教授 / 工业界研究员稳定状态 | ★★★ |
| 近期连发 paper（最近 3 月 ≥ 2 篇） | +1 |
| 主页 / X 出现"open to discuss"等关键词 | +1 |
| 最近 6 个月沉默 | -1 |

### 9.5 综合分

```
综合分 = weighted_geomean(
    学术影响 ^ 0.20,
    方向匹配 ^ 0.30,
    接触可行 ^ 0.25,
    时间窗口 ^ 0.25
)
```

**用 geometric mean 不用 arithmetic mean** — 任一维度 1 星整体熄火，避免"假全才"被推荐到周报顶部。

### 9.6 实现成本

- 单 candidate 评分：4 次 LLM call ≈ $0.05
- 1000 人入库一次性：$50
- 每周更新 200 active：$10/周

### 9.7 必须避免的 pitfalls

1. 不用原始 h-index — 用 h-frac 抗百人作者 paper
2. 方向匹配的 thesis 不能写死 — 必须每周从 HH 团队近期阅读重算
3. 不要学 a16z 评 founder potential — HH 不投资，会污染信号
4. Citation velocity 给至少 6-12 个月窗口 — 否则 viral tweet 撬动结果
5. CSRankings tier 偏差 — 系统性低估非美名校（清华 IIIS / EPFL / Tel Aviv），需手工 override 白名单
6. 小红书 / 知乎 scrape 合规 — 走 robots.txt + 个人开放删除入口

---

## 10. 关键风险与对策

| 风险 | 概率 | 对策 |
|---|---|---|
| **landscape ontology 漂移** | 中（已通过手画 ontology 降低） | 主方向 + 子标签全人工维护，LLM 只挂 paper 不创建 tag |
| **Insight 区噪声化** | 高 | 必须经人审 + 至少一条交叉验证 |
| **Mapping 评分静态化** | 中 | thesis vector 每周从最近阅读重算；time_window 每周更新 |
| **知识库变"日报存档"** | 中 | V3 RAG query bot 是知识库存活的关键 |
| **决策反馈表不被填** | 中 | 飞书 Bitable button 字段，30 秒级别，5 人共担 |
| **lark-cli 版本升级** | 低 | 跟随官方升级（当前 1.0.17，最新 1.0.20） |

---

## 11. 资源索引

### 飞书

- **规划文档（wiki）**：https://my.feishu.cn/wiki/Nj6Gw8a6tiDzv9kSSLKcReFWnAd
- **架构画板**：token `Ed9Sw0OBUhgptYb1WSncrvnfnOf`
- **AI 研究图谱底表（Bitable）**：https://my.feishu.cn/wiki/D459wP75uiK8RMk0J9Mclvh4nNf
- **HH Research Pipeline Bitable**（pipeline 实际写入）：https://my.feishu.cn/base/UdwrbpCMoasCs3snCvbcKgbsnfc
  - whitelist 表：`tblpVgQBAkPptnip`（347 条）
  - signals 表：`tbllGsqhy4swhzkz`
  - daily_digest 表：`tblYQtnTu0mirBE0`
  - ops_metrics 表：`tblsnDe4BCmHWlNI`
- **HH Research 日报 wiki 节点**：https://my.feishu.cn/wiki/LG1ewqdBsi7ORskSIxhcow9Un2e
- **5.19 v3 baseline 日报（认可样板）**：https://my.feishu.cn/wiki/BO4YwOHRIiLG1vkoBRbcp9danTf
- **5.20 当前 v4 XML 日报**：https://my.feishu.cn/wiki/GxakwYWFvixjGAkxFlqcLnE5nZe
- **HH Research Daily 多端推送方案**（IT 沟通材料）：https://my.feishu.cn/docx/IILRd227AobJg0xffQGcGnDNnxe
- **HRes' aha moment 申请操作指引**（leader 飞书 bot 创建手册）：https://my.feishu.cn/docx/OSbLd9v5OoMo9rxHOY7cVR7dnDg
- **lark-cli profile**：`personal`（app `cli_a9605d9a8c79dbdf`），user 郭昊霖（`ou_69c034f8f67053dca0cfaf9c6e9f3262`）
- **参考日报样式（MiraclePlus）**：https://miracleplus.feishu.cn/wiki/U9MawdGWwi6ujckeggic6Csln1g

### 文件路径

| 资源 | 路径 |
|---|---|
| **GitHub repo** | https://github.com/jingruzhao103-bit/HH-Research |
| **GitHub tags** | v3.2 / v4.0 / v4.1 / v4.2 |
| 仓库根（本地，绑 GitHub） | `/Users/haolinguo/claude code/HH research/` |
| daily-digest 子项目根 | `/Users/haolinguo/claude code/HH research/daily-digest/` |
| Mapping schema 与种子数据（独立） | `/Users/haolinguo/claude code/HH researcher mapping/feishu/` |
| 实施计划（已对齐 6 周） | `/Users/haolinguo/.claude/plans/cc-hh-research-ai-ai-infra-clever-church.md` |
| Memory（Claude 自动记忆，含 5.21 路线图） | `/Users/haolinguo/.claude/projects/-Users-haolinguo-claude-code-HH-research/memory/` |
| **5.21 产品路线图** | `docs/roadmap/2026-05-21-product-roadmap.md` |
| **H Link 锚点期望 spec** | `docs/specs/2026-05-21-hlink-anchor-expectations.md` |
| 日报 v4 XML prompt | `config/prompts/daily_digest.md` |
| 信号抽取 prompt | `config/prompts/extract_signal.md` |
| Pipeline 主入口 | `src/hh_research/pipeline/daily.py` |
| Daily writer (v5 双桶路由) | `src/hh_research/extract/daily_writer.py` |
| 飞书发布器 | `src/hh_research/publish/lark_doc_publisher.py` |
| H Link 推送器 | `src/hh_research/publish/hlink_publisher.py` |
| 锚点注入脚本 | `scripts/publish_with_anchors.py` |
| Author lookup post-process | `scripts/author_lookup_post_process.py` |
| 企业群广播 | `scripts/broadcast_today.sh` + `scripts/send_digest_to_enterprise.py` |

### 灵感与对标

- **奇绩 alpha sight**（对标，要超越）
- **Karpathy 的 Obsidian vault**（个人案例 N=1，思想可借鉴但实现不适用 5-10 人团队）
- **MiroFish (github.com/666ghj/MiroFish)**：4-tool 检索分层抽象、ontology 自动生成、报告目录化输出 — 这三个直接借鉴；其 OASIS 模拟引擎、Zep Cloud 不抄
- **AMiner AI 2000 / CSRankings / Semantic Scholar**：评分体系参考

### 调研记录摘要（D4 决策依据）

- **学术界**：H-index 失真（PNAS 2021）→ 改用 h-frac；Q-model（Sinatra 2016 Science）个体能力的隐变量；Wang-Song-Barabási（Science 2013）单 paper 终生引用可由 early citation 推断
- **VC 实践**：a16z 9 项 founder rubric；Sequoia Arc 数据驱动；Khosla 5 维 deep-tech rubric；高瓴 / 红杉中国 / 奇绩 公开 rubric 均未公开
- **工具**：Harmonic.ai relevance scoring、Affinity relationship strength（recency × frequency × multiplicity）、Pioneer.app 4-week 滑动窗

---

## 12. Onboarding 速查

### 我是新来的，5 分钟入门

1. 读本文 §0 + §2.1 架构画板 → 知道项目是什么
2. 读 §7 → 知道当前进度
3. 读 §8 → 知道下一步做什么

### 我要写代码，需要什么背景

1. 读 §3 系统架构 + §4 数据模型 → 理解 schema
2. 读 §6 技术栈 → 知道用什么工具
3. 看 worktree 的 `src/hh_research/pipeline/daily.py` 主入口
4. 看 mapping 文件夹的 `*_fields.json` 了解 Bitable schema

### 我是 Claude，第一次接到这个项目的任务

1. 必读：`/Users/haolinguo/.claude/projects/-Users-haolinguo-claude-code-HH-research/memory/MEMORY.md`
2. 检查：`lark-cli --profile personal auth status` — user 身份是否登录
3. 走查：本文 §11 资源索引里的所有路径都可达
4. 优先尊重：本文 §6.2 的 D1-D5 决策已敲定，无新信息不要推翻

### 当前最大的阻塞

- **TODO-01 (P0 5.22) 3 推送通道跑通** — 飞书 1-on-1 等 leader 创建企业自建应用；H Link 等 IT 开通开发者权限 + 管理后台 URL（参见 memory `push_channels_hres_aha_moment.md`）
- **TODO-05 (中期 P0) Alert 实时推送系统** — 启动等 TODO-07 实体白名单先做
- **20+ 同事名单 + open_id** — 用户提供中
- 详见 [docs/roadmap/2026-05-21-product-roadmap.md](docs/roadmap/2026-05-21-product-roadmap.md)

---

**文档版本：** v0.2（2026-05-21） — 同步过去 3 周进展（4 源 + Bedrock + v4 XML + 锚点 + launchd + HRes' aha moment 推送 + 5.21 路线图）
**作者：** 郭昊霖 + Claude（共同迭代）
**许可：** 内部文档，不对外发布
