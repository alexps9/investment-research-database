"""
Evolution Map data — merged from seed_papers.py + demo prototype.
PRD v2 four-layer ontology: Era → Lane → Row → Paper
"""

from typing import Optional

from app.models.evolution import (
    EvolutionPaper,
    IterationDef,
    IterationMutation,
    LaneDef,
    RowDef,
)

LANES = [
    LaneDef(id="context_scaling", title="Context Scaling", subtitle="序列复杂度 & 长上下文", color="#2563EB"),
    LaneDef(id="memory_wall", title="Memory Wall", subtitle="推理效率", color="#059669"),
    LaneDef(id="compute_scaling", title="Compute Scaling", subtitle="测试时计算", color="#EA580C"),
]

ROWS = [
    RowDef(id="linearization", lane="context_scaling", title="1-A Linearization", subtitle="O(n) Revolution"),
    RowDef(id="sparse", lane="context_scaling", title="1-B Sparse", subtitle="Attention Optimizers"),
    RowDef(id="memory_aug", lane="context_scaling", title="1-C Memory-Augmented", subtitle="Position & Memory"),
    RowDef(id="kv_compression", lane="memory_wall", title="2-A KV Compression", subtitle="GQA → MLA"),
    RowDef(id="kernel_opt", lane="memory_wall", title="2-B Kernel Opt.", subtitle="FlashAttn Series"),
    RowDef(id="paging", lane="memory_wall", title="2-B Paging", subtitle="vLLM / SGLang"),
    RowDef(id="speculative", lane="memory_wall", title="2-C Speculative", subtitle="Draft & Verify"),
    RowDef(id="moe", lane="compute_scaling", title="3-A MoE", subtitle="Parameter Scaling"),
    RowDef(id="reasoning", lane="compute_scaling", title="3-B Reasoning", subtitle="Test-time Compute"),
    RowDef(id="agent_rl", lane="compute_scaling", title="3-C Agent RL", subtitle="Action Era"),
]

PAPERS = [
    # === Row: linearization ===
    EvolutionPaper(id="rope", title="RoPE", year=2023, quarter=1, paradigm="attention_native", layer="memory", lane="context_scaling", row="linearization", path="trunk", size="lg"),
    EvolutionPaper(id="mamba", title="Mamba", year=2023, quarter=4, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="ssm", size="lg"),
    EvolutionPaper(id="mamba2", title="Mamba-2", year=2024, quarter=2, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="ssm", size="md", builds_on=["mamba"]),
    EvolutionPaper(id="mamba3", title="Mamba-3", year=2026, quarter=1, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="ssm", size="lg", builds_on=["mamba2"]),
    EvolutionPaper(id="rwkv4", title="RWKV-4", year=2023, quarter=2, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="linear_rnn", size="md"),
    EvolutionPaper(id="rwkv5", title="RWKV-5", year=2023, quarter=4, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="linear_rnn", size="md", builds_on=["rwkv4"]),
    EvolutionPaper(id="rwkv6", title="RWKV-6", year=2024, quarter=2, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="linear_rnn", size="md", builds_on=["rwkv5"]),
    EvolutionPaper(id="rwkv7", title="RWKV-7", year=2024, quarter=4, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="linear_rnn", size="lg", builds_on=["rwkv6"]),
    EvolutionPaper(id="retnet", title="RetNet", year=2023, quarter=3, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="linear_attn", size="md"),
    EvolutionPaper(id="gla", title="GLA", year=2023, quarter=4, paradigm="post_attention", layer="arch", lane="context_scaling", row="linearization", path="linear_attn", size="sm", builds_on=["retnet"]),
    # === Row: sparse ===
    EvolutionPaper(id="streaming", title="StreamingLLM", year=2023, quarter=3, paradigm="sparse_long", layer="arch", lane="context_scaling", row="sparse", path="trunk", size="lg"),
    EvolutionPaper(id="ringattn", title="Ring Attention", year=2023, quarter=4, paradigm="sparse_long", layer="sys", lane="context_scaling", row="sparse", path="sparse", size="md"),
    EvolutionPaper(id="infiniattn", title="Infini-Attention", year=2024, quarter=2, paradigm="sparse_long", layer="arch", lane="context_scaling", row="sparse", path="sparse", size="md", builds_on=["streaming"]),
    EvolutionPaper(id="longnet", title="LongNet", year=2023, quarter=3, paradigm="sparse_long", layer="sys", lane="context_scaling", row="sparse", path="extrapolation", size="sm"),
    # === Row: memory_aug ===
    EvolutionPaper(id="alibi", title="ALiBi", year=2023, quarter=2, paradigm="attention_native", layer="memory", lane="context_scaling", row="memory_aug", path="trunk", size="lg"),
    EvolutionPaper(id="yarn", title="YaRN", year=2023, quarter=3, paradigm="sparse_long", layer="memory", lane="context_scaling", row="memory_aug", path="trunk", size="md", builds_on=["alibi"]),
    EvolutionPaper(id="longrope", title="LongRoPE", year=2024, quarter=1, paradigm="sparse_long", layer="memory", lane="context_scaling", row="memory_aug", path="trunk", size="md", builds_on=["yarn"]),
    EvolutionPaper(id="hmt", title="HMT", year=2024, quarter=1, paradigm="sparse_long", layer="memory", lane="context_scaling", row="memory_aug", path="memory", size="sm"),
    EvolutionPaper(id="persistent_mem", title="Persistent Memory", year=2025, quarter=2, paradigm="sparse_long", layer="memory", lane="context_scaling", row="memory_aug", path="memory", size="lg", builds_on=["hmt"]),
    # === Row: kv_compression ===
    EvolutionPaper(id="flash2", title="FlashAttn-2", year=2023, quarter=3, paradigm="attention_native", layer="sys", lane="memory_wall", row="kv_compression", path="trunk", size="lg"),
    EvolutionPaper(id="gqa", title="GQA", year=2023, quarter=2, paradigm="attention_native", layer="memory", lane="memory_wall", row="kv_compression", path="kv_comp", size="md"),
    EvolutionPaper(id="mla", title="MLA (V2)", year=2024, quarter=2, paradigm="attention_native", layer="memory", lane="memory_wall", row="kv_compression", path="kv_comp", size="lg", builds_on=["gqa"]),
    EvolutionPaper(id="mla_v3", title="MLA (V3)", year=2024, quarter=4, paradigm="attention_native", layer="memory", lane="memory_wall", row="kv_compression", path="kv_comp", size="lg", builds_on=["mla"]),
    EvolutionPaper(id="transmla", title="TransMLA", year=2025, quarter=4, paradigm="attention_native", layer="memory", lane="memory_wall", row="kv_compression", path="kv_comp", size="lg", builds_on=["mla_v3"]),
    # === Row: kernel_opt ===
    EvolutionPaper(id="flash3", title="FlashAttn-3", year=2024, quarter=3, paradigm="attention_native", layer="sys", lane="memory_wall", row="kernel_opt", path="trunk", size="lg", builds_on=["flash2"]),
    EvolutionPaper(id="flash4", title="FlashAttn-4", year=2025, quarter=3, paradigm="attention_native", layer="sys", lane="memory_wall", row="kernel_opt", path="trunk", size="md", builds_on=["flash3"]),
    # === Row: paging ===
    EvolutionPaper(id="pagedattn", title="PagedAttention", year=2023, quarter=3, paradigm="attention_native", layer="sys", lane="memory_wall", row="paging", path="trunk", size="lg"),
    EvolutionPaper(id="sglang", title="SGLang", year=2023, quarter=4, paradigm="attention_native", layer="sys", lane="memory_wall", row="paging", path="paging", size="md", builds_on=["pagedattn"]),
    EvolutionPaper(id="vllm2", title="vLLM v2", year=2024, quarter=3, paradigm="attention_native", layer="sys", lane="memory_wall", row="paging", path="paging", size="md", builds_on=["pagedattn"]),
    # === Row: speculative ===
    EvolutionPaper(id="specdec", title="Speculative Decoding", year=2023, quarter=1, paradigm="conditional", layer="infer", lane="memory_wall", row="speculative", path="trunk", size="lg"),
    EvolutionPaper(id="medusa", title="Medusa", year=2024, quarter=1, paradigm="conditional", layer="infer", lane="memory_wall", row="speculative", path="speculative", size="md", builds_on=["specdec"]),
    EvolutionPaper(id="eagle", title="EAGLE", year=2024, quarter=2, paradigm="conditional", layer="infer", lane="memory_wall", row="speculative", path="speculative", size="md", builds_on=["specdec"]),
    EvolutionPaper(id="eagle2", title="EAGLE-2", year=2024, quarter=4, paradigm="conditional", layer="infer", lane="memory_wall", row="speculative", path="speculative", size="md", builds_on=["eagle"]),
    # === Row: moe ===
    EvolutionPaper(id="gshard", title="GShard", year=2023, quarter=1, paradigm="conditional", layer="arch", lane="compute_scaling", row="moe", path="moe", size="sm"),
    EvolutionPaper(id="mixtral", title="Mixtral", year=2024, quarter=1, paradigm="conditional", layer="arch", lane="compute_scaling", row="moe", path="trunk", size="lg", builds_on=["gshard"]),
    EvolutionPaper(id="dsmoe", title="DeepSeek-MoE", year=2024, quarter=1, paradigm="conditional", layer="arch", lane="compute_scaling", row="moe", path="moe", size="md", builds_on=["gshard"]),
    EvolutionPaper(id="dsv3_moe", title="DeepSeek-V3 MoE", year=2024, quarter=4, paradigm="conditional", layer="arch", lane="compute_scaling", row="moe", path="moe", size="lg", builds_on=["dsmoe"]),
    EvolutionPaper(id="qwen3", title="Qwen3 MoE", year=2025, quarter=2, paradigm="conditional", layer="arch", lane="compute_scaling", row="moe", path="moe", size="lg", builds_on=["dsv3_moe"]),
    # === Row: reasoning ===
    EvolutionPaper(id="cot", title="Chain-of-Thought", year=2023, quarter=1, paradigm="reasoning", layer="infer", lane="compute_scaling", row="reasoning", path="reasoning", size="md"),
    EvolutionPaper(id="tot", title="Tree-of-Thought", year=2023, quarter=3, paradigm="reasoning", layer="infer", lane="compute_scaling", row="reasoning", path="reasoning", size="sm", builds_on=["cot"]),
    EvolutionPaper(id="o1_preview", title="o1-preview", year=2024, quarter=3, paradigm="reasoning", layer="train", lane="compute_scaling", row="reasoning", path="reasoning", size="lg", builds_on=["tot"]),
    EvolutionPaper(id="r1", title="DeepSeek-R1", year=2025, quarter=1, paradigm="reasoning", layer="train", lane="compute_scaling", row="reasoning", path="trunk", size="lg", builds_on=["o1_preview"]),
    EvolutionPaper(id="s1", title="s1 (Small & Strong)", year=2025, quarter=4, paradigm="reasoning", layer="train", lane="compute_scaling", row="reasoning", path="reasoning", size="lg", builds_on=["r1"]),
    # === Row: agent_rl ===
    EvolutionPaper(id="agent_rl", title="Agent RL", year=2025, quarter=3, paradigm="reasoning", layer="train", lane="compute_scaling", row="agent_rl", path="trunk", size="lg"),
    EvolutionPaper(id="verifier", title="Verifier Scaling", year=2026, quarter=1, paradigm="reasoning", layer="train", lane="compute_scaling", row="agent_rl", path="verifier", size="lg", builds_on=["agent_rl"]),
]

ITERATIONS = [
    IterationDef(
        id="ssm",
        title="Mamba Evolution",
        subtitle="SSM → Selective State Space → Hardware-Aware Hybrid",
        path="ssm",
        row="linearization",
        papers=["mamba", "mamba2", "mamba3"],
        mutations={
            "mamba": IterationMutation(
                summary="首创选择性状态空间模型",
                detail="用 input-dependent selection mechanism 替代 S4 的固定 HiPPO 矩阵。",
                bottleneck="S4 的固定状态转移无法建模 content-based reasoning",
                result="语言建模 perplexity 持平 Transformer，推理速度 5× 提升",
            ),
            "mamba2": IterationMutation(
                summary="结构化状态空间对偶性（SSD）",
                detail="发现 selective SSM 与半可分矩阵的数学对偶关系，重构为矩阵乘法。",
                bottleneck="Mamba-1 的 sequential scan 无法利用 GPU 并行性",
                result="训练吞吐量提升 2-8×，模型质量持平或略优于 V1",
            ),
            "mamba3": IterationMutation(
                summary="硬件感知 + Attention 混合",
                detail="针对 H100/B200 重新设计 kernel，引入少量 Attention 层构成 hybrid 架构。",
                bottleneck="Pure SSM 在 in-context retrieval 上仍弱于 Attention",
                result="Retrieval-heavy benchmark 接近 Transformer，长序列推理保持 O(1)",
            ),
        },
    ),
    IterationDef(
        id="linear_rnn",
        title="RWKV Evolution",
        subtitle="RNN Revival — Token Shift → Data-Dependent State Transition",
        path="linear_rnn",
        row="linearization",
        papers=["rwkv4", "rwkv5", "rwkv6", "rwkv7"],
        mutations={
            "rwkv4": IterationMutation(
                summary="线性 RNN + Token Shift 机制",
                detail="用 time-mixing 和 channel-mixing 替代 self-attention。",
                bottleneck="传统 RNN 无法并行训练，梯度消失限制扩展性",
                result="首个可并行训练的 14B RNN 模型",
            ),
            "rwkv5": IterationMutation(
                summary="多头线性注意力（Eagle）",
                detail="引入 multi-head 机制，每个 head 有独立 decay 参数。",
                bottleneck="V4 单头结构表达力有限",
                result="短文本 benchmark 提升 5-8%，与 LLaMA-2 7B 可比",
            ),
            "rwkv6": IterationMutation(
                summary="Data-Dependent Decay（Finch）",
                detail="将固定 exponential decay 改为 input-dependent。",
                bottleneck="V5 的固定 decay 无法区分该记住和该遗忘的信息",
                result="Long-range retrieval 和 associative recall 大幅提升",
            ),
            "rwkv7": IterationMutation(
                summary="扩展状态维度 + 矩阵值状态",
                detail="将 state 从向量扩展为矩阵，状态容量增加一个数量级。",
                bottleneck="V6 状态容量受限于向量维度",
                result="In-context learning 接近 Transformer，保持 O(d²) 推理效率",
            ),
        },
    ),
]


def get_all_papers() -> list[EvolutionPaper]:
    return list(PAPERS)


def get_papers_by_lane(lane_id: str) -> list[EvolutionPaper]:
    return [p for p in PAPERS if p.lane == lane_id]


def get_papers_by_row(row_id: str) -> list[EvolutionPaper]:
    return [p for p in PAPERS if p.row == row_id]


def get_paper_by_id(paper_id: str) -> Optional[EvolutionPaper]:
    return next((p for p in PAPERS if p.id == paper_id), None)
