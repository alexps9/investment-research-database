<title>HH Research Daily · 2026-06-11</title>

<h1>📌 Top 3 大新闻</h1>

<p>{anchor:top_1}</p>
<h3>Anthropic CEO Amodei 万字长文呼吁给 AI 立规矩——新模型上线前先过安全测试、由第三方把关，同天再掏 1.5 亿美元培养 AI 人才</h3>
<ul>
  <li><b>信号源</b>：<b>Anthropic</b> 官方（<a href="https://x.com/AnthropicAI/status/2064783418844762489">政策长文 @ X</a> · <a href="https://x.com/AnthropicAI/status/2064783424251101553">奖学金公告 @ X</a> · <a href="https://x.com/rohanpaul_ai/status/2064804098332111140">Rohan Paul 解读</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">这篇长文的意义不在技术，而在于它标志着 <b>AI 头部厂商正式从"我们会自觉"转向主动要求政府立硬规矩</b>。Amodei 主张的四件事说白了是：模型公开发布前必须先通过安全测试；测试不能自己说了算，要由与公司无利益关系的第三方来检查；模型的核心参数（权重）要像机密一样防止被偷；民主国家联手管住 AI 安全标准和高端芯片的流向。这些几乎逐条对应学术界和政策圈多年的呼吁——但这次是由一个正与 OpenAI、Google 激烈竞争的前沿实验室 CEO 亲自写出来。其格局逻辑类似核技术出现后美国主导建立国际原子能机构（IAEA）：<b>谁定义规则，谁就拥有框架优势</b>——若被采纳，将对缺乏安全测试体系的实验室形成事实上的准入门槛。同日的 1.5 亿美元奖学金则是另一条腿：向上影响政策、向下培养人才和用户生态，说明这是成体系的战略动作而非单纯公关。</p>
</callout>
<p text-indent="1"><b>核心主张：</b><b>Dario Amodei</b> 于 6 月 10 日发表长文，判断前沿 AI 的发展速度已经快过了政府的反应能力，提出四项具体规矩：新模型公开发布前必须先通过安全测试；由与公司无利益关系的第三方机构来检查验证；模型核心参数（权重）须按机密级别防窃取；民主国家联手协调 AI 安全标准与高端芯片出口管控——把 AI 治理和半导体地缘政治直接挂上了钩。</p>
<p text-indent="1"><b>配套动作：</b>Anthropic 同步宣布三项治理机制类新举措（细节将陆续披露），并于 6 月 11 日正式启动总额 <b>1.5 亿美元</b>的国家奖学金计划（National Fellowship Program），面向职业早期人群，目标是把 AI 技术惠益扩展至美国各地社区——这是 Anthropic 迄今在 AI 社会影响方向最大的单笔公开承诺。</p>
<p text-indent="1"><b>格局含义：</b>头部实验室主动入场将显著加快立法节奏；这一表态若引发其他前沿实验室跟进或反驳，将成为 2026 年 AI 政策走向的重要坐标。</p>
<p text-indent="1"><em>* 注：长文内容综合官方账号与 Rohan Paul 转述解读，三项新举措细节尚未在官网完整披露，以原文为准。</em></p>

<hr/>

<p>{anchor:top_2}</p>
<h3>Google 发布 DiffusionGemma——26B MoE 扩散语言模型开源，H100 单卡推理速度突破 1000 tokens/s，向自回归范式发起正面挑战</h3>
<ul>
  <li><b>信号源</b>：<b>Google DeepMind</b> 官方（<a href="https://x.com/GoogleDeepMind/status/2064741061352636762">X 官方推文</a> · <a href="https://deepmind.google/blog/diffusiongemma-4x-faster-text-generation/">DeepMind 博客</a>）；<b>NVIDIA</b> 官方（<a href="https://blogs.nvidia.com/blog/rtx-ai-garage-local-gemma-diffusion/">NVIDIA Blog</a>）；<b>Sander Dieleman</b>（<a href="https://x.com/sedielem/status/2064754205634461710">X 评测</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">DiffusionGemma 把"文本扩散模型能否在速度与质量上挑战自回归"这一研究圈问题，第一次推进到有产业分量的阶段。<b>选择 Apache 2.0 开源是关键战略动作</b>：Google 把这套范式的基础实现公开，邀请整个生态共同验证和优化 text diffusion 路线，而非独自押注。扩散式生成把计算瓶颈从内存带宽转移到算力本身——算力充足而带宽受限的场景（高并发、单用户低延迟）将率先受益。官方明确该模型"优先速度而非质量"，与 Gemma 4 形成互补定位：短期更可能先在工具链与 Agent 编排场景落地，而非正面替代旗舰模型。</p>
</callout>
<p text-indent="1"><b>发布要点：</b><b>Google DeepMind</b> 于 6 月 10 日发布 <b>DiffusionGemma</b>——26B 参数 MoE 架构（激活约 3.8B）的扩散式语言模型，<b>Apache 2.0</b> 开源。单张 <b>NVIDIA H100</b> 上推理吞吐超 <b>1000 tokens/s</b>，官方称较标准自回归方式最高提速 <b>4 倍</b>。</p>
<p text-indent="1"><b>机制差异：</b>与自回归逐 token 生成不同，DiffusionGemma 先铺满 256 个随机占位 token，再经多轮并行去噪迭代精炼整块文本，过程中可对全局内容自我修正。</p>
<p text-indent="1"><b>路线脉络（related work）：</b>文本扩散并非 Google 心血来潮，这条路线近两年节点清晰：2025 年 2 月，中国人民大学高瓴人工智能学院等机构的 <b>LLaDA</b>（<a href="https://arxiv.org/abs/2502.09992">arXiv 2502.09992</a>，8B 从零训练）首次证明扩散语言模型能做到与 LLaMA3 8B 相当的性能，获 NeurIPS 2025 Oral——学术上验证了"路线可行"；同年，扩散模型共同发明人、Stanford 教授 <b>Stefano Ermon</b> 创立的 <b>Inception Labs</b> 推出首个商用级扩散语言模型 <b>Mercury</b>，宣称比速度优化后的自回归模型快至 <b>10 倍</b>——商业上验证了"客户愿意为速度买单"；Google 自己也在 2025 年 I/O 上以实验版 <b>Gemini Diffusion</b> 试水。DiffusionGemma 是这条路线第一次同时具备<b>大厂背书 + 开放权重 + 全生态 Day-0 支持</b>——竞赛从实验室阶段进入生态卡位阶段。</p>
<p text-indent="1"><b>生态接入：</b><b>NVIDIA</b> Day-0 提供 BF16/NVFP4 checkpoint 与 vLLM FP8 支持，覆盖 GeForce RTX 至 DGX 全产品线；Unsloth 同日完成 llama.cpp 适配支持本地 GGUF 推理。Google DeepMind 研究员 <b>Sander Dieleman</b> 实测验证本地推理可超 1000 tokens/s。</p>
<p text-indent="1"><em>* 注：速度数字来自 Google 与 NVIDIA 官方声明，具体测试条件（batch size、精度、序列长度）未完整披露。</em></p>

<hr/>

<p>{anchor:top_3}</p>
<h3>World Labs 开源 Spark 2.0——让 AI 生成的 3D 世界直接在浏览器里流畅运行，手机也能即点即进</h3>
<ul>
  <li><b>信号源</b>：<b>World Labs</b> 官方（<a href="https://x.com/theworldlabs/status/2064749936907075638">X 官方推文</a> · <a href="https://www.worldlabs.ai/blog/spark-2.0">官方博客</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">先解释一个名词：高斯泼溅（Gaussian Splatting）是用千万级带颜色的半透明"小光斑"拼出逼真 3D 场景的渲染技术，也是当前 AI 生成 3D 内容的主流表示方式。它过去的痛点是"重"——高保真场景要么离线渲染，要么依赖专用客户端，普通用户根本打不开。<b>Spark 2.0 解决的正是 AI 生成 3D 世界的"最后一公里"：分发。</b>李飞飞的 World Labs 把这个渲染器开源、并构建在 Web 上最流行的 3D 框架 Three.js 之上，意味着任何网页开发者都能把 AI 生成的 3D 世界嵌进自己的产品；用户无需安装任何软件，从手机到 VR 设备打开浏览器即可进入。<b>能生成世界的公司不少，能让世界被随处打开的公司目前只有这一家在认真做</b>——这是把"3D 内容的分发标准"攥在手里的平台打法。</p>
</callout>
<p text-indent="1"><b>发布要点：</b><b>Spark</b> 是 World Labs 开源的 3D 高斯泼溅网页渲染器（GitHub 3000+ star），2.0 版本三项核心升级：新的 .RAD 辐射场文件格式、层级细节系统（LOD，按观察距离自动调节精细度）、GPU 显存分页——三者结合使超大规模场景在手机硬件上也能流畅运行，官方称可向任意设备流式传输 <b>1 亿+ 高斯点</b>的 3D 世界。</p>
<p text-indent="1"><b>本次展示：</b>团队用 Spark 2.0 在浏览器中实时渲染 ICARE 项目的 7 个创意世界场景，并演示了 Blender 直连 Spark 实时运行环境——创作者在 Blender 中操控镜头、实时预览渲染结果，游戏世界与宣传视频共用同一套世界资产。</p>
<p text-indent="1"><b>产业含义：</b>高保真 3D 内容的交付门槛从"专用客户端"降到"标准浏览器"，制作与分发之间的工程摩擦被大幅压缩；对内容平台和创作工具生态而言，"制作即分发"的路径正在成型。</p>
<p text-indent="1"><em>* 注：1 亿+ 高斯点流式传输为官方宣称（World Labs 博客与 sparkjs.dev 文档），独立设备实测数据待见。</em></p>

<hr/>

<h1>🗺️ 今日导览</h1>
<p><a href="https://anchor.placeholder/section_资本动向"><b>💰 资本动向</b></a>　Warner Music 收购 Sureel AI——给 AI 生成音乐找到"该付钱给谁"的技术（<a href="https://anchor.placeholder/section_资本动向">↗</a>）</p>
<p><a href="https://anchor.placeholder/section_前沿技术"><b>🔬 前沿技术</b></a></p>
<grid>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_基础模型"><b>基础模型</b></a></p>
    <ul>
      <li>Anthropic Fable 5 新增使用限制，开发者信任争议升温（<a href="https://anchor.placeholder/card_1">↗</a>）</li>
      <li>xAI Grok Voice：类人语音 + 激进低价（<a href="https://anchor.placeholder/card_2">↗</a>）</li>
      <li>OpenAI × Visa：AI agent 获授权自主完成在线支付（<a href="https://anchor.placeholder/card_3">↗</a>）</li>
      <li>Agents' Last Exam：最强 agent 最难层级全通过率仅 2.6%（<a href="https://anchor.placeholder/card_4">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_世界模型"><b>世界模型</b></a></p>
    <ul>
      <li>QGF：test-time Q 值引导，无需重训优化机器人策略（<a href="https://anchor.placeholder/card_5">↗</a>）</li>
      <li>SARM2+SPIRAL：机器人自我提升，折叠任务 58%→100%（<a href="https://anchor.placeholder/card_6">↗</a>）</li>
      <li>OMG：diffusion 人形全身多模态控制，具备 scaling 规律（<a href="https://anchor.placeholder/card_7">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_AI_infra"><b>AI infra</b></a></p>
    <ul>
      <li>NVIDIA CPO 交换机：128K GPU 集群消除 65.5 万光模块（<a href="https://anchor.placeholder/card_8">↗</a>）</li>
      <li>OpenAI × NVIDIA 拟建 10GW 数据中心，20 年租约（<a href="https://anchor.placeholder/card_9">↗</a>）</li>
      <li>Meta × Reliance 签署印度首个 AI 数据中心协议（<a href="https://anchor.placeholder/card_10">↗</a>）</li>
      <li>OpenAI 模型接入 Oracle Cloud，企业用现有云配额直接调用（<a href="https://anchor.placeholder/card_11">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_ai4s"><b>AI4S</b></a></p>
    <ul>
      <li>EinsteinArena：多 agent 协作已产出 12 项数学新 SOTA（<a href="https://anchor.placeholder/card_12">↗</a>）</li>
    </ul>
  </column>
</grid>

<hr/>

<p>{anchor:section_资本动向}</p>
<h1>💰 资本动向</h1>
<ul>
  <li><b>Warner Music</b> 收购 <b>Sureel AI</b>（做"AI 音乐溯源"的初创公司——它的技术能识别一段 AI 生成的音乐里借鉴了哪些原创作品、用了谁的旋律或声音风格，从而确定<b>版权费应该付给谁</b>）：华纳以战略并购方式把这项溯源能力收入囊中。与此前唱片公司对 AI 公司提起诉讼的路径不同，此次选择"买入"而非"起诉"——版权方应对 AI 生成内容的策略正在多元化，溯源技术正从合规工具升级为版权方手中的战略资产。（<a href="https://x.com/TechCrunch/status/2064717317997822058">↗</a>）</li>
</ul>

<hr/>

<p>{anchor:section_前沿技术}</p>
<h1>🔬 前沿技术</h1>

<p>{anchor:section_基础模型}</p>
<h3>基础模型</h3>

<p>{anchor:card_1}</p>
<h4>Anthropic Claude Fable 5 发布后新增使用限制——开发者平台信任争议升温</h4>
<ul>
  <li><b>信号源</b>：<b>Anthropic</b>（<a href="https://www.latent.space/p/ainews-anthropic-claude-fable-5-mythos">Latent Space AINews</a>）· <b>Steven Sinofsky</b> 评论（<a href="https://x.com/stevesi/status/2064707194294050882">X 推文</a>）· <b>Perplexity</b> 集成（<a href="https://x.com/perplexity_ai/status/2064771411894567373">官方推文</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1"><b>争议核心是开发者对平台可预期性的基本诉求被打破</b>：付费后附加使用约束，影响的不只是当前用户，而是整个 API 生态对 Anthropic 长期可靠性的判断。Perplexity 仍快速集成说明模型能力吸引力不减，但条款不确定性将促使应用层开发者加速构建多模型 fallback 策略。</p>
</callout>
<p text-indent="1">昨日发布的 Claude Fable 5 出现后续争议：<b>Anthropic</b> 对新模型附加使用限制，前 <b>Microsoft</b> Windows 负责人 <b>Steven Sinofsky</b> 公开批评"付费开发工具发布后不应强制附加新约束，平台不能成为移动靶"。同日 <b>Perplexity</b> 将 Fable 5 集成为其 Computer 产品的 orchestrator（面向 Pro/Max 用户），头部模型的下游集成意愿依然强劲。</p>
<p text-indent="1"><em>* 注：使用限制具体条款来自媒体与社区讨论，非 Anthropic 官方正式披露文件。</em></p>

<p>{anchor:card_2}</p>
<h4>xAI 发布 Grok Voice——类人语音节奏与情感温度，延续激进低价策略冲击语音 AI 市场</h4>
<ul>
  <li><b>信号源</b>：<b>xAI</b> 官方（<a href="https://x.com/xai/status/2064777588036530309">官方推文</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">语音 AI 的竞争正从"能说话"转向"说得像人"，Grok Voice 选的三个维度（停顿节奏、语调、情感温度）正是 OpenAI Advanced Voice 与 ElevenLabs 的主战场。<b>低价不是口号而有产品线实绩：xAI 语音 Agent API 此前已按 $0.05/分钟平价计费、语音转文字约为竞品的两成到五成，语音平台 Vapi 已将 Grok 设为默认语音层</b>——低价正从获客手段变成生态卡位。同时 SuperGrok 订阅端 40 分钟语音上限引发的争议，显示低价扩张与商业化回收的平衡仍在摸索。</p>
</callout>
<p text-indent="1"><b>xAI</b> 于 6 月 10 日发布 <b>Grok Voice</b>，强调语音节奏、语调与情感温度三维度达到类人水准，宣称定价显著低于 OpenAI Advanced Voice Mode、Google Gemini Live、ElevenLabs 等竞品；本次发布未披露具体架构、延迟与价格数字。</p>
<p text-indent="1"><em>* 注：定价与生态背景（$0.05/分钟、Vapi 集成、40 分钟上限争议）来自 xAI 4-5 月语音产品线公开资料，作为对照背景，非本次发布披露内容。</em></p>

<p>{anchor:card_3}</p>
<h4>OpenAI × Visa 合作——AI agent 获授权自主完成在线支付交易</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI</b>（<a href="https://x.com/PolymarketMoney/status/2064771222957883554">Polymarket Money 推文转述</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1"><b>支付能力是 AI agent 从"建议者"升级为"执行者"的关键缺失环节。</b>与 Visa 的打通使 agent 可闭合"规划—执行—结算"的完整循环，将重塑电商、差旅、采购等场景的价值主张，同时引发授权边界、消费者保护与欺诈风险的新一轮讨论。</p>
</callout>
<p text-indent="1"><b>OpenAI</b> 与 <b>Visa</b> 达成合作，AI agent 可在用户授权范围内直接发起在线支付、自主完成购买交易，无需逐笔人工确认——这是主流支付网络与头部 AI 平台在 agentic 支付场景的首个公开合作。</p>
<p text-indent="1"><em>* 注：合作细节来自第三方转述报道，OpenAI 与 Visa 尚未发布联合官方声明。</em></p>

<p>{anchor:card_4}</p>
<h4>Agents' Last Exam：覆盖 55 个真实数字工作领域，最强 agent 最难层级全通过率仅 2.6%</h4>
<ul>
  <li><b>信号源</b>：Rohan Paul 转述 arXiv 论文（<a href="https://x.com/rohanpaul_ai/status/2064867621720535162">Rohan Paul @ X</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">这项评测把问题从"AI 能否在 benchmark 上得高分"转向"AI 能否完成人们赖以谋生的真实工作"。<b>2.6% 的全通过率与 agent 在各类合成 benchmark 上的亮眼成绩形成鲜明反差</b>——"通用职业 agent"距实用部署仍有巨大工程差距；该框架贴近真实工作场景，有望成为新的社区基准。</p>
</callout>
<p text-indent="1"><b>Agents' Last Exam</b> 覆盖工程、金融、医学、法律等 <b>55 个数字工作领域</b>的真实专家任务，要求 agent 在完整计算机环境中操作文件、浏览器、命令行与桌面软件，端到端交付成果并经自动化检查或严格评分。结果显示当前最强 agent 在最难层级的平均全通过率仅 <b>2.6%</b>。</p>
<p text-indent="1"><em>* 注：数据来自 Rohan Paul 对 arXiv 论文的转述，细节以论文原文为准。</em></p>

<hr/>

<p>{anchor:section_世界模型}</p>
<h3>世界模型</h3>

<p>{anchor:card_5}</p>
<h4>QGF：test-time Q 值梯度引导 flow policy，无需重训即实现 RL 策略优化</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.11087">Q-Guided Flow for Offline RL</a>（Zhiyuan Zhou · 一作；<b>Sergey Levine</b> · 合作，UC Berkeley）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">QGF 把 RL 策略改进完全推迟到推理阶段，绕过 actor-critic 联合训练的不稳定性。<b>核心洞察：flow matching 的 ODE 求解过程可以接受外部"力场"（Q 值梯度）引导，而无需更新策略参数</b>——与 test-time compute scaling 的大方向高度契合：训练一次，推理时按需"加力"。对机器人学习与离线 RL 的含义是：高质量行为克隆数据 + 轻量 critic 可能比复杂的联合训练更实用。</p>
</callout>
<p text-indent="1"><b>UC Berkeley</b> Sergey Levine 组提出 <b>QGF</b>：训练阶段用标准行为克隆训练 flow policy 与 value critic；推理阶段在 flow matching ODE 求解的每个积分步骤叠加与 Q 值梯度对齐的扰动项，引导动作采样向高回报区域偏移。在高维动作空间的离线 RL 基准上超过现有 test-time 方法、与 training-time SOTA 相当，计算开销显著更低，且随模型规模扩大表现出良好 scaling 特性。</p>

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
      <td vertical-align="top"><p>Zhiyuan Zhou（一作）</p></td>
      <td vertical-align="top"><p>UC Berkeley</p></td>
      <td vertical-align="top"><p><a href="https://github.com/shazhiju87">@shazhiju87</a></p></td>
      <td vertical-align="top"><p>zhiyuan_zhou@berkeley.edu · <a href="https://zhouzypaul.github.io/">主页</a></p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>Sergey Levine</b>（合作）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:card_6}</p>
<h4>SARM2 + SPIRAL：多任务 reward 模型驱动 VLA 机器人自我提升——Folding Shorts 成功率 58% → 100%</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.10305">SARM2: Stage-Aware Reward Modeling for Robot Manipulation</a>（Qianzhong Chen · 一作；<b>Pieter Abbeel</b> · 合作）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">高质量演示数据的稀缺是机器人学习扩展的核心瓶颈。SARM2+SPIRAL 的路径：用通用 dense reward 模型替代人工演示，让机器人从廉价自主 rollout 数据中自我迭代。<b>reward 估计误差降低 80% 直接转化为任务成功率大幅跃升，验证了 reward 质量（而非 policy 容量）才是当前瓶颈。</b></p>
</callout>
<p text-indent="1"><b>Pieter Abbeel</b> 团队提出 <b>SARM2</b>：action-primitive 阶段估计器将长时域任务分解为子阶段，MMoE（多门控混合专家）value head 提供跨任务 dense per-step rewards，无需逐任务人工标注；配套 <b>SPIRAL</b> 框架将奖励信号用于 on-policy rollout 形成数据飞轮。<b>10 任务</b>基准上 reward 估计 MSE 较最强 baseline 降低 <b>80%</b>；Folding Shorts 成功率 <b>58%→100%</b>，Cleaning Whiteboard <b>50%→90%</b>。</p>

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
      <td vertical-align="top"><p>Qianzhong Chen（一作）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>qchen23@stanford.edu · <a href="https://qianzhong-chen.github.io/">主页</a></p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>Pieter Abbeel</b>（合作）</p></td>
      <td vertical-align="top"><p>Professor at UCB · Berkeley College</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="http://www.cs.berkeley.edu/~pabbeel">主页</a></p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:card_7}</p>
<h4>OMG：diffusion 驱动人形机器人全身多模态控制框架——具备 scaling 规律，向 foundation model 迈进</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.10340">OMG: Omni-Modal Motion Generation for Humanoid Whole-Body Control</a>（Siqiao Huang · 共一；Kun-Ying Lee · 共一；<b>Hang Zhao</b> · 通讯）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">人形机器人控制的"模态孤岛"长期阻碍通用化：语言指令、音频节奏、参考动作各成体系。OMG 用大脑-小脑分层架构把多模态条件统一注入 diffusion 生成主干，<b>明确的 model scaling 规律是关键信号——该框架具备可预期的能力增长路径，是迈向人形机器人 foundation model 的具体证据。</b></p>
</callout>
<p text-indent="1"><b>Hang Zhao</b>（清华大学）通讯的 OMG 采用分层架构：上层 diffusion 运动生成模块接收语言、音频节奏、人体参考动作等多模态条件生成运动序列，下层 reactive tracking 控制器实时执行到物理关节。团队构建自动化数据 pipeline 合成大规模多模态配对数据；全身控制任务达 SOTA，展现明确 scaling 规律，部分数据与权重将开源。</p>

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
      <td vertical-align="top"><p>Siqiao Huang（共一）</p></td>
      <td vertical-align="top"><p>—；导师：Max Simchowitz</p></td>
      <td vertical-align="top"><p><a href="https://github.com/knightnemo">@knightnemo</a></p></td>
      <td vertical-align="top"><p><a href="https://knightnemo.github.io/">主页</a></p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p>Kun-Ying Lee（共一）</p></td>
      <td vertical-align="top"><p>Tsinghua；导师：Hang Zhao</p></td>
      <td vertical-align="top"><p><a href="https://github.com/KunYing-Lee">@KunYing-Lee</a></p></td>
      <td vertical-align="top"><p><a href="https://kunying-lee.github.io/">主页</a></p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>Hang Zhao</b>（通讯）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
  </tbody>
</table>

<hr/>

<p>{anchor:section_AI_infra}</p>
<h3>AI infra</h3>

<p>{anchor:card_8}</p>
<h4>NVIDIA 发布 Co-Packaged Optics 交换机——128K GPU 集群消除约 65.5 万独立光模块，大幅降低互联功耗</h4>
<ul>
  <li><b>信号源</b>：<b>NVIDIA</b> 官方博客（<a href="https://x.com/rohanpaul_ai/status/2064769648558756186">Rohan Paul 转述</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">GPU 集群迈向十万卡级，网络互联的功耗与可靠性瓶颈已不亚于算力本身。<b>CPO 把光通信组件封装进交换芯片旁，把故障点从数十万个量级压缩到接近零——这是数据中心网络架构的代际跃迁。</b>CPO 量产进度将成为超大集群能否按期建成的关键路径，光模块供应链格局随之重构。</p>
</callout>
<p text-indent="1"><b>NVIDIA</b> 发布 <b>Co-Packaged Optics（CPO）</b>交换机，将光通信模块与网络芯片封装整合，替代传统插拔式光模块——在 <b>128,000 GPU</b> 规模的数据中心中可消除约 <b>65.5 万个</b>独立光模块。近端封装降低信号损耗，让 GPU 不再因数据传输等待而空转，对 agentic inference 等延迟敏感场景尤为关键。</p>

<p>{anchor:card_9}</p>
<h4>OpenAI × NVIDIA 拟在俄亥俄州联邦土地建设 10GW AI 数据中心园区，20 年租约运营</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI / NVIDIA</b>（<a href="https://x.com/PolymarketMoney/status/2064709072390373718">Polymarket Money 转述</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1"><b>10GW 相当于一座中型核电站的总装机容量，将是全球最大 AI 算力聚集地之一。</b>NVIDIA 同时担任硬件供应方与财务担保方，等于把算力需求风险部分内化到自身资产负债表——有利于锁定长期需求并影响下一代硬件路线图节奏；联邦土地的使用也显示政府在 AI 算力基建中的角色趋于主动。</p>
</callout>
<p text-indent="1">据报道，<b>OpenAI</b> 正洽谈在俄亥俄州联邦土地上租赁拟建的 <b>10GW</b> AI 数据中心园区，<b>NVIDIA</b> 提供硬件与财务担保，OpenAI 以 <b>20 年</b>租约运营——这是目前已披露的最大单体 AI 算力基础设施项目之一。</p>
<p text-indent="1"><em>* 注：项目细节来自第三方转述，双方尚未发布官方确认声明。</em></p>

<p>{anchor:card_10}</p>
<h4>Meta × Reliance：签署印度首个 AI 数据中心合作协议，正式进入印度 AI 基础设施市场</h4>
<ul>
  <li><b>信号源</b>：<b>Meta / Reliance</b>（<a href="https://x.com/TechCrunch/status/2064605127248683510">TechCrunch</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">印度是全球最大的未充分渗透 AI 基础设施市场之一，<b>此次合作标志着美国大型科技公司将 AI 算力部署正式延伸至印度</b>；实体数据中心的本地化属性更符合印度政策偏好。Reliance 的零售、电信、媒体综合生态将为 Meta AI 服务提供独特的本地分发渠道。</p>
</callout>
<p text-indent="1"><b>Meta</b> 与印度最大综合企业 <b>Reliance</b> 签署首个 AI 数据中心合作协议，是 Meta 在印度落地 AI 算力的首次正式合作；具体规模与投资额未见官方披露。</p>

<p>{anchor:card_11}</p>
<h4>OpenAI 模型及 Codex 接入 Oracle Cloud——企业客户可用现有云配额直接调用</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI</b> 官方（<a href="https://openai.com/index/openai-on-oracle-cloud">OpenAI 官方博客</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">核心价值是"零额外签约摩擦"：企业无需单独与 OpenAI 签约，用已有 Oracle Cloud 承诺额度即可调用 OpenAI 模型与 Codex——大幅降低深度绑定 Oracle 的传统行业客户引入 AI 的决策成本。<b>OpenAI 的渠道策略正从直销走向依托云巨头分销网络</b>：继 Azure 之后，Oracle 成为又一企业级分发渠道，对 Anthropic（AWS Bedrock）与 Google 意味着企业采购入口的竞争被进一步封堵。</p>
</callout>
<p text-indent="1"><b>OpenAI</b> 宣布与 <b>Oracle Cloud Infrastructure（OCI）</b>集成：企业客户可通过已有的 Oracle Cloud 资源承诺配额直接访问 OpenAI 全系模型及 Codex，无需单独签署服务协议，并支持企业级安全与治理要求。Oracle 在金融、制造、医疗等传统行业的庞大存量客户，将成为 OpenAI 此前难以直接触达的增量用户群。</p>

<hr/>

<p>{anchor:section_ai4s}</p>
<h3>AI4S</h3>

<p>{anchor:card_12}</p>
<h4>EinsteinArena：多 agent 协作科研平台已产生 12 项数学新 SOTA，kissing number 11D 下界提升至 604</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.10402">EinsteinArena: A Platform for AI-Driven Open Scientific Discovery</a>（Federico Bianchi · 共一；Yongchan Kwon · 共一；<b>James Zou</b> · 资深合作，Stanford）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">最关键的机制不是单个 agent 的能力，而是"公开中间结果 + 验证器反馈"的协作闭环——失败尝试与成功思路对所有 agent 可见，集体智能得以涌现。<b>11 维 kissing number 突破（593→604）来自多轮迭代而非单次调用，说明 AI 协作科研在某类组合优化问题上已超越人类最优解。</b>启示：可验证性是该范式规模化的必要条件——缺乏可靠验证器的领域难以复制。</p>
</callout>
<p text-indent="1"><b>Stanford James Zou</b> 团队的 <b>EinsteinArena</b> 为每个开放数学问题配备自动验证器、公开排行榜与 agent 可读写的讨论论坛，多个独立 AI agent 自主提交解法、借鉴他人思路。截至 2026 年 5 月已产生 <b>12 项新 SOTA 数学结果</b>，其中 11 维接吻数下界从 <b>593 提升至 604</b>。</p>

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
      <td vertical-align="top"><p>Federico Bianchi（共一）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="https://github.com/federico-bianchi">@federico-bianchi</a></p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p>Yongchan Kwon（共一）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="https://github.com/ykwon0407">@ykwon0407</a></p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p><b>James Zou</b>（资深合作）</p></td>
      <td vertical-align="top"><p>Palo Alto University</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
  </tbody>
</table>

<hr/>
<p><em>本日报由 HH Research Pipeline 自动生成，由 Claude 抽取和撰写，以原文为准。</em></p>
<p><em>本日精选 16 条信号（Top 3 · 资本动向 1 条 · 赛道卡片 12 张）</em></p>
