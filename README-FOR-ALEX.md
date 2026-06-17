# World Model 论文数据库 & 技术路线图

> QiuTian 的 World Model 研究工具。这个分支包含完整项目，供 Alex 对接数据。

---

## 你最需要看的

### 1. 论文数据（186 篇，已标注 taxonomy）

**文件位置**: `backend/data/world_model_export.json`

**核心字段**:
| 字段 | 说明 |
|------|------|
| id | 唯一标识（如 `dreamer_v1`） |
| title | 论文简称 |
| full_title | 完整标题 |
| year / quarter | 发表时间（如 2024 Q2） |
| **lane** | 技术路线大类（4 类） |
| **row** | 技术路线子类（12 类） |
| org | 机构 |
| authors | JSON 数组，作者列表 |
| arxiv_id | arXiv ID（55 篇有） |
| cited_by_count | 真实引用数（Semantic Scholar） |
| impact_score | 综合影响力评分（0-100） |

**示例数据**:
```json
{
  "title": "Dreamer V1",
  "year": 2020, "quarter": 1,
  "lane": "rl_based",
  "row": "rssm_based",
  "org": "Google/Danijar",
  "authors": ["Danijar Hafner", "Timothy Lillicrap", "Jimmy Ba"],
  "impact_score": 91.7
}
```

### 2. Taxonomy 结构（4 Lanes x 12 Rows）

```
rl_based (RL-Based / 在想象中训练)
├── rssm_based      — PlaNet / Dreamer V1-V3
├── transformer_wm  — TD-MPC / TD-MPC2 / PWM
└── diffusion_planning — Diffuser / Decision Diffuser

video_gen (Video-Generative / 从观看中学习)
├── diffusion_video     — Sora / Cosmos / Wan / GameNGen
├── autoregressive_video — Genie 2 / LWM / Emu3
└── 3dgs_nerf           — 3DGS / NeRF 3D World Modeling

latent_space (Latent-Space / 抽象表示预测)
├── jepa_based  — I-JEPA / V-JEPA 2
├── dino_based  — DINO-WM
└── slot_based  — SlotAttention / SlotFormer / Dyn-O

vla (Policy / 策略层：从理解到行动)
├── vla_llm        — RT-2 / Octo
├── vla_diffusion  — π0 / Diffusion Policy
└── vla_driving    — DriveVLA / GAIA-1
```

### 3. 与你的数据库对接建议

你的系统里对应关系：
- 我的 `papers` → 你的 `entities` (entity_type = "paper")
- 我的 `authors` → 你的 `entities` (entity_type = "person") + `entity_relations` (AUTHORED)
- 我的 `lane/row` → 你的 `entities` (entity_type = "topic") + `entity_relations` (FOCUSES_ON)
- 我的 `org` → 你的 `organizations`

---

## 项目结构

```
backend/
├── data/world_model_export.json  ← 核心数据（JSON 导出）
├── app/
│   ├── api/world_model.py  — CRUD API
│   ├── services/           — 业务逻辑
│   └── models/             — 数据模型
└── scripts/
    ├── backfill_openalex.py    — OpenAlex 数据补全
    ├── backfill_citations_ss.py — Semantic Scholar 引用数
    └── expand_from_seeds.py    — 论文扩展（snowball）

frontend/
├── src/app/world-model-v2/  ← 主视图（Overview 投影 + 交互）
├── src/app/world-model-trunks/ ← 路线图视图（Lineage）
├── src/data/world-model-data.json ← 前端静态数据（167篇，稍旧）
└── src/components/          — React 组件
```

## 如何运行

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000/world-model-v2
```

## 数据统计

- 总论文数: **186**
- 有作者信息: 186 (100%)
- 有机构信息: 184 (99%)
- 有 arXiv ID: 55 (30%)
- 时间跨度: 2019 - 2026
- Lane 分布: Video-Gen 80 / RL-Based 52 / Policy 28 / Latent-Space 26

## 核心人物（按论文数排序）

| 人物 | 论文数 | 方向 | 机构 |
|------|--------|------|------|
| Danijar Hafner | 7 | RL-Based (RSSM) | Google → UC Berkeley |
| Pieter Abbeel | 6 | Video-Gen + RL | UC Berkeley |
| Yilun Du | 5 | Video-Gen + Diffusion | UC Berkeley / Google |
| Nicklas Hansen | 5 | RL-Based (MPC) | MIT |
| Hao Su | 5 | RL-Based (MPC) | MIT / UC San Diego |
| Timothy Lillicrap | 4 | RL-Based (RSSM) | Google/DeepMind |
| Yann LeCun | 4 | Latent-Space (JEPA) | Meta |

---

> 有问题 Slack 找我 @QiuTian
