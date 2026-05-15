"""
Pydantic models for Evolution Map (PRD v2 four-layer ontology).

Era → Bottleneck/Lane → Row/Paradigm → Paper
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Paradigm = Literal[
    "attention_native",
    "post_attention",
    "sparse_long",
    "conditional",
    "reasoning",
    # World Model paradigms — RL-Based
    "rssm",
    "imagination_rl",
    "model_based_rl",
    "hierarchical_rl",
    "memory_augmented",
    "offline_model_based",
    "multi_agent_wm",
    "collaborative_wm",
    "generalization",
    "curriculum_learning",
    "tokenized_wm",
    "zero_shot",
    "non_stationary",
    "simulation",
    # World Model paradigms — Observation-Level Generative
    "pixel_gen",
    "llm_world_model",
    "causal_llm",
    "reasoning_planning",
    "text_simulator",
    "diffusion_video",
    "ar_video",
    "vlm",
    "efficient_video",
    "memory_augmented_video",
    "data_efficient_video",
    "interactive_video",
    "game_world_model",
    "long_video",
    "video_to_world",
    "latent_action",
    "text_to_3d",
    "text_to_4d",
    "perpetual_3d",
    "scene_generation",
    "image_to_3d",
    "lidar_4d",
    "depth_inpainting",
    # World Model paradigms — Latent Space
    "latent_dynamics",
    "joint_embedding",
    "joint_embedding_video",
    "jepa_planning",
    "sequential_jepa",
    "motion_content",
    "feature_world_model",
    "dino_video_wm",
    "dino_future_prediction",
    "group_structure",
    "long_context_wm",
    # World Model paradigms — Object-Centric
    "object_centric",
    "object_discovery",
    "object_dynamics",
    "language_object_wm",
    "exploration_object",
    "structured_object_wm",
    "generative_object",
    "interactive_object_rl",
    "object_rl_benefits",
    "object_policy",
    "object_latent_actions",
    "causal_object",
    "compositional_generalization",
    "object_centric_driving",
    "robot_object_wm",
    # World Model paradigms — Robotics
    "rl_planning",
    "robot_imagination",
    "video_to_action",
    "video_prediction_rl",
    "flow_motion_wm",
    "4d_embodied",
    "occupancy_4d",
    "wrist_view_4d",
    "detailed_robot_wm",
    "physics_video_wm",
]

Layer = Literal["arch", "sys", "infer", "train", "memory"]

Size = Literal["sm", "md", "lg"]


class EvolutionPaper(BaseModel):
    id: str
    title: str
    year: int
    quarter: Literal[1, 2, 3, 4]
    paradigm: Paradigm
    layer: Layer
    lane: str = Field(..., description="Top-level bottleneck lane ID")
    row: str = Field(..., description="Sub-row within lane")
    path: str = Field(..., description="Track within row (trunk or named fork)")
    size: Size = Field(default="md", description="Legacy sm/md/lg (fallback if no impact_score)")
    builds_on: List[str] = Field(default_factory=list)
    authors: List[str] = Field(default_factory=list)
    arxiv_id: Optional[str] = None
    cited_by_count: int = 0
    venue_tier: Optional[int] = Field(default=None, description="1-5, T1=top oral, T5=tech report")
    institution_tier: Optional[int] = Field(default=None, description="1-4, T1=top AI lab")
    impact_score: Optional[float] = Field(default=None, description="0-100 continuous, computed")
    impact_override: Optional[float] = Field(default=None, description="Manual override for impact_score")
    is_rising: bool = False
    is_weak_signal: bool = False


class LaneDef(BaseModel):
    id: str
    title: str
    subtitle: str
    color: str


class RowDef(BaseModel):
    id: str
    lane: str
    title: str
    subtitle: str


class IterationMutation(BaseModel):
    summary: str
    detail: str
    bottleneck: Optional[str] = None
    result: Optional[str] = None


class IterationDef(BaseModel):
    id: str
    title: str
    subtitle: str
    path: str
    row: str
    papers: List[str]
    mutations: dict[str, IterationMutation]


class EvolutionMapResponse(BaseModel):
    lanes: List[LaneDef]
    rows: List[RowDef]
    papers: List[EvolutionPaper]
    iterations: List[IterationDef]
