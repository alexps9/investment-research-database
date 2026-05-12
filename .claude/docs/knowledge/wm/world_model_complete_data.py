"""
Complete World Model Evolution Map Data
Source: README.md from Awesome-World-Models repository
Coverage: Part 1-5 (RL-Based, Observation-Level, Latent Space, Object-Centric, Robotics)

Citation Relations extracted from:
- Paper titles and naming conventions
- Web search results (arXiv, OpenReview, official repos)
- Logical evolution patterns
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Paper:
    id: str
    title: str
    year: int
    quarter: int  # 1-4
    venue: str
    lane: str  # obs_gen, latent_wm, rl_wm, obj_centric, robotics
    row: str   # sub-category
    paradigm: str
    layer: str = "arch"  # arch, sys, train
    size: str = "md"  # sm, md, lg
    builds_on: List[str] = field(default_factory=list)
    cites: List[str] = field(default_factory=list)  # Related but not direct inheritance
    influenced_by: List[str] = field(default_factory=list)  # Conceptual influence
    path: str = "trunk"  # trunk, multimodal, game, driving
    note: str = ""

# ============================================================
# LANE 1: RL-Based World Models (Part 1)
# ============================================================

RL_PAPERS = [
    # RSSM Foundation (2018-2019)
    Paper(
        id="planet",
        title="PlaNet: Learning latent dynamics for planning from pixels",
        year=2019, quarter=2, venue="ICML",
        lane="rl_wm", row="rssm_foundation", paradigm="rssm",
        size="lg", path="trunk",
        note="RSSM architecture foundation"
    ),
    
    # Dreamer Series
    Paper(
        id="dreamer_v1",
        title="Dreamer: Dream to control: Learning behaviors by latent imagination",
        year=2020, quarter=1, venue="ICLR",
        lane="rl_wm", row="dreamer_series", paradigm="imagination_rl",
        size="lg", path="trunk",
        builds_on=["planet"],
        cites=["rssm"],
        note="First end-to-end imagination-based RL"
    ),
    Paper(
        id="dreamer_v2",
        title="DreamerV2: Mastering atari with discrete world models",
        year=2021, quarter=1, venue="ICLR",
        lane="rl_wm", row="dreamer_series", paradigm="imagination_rl",
        size="lg", path="trunk",
        builds_on=["dreamer_v1"],
        note="Discrete categorical latent states"
    ),
    Paper(
        id="dreamer_v3",
        title="DreamerV3: Mastering diverse control tasks through world models",
        year=2025, quarter=1, venue="Nature",
        lane="rl_wm", row="dreamer_series", paradigm="imagination_rl",
        size="lg", path="trunk",
        builds_on=["dreamer_v2"],
        note="Universal architecture, fixed hyperparameters"
    ),
    
    # Dreamer Variants
    Paper(
        id="dreamsmooth",
        title="DreamSmooth: Improving model-based RL via reward smoothing",
        year=2024, quarter=1, venue="ICLR",
        lane="rl_wm", row="dreamer_variants", paradigm="imagination_rl",
        size="sm", path="trunk",
        builds_on=["dreamer_v1"]
    ),
    Paper(
        id="pigdreamer",
        title="PIGDreamer: Privileged information guided world models",
        year=2025, quarter=3, venue="ICML",
        lane="rl_wm", row="dreamer_variants", paradigm="imagination_rl",
        size="sm", path="trunk",
        builds_on=["dreamer_v1"]
    ),
    Paper(
        id="harmonydream",
        title="HarmonyDream: Task Harmonization Inside World Models",
        year=2024, quarter=2, venue="ICML",
        lane="rl_wm", row="dreamer_variants", paradigm="imagination_rl",
        size="sm", path="trunk",
        builds_on=["dreamer_v1"]
    ),
    Paper(
        id="dymodreamer",
        title="DyMoDreamer: World modeling with dynamic modulation",
        year=2025, quarter=4, venue="NeurIPS",
        lane="rl_wm", row="dreamer_variants", paradigm="imagination_rl",
        size="sm", path="trunk",
        builds_on=["dreamer_v1"]
    ),
    
    # TD-MPC Series
    Paper(
        id="tdmpc",
        title="TD-MPC: Temporal Difference Learning for Model Predictive Control",
        year=2022, quarter=2, venue="ICML",
        lane="rl_wm", row="tdmpc_series", paradigm="model_based_rl",
        size="lg", path="trunk",
        influenced_by=["planet", "dreamer_v1"],
        note="TD learning + MPC planning"
    ),
    Paper(
        id="tdmpc2",
        title="TD-MPC2: Scalable, robust world models for continuous control",
        year=2024, quarter=1, venue="ICLR",
        lane="rl_wm", row="tdmpc_series", paradigm="model_based_rl",
        size="lg", path="trunk",
        builds_on=["tdmpc"],
        note="Multi-task scaling"
    ),
    
    # TD-MPC Variants
    Paper(
        id="pwm",
        title="PWM: Policy learning with multi-task world models",
        year=2025, quarter=1, venue="ICLR",
        lane="rl_wm", row="tdmpc_variants", paradigm="model_based_rl",
        size="md", path="trunk",
        builds_on=["tdmpc2"],
        note="Multi-task policy learning"
    ),
    Paper(
        id="iq_mpc",
        title="IQ-MPC: Reward-free world models for online imitation learning",
        year=2025, quarter=2, venue="ICML",
        lane="rl_wm", row="tdmpc_variants", paradigm="model_based_rl",
        size="sm", path="trunk",
        builds_on=["tdmpc"]
    ),
    
    # Hierarchical World Models
    Paper(
        id="hieros",
        title="Hieros: Hierarchical imagination on structured state space sequence world models",
        year=2024, quarter=2, venue="ICML",
        lane="rl_wm", row="hierarchical_wm", paradigm="hierarchical_rl",
        size="md", path="trunk",
        builds_on=["dreamer_v1"]
    ),
    Paper(
        id="thick",
        title="THICK: Learning hierarchical world models with adaptive temporal abstractions",
        year=2024, quarter=1, venue="ICLR",
        lane="rl_wm", row="hierarchical_wm", paradigm="hierarchical_rl",
        size="md", path="trunk",
        builds_on=["dreamer_v2"]
    ),
    
    # Memory & Long-horizon
    Paper(
        id="r2i",
        title="R2I: Mastering memory tasks with world models",
        year=2024, quarter=1, venue="ICLR",
        lane="rl_wm", row="memory_wm", paradigm="memory_augmented",
        size="md", path="trunk",
        influenced_by=["rssm"]
    ),
    Paper(
        id="leq",
        title="LEQ: Model-based offline RL with lower expectile q-learning",
        year=2025, quarter=1, venue="ICLR",
        lane="rl_wm", row="offline_rl", paradigm="offline_model_based",
        size="sm", path="trunk",
        influenced_by=["dreamer_v1"]
    ),
    
    # Multi-agent & Collaborative
    Paper(
        id="dima",
        title="DIMA: Revisiting multi-agent world modeling from a diffusion-inspired perspective",
        year=2025, quarter=4, venue="NeurIPS",
        lane="rl_wm", row="multi_agent", paradigm="multi_agent_wm",
        size="md", path="trunk",
        influenced_by=["dreamer_v1", "diffusion_models"],
        note="Diffusion-inspired multi-agent"
    ),
    Paper(
        id="coworld",
        title="CoWorld: Making offline RL online: Collaborative world models",
        year=2024, quarter=4, venue="NeurIPS",
        lane="rl_wm", row="multi_agent", paradigm="collaborative_wm",
        size="md", path="trunk",
        builds_on=["dreamer_v1"],
        note="Offline to online visual RL"
    ),
    
    # Specialized Variants
    Paper(
        id="pcm",
        title="PCM: Policy-conditioned environment models are more generalizable",
        year=2024, quarter=2, venue="ICML",
        lane="rl_wm", row="policy_conditioned", paradigm="generalization",
        size="sm", path="trunk"
    ),
    Paper(
        id="waker",
        title="WAKER: Reward-free curricula for training robust world models",
        year=2024, quarter=1, venue="ICLR",
        lane="rl_wm", row="robustness", paradigm="curriculum_learning",
        size="sm", path="trunk"
    ),
    Paper(
        id="rem",
        title="REM: Improving token-based world models with parallel observation prediction",
        year=2024, quarter=2, venue="ICML",
        lane="rl_wm", row="token_based", paradigm="tokenized_wm",
        size="sm", path="trunk",
        influenced_by=["transformers"]
    ),
    Paper(
        id="crssm",
        title="cRSSM: Dreaming of many worlds: Learning contextual world models",
        year=2024, quarter=1, venue="EWRL",
        lane="rl_wm", row="contextual", paradigm="zero_shot",
        size="sm", path="trunk",
        builds_on=["dreamer_v2"]
    ),
    Paper(
        id="adaptive_wm",
        title="Adaptive world models: Learning behaviors by latent imagination under non-stationarity",
        year=2024, quarter=4, venue="NeurIPS",
        lane="rl_wm", row="adaptive", paradigm="non_stationary",
        size="sm", path="trunk",
        builds_on=["dreamer_v1"]
    ),
    Paper(
        id="mosim",
        title="MoSim: Neural motion simulator pushing the limit of world models in RL",
        year=2025, quarter=2, venue="CVPR",
        lane="rl_wm", row="motion_simulation", paradigm="simulation",
        size="md", path="trunk",
        influenced_by=["dreamer_v3"]
    ),
]

# ============================================================
# LANE 2: Observation-Level Generative (Part 2)
# ============================================================

OBS_GEN_PAPERS = [
    # Language Observations
    Paper(
        id="gpt4",
        title="GPT-4 Technical Report",
        year=2023, quarter=1, venue="arXiv",
        lane="obs_gen", row="language_wm", paradigm="llm_world_model",
        size="lg", path="multimodal"
    ),
    Paper(
        id="llama3",
        title="The Llama 3 Herd of Models",
        year=2024, quarter=3, venue="arXiv",
        lane="obs_gen", row="language_wm", paradigm="llm_world_model",
        size="lg", path="multimodal",
        builds_on=["gpt4"]
    ),
    Paper(
        id="llmcwm",
        title="LLMCWM: Language agents meet causality",
        year=2025, quarter=1, venue="ICLR",
        lane="obs_gen", row="language_wm", paradigm="causal_llm",
        size="md", path="multimodal",
        influenced_by=["gpt4"]
    ),
    Paper(
        id="rap",
        title="RAP: Reasoning with language model is planning with world model",
        year=2023, quarter=4, venue="EMNLP",
        lane="obs_gen", row="language_wm", paradigm="reasoning_planning",
        size="md", path="multimodal",
        influenced_by=["gpt4"]
    ),
    Paper(
        id="bytesized32",
        title="ByteSized32-State-Prediction: Can language models serve as text-based world simulators?",
        year=2024, quarter=2, venue="ACL",
        lane="obs_gen", row="language_wm", paradigm="text_simulator",
        size="sm", path="multimodal"
    ),
    
    # Video Generation (Main Stream)
    Paper(
        id="sora",
        title="Sora: Video generation models as world simulators",
        year=2024, quarter=1, venue="OpenAI",
        lane="obs_gen", row="video_generation", paradigm="diffusion_video",
        size="lg", path="trunk",
        note="Video diffusion as world simulator"
    ),
    Paper(
        id="gen3",
        title="Gen-3 Alpha",
        year=2024, quarter=2, venue="Runway",
        lane="obs_gen", row="video_generation", paradigm="diffusion_video",
        size="lg", path="trunk",
        builds_on=["sora"],
        cites=["video_diffusion_models"]
    ),
    Paper(
        id="wan",
        title="Wan: Open and Advanced Large-Scale Video Generative Models",
        year=2025, quarter=1, venue="arXiv",
        lane="obs_gen", row="video_generation", paradigm="diffusion_video",
        size="lg", path="trunk",
        builds_on=["sora", "gen3"]
    ),
    Paper(
        id="cosmos",
        title="Cosmos: World Foundation Model Platform for Physical AI",
        year=2025, quarter=1, venue="NVIDIA",
        lane="obs_gen", row="video_generation", paradigm="diffusion_video",
        size="lg", path="trunk",
        builds_on=["sora"],
        note="NVIDIA's physical AI world model"
    ),
    
    # Autoregressive Video
    Paper(
        id="emu3",
        title="Emu3: Next-token prediction is all you need",
        year=2024, quarter=3, venue="arXiv",
        lane="obs_gen", row="autoregressive_video", paradigm="ar_video",
        size="md", path="multimodal",
        influenced_by=["llama3"],
        note="Multimodal autoregressive"
    ),
    Paper(
        id="llava",
        title="LLaVA: Visual instruction tuning",
        year=2023, quarter=4, venue="NeurIPS",
        lane="obs_gen", row="autoregressive_video", paradigm="vlm",
        size="md", path="multimodal"
    ),
    
    # Specialized Video Models
    Paper(
        id="t2v_turbo",
        title="T2V-Turbo: Breaking the quality bottleneck of video consistency",
        year=2024, quarter=4, venue="NeurIPS",
        lane="obs_gen", row="video_efficiency", paradigm="efficient_video",
        size="sm", path="trunk",
        builds_on=["sora"]
    ),
    Paper(
        id="spmem",
        title="SPMEM: Video world models with long-term spatial memory",
        year=2025, quarter=4, venue="NeurIPS",
        lane="obs_gen", row="video_memory", paradigm="memory_augmented_video",
        size="md", path="trunk",
        influenced_by=["sora"]
    ),
    Paper(
        id="videocrafter2",
        title="VideoCrafter2: Overcoming data limitations for high-quality video diffusion",
        year=2024, quarter=2, venue="CVPR",
        lane="obs_gen", row="video_quality", paradigm="data_efficient_video",
        size="md", path="trunk"
    ),
    
    # Interactive / Playable Worlds
    Paper(
        id="genie2",
        title="Genie 2: A large-scale foundation world model",
        year=2024, quarter=4, venue="DeepMind",
        lane="obs_gen", row="interactive_worlds", paradigm="interactive_video",
        size="lg", path="game",
        builds_on=["sora"],
        note="Interactive world generation"
    ),
    Paper(
        id="oasis",
        title="Oasis: A Universe in a Transformer",
        year=2024, quarter=3, venue="Decart",
        lane="obs_gen", row="interactive_worlds", paradigm="game_world_model",
        size="md", path="game",
        influenced_by=["sora", "genie2"]
    ),
    Paper(
        id="teleworld",
        title="TeleWorld: Macro-from-Micro Planning for High-Quality Long Video Generation",
        year=2025, quarter=3, venue="arXiv",
        lane="obs_gen", row="interactive_worlds", paradigm="long_video",
        size="md", path="trunk",
        builds_on=["sora"]
    ),
    Paper(
        id="vid2world",
        title="Vid2World: Crafting video diffusion models to interactive world models",
        year=2025, quarter=2, venue="arXiv",
        lane="obs_gen", row="interactive_worlds", paradigm="video_to_world",
        size="md", path="trunk",
        builds_on=["sora"],
        influenced_by=["genie2"]
    ),
    Paper(
        id="cola_world",
        title="CoLA-World: Co-Evolving Latent Action World Models",
        year=2025, quarter=4, venue="arXiv",
        lane="obs_gen", row="interactive_worlds", paradigm="latent_action",
        size="sm", path="trunk"
    ),
    
    # 3D/4D Generation
    Paper(
        id="text2room",
        title="Text2Room: Extracting textured 3D meshes from 2D text-to-image models",
        year=2023, quarter=3, venue="ICCV",
        lane="obs_gen", row="3d_generation", paradigm="text_to_3d",
        size="md", path="trunk",
        influenced_by=["dreamfusion"]
    ),
    Paper(
        id="4dfy",
        title="4D-fy: Text-to-4D generation using hybrid score distillation",
        year=2024, quarter=2, venue="CVPR",
        lane="obs_gen", row="4d_generation", paradigm="text_to_4d",
        size="md", path="trunk",
        builds_on=["text2room"],
        note="4D generation from text"
    ),
    Paper(
        id="wonderjourney",
        title="WonderJourney: Going from anywhere to everywhere",
        year=2024, quarter=2, venue="CVPR",
        lane="obs_gen", row="3d_generation", paradigm="perpetual_3d",
        size="md", path="trunk"
    ),
    Paper(
        id="scenescape",
        title="SceneScape: Text-driven consistent scene generation",
        year=2023, quarter=4, venue="NeurIPS",
        lane="obs_gen", row="3d_generation", paradigm="scene_generation",
        size="md", path="trunk"
    ),
    Paper(
        id="wonderworld",
        title="WonderWorld: Interactive 3D scene generation from a single image",
        year=2025, quarter=2, venue="CVPR",
        lane="obs_gen", row="3d_generation", paradigm="image_to_3d",
        size="lg", path="trunk",
        builds_on=["wonderjourney", "text2room"]
    ),
    Paper(
        id="lidar_crafter",
        title="LiDARCrafter: Dynamic 4D world modeling from LiDAR sequences",
        year=2025, quarter=2, venue="arXiv",
        lane="obs_gen", row="4d_generation", paradigm="lidar_4d",
        size="md", path="trunk",
        influenced_by=["4dfy"]
    ),
    Paper(
        id="invisible_stitch",
        title="Invisible Stitch: Generating smooth 3D scenes with depth inpainting",
        year=2024, quarter=1, venue="3DV",
        lane="obs_gen", row="3d_generation", paradigm="depth_inpainting",
        size="sm", path="trunk"
    ),
]

# ============================================================
# LANE 3: Latent Space World Models (Part 3)
# ============================================================

LATENT_WM_PAPERS = [
    # JEPA Series
    Paper(
        id="i_jepa",
        title="I-JEPA: Self-supervised learning from images with a joint-embedding predictive architecture",
        year=2023, quarter=2, venue="CVPR",
        lane="latent_wm", row="jepa_family", paradigm="joint_embedding",
        size="lg", path="trunk",
        influenced_by=["lecun_jepa", "vicreg"],
        note="Image-level JEPA"
    ),
    Paper(
        id="v_jepa",
        title="V-JEPA: Revisiting Feature Prediction for Learning Visual Representations from Video",
        year=2024, quarter=1, venue="TMLR",
        lane="latent_wm", row="jepa_family", paradigm="joint_embedding_video",
        size="lg", path="trunk",
        builds_on=["i_jepa"],
        note="Video extension of JEPA"
    ),
    Paper(
        id="v_jepa_2",
        title="V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning",
        year=2025, quarter=2, venue="arXiv",
        lane="latent_wm", row="jepa_family", paradigm="jepa_planning",
        size="lg", path="trunk",
        builds_on=["v_jepa"],
        note="Adds action-conditioned prediction"
    ),
    Paper(
        id="seq_jepa",
        title="seq-JEPA: Autoregressive Predictive Learning of Invariant-Equivariant World Models",
        year=2025, quarter=4, venue="NeurIPS",
        lane="latent_wm", row="jepa_family", paradigm="sequential_jepa",
        size="md", path="trunk",
        builds_on=["v_jepa"]
    ),
    Paper(
        id="mc_jepa",
        title="MC-JEPA: Joint-Embedding Predictive Architecture for Motion and Content Features",
        year=2023, quarter=3, venue="arXiv",
        lane="latent_wm", row="jepa_family", paradigm="motion_content",
        size="sm", path="trunk",
        influenced_by=["i_jepa"]
    ),
    
    # DINO-based World Models
    Paper(
        id="dino_wm",
        title="DINO-WM: World Models on Pre-trained Visual Features Enable Zero-shot Planning",
        year=2025, quarter=3, venue="ICML",
        lane="latent_wm", row="dino_features", paradigm="feature_world_model",
        size="md", path="trunk",
        influenced_by=["dinov2", "i_jepa"],
        note="World models on DINO features"
    ),
    Paper(
        id="dino_world",
        title="DINO-World: Back to the Features: DINO as a Foundation for Video World Models",
        year=2025, quarter=3, venue="arXiv",
        lane="latent_wm", row="dino_features", paradigm="dino_video_wm",
        size="md", path="trunk",
        builds_on=["dino_wm"],
        note="Video prediction in DINO latent space"
    ),
    Paper(
        id="dino_foresight",
        title="DINO-Foresight: Looking into the Future with DINO",
        year=2025, quarter=4, venue="NeurIPS",
        lane="latent_wm", row="dino_features", paradigm="dino_future_prediction",
        size="md", path="trunk",
        builds_on=["dino_wm", "dino_world"]
    ),
    
    # Structured Latent Space
    Paper(
        id="world_models_group_latents",
        title="World Models Group Latents: Learning Abstract World Models with Group-Structured Latent Space",
        year=2025, quarter=2, venue="arXiv",
        lane="latent_wm", row="structured_latent", paradigm="group_structure",
        size="md", path="trunk",
        influenced_by=["group_theory", "i_jepa"]
    ),
    
    # Tokenized World Models
    Paper(
        id="lwm",
        title="LWM: World Model on Million-Length Video and Language with Blockwise RingAttention",
        year=2025, quarter=1, venue="ICLR",
        lane="latent_wm", row="tokenized_wm", paradigm="long_context_wm",
        size="md", path="trunk",
        influenced_by=["llama3", "ring_attention"],
        note="Million-length video + language"
    ),
]

# ============================================================
# LANE 4: Object-Centric World Models (Part 4)
# ============================================================

OBJ_CENTRIC_PAPERS = [
    # Slot Attention Foundation
    Paper(
        id="slot_attention",
        title="Object-centric Learning with Slot Attention",
        year=2020, quarter=3, venue="NeurIPS",
        lane="obj_centric", row="slot_attention", paradigm="object_discovery",
        size="lg", path="trunk",
        note="Foundation of object-centric learning"
    ),
    Paper(
        id="slotformer",
        title="SlotFormer: Unsupervised Visual Dynamics Simulation with Object-Centric Models",
        year=2023, quarter=1, venue="ICLR",
        lane="obj_centric", row="slot_attention", paradigm="object_dynamics",
        size="md", path="trunk",
        builds_on=["slot_attention"],
        note="Object-centric world models"
    ),
    Paper(
        id="lslotformer",
        title="LSlotFormer: Object-Centric World Model for Language-Guided Manipulation",
        year=2025, quarter=1, venue="ICLRW",
        lane="obj_centric", row="slot_attention", paradigm="language_object_wm",
        size="md", path="trunk",
        builds_on=["slotformer"],
        note="Language-guided object manipulation"
    ),
    Paper(
        id="mead",
        title="MEAD: Efficient Exploration and Discriminative World Model Learning with Object-Centric Abstraction",
        year=2025, quarter=1, venue="ICLR",
        lane="obj_centric", row="slot_attention", paradigm="exploration_object",
        size="md", path="trunk",
        builds_on=["slotformer"]
    ),
    
    # Structured Object Dynamics
    Paper(
        id="dyn_o",
        title="Dyn-O: Building Structured World Models with Object-Centric Representations",
        year=2025, quarter=4, venue="NeurIPS",
        lane="obj_centric", row="structured_dynamics", paradigm="structured_object_wm",
        size="md", path="trunk",
        builds_on=["slotformer"],
        influenced_by=["slot_attention", "graph_networks"],
        note="Structured world models with objects"
    ),
    Paper(
        id="g_swm",
        title="G-SWM: Improving Generative Imagination in Object-Centric World Models",
        year=2020, quarter=3, venue="ICML",
        lane="obj_centric", row="structured_dynamics", paradigm="generative_object",
        size="sm", path="trunk",
        influenced_by=["slot_attention"]
    ),
    
    # Object-Centric + RL
    Paper(
        id="fioc_wm",
        title="FIOC-WM: Learning Interactive World Model for Object-Centric RL",
        year=2025, quarter=1, venue="arXiv",
        lane="obj_centric", row="ocrl", paradigm="interactive_object_rl",
        size="sm", path="trunk",
        builds_on=["slotformer"],
        influenced_by=["dreamer_v1"]
    ),
    Paper(
        id="objects_matter",
        title="Objects matter: object-centric world models improve RL in visually complex environments",
        year=2025, quarter=1, venue="arXiv",
        lane="obj_centric", row="ocrl", paradigm="object_rl_benefits",
        size="sm", path="trunk",
        influenced_by=["slot_attention", "dreamer_v1"]
    ),
    Paper(
        id="owm_meets_policy",
        title="When Object-Centric World Models Meet Policy Learning: From Pixels to Policies",
        year=2025, quarter=4, venue="arXiv",
        lane="obj_centric", row="ocrl", paradigm="object_policy",
        size="sm", path="trunk",
        builds_on=["slotformer", "dreamer_v1"]
    ),
    Paper(
        id="object_centric_latent_action",
        title="Object-Centric Latent Action Learning",
        year=2025, quarter=1, venue="ICLRW",
        lane="obj_centric", row="ocrl", paradigm="object_latent_actions",
        size="sm", path="trunk",
        influenced_by=["slot_attention"]
    ),
    
    # Compositional & Causal
    Paper(
        id="compositional_ocl",
        title="Compositional OCL: Unifying Causal and Object-centric Representation Learning",
        year=2024, quarter=1, venue="ICLRW",
        lane="obj_centric", row="causal_compositional", paradigm="causal_object",
        size="sm", path="trunk",
        influenced_by=["slot_attention", "causal_representation"]
    ),
    Paper(
        id="oc_repr_generalize",
        title="Object-Centric Representations Generalize Better Compositionally with Less Compute",
        year=2025, quarter=1, venue="ICLRW",
        lane="obj_centric", row="causal_compositional", paradigm="compositional_generalization",
        size="sm", path="trunk",
        builds_on=["slot_attention"]
    ),
    
    # Driving Applications
    Paper(
        id="carformer",
        title="CarFormer: Self-driving with Learned Object-Centric Representations",
        year=2024, quarter=3, venue="ECCV",
        lane="obj_centric", row="driving_object", paradigm="object_centric_driving",
        size="md", path="driving",
        builds_on=["slotformer"],
        note="Object-centric representations for driving"
    ),
    
    # Robotics
    Paper(
        id="focus",
        title="FOCUS: object-centric world models for robotic manipulation",
        year=2025, quarter=1, venue="Frontiers Neurorobotics",
        lane="obj_centric", row="robotics_object", paradigm="robot_object_wm",
        size="sm", path="trunk",
        builds_on=["slot_attention"]
    ),
]

# ============================================================
# LANE 5: Robotics World Models (Part 5 - Partial)
# ============================================================

ROBOTICS_PAPERS = [
    # Visual Future Prediction
    Paper(
        id="robodreamer",
        title="RoboDreamer: Learning Compositional World Models for Robot Imagination",
        year=2024, quarter=2, venue="ICML",
        lane="robotics", row="visual_future_pred", paradigm="robot_imagination",
        size="md", path="trunk",
        influenced_by=["sora", "dreamer_v1"],
        note="Robot imagination with video diffusion"
    ),
    Paper(
        id="grounding_video",
        title="Grounding Video Models to Actions through Goal Conditioned Exploration",
        year=2025, quarter=1, venue="ICLR",
        lane="robotics", row="visual_future_pred", paradigm="video_to_action",
        size="md", path="trunk",
        builds_on=["sora"],
        influenced_by=["dreamer_v1"]
    ),
    Paper(
        id="vipra",
        title="ViPRA: Video Prediction for Robot Actions",
        year=2025, quarter=4, venue="arXiv",
        lane="robotics", row="visual_future_pred", paradigm="video_prediction_rl",
        size="md", path="trunk",
        influenced_by=["sora", "robodreamer"]
    ),
    Paper(
        id="flowdreamer",
        title="FlowDreamer: RGB-D World Model with Flow-based Motion for Manipulation",
        year=2025, quarter=2, venue="arXiv",
        lane="robotics", row="visual_future_pred", paradigm="flow_motion_wm",
        size="sm", path="trunk",
        influenced_by=["robodreamer"]
    ),
    
    # 4D World Models for Robotics
    Paper(
        id="tesseract",
        title="TesserAct: Learning 4D Embodied World Models",
        year=2025, quarter=2, venue="arXiv",
        lane="robotics", row="4d_robotics", paradigm="4d_embodied",
        size="md", path="trunk",
        builds_on=["4dfy"],
        influenced_by=["dreamer_v1"]
    ),
    Paper(
        id="orv",
        title="ORV: 4D Occupancy-centric Robot Video Generation",
        year=2025, quarter=2, venue="arXiv",
        lane="robotics", row="4d_robotics", paradigm="occupancy_4d",
        size="md", path="trunk",
        builds_on=["tesseract"],
        influenced_by=["sora"]
    ),
    Paper(
        id="wristworld",
        title="WristWorld: Generating Wrist-Views via 4D World Models",
        year=2025, quarter=4, venue="arXiv",
        lane="robotics", row="4d_robotics", paradigm="wrist_view_4d",
        size="sm", path="trunk",
        builds_on=["orv", "tesseract"]
    ),
    
    # Fine-grained Robot Models
    Paper(
        id="irasim",
        title="IRASim: A Fine-Grained World Model for Robot Manipulation",
        year=2025, quarter=4, venue="ICCV",
        lane="robotics", row="fine_grained", paradigm="detailed_robot_wm",
        size="md", path="trunk",
        influenced_by=["sora", "genie2"]
    ),
    Paper(
        id="wisa",
        title="WISA: World Simulator Assistant for Physics-aware Text-to-Video",
        year=2025, quarter=4, venue="NeurIPS",
        lane="robotics", row="physics_aware", paradigm="physics_video_wm",
        size="md", path="trunk",
        influenced_by=["sora", "wonderworld"]
    ),
]

# ============================================================
# CROSS-LANE INFLUENCES (Conceptual connections)
# ============================================================

CROSS_LANE_INFLUENCES = {
    # Era 1 -> Era 2 Foundation
    "planet": ["dreamer_v1", "tdmpc"],

    # Video generation influences + cross-lane to robotics
    "sora": ["gen3", "wan", "cosmos", "genie2", "teleworld", "vid2world",
             "robodreamer", "grounding_video", "vipra"],
    "genie2": ["oasis", "irasim"],

    # JEPA evolution
    "i_jepa": ["v_jepa", "mc_jepa"],
    "v_jepa": ["v_jepa_2", "seq_jepa"],

    # DINO features
    "dino_wm": ["dino_world", "dino_foresight"],

    # Object-centric foundation
    "slot_attention": ["slotformer", "g_swm", "objects_matter", "focus"],
    "slotformer": ["lslotformer", "dyn_o", "fioc_wm", "mead", "carformer", "owm_meets_policy"],

    # Cross-lane fusion (Era 3)
    "dreamer_v1": ["fioc_wm", "objects_matter", "owm_meets_policy"],  # RL -> Object-centric
    "v_jepa_2": ["dyn_o"],  # Latent -> Object-centric

    # 4D evolution
    "text2room": ["4dfy", "wonderworld"],
    "4dfy": ["tesseract", "orv", "lidar_crafter"],
    "tesseract": ["orv", "wristworld"],
}

# External references: IDs used in builds_on/influenced_by that are NOT in ALL_PAPERS.
# These represent foundational works outside the survey scope.
EXTERNAL_REFS = [
    "rssm",            # Hafner et al. 2018 (embedded in PlaNet)
    "lecun_jepa",      # LeCun's JEPA position paper (2022)
    "vicreg",          # VICReg self-supervised learning
    "dinov2",          # DINOv2 (Meta, 2023)
    "ring_attention",  # Ring Attention (UC Berkeley, 2023)
    "dreamfusion",     # DreamFusion (Google, 2022)
    "magnificent_3d",  # Not a real paper — remove from 4dfy builds_on
    "diffusion_models",  # General diffusion models concept
    "transformers",    # Transformer architecture (Vaswani 2017)
    "graph_networks",  # GNN family
    "causal_representation",  # Causal representation learning
    "group_theory",    # Mathematical group theory
    "video_diffusion_models",  # Video diffusion family
]

# ============================================================
# ERA CLASSIFICATION
# ============================================================

ERA_DEFINITIONS = {
    "era_1": {
        "name": "Latent Dynamics (2018-2023)",
        "years": (2018, 2023),
        "dominant_lane": "rl_wm",
        "key_papers": ["planet", "dreamer_v1", "dreamer_v2", "slot_attention", "i_jepa"],
        "pressure": "Sample Efficiency Crisis"
    },
    "era_2": {
        "name": "Generative Simulation (2024-2025)",
        "years": (2024, 2025),
        "dominant_lane": "obs_gen",
        "key_papers": ["sora", "v_jepa", "dino_wm", "slotformer", "robodreamer"],
        "pressure": "High-Fidelity World Generation"
    },
    "era_3": {
        "name": "Causal Reasoning (2025-2026+)",
        "years": (2025, 2027),
        "dominant_lane": "obj_centric",
        "key_papers": ["dyn_o", "v_jepa_2", "dreamer_v3", "owm_meets_policy"],
        "pressure": "Physical Consistency & Causality"
    }
}

# ============================================================
# AGGREGATE ALL PAPERS
# ============================================================

ALL_PAPERS = (
    RL_PAPERS + 
    OBS_GEN_PAPERS + 
    LATENT_WM_PAPERS + 
    OBJ_CENTRIC_PAPERS + 
    ROBOTICS_PAPERS
)

# Statistics
PAPER_COUNT = len(ALL_PAPERS)
LANE_COUNTS = {
    "rl_wm": len(RL_PAPERS),
    "obs_gen": len(OBS_GEN_PAPERS),
    "latent_wm": len(LATENT_WM_PAPERS),
    "obj_centric": len(OBJ_CENTRIC_PAPERS),
    "robotics": len(ROBOTICS_PAPERS)
}

if __name__ == "__main__":
    print(f"Total papers: {PAPER_COUNT}")
    print(f"By lane: {LANE_COUNTS}")
