# HH Research 产品路线图（5.21 产品会议产出）

> 日期：2026-05-21
> 上下文：基于 5.21 产品会议讨论 + 现有 v4 XML pipeline + HRes' aha moment 推送链路状态
> 关联：[2026-05-21-hlink-anchor-expectations.md](../specs/2026-05-21-hlink-anchor-expectations.md)

## TL;DR

- **明天 (5.22) P0**：3 推送通道跑通（飞书企业群 / 飞书 1-on-1 / H Link 1-on-1），5 人白名单
- **本周末 (5.23-24)**：扩到 20+ 全员
- **下周 ~ 一个月**：Alert 实时推送系统（中期 P0）+ 内容质量迭代
- **一个月以上**：个性化推送、视频、知识问答

## 🔴 短期（本周 ~ 周末）

### TODO-01 · 3 推送端口跑通 (P0)

**时间：** 2026-05-22（明天）
**目标：** 飞书群报 / 飞书订阅 bot / H Link 三通道，5 人白名单全部跑通
**当前状态：**

| 通道 | 状态 | 当日动作 |
|---|---|---|
| A 飞书企业群 | ✅ 已上线 09:30 | 把 5 同事拉进群（如尚未在） |
| B 飞书 1-on-1 | ⏳ 等 leader 完成企业自建应用创建 | 拿到 app_id/secret 后写 `feishu_bot_publisher.py` + 联调 |
| C H Link 1-on-1 | 🛠️ 代码就绪 | 等 IT 开通开发者权限 + Max 配 VM + 凭证到位 + 单点联调 |

**子任务：**
- [ ] Leon LIU + Max 给 5 同事配虚拟机 + H Link bot 权限
- [ ] 用户拿到 5 同事 open_id 并发飞书群
- [ ] B 链路：等 leader 创建应用 → 写 `feishu_bot_publisher.py`
- [ ] C 链路：凭证到位 → 填 `.env` 6 项 → 单点联调

### TODO-02 · H Link 锚点期望提交

**时间：** 本周内
**目标：** [2026-05-21-hlink-anchor-expectations.md](../specs/2026-05-21-hlink-anchor-expectations.md) 转飞书 docx → 提交 Max / Leon 团队 → 收平台演进时间表

### TODO-03 · 20+ 同事名单 + open_id 收集

**时间：** 本周
**目标：** 用户提供 20+ 投前同事姓名 + 飞书 open_id + H Link open_id（两套独立 ID）→ 写入 memory + pipeline notify_user 列表

### TODO-04 · 扩到 20+ 全员

**时间：** 2026-05-23 至 2026-05-24（周六周日）
**前置：** TODO-01 + TODO-03 完成
**目标：** 5 人白名单扩到完整 20+ 投前同事

## 🟡 中期（下周 ~ 一个月内）

### TODO-05 · Alert 实时推送系统（中期 P0）

**目标：** 实时 X 监控 + LLM 重要性判定 + 1V1 推送（如 Karpathy 跳槽这种重大事件）
**核心组件：**
- 输入：P0 信号源（依赖 TODO-07 实体白名单）
- 监控：X 高频轮询（现状 socialdata.tools 6s/user，需评估是否撑得住 50 账号 5min 轮询，或换 streaming 接口）
- 判定：LLM 重要性 trigger（过滤 "gm" "lol" 噪音，识别跳槽 / 收购 / 发布等关键事件）
- 触达：1V1 推送（飞书 + H Link 双通道）
- 用户级订阅：每人选关注哪些 P0 源

**依赖：** TODO-07 实体白名单

### TODO-06 · 推送时间窗口切换

**目标：** 数据窗口 + 发布时间统一切换

| 项 | 当前 | 新 |
|---|---|---|
| 数据窗口 | BJT 0:00 → 0:00 | BJT 8:00 → 8:00 |
| Pipeline 启动 | launchd 00:00 | launchd 08:30 |
| 健检 | 00:30 | 11:30 |
| 企业群广播 | 09:30 | 12:00 |

**设计意图：** BJT 8:00 = PDT 17:00（美西工作日刚结束）+ arxiv UTC 0:00 announcement = BJT 8:00 — 窗口完整覆盖美西活跃时段 + 国内白天。
**实现：** daily.py 加 `--cutoff-hour 8` 参数 + 改 3 个 launchd plist 文件

### TODO-07 · 头条规则定义 + 重要实体白名单 boost

**目标：** 把"什么算头条 / 影响力最深"的规则集明确化
**子任务：**
- 与用户沟通定义具体规则（哪些场景 → 必上头条）
- 写成 spec
- 落到 `extract_signal.md` prompt（影响 LLM 打分）
- 落到 `daily_writer.py` score 函数（影响最终选头条）
- 在 whitelist 表加 `is_priority_source` 字段（或新建 entity 白名单表）
- 命中白名单 signal 自动 `headline_priority=5` 或直接进头条池
- 保留人工 override 通道

### TODO-08 · 日报内 hover 释义（Wiki 强绑定）

**目标：** 日报关键术语首次出现 → 自动接 wiki 术语页锚链接 → 飞书 docx native 卡片预览 → hover 出释义
**参考产品：** "大模型101"
**前置：** 建术语 wiki 库（MoE / RLHF / GRPO / Test-time Scaling 等条目）
**已有基础：** 缩写格式规则已固化（v6.3 `中文释义（英文缩写）` 格式）

### TODO-09 · 阅读监控埋点

**目标：** 监测用户点击率 + 停留时间（4 个监测点：群报 / 订阅 bot / Hlink / 日报本身）
**实现：**
- 自建短链跳转服务（log: click_ts + user_id + 来源渠道 + section/item_id）
- 日报内所有外链 + 锚链接走短链
- 接 H Link 已读 / 未读 API（依赖 TODO-02 H Link 期望落地）
- 验证飞书 OpenAPI 是否有 docx view analytics（用 lark-openapi-explorer skill 查）
- 飞书 docx 停留时间：评估 ROI 后再决定是否做自建 web 镜像

### TODO-10 · Insights 改写

**三个轴：**

| 轴 | 目标 |
|---|---|
| 长度 | 篇幅短 + 易懂"既要又要"（目标 150-200 字 vs 现状 200-280） |
| 文风 | 高质量论文讲解 + 优质科技公众号风格蒸馏，少 LLM 套话 |
| 读者画像 | 比普通白领对 AI 认知高 1-2 步 ≈ 本科 CS/AI 学生级 |

**执行方式：**
- A/B 双版本生成对比挑选（A = 现状 v6.3，B = 新规格）
- 拆分：论文类 vs X 推文类用不同 prompt → 合流 pending_insight_extraction_skill.md
- 参考公众号对标名单（待用户补）
- 节奏：等用户汇总完会上其他 our insights 讨论后启动

### TODO-11 · 问卷反馈机制（待定）

**目标：** 借助"飞书群报"高触达渠道，定期推问卷收集反馈
**状态：** 是否真做视埋点数据 + 用户口头反馈量再定
**理由：** 用户量只有 20+，1V1 反馈成本可能低于问卷

## 🟢 远期（一个月以上）

### TODO-12 · 个性化推送（较近的远期）

**目标：** Alert 与日报双维个性化

**待定颗粒度：**
- 只能选 5 个赛道大类
- 或可选具体实体（关注 OpenAI 不关注 Meta）
- 或赛道 + 实体都能选

**实现方案候选：**

| 方案 | 实现 | 复杂度 |
|---|---|---|
| A | 全员收同一份日报，前面加个性化 TL;DR 段 | 低 |
| B | 按赛道订阅分版本生成 | 中 |
| C | 每用户独立 LLM 跑一份完全定制 | 高 |

### TODO-13 · 视频嵌入

**目标：** 日报嵌入官方 demo 视频链接（YouTube 官方频道 / X 嵌入视频 / Anthropic、OpenAI YouTube 等）
**前置：** 现 image_extractor 只抓 arxiv 首图 / PDF 首页，无视频处理逻辑

### TODO-14 · 飞书知识问答接入

**目标：** 建独立术语知识库 → 接 ask.feishu.cn 知识问答 bot → 用户对术语 ad-hoc 提问

## 📌 待补充

1. 20+ 同事名单 + open_id（用户提供）
2. 会上其他 our insights 改进讨论的汇总（用户整理）
3. H Link 平台文档（建好后进 memory）
4. 高质量公众号对标名单（TODO-10 用）
5. TODO-07 头条规则 deep-dive 沟通（用户随后专题讨论）
6. TODO-10 Insights deep-dive 沟通（用户随后专题讨论）

## 关键依赖图

```
TODO-01 (3 通道跑通)
  ├─ A 飞书企业群 (已上线)
  ├─ B 飞书 bot (← leader 创建应用)
  └─ C H Link (← IT 开权限 + Max 配 VM)

TODO-05 Alert ← TODO-07 实体白名单

TODO-09 埋点 ← TODO-02 H Link 已读 API 期望落地

TODO-12 个性化 ← TODO-10 Insights 改写 + 用户反馈数据
```
