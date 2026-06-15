# 2026-06-02 日报 Pipeline 事故定位分析（供 Codex 审阅）

> **目的**：2026-06-02 当天日报生成全程异常——多次残缺、反复重跑（约 6 次）、最终靠「手动补采 arxiv + regenerate + 手动编辑头条」才产出完整版，且**正式 `last_digest` 至今仍指向凌晨的残缺版**。本文系统定位全部问题、根因与证据，供 Codex 审阅后排定修复方案。本文只做定位，不含实现。

---

## 1. 结果概述（TL;DR）

- **最终推送给用户的是 v4（手动编辑版）**：数据 = 凌晨支线采的 121 条 X/RSS + 白天补采的 11 篇 arxiv 白名单论文，头条为**人工手写**（NVIDIA 综述 / Anthropic / Composer / PithTrain）。
- **正式 `data/state/last_digest.json` 仍 = 凌晨残缺版 `G9XTwEU`（00:43，frontier=0，无前沿研究）**。所有 v1–v4 都是独立 wiki doc + 1-1 bot 推送，**未更新 last_digest** → 若 12:00 broadcast 触发会发残缺版。
- 当天 `frontier`（前沿研究）多次为 0，根因有二：① arxiv 采集在 export API 限流下直接归零；② 一次正式跑被**去重库污染**吃掉了 11 篇 arxiv。

---

## 2. 事件时间线（均有 `data/logs/` 证据）

| 时间 (CST) | 触发 | whitelist | arxiv | 结果 | 证据 |
|---|---|---|---|---|---|
| 00:00 | 支线 daily-pipeline | **420** | fetched **0** | 129 信号 → digest `G9XTwEU`，`frontier=0` | pipeline.daily.log 00:00:08 / 00:39:44 |
| 09:16 | 主线 daily-pipeline-main | **0**（读取失败）| 0 | raw 8 → 残缺日报 + 通知用户 | `whitelist read failed … no such host` (daily_main log) |
| 09:47 | 手动 arxiv 验证 | 420 | **11** | 证明 arxiv.org HTML 路径可用 | pipeline.daily.log 09:47:27 |
| 10:04 | 手动跑 | **0**（5000）| 0 | raw 0 | `whitelist read failed … code 5000` |
| 10:16 | 完整 pipeline | **0**（5000）| 0 | 残缺 4 RSS → 发布 `NDfKwQVP` | pipeline.daily.log 10:16:12 |
| 10:49→12:16 | 完整 pipeline（已加 read 重试）| 420 | 11 采到但**被去重吃掉** | `frontier=0 industry=50` → 残缺 | daily_writer bucket 12:16 |
| 12:27 | 手动补采 arxiv（新去重库+跳图片）| 420 | 11 写入 Bitable | 修复数据 | inserted 11 |
| 12:49 | regenerate（读 Bitable 132）| — | — | **frontier=20** → 完整版 `MpLCwgln` | boqga5esg |
| 13:24→13:51 | 手动编辑头条 → 发布 | — | — | v2 `IFAWwIJX` / v3 `Lsw0w0rl` / v4 `KUW6wkTe` | publish_edited_digest |

> 飞书读取失败 ≥3 次（09:16 DNS、10:04 / 10:16 code 5000）；每次都直接把 whitelist 归零。

---

## 3. 问题清单（按严重度 · 含根因/证据/涉及代码/建议方向）

### 🔴 P0（直接导致日报残缺 / 错误 / 脱节）

**P0-1 `read_whitelist` 无重试，飞书一次瞬时故障即「whitelist=0」全盘残缺**
- 根因：`bitable_client._lark_cli` 原实现 rc≠0 即抛错；`read_whitelist` 上层一次失败即返回 0 条。飞书 API 当天间歇 `5000` / DNS `no such host`，每次都触发归零。
- 证据：09:16 / 10:04 / 10:16 三次 `whitelist: 0 total`。
- 涉及：`src/hh_research/storage/bitable_client.py` `_lark_cli` / `read_whitelist`。
- 现状：**已临时加退避重试**（只读命令 8 次）。建议 Codex 复核重试参数、是否对 `read_whitelist` 加「读到 0 条视为失败而非空集」的保护。

**P0-2 白名单读取失败后 pipeline 仍继续运行并推送残缺版（无熔断）**
- 根因：`read_whitelist` 失败返回 0 → pipeline 不中断，继续采集（X/openalex 因无名单也 0，仅 RSS 有数据）→ 生成残缺 digest → publish + notify 用户。
- 证据：09:16 失败 → raw 8 → 09:30 `frontier=0 industry=8` 残缺日报照发 + IM 通知。
- 涉及：`src/hh_research/pipeline/daily.py`（step 1 后无 whitelist 数量校验/熔断）。
- 建议：whitelist=0（或远低于历史值，如 < 300）时 **abort + 退避重试**，绝不继续生成/发布。

**P0-3 去重库污染：测试跑用了默认 `dedup.sqlite`，把 11 篇 arxiv 标记「已见」，正式跑被去重吃掉 → frontier=0**
- 根因：手动验证 arxiv 流程时未指定独立 `--dedup-db`，污染生产默认库；正式 pipeline 用同库 → 11 篇 arxiv 全部 `skipped already-seen` → 前沿研究空。这是**操作失误叠加缺乏隔离机制**。
- 证据：补采前正式跑 `frontier=0`；改用全新 `--dedup-db` 重采后 11 篇入库、regenerate `frontier=20`。`data/` 下遗留 `dedup.sqlite`(被污染) + 3 个 `dedup_arxiv_fix*.sqlite`。
- 涉及：`daily.py` 默认 dedup-db 行为 + 缺少「dry-run/测试不写 dedup」开关。
- 建议：① dry-run/验证模式默认**不写** dedup；② 或测试强制独立库；③ 文档约定。
- **待补硬证据**（Codex 要求）：将 09:47 那 11 个 arxiv `source_id` 与 `dedup.sqlite` 的 seen 表逐条对照，确认「11 篇全部被标记 already-seen」。现有日志只证明「10:49 采到 11 篇、dedup 后 121 new / 131 skipped、最终 frontier=0」，尚缺这一步逐条对照。

**P0-4 `publish` 不更新 state，正式版与推送版长期脱节（两个 state 文件均残缺）**
- 根因：`scripts/publish_edited_digest.py:23` 只 publish + inject anchors + notify，**不回写 state**。
- 证据（经 Codex 修正补全）：存在**两个** state 文件，均未指向最终 v4：
  - `data/state/last_digest.json` = `G9XTwEU`（00:43 支线残缺）
  - `data/state/last_digest_main.json` = `GAtwwVku…`（09:32 主线残缺）
- 风险（精确化）：**主线 12:00 broadcast 读的是 `last_digest_main.json`**（不是 last_digest.json），而它仍是 09:32 残缺主线版 → 会广播残缺版；支线路径读 last_digest.json，同样残缺。
- 建议：明确「正式版」写回 state 的唯一入口（主线写 `last_digest_main`、支线写 `last_digest`），预览版与正式版状态分离且可控。

**P0-5 前沿研究采集脆弱：网络异常致 arxiv 全 0 时不熔断、静默发布残缺版**
- 根因（经 Codex 修正）：`arxiv_collector` **已经是「近 8 天窗口优先 arxiv.org HTML，失败才 fallback export API」**（`arxiv_collector.py:109` `use_html_announcement_list = until >= now-8d`；`:126` html primary → export fallback）——**降级顺序本身没问题**。09:16 的真正根因是 **DNS/网络把 HTML 与 export 同时打挂**（`nodename nor servname provided`），两条路都失败 → arxiv 归 0；而 pipeline 对 arxiv=0 既不告警也不熔断，照常发布。
- 证据：09:16 `arxiv html primary failed … falling back to export API` 后两条都失败 → arxiv 0；网络恢复后 09:47 / 10:10 走 HTML 正常采到 11 篇。
- 涉及：`arxiv_collector.py`（网络错误重试）+ `daily.py`（arxiv 全 0 熔断）。
- 建议（修正后）：① 主线启动前**网络就绪检查**；② **arxiv 质量熔断**——窗口内 HTML candidate 非 0 但 matched/new arxiv 为 0、或网络错误致全 0 时，告警 + 重试 + **不静默发布**。

### 🟡 P1（质量流程被绕过 / 机制缺失）

**P1-1 v7 质量门控被跳过，手动编辑版完全未过 gate**
- 根因：regenerate 时加 `--allow-review-fail` 跳过 `v7.0 P0 quality gate`；后续 v2–v4 经 `publish_edited_digest.py` 直接发布，**不经过** `digest_review_agent` 审查。
- 证据：`scripts/regenerate_digest.py:437` gate 逻辑 + `--allow-review-fail`；publish_edited_digest 无 review 调用。
- 影响：最终成品未经事实性/去重/格式自动校验。
- 建议：手动编辑后**强制补跑 v7 gate**（可加非阻断的"warn-only"模式）。

**P1-2 v8 头条机制不支持「指定头条」，导致定制需求只能手动编辑绕过强约束**
- 根因：`headline_selector.py`(v8.0) 自动按 tier/novelty/constraint_pass 选头条，无 pin 接口。用户要精确指定 4 条 + 整合综述 → 只能手写 XML → 绕过 v8 `headline_classifier` 强约束（如"白名单作者完整列出"——参见 memory `feedback_tldr_whitelist_authors_complete`）。
- 涉及：`src/hh_research/pipeline/headline_selector.py` / `headline_classifier.py`。
- 建议：v8 增加「pin 指定 source_id/实体为头条」能力，使定制头条仍走强约束 + v7 gate。

**P1-3 图片提取串行且慢（11 篇 27 分钟），无跳过开关**
- 根因：`enrich_signal_with_images`（ar5iv miss → PyMuPDF PDF fallback）逐篇串行下载解析。
- 现状：**已临时加 `HH_SKIP_IMAGE_ENRICH` 开关**（`daily.py`）。建议根治：并行化 + 仅对头条论文抓图。

### 🟢 P2（性能 / 体验）

**P2-1 X 采集串行慢**：309 账号 per-user 串行 + 个别 60s 超时，约 30 分钟。建议并发/按活跃度调度（memory 已记为待办）。

**P2-2 1-1 bot 推送收件人不一致**：系统 `userEmail` 为 `hlguo2@`，但订阅者表登记为 `hlguo@`，首两次推送 400 失败；且 hres-bot 用 app 私有 open_id 命名空间，personal open_id 不通。建议：推送统一以订阅者表 email 为准 + 文档记录命名空间陷阱。

### 🔵 补充问题（Codex 复核新增）

**P1-4 `regenerate_digest.py` 自身有慢路径——是刚才命令"卡很久"的真正原因**
- `regenerate_digest.py:375-410` 对每篇 arxiv 逐篇跑 coauthor enrichment（`enrich_paper_coauthors_v4`，双源 + 审查 agent）；`:445` publish 时还会**再次**做图片提取/插图。
- 影响：即使复用 Bitable 信号，regenerate 仍可能很慢。
- 建议：加 `--skip-author-enrich` / `--skip-image-enrich` / `--no-publish-images` + 阶段日志。

**P1-5 `_lark_cli` 重试无总超时预算，故障时变成"长时间等待"**
- `bitable_client.py:25` timeout 默认 60s，`:50` 只读命令重试 8 次 + 退避（3/6/12/24/30…），最坏单次调用可拖数分钟。
- 影响：提高了成功率，但飞书持续故障时会变成长等待，且无统一总超时/进度日志。
- 建议：加总超时预算 + 每次重试打印明确日志。

**P2-3 诊断命令 `grep | head` 过滤了进度输出**：排障时大量进度被过滤，"正在做什么"不可见——非根因，但影响可观测性。

---

## 4. 已临时修复 vs 待根治

| 项 | 状态 |
|---|---|
| `read_whitelist` 退避重试（P0-1） | ✅ 已临时加（bitable_client._lark_cli），待 Codex 复核 |
| `HH_SKIP_IMAGE_ENRICH` 跳过图片（P1-3） | ✅ 已临时加（daily.py） |
| arxiv 改走 arxiv.org HTML（P0-5） | ⚠️ 手动绕过，未固化为默认 |
| 去重库污染（P0-3） | ⚠️ 已用新库补采，但默认 `dedup.sqlite` 仍被污染、无隔离机制 |
| 白名单失败熔断（P0-2） | ❌ 未修 |
| last_digest 更新脱节（P0-4） | ❌ 未修（last_digest 仍是残缺版） |
| v7 补跑 / v8 pin 头条（P1-1/P1-2） | ❌ 未修 |

---

## 5. 环境因素（非代码，但需缓解策略）

- **飞书 API 间歇 5000**：本机 Clash 代理对 `open.feishu.cn`（国内服务）路由不稳；建议规则层让飞书直连（DIRECT），代理仅用于 arxiv 等海外源。
- **arxiv 限流 / DNS**：机器 08:30 唤醒后网络/DNS 未就绪即触发主线 → 启动前应加网络就绪探测 + 退避。

---

## 6. 给 Codex 的审阅重点 / 待确认

1. **修复优先级**：P0-1/P0-2（whitelist 健壮性+熔断）与 P0-4（last_digest）是否应最先做？
2. **read_whitelist 重试**是否充分？是否需要「读到 0 条即判失败」+ 历史基线对比熔断。
3. **去重隔离**：dry-run 默认不写 dedup，还是测试强制独立库？是否清理被污染的 `dedup.sqlite`。
4. **arxiv 降级顺序**：是否把 arxiv.org HTML 设为默认 primary、export API 仅兜底。
5. **正式 vs 预览** 的状态机：last_digest 写回入口如何收敛，避免脱节。
6. **v7/v8 与手动定制的兼容**：v8 加 pin 头条 + 手动编辑后强制补跑 v7 gate，哪个先做。
7. 是否需要立即把今天的 v4 设为正式版（更新 state）+ 修主线熔断，以免明天复发。

---

## 7. 修复优先级（采纳 Codex 复核建议）

1. **立即写回正确 state**：把今天最终 v4 写回 `last_digest_main.json`（主线 12:00 broadcast 读此）；若支线仍启用，同步 `last_digest.json`。
2. **whitelist 熔断**：`whitelist == 0` 或 `< 300`（历史基线）即 abort，禁止 publish/notify。
3. **arxiv 质量熔断**：窗口内 HTML candidate 非 0 但 matched/new arxiv 为 0、或网络错误致全 0 时，告警 + 重试 + 不发布。
4. **dedup 隔离**：验证/手动补采默认不写生产 dedup；生产 / 支线 / 测试库强制分离。
5. **regenerate 加开关 + 阶段日志**：`--skip-author-enrich` / `--skip-image-enrich` / `--no-publish-images`。
6. （次级）主线网络就绪检查、`_lark_cli` 总超时预算、`publish_edited_digest` 补 v7 gate、v8 `headline_selector` 支持 pin 指定头条。

> 说明：本文已据 Codex 复核修正 P0-4（state 文件对象）、P0-5（arxiv 根因为 DNS 双挂而非降级顺序），并补入 P1-4/P1-5/P2-3 与本节修复优先级。

---

## 8. dedup 污染硬证据（2026-06-02 执行期实测，Codex 要求逐条对照）

在 `claude/digest-stability` 实施 Task4 时对 `data/dedup.sqlite` 取证：

- **被误 mark 的 11 条 arxiv**（`first_seen_at = 2026-06-02 02:13:23`，同一次 `mark_many`）：
  `arxiv:2605.31463 / 31120 / 30523 / 30409 / 31518 / 30947 / 31598 / 31508 / 31466 / 31429 / 31271`
- **旁证**：调试时建的临时库 `data/dedup_arxiv_fix3_2026-06-02.sqlite` 恰好 `arxiv=11 total=11`，即同一批。
- **时间归因**：02:13 非支线调度（00:00/00:30/09:30），系手动 test 跑 + 旧 bug（`--skip-bitable-write` 仍无条件 `mark_many`）误标 → 后续跑这 11 篇被去重吃掉 → frontier=0。
- **清理**：备份 `data/dedup.sqlite.bak-task4-2026-06-02` 后删除这 11 条；`seen` 总数 3515 → 3504。
- **代码修复**：`should_mark_dedup(skip_bitable_write, write_succeeded)` 门控 + step5 仅写库成功后 mark（commit Task4，TDD）。
