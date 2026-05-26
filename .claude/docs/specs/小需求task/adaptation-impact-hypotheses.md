# Adaptation Impact 假设检验

## 问题

36 个 adaptation 中，25 个 impact_score 在 13.5-14（最低档），原因是缺 venue_tier / institution_tier / cited_by_count 数据。
但其中有些论文明显很重要，应该有更高的分数。

## 假设：以下 adaptation 应该有显著更高的 impact

### Tier A: 应该 ≥ 40 分（有实际影响力的重要工作）

| Paper | 理由 | 预估 impact |
|-------|------|-------------|
| GR-1 (ByteDance) | 首个 GPT-style video → robot 实现，大量引用 | ~50 |
| UniPi (Google Brain) | 开创性工作：video 做 policy，2023 发表引用 200+ | ~55 |
| Cosmos Policy (NVIDIA) | 工业级 world model→policy，NVIDIA 大投入 | 42 (当前) |
| GE-Act (AgibotTech) | DiT→MoE→action，Genie Envisioner 配套实现 | ~40 |
| π0.5 (Physical Intelligence) | π0 升级版，top-tier 机构 | ~45 |

### Tier B: 应该 ≥ 30 分（有价值的跟进工作）

| Paper | 理由 | 预估 impact |
|-------|------|-------------|
| GigaBrain-0.5M (极佳视界) | 国内首个大规模 video WM→robot，Wan 基座 | ~35 |
| LDA-1B (PKU) | 10亿参数 MoE-VLA，规模化尝试 | ~30 |
| Vidarc (Alibaba) | Wan 适配自动驾驶，大厂工程落地 | ~35 |
| UWM (MIT) | 统一 world model，MIT 出品 | ~38 |
| FLARE (NVIDIA) | NVIDIA 机器人基础设施 | ~35 |

### Tier C: 当前分数基本合理（≤ 25）

| Paper | 理由 |
|-------|------|
| DiWA, WMPO, WorldEval, WorldGym | 纯 arxiv、小组工作、引用低 |
| video2act, tc_idm, video_policy | 方法论探索，无大规模验证 |

## 验证步骤

1. 对 Tier A + B 的 10 篇论文补充 venue_tier / institution_tier / cited_by_count
2. 重跑 impact 算法
3. 检查结果是否在预估范围内
4. 视觉检查：这些论文在 v2 页面上应该明显比 Tier C 大

## 视觉预期

补数据后在页面上应该看到：
- Sora 周围的 adaptation 群中，UniPi 和 UWM 应该是明显较大的点
- Cosmos 周围的 Cosmos Policy 已经比较大了
- π0 周围的 π0.5 应该接近 foundation 大小
- Wan 周围的 GigaBrain 和 Vidarc 应该中等大小，不该跟 diwa/wmpo 一样小

---

## Adaptation 标题显示假设（impact > 35 显示 8px 灰色标题）

以下 11 个 adaptation 应该在图上能看到标题文字：

| # | Paper | 预期位置（Row） | 预期附近 Foundation |
|---|-------|----------------|-------------------|
| 1 | UniPi (80.7) | diffusion_video | 在 Sora 附近 |
| 2 | Gen2Act (69.5) | diffusion_video | 在 Sora 附近 |
| 3 | π0.5 (55.0) | vla_diffusion | 在 π0 附近 |
| 4 | FLARE (46.7) | jepa_based | 单独或附近 V-JEPA |
| 5 | UWM (44.6) | diffusion_video | 在 Sora 附近 |
| 6 | GR-1 (43.3) | autoregressive_video | 在 Genie 2 附近 |
| 7 | Cosmos Policy (41.5) | diffusion_video | 在 Cosmos 附近 |
| 8 | RL Token (39.9) | vla_llm | 在 π0 或 RT-2 附近 |
| 9 | WM Robot Survey (37.5) | rssm_based | 独立 |
| 10 | Vidarc (36.6) | diffusion_video | 在 Wan 附近 |
| 11 | GE-Act (35.5) | diffusion_video | 在 Sora 附近 |

### 不应该显示标题的（impact ≤ 35）：

- GigaBrain (26.3), LDA-1B (29.0), VidMan (32.6), Fast-WAM (25.4)
- diwa, wmpo, worldeval, worldgym (13-17 分)

### 验证方法

1. 在 2024-2026 视图下，diffusion_video row 应该能看到 UniPi / Gen2Act / UWM / Cosmos Policy / Vidarc / GE-Act 六个灰色小字标题
2. autoregressive_video row 应该能看到 GR-1 标题
3. vla_diffusion row 应该能看到 π0.5 标题
4. 那些 13-17 分的小点不应该有任何文字
