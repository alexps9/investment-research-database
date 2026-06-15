<title>HH Research Daily · 2026-06-13</title>

<h1>📌 Top 3 大新闻</h1>

<p>{anchor:top_1}</p>
<h3>Prometheus 完成 120 亿美元融资——贝索斯押注"物理世界通用工程师"，具身 AI 赛道进入超大规模资本竞争</h3>
<ul>
  <li><b>信号源</b>：<b>TechCrunch</b>（<a href="https://x.com/TechCrunch/status/2065238978702561698">X 报道</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Prometheus 的定位不是又一家做聊天机器人的公司——它明确对标"物理世界"，目标是让 AI 具备工程设计与真实环境交互的通用能力，用 "artificial general engineer"（通用工程智能）这个标签与纯软件 AGI 路线划清界限。<b>120 亿美元的融资规模将 Prometheus 直接拉到与 xAI、Anthropic 同一量级</b>，标志着具身/物理 AI 赛道的资本密度已从"创业期"跳升到"基础设施期"。这与 World Labs、Figure、Physical Intelligence 等公司形成共振：资本正在押注"能在物理世界干活的 AI"将是下一个计算平台。对 AI infra 层（机器人专用芯片、仿真平台、传感器生态）和应用层（工厂自动化、建筑、能源工程）而言，这是一个明确的市场信号。</p>
</callout>
<p text-indent="1"><b>Prometheus</b> 获得 Jeff Bezos 支持，本轮融资规模达 <b>120 亿美元</b>，目标是构建"人工通用工程师"（artificial general engineer，AGE）——即能在物理世界执行工程设计、规划与操作任务的通用 AI 系统，而非局限于软件或文字层面的能力。</p>
<p text-indent="1">该定位与近年来兴起的具身 AI 赛道高度重合，但相比传统机器人公司更强调"工程推理"能力，即让 AI 理解并参与设计图纸、结构规划、制造流程等高层次工程任务，而不仅仅是执行搬运或装配的低层动作。</p>
<p text-indent="1"><em>* 注：融资金额与公司技术细节来自 TechCrunch 媒体报道，Prometheus 尚未发布官方公告，具体技术路线与资方构成以后续官方披露为准。</em></p>

<hr/>

<p>{anchor:top_2}</p>
<h3>Google AI 单周密集发布：Gemini 3.5 实时语音翻译 API 开放、DiffusionGemma 探索文字扩散新架构</h3>
<ul>
  <li><b>信号源</b>：<b>GoogleAI</b> 官方（<a href="https://x.com/GoogleAI/status/2065478191247130703">X · 周更汇总</a>）· <b>Google AI Developers</b> 官方（<a href="https://x.com/googleaidevs/status/2065548876753654106">X · Live Translate 详情</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">这批更新里最值得关注的是两个方向：一是<b> Gemini 3.5 Live Translate 将语音到语音实时翻译（S2ST）以 API 形式开放</b>，这意味着开发者可以把"即时同传"直接嵌入产品，从直播本地化到远程医疗翻译都是潜在场景；二是 DiffusionGemma 把文字生成从"自回归逐字预测"换成"扩散式并行去噪"，这是架构层面的路线探索——如果文本扩散在延迟和质量上追上自回归，将从根本上改变 LLM 推理的计算图。NotebookLM 的 agentic 升级和 Project Genie 全球开放属于产品生态拓展，与上述两条技术路线一起，显示 Google 在同一周内同时推进能力边界和生态铺排。</p>
</callout>
<p text-indent="1"><b>Gemini 3.5 Live Translate</b>：通过 <b>Gemini Live API</b> 提供近实时语音到语音流式翻译（speech-to-speech streaming translation，S2ST），持续接收语音流并实时输出目标语言语音及同步文字转录，可用于直播、会议、全球广播的即时本地化。</p>
<p text-indent="1"><b>DiffusionGemma</b>：以文本扩散（text diffusion）方式替代自回归生成文字，模型以并行去噪的方式生成输出而非逐字预测。这是对主流 Transformer 自回归架构的差异化探索，目前以实验性开源模型形式发布。</p>
<p text-indent="1"><b>其他更新</b>：NotebookLM 获得 agentic 能力升级（可主动执行多步骤任务），Project Genie（互动世界生成）面向全球用户开放。</p>

<hr/>

<p>{anchor:top_3}</p>
<h3>DeepMind 联合创始人 Shane Legg 发布 AGI→ASI 路线图——四条路径分析，多智能体集体涌现是最被低估的</h3>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.12683">Beyond AGI: Pathways to Artificial Superintelligence</a>（Tim Genewein · 一作；<b>Shane Legg</b> · 资深合作）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">这份报告的价值不在于预测时间表，而在于<b>把"AGI 之后会发生什么"这个问题从玄学拉回到工程框架</b>。四条路径中，递归自我改进路径因依赖"AI 加速 AI 研发"的正反馈而最受关注，但报告同样指出其受硬件稀缺与真实世界测试需求制约；多智能体集体涌现路径则被认为是当前研究社区最低估的——大规模专业化 agent 分工协作可能比单一超强模型更早实现"超越大型人类组织"的认知门槛。报告明确拒绝了"单一奇点跃迁"叙事，认为未来更可能是 AI 在科技各领域引发的一系列连续性突破。对 AI 安全、治理与基础设施领域而言，这份来自 DeepMind 创始人的框架文件具有较高参考权重。</p>
</callout>
<p text-indent="1">报告将从 AGI 到人工通用超级智能（Artificial Superintelligence，ASI，即认知能力超越大规模人类组织的系统）的路径归纳为四类：<b>持续 scaling AGI</b>、<b>AI 范式转变</b>（新架构或训练范式取代现有主流）、<b>递归自我改进</b>（AI 加速 AI 研发的正反馈循环）、以及<b>大规模多智能体集体涌现</b>（多个专业化 AI agent 协作超越单一系统）。</p>
<p text-indent="1">以 Universal AI（理论上的最优智能体）为形式化上界，报告为每条路径梳理了关键摩擦点：数据/算力/能源天花板（scaling 路径）、范式转换的不可预期性（范式路径）、硬件稀缺与真实世界验证成本（递归改进路径）、协调与通信开销（多智能体路径）。</p>
<p text-indent="1">报告结论强调：通往 ASI 的不确定性极高，无法排除未来数年持续加速的可能，准备应对这一前景需要全球跨学科协同。报告同时提出若干开放研究问题，供后续社区探讨。</p>

<p><b>Researcher Mapping</b></p>
<table>
  <colgroup><col width="180"/><col/><col width="130"/><col width="200"/></colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p><b>姓名（角色）</b></p></th>
      <th background-color="light-gray"><p><b>现状</b></p></th>
      <th background-color="light-gray"><p><b>GitHub</b></p></th>
      <th background-color="light-gray"><p><b>邮箱 / 主页</b></p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td vertical-align="top"><p>Tim Genewein（一作）</p></td>
      <td vertical-align="top"><p>Google DeepMind (United Kingdom)</p></td>
      <td vertical-align="top"><p><a href="https://github.com/tgenewein">@tgenewein</a></p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>Shane Legg</b>（资深合作）</p></td>
      <td vertical-align="top"><p>Google DeepMind · 联合创始人</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
  </tbody>
</table>

<hr/>

<h1>🗺️ 今日导览</h1>
<p><a href="https://anchor.placeholder/section_资本动向"><b>💰 资本动向</b></a>　Mistral 据传融资 €30 亿，估值翻倍至 €200 亿（<a href="https://anchor.placeholder/section_资本动向">↗</a>）</p>
<p><a href="https://anchor.placeholder/section_前沿技术"><b>🔬 前沿技术</b></a></p>
<grid>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_基础模型"><b>基础模型</b></a></p>
    <ul>
      <li>MiniMax M3 开源：1M token + 稀疏注意力架构 MSA（<a href="https://anchor.placeholder/card_1">↗</a>）</li>
      <li>Kimi K2.7-Code：1T MoE，thinking tokens 减少 30%（<a href="https://anchor.placeholder/card_2">↗</a>）</li>
      <li>Qwen3.7-Max 旗舰发布：专攻 agentic + 前端代码生成（<a href="https://anchor.placeholder/card_3">↗</a>）</li>
      <li>FrontierMath v2：42% 题目修正，GPT-5.5 领跑 Tiers 1–3（<a href="https://anchor.placeholder/card_4">↗</a>）</li>
      <li>CRPO 论文：LLM 心理健康评估 F1 +10.4 个百分点（<a href="https://anchor.placeholder/card_5">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_世界模型"><b>世界模型</b></a></p>
    <ul>
      <li>World Labs 三连发：Modality Forcing + Flex4DHuman + 3D 论文（<a href="https://anchor.placeholder/card_6">↗</a>）</li>
      <li>Mana 论文：机器人操控"动画化"，zero-shot sim-to-real（<a href="https://anchor.placeholder/card_7">↗</a>）</li>
      <li>FRS 论文：反向 flow 引导机器人策略，成功率最高 +95%（<a href="https://anchor.placeholder/card_8">↗</a>）</li>
      <li>Google DeepMind 在欧洲启动 Robotics Accelerator（<a href="https://anchor.placeholder/card_9">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_AI_infra"><b>AI infra</b></a></p>
    <ul>
      <li>NVIDIA GB300 NVL72：每兆瓦并发 agent 数是 H200 的 20 倍（<a href="https://anchor.placeholder/card_10">↗</a>）</li>
      <li>Anthropic 转向自建数据中心，美国超 1GW 容量（<a href="https://anchor.placeholder/card_11">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_ai4s"><b>AI4S</b></a></p>
    <ul>
      <li>Nature Medicine：通用 LLM 临床问答全面超越专用医疗 AI（<a href="https://anchor.placeholder/card_12">↗</a>）</li>
    </ul>
  </column>
</grid>

<p>{anchor:section_资本动向}</p>
<h1>💰 资本动向</h1>
<ul>
  <li><b>Mistral</b>（欧洲顶尖开源基础模型公司，Mistral 7B/Large 等系列的开发商）：据传正在寻求新一轮融资，目标金额 <b>€30 亿</b>，估值约 <b>€200 亿</b>（约 231.5 亿美元），较上一轮 Series C 的 €117 亿估值接近翻倍。若消息属实，此次估值跳升反映出头部开源模型公司在当前市场环境下持续获得资本青睐，欧洲 AI 赛道的资本密度正快速向美国顶尖公司靠拢。（<a href="https://techcrunch.com/2026/06/12/mistral-is-rumored-to-be-raising-e3b-at-e20-valuation/">↗</a>）<em>* 注：融资为传闻，来自 TechCrunch 媒体报道，Mistral 官方未确认。</em></li>
</ul>

<p>{anchor:section_前沿技术}</p>
<h1>🔬 前沿技术</h1>

<p>{anchor:section_基础模型}</p>
<h3>基础模型</h3>

<p>{anchor:card_1}</p>
<h4>MiniMax 开源旗舰模型 M3：1M token 超长上下文 + 稀疏注意力架构 MSA，vLLM 当日支持</h4>
<ul>
  <li><b>信号源</b>：<b>vLLM</b> 官方（<a href="https://x.com/vllm_project/status/2065445059039031799">X</a>）· <b>NVIDIA AI</b> 官方（<a href="https://x.com/NVIDIAAI/status/2065445179289665672">X</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">MiniMax M3 的核心技术亮点在于 <b>MSA（Mixture Sparse Attention，混合稀疏注意力）架构</b>：将 KV 缓存（KV cache，模型处理长文本时保存的中间结果）切成 128-token 块，每次查询先对块打分再只对高分块计算完整注意力，使 1M token 的超长上下文 serving 在实际中变得可行，而非只是理论支持。vLLM day-0 集成 + NVIDIA 免费 GPU 端点覆盖 NVIDIA 和 AMD 双硬件，显示 MiniMax 在开源生态布局上策略清晰。</p>
</callout>
<p text-indent="1"><b>MiniMax M3</b> 是 MiniMax 发布的开源旗舰多模态模型，支持文本、图像和视频三种输入，上下文窗口达 <b>1M token</b>。架构核心是 MoE（Mixture of Experts，专家混合架构）+ MSA（稀疏注意力）+ MLA（Multi-head Latent Attention）组合，原生支持 computer use（直接操控计算机界面）能力。</p>
<p text-indent="1">vLLM 提供当日（day-0）支持，覆盖 NVIDIA 和 AMD 硬件；NVIDIA NeMo RL 框架同步支持，提供 GRPO（group relative policy optimization）后训练配方，方便开发者对 M3 进行针对性微调。NVIDIA 另为 M3 提供免费 GPU 加速推理端点。</p>

<p>{anchor:card_2}</p>
<h4>Kimi K2.7-Code 发布：1T 参数 MoE，thinking tokens 减少约 30%，256K 上下文</h4>
<ul>
  <li><b>信号源</b>：<b>vLLM</b> 官方（<a href="https://x.com/vllm_project/status/2065427423148318747">X</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">K2.7-Code 是 Moonshot AI 针对代码与 agentic 任务的专项优化版本，核心改进是<b>减少约 30% 的 thinking tokens（推理过程中模型"自言自语"的中间步骤）</b>，在不损失精度的前提下降低推理延迟和成本。这对多轮工具调用的 agentic workload 尤为重要——每轮调用都缩短意味着整体任务时延成倍压缩。可直接复用 K2.6 的 vLLM 部署配置，迁移成本极低。</p>
</callout>
<p text-indent="1"><b>Kimi K2.7-Code</b> 是 <b>Moonshot AI</b> 在 K2.6 基础上推出的代码与 agentic 专项优化模型，总参数量 <b>1T</b>，每个 token 激活 <b>32B</b> 参数（MoE 架构），上下文窗口 <b>256K token</b>。相比 K2.6，主要改进是 thinking tokens 减少约 <b>30%</b>，提升推理效率。</p>
<p text-indent="1">模型采用 MLA（Multi-head Latent Attention）注意力机制，vLLM 提供完整支持，部署时可直接复用 K2.6 的配置文件。</p>

<p>{anchor:card_3}</p>
<h4>阿里云发布 Qwen3.7-Max：主打 agentic 任务与前端代码，单条 prompt 生成可交互 3D 场景</h4>
<ul>
  <li><b>信号源</b>：<b>Alibaba Cloud</b> 官方（<a href="https://x.com/alibaba_cloud/status/2065337945628770816">X</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Qwen3.7-Max 将前端代码生成（Three.js 3D 场景、动态 SVG）作为重点展示能力，这标志着大模型在"从自然语言直接生成可运行 Web 体验"方向上的竞争已进入能力展示阶段。<b>agentic workload 与前端渲染能力的组合定位</b>，覆盖了从自动化工作流到创意设计工具的较宽应用场景，是对 Claude 和 GPT-4o 类模型在代码生成赛道的直接竞争。</p>
</callout>
<p text-indent="1"><b>Qwen3.7-Max</b> 是 <b>Alibaba Cloud</b> 发布的新旗舰模型，定位为 agentic 工作负载与前端代码生成的专项优化模型。官方展示能力包括：从单条 prompt 直接生成 Three.js 3D 交互场景、动态 SVG 图形，以及复杂多步骤 agentic 任务的自动执行。</p>
<p text-indent="1">该模型延续 Qwen 系列的开放策略，具体参数规模与 benchmark 成绩官方未随本次发布完整披露。</p>

<p>{anchor:card_4}</p>
<h4>FrontierMath v2 更新：42% 题目经审计修正，GPT-5.5 领跑 Tiers 1–3，Claude Fable 5 紧随其后</h4>
<ul>
  <li><b>信号源</b>：<b>Epoch AI</b> 官方（<a href="https://x.com/EpochAIResearch/status/2065488154086568445">X · v2 发布</a> · <a href="https://x.com/EpochAIResearch/status/2065511916035018943">X · Claude Fable 5 成绩</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">此次 FrontierMath v2 的意义不仅是更新排行榜，更是一次<b>对 benchmark 本身可靠性的公开审计</b>——42% 的题目被发现存在错误并经修正，说明高难度数学评测的题目质量本身就是一个需要持续维护的工程问题。修正后 GPT-5.5（xhigh 档）以 <b>85%</b> 领跑 Tiers 1–3，Google AI co-mathematician 以 <b>76%</b> 领跑 Tier 4，Claude Fable 5 在 Tiers 1–3 达到 <b>87%</b>、Tier 4 达到 <b>88%</b>。Epoch AI 同时表示 FrontierMath 低难度层级已趋于饱和，未来将转向真实数学研究前沿的开放问题。</p>
</callout>
<p text-indent="1"><b>Epoch AI</b> 对数学推理 benchmark <b>FrontierMath</b> 进行大规模错误审计，<b>42%</b> 的题目受影响并完成修正，更新后的 v2 版本同步公开新排行榜。FrontierMath 是专为测试前沿数学能力设计的分层 benchmark，共分 Tier 1–4，难度从竞赛数学到数学研究前沿递进。</p>
<p text-indent="1">修正后各模型成绩：<b>GPT-5.5</b>（xhigh 档）在 Tiers 1–3 得分 <b>85%</b>；<b>Google AI co-mathematician</b> 在 Tier 4 得分 <b>76%</b>；<b>Claude Fable 5</b> 在 Tiers 1–3 达到 <b>87%</b>，Tier 4 达到 <b>88%</b>。<em>* 注：模型版本名称与分档来自 Epoch AI 推文，非各厂商官方发布口径。</em></p>

<p>{anchor:card_5}</p>
<h4>CRPO 论文：阶段性熵调节让 LLM "从模糊到确定"，心理健康评估 F1 平均提升 10.4 个百分点</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.13176">Cognitive Relative Policy Optimization for LLM Mental Health Assessment</a>（<b>Xin Wang</b> · 一作）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">CRPO 的核心创新在于将推理过程的"早探索、晚收敛"行为形式化为一种<b>阶段性熵正则化（stage-wise entropy regularization）</b>机制——推理早期允许高不确定性广泛探索，后期强制向确定判断收敛，模拟临床医生"广泛问诊→锁定诊断"的认知过程。在 8 个心理健康数据集上平均 weighted F1 超越最佳 RL baseline <b>10.4 个百分点</b>，这类方法在任何需要"先发散再收敛"的专业推理场景（法律、医疗、教育评估）均有迁移潜力。</p>
</callout>
<p text-indent="1">CRPO（Cognitive Relative Policy Optimization）在 GRPO（Group Relative Policy Optimization）框架基础上扩展，引入认知评估理论（cognitive appraisal theory）将推理过程分为多个阶段：早期阶段设置较高的熵约束（即允许模型"不确定"，广泛探索可能的评估路径），后期阶段逐步降低允许熵值，迫使模型向高置信判断收敛。</p>
<p text-indent="1">基于 CRPO 训练的模型 <b>Mental-R1</b> 在 <b>8 个心理健康评估数据集</b>上平均 weighted F1 较最佳强化学习 baseline 提升 <b>10.4 个百分点</b>，在推理密集型案例中优势尤为明显。</p>

<p><b>Researcher Mapping</b></p>
<table>
  <colgroup><col width="180"/><col/><col width="130"/><col width="200"/></colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p><b>姓名（角色）</b></p></th>
      <th background-color="light-gray"><p><b>现状</b></p></th>
      <th background-color="light-gray"><p><b>GitHub</b></p></th>
      <th background-color="light-gray"><p><b>邮箱 / 主页</b></p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td vertical-align="top"><p><b>Xin Wang</b>（一作）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="https://eric-xw.github.io">主页</a></p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:section_世界模型}</p>
<h3>世界模型</h3>

<p>{anchor:card_6}</p>
<h4>World Labs 三连发：Modality Forcing 让图像模型"长出"深度感知，Flex4DHuman 从手机视频还原动态 4D 人体</h4>
<ul>
  <li><b>信号源</b>：<b>World Labs</b> 官方（<a href="https://x.com/theworldlabs/status/2065466833571123542">X · Modality Forcing</a> · <a href="https://x.com/theworldlabs/status/2065466835601068360">X · Flex4DHuman</a> · <a href="https://x.com/theworldlabs/status/2065466830052098058">X · 3D 论文汇总</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">World Labs 同日发布三个研究方向，聚焦将现有 2D 生成能力提升为 3D/4D 世界理解能力。<b>Modality Forcing</b> 是其中最具架构意义的一项：不重新设计模型，而是通过训练技巧让已有的 text-to-image 模型同时学会生成和理解深度信息，统一 text-to-RGBD（同时生成 RGB 图像和深度图）、深度估计和 depth-to-image 三个原本分立的任务。<b>Flex4DHuman</b> 则解决了从单台手机拍摄的视频重建动态 4D 人体模型的难题，先用微调的视频扩散模型"脑补"出多视角同步画面，再蒸馏为 4D Gaussian Splatting（一种可以自由旋转视角的动态 3D 表示方法）表示。</p>
</callout>
<p text-indent="1"><b>Modality Forcing</b>：在 text-to-image 模型的训练阶段引入深度信息，让模型学会联合生成 RGB+深度（RGBD）输出，并同时支持独立的深度估计和 depth-to-image 任务。核心思路是利用现有大规模图像模型的已有能力，通过 modality forcing 技巧扩展其感知维度，而非从头训练专用深度模型。</p>
<p text-indent="1"><b>Flex4DHuman</b>：输入单目视频（普通单镜头拍摄），通过经过微调的视频扩散模型生成多视角同步视频帧，再将这些多视角画面蒸馏为 <b>4D Gaussian Splatting</b> 表示，可将人物舞蹈等动态内容合成进 3D 场景并支持自由视角浏览。</p>

<p>{anchor:card_7}</p>
<h4>Mana 论文：把机器人操控重新定义为"动画关键帧"问题，四种关节工具 zero-shot 迁移至真实世界</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.13677">Mana: Dexterous Manipulation as Animation</a>（Guanya Shi · 共一；<b>Pieter Abbeel</b> · 合作）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Mana 的核心洞见是重新定义"数据标注"——不需要采集机器人遥操作数据，也不需要演示视频，只需用户点击鼠标标注工具的功能关键点（如剪刀的开合轴），系统自动完成从关键帧到完整操控轨迹的所有生成步骤。<b>每件工具标注时间不足 1 分钟</b>，配合仿真到真实（sim-to-real）的零样本迁移，大幅降低了灵巧操控任务的数据成本门槛。这一范式若能扩展到更多工具类型，将对工业机器人末端执行器能力产生直接影响。</p>
</callout>
<p text-indent="1">Mana（Manipulation Animator）框架将机器人灵巧操控（dexterous manipulation，即用机器人手部精细操控物体）重新定义为动画问题：以程序化生成的抓取姿势作为关键帧，运动规划器将关键帧扩展为粗粒度轨迹，强化学习再对接触力和手指协调进行精细化优化。</p>
<p text-indent="1">用户只需为工具标注"功能可供性"（functional affordance，即工具的哪个部分用于什么动作，如剪刀的刀刃开合轴），耗时 <b>< 1 分钟</b>。该框架在剪刀、钳子等 <b>4 种</b>不同尺寸和关节类型的工具上验证了仿真到现实（sim-to-real）的零样本迁移，覆盖抓取与手内操控两个阶段。</p>

<p><b>Researcher Mapping</b></p>
<table>
  <colgroup><col width="180"/><col/><col width="130"/><col width="200"/></colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p><b>姓名（角色）</b></p></th>
      <th background-color="light-gray"><p><b>现状</b></p></th>
      <th background-color="light-gray"><p><b>GitHub</b></p></th>
      <th background-color="light-gray"><p><b>邮箱 / 主页</b></p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td vertical-align="top"><p>Guanya Shi（共一）</p></td>
      <td vertical-align="top"><p>Carnegie Mellon University · MIT PhD 在读</p></td>
      <td vertical-align="top"><p><a href="https://github.com/GuanyaShi">@GuanyaShi</a></p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>Pieter Abbeel</b>（合作）</p></td>
      <td vertical-align="top"><p>Berkeley College · Professor at UCB</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="http://www.cs.berkeley.edu/~pabbeel">主页</a></p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:card_8}</p>
<h4>FRS 论文（Chelsea Finn）：把机器人策略"反向运行"寻找更优动作，BC 蒸馏后成功率最高提升 95%</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.13675">Flow Reversal Steering for Robot Manipulation</a>（Andy Sing Ong Tang · 一作；<b>Chelsea Finn</b> · 合作）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">FRS（Flow Reversal Steering，反向流引导）的关键贡献是将 flow matching 生成模型（一种通过学习"从噪声到数据"的路径来生成内容的方法）的可逆性用于机器人控制：把次优动作反向映射到隐空间找到对应噪声，再在噪声空间搜索更好的起点，正向生成高质量动作。<b>这使得语言描述和粗略示范都能成为机器人策略的引导信号</b>，且无需重新收集演示数据。结合行为克隆（behavioral cloning，BC，即让小模型模仿 FRS 的输出）蒸馏后，不到一分钟训练即可将任务成功率提升最高 <b>95%</b>，对数据效率极为敏感的机器人学习场景有较高实用价值。</p>
</callout>
<p text-indent="1">FRS 以 flow matching 通用策略（generalist policy）为基础，利用流常微分方程（flow ODE）的可逆性：给定一个粗糙但语义合理的动作，通过反向积分将其映射到对应的隐空间噪声；在噪声空间中搜索更靠近高质量动作模式的邻近点，再正向积分还原为优质动作。支持三种使用场景：零样本控制提升、行为克隆蒸馏、以及强化学习（RL）探索引导。</p>
<p text-indent="1">实验结果：FRS 引导下的 BC 蒸馏策略在不到一分钟训练内成功率最高提升 <b>95%</b>；作为 RL 引导信号时，FRS 在多个标准 RL 无法改进的任务上取得性能提升。实验覆盖仿真和真实世界操控任务。</p>

<p><b>Researcher Mapping</b></p>
<table>
  <colgroup><col width="180"/><col/><col width="130"/><col width="200"/></colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p><b>姓名（角色）</b></p></th>
      <th background-color="light-gray"><p><b>现状</b></p></th>
      <th background-color="light-gray"><p><b>GitHub</b></p></th>
      <th background-color="light-gray"><p><b>邮箱 / 主页</b></p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td vertical-align="top"><p>Andy Sing Ong Tang（一作）</p></td>
      <td vertical-align="top"><p>—；导师：Chelsea Finn</p></td>
      <td vertical-align="top"><p><a href="https://github.com/andytang2008">@andytang2008</a></p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>Chelsea Finn</b>（合作）</p></td>
      <td vertical-align="top"><p>Stanford · AP at Stanford；Co-founder of Physical Intelligence</p></td>
      <td vertical-align="top"><p><a href="http://www.github.com/cbfinn/">@cbfinn</a></p></td>
      <td vertical-align="top"><p><a href="http://ai.stanford.edu/~cbfinn">主页</a></p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:card_9}</p>
<h4>Google DeepMind 在欧洲启动 Robotics Accelerator：首批 15 家初创公司接入 Gemini Robotics 技术栈</h4>
<ul>
  <li><b>信号源</b>：<b>Google DeepMind</b> 官方（<a href="https://x.com/GoogleDeepMind/status/2065388989146628563">X</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Google DeepMind 通过孵化器形式将 Gemini Robotics 模型开放给欧洲机器人初创公司，<b>三个月加速期内提供 Gemini Robotics 模型访问权限和 AI 技术栈支持</b>。这是一种典型的"生态圈地"策略——用计算资源和模型访问权换取对机器人应用层的影响力，与 AWS、GCP 对 AI 初创公司的早期绑定模式类似，但目标从云算力下沉到具身 AI 平台层。首批 15 家公司覆盖欧洲，时间节点与 Prometheus 融资同日，具身 AI 生态正在多个维度同步加速构建。</p>
</callout>
<p text-indent="1"><b>Google DeepMind Robotics Accelerator</b> 首批招募 <b>15 家</b>欧洲机器人初创公司，为期 <b>三个月</b>，参与公司可获得 Gemini Robotics 模型访问权限及 DeepMind 具身 AI 技术栈支持。该项目目标是加速 physical AI（物理 AI，即能在真实物理环境中运作的 AI 系统）生态在欧洲的落地。</p>

<p>{anchor:section_AI_infra}</p>
<h3>AI infra</h3>

<p>{anchor:card_10}</p>
<h4>NVIDIA GB300 NVL72 AgentPerf 首测：每兆瓦并发 coding agent 数是 H200 的 20 倍</h4>
<ul>
  <li><b>信号源</b>：<b>NVIDIA Blog</b>（<a href="https://blogs.nvidia.com/blog/nvidia-blackwell-agentperf-artificial-analysis/">官方博客</a>）· <b>Rohan Paul</b>（<a href="https://x.com/rohanpaul_ai/status/2065576558312710584">X · 技术解读</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">AgentPerf 是业内首个专为 agentic AI 工作负载设计的基础设施 benchmark，其核心指标是"在保证响应时效的前提下，每兆瓦功耗能支持多少并发 agent"——这与传统的 tokens/s 吞吐量测试有本质区别，更贴近真实的多 agent 长上下文调用场景。<b>GB300 NVL72 以 61,400 并发 coding agents/MW 领跑，约为上代 H200（2,600/MW）的 20 倍</b>，核心来源于 72 GPU NVLink 机架级互联、MoE 专家路由分布式调度与通信-计算重叠优化。AgentPerf 成为新的基础设施能效评比维度，未来 AMD、Google TPU 等平台的 agentic 能效对比将更有据可查。</p>
</callout>
<p text-indent="1">Artificial Analysis 发布业内首个 agentic AI 基础设施 benchmark <b>AgentPerf</b>，核心指标为在严格延迟约束下每兆瓦可支持的最大并发 AI agent 数量，支持 5K–131K token 超长上下文，综合评估内存、网络、MoE 路由（专家混合模型中的请求分发逻辑）和延迟等维度。</p>
<p text-indent="1"><b>NVIDIA Blackwell Ultra GB300 NVL72</b> 在首轮测试中以每兆瓦 <b>61,400</b> 个并发 coding agents 领跑，上代 <b>H200</b> 为每兆瓦 <b>2,600</b> 个，差距约 <b>20 倍</b>。该平台采用 72 GPU NVLink 机架级互联架构，并通过通信-计算重叠优化提升 agentic workload 下的实际能效。</p>

<p>{anchor:card_11}</p>
<h4>Anthropic 转向自建数据中心：美国规划超 1GW 容量，Colossus 1 集群据报已租给 Anthropic</h4>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b>（<a href="https://x.com/rohanpaul_ai/status/2065476551349870921">X · The Information 转述</a> · <a href="https://x.com/PolymarketMoney/status/2065507489546985838">X · Colossus 租约</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Anthropic 的算力策略出现明显转向：从依赖 AWS/Google Cloud 等云服务商的"租户模式"，升级为主动租赁并运营数据中心的"基础设施运营模式"。<b>美国超 1GW 容量规划</b>若落地，将使 Anthropic 的自主算力体量进入与 OpenAI/Meta 对等的量级。Colossus 1 集群（原为 xAI 训练 Grok 使用）因算力利用率不足而转租给 Anthropic 的报道，折射出头部 AI 公司之间算力资源的动态流转——大规模 GPU 集群的闲置成本极高，转租是合理的资产利用决策。此举对 AWS Trainium 和 Google Cloud TPU 的战略布局均构成一定压力。</p>
</callout>
<p text-indent="1">据 The Information 报道（经 Rohan Paul 转述），<b>Anthropic</b> 正从纯租用云计算算力模式转向自建和管理数据中心，美国境内计划自主运营的算力容量超过 <b>1GW</b>，<b>Google</b> 据称将支持部分租约付款。相关合作包括与 Fluidstack 的 <b>500 亿美元</b>合作及 Colossus 1 整栋数据中心租约。</p>
<p text-indent="1">另据预测市场账号 Polymarket Money 报道，<b>Colossus 1</b> 超算集群（与 xAI/SpaceX 相关实体关联）因无法被 Grok 训练完全消化，已将集群租赁给 Anthropic 使用。<em>* 注：以上内容均来自媒体报道与预测市场账号，Anthropic 官方未发布公告，细节以后续官方确认为准。</em></p>

<p>{anchor:section_ai4s}</p>
<h3>AI4S</h3>

<p>{anchor:card_12}</p>
<h4>Nature Medicine 研究：通用前沿大模型临床问答全面超越专用医疗 AI，医生盲评偏好 GPT/Gemini/Claude</h4>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b>（<a href="https://x.com/rohanpaul_ai/status/2065560579167883344">X · 转述 Nature Medicine</a>）· <b>Ethan Mollick</b>（<a href="https://x.com/emollick/status/2065444925483692192">X · 评论</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">这项研究的结论对医疗 AI 赛道有直接含义：<b>通用前沿模型（GPT-5.2、Gemini 3.1 Pro、Claude Opus 4.6）在全部三项评估中均优于专为医生设计的临床 AI 产品（OpenEvidence、UpToDate Expert AI）</b>，后者甚至仅与 Google 搜索 AI 摘要持平。这并非偶然——通用模型的训练规模和知识广度使其在覆盖度和回答清晰度上具备结构性优势，而专用产品依赖的数据护城河在模型能力快速提升的背景下正在被侵蚀。这对专用医疗 AI 公司的产品定位提出挑战，单纯的"医疗数据微调"可能已不足以构建差异化竞争力。</p>
</callout>
<p text-indent="1">发表于 <b>Nature Medicine</b> 的一项研究（经 Rohan Paul 和 Ethan Mollick 转述）对比了通用前沿大模型与专用临床 AI 工具在医疗问答任务上的表现，采用执业医生盲评方式评估。</p>
<p text-indent="1">结果显示，<b>GPT-5.2、Gemini 3.1 Pro、Claude Opus 4.6</b> 在全部三项评估指标上均超越专用临床 AI 产品 <b>OpenEvidence</b> 和 <b>UpToDate Expert AI</b>；后两者的表现仅与 Google 搜索 AI Overview（自动启用的搜索摘要功能）相当。医生盲评在回答完整性和清晰度两个维度上更倾向于通用前沿模型。<em>* 注：具体测评设计与样本量以 Nature Medicine 原文为准，此处数据来自社交媒体转述。</em></p>

<hr/>
<p><em>本日报由 HH Research Pipeline 自动生成，由 Claude 抽取和撰写，以原文为准。</em></p>
<p><em>本日精选 15 条信号（Top 3 · 资本动向 1 条 · 赛道卡片 12 张）</em></p>