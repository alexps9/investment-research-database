<title>HH Research Daily · 2026-05-31</title>

<h2>今日 TL;DR</h2>
<ul>
  <li>【多模态智能】<b>Google</b> 将 <b>Gemini 3 Pro 图像模型与 Gemini 3.1 Flash 图像模型</b>正式推向生产可用（GA）状态，开发者可通过 Gemini API 直接调用。图像生成与理解能力正从预览进入大规模商业落地阶段。（<a href="https://anchor.placeholder/headline_1">↗</a>）</li>
  <li>【AI infra】<b>SoftBank</b> 承诺向法国投资 <b>€750 亿</b>，在 Hauts-de-France 建设目标 <b>5GW</b> 的欧洲最大 AI 算力综合体，首期 3.1GW 预计 2031 年完工。欧洲 AI 算力版图出现结构性新变量。（<a href="https://anchor.placeholder/headline_3">↗</a>）</li>
  <li>【AI infra】<b>Amazon</b> 推出 <b>弹性网络图（Resilient Network Graphs，RNG）</b>数据中心网络架构，以拟随机平坦图替代传统层级化胖树（fat-tree）拓扑，硬件需求降低 <b>69%</b>、吞吐量提升 <b>33%</b>，已成为 AWS 大多数工作负载的默认网络。数据中心互联层的架构路线出现新解法。（<a href="https://anchor.placeholder/headline_5">↗</a>）</li>
</ul>

<hr/>

<h2>内容导览</h2>
<table>
  <colgroup><col width="200"/><col/></colgroup>
  <thead>
    <tr>
      <th background-color="light-gray"><p><b>赛道</b></p></th>
      <th background-color="light-gray"><p><b>今日信号</b></p></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><p><b>一、前沿研究（0 篇论文）</b></p></td>
      <td><p>—</p></td>
    </tr>
    <tr>
      <td><p><b>二、行业应用（3 条头条 + 若干补充）</b></p></td>
      <td><p>—</p></td>
    </tr>
    <tr>
      <td><p><a href="https://anchor.placeholder/section_应用_基础模型">基础模型</a></p></td>
      <td><p>OpenAI Agentic OS 演示 · Wagner 多智能体会议室 · Liquid LFM2.5 本地工具调用</p></td>
    </tr>
    <tr>
      <td><p><a href="https://anchor.placeholder/section_应用_多模态智能">多模态智能</a></p></td>
      <td><p>Google Gemini 3 Pro 图像 GA · Meta AI 可穿戴扩张计划</p></td>
    </tr>
    <tr>
      <td><p><a href="https://anchor.placeholder/section_应用_AI_infra">AI infra</a></p></td>
      <td><p>Amazon RNG 网络架构 · SoftBank 法国 5GW 算力 · NVIDIA DynoSim 推理仿真</p></td>
    </tr>
    <tr>
      <td><p><a href="https://anchor.placeholder/section_应用_商业进展">商业进展</a></p></td>
      <td><p>SoftBank €750 亿投资法国数据中心 · GitHub Copilot 按 token 计费</p></td>
    </tr>
  </tbody>
</table>

<p><em>说明：空赛道（世界模型、ai4s）当日无满足条件信号，整行省略。</em></p>

<hr/>

<h2>头条</h2>

<p>{anchor:headline_1}</p>
<h3>Google Gemini 3 Pro 与 3.1 Flash 图像模型正式 GA，Gemini API 开放生产调用</h3>
<ul>
  <li><b>信号源</b>：<b>Google AI Developers</b>(官方账号)</li>
  <li><b>原文</b>：<a href="https://x.com/googleaidevs/status/2060685345738375640">Google AI Developers @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>图像生成与理解一直是多模态大模型的核心战场，各家都在争抢开发者在生产环境中的首选位置。<b>Google 这次把 gemini-3-pro-image 和 gemini-3.1-flash-image 同时推向 GA</b>，意味着开发者不再需要等预览配额，可以直接在产品里调用。两款模型一重一轻，覆盖高质量生成和低延迟快速响应两个场景——<b>这说明 Google 打的是"让开发者没有理由再去找替代方案"的平台策略</b>，而不是单点旗舰竞争。</p>
</callout>

<p>　　图像生成与理解模型从"可以用"到"可以放生产"之间，有一道隐形的门槛：SLA、限流、版本稳定性、计费可预期性。GA 状态意味着 Google 在这些维度给出了承诺，开发者可以基于此构建对外服务。</p>
<p>　　gemini-3-pro-image 定位高质量生成场景，gemini-3.1-flash-image 定位低延迟快速响应场景。两款同时 GA 的意图在于覆盖企业级产品中最常见的两种需求：一种是需要出图质量的内容生产流程，另一种是需要实时响应的交互式应用。对于已经在 Gemini API 生态里构建产品的开发者来说，迁移成本极低，粘性会在这一步显著上升。</p>

<hr/>

<p>{anchor:headline_3}</p>
<h3>SoftBank 承诺向法国投资 €750 亿，目标建设 5GW 欧洲最大 AI 算力综合体</h3>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b>（转述 Financial Times 报道）</li>
  <li><b>原文</b>：<a href="https://x.com/rohanpaul_ai/status/2060810476502786211">Rohan Paul @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>欧洲 AI 算力版图的判断里，一直缺少一个能和美国超大规模数据中心规模对齐的项目。<b>SoftBank 这次承诺的 €750 亿、5GW 目标体量</b>，如果真正落地，将成为欧洲迄今最大的单一 AI 算力基础设施承诺。法国的核电结构提供了相对稳定的电力成本基础，这是其他欧洲选址的核心差异。<b>融资路径是最大的不确定性</b>——行业估算每 1GW 约需 500 亿美元，意味着 SoftBank 需要大量项目债务和外部合作伙伴；承诺金额和实际动工节奏之间的落差，值得持续跟踪。</p>
</callout>

<p>　　全球 AI 算力基础设施的投资竞争正在进入新阶段：不再只是云厂商自建，主权基金和大型资本方开始以独立算力基础设施运营商的角色入场。SoftBank 此前在 ARM、Vision Fund 上的布局显示其愿意承受长周期资本锁定，法国项目延续了这一风格。</p>
<p>　　首期 3.1GW 预计 2031 年完工，时间跨度较长。Dunkirk 选址与法国核电网络的连接质量、项目债务结构和合作伙伴引入节奏，将是判断该项目能否从承诺走向实际建设的核心指标。对于关注欧洲算力供给侧的观察者，这是一个需要追踪落地进度而非只看承诺金额的信号。</p>

<p><em>* 注：上述数据来自 Financial Times 报道，SoftBank 官方尚未发布完整项目细节，融资安排和合作伙伴结构待进一步披露。</em></p>

<hr/>

<p>{anchor:headline_5}</p>
<h3>Amazon 推出弹性网络图架构，硬件需求降低 69%、吞吐量提升 33%，成为 AWS 默认网络</h3>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b>（转述 Amazon/AWS 研究）</li>
  <li><b>原文</b>：<a href="https://x.com/rohanpaul_ai/status/2060671309940396252">Rohan Paul @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>数据中心网络架构长期以胖树（fat-tree）拓扑为主流，这套方案在少数高流量链路上容易产生拥塞。<b>Amazon 的弹性网络图（RNG）用拟随机平坦图替代层级化拓扑，通过 Spraypoint 路由和 ShuffleBox 布线实现多路径负载分散</b>，把"高速公路固定匝道"变成"密布立交网格"。<b>硬件需求降低 69%、吞吐量提升 33% 的组合，如果在 AWS 大规模工作负载上持续验证，将对数据中心网络设备供应商的产品路线图形成直接压力</b>——AWS 的内部架构决策历来对行业有示范效应。</p>
</callout>

<p>　　传统胖树拓扑的核心问题是：流量在少数上行链路上汇聚，一旦出现热点就会产生严重拥塞。RNG 的思路是从根本上打破这种层级汇聚结构，让每个节点都通过准随机方式与多个对等节点直连，流量天然分散到大量并行路径上。</p>
<p>　　AWS 将 RNG 设为大多数工作负载的默认网络，意味着这不是实验性部署，而是已经通过了生产规模的验证。硬件需求大幅降低意味着同等网络能力所需的交换机和布线数量显著减少，这对数据中心建设成本和运营效率都有直接影响。传统网络设备厂商需要关注这类云厂商自研网络架构对标准化设备采购的替代效应。</p>

<hr/>

<h2>一、前沿研究</h2>

<p><em>本日 FRONTIER_RESEARCH_SIGNALS 为空，无前沿研究论文信号。</em></p>

<hr/>

<h2>二、行业应用</h2>

<p>{anchor:section_应用_基础模型}</p>
<h3>基础模型 (产品 / 集成 / Agentic 商业化)</h3>

<h4>OpenAI 演示语音优先移动端智能代理操作系统，代理可跨应用执行操作</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI Developers</b>（官方账号）</li>
  <li><b>原文</b>：<a href="https://x.com/OpenAIDevs/status/2060768896580452841">OpenAI Developers @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>手机操作系统层的 AI 代理化一直是行业里"说了很久但没人真正做出来"的方向。<b>OpenAI 这次演示的 Agentic OS 把语音作为主要交互层，代理不只是回答问题，而是能跨 app 实际执行操作</b>。这个演示的关键不在于语音本身，而在于"代理被允许在系统层操控应用"——<b>一旦这个权限模型被确立，手机 OS 厂商（Apple、Google）的代理集成深度就成了新的竞争轴</b>，而不只是模型能力的比拼。</p>
</callout>
<p>　　当前主流的手机 AI 助手（Siri、Google Assistant）本质上仍是问答系统，偶尔能触发少数预设动作。OpenAI 展示的形态是：以语音为核心输入，代理拥有跨应用执行权限，可以完成诸如"发邮件同时在日历里添加待办"这类需要跨应用协调的任务。</p>
<p>　　这个演示目前处于 demo 阶段，距离实际产品发布和系统级权限落地还有相当距离。但它划定了一条方向线：AI 代理的战场正在从应用层向系统层下移。对于正在构建移动端 AI 应用的开发者来说，需要开始关注系统级代理权限的开放程度，这将直接影响产品边界。</p>

<p><em>* 注：本次内容为 OpenAI Developers 官方账号发布的演示视频，属于概念演示阶段，暂无具体产品发布时间线披露。</em></p>

<h4>OpenAI 演示 Wagner 多智能体虚拟会议室，用于基础设施规划协作</h4>
<ul>
  <li><b>信号源</b>：<b>OpenAI Developers</b>（官方账号）</li>
  <li><b>原文</b>：<a href="https://x.com/OpenAIDevs/status/2060768795254550966">OpenAI Developers @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>Wagner 把多智能体协作具象化为"虚拟会议室"形态，让人类团队和 AI 代理在同一空间内对话协商基础设施规划。这是对"代理作为同事而非工具"这一产品叙事的具体示范——<b>多智能体协作的界面设计正在从命令行和 API 向拟人化会议室形态探索</b>，这个方向对 B 端协作工具市场的影响值得关注。</p>
</callout>
<p>OpenAI 展示了 Wagner 项目：一个多智能体虚拟会议室，人类团队可与房间内的 AI 代理协作讨论和规划基础设施方案。代理不只执行单一指令，而是在会议室情境中参与持续对话。这是 OpenAI Agentic OS 演示之外，另一个展示代理协作形态的具体案例。</p>

<h4>Liquid LFM2.5-8B 本地工具调用击败 gpt-oss-20b：7/7 完成 vs 3/7，速度 266 tok/s</h4>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b></li>
  <li><b>原文</b>：<a href="https://x.com/rohanpaul_ai/status/2060821501650387102">Rohan Paul @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>这次对比揭示了工具调用（tool calling）本质上是控制问题而非纯语言能力问题。<b>Liquid LFM2.5-8B-A1B 在 MacBook M5 Max 上完成全部 7/7 工具调用、速度 266 tok/s、RAM 仅 4.8GB，而 gpt-oss-20b 仅完成 3/7 并耗用 11GB RAM</b>——说明模型规模不是代理可靠性的决定因素，针对控制行为的训练才是关键。<b>对端侧代理产品路线来说，小模型+专项训练的路径竞争力正在上升</b>。</p>
</callout>
<p>Rohan Paul 分享的对比测试显示：Liquid 的专家混合（MoE）小模型 LFM2.5-8B-A1B 在 MacBook M5 Max 本地运行，完成了全部 7 个工具调用任务，速度 266 tok/s，RAM 占用仅 4.8GB。相比之下，参数量更大的 gpt-oss-20b 仅完成 3/7 调用，且耗用 11GB RAM。测试场景为本地 agent tool calling，关键在于模型能否跨上下文维护任务状态并正确判断执行时机。</p>

<h4>LLM + Lean 形式化验证以约 $300/题成本解决 9 个 Erdős 开放问题和 44 个 OEIS 猜想</h4>
<ul>
  <li><b>信号源</b>：<b>Carlos E. Perez</b>（IntuitMachine）</li>
  <li><b>原文</b>：<a href="https://x.com/IntuitMachine/status/2060832732557512857">Carlos E. Perez @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>核心思路是让 LLM 反复提议 Lean 形式化证明片段，由编译器逐步校验每一步，而非依赖 LLM 直接生成"听起来正确"的证明。<b>简单的"LLM 提案 + 编译器反馈"循环在成本效率上超越了更复杂的架构变体</b>，约 $300/题的成本解决了此前悬而未决的开放数学问题。这对形式化验证工具和数学自动化赛道有直接参考价值。</p>
</callout>
<p>研究者介绍了一个名为"Ralph loop"的方案：LLM 与 Lean 形式化验证系统结合，LLM 不断提议证明片段，Lean 编译器实时校验并反馈错误，循环迭代直至证明完成。以约 $300/题的成本，该方案成功解决了 9 个 Erdős 开放问题和 44 个 OEIS 数列猜想。实验发现，简单的 LLM+编译器反馈循环在成本效率上优于更复杂的架构。</p>

<p><em>* 注：该研究由 Carlos E. Perez 转述，具体论文来源和独立验证情况尚不明确，建议查阅原始研究出处。</em></p>

<hr/>

<p>{anchor:section_应用_多模态智能}</p>
<h3>多模态智能 (产品)</h3>

<h4>Google Gemini 3 Pro 图像模型与 Gemini 3.1 Flash 图像模型正式 GA</h4>
<ul>
  <li><b>信号源</b>：<b>Google AI Developers</b>（官方账号）</li>
  <li><b>原文</b>：<a href="https://x.com/googleaidevs/status/2060685345738375640">Google AI Developers @ X</a></li>
</ul>

<p><em>头条已涵盖本信号，详见上方头条卡片。</em></p>

<h4>Meta 计划 2026 年下半年销售 1000 万台可穿戴设备，含 AI pendant 与企业版眼镜</h4>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b>（转述 The Information）</li>
  <li><b>原文</b>：<a href="https://x.com/rohanpaul_ai/status/2060682478210166790">Rohan Paul @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>AI 交互界面的下一站是否在可穿戴形态，一直是行业里争议较大的判断。<b>Meta 这次给出了一个具体的押注：1000 万台销售目标、680 万月活、AI pendant 加上企业级 Wearables for Work</b>。Reality Labs Q1-26 亏损 40.3 亿美元的背景下，这个销售目标更像是"必须走通"的商业化验证，而不是探索性布局。<b>如果可穿戴硬件能带动 Hatch 订阅和 wearable apps 的持续收入，Meta 将拥有一个不依赖手机厂商分发渠道的 AI 平台入口</b>，这对平台竞争格局的影响值得关注。</p>
</callout>
<p>　　Meta 在 AI 可穿戴方向的布局有清晰的逻辑链：Ray-Ban 智能眼镜已经验证了一定的市场接受度，AI pendant 是对这条产品线的延伸，Wearables for Work 是将同一硬件形态推向 B 端的商业化尝试。三条产品线同时推进，说明 Meta 在测试不同的付费和分发路径。</p>
<p>　　Reality Labs 的持续亏损使得可穿戴部门需要在近期给出商业化数据支撑。1000 万台的销售目标放在 2026 年下半年这个时间窗口，对供应链和渠道的要求相当高。月活目标 680 万意味着硬件激活率需要维持在较高水平，这在可穿戴设备品类里历来是难点。</p>

<p><em>* 注：上述数据来自 The Information 报道（经 Rohan Paul 转述），为内部规划数字，未经 Meta 官方正式披露。</em></p>

<hr/>

<p>{anchor:section_应用_AI_infra}</p>
<h3>AI infra (基础设施产品)</h3>

<h4>Amazon 推出 RNG 数据中心网络架构，已成为 AWS 大多数工作负载默认网络</h4>
<ul>
  <li><b>信号源</b>：<b>Rohan Paul</b>（转述 Amazon/AWS 研究）</li>
  <li><b>原文</b>：<a href="https://x.com/rohanpaul_ai/status/2060671309940396252">Rohan Paul @ X</a></li>
</ul>

<p><em>头条已涵盖本信号，详见上方头条卡片。</em></p>

<h4>NVIDIA 推出 DynoSim：基于 Rust 的 LLM 推理服务工作负载仿真工具，仿真速度达实时 1500 倍</h4>
<ul>
  <li><b>信号源</b>：<b>NVIDIA AI</b>（官方账号）</li>
  <li><b>原文</b>：<a href="https://x.com/NVIDIAAI/status/2060781385686659416">NVIDIA AI @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>LLM 推理服务（inference serving）的部署调优长期依赖"逐一测试真实硬件"的方式，成本高且迭代慢。<b>DynoSim 将这个流程拆成"仿真筛选 + 真实验证"两阶段，全 Rust 实现使仿真速度比实时快 1500 倍</b>，大幅压缩推理栈的调优周期。对于管理大规模推理集群的团队来说，这类工具直接降低了探索部署配置空间的边际成本。</p>
</callout>
<p>NVIDIA 推出 DynoSim，定位为 LLM inference serving 工作负载仿真工具，基于 Rust 实现，可在真实硬件验证前快速筛选部署配置，仿真速度达实时的 1500 倍。该工具归属于 NVIDIA Dynamo 推理栈生态。其核心价值在于将"先仿真、再验证"的两阶段方法引入 LLM serving 调优，减少工程师在真实集群上反复试错的时间和资源消耗。</p>

<h4>Unsloth AI Dynamic Quants 将 Qwen 3.6 27B 部署至消费级 AMD GPU，推理速度 87 tok/s</h4>
<ul>
  <li><b>信号源</b>：<b>Daniel Han</b>（UnslothAI）</li>
  <li><b>原文</b>：<a href="https://x.com/danielhanchen/status/2060688959215444063">Daniel Han @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>动态量化（Dynamic Quants）技术让 27B 参数量模型在消费级 AMD GPU 上达到 87 tok/s 的实用推理速度，<b>这意味着大参数量开源模型的本地部署门槛正在持续下移</b>。对于不依赖云端 API、需要在本地或边缘环境运行大模型的开发者和企业，消费级硬件+量化工具的组合正在变得越来越可行。</p>
</callout>
<p>Daniel Han 演示了 UnslothAI 的 Dynamic Quants 技术：将 Qwen 3.6 27B 模型量化后部署在消费级 AMD GPU 上，推理速度达到 87 tokens/s。动态量化的核心思路是根据模型层的重要性差异，自适应地分配不同精度，在压缩模型体积的同时尽量保留关键层的精度。这一演示延续了 UnslothAI 在低资源高效推理方向的持续探索。</p>

<hr/>

<p>{anchor:section_应用_商业进展}</p>
<h3>商业进展 (IPO / 融资 / 收购 / 法务 / 高管)</h3>

<h4>SoftBank 承诺向法国投资最高 €750 亿建设 AI 数据中心，目标 5GW 欧洲最大算力设施</h4>
<ul>
  <li><b>信号源</b>：<b>TechCrunch</b>（媒体）· <b>Rohan Paul</b>（转述 Financial Times）</li>
  <li><b>原文</b>：<a href="https://x.com/TechCrunch/status/2060840494574526814">TechCrunch @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p><b>SoftBank €750 亿、5GW 的承诺</b>是迄今欧洲单一 AI 算力基础设施投资中金额最大的公开声明。法国核电网络提供了相对稳定的电力成本基础，这是选址的核心逻辑。<b>融资结构和合作伙伴引入节奏是关键变量</b>——按行业估算每 1GW 约需 500 亿美元，SoftBank 自身资产负债表难以独立承担，项目债务和战略合作伙伴的进展将决定从"承诺"到"动工"的实际节奏。</p>
</callout>
<p>SoftBank 宣布将在法国 Hauts-de-France 投资建设欧洲最大 AI 算力设施，投资承诺上限达 €750 亿，总目标容量 5GW，首期 3.1GW 预计 2031 年完工。选址核心在 Dunkirk，利用法国核电的廉价稳定电力。TechCrunch 和 Financial Times 均对此进行了报道。</p>

<h4>GitHub Copilot 推出基于 token 的计费方式，引发开发者社区强烈不满</h4>
<ul>
  <li><b>信号源</b>：<b>TechCrunch</b>（媒体）</li>
  <li><b>原文</b>：<a href="https://x.com/TechCrunch/status/2060761245909983594">TechCrunch @ X</a></li>
</ul>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>GitHub Copilot 将计费模式从订阅制改为按 token 用量计费，<b>开发者对费用可预测性和成本控制表达了强烈不满</b>。这次计费调整本质上是将推理成本的不确定性从 Microsoft/GitHub 侧转移到用户侧，对于重度使用者来说月度费用将变得不可预期。<b>这类计费模式的争议对 AI 编程助手赛道的其他竞争者来说是一个窗口</b>——用户对可预期订阅制的偏好可能推动向替代产品迁移。</p>
</callout>
<p>GitHub Copilot 宣布推出基于 token 的计费方式，将用量计费引入此前以固定月费为主的订阅体系。TechCrunch 报道显示，这一变化引发了开发者社区的强烈负面反馈，主要集中在费用不可预测性和高频使用场景下的成本控制担忧。</p>

<hr/>

<p><em>本日报由 HH Research Pipeline 自动生成，由 Claude 抽取和撰写，以原文为准。</em></p>
<p><em>处理信号 42 条 · 头条 3 条 · 行业应用高价值 7 条</em></p>
