# Hover Foundation → Adaptation 聚集高亮 — 测试用例

## 测试前提

页面: `localhost:3001/world-model-v2`，选择"2024-2026"时间范围

## Test Case 1: Hover Sora

**操作**: 鼠标悬浮在 Sora (OpenAI) 节点上
**预期**:
- Sora 自身：正常高亮（stroke 变黑）
- 以下 adaptation 应保持可见（builds_on 包含 'sora'）：
  - uwm, uva, ge_act, gen2act, video2act, tc_idm, video_policy, diwa, wmpo, worldeval, unipi
  - spatial_memory_wm, worldmodelbench, physical_principles, wisa
- 以下 foundation 应淡化至 12% opacity：
  - Cosmos, Wan, GameNGen, TeleWorld, Oasis, Vista, etc.
- 无关的 adaptation（如 vidarc→wan, cosmos_policy→cosmos）也应淡化

## Test Case 2: Hover Cosmos

**操作**: 鼠标悬浮在 Cosmos (NVIDIA) 节点上
**预期**:
- 保持可见的 adaptation：cosmos_policy, dit4dit, worldgym, dreamdojo, sana_wm, blitzgs
- 其他 foundation 和 adaptation 淡化

## Test Case 3: Hover Dreamer V3 (rl_based lane)

**操作**: 切换到"全部"时间范围，hover Dreamer V3
**预期**:
- 保持可见：dreamsmooth, pigdreamer, dymodreamer, flowdreamer, robodreamer, navmorph, adaptive_wm, coworld, latent_particle_wm
- 其他 foundation (PlaNet, Dreamer V1/V2, TD-MPC 等) 淡化

## Test Case 4: Hover π0 (vla lane)

**操作**: hover π0 (Physical Intelligence)
**预期**:
- 保持可见：pi0_7, motubrain, realtime_vla_flash, rl_token, vla_mbpo, dial
- 其他 foundation (RT-2, Octo, Diffusion Policy 等) 淡化

## Test Case 5: Hover adaptation（非 Foundation）

**操作**: hover 一个 adaptation 小点
**预期**: 不触发聚集效果，所有节点保持正常 opacity

## 验证方法

1. 打开 DevTools → 悬浮节点 → 检查其他节点的 `<g>` 元素的 `style.opacity`
2. 应该看到匹配的 adaptation 的 `opacity: 1`，不匹配的 `opacity: 0.12`
3. 或者直接目视：hover Sora 后，应该只有 Sora 及其"卫星"保持清晰，其他整行都几乎看不见
