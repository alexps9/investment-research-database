# Alert — AI 行业实时信号监控

实时监控 Twitter、RSS、中文媒体的 AI 行业信号，经 LLM 判别后推送至飞书群。

## 架构

```
信号源 (Twitter / RSS / 中文媒体)
  ↓
fetcher.py        抓取 + 正文补全
  ↓
prefilter.py      硬规则过滤（噪音秒杀，不调 LLM）
  ↓
score.py          tier 分级 + 热度评分 + 多源三角验证 + 聚类去重
  ↓
classifier.py     LLM 两步判别（Judge → Summary）
  ↓
reviewer.py       发送前 skeptic 审核（防旧闻/夸大）
  ↓
verifier.py       交叉验证 — 搜索原始出处链接
  ↓
sender.py         格式化 → 飞书推送
```

## 目录结构

```
alert/
├── main.py              主管线入口
├── fetcher.py           Twitter + RSS + 媒体抓取
├── prefilter.py         确定性硬过滤
├── score.py             打分 + 多源聚类
├── classifier.py        LLM 判别（Bedrock Claude）
├── reviewer.py          发送前审核
├── verifier.py          交叉验证原始来源
├── sender.py            飞书推送
├── store.py             SQLite 去重 + 审计
├── approve.py           命令行：人工审核 pending
├── config/
│   ├── config.json      运行参数（轮询间隔、时间窗口）
│   ├── p0_whitelist.yml Twitter 监控名单（P0+/P0）
│   ├── rss_feeds.yaml   官方 RSS 源（公司博客）
│   └── media_feeds.yaml 第三方媒体 RSS 源
├── .env.example         环境变量模板
└── requirements.txt     Python 依赖
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入：TWITTERAPI_IO_KEY, BEDROCK_API_KEY, FEISHU_* 系列

# 3. 单次运行
python main.py

# 4. 定时运行（macOS launchd 每小时，参考 deploy/ 目录说明）
```

## 判别逻辑

两层判别，确定性打分在前、LLM 在后：

1. **prefilter**（prefilter.py）：确定性规则，0ms
   - 硬过滤噪音（转发/短文/生活内容）
   - 依赖 HH-Research 的 HeadlineClassifier；如不可用自动退化为全量交 LLM

2. **打分层**（score.py）：纯规则，毫秒级
   - `tier`：信号源权威度（tier_1a 官方 → tier_3 搬运号）
   - `engagement`：热度加权分
   - `verified`：多源三角验证

3. **LLM 层**（classifier.py）：理解内容，判定重要性
   - important → 直接推送飞书
   - medium（media 来源）→ pending 待确认
   - skip → 不推

核心判断标准：**投研的人看完会做出不同的决策或动作吗？**

## 信号源配置

| 文件 | 内容 | 示例 |
|------|------|------|
| `config/p0_whitelist.yml` | Twitter 监控名单 | OpenAI, Anthropic, Karpathy... |
| `config/rss_feeds.yaml` | 官方博客 RSS | openai.com/blog, anthropic.com... |
| `config/media_feeds.yaml` | 第三方媒体 | IT之家, 36氪, TechCrunch AI... |

## 环境变量

| 变量 | 用途 |
|------|------|
| `TWITTERAPI_IO_KEY` | Twitter 抓取 API |
| `BEDROCK_API_KEY` | Claude LLM（classifier + verifier） |
| `BEDROCK_REGION` | AWS region（默认 us-east-1） |
| `FEISHU_APP_ID` | 飞书机器人 |
| `FEISHU_APP_SECRET` | 飞书机器人密钥 |
| `FEISHU_RECEIVE_ID` | 推送目标群 chat_id |

## 可选依赖

- **HH-Research**（`../HH-Research/daily-digest/src/`）：提供 prefilter 的 HeadlineClassifier。
  不装也能跑——prefilter 退化为全量过 LLM，准确率不变，只是 LLM 调用量略增。
