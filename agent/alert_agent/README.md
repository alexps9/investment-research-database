# alert_agent — 实时 AI 行业信号判别 Agent

实时监控 Twitter / 官方 RSS / 中文媒体的 AI 行业信号，经判别后写一句话中文摘要、
交叉验证原始来源，并推送到飞书群 + 落库到知识库。

本目录是把原独立 `alert/` 管线重构进 HH-Research 多智能体系统的结果：
原先用 Bedrock-Claude 手写的「判别 / 摘要 / 终审」三步，统一改为一个 AutoGen
`AssistantAgent`（`alert_agent`），由项目共享的模型客户端（默认 DeepSeek）驱动；
可复用的能力上提到了项目的 `tools/` 与 `skills/`。

## 架构

```
fetch (Twitter/RSS/媒体)        agent/alert_agent/fetcher.py     ┐
score + 三角验证 + 聚类去重      skills/signal_triage             │ 确定性（便宜可复现）
prefilter 噪音硬过滤(可选)       agent/alert_agent/prefilter.py   ┘
判别 → 摘要 → 验证 → 推送/落库   agent/alert_agent (AutoGen)       ← LLM 驱动
```

## 重构去向（哪些代码变成了 tools / skills）

| 原 alert 模块 | 现位置 | 说明 |
|---|---|---|
| `classifier.py`（judge+summary） | `agent/alert_agent/__init__.py` 的系统提示 | 由 AutoGen agent + DeepSeek 取代 Bedrock 调用 |
| `reviewer.py`（发送前终审） | 同上（折叠进系统提示「四、发送前自审」） | |
| `sender.py`（飞书推送） | `tools/notify.send_feishu` | 异步原子工具 |
| `verifier.py`（DDG 搜索原始来源） | `tools/websearch.search_web` / `find_primary_source` | 去掉 Bedrock「选源」，改由 agent 判断 |
| `score.py`（分级/打分/三角验证/去重） | `skills/signal_triage` | jieba 可选，去掉 LLM 升级判重 |
| `kb_sync.py`（写信号到知识库） | `tools/signals.create_signal` | 复用既有 CRUD 工具 |
| `fetcher.py` / `store.py` / `prefilter.py` / `config/` | 保留在本目录 | alert 专属的数据基础设施 |
| HeadlineClassifier（v8.0 强约束判别） | `agent/alert_agent/headline/`（vendored） | 从 jingruzhao103-bit/HH-Research `daily-digest` 抽取，自包含、离线可用 |

## 快速开始

```bash
# 在仓库根目录
pip install -r agent/requirements.txt          # autogen + httpx + dotenv
pip install -r agent/alert_agent/requirements.txt  # requests + pyyaml + jieba

cp agent/alert_agent/.env.example agent/alert_agent/.env   # 填 key

python -m agent.alert_agent.pipeline --limit 5  # 跑一遍（先小批量验证）
python -m agent.alert_agent.pipeline --no-twitter  # 只跑 RSS + 媒体（无 Twitter key 时）
```

未配置 `TWITTERAPI_IO_KEY` 时自动跳过 Twitter；未配置 `FEISHU_WEBHOOK_URL` 时
飞书推送进入 dry-run（只打印不发送）。

## 人工审核

媒体信号可走人工确认队列（`pending/`），用命令行逐条审核后再推送：

```bash
python agent/alert_agent/approve.py
```

## 设计取舍

- **确定性优先**：分级/打分/三角验证/聚类去重等高度调过参的逻辑保持确定性
  （`skills/signal_triage`），既便宜又可复现，只把「理解内容 + 判定重要性 + 写摘要」
  交给 LLM agent。
- **判重**：tweet 级判重由本地 SQLite（`store.py`）负责；事件级 / 知识库级判重交给
  agent（`semantic_search`）与 `create_signal` 的 URL 唯一约束，不再依赖 Bedrock。
- **prefilter** 使用本地 vendored 的 HH-Research v8.0 `HeadlineClassifier`
  （`headline/`），无需任何外部仓库即可运行：基于 `config/p0_whitelist.yml`
  的 P0+/P0 名单做确定性 5 维打分 + 8 条强约束判别，`pass` 直接进摘要、
  `borderline` 交 agent、`skip` 丢弃。`headline/` 由
  jingruzhao103-bit/HH-Research 的 `daily-digest/src/hh_research` 抽取而来
  （`Signal` 从 pydantic 模型精简为零依赖 dataclass，逻辑保持一致）。

> ⚠️ Windows 注意：所有读取中文 YAML/JSON 配置的 `open()` 必须带
> `encoding="utf-8"`，否则在中文 Windows 上会用 cp936 解码失败（whitelist 被
> 静默读空，prefilter 全部退化）。本目录的 fetcher/prefilter 已修正。
