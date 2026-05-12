"""
Seed papers for citation-graph MVP (Scheme B lane taxonomy).

See .claude/docs/specs/citation-graph-spec.md §2 for lane definitions.

Lane 1: 序列复杂度 & 长上下文 (sub-lanes 1A/1B/1C)
Lane 2: 推理效率 - KV Cache + 工程 (sub-lanes 2A/2B/2C)
Lane 3: 参数规模化 (MoE) (sub-lanes 3A/3B/3C)

Design notes:
- paper_id uses stable slugs so FE / spec / tests all reference the same key.
- arxiv_id may be None (e.g. RWKV-7, FlashAttn-4, o1); source_url is the
  fallback when that happens.
- cited_by_count_manual lets us ship a reasonable size for papers where
  OpenAlex lookup fails or is stale; enrichment flow overrides with live
  counts when available.
- Before-2023 papers carry is_pre_2023=True and render in the aggregation
  column left of the Q1-2023 gutter.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Lane = Literal[1, 2, 3]
SubLane = Literal["A", "B", "C"]
Tier = Literal[1, 2]
Alpha = Literal["high", "mid", "low"]
School = Literal[
    # 1-A
    "ssm", "rnn", "linattn", "hybrid",
    # 1-B
    "sparse-pattern", "streaming",
    # 1-C
    "rotary", "retrieval",
    # 2-A
    "head-sharing", "latent-compress",
    # 2-B
    "io-kernel", "memory-mgmt",
    # 2-C
    "draft-verify", "parallel-head",
    # 3-A
    "sparse-infra",
    # 3-B
    "token-to-expert", "expert-to-token",
    # 3-C
    "production",
]

LANE_NAMES: dict[int, str] = {
    1: "序列复杂度 & 长上下文",
    2: "推理效率（KV Cache + 工程）",
    3: "参数规模化（MoE）",
}

SUB_LANE_NAMES: dict[str, str] = {
    "1A": "线性化架构",
    "1B": "稀疏 & 长文本扩展",
    "1C": "位置编码 & 记忆",
    "2A": "KV Cache 结构优化",
    "2B": "推理算子工程",
    "2C": "解码策略",
    "3A": "MoE 基础设施",
    "3B": "路由与负载均衡",
    "3C": "工业集成",
}


class SeedPaper(BaseModel):
    """Hand-curated seed paper for the citation graph.

    Every non-deprecated paper must be placed in exactly one (lane, sub_lane)
    cell. Cross-lane relationships live in `tags` and are shown in the Side
    Panel Evolution module, not by duplicating the node.
    """

    paper_id: str = Field(..., description="Stable slug used as primary key")
    title: str
    authors: List[str] = Field(default_factory=list, description="First 3 authors")
    year: int
    quarter: Literal[1, 2, 3, 4] = Field(
        ..., description="Calendar quarter (pre-2023 papers use 1 as placeholder)"
    )
    is_pre_2023: bool = Field(default=False)

    lane: Lane
    sub_lane: SubLane
    school: Optional[School] = Field(None, description="Tech school within sub-lane, see docs/paper-taxonomy.md")
    tier: Tier = Field(..., description="1=source/landmark, 2=derivative")

    arxiv_id: Optional[str] = Field(None, description="arXiv ID, None for blog/tech-report only")
    openalex_id: Optional[str] = Field(None, description="OpenAlex Work ID if known")
    source_url: Optional[str] = Field(None, description="Fallback URL when arxiv_id is None")

    cited_by_count_manual: Optional[int] = Field(
        None, description="Fallback citation count when live enrichment unavailable"
    )
    alpha: Optional[Alpha] = Field(None, description="Research importance signal")
    tags: List[str] = Field(default_factory=list)
    note: Optional[str] = Field(None, description="Why this paper sits in this sub-lane")


def _sub_lane_key(paper: SeedPaper) -> str:
    return f"{paper.lane}{paper.sub_lane}"


# ---------------------------------------------------------------------------
# Lane 1 — 序列复杂度 & 长上下文
# ---------------------------------------------------------------------------
LANE_1_PAPERS: List[SeedPaper] = [
    # -- 1A 线性化架构 --------------------------------------------------------
    SeedPaper(
        paper_id="linear-transformer",
        title="Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention",
        authors=["Angelos Katharopoulos", "Apoorv Vyas", "Nikolaos Pappas"],
        year=2020, quarter=3, is_pre_2023=True,
        lane=1, sub_lane="A", school="linattn", tier=2,
        arxiv_id="2006.16236",
        tags=["linear", "pre-2023"],
        note="Seminal linear-attention reformulation",
    ),
    SeedPaper(
        paper_id="performer",
        title="Rethinking Attention with Performers",
        authors=["Krzysztof Choromanski", "Valerii Likhosherstov", "David Dohan"],
        year=2020, quarter=3, is_pre_2023=True,
        lane=1, sub_lane="A", school="linattn", tier=2,
        arxiv_id="2009.14794",
        tags=["linear", "random-features", "pre-2023"],
    ),
    SeedPaper(
        paper_id="hippo",
        title="HiPPO: Recurrent Memory with Optimal Polynomial Projections",
        authors=["Albert Gu", "Tri Dao", "Stefano Ermon"],
        year=2020, quarter=3, is_pre_2023=True,
        lane=1, sub_lane="A", school="ssm", tier=2,
        arxiv_id="2008.07669",
        tags=["ssm", "theory", "pre-2023"],
        note="Theoretical foundation for S4",
    ),
    SeedPaper(
        paper_id="s4",
        title="Efficiently Modeling Long Sequences with Structured State Spaces",
        authors=["Albert Gu", "Karan Goel", "Christopher Ré"],
        year=2021, quarter=4, is_pre_2023=True,
        lane=1, sub_lane="A", school="ssm", tier=1,
        arxiv_id="2111.00396",
        tags=["ssm", "pre-2023"],
        note="SSM paradigm founder",
    ),
    SeedPaper(
        paper_id="h3",
        title="Hungry Hungry Hippos: Towards Language Modeling with State Space Models",
        authors=["Daniel Y. Fu", "Tri Dao", "Khaled K. Saab"],
        year=2022, quarter=4, is_pre_2023=True,
        lane=1, sub_lane="A", school="ssm", tier=2,
        arxiv_id="2212.14052",
        tags=["ssm", "hybrid", "pre-2023"],
    ),
    SeedPaper(
        paper_id="hyena",
        title="Hyena Hierarchy: Towards Larger Convolutional Language Models",
        authors=["Michael Poli", "Stefano Massaroli", "Eric Nguyen"],
        year=2023, quarter=1,
        lane=1, sub_lane="A", school="ssm", tier=2,
        arxiv_id="2302.10866",
        tags=["ssm", "long-convolution"],
    ),
    SeedPaper(
        paper_id="rwkv-v4",
        title="RWKV: Reinventing RNNs for the Transformer Era",
        authors=["Bo Peng", "Eric Alcaide", "Quentin Anthony"],
        year=2023, quarter=2,
        lane=1, sub_lane="A", school="rnn", tier=1,
        arxiv_id="2305.13048",
        tags=["rnn", "linear"],
        alpha="mid",
        note="Open-source RNN revival flagship",
    ),
    SeedPaper(
        paper_id="retnet",
        title="Retentive Network: A Successor to Transformer for Large Language Models",
        authors=["Yutao Sun", "Li Dong", "Shaohan Huang"],
        year=2023, quarter=3,
        lane=1, sub_lane="A", school="rnn", tier=1,
        arxiv_id="2307.08621",
        tags=["linear", "microsoft"],
        alpha="mid",
    ),
    SeedPaper(
        paper_id="mamba",
        title="Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
        authors=["Albert Gu", "Tri Dao"],
        year=2023, quarter=4,
        lane=1, sub_lane="A", school="ssm", tier=1,
        arxiv_id="2312.00752",
        openalex_id="W4389326242",
        tags=["ssm", "selective"],
        alpha="high",
        note="Paradigm-level challenger to Attention",
    ),
    SeedPaper(
        paper_id="gla",
        title="Gated Linear Attention Transformers with Hardware-Efficient Training",
        authors=["Songlin Yang", "Bailin Wang", "Yikang Shen"],
        year=2023, quarter=4,
        lane=1, sub_lane="A", school="linattn", tier=2,
        arxiv_id="2312.06635",
        tags=["linear", "gated"],
    ),
    SeedPaper(
        paper_id="griffin",
        title="Griffin: Mixing Gated Linear Recurrences with Local Attention for Efficient Language Models",
        authors=["Soham De", "Samuel L. Smith", "Anushan Fernando"],
        year=2024, quarter=1,
        lane=1, sub_lane="A", school="hybrid", tier=2,
        arxiv_id="2402.19427",
        openalex_id="W6891815739",
        tags=["hybrid", "linear", "deepmind"],
    ),
    SeedPaper(
        paper_id="jamba",
        title="Jamba: A Hybrid Transformer-Mamba Language Model",
        authors=["Opher Lieber", "Barak Lenz", "Hofit Bata"],
        year=2024, quarter=1,
        lane=1, sub_lane="A", school="hybrid", tier=1,
        arxiv_id="2403.19887",
        openalex_id="W4393399080",
        tags=["ssm", "hybrid", "moe"],
        alpha="mid",
        note="Main innovation is Hybrid SSM; MoE is secondary",
    ),
    SeedPaper(
        paper_id="mamba-2",
        title="Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality",
        authors=["Tri Dao", "Albert Gu"],
        year=2024, quarter=2,
        lane=1, sub_lane="A", school="ssm", tier=1,
        arxiv_id="2405.21060",
        tags=["ssm", "ssd", "theory"],
        alpha="high",
        note="SSD unifies SSM and Attention theoretically",
    ),
    SeedPaper(
        paper_id="xlstm",
        title="xLSTM: Extended Long Short-Term Memory",
        authors=["Maximilian Beck", "Korbinian Pöppel", "Markus Spanring"],
        year=2024, quarter=2,
        lane=1, sub_lane="A", school="rnn", tier=2,
        arxiv_id="2405.04517",
        openalex_id="W4396815331",
        tags=["rnn", "linear"],
    ),
    SeedPaper(
        paper_id="deltanet",
        title="Parallelizing Linear Transformers with the Delta Rule over Sequence Length",
        authors=["Songlin Yang", "Bailin Wang", "Yu Zhang"],
        year=2024, quarter=2,
        lane=1, sub_lane="A", school="rnn", tier=2,
        arxiv_id="2406.06484",
        tags=["linear", "delta-rule"],
    ),
    SeedPaper(
        paper_id="rwkv-v7",
        title="RWKV-7 Goose",
        authors=["Bo Peng", "RWKV community"],
        year=2024, quarter=4,
        lane=1, sub_lane="A", school="rnn", tier=2,
        arxiv_id=None,
        source_url="https://github.com/BlinkDL/RWKV-LM",
        tags=["rnn", "linear", "non-arxiv"],
        note="No formal arXiv; GitHub / blog series only",
    ),

    # -- 1B 稀疏 & 长文本扩展 ------------------------------------------------
    SeedPaper(
        paper_id="longformer",
        title="Longformer: The Long-Document Transformer",
        authors=["Iz Beltagy", "Matthew E. Peters", "Arman Cohan"],
        year=2020, quarter=2, is_pre_2023=True,
        lane=1, sub_lane="B", school="sparse-pattern", tier=2,
        arxiv_id="2004.05150",
        tags=["sparse", "long-context", "pre-2023"],
    ),
    SeedPaper(
        paper_id="big-bird",
        title="Big Bird: Transformers for Longer Sequences",
        authors=["Manzil Zaheer", "Guru Guruganesh", "Avinava Dubey"],
        year=2020, quarter=3, is_pre_2023=True,
        lane=1, sub_lane="B", school="sparse-pattern", tier=2,
        arxiv_id="2007.14062",
        tags=["sparse", "long-context", "pre-2023"],
    ),
    SeedPaper(
        paper_id="streaming-llm",
        title="Efficient Streaming Language Models with Attention Sinks",
        authors=["Guangxuan Xiao", "Yuandong Tian", "Beidi Chen"],
        year=2023, quarter=3,
        lane=1, sub_lane="B", school="streaming", tier=2,
        arxiv_id="2309.17453",
        tags=["streaming", "long-context", "attention-sink"],
        alpha="mid",
    ),
    SeedPaper(
        paper_id="longnet",
        title="LongNet: Scaling Transformers to 1,000,000,000 Tokens",
        authors=["Jiayu Ding", "Shuming Ma", "Li Dong"],
        year=2023, quarter=3,
        lane=1, sub_lane="B", school="sparse-pattern", tier=2,
        arxiv_id="2307.02486",
        tags=["sparse", "long-context", "dilated"],
    ),
    SeedPaper(
        paper_id="ring-attention",
        title="Ring Attention with Blockwise Transformers for Near-Infinite Context",
        authors=["Hao Liu", "Matei Zaharia", "Pieter Abbeel"],
        year=2023, quarter=4,
        lane=1, sub_lane="B", school="streaming", tier=1,
        arxiv_id="2310.01889",
        openalex_id="W4387356039",
        tags=["distributed", "long-context"],
        alpha="mid",
    ),
    SeedPaper(
        paper_id="infini-attention",
        title="Leave No Context Behind: Efficient Infinite Context Transformers with Infini-attention",
        authors=["Tsendsuren Munkhdalai", "Manaal Faruqui", "Siddharth Gopal"],
        year=2024, quarter=2,
        lane=1, sub_lane="B", school="streaming", tier=1,
        arxiv_id="2404.07143",
        tags=["long-context", "memory"],
        alpha="high",
    ),

    # -- 1C 位置编码 & 记忆 ---------------------------------------------------
    SeedPaper(
        paper_id="rope",
        title="RoFormer: Enhanced Transformer with Rotary Position Embedding",
        authors=["Jianlin Su", "Yu Lu", "Shengfeng Pan"],
        year=2021, quarter=2, is_pre_2023=True,
        lane=1, sub_lane="C", school="rotary", tier=1,
        arxiv_id="2104.09864",
        tags=["rope", "position", "pre-2023"],
        alpha="high",
        note="De-facto standard for open-source LLMs",
    ),
    SeedPaper(
        paper_id="alibi",
        title="Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation",
        authors=["Ofir Press", "Noah A. Smith", "Mike Lewis"],
        year=2021, quarter=3, is_pre_2023=True,
        lane=1, sub_lane="C", school="rotary", tier=2,
        arxiv_id="2108.12409",
        tags=["position", "linear-bias", "pre-2023"],
    ),
    SeedPaper(
        paper_id="retro",
        title="Improving Language Models by Retrieving from Trillions of Tokens",
        authors=["Sebastian Borgeaud", "Arthur Mensch", "Jordan Hoffmann"],
        year=2021, quarter=4, is_pre_2023=True,
        lane=1, sub_lane="C", school="retrieval", tier=2,
        arxiv_id="2112.04426",
        tags=["retrieval", "memory", "deepmind", "pre-2023"],
    ),
    SeedPaper(
        paper_id="yarn",
        title="YaRN: Efficient Context Window Extension of Large Language Models",
        authors=["Bowen Peng", "Jeffrey Quesnelle", "Honglu Fan"],
        year=2023, quarter=3,
        lane=1, sub_lane="C", school="rotary", tier=2,
        arxiv_id="2309.00071",
        tags=["rope", "long-context", "extrapolation"],
    ),
    SeedPaper(
        paper_id="longrope",
        title="LongRoPE: Extending LLM Context Window Beyond 2 Million Tokens",
        authors=["Yiran Ding", "Li Lyna Zhang", "Chengruidong Zhang"],
        year=2024, quarter=1,
        lane=1, sub_lane="C", school="rotary", tier=2,
        arxiv_id="2402.13753",
        tags=["rope", "long-context", "microsoft"],
    ),
    SeedPaper(
        paper_id="hmt",
        title="HMT: Hierarchical Memory Transformer for Long Context Language Processing",
        authors=["Zifan He", "Zongyue Qin", "Neha Prakriya"],
        year=2024, quarter=1,
        lane=1, sub_lane="C", school="retrieval", tier=2,
        arxiv_id="2405.06067",
        tags=["memory", "hierarchical", "long-context"],
    ),
]


# ---------------------------------------------------------------------------
# Lane 2 — 推理效率（KV Cache + 工程）
# ---------------------------------------------------------------------------
LANE_2_PAPERS: List[SeedPaper] = [
    # -- 2A KV Cache 结构优化 -----------------------------------------------
    SeedPaper(
        paper_id="mqa",
        title="Fast Transformer Decoding: One Write-Head is All You Need",
        authors=["Noam Shazeer"],
        year=2019, quarter=4, is_pre_2023=True,
        lane=2, sub_lane="A", school="head-sharing", tier=2,
        arxiv_id="1911.02150",
        tags=["kv-cache", "pre-2023"],
        note="Multi-Query Attention origin",
    ),
    SeedPaper(
        paper_id="gqa",
        title="GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints",
        authors=["Joshua Ainslie", "James Lee-Thorp", "Michiel de Jong"],
        year=2023, quarter=2,
        lane=2, sub_lane="A", school="head-sharing", tier=1,
        arxiv_id="2305.13245",
        tags=["kv-cache"],
        alpha="high",
        note="Adopted by Llama-2/3; middle-ground between MHA and MQA",
    ),
    SeedPaper(
        paper_id="deepseek-v2",
        title="DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model",
        authors=["DeepSeek-AI"],
        year=2024, quarter=2,
        lane=2, sub_lane="A", school="latent-compress", tier=1,
        arxiv_id="2405.04434",
        tags=["kv-cache", "mla", "moe"],
        alpha="high",
        note="MLA first published here",
    ),
    SeedPaper(
        paper_id="deepseek-v3",
        title="DeepSeek-V3 Technical Report",
        authors=["DeepSeek-AI"],
        year=2024, quarter=4,
        lane=2, sub_lane="A", school="latent-compress", tier=1,
        arxiv_id="2412.19437",
        openalex_id="W4405903187",
        tags=["kv-cache", "mla", "moe"],
        alpha="high",
        note="MLA + fine-grained MoE at industrial scale",
    ),
    SeedPaper(
        paper_id="transmla",
        title="TransMLA: Multi-Head Latent Attention Is All You Need",
        authors=["Fanxu Meng", "Zengwei Yao", "Muhan Zhang"],
        year=2025, quarter=2,
        lane=2, sub_lane="A", school="latent-compress", tier=2,
        arxiv_id="2502.07864",
        tags=["mla", "migration"],
        note="Converts GQA checkpoints to MLA without retraining",
    ),

    # -- 2B 推理算子工程 ----------------------------------------------------
    SeedPaper(
        paper_id="flash-attn",
        title="FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        authors=["Tri Dao", "Daniel Y. Fu", "Stefano Ermon"],
        year=2022, quarter=2, is_pre_2023=True,
        lane=2, sub_lane="B", school="io-kernel", tier=1,
        arxiv_id="2205.14135",
        tags=["flash", "kernel", "pre-2023"],
        alpha="high",
        note="IO-aware kernel; baseline all later FAs build on",
    ),
    SeedPaper(
        paper_id="flash-attn-2",
        title="FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning",
        authors=["Tri Dao"],
        year=2023, quarter=3,
        lane=2, sub_lane="B", school="io-kernel", tier=2,
        arxiv_id="2307.08691",
        openalex_id="W4384648639",
        tags=["flash", "kernel"],
        alpha="mid",
    ),
    SeedPaper(
        paper_id="flash-attn-3",
        title="FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision",
        authors=["Jay Shah", "Ganesh Bikshandi", "Ying Zhang"],
        year=2024, quarter=3,
        lane=2, sub_lane="B", school="io-kernel", tier=1,
        arxiv_id="2407.08608",
        tags=["flash", "kernel", "hopper"],
        alpha="mid",
        note="H100 / WGMMA + FP8",
    ),
    SeedPaper(
        paper_id="flash-attn-4",
        title="FlashAttention-4 (talk / GitHub release)",
        authors=["Tri Dao"],
        year=2025, quarter=3,
        lane=2, sub_lane="B", school="io-kernel", tier=2,
        arxiv_id=None,
        source_url="https://github.com/Dao-AILab/flash-attention",
        tags=["flash", "kernel", "blackwell", "non-arxiv"],
        note="No formal paper yet; talk + code only",
    ),
    SeedPaper(
        paper_id="paged-attention",
        title="Efficient Memory Management for Large Language Model Serving with PagedAttention",
        authors=["Woosuk Kwon", "Zhuohan Li", "Siyuan Zhuang"],
        year=2023, quarter=3,
        lane=2, sub_lane="B", school="memory-mgmt", tier=1,
        arxiv_id="2309.06180",
        tags=["paged", "vllm", "serving"],
        alpha="high",
        note="vLLM origin paper; de-facto serving stack",
    ),
    SeedPaper(
        paper_id="sglang",
        title="SGLang: Efficient Execution of Structured Language Model Programs",
        authors=["Lianmin Zheng", "Liangsheng Yin", "Zhiqiang Xie"],
        year=2023, quarter=4,
        lane=2, sub_lane="B", school="memory-mgmt", tier=2,
        arxiv_id="2312.07104",
        tags=["serving", "radix-cache"],
        note="RadixAttention for prefix caching",
    ),

    # -- 2C 解码策略 --------------------------------------------------------
    SeedPaper(
        paper_id="speculative-decoding",
        title="Fast Inference from Transformers via Speculative Decoding",
        authors=["Yaniv Leviathan", "Matan Kalman", "Yossi Matias"],
        year=2023, quarter=1,
        lane=2, sub_lane="C", school="draft-verify", tier=1,
        arxiv_id="2211.17192",
        tags=["speculative"],
        alpha="high",
        note="Original Google formulation (v2 in 2023)",
    ),
    SeedPaper(
        paper_id="medusa",
        title="Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads",
        authors=["Tianle Cai", "Yuhong Li", "Zhengyang Geng"],
        year=2024, quarter=1,
        lane=2, sub_lane="C", school="parallel-head", tier=2,
        arxiv_id="2401.10774",
        tags=["speculative", "multi-head"],
    ),
    SeedPaper(
        paper_id="lookahead-decoding",
        title="Break the Sequential Dependency of LLM Inference Using Lookahead Decoding",
        authors=["Yichao Fu", "Peter Bailis", "Ion Stoica"],
        year=2024, quarter=2,
        lane=2, sub_lane="C", school="parallel-head", tier=2,
        arxiv_id="2402.02057",
        tags=["speculative", "parallel"],
    ),
    SeedPaper(
        paper_id="eagle",
        title="EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty",
        authors=["Yuhui Li", "Fangyun Wei", "Chao Zhang"],
        year=2024, quarter=1,
        lane=2, sub_lane="C", school="parallel-head", tier=2,
        arxiv_id="2401.15077",
        tags=["speculative"],
    ),
    SeedPaper(
        paper_id="eagle-2",
        title="EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees",
        authors=["Yuhui Li", "Fangyun Wei", "Chao Zhang"],
        year=2024, quarter=2,
        lane=2, sub_lane="C", school="parallel-head", tier=2,
        arxiv_id="2406.16858",
        tags=["speculative", "draft-tree"],
    ),
]


# ---------------------------------------------------------------------------
# Lane 3 — 参数规模化（MoE）
# ---------------------------------------------------------------------------
LANE_3_PAPERS: List[SeedPaper] = [
    # -- 3A MoE 基础设施 ----------------------------------------------------
    SeedPaper(
        paper_id="gshard",
        title="GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding",
        authors=["Dmitry Lepikhin", "HyoukJoong Lee", "Yuanzhong Xu"],
        year=2020, quarter=2, is_pre_2023=True,
        lane=3, sub_lane="A", school="sparse-infra", tier=2,
        arxiv_id="2006.16668",
        tags=["moe", "google", "pre-2023"],
    ),
    SeedPaper(
        paper_id="switch-transformer",
        title="Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity",
        authors=["William Fedus", "Barret Zoph", "Noam Shazeer"],
        year=2021, quarter=1, is_pre_2023=True,
        lane=3, sub_lane="A", school="sparse-infra", tier=1,
        arxiv_id="2101.03961",
        tags=["moe", "pre-2023"],
        alpha="high",
        note="Single-expert routing landmark",
    ),
    SeedPaper(
        paper_id="glam",
        title="GLaM: Efficient Scaling of Language Models with Mixture-of-Experts",
        authors=["Nan Du", "Yanping Huang", "Andrew M. Dai"],
        year=2021, quarter=4, is_pre_2023=True,
        lane=3, sub_lane="A", school="sparse-infra", tier=2,
        arxiv_id="2112.06905",
        tags=["moe", "google", "pre-2023"],
    ),
    SeedPaper(
        paper_id="megablocks",
        title="MegaBlocks: Efficient Sparse Training with Mixture-of-Experts",
        authors=["Trevor Gale", "Deepak Narayanan", "Cliff Young"],
        year=2022, quarter=4, is_pre_2023=True,
        lane=3, sub_lane="A", school="sparse-infra", tier=2,
        arxiv_id="2211.15841",
        tags=["moe", "kernel", "pre-2023"],
    ),
    SeedPaper(
        paper_id="st-moe",
        title="ST-MoE: Designing Stable and Transferable Sparse Expert Models",
        authors=["Barret Zoph", "Irwan Bello", "Sameer Kumar"],
        year=2022, quarter=2, is_pre_2023=True,
        lane=3, sub_lane="A", school="sparse-infra", tier=2,
        arxiv_id="2202.08906",
        tags=["moe", "stability", "pre-2023"],
    ),

    # -- 3B 路由与负载均衡 -------------------------------------------------
    SeedPaper(
        paper_id="expert-choice",
        title="Mixture-of-Experts with Expert Choice Routing",
        authors=["Yanqi Zhou", "Tao Lei", "Hanxiao Liu"],
        year=2022, quarter=2, is_pre_2023=True,
        lane=3, sub_lane="B", school="expert-to-token", tier=2,
        arxiv_id="2202.09368",
        tags=["moe", "routing", "pre-2023"],
        note="Expert picks tokens rather than tokens pick expert",
    ),
    SeedPaper(
        paper_id="deepseek-moe",
        title="DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models",
        authors=["Damai Dai", "Chengqi Deng", "Chenggang Zhao"],
        year=2024, quarter=1,
        lane=3, sub_lane="B", school="expert-to-token", tier=2,
        arxiv_id="2401.06066",
        tags=["moe", "routing", "fine-grained"],
        alpha="mid",
        note="Fine-grained + shared experts; basis of V2/V3",
    ),
    SeedPaper(
        paper_id="openmoe",
        title="OpenMoE: An Early Effort on Open Mixture-of-Experts Language Models",
        authors=["Fuzhao Xue", "Zian Zheng", "Yao Fu"],
        year=2024, quarter=1,
        lane=3, sub_lane="B", school="token-to-expert", tier=2,
        arxiv_id="2402.01739",
        tags=["moe", "open-source", "analysis"],
    ),

    # -- 3C 工业集成 --------------------------------------------------------
    SeedPaper(
        paper_id="mixtral-8x7b",
        title="Mixtral of Experts",
        authors=["Albert Q. Jiang", "Alexandre Sablayrolles", "Antoine Roux"],
        year=2024, quarter=1,
        lane=3, sub_lane="C", school="production", tier=1,
        arxiv_id="2401.04088",
        openalex_id="W4390723197",
        tags=["moe", "open-source", "mistral"],
        alpha="high",
        note="Commercial inflection for open MoE",
    ),
    SeedPaper(
        paper_id="qwen-moe",
        title="Qwen1.5-MoE: Matching 7B Model Performance with 1/3 Activated Parameters",
        authors=["Qwen Team"],
        year=2024, quarter=1,
        lane=3, sub_lane="C", school="production", tier=2,
        arxiv_id=None,
        source_url="https://qwenlm.github.io/blog/qwen-moe/",
        tags=["moe", "alibaba", "non-arxiv"],
    ),
    SeedPaper(
        paper_id="grok-1",
        title="Grok-1 (open-weights release)",
        authors=["xAI"],
        year=2024, quarter=1,
        lane=3, sub_lane="C", school="production", tier=2,
        arxiv_id=None,
        source_url="https://github.com/xai-org/grok-1",
        tags=["moe", "xai", "open-weights", "non-arxiv"],
    ),
    SeedPaper(
        paper_id="dbrx",
        title="Introducing DBRX: A New State-of-the-Art Open LLM",
        authors=["Databricks Mosaic team"],
        year=2024, quarter=1,
        lane=3, sub_lane="C", school="production", tier=2,
        arxiv_id=None,
        source_url="https://www.databricks.com/blog/introducing-dbrx-new-state-art-open-llm",
        tags=["moe", "databricks", "non-arxiv"],
        note="Fine-grained MoE; 132B total / 36B active",
    ),
]


# ---------------------------------------------------------------------------
# Aggregate & helpers
# ---------------------------------------------------------------------------
SEED_PAPERS: List[SeedPaper] = LANE_1_PAPERS + LANE_2_PAPERS + LANE_3_PAPERS


def get_all_seed_papers() -> List[SeedPaper]:
    return list(SEED_PAPERS)


def get_seed_by_lane(lane: int) -> List[SeedPaper]:
    return [p for p in SEED_PAPERS if p.lane == lane]


def get_seed_by_sub_lane(lane: int, sub_lane: str) -> List[SeedPaper]:
    return [p for p in SEED_PAPERS if p.lane == lane and p.sub_lane == sub_lane]


def get_seed_map() -> dict[str, SeedPaper]:
    return {p.paper_id: p for p in SEED_PAPERS}


def count_by_sub_lane() -> dict[str, int]:
    """Return {'1A': 8, '1B': 6, ...} for dashboard / coverage checks."""
    counts: dict[str, int] = {}
    for p in SEED_PAPERS:
        key = _sub_lane_key(p)
        counts[key] = counts.get(key, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Hand-curated citation edges (OpenAlex preprints often have empty references).
# Format: (source_paper_id, target_paper_id) = source builds on / cites target.
# ---------------------------------------------------------------------------
SEED_CITATIONS: list[tuple[str, str]] = [
    # Lane 1 internal chains
    ("s4", "hippo"),
    ("h3", "s4"),
    ("hyena", "s4"),
    ("mamba", "s4"),
    ("mamba", "h3"),
    ("mamba-2", "mamba"),
    ("jamba", "mamba"),
    ("jamba", "flash-attn"),          # cross-lane → Lane 2B
    ("griffin", "mamba"),
    ("rwkv-v4", "linear-transformer"),
    ("rwkv-v7", "rwkv-v4"),
    ("retnet", "linear-transformer"),
    ("gla", "linear-transformer"),
    ("deltanet", "gla"),
    ("xlstm", "mamba"),                # positioned as RNN revival vs SSM
    ("longnet", "longformer"),
    ("ring-attention", "flash-attn"),  # cross-lane → Lane 2B
    ("infini-attention", "streaming-llm"),
    ("yarn", "rope"),
    ("longrope", "rope"),
    ("longrope", "yarn"),
    ("hmt", "retro"),
    # Lane 2 internal chains
    ("gqa", "mqa"),
    ("deepseek-v2", "gqa"),
    ("deepseek-v3", "deepseek-v2"),
    ("deepseek-v3", "deepseek-moe"),   # cross-lane → Lane 3B
    ("transmla", "deepseek-v2"),
    ("flash-attn-2", "flash-attn"),
    ("flash-attn-3", "flash-attn-2"),
    ("flash-attn-4", "flash-attn-3"),
    ("paged-attention", "flash-attn"),
    ("sglang", "paged-attention"),
    ("medusa", "speculative-decoding"),
    ("lookahead-decoding", "speculative-decoding"),
    ("eagle", "speculative-decoding"),
    ("eagle-2", "eagle"),
    # Lane 3 internal chains
    ("switch-transformer", "gshard"),
    ("glam", "gshard"),
    ("st-moe", "switch-transformer"),
    ("expert-choice", "switch-transformer"),
    ("megablocks", "switch-transformer"),
    ("mixtral-8x7b", "switch-transformer"),
    ("deepseek-moe", "expert-choice"),
    ("deepseek-moe", "mixtral-8x7b"),
    ("qwen-moe", "mixtral-8x7b"),
    ("grok-1", "mixtral-8x7b"),
    ("dbrx", "mixtral-8x7b"),
    ("dbrx", "deepseek-moe"),
    ("openmoe", "mixtral-8x7b"),
]

