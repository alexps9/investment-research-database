"""
Insight report service: generates three-part reports for each technology path.

MVP strategy: hardcoded reports based on domain knowledge of the 10 seed papers.
Phase B will replace with dynamic generation (TF-IDF + LLM).
"""

from datetime import datetime

from app.data.seed_papers import PATH_NAMES, PATH_TO_COMMUNITY
from app.models.reports import (
    AuthorInfo,
    BottleneckReport,
    InsightReport,
    InstitutionInfo,
    Milestone,
    TalentReport,
    TemporalReport,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_report(path: str) -> InsightReport:
    """
    Generate a three-part insight report for a technology path.

    Args:
        path: Path letter (A/B/C/D)

    Returns:
        InsightReport with temporal, talent, and bottleneck sections
    """
    if path not in _REPORTS:
        raise ValueError(
            f"Unknown path '{path}'. Valid paths: A, B, C, D"
        )

    return _REPORTS[path]()


def _report_a() -> InsightReport:
    """Path A: Attention Optimization"""
    return InsightReport(
        path="A",
        path_name=PATH_NAMES[str(PATH_TO_COMMUNITY["A"])],
        paper_count=3,
        temporal=TemporalReport(
            stage="成熟期",
            timeline_desc=(
                "Attention 优化从学术突破转向工业落地。"
                "FlashAttention-2 (2023) 解决了 IO 瓶颈，将 Attention 计算效率提升 2 倍；"
                "Ring Attention (2024) 突破单机内存限制，实现近乎无限长度上下文；"
                "DeepSeek-V3 (2024) 的 MLA 架构代表工业界最前沿，"
                "将 Attention 优化与 MoE 结合推向生产规模。"
            ),
            year_range="2023-2024",
            key_milestones=[
                Milestone(year=2023, paper_title="FlashAttention-2",
                         contribution="IO-aware exact attention, 2x speedup over FlashAttention"),
                Milestone(year=2024, paper_title="Ring Attention",
                         contribution="Blockwise attention across devices, near-infinite context"),
                Milestone(year=2024, paper_title="DeepSeek-V3",
                         contribution="Multi-head Latent Attention (MLA) at production scale"),
            ],
        ),
        talent=TalentReport(
            top_authors=[
                AuthorInfo(name="Tri Dao", paper_count=1, total_citations=140),
                AuthorInfo(name="Hao Liu", paper_count=1, total_citations=12),
            ],
            institutions=[
                InstitutionInfo(name="Princeton University", paper_count=1, category="academic"),
                InstitutionInfo(name="Together AI", paper_count=1, category="industry"),
                InstitutionInfo(name="UC Berkeley", paper_count=1, category="academic"),
                InstitutionInfo(name="DeepSeek", paper_count=1, category="industry"),
            ],
            summary=(
                "Attention 优化由学术界和工业界共同推动。"
                "Tri Dao (Princeton → Together AI) 是核心人物，FlashAttention 系列奠定了基础。"
                "DeepSeek 团队将优化推向工业规模，UC Berkeley 的 Hao Liu 解决了分布式长上下文问题。"
            ),
        ),
        bottleneck=BottleneckReport(
            current_bottleneck=(
                "超长上下文的内存墙：即使有 Ring Attention，"
                "百万 token 级别的推理仍面临通信开销和 KV Cache 膨胀问题。"
            ),
            existing_solutions=[
                "FlashAttention-2: IO-aware tiling 减少 HBM 访问",
                "Ring Attention: 跨设备 blockwise 计算突破单机限制",
                "MLA (DeepSeek-V3): 低秩压缩 KV Cache 减少内存占用",
            ],
            next_directions=[
                "硬件-算法协同设计（定制 Attention 加速器）",
                "稀疏 Attention 与 MoE 的深度融合",
                "KV Cache 压缩与量化的极限探索",
            ],
            summary=(
                "Attention 优化已从算法层面逼近理论极限，"
                "下一步突破可能需要硬件协同或架构范式转变。"
            ),
        ),
        generated_at=datetime.utcnow(),
    )


def _report_b() -> InsightReport:
    """Path B: State Space Models"""
    return InsightReport(
        path="B",
        path_name=PATH_NAMES[str(PATH_TO_COMMUNITY["B"])],
        paper_count=3,
        temporal=TemporalReport(
            stage="成长期",
            timeline_desc=(
                "SSM 从理论突破快速进入混合架构阶段。"
                "Mamba (2023) 证明选择性状态空间可以匹敌 Transformer；"
                "Jamba (2024) 首次在大规模模型中混合 Transformer 和 Mamba；"
                "Griffin (2024) 由 Google DeepMind 提出门控线性循环 + 局部注意力的混合方案。"
                "趋势明确：纯 SSM 不够，混合架构是主流方向。"
            ),
            year_range="2023-2024",
            key_milestones=[
                Milestone(year=2023, paper_title="Mamba",
                         contribution="Selective state spaces with linear scaling, challenging Transformer"),
                Milestone(year=2024, paper_title="Jamba",
                         contribution="First production-scale Transformer-Mamba hybrid (52B params)"),
                Milestone(year=2024, paper_title="Griffin",
                         contribution="Gated linear recurrence + local attention hybrid"),
            ],
        ),
        talent=TalentReport(
            top_authors=[
                AuthorInfo(name="Albert Gu", paper_count=1, total_citations=980),
                AuthorInfo(name="Tri Dao", paper_count=1, total_citations=980),
            ],
            institutions=[
                InstitutionInfo(name="Carnegie Mellon University", paper_count=1, category="academic"),
                InstitutionInfo(name="AI21 Labs", paper_count=1, category="industry"),
                InstitutionInfo(name="Google DeepMind", paper_count=1, category="industry"),
            ],
            summary=(
                "Albert Gu (CMU) 是 SSM 领域的奠基人，Mamba 论文引用近千次。"
                "工业界快速跟进：AI21 Labs 推出 Jamba，Google DeepMind 推出 Griffin/RecurrentGemma。"
                "Tri Dao 同时活跃在 Attention 优化和 SSM 两条路径。"
            ),
        ),
        bottleneck=BottleneckReport(
            current_bottleneck=(
                "混合架构的最优配比尚未确定：Transformer 层和 SSM 层的比例、"
                "交替方式、以及在不同任务上的表现差异仍在探索中。"
            ),
            existing_solutions=[
                "Mamba: 选择性扫描机制实现输入依赖的状态转移",
                "Jamba: 1:7 的 Attention:Mamba 层比例 + MoE",
                "Griffin: 门控线性循环 + 局部滑动窗口注意力",
            ],
            next_directions=[
                "自适应混合比例（根据输入动态切换 Attention/SSM）",
                "SSM 在多模态任务中的扩展（Vision Mamba 等）",
                "硬件友好的 SSM 实现（利用 GPU tensor core）",
            ],
            summary=(
                "SSM 已证明可行性，但混合架构的设计空间巨大。"
                "下一步关键是找到 Attention 和 SSM 的最优组合方式。"
            ),
        ),
        generated_at=datetime.utcnow(),
    )


def _report_c() -> InsightReport:
    """Path C: Recurrent Revival"""
    return InsightReport(
        path="C",
        path_name=PATH_NAMES[str(PATH_TO_COMMUNITY["C"])],
        paper_count=3,
        temporal=TemporalReport(
            stage="萌芽期",
            timeline_desc=(
                "循环架构在 Transformer 主导的时代尝试复兴。"
                "xLSTM (2024) 由 LSTM 发明人 Hochreiter 亲自操刀，用指数门控重塑经典架构；"
                "RWKV-6/7 (2024) 将 RNN 线性化，兼顾训练并行性和推理效率；"
                "TTT Layers (2024) 提出激进方案：用测试时学习替代传统隐藏状态。"
                "三条路线各自独立，尚未形成统一范式。"
            ),
            year_range="2024",
            key_milestones=[
                Milestone(year=2024, paper_title="xLSTM",
                         contribution="Exponential gating + matrix memory for modernized LSTM"),
                Milestone(year=2024, paper_title="Eagle and Finch (RWKV-6/7)",
                         contribution="Matrix-valued states and dynamic recurrence for linear RNNs"),
                Milestone(year=2024, paper_title="TTT Layers",
                         contribution="Replace hidden state with a learning algorithm"),
            ],
        ),
        talent=TalentReport(
            top_authors=[
                AuthorInfo(name="Sepp Hochreiter", paper_count=1, total_citations=87),
                AuthorInfo(name="Bo Peng", paper_count=1, total_citations=10),
            ],
            institutions=[
                InstitutionInfo(name="JKU Linz / NXAI", paper_count=1, category="academic"),
                InstitutionInfo(name="RWKV Foundation", paper_count=1, category="industry"),
                InstitutionInfo(name="UC San Diego", paper_count=1, category="academic"),
            ],
            summary=(
                "循环复兴由学术界老将主导。Sepp Hochreiter (LSTM 发明人) 亲自下场，"
                "RWKV 社区以开源方式推进，TTT 来自 UC San Diego。"
                "与路径 A/B 的工业界主导形成鲜明对比。"
            ),
        ),
        bottleneck=BottleneckReport(
            current_bottleneck=(
                "循环架构在长距离依赖建模上仍弱于 Attention，"
                "且缺乏大规模训练验证（最大模型仅数十亿参数）。"
            ),
            existing_solutions=[
                "xLSTM: 指数门控扩大记忆容量",
                "RWKV: 线性化 RNN 实现训练并行",
                "TTT: 用梯度下降替代固定状态转移",
            ],
            next_directions=[
                "循环架构的百亿参数级验证",
                "与 Attention 的混合（类似路径 B 的策略）",
                "硬件优化的循环计算原语",
            ],
            summary=(
                "循环复兴仍处于早期探索阶段，各方案独立发展。"
                "能否在大规模上证明自己是关键挑战。"
            ),
        ),
        generated_at=datetime.utcnow(),
    )


def _report_d() -> InsightReport:
    """Path D: Mixture of Experts"""
    return InsightReport(
        path="D",
        path_name=PATH_NAMES[str(PATH_TO_COMMUNITY["D"])],
        paper_count=1,
        temporal=TemporalReport(
            stage="成长期",
            timeline_desc=(
                "MoE 从 Google 的研究项目演变为开源社区的主流 Scaling 策略。"
                "Mixtral (2024) 证明 8x7B 的稀疏专家架构可以匹敌 70B 稠密模型，"
                "以远低于稠密模型的推理成本实现同等性能。"
                "DeepSeek-V3 也采用了 MoE，说明这一策略已被工业界广泛接受。"
            ),
            year_range="2024",
            key_milestones=[
                Milestone(year=2024, paper_title="Mixtral of Experts",
                         contribution="Open-source MoE matching 70B dense model performance"),
            ],
        ),
        talent=TalentReport(
            top_authors=[
                AuthorInfo(name="Albert Q. Jiang", paper_count=1, total_citations=118),
                AuthorInfo(name="Alexandre Sablayrolles", paper_count=1, total_citations=118),
            ],
            institutions=[
                InstitutionInfo(name="Mistral AI", paper_count=1, category="industry"),
            ],
            summary=(
                "MoE 的开源推广主要由 Mistral AI 主导。"
                "作为欧洲 AI 创业公司的代表，Mistral 用 Mixtral 证明了"
                "小团队也能通过 MoE 策略训练出顶级模型。"
            ),
        ),
        bottleneck=BottleneckReport(
            current_bottleneck=(
                "MoE 的负载均衡和专家利用率仍是核心挑战。"
                "部分专家可能被过度使用而其他专家闲置，"
                "导致实际计算效率低于理论值。"
            ),
            existing_solutions=[
                "Mixtral: Top-2 路由 + 辅助负载均衡损失",
            ],
            next_directions=[
                "细粒度专家（更多更小的专家）",
                "MoE 与 SSM 的结合（如 Jamba 已初步尝试）",
                "动态专家数量（根据输入复杂度调整激活专家数）",
            ],
            summary=(
                "MoE 是当前最实用的 Scaling 策略，但专家路由和负载均衡"
                "仍有优化空间。与其他架构创新的结合是重要方向。"
            ),
        ),
        generated_at=datetime.utcnow(),
    )


# Dispatch table
_REPORTS = {
    "A": _report_a,
    "B": _report_b,
    "C": _report_c,
    "D": _report_d,
}
