

---
站在 robot learning 的视角去梳理的。简单分享一下 takeaways 和一些思考。
一、世界模型到底是什么？和视频生成有什么区别？
这篇文章的定义非常 robotics-centered：世界模型是预测 agent-environment dynamics 的模型，核心是预测“在当前 state 下，采取某个 action 之后，环境会怎么演变”。最关键的一个限定词是 action-conditioned —— 也就是说，你的预测必须对动作输入敏感。
按这个标准回头看，大部分号称世界模型的视频生成模型其实不合格。一个能生成丝滑视频的模型，如果它的输出主要由历史 context 和文本 prompt 决定，而不能 faithfully 反映“如果机械臂换一个方向去抓，场景会怎么变”，那它只是一个 video predictor，不是 world model。visually plausible ≠ action-consistent。生成得好看但不响应动作干预，对 embodied decision making 没有任何价值。
二、世界模型怎么和 policy 结合？
作者把现有的 world-model-based policy 分成了六个范式，从耦合最松到最紧：
1. IDM-style (解耦式)
最直觉的做法：让 video model 先“想象”未来会发生什么，再让另一个模型把想象的视频翻译成动作。代表作 UniPi、Vidar、VPP。优点是模块化、video 部分可以直接复用 Internet 上的海量人类视频做预训练。缺点是两个模块各练各的，video “想象”得再漂亮，机器人未必真的做得出来 —— 你想象自己优雅地把咖啡杯放到桌上，但手会不会抖、力道够不够，是想象不出来的。误差会沿着这种 gap 累积。
2. Single-backbone (单 backbone 统一式)
让一个模型同时生成视频和动作，不分先后。原理是：既然 video model 已经 pretrained 在海量时序数据上，它脑子里其实已经“懂”运动连续性和物理直觉了，那为什么要把动作生成单独拎出来？直接让动作和视频在同一个生成过程里出来，policy 就能白嫖这些先验。代价是又大又慢 —— 每次让机器人动一下，都要在心里过一遍完整的视频生成，实时性堪忧。
3. MoE/MoT-style (专家混合式)
折中方案：保留两个独立的“专家”（一个管视频、一个管动作），但让它们频繁开会。motivation 很务实：看视频和做动作其实是两种不同的任务 —— 视频是慢的、丰富的；动作是快的、精确的。强行让一个脑子同时 handle 这两件事，可能两边都做不好。分工 + 协作比大一统更稳。这一派现在工程上跑得最稳的几个 VLA 系统都是用的这条路。
4. Unified VLA (统一 VLA 式)
未来预测只在训练时用，部署时不用。和前面三类的关键区别在这里 —— 前面三类是“边想象边行动”，这一类是“小时候靠想象未来来学，长大了就不想象了”。模型训练时被要求同时预测动作和未来画面，逼它内化出 predictive structure；但真正部署时只输出动作，推理成本和普通 VLA 一样。对资源有限的团队来说，这可能是最实用的 paradigm。
5. Latent-space world modeling (潜空间世界建模)
完全不预测像素，只在抽象表征空间里做对齐。这其实是 LeCun 在 JEPA 论文里反复强调的路线，代表作 Nvidia 的 FLARE、VLA-JEPA、JEPA-VLA。底层的判断很有意思：机器人不需要知道未来每个像素长什么样，它只需要知道任务相关的关键变化。生成完整图像里绝大多数信息（背景、纹理、光照）对决策毫无帮助。这条路的训练成本比 video diffusion 低一个数量级，但效果不输。
6. Symbolic world model (符号化世界模型)
最异类的一派，完全不在视觉空间建模，而是在“物体、关系、动作”这些抽象符号层面建模。代表作 VisualPredicator、ExoPredicator。这一派要回答的问题是：长程任务真正的瓶颈到底在哪？你让机器人“做一杯咖啡”，难点不是预测下一帧画面长什么样，而是把任务分解成“找杯子 -> 放咖啡粉 -> 倒水 -> 搅拌”这样的步骤链。这种 compositional reasoning 在像素空间里几乎无解，但在符号空间里很自然。缺点是需要预先定义符号体系，grounding 比较脆弱。但和神经感知混合 (neuro-symbolic) 可能是长程任务的关键突破口之一。
在 LIBERO 这种 standard benchmark 上，这六类方法的 SOTA 其实差不多，都在 95%+。这说明对于 policy learning 来说，世界模型的 integration paradigm 没有定论，各种路径都 work。生成像素不是必须的，latent 或者 symbolic 的 predictive structure 也能产生类似的提升。这也反映出了世界控制的技术路线没有收敛，还在多条路线试错的阶段。
三、世界模型在具身智能中的应用：simulator 和 evaluator
文章另一个亮点是把 "world model as simulator" 这条线讲透了。除了和 policy 耦合，世界模型还有两个非常实用的角色：
- 强化学习环境： 真实 robot 做 RL 太贵太危险，用学到的世界模型当虚拟环境跑 RL。
- Policy evaluator： 在真实部署前，用世界模型 rollout 多个候选 action，用预测出的未来打分，选最好的。
这第二个用法本质上是把世界模型从“生成器”变成了“裁判”。Google 用 Veo 去给 Gemini Robotics 做 offline policy evaluation，WorldEval 研究“用世界模型 rollout 出的 policy ranking 能不能 replicate 真实 ranking”。如果这条路走通了，机器人 policy 的评测成本会下降一个数量级。
但作者也指出一个问题：evaluator 的有效性完全取决于 rollout 的可靠性。如果世界模型有幻觉，那评分本身就不可信。所以 Ctrl-World、WoVR 这些工作都在强调 action faithfulness —— 这又回到了第一点，判断一个 world model 好不好，不是看它生成得多真实，而是看它对 action 干预多敏感。
四、一些个人的思考
第一，要分清楚世界模型究竟在服务什么。
一类公司本质做的是视频生成，目标是把视频做得更真、更长、更有控制力，服务的下游是内容生产 —— 广告、影视、短视频。Pixverse、可灵、Sora、Veo 都是这一派。它们的产品评价标准很清楚：画面质量、prompt following、生成速度、可控编辑性。这一派的护城河是视觉效果 + 用户基数 + 工作流集成，和机器人没什么关系。
另一类公司做的是 embodied world model，目标是让机器人能在脑子里 rollout 未来、做 RL、做 policy evaluation，服务的下游是具身智能 —— 机械臂、人形、自动驾驶。极佳视界 (Giga AI)、世界实验室、Wayve 是这一派。它们的产品评价标准是论文里反复强调的那套：action faithfulness、long-horizon consistency、对 policy 的提升幅度、能不能 replace 真实环境跑 RL。
这两套体系几乎没有交集。一个能生成电影级画面视频模型，放到机器人上可能连“机械臂换个方向抓杯子”都响应不了；反过来，一个对 action 敏感的 world model，生成的画面可能远谈不上漂亮。它们的客户不同、scaling law 不同、技术栈不同、估值锚定也不同，只是因为都叫“世界模型”被强行归到一起。
极佳视界最近估值涨得快，我觉得核心稀缺性其实不在视频生成本身（论文里对 GigaWorld 的定位写得很 clear —— 它是 "data engine"，不是 "video benchmark winner"）。真正稀缺的是它同时押注了 video branch + 3D physically grounded branch，绑定的是具身智能数据合成这个赛道，而国内能讲清楚这个故事且有产品兑现的公司不多。在论文 Section 5.5 里，GigaWorld-0 被和 Cosmos Predict 2.5、Genie Envisioner 这些放在同一批讨论，定位是 "foundation layer for embodied data synthesis"。
第二，foundation video model 是不是必经之路？
这是更根本的问题。现在的主流共识默认是：做 embodied world model，就要先 scale 一个大视频生成模型，再 adapt 到机器人上。Cosmos、GigaWorld、Genie Envisioner 都是这条路。
但论文在结论里给了一句很微妙的话："whether video-pretrained backbones are consistently superior..."
to matched-scale VLM backbonesfor robotic control remains an openempirical question"。 翻译-下 就是 :video-pretrained 比VLM-pretrained更适合机器人控制,这个判断目前还没有被严格证明。
如果未来某个时点发 现 videobackbone并不真的比VLM backbone更适合机器人,那现在在foundation videomodel上烧的这些钱、卡、数据,有相当一部分会变成沉没成本。Lecun一直主张的latent prediction(JEPA)路线之所以不是主流,主要是因为它的叙事不够性感、demo不够impressive
我个人的判断是:foundation videomodel不会是唯一解,但短期内最好讲故事。video model有demo效果、有scalingstory、有内容生成的复用空间,这些都让它在融资和PR层面占绝对优势。但长期来看,latent prediction和neuro-symbolic这些路线有可能会反扑--尤其当机器人开始追求真正的long-horizon任务时
Who knows两年后回头看,现在被全市场追捧的foundation video model会不会变成"我们走了一段必要但昂贵的弯路
