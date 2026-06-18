# HH Research AI Track Taxonomy

5 个赛道（含 "其他"）+ 头条候选标记。

## track（必填，单选）

- **基础模型 (Cognitive Models)**
  推理、Agents、规划、决策、强化学习、后训练、对齐、基础语言模型能力。
  典型方向：reasoning, RL, posttrain (RLHF/DPO), planning, alignment, agents, tool-use, code generation, foundation model capabilities, long-context.

- **多模态智能 (Multimodal Intelligence)**
  视觉-语言、语音、视频理解、多模态融合、感知。
  典型方向：VLM, vision-language, audio/speech, video understanding, multimodal fusion, scene understanding, grounding, contextual AI.

- **世界模型 (World Model, 含具身智能)**
  3D 重建、视频生成、世界模型、空间推理、物理推理、机器人、VLA、操控、具身智能。
  典型方向：3D reconstruction, NeRF/Gaussian splatting, video generation, world modeling, spatial AI, physical reasoning, robotics, manipulation, locomotion, VLA, embodied agents, sim2real.

- **AI infra**
  训练、推理、serving、量化、KV cache、硬件、MLSys、编译器。
  典型方向：training systems, inference optimization, KV cache, quantization, hardware, serving frameworks, MLSys, compilers, efficient inference.

- **ai4s (AI for Science)**
  科研 AI（生物 / 材料 / 化学 / 物理 / 医疗 / 气候）。
  典型方向：protein structure, drug discovery, materials, chemistry, climate, medical imaging, computational biology, physics simulation.

- **其他**
  以上都不合适（含元研究、政策、评测、数据集等）。

## is_headline_candidate（布尔，头条筛选 agent 用）

被标为 `true` 的条件（满足任一）：
1. **来自顶尖机构 / 顶尖实验室的重要内容**
   - 大厂：OpenAI / Anthropic / Google / Google DeepMind / Meta / Microsoft / NVIDIA / Apple / xAI / Mistral / DeepSeek
   - 顶尖实验室：Stanford AI Lab / Berkeley BAIR / MIT CSAIL / CMU / Princeton NLP / Tsinghua AI 等
2. **重大产品/模型发布**
   - 新模型发布（如 GPT-X、Claude X、Gemini X、Grok X、Llama X 系列）
   - 主要产品上线 / 重要新功能 / API 重大变更
3. **重大科研突破论文**
   - 提出新的训练范式 / 架构创新 / 显著性能突破
   - 解决长期未决难题
   - novelty_score = 5 的论文
4. **行业重大动态**
   - 重要融资 / 收购 / 战略合作
   - 关键人才流动（高级别）

不应标为 `true` 的：
- 普通技术分享、闲聊、评论
- 增量改进的论文（novelty_score ≤ 3）
- 个人观点、转推、回复
- 不来自顶尖机构的 incremental 工作

## headline_priority（1-5 整数，仅 is_headline_candidate=true 时填）

- 5 = 重大产品发布（如新一代旗舰模型）/ 行业级突破论文
- 4 = 重要技术发布 / 顶会接收的高影响力论文
- 3 = 顶尖机构的常规更新 / 有创新但范围较窄的论文
- 1-2 = 不应该标 headline，请重新评估

## key_terms

英文术语（1-5 个），保留原文不翻译：
- ✅ MoE, RLHF, DPO, KV cache, speculative decoding, state space models, MLA
- ❌ 不要泛化为上位概念

## novelty_score（1-5 整数）

- 5 = 行业级重大新闻（顶尖机构旗舰发布、重大突破）
- 4 = 明显创新点、值得跟踪的研究
- 3 = 中等重要、增量改进
- 2 = 弱信号，归入折叠区
- 1 = 噪声（如纯转发、闲聊）

## 写作语言规范

- `summary_zh` / `cognitive_takeaway_zh` / `core_findings_zh` / 等中文字段：**中文句子**
- 专业名词、模型名、算法名、公司名、论文标题：**保留英文原文**，不翻译
  - ✅ "Google 发布 Gemini 3，引入 MoE 架构"
  - ❌ "谷歌发布双子星 3，引入专家混合架构"
- 数字、benchmark 名称（AIME 2024, MMLU 等）：保留原样
- **重要约束**：`cognitive_takeaway_zh` 仅讲清楚研究内容本身，**不要涉及投资、商业化、市场影响判断**
