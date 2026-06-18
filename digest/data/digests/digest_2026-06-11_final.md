<title>HH Research Daily · 2026-06-11</title>

<h1>📌 Top 3 大新闻</h1>

<p>{anchor:top_1}</p>
<h3>Google 发布 DiffusionGemma——26B MoE 扩散语言模型开源，H100 单卡推理速度突破 1000 tokens/s</h3>
<ul>
  <li><b>信号源</b>：<b>Google DeepMind</b> 官方（<a href="https://deepmind.google/blog/diffusiongemma-4x-faster-text-generation/">DeepMind Blog</a> · <a href="https://x.com/GoogleDeepMind/status/2064741061352636762">官方推文</a> · <a href="https://blogs.nvidia.com/blog/rtx-ai-garage-local-gemma-diffusion/">NVIDIA Blog</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">DiffusionGemma 是自回归语言模型主导地位受到最直接挑战的一个具体信号。它将 diffusion 范式引入文本生成：放弃逐 token 左到右的串行预测，改为对 256 个 token 位置并行去噪，推理瓶颈从内存带宽（自回归的死穴）转移到算力利用率，从而在 H100 等算力密集硬件上释放出超 4× 的吞吐提升。<b>这一路线的核心价值不仅在于速度，而在于它天然支持"全局修订"——模型可以在去噪过程中回头修改已生成内容，这对需要全局一致性的任务（代码、数学推导、长文档）有结构性优势。</b>Apache 2.0 开源 + NVIDIA Day-0 推理基础设施支持（BF16/NVFP4/vLLM FP8）+ Unsloth GGUFs 快速跟进，意味着扩散式语言模型正式进入开源生态主流竞争。下游值得关注的变化：RAG 和 Agent 的 prompt 结构假设（单向上下文依赖）在 diffusion 框架下需要重新审视。</p>
</callout>
<p text-indent="1"><b>Google DeepMind</b> 于 2026 年 6 月 10 日正式发布 <b>DiffusionGemma</b>，模型规模为 <b>26B 参数 MoE 架构，激活参数仅 3.8B</b>，Apache 2.0 开源许可。核心机制是文本扩散（text diffusion）：每步并行对 <b>256 个 token 位置</b>进行去噪，而非逐 token 自回归预测。</p>
<p text-indent="1">在推理速度上，<b>NVIDIA H100</b> 单卡实测约 <b>1000–1100 tokens/s</b>，是同系列 Gemma 4 变体的数倍。<b>NVIDIA</b> 同步提供 BF16/NVFP4 checkpoint、GPU 加速端点及 vLLM FP8 支持；Unsloth 团队已完成 llama.cpp 本地适配，支持 Unsloth GGUFs。Google 明确定位该模型优先速度而非质量，与 Gemma 4 形成差异化互补。</p>
<p text-indent="1"><b>Sander Dieleman</b>（Google DeepMind）同步展示，text diffusion 通过 token 轴并行可在本地设备上绕过自回归的内存带宽瓶颈，实现超 1000 tokens/s 的本地推理吞吐。<b>Daniel Han</b>（Unsloth）则发布微调教程，展示 diffusion LLM 在 Sudoku 等需要全局一致性的推理任务上优于自回归 LLM。</p>

<hr/>

<p>{anchor:top_2}</p>
<h3>Anthropic 发布 Claude Fable 5 "Mythos"——新增争议性使用限制，Perplexity Computer 产品首日集成</h3>
<ul>
  <li><b>信号源</b>：<b>Anthropic</b>（<a href="https://www.latent.space/p/ainews-anthropic-claude-fable-5-mythos">AINews 报道</a> · <a href="https://x.com/perplexity_ai/status/2064771411894567373">Perplexity 官方推文</a> · <a href="https://x.com/stevesi/status/2064707194294050882">Steven Sinofsky 推文</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Claude Fable 5（Mythos 级）的发布本身是行业预期中的旗舰更新，但伴生的争议更值得关注：<b>Anthropic 在付费开发工具上线后单方面新增使用限制，触碰了开发者生态的核心信任底线——"平台稳定性"。</b>前 Windows 负责人 Steven Sinofsky 的批评精确指出了问题所在：购买通用开发工具的开发者，不应在付费后遭遇附加约束。这与 Anthropic 同步起草 AI 监管政策提案的时间节点高度重叠，反映出该公司在"主动推动监管"与"维护开发者生态"两个目标之间的结构性张力。Perplexity 将 Claude Fable 5 集成为 Computer 产品的 orchestrator，说明顶级模型的生态整合速度依然强劲，但使用条款的不确定性将持续影响依赖 Anthropic API 的应用层开发者的长期规划。</p>
</callout>
<p text-indent="1"><b>Anthropic</b> 发布新一代旗舰模型 <b>Claude Fable 5</b>（Mythos 级命名），定位高端推理与长任务执行。此次发布伴随争议性使用条款，引发开发者社区广泛讨论。</p>
<p text-indent="1"><b>Perplexity</b> 于发布首日将 Claude Fable 5 集成至其 Computer 产品作为 orchestrator 模型，仅对 Pro 和 Max 订阅用户开放，用于驱动长时、多步骤复杂任务。前 <b>Microsoft</b> Windows 负责人 <b>Steven Sinofsky</b> 公开批评 Anthropic 对 Claude Fable 5 与 Claude Mythos 5 新增使用限制的做法，称付费开发工具发布后不应强制附加新约束，"平台不能成为移动靶"。</p>
<p text-indent="1">与此同时，<b>Anthropic</b> 据报道正起草政策提案，建议政府对新 AI 模型进行监管。两个动作同步出现，折射出头部 AI 公司在商业扩张与合规收紧之间寻找平衡的内在矛盾。<b>Ethan Mollick</b>（Wharton）另外观察到 Claude 多 agent 长任务系统中会出现语言风格"漂移"现象，各 agent 相互强化形成类内部行话（"Claudish"），需显式要求普通英语输出。</p>
<p text-indent="1"><em>* 注：使用限制的具体条款细节来自媒体报道与社区讨论，非 Anthropic 官方正式披露文件。</em></p>

<hr/>

<p>{anchor:top_3}</p>
<h3>xAI 发布 Grok Voice——主打类人语音交互体验，以低价差异化切入语音 AI 赛道</h3>
<ul>
  <li><b>信号源</b>：<b>xAI</b> 官方（<a href="https://x.com/xai/status/2064777588036530309">官方推文</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">语音交互是 AI 产品化最直接的消费者入口之一，xAI 此次以"类人体验（timing、tone、warmth）+ 显著低价"双轴切入，是对 OpenAI Advanced Voice Mode 和 Google Gemini Live 的正面竞争。<b>关键信号在于定价策略：xAI 明确声称价格远低于竞品，这将对语音 AI 市场的定价锚点产生向下压力。</b>如果 Grok Voice 的质量主张成立，低价路线将加速语音接口向应用层和硬件厂商的普及，但也会压缩独立语音 AI 服务商的生存空间。目前信号主要来自官方发布声明，体验质量与实际定价细节有待独立验证。</p>
</callout>
<p text-indent="1"><b>xAI</b> 于 2026 年 6 月 10 日正式发布 <b>Grok Voice</b>，官方宣传重点为三项语音体验维度：语音节奏（timing）、语调（tone）和情感温度（warmth），定位达到"类人"交互水准。</p>
<p text-indent="1">在商业策略上，xAI 明确宣称 Grok Voice 价格远低于竞品，同时打出质量与价格两张牌，试图在语音 AI 赛道建立差异化定位。此次发布属于 xAI 在 Grok 产品线上的功能扩展，是其与 OpenAI、Google 在语音交互入口上竞争的最新动作。</p>
<p text-indent="1"><em>* 注：定价细节与具体价格数字来自 xAI 官方声明，独立对比评测尚未见报。</em></p>

<hr/>

<h1>🗺️ 今日导览</h1>
<p><a href="https://anchor.placeholder/section_资本动向"><b>💰 资本动向</b></a>　Warner Music 收购 AI 内容归因初创 Sureel AI，版权方从"起诉"转向"买入"（<a href="https://anchor.placeholder/section_资本动向">↗</a>）</p>
<p><a href="https://anchor.placeholder/section_前沿技术"><b>🔬 前沿技术</b></a></p>
<grid>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_基础模型"><b>基础模型</b></a></p>
    <ul>
      <li>OpenAI × Visa：AI agent 获授权自主完成在线支付（<a href="https://anchor.placeholder/card_2">↗</a>）</li>
      <li>QGF：test-time Q 值引导 flow policy，无需重训即优化 RL 策略（<a href="https://anchor.placeholder/card_3">↗</a>）</li>
      <li>DLA 动态线性注意力，16 数据集超越现有 SOTA（<a href="https://anchor.placeholder/card_4">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_世界模型"><b>世界模型</b></a></p>
    <ul>
      <li>World Labs Spark 2.0 浏览器实时流渲染数百万 Gaussian splats（<a href="https://anchor.placeholder/card_5">↗</a>）</li>
      <li>SARM2+SPIRAL：VLA 机器人无需 demo 即可自我提升，10 任务 MSE 降低 80%（<a href="https://anchor.placeholder/card_6">↗</a>）</li>
      <li>OMG：diffusion 驱动人形机器人全身多模态控制，具备 scaling 规律（<a href="https://anchor.placeholder/card_7">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_AI_infra"><b>AI infra</b></a></p>
    <ul>
      <li>NVIDIA CPO 交换机：128K GPU 集群消除 65.5 万独立光模块（<a href="https://anchor.placeholder/card_8">↗</a>）</li>
      <li>OpenAI × NVIDIA 拟建 10GW 联邦土地数据中心园区（<a href="https://anchor.placeholder/card_9">↗</a>）</li>
      <li>Meta × Reliance：首个印度 AI 数据中心合作协议落地（<a href="https://anchor.placeholder/card_10">↗</a>）</li>
    </ul>
  </column>
  <column width-ratio="0.25">
    <p><a href="https://anchor.placeholder/section_ai4s"><b>AI4S</b></a></p>
    <ul>
      <li>EinsteinArena：多 agent 协作已产生 12 项数学新 SOTA，kissing number 提升至 604（<a href="https://anchor.placeholder/card_11">↗</a>）</li>
      <li>OpenAI 披露 PRC 关联影响力操作利用 AI 干预美国政策讨论（<a href="https://anchor.placeholder/card_12">↗</a>）</li>
    </ul>
  </column>
</grid>

<p>{anchor:section_资本动向}</p>
<h1>💰 资本动向</h1>
<ul>
  <li><b>Warner Music</b> 收购 <b>Sureel AI</b>（AI 内容归因初创公司）：以战略并购方式布局音乐内容的 AI 归因技术，旨在解决 AI 生成内容中创作者版权归属问题。传统音乐版权方通过收购技术公司主动介入 AI 内容生态治理——与此前唱片公司对 AI 公司提起诉讼的路径不同，此次选择"买入"而非"起诉"，反映出版权方应对 AI 内容归因问题的策略正在多元化；对内容产业链而言，归因技术正从合规工具升级为版权方的战略资产。（<a href="https://x.com/TechCrunch/status/2064717317997822058">↗</a>）</li>
</ul>

<hr/>

<p>{anchor:section_前沿技术}</p>
<h1>🔬 前沿技术</h1>

<p>{anchor:section_基础模型}</p>
<h3>基础模型</h3>

<p>{anchor:card_2}</p>
<h4>OpenAI × Visa 合作——AI agent 获授权自主完成在线支付交易</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI</b>（<a href="https://x.com/PolymarketMoney/status/2064771222957883554">Polymarket Money 推文转述</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1"><b>支付能力是 AI agent 从"建议者"升级为"执行者"的关键缺失环节之一。</b>OpenAI 与 Visa 的合作标志着 agentic AI 在商业闭环上迈出实质性一步——agent 可以自主完成购买而非仅提供建议。这一能力的解锁将重塑 AI agent 在电商、差旅、采购等场景的价值主张，同时也引发关于授权边界、消费者保护和欺诈风险的新一轮讨论。</p>
</callout>
<p text-indent="1"><b>OpenAI</b> 与支付网络巨头 <b>Visa</b> 达成合作，赋予 AI agent 直接发起在线支付的能力，使其可在任务执行过程中自主完成购买交易，而无需每次返回用户确认。</p>
<p text-indent="1">这是 agentic AI 工具化进程中的重要节点：agent 与支付基础设施的直连，将"自主执行"从信息处理层延伸至经济行为层，对下游 agent 框架的权限管理与审计机制提出新要求。</p>
<p text-indent="1"><em>* 注：合作细节来自第三方转述报道，OpenAI 与 Visa 尚未发布联合官方声明。</em></p>

<p>{anchor:card_3}</p>
<h4>QGF：test-time Q 值梯度引导 flow policy，无需重训即实现 RL 策略优化</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.11087">Q-Guided Flow for Offline RL</a>（Zhiyuan Zhou · 一作；<b>Sergey Levine</b> · 合作，UC Berkeley）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">QGF 将 RL 策略改进的计算完全推迟到推理阶段，绕过 actor-critic 联合训练的不稳定性。<b>其核心洞察是：flow matching 的 ODE 求解过程可以接受外部"力场"（Q 值梯度）引导，而不需要对策略参数做任何更新。</b>这一范式与 test-time compute scaling 的大方向高度契合——训练一次，推理时按需"加力"。对机器人学习和离线 RL 社区的含义是：高质量 behavioral cloning 数据 + 轻量 critic 可能比复杂的 actor-critic 训练更实用。</p>
</callout>
<p text-indent="1"><b>UC Berkeley</b> Sergey Levine 组提出 <b>QGF（Q-Guided Flow）</b>，分两阶段：训练阶段用标准 behavioral cloning（行为克隆）训练 flow policy 和 value function critic；test time 阶段，在 flow matching ODE 求解的每个积分步骤中叠加与 Q 值梯度对齐的扰动项，引导采样动作向高回报区域偏移，不对 policy 参数做任何更新。</p>
<p text-indent="1">在高维动作空间的单任务和 goal-conditioned 离线强化学习（offline RL）基准上，QGF 超过现有 test-time RL 方法，并与 training-time SOTA 算法竞争力相当，但计算开销显著更低。随模型规模增大表现出良好 scaling 特性。</p>

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

<p>{anchor:card_4}</p>
<h4>DLA 动态线性注意力——自适应状态合并，16 数据集三类任务超越 SOTA</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.10650">Dynamic Linear Attention</a>（<b>Xin Wang</b> · 共一；Hui Shen · 共一）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Linear attention 长期面临"精度-效率"二难：固定合并策略无法区分重要与次要 token，导致长序列下关键信息被不可逆覆盖。<b>DLA 的贡献是把"合并边界"从静态变为数据驱动，使模型能在语义跳变处保留细节、在平稳区间激进压缩，将 linear attention 的长上下文实用性推向新台阶。</b>固定 cache 容量设计也让内存增长可控，有利于超长序列推理场景的工程部署。</p>
</callout>
<p text-indent="1">现有 multi-state linear attention 使用固定合并策略，无法识别关键 token，导致长序列下信息不可逆丢失。DLA（Dynamic Linear Attention）引入两个核心模块：<b>Information-Aware Dynamic State Merging</b>（依据 token 级信息变化量自适应划分状态边界，语义跳变处保留高分辨率、平稳区间激进压缩）和 <b>Capacity-Bounded Memory Modeling</b>（固定 cache 大小，选择性合并低信息相邻状态控制内存增长）。</p>
<p text-indent="1">在 <b>16 个数据集、三类任务</b>上预训练评测，DLA 优于现有 SOTA multi-state linear attention 方法，验证了动态合并策略相比固定策略在长上下文建模中的有效性。</p>

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
      <td vertical-align="top"><p><b>Xin Wang</b>（共一）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="https://eric-xw.github.io">主页</a></p></td>
    </tr>
    <tr>
      <td vertical-align="top"><p>Hui Shen（共一）</p></td>
      <td vertical-align="top"><p>—</p></td>
      <td vertical-align="top"><p><a href="https://github.com/killthefullmoon">@killthefullmoon</a></p></td>
      <td vertical-align="top"><p>—</p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:section_世界模型}</p>
<h3>世界模型</h3>

<p>{anchor:card_5}</p>
<h4>World Labs Spark 2.0 × Three.js——浏览器实时流式渲染数百万 Gaussian splats，创意 3D 工作流打通</h4>
<ul>
  <li><b>信号源</b>：<b>World Labs</b> 官方（<a href="https://x.com/theworldlabs/status/2064749936907075638">推文</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">Gaussian splatting 的浏览器端实时流渲染是 3D 内容交付的重要节点：过去高保真 3D 场景只能离线渲染或依赖重量级本地客户端，Spark 2.0 与 Three.js 的结合将其搬进标准 Web 环境。<b>对创意工作流的影响是：团队可直接在浏览器中迭代、协作和发布沉浸式场景，"制作即分发"的路径缩短。</b>结合 Blender 直连 Spark 2.0 runtime 的演示（游戏世界与宣传片共用同一套世界模型），World Labs 正在推进"单一世界模型驱动多种输出形态"的平台逻辑。</p>
</callout>
<p text-indent="1"><b>World Labs</b> 展示 <b>Spark 2.0</b> 与 Three.js 结合，实现<b>数百万 Gaussian splats</b> 在浏览器端的实时流式渲染，应用于 ICARE 项目的 7 个创意世界场景。团队还展示将 Blender 直接接入 Spark 2.0 实时 runtime，在游戏世界中操控摄像机动画，无需单独搭建过场动画场景。</p>
<p text-indent="1">这一集成将高保真 3D 场景的交付门槛从专用客户端降至标准浏览器，创意团队可在同一套世界模型 runtime 上同时进行开发与发布，减少内容制作与分发之间的工程摩擦。</p>

<p>{anchor:card_6}</p>
<h4>SARM2 + SPIRAL：多任务 reward 模型驱动 VLA 机器人自我提升——Folding Shorts 成功率 58% → 100%</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.10305">SARM2: Stage-Aware Reward Modeling for Robot Manipulation</a>（Qianzhong Chen · 一作；<b>Pieter Abbeel</b> · 合作）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">高质量 demonstration 数据的稀缺是机器人学习扩展的核心瓶颈。SARM2+SPIRAL 的路径是：用通用 dense reward 模型替代人工演示，让机器人从廉价自主 rollout 数据中自我迭代。<b>MMoE 跨任务设计 + action-primitive 阶段化是关键——前者复用跨任务共性、后者提供精细的 per-step 奖励信号，两者结合才能形成稳定的数据飞轮。</b>MSE 降低 80% 的 reward 估计精度提升直接转化为任务成功率的大幅跃升，验证了 reward 质量是瓶颈而非 policy 容量。</p>
</callout>
<p text-indent="1"><b>Pieter Abbeel</b> 团队提出 <b>SARM2</b>（Stage-Aware Reward Model）：包含一个 action-primitive 阶段估计器（将长时域任务分解为子阶段）和一个 <b>MMoE（多门控混合专家）</b> value head，提供跨任务的 dense per-step rewards，无需逐任务人工标注。</p>
<p text-indent="1"><b>SPIRAL</b>（Self-Policy Improvement via Reward-Aligned Learning）框架将 SARM2 的奖励信号用于 on-policy rollout，形成数据飞轮。在 <b>10 任务</b>机器人操控基准上，reward 估计均方误差（MSE）较最强 baseline 降低 <b>80%</b>；Folding Shorts 任务成功率从 <b>58% 提升至 100%</b>，Cleaning Whiteboard 从 <b>50% 提升至 90%</b>。</p>

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
  <p text-indent="1">人形机器人控制的"模态孤岛"问题长期阻碍通用化：语言指令、音频节奏、参考动作视频各成体系。OMG 通过大脑-小脑分层架构将多模态条件统一注入 diffusion 生成主干，<b>明确的 model scaling 规律是关键信号——这意味着该框架具备可预期的能力增长路径，是迈向人形机器人 foundation model 的具体证据。</b>数据 pipeline 的标准化（MotionPair-60K 类似工程）与 scaling 能力结合，将决定下一阶段人形控制竞争的门槛。</p>
</callout>
<p text-indent="1"><b>Hang Zhao</b>（清华大学）通讯的 OMG 框架采用"大脑-小脑"分层架构：上层 diffusion-based 运动生成模块接收语言、音频节奏、人体参考动作等<b>多模态条件输入</b>，生成运动序列；下层 reactive motion tracking 控制器负责将运动序列实时执行到物理关节上。</p>
<p text-indent="1">团队构建了自动化数据整理与标注 pipeline，合成大规模高质量多模态配对训练数据。实验验证 OMG 在全身控制任务上达到 SOTA 性能，展现出明确的<b>模型 scaling 规律</b>，并能高效适应新模态与新分布，部分数据与权重将开源发布。</p>

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
      <td vertical-align="top"><p><a href="http://keg.cs.tsinghua.edu.cn/jietang/">—</a></p></td>
    </tr>
  </tbody>
</table>

<p>{anchor:section_AI_infra}</p>
<h3>AI infra</h3>

<p>{anchor:card_8}</p>
<h4>NVIDIA 发布 Co-Packaged Optics 交换机——128K GPU 集群消除约 65.5 万独立光模块，大幅降低互联功耗</h4>
<ul>
  <li><b>信号源</b>：<b>NVIDIA</b> 官方博客（<a href="https://x.com/rohanpaul_ai/status/2064769648558756186">Rohan Paul 转述</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">随着 GPU 集群规模向十万卡级别迈进，网络互联的功耗与可靠性瓶颈已不亚于算力本身。<b>CPO 将光通信组件封装在交换芯片旁边，消除了传统可插拔光模块的信号损耗和功耗开销，这是数据中心网络架构的一次代际跃迁——不只是省电，而是将故障点从数十万个量级压缩到接近零。</b>对 AI infra 生态的传导：CPO 量产进度将成为超大规模集群（>100K GPU）能否按预期建成的关键路径之一，光模块供应链格局随之重构。</p>
</callout>
<p text-indent="1"><b>NVIDIA</b> 发布 <b>Co-Packaged Optics（CPO）</b>交换机，将光通信模块与网络芯片封装整合，替代传统插拔式光模块。在 <b>128,000 GPU</b> 规模的数据中心中，可消除约 <b>65.5 万个</b>独立光模块，大幅降低 GPU 互联功耗并减少潜在故障点。</p>
<p text-indent="1">传统插拔式光模块每个都是独立故障源，在十万卡级集群中可靠性挑战极大；CPO 通过近端封装降低信号传输损耗，让 GPU 不再因数据传输等待而空转，对 agentic inference 等延迟敏感场景尤为关键。</p>

<p>{anchor:card_9}</p>
<h4>OpenAI × NVIDIA 拟在俄亥俄州联邦土地建设 10GW AI 数据中心园区，20 年租约运营</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI / NVIDIA</b>（<a href="https://x.com/PolymarketMoney/status/2064709072390373718">Polymarket Money 转述</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1"><b>10GW 相当于一座中型核电站的总装机容量，这一规模的数据中心园区将是全球最大 AI 算力聚集地之一。</b>NVIDIA 作为硬件供应方同时提供财务担保，说明此项目不只是简单的采购合同，而是 NVIDIA 将算力基础设施风险内化的战略选择，有利于锁定长期需求并影响下一代硬件路线图的规划节奏。联邦土地的使用也意味着政府在 AI 算力基础设施建设中扮演更主动的角色。</p>
</callout>
<p text-indent="1">据报道，<b>OpenAI</b> 正洽谈在俄亥俄州联邦土地上租赁一座拟建 <b>10GW</b> AI 数据中心园区，<b>NVIDIA</b> 提供硬件与财务担保，<b>OpenAI</b> 以 <b>20 年</b>租约运营。10GW 的总装机规模相当于一座中型核电站，是目前已披露的最大单体 AI 算力基础设施项目之一。</p>
<p text-indent="1">该项目体现了头部 AI 机构对算力基础设施的长周期重度布局，NVIDIA 兼任供应商与财务担保方的双重角色，将算力需求风险部分转移至自身资产负债表。</p>
<p text-indent="1"><em>* 注：项目细节来自第三方转述，双方尚未发布官方确认声明。</em></p>

<p>{anchor:card_10}</p>
<h4>Meta × Reliance：签署印度首个 AI 数据中心合作协议，正式进入印度 AI 基础设施市场</h4>
<ul>
  <li><b>信号源</b>：<b>Meta / Reliance</b>（<a href="https://x.com/TechCrunch/status/2064605127248683510">TechCrunch</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">印度是全球最大的未充分渗透 AI 基础设施市场之一，<b>Meta 与 Reliance 的合作标志着美国大型科技公司将 AI 算力部署正式延伸至印度</b>，与 Starlink 在印度遭遇监管阻力形成对比——实体数据中心合作的本地化属性更符合印度政策偏好。Reliance 的本地生态整合能力（零售、电信、媒体）将使 Meta 的 AI 服务在印度市场的分发具备独特的渠道优势。</p>
</callout>
<p text-indent="1"><b>Meta</b> 与印度最大综合企业 <b>Reliance</b> 签署首个 AI 数据中心合作协议，正式进入印度 AI 基础设施市场。这是 Meta 在印度落地 AI 算力部署的首次正式合作，也是大型科技公司将 AI 基础设施扩展至印度这一主要新兴市场的具体动作。</p>
<p text-indent="1">Reliance 的综合生态（JioMart 零售、Jio 电信、旗下媒体）为 Meta AI 服务在印度的渗透提供了多元渠道入口；合作的具体规模与投资额目前未见官方披露。</p>

<p>{anchor:section_ai4s}</p>
<h3>AI4S</h3>

<p>{anchor:card_11}</p>
<h4>EinsteinArena：多 agent 协作科研平台已产生 12 项数学新 SOTA，kissing number 11D 下界提升至 604</h4>
<ul>
  <li><b>论文</b>：<a href="https://arxiv.org/abs/2606.10402">EinsteinArena: A Platform for AI-Driven Open Scientific Discovery</a>（Federico Bianchi · 共一；Yongchan Kwon · 共一；<b>James Zou</b> · 资深合作，Stanford）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">EinsteinArena 最关键的机制不是单个 agent 的能力，而是"公开中间结果 + 验证器反馈"的协作闭环——失败尝试和成功思路对所有 agent 可见，使集体智能得以涌现。<b>11 维 kissing number 的突破（593→604）来自多轮迭代而非单次调用，说明 AI 协作科研范式在某类组合优化问题上已具备超越人类最优解的能力。</b>对 AI4S 生态的启示是：可验证性（verifier 的存在）是 agent 科研范式规模化的必要条件——没有可靠验证器的领域难以复制这一模式。</p>
</callout>
<p text-indent="1"><b>Stanford James Zou</b> 团队提出 <b>EinsteinArena</b>，为每个开放数学问题配备三要素：自动验证器（verifier）、公开排行榜（leaderboard）、agent 可读写的讨论论坛。多个独立 AI agent 自主提交解法、阅读他人讨论、借鉴已有思路，形成分布式协作循环。</p>
<p text-indent="1">截至 2026 年 5 月，平台已产生 <b>12 项新 SOTA 数学结果</b>，均超过此前所有人类与 AI 方案。其中，<b>11 维接吻数问题（kissing number）</b>下界从 <b>593 提升至 604</b>，突破来自多轮 agent 提交与公开讨论的协作迭代，验证了去中心化 AI 协作科研优于单 agent 孤立运行。</p>

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

<p>{anchor:card_12}</p>
<h4>OpenAI 披露 PRC 关联影响力操作——利用 AI 工具渗透美国 AI 政策辩论与数据中心叙事</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI</b> 官方（<a href="https://openai.com/index/prc-linked-influence-operations-ai-debates">OpenAI 报告</a>）</li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p text-indent="1">这份报告的意义在于揭示了一种新型信息战逻辑：<b>AI 技术既是渗透目标（政策讨论、数据中心叙事），也是渗透工具（内容生成与放大），形成双重威胁结构。</b>具体来看，操控 AI 政策辩论可影响监管走向，散布 ChatGPT 相关虚假信息可干扰公众认知与市场情绪。OpenAI 主动披露此类行动，一方面是履行透明度义务，另一方面也在塑造行业叙事——强化"AI 安全需要政府参与"的话语，与其正在推进的监管倡导工作形成呼应。</p>
</callout>
<p text-indent="1"><b>OpenAI</b> 发布专项报告，记录与中国（PRC）政府相关的影响力操作如何借助 AI 工具在美国舆论场中操纵讨论方向，涉及 AI 技术监管政策、数据中心建设叙事、贸易关税议题，以及 ChatGPT 相关虚假信息的传播。</p>
<p text-indent="1">报告记录的操作模式包括：利用 AI 生成和扩散内容干预特定政策讨论，并通过社交媒体渠道放大。这是 OpenAI 迄今在 AI 用于地缘信息战方面最系统性的公开披露，时间节点与美国国会关于 AI 监管立法讨论高度重叠。</p>

<hr/>
<p><em>本日报由 HH Research Pipeline 自动生成，由 Claude 抽取和撰写，以原文为准。</em></p>
<p><em>本日精选 15 条信号（Top 3 · 资本动向 1 条 · 赛道卡片 11 张）</em></p>