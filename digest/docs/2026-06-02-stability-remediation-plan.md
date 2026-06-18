# 日报 Pipeline 稳定性 + 速度补丁 实施计划（供 Codex 审 → 执行）

> 配套事故复盘：`docs/2026-06-02-digest-pipeline-incident.md`
> 本文是**可执行实施计划**，每个任务带「改动文件 + 验收标准 + 验证命令」。

---

## 0. 背景与目标（已与用户对齐 2026-06-02）

**澄清结论（已查证，推翻原假设）**：
- `v7.9` 在仓库/文档/memory **零记录**；
- **v8（headline_classifier/selector）从未接入日报生成主链路**——`daily.py`/`daily_writer.py` 不调用它，只有 `backtest_headlines.py` 与 `rebuild_snapshot_from_bitable.py` 引用；日报头条一直是 `daily_writer._classify_section` 的 **v5 逻辑**（frontier/industry 分桶 + weighted 3+2 配额）；
- 5.30–5.31 的生成链路 = **现在这套**：`daily_writer`(v5) + prompt `v6.8.5-trial` + v7 quality gate。

**目标（用户选定「主要修稳定性 + 速度」）**：在**现有生成链路上**打稳定性 + 速度补丁。
**非目标（明确不做）**：① 不回退 prompt/版本；② 不动 v8、不做 v8 pin headline（未接入，与本次无关）；③ 不改生成风格。

---

## 1. 执行环境固定（P0 · 执行前必做）

> ⚠️ **base 分支调整（2026-06-02 与用户对齐，相对 Codex 前几轮假设的变更）**：生产基线回到 **`main`**（= 5.31 现链路，347 whitelist 原版，v6.8.5 prompt）。`claude/signal-expansion` 比 main 多出的 **420 whitelist 扩充 + 30 RSS 未过团队审核**，不应作为稳定性补丁 base。经核实**两分支 `src/` 生产源码零差异**（扩充只动 config/scripts），故补丁能干净地 base 到 main、与信号扩充互不干扰；信号扩充作为独立线，团队审完再合 main。

- **本计划规范路径（唯一）**：主工作区 [`daily-digest/docs/2026-06-02-stability-remediation-plan.md`](</Users/haolinguo/claude code/HH research/daily-digest/docs/2026-06-02-stability-remediation-plan.md>)。
  ⚠️ **不存在** worktree 副本——`…/interesting-brahmagupta-d0a5ff/docs/...` 为 **MISSING**，**勿引用**。
- **工作目录**：`/Users/haolinguo/claude code/HH research/daily-digest`（主检出，含 `.venv`/`.env`/`data`）。**不在任何 worktree 执行**。
- **base 分支**：`main`。⚠️ **HEAD 不写死**——另一会话可能正在向 main commit 5.31 基线，执行前用 `git -C "/Users/haolinguo/claude code/HH research" rev-parse --short main` **重新确认实时 HEAD**（撰写本计划时 main=`419802f`，signal-expansion=`c6d31d9`，**均会变，以执行时实测为准**）。
- **工作分支**：从 main 新建 `claude/digest-stability`，所有 Task commit 到此分支，完成后 PR 合 main。
- **需从 signal-expansion 带过来的产物**（cherry-pick 或重新落文件，**不带** 420 whitelist/RSS 扩充）：① 本计划 + 事故复盘 docs（`adf1b14`/`af1bbd0`）；② `scripts/publish_edited_digest.py`（Task 1 用，已保护在 `c6d31d9`）。
- 每个任务开始前打印确认：`pwd` / `git branch --show-current` / `git rev-parse --short HEAD`。

**signal-expansion 上的临时止血（在 `c6d31d9`，仅作参考；base 切 main 后按 TDD 正式重做，不直接 cherry-pick）**：
- `bitable_client._lark_cli` 只读命令退避重试（→ Task 6 正式化 + 加总超时预算）
- `daily.py` `HH_SKIP_IMAGE_ENRICH` 默认跳过图片——⚠️**方向错误**（会让正式日报缺论文图）；→ Task 5 改为「发布默认做图片 + 限时/缓存/裁剪范围，仅 emergency 才跳过」

---

## 2. 任务清单

### Task 1（P0 · 最紧急）状态写回闭环（覆盖自动 + 手工两条链路）
**现状（Codex P1 厘清）**：**自动主线已有 state 写回 + fail-loud**——`scripts/run_daily_pipeline_main.sh:~143` 在 rc=0 且有 URL 时写 `last_digest_main.json`（含 date/url/status/completed_at/digest_local_path），且「有 URL 但无本地 digest」会 `notify_failure` + `exit 1`、不写空 state。**缺口只在手工路径**：`publish_edited_digest.py:23` 只 publish/notify、不写 state；今天 v4 是手工编辑发布，故 `last_digest_main.json` 仍停在 09:32 残缺版。
**改动**：
- `scripts/publish_edited_digest.py`：加 `--mark-final` + `--line {main|sub}`，写**与自动路径完全同 schema** 的 state（Codex P1：必须贴合广播脚本）——必含 `date` / `url` / `status:"success"` / `completed_at` / **`digest_local_path`**（`broadcast_today_main.sh` 靠它读正文）/ **`line:"main"`**（对齐 `run_daily_pipeline_main.sh:143` 字段，广播脚本依赖）+ `source:"manual_edit"` / `node_token` / `title`。
- 立即用该能力把今天 v4 写入 `last_digest_main.json`（⚠️ v4 真实 wiki url 需执行前从 1-1 推送或重发确认，原记的 `KUW6wkTe` 不准）。
**验收（两条链路都覆盖）**：
- 手工：`--mark-final --line main` 后 `last_digest_main.json` url==v4、`source=="manual_edit"`；幂等重跑不污染；
- 自动：回放一次自动发布，断言 `run_daily_pipeline_main.sh` 写出的 state 指向新版（沿用既有 fail-loud，不退化）。

### Task 2（P0）whitelist 熔断（读失败/过少即 abort，禁止发布）
**问题**：`read_whitelist` 失败返回 0 条，pipeline 继续生成残缺版并 publish+notify（09:16/10:04/10:16 三次）。
**改动**：
- `pipeline/daily.py` step 1 后：`if len(whitelist)==0 or len(whitelist) < WHITELIST_MIN(=300)` → **abort**（退避重试 N 次后仍不足则退出，**不进入采集/extract/publish/notify**）。
- `read_whitelist` 区分「真空集」与「读取失败」：失败抛错而非返回 []。
**验收**：
- 注入「飞书读取失败」模拟（mock `_lark_cli` 抛错）→ pipeline 退出码 ≠0、**无 publish/notify**、日志明确 `whitelist fuse triggered`；
- 正常时（**347**，main 基线）照常运行。

### Task 3（P0）arxiv 质量熔断（用 stage metrics 落地判定口径）
**问题**：DNS/网络致 arxiv 全 0 时（HTML+export 双挂），pipeline 不告警照常发 `frontier=0`。arxiv collector 本就是 HTML-primary，**不改降级顺序**。
**判定口径（Codex P1 修正，避免误杀「有新论文但无白名单命中」）**：基于 collector stage metrics 分三级——
- **直接 block（硬失败）**：`HTML 与 export 均抛网络错误`（如 nodename nor servname）——采集器整体挂掉，必拦。
- **degraded / warn（不单凭此条 block）**：`html_candidates > 0 且 matched == 0`——很可能是「当天有 arxiv 新论文、但恰好无白名单作者命中」的正常情况。标 degraded + 告警，再结合〔工作日 / 历史 frontier 基线 / author-query fallback 重试 / 人工阈值〕综合判断是否阻止 publish，**不直接拦**。
- **放行**：`html_candidates == 0`（周末/节假日/短窗口本就无新论文，正常）。
**改动**：
- `arxiv_collector` 暴露 stage metrics（`html_candidates` / `matched` / `network_error`）到 summary；
- `pipeline/daily.py`：双网络错误 → 告警 + 重试，仍失败则**阻止自动 publish**；`candidates>0 & matched=0` → 标 degraded + 告警 + fallback 重试，结合基线判断，**不直接拦**。
**验收**：
- mock `HTML/export 双网络错误` → 日志 `arxiv fuse` + 不自动 publish；
- mock `html_candidates>0 & matched=0` → 标 degraded/warn（**不必然 block**，日志可见 degraded）；
- `html_candidates==0`（空窗口）→ **放行不误杀**；
- arxiv 正常（11 篇）→ 正常发布。

### Task 4（P0）dedup mark 绑定 Bitable 写入成功（精确边界）
**问题（Codex P1 精确化）**：dedup mark 边界当前**错误地无条件执行**——`daily.py:312` 的 `dedup.mark_many(...)` 在 `if skip_bitable_write`(`:281`) 块**之外**，即使 `--skip-bitable-write`（replay/dry-run/test）也照样 mark，污染生产去重。这正是今天 frontier=0 的根因（test 跑用默认 `dedup.sqlite` 吃掉 11 篇 arxiv）。原 5-29 注释只解释「写后再 mark」的 retry-safe 语义，**未覆盖 skip-write 不应 mark 的情形**。
**正确边界（Codex）**：**只有 Bitable 写入成功才可 mark dedup**；`--skip-bitable-write` / replay / dry-run **绝不 mark**。
**改动**：
- `daily.py`：把 `:312 mark_many` **移入 `:283` 的 `else`（写库分支）内**，且**仅对写入成功的 source_id** mark（沿用 5-29「写后再 mark」retry-safe 语义，不破坏）；`skip_bitable_write` 分支不 mark。
- 文档约定：生产 `dedup_main.sqlite`（主线）/ `dedup.sqlite`（支线）/ 测试临时库**强制分离**。
**验收（含 Codex 要求的硬证据）**：
- 先 dump：把 09:47 那 11 个 arxiv `source_id` 与被污染的 `dedup.sqlite` seen 表逐条对照，确认「11 篇全被标记 already-seen」并写入复盘；
- 清理被污染的 seen（移除那 11 条或重建支线库）；
- 回归测试：带 `--skip-bitable-write` 跑一次，断言 dedup 库**条数不变**；正常发布跑一次，断言**仅写库成功**的 source_id 进 dedup。

### Task 5（P1）速度：保留图片质量的前提下提速（默认做图片，仅限时/缓存/裁剪范围）
**⚠️ 纠偏（Codex P0）**：图片提取/插入是正式日报必备能力，**不能默认跳过**。`daily.py:161`(提取)+`:457`(插入)、`regenerate_digest.py:453`(提取)+`:463`(插入) 全部**保留**；其中 regenerate 的图片提取本就在 `if args.publish:`(`:443`) 块内——预览天然不提取、无需加 skip。
**问题（真正的慢点）**：① regenerate 逐篇 coauthor enrich（`regenerate_digest.py:375-413`）；② 图片对**全部 ~70 信号**逐篇 ar5iv+PDF（`daily.py:161` 全量、`regenerate_digest.py:453-461` 全量），图片阶段 ~27min。
**改动（提速但不牺牲发布图片）**：
- **范围裁剪 + 实现抓手（Codex P1）**：图片只对「头条 ∪ arxiv 前沿论文」提取。⚠️**当前无抓手**——`DailyDigest`(daily_writer.py:266) 只返回 `signal_ids`（全部），headline 选择结果（`:203-216` 的 `headlines`）未暴露。故先补：让 `DailyDigest` 增 `headline_signal_ids=[s.source_id for s in headlines]`（或抽出可复用 `select_headlines()` helper）；范围 = `headline_signal_ids ∩ arxiv ∪ frontier(arxiv)`。**并调整提取时序**：daily.py 现在 `:161`（采集后、选 headline 前）就全量提取，需推迟到 `write()` 返回 `headline_signal_ids` 之后再按范围提取（或先用 helper 预选 headline ids 再提取）。
- **限时**：单篇提取超时预算（如 ≤30s）、图片阶段总预算（如 ≤8min）；超时跳过该篇并计入 `images_failed`，**不阻塞正文发布**。
- **缓存**：`image_extractor` 按 arxiv_id 落盘缓存（`data/cache/images/`），重生成/重试命中缓存不重抓。
- **author enrich**：仅此步加 `--skip-author-enrich`，**预览默认跳过**，正式发布默认做（保留署名质量）。
- **收敛临时开关**：`daily.py:165` `HH_SKIP_IMAGE_ENRICH` 由「默认跳过」改为「仅 emergency override（如 `--emergency-no-images`）」，默认做图片。
- 阶段日志：每步打印开始/结束/耗时 + `images_inserted/images_failed`。
**验收（耗时 + 图片质量双约束）**：
- 正式发布（--publish）后飞书文档**至少成功插入若干论文图片**，日志/state 记录 `images_inserted/images_failed`；
- 图片阶段超时**不阻塞正文发布**，且输出**可重试命令 + 告警**；
- `regenerate` 预览（跳过 author enrich + 仅头条配图）：耗时显著下降（目标 **≤10min**）；完整 `daily.py`：**≤45–60min**；
- 日志可见每阶段耗时。

### Task 6（P1）_lark_cli 总超时预算 + preflight + 可观测性
**改动**：
- `_lark_cli` 重试加**总超时预算**（如全程 ≤120s）+ 每次重试打印 `attempt i/N, waited Xs`；
- 新增 **preflight**（pipeline 启动前）：探测飞书 API / arxiv / 网络，任一不可用 → 不进入生成/发布，告警退出；
- 主线启动前**网络就绪检查**（机器唤醒场景）。
**验收**：
- preflight 在飞书不可用时直接退出、无残缺发布；
- _lark_cli 故障时有明确进度日志、不无限拖。

---

## 3. 端到端验收（回放 6.1 窗口）

```bash
cd "/Users/haolinguo/claude code/HH research/daily-digest"
# 回放当日窗口；用全新临时 dedup 库（Codex P2：避免重复跑被自己的 replay dedup 吃掉）
REPLAY_DB="$(mktemp -t dedup_replay.XXXXXX).sqlite"; rm -f "$REPLAY_DB"
LARK_CLI_NO_PROXY=1 .venv/bin/python -m hh_research.pipeline.daily \
  --since 2026-06-01T01:00:00Z --until 2026-06-02T01:00:00Z \
  --arxiv-mode category --dedup-db "$REPLAY_DB" \
  --skip-bitable-write --skip-metrics   # 验收用，不污染生产；每次全新库保证可重复
```
**通过标准**：
1. `whitelist: 347`（main 基线原版，熔断未误触发）；
2. `frontier > 0` 且 `industry > 0`（arxiv 进前沿研究）；
3. v7 quality gate 通过（不靠 `--allow-review-fail`）；
4. 若走发布路径（另跑一次 `--publish`，**两条链路都验**）：`last_digest_main.json` 指向新版、`source` 正确；
5. **图片**：发布后飞书文档 `images_inserted > 0`（或明确记录 `images_inserted/images_failed`）；图片阶段超时不阻塞正文，留可重试命令 + 告警；
6. **dedup**：`--skip-bitable-write` 回放后 dedup 库条数不变（无污染）；
7. 总耗时达 Task 5 目标（regenerate ≤10min / pipeline ≤45–60min）。

---

## 4. 执行顺序与回滚
- 顺序：Task 1（救急 state）→ Task 2/3/4（P0 熔断+隔离）→ Task 5/6（速度+可观测）。
- 每个 Task 独立 commit（TDD：先写失败测试再实现），便于回滚。
- 回滚源：`data/state/*.json` 改前备份；dedup 改动可逆。

## 5. 给 Codex / 用户的待确认（本轮已回应项已标注）
0. **【新增·需用户拍板】base = `main`（5.31 基线，347 whitelist）**，非 signal-expansion（420 未过团队审核）——本轮已按此重写「执行环境固定」；若想留在 signal-expansion 请告知，我再调。
1. `WHITELIST_MIN=300` 阈值对 main 的 **347** whitelist 是否合适。
2. ~~arxiv 熔断判定~~ → **已按 Codex P1 修正（Task 3）**：仅双网络错误直接 block；`candidates>0 & matched=0` 降级为 degraded/warn + 综合判断，不直接拦（避免误杀「有新论文无白名单命中」）。
3. 速度目标（regenerate ≤10min / pipeline ≤45–60min）是否接受。
4. ~~临时止血去留~~ → **已定**：base 切 main 后按 TDD 重做（不直接 cherry-pick）；`_lark_cli` 重试 + 总超时预算（Task 6）、图片 emergency-only 默认做图（Task 5）。
5. ~~图片裁剪抓手~~ → **已补实现口径（Task 5）**：`DailyDigest.headline_signal_ids` + 调整提取时序，范围 = 头条∩arxiv ∪ frontier(arxiv)。
6. ~~路径/HEAD 过期~~ → **已修（执行环境段）**：规范路径指向主工作区那份、标注 worktree 副本 MISSING；HEAD 不写死、执行前实测 `git rev-parse main`。
7. 是否把 v8 旁路模块（headline_classifier/selector）显式标注「未接入、暂不维护」以免后续混淆。
