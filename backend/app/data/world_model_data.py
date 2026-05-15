"""
World Model Evolution Map data.
Four-layer ontology: Era → Lane (Bottleneck) → Row (Paradigm) → Paper

Eras:
  1. 潜动力学 (Latent Dynamics) 2018-2023: learn compressed dynamics
  2. 生成式仿真 (Generative Simulation) 2024-2025: pixel/video-level world generation
  3. 因果推理 (Causal Reasoning) 2025-2026+: structured causal world models

Lanes (Bottlenecks):
  A. Observation-Level Generative — pixel/video generation as world modeling
  B. Latent-Space World Models — learn dynamics in latent space
  C. RL-Based World Models — imagination for planning
  D. Object-Centric World Models — compositional/structured representations
"""

from app.models.evolution import (
    EvolutionPaper,
    IterationDef,
    IterationMutation,
    LaneDef,
    RowDef,
)

LANES = [
    LaneDef(id="rl_wm", title="强化学习驱动世界模型", subtitle="RL-Based WMs", color="#059669"),
    LaneDef(id="obs_gen", title="观测层生成式世界模型", subtitle="Observation-Level Generative", color="#2563EB"),
    LaneDef(id="latent_wm", title="潜空间世界模型", subtitle="Latent-Space WMs", color="#7C3AED"),
    LaneDef(id="obj_centric", title="对象中心世界模型", subtitle="Object-Centric WMs", color="#EA580C"),
]

ROWS = [
    # Lane A: RL-Based World Models
    RowDef(id="dreamer_series", lane="rl_wm", title="A-1 Dreamer Series", subtitle="Imagination → Policy"),
    RowDef(id="dreamer_variants", lane="rl_wm", title="A-2 Dreamer Variants", subtitle="Task-specific Extensions"),
    RowDef(id="tdmpc_series", lane="rl_wm", title="A-3 TD-MPC Series", subtitle="TD + Model Predictive Control"),
    RowDef(id="hierarchical_wm", lane="rl_wm", title="A-4 Hierarchical WMs", subtitle="Temporal Abstraction"),
    RowDef(id="multi_agent", lane="rl_wm", title="A-5 Multi-Agent & Collaborative", subtitle="Multi-agent Dynamics"),
    RowDef(id="specialized_rl", lane="rl_wm", title="A-6 Specialized Variants", subtitle="Memory / Offline / Robustness"),
    RowDef(id="imagination_robotics", lane="rl_wm", title="A-7 Imagination for Robotics", subtitle="Video Prediction → Action"),

    # Lane B: Observation-Level Generative
    RowDef(id="language_wm", lane="obs_gen", title="B-1 Language WMs", subtitle="LLM as World Simulator"),
    RowDef(id="video_generation", lane="obs_gen", title="B-2 Video Generation", subtitle="Diffusion Video"),
    RowDef(id="autoregressive_video", lane="obs_gen", title="B-3 Autoregressive Video", subtitle="AR Multimodal"),
    RowDef(id="interactive_worlds", lane="obs_gen", title="B-4 Interactive Worlds", subtitle="Playable / Game"),
    RowDef(id="3d_4d_generation", lane="obs_gen", title="B-5 3D/4D Generation", subtitle="Scene Synthesis"),
    RowDef(id="embodied_generation", lane="obs_gen", title="B-6 Embodied Generation", subtitle="4D Robotics Video/Physics"),

    # Lane C: Latent-Space World Models
    RowDef(id="jepa_family", lane="latent_wm", title="C-1 JEPA Family", subtitle="Joint Embedding Prediction"),
    RowDef(id="dino_features", lane="latent_wm", title="C-2 DINO-based WMs", subtitle="Pre-trained Visual Features"),
    RowDef(id="structured_latent", lane="latent_wm", title="C-3 Structured Latent", subtitle="Group / Tokenized"),

    # Lane D: Object-Centric World Models
    RowDef(id="slot_attention", lane="obj_centric", title="D-1 Slot Attention", subtitle="Object Discovery"),
    RowDef(id="structured_dynamics", lane="obj_centric", title="D-2 Structured Dynamics", subtitle="Object Interaction"),
    RowDef(id="ocrl", lane="obj_centric", title="D-3 Object-Centric RL", subtitle="OC + Policy Learning"),
    RowDef(id="causal_compositional", lane="obj_centric", title="D-4 Causal & Compositional", subtitle="Causal Object Repr"),

]

PAPERS = [
    # ═══════════════════════════════════════════════════════════
    # Lane A: RL-Based World Models (22 papers)
    # ═══════════════════════════════════════════════════════════

    # Row: dreamer_series (主干)
    EvolutionPaper(id="planet", title="PlaNet", year=2019, quarter=2, paradigm="rssm", layer="arch", lane="rl_wm", row="dreamer_series", path="trunk", size="lg", cited_by_count=367, institution_tier=1, venue_tier=2),
    EvolutionPaper(id="dreamer_v1", title="Dreamer V1", year=2020, quarter=1, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_series", path="trunk", size="lg", builds_on=["planet"], cited_by_count=137, institution_tier=1, venue_tier=2),
    EvolutionPaper(id="dreamer_v2", title="Dreamer V2", year=2021, quarter=1, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_series", path="trunk", size="lg", builds_on=["dreamer_v1"], cited_by_count=23, institution_tier=1, venue_tier=2),
    EvolutionPaper(id="dreamer_v3", title="Dreamer V3", year=2025, quarter=1, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_series", path="trunk", size="lg", builds_on=["dreamer_v2"], cited_by_count=155, institution_tier=1, venue_tier=2),

    # Row: dreamer_variants
    EvolutionPaper(id="dreamsmooth", title="DreamSmooth", year=2024, quarter=1, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_variants", path="trunk", size="sm", builds_on=["dreamer_v1"], cited_by_count=1),
    EvolutionPaper(id="pigdreamer", title="PIGDreamer", year=2025, quarter=3, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_variants", path="trunk", size="sm", builds_on=["dreamer_v1"]),
    EvolutionPaper(id="harmonydream", title="HarmonyDream", year=2024, quarter=2, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_variants", path="trunk", size="sm", builds_on=["dreamer_v1"], cited_by_count=1),
    EvolutionPaper(id="dymodreamer", title="DyMoDreamer", year=2025, quarter=4, paradigm="imagination_rl", layer="arch", lane="rl_wm", row="dreamer_variants", path="trunk", size="sm", builds_on=["dreamer_v1"]),

    # Row: tdmpc_series
    EvolutionPaper(id="tdmpc", title="TD-MPC", year=2022, quarter=2, paradigm="model_based_rl", layer="arch", lane="rl_wm", row="tdmpc_series", path="trunk", size="lg", cited_by_count=27, institution_tier=2, venue_tier=2),
    EvolutionPaper(id="tdmpc2", title="TD-MPC2", year=2024, quarter=1, paradigm="model_based_rl", layer="arch", lane="rl_wm", row="tdmpc_series", path="trunk", size="lg", builds_on=["tdmpc"], cited_by_count=8, institution_tier=2, venue_tier=2),
    EvolutionPaper(id="pwm", title="PWM", year=2025, quarter=1, paradigm="model_based_rl", layer="arch", lane="rl_wm", row="tdmpc_series", path="trunk", size="md", builds_on=["tdmpc2"], cited_by_count=2),
    EvolutionPaper(id="iq_mpc", title="IQ-MPC", year=2025, quarter=2, paradigm="model_based_rl", layer="arch", lane="rl_wm", row="tdmpc_series", path="trunk", size="sm", builds_on=["tdmpc"], cited_by_count=1),

    # Row: hierarchical_wm
    EvolutionPaper(id="hieros", title="Hieros", year=2024, quarter=2, paradigm="hierarchical_rl", layer="arch", lane="rl_wm", row="hierarchical_wm", path="trunk", size="md", builds_on=["dreamer_v1"]),
    EvolutionPaper(id="thick", title="THICK", year=2024, quarter=1, paradigm="hierarchical_rl", layer="arch", lane="rl_wm", row="hierarchical_wm", path="trunk", size="md", builds_on=["dreamer_v2"]),

    # Row: multi_agent
    EvolutionPaper(id="dima", title="DIMA", year=2025, quarter=4, paradigm="multi_agent_wm", layer="arch", lane="rl_wm", row="multi_agent", path="trunk", size="md", cited_by_count=11),
    EvolutionPaper(id="coworld", title="CoWorld", year=2024, quarter=4, paradigm="collaborative_wm", layer="arch", lane="rl_wm", row="multi_agent", path="trunk", size="md", builds_on=["dreamer_v1"]),

    # Row: specialized_rl
    EvolutionPaper(id="r2i", title="R2I", year=2024, quarter=1, paradigm="memory_augmented", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="md", cited_by_count=6),
    EvolutionPaper(id="leq", title="LEQ", year=2025, quarter=1, paradigm="offline_model_based", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="sm", cited_by_count=1),
    EvolutionPaper(id="pcm", title="PCM", year=2024, quarter=2, paradigm="generalization", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="sm", cited_by_count=0),
    EvolutionPaper(id="waker", title="WAKER", year=2024, quarter=1, paradigm="curriculum_learning", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="sm", cited_by_count=0),
    EvolutionPaper(id="rem", title="REM", year=2024, quarter=2, paradigm="tokenized_wm", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="sm", cited_by_count=0),
    EvolutionPaper(id="crssm", title="cRSSM", year=2024, quarter=1, paradigm="zero_shot", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="sm", builds_on=["dreamer_v2"]),
    EvolutionPaper(id="adaptive_wm", title="Adaptive WM", year=2024, quarter=4, paradigm="non_stationary", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="sm", builds_on=["dreamer_v1"], cited_by_count=0),
    EvolutionPaper(id="mosim", title="MoSim", year=2025, quarter=2, paradigm="simulation", layer="arch", lane="rl_wm", row="specialized_rl", path="trunk", size="md", cited_by_count=5),

    # Row: imagination_robotics (from former Lane E)
    EvolutionPaper(id="robodreamer", title="RoboDreamer", year=2024, quarter=2, paradigm="robot_imagination", layer="arch", lane="rl_wm", row="imagination_robotics", path="trunk", size="md", cited_by_count=4, institution_tier=2, venue_tier=4),
    EvolutionPaper(id="vipra", title="ViPRA", year=2025, quarter=4, paradigm="video_prediction_rl", layer="arch", lane="rl_wm", row="imagination_robotics", path="trunk", size="md", cited_by_count=10),
    EvolutionPaper(id="flowdreamer", title="FlowDreamer", year=2025, quarter=2, paradigm="flow_motion_wm", layer="arch", lane="rl_wm", row="imagination_robotics", path="trunk", size="sm"),

    # ═══════════════════════════════════════════════════════════
    # Lane B: Observation-Level Generative (30 papers)
    # ═══════════════════════════════════════════════════════════

    # Row: language_wm
    EvolutionPaper(id="gpt4", title="GPT-4", year=2023, quarter=1, paradigm="llm_world_model", layer="arch", lane="obs_gen", row="language_wm", path="trunk", size="lg", cited_by_count=2318, institution_tier=1, venue_tier=5),
    EvolutionPaper(id="llama3", title="LLaMA 3", year=2024, quarter=3, paradigm="llm_world_model", layer="arch", lane="obs_gen", row="language_wm", path="trunk", size="lg", builds_on=["gpt4"], cited_by_count=3879, institution_tier=1, venue_tier=4),
    EvolutionPaper(id="llmcwm", title="LLMCWM", year=2025, quarter=1, paradigm="causal_llm", layer="arch", lane="obs_gen", row="language_wm", path="trunk", size="md"),
    EvolutionPaper(id="rap", title="RAP", year=2023, quarter=4, paradigm="reasoning_planning", layer="arch", lane="obs_gen", row="language_wm", path="trunk", size="md", cited_by_count=211),
    EvolutionPaper(id="bytesized32", title="ByteSized32", year=2024, quarter=2, paradigm="text_simulator", layer="arch", lane="obs_gen", row="language_wm", path="trunk", size="sm", cited_by_count=1),

    # Row: video_generation (主干)
    EvolutionPaper(id="sora", title="Sora", year=2024, quarter=1, paradigm="diffusion_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="lg", cited_by_count=101, institution_tier=1, venue_tier=5),
    EvolutionPaper(id="gen3", title="Gen-3 Alpha", year=2024, quarter=2, paradigm="diffusion_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="lg", builds_on=["sora"], cited_by_count=5, institution_tier=3, venue_tier=5),
    EvolutionPaper(id="wan", title="Wan (Alibaba, cited_by_count=7, institution_tier=3, venue_tier=4)", year=2025, quarter=1, paradigm="diffusion_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="lg", builds_on=["sora"]),
    EvolutionPaper(id="cosmos", title="Cosmos (NVIDIA, cited_by_count=7, institution_tier=1, venue_tier=4)", year=2025, quarter=1, paradigm="diffusion_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="lg", builds_on=["sora"]),
    EvolutionPaper(id="t2v_turbo", title="T2V-Turbo", year=2024, quarter=4, paradigm="efficient_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="sm", builds_on=["sora"], cited_by_count=1),
    EvolutionPaper(id="spmem", title="SPMEM", year=2025, quarter=4, paradigm="memory_augmented_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="md", cited_by_count=1),
    EvolutionPaper(id="videocrafter2", title="VideoCrafter2", year=2024, quarter=2, paradigm="data_efficient_video", layer="arch", lane="obs_gen", row="video_generation", path="trunk", size="md", cited_by_count=162),

    # Row: autoregressive_video
    EvolutionPaper(id="emu3", title="Emu3", year=2024, quarter=3, paradigm="ar_video", layer="arch", lane="obs_gen", row="autoregressive_video", path="trunk", size="md", cited_by_count=4),
    EvolutionPaper(id="llava", title="LLaVA", year=2023, quarter=4, paradigm="vlm", layer="arch", lane="obs_gen", row="autoregressive_video", path="trunk", size="md", cited_by_count=1140, institution_tier=2, venue_tier=2),

    # Row: interactive_worlds
    EvolutionPaper(id="genie2", title="Genie 2", year=2024, quarter=4, paradigm="interactive_video", layer="arch", lane="obs_gen", row="interactive_worlds", path="game", size="lg", builds_on=["sora"], institution_tier=1, venue_tier=5),
    EvolutionPaper(id="oasis", title="Oasis", year=2024, quarter=3, paradigm="game_world_model", layer="arch", lane="obs_gen", row="interactive_worlds", path="game", size="md", cited_by_count=0),
    EvolutionPaper(id="teleworld", title="TeleWorld", year=2025, quarter=3, paradigm="long_video", layer="sys", lane="obs_gen", row="interactive_worlds", path="trunk", size="md", builds_on=["sora"]),
    EvolutionPaper(id="vid2world", title="Vid2World", year=2025, quarter=2, paradigm="video_to_world", layer="arch", lane="obs_gen", row="interactive_worlds", path="trunk", size="md", builds_on=["sora"]),
    EvolutionPaper(id="cola_world", title="CoLA-World", year=2025, quarter=4, paradigm="latent_action", layer="arch", lane="obs_gen", row="interactive_worlds", path="trunk", size="sm", cited_by_count=3),

    # Row: 3d_4d_generation
    EvolutionPaper(id="text2room", title="Text2Room", year=2023, quarter=3, paradigm="text_to_3d", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="md", cited_by_count=129, institution_tier=2, venue_tier=2),
    EvolutionPaper(id="4dfy", title="4D-fy", year=2024, quarter=2, paradigm="text_to_4d", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="md", builds_on=["text2room"], cited_by_count=46),
    EvolutionPaper(id="wonderjourney", title="WonderJourney", year=2024, quarter=2, paradigm="perpetual_3d", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="md", cited_by_count=28),
    EvolutionPaper(id="scenescape", title="SceneScape", year=2023, quarter=4, paradigm="scene_generation", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="md", cited_by_count=24),
    EvolutionPaper(id="wonderworld", title="WonderWorld", year=2025, quarter=2, paradigm="image_to_3d", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="lg", builds_on=["wonderjourney", "text2room"], cited_by_count=16),
    EvolutionPaper(id="lidar_crafter", title="LiDARCrafter", year=2025, quarter=2, paradigm="lidar_4d", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="md"),
    EvolutionPaper(id="invisible_stitch", title="Invisible Stitch", year=2024, quarter=1, paradigm="depth_inpainting", layer="arch", lane="obs_gen", row="3d_4d_generation", path="trunk", size="sm", cited_by_count=3),

    # Row: embodied_generation (from former Lane E)
    EvolutionPaper(id="grounding_video", title="Grounding Video", year=2025, quarter=1, paradigm="video_to_action", layer="arch", lane="obs_gen", row="embodied_generation", path="trunk", size="md", builds_on=["sora"], cited_by_count=8),
    EvolutionPaper(id="tesseract", title="TesserAct", year=2025, quarter=2, paradigm="4d_embodied", layer="arch", lane="obs_gen", row="embodied_generation", path="trunk", size="md", builds_on=["4dfy"], cited_by_count=14, institution_tier=2, venue_tier=4),
    EvolutionPaper(id="orv", title="ORV", year=2025, quarter=2, paradigm="occupancy_4d", layer="arch", lane="obs_gen", row="embodied_generation", path="trunk", size="md", builds_on=["tesseract"], cited_by_count=1),
    EvolutionPaper(id="wristworld", title="WristWorld", year=2025, quarter=4, paradigm="wrist_view_4d", layer="arch", lane="obs_gen", row="embodied_generation", path="trunk", size="sm", builds_on=["tesseract"]),
    EvolutionPaper(id="irasim", title="IRASim", year=2025, quarter=4, paradigm="detailed_robot_wm", layer="arch", lane="obs_gen", row="embodied_generation", path="trunk", size="md", cited_by_count=1),
    EvolutionPaper(id="wisa", title="WISA", year=2025, quarter=4, paradigm="physics_video_wm", layer="arch", lane="obs_gen", row="embodied_generation", path="trunk", size="md", cited_by_count=9),

    # ═══════════════════════════════════════════════════════════
    # Lane C: Latent-Space World Models (10 papers)
    # ═══════════════════════════════════════════════════════════

    # Row: jepa_family
    EvolutionPaper(id="i_jepa", title="I-JEPA", year=2023, quarter=2, paradigm="joint_embedding", layer="arch", lane="latent_wm", row="jepa_family", path="trunk", size="lg", cited_by_count=272, institution_tier=1, venue_tier=2),
    EvolutionPaper(id="v_jepa", title="V-JEPA", year=2024, quarter=1, paradigm="joint_embedding_video", layer="arch", lane="latent_wm", row="jepa_family", path="trunk", size="lg", builds_on=["i_jepa"], cited_by_count=56, institution_tier=1, venue_tier=4),
    EvolutionPaper(id="v_jepa_2", title="V-JEPA 2", year=2025, quarter=2, paradigm="jepa_planning", layer="arch", lane="latent_wm", row="jepa_family", path="trunk", size="lg", builds_on=["v_jepa"], institution_tier=1, venue_tier=4),
    EvolutionPaper(id="seq_jepa", title="seq-JEPA", year=2025, quarter=4, paradigm="sequential_jepa", layer="arch", lane="latent_wm", row="jepa_family", path="trunk", size="md", builds_on=["v_jepa"]),
    EvolutionPaper(id="mc_jepa", title="MC-JEPA", year=2023, quarter=3, paradigm="motion_content", layer="arch", lane="latent_wm", row="jepa_family", path="trunk", size="sm", cited_by_count=5),

    # Row: dino_features
    EvolutionPaper(id="dino_wm", title="DINO-WM", year=2025, quarter=3, paradigm="feature_world_model", layer="arch", lane="latent_wm", row="dino_features", path="trunk", size="md", cited_by_count=5, institution_tier=1, venue_tier=4),
    EvolutionPaper(id="dino_world", title="DINO-World", year=2025, quarter=3, paradigm="dino_video_wm", layer="arch", lane="latent_wm", row="dino_features", path="trunk", size="md", builds_on=["dino_wm"], cited_by_count=5),
    EvolutionPaper(id="dino_foresight", title="DINO-Foresight", year=2025, quarter=4, paradigm="dino_future_prediction", layer="arch", lane="latent_wm", row="dino_features", path="trunk", size="md", builds_on=["dino_wm"], cited_by_count=1),

    # Row: structured_latent
    EvolutionPaper(id="world_models_group_latents", title="WM Group Latents", year=2025, quarter=2, paradigm="group_structure", layer="arch", lane="latent_wm", row="structured_latent", path="trunk", size="md", cited_by_count=15),
    EvolutionPaper(id="lwm", title="LWM", year=2025, quarter=1, paradigm="long_context_wm", layer="arch", lane="latent_wm", row="structured_latent", path="trunk", size="md", cited_by_count=17),

    # ═══════════════════════════════════════════════════════════
    # Lane D: Object-Centric World Models (14 papers)
    # ═══════════════════════════════════════════════════════════

    # Row: slot_attention
    EvolutionPaper(id="slot_attention", title="Slot Attention", year=2020, quarter=3, paradigm="object_discovery", layer="arch", lane="obj_centric", row="slot_attention", path="trunk", size="lg", cited_by_count=218, institution_tier=1, venue_tier=2),
    EvolutionPaper(id="slotformer", title="SlotFormer", year=2023, quarter=1, paradigm="object_dynamics", layer="arch", lane="obj_centric", row="slot_attention", path="trunk", size="md", builds_on=["slot_attention"], cited_by_count=10),
    EvolutionPaper(id="lslotformer", title="LSlotFormer", year=2025, quarter=1, paradigm="language_object_wm", layer="arch", lane="obj_centric", row="slot_attention", path="trunk", size="md", builds_on=["slotformer"]),
    EvolutionPaper(id="mead", title="MEAD", year=2025, quarter=1, paradigm="exploration_object", layer="arch", lane="obj_centric", row="slot_attention", path="trunk", size="md", builds_on=["slotformer"], cited_by_count=44),

    # Row: structured_dynamics
    EvolutionPaper(id="dyn_o", title="Dyn-O", year=2025, quarter=4, paradigm="structured_object_wm", layer="arch", lane="obj_centric", row="structured_dynamics", path="trunk", size="md", builds_on=["slotformer"], cited_by_count=13),
    EvolutionPaper(id="g_swm", title="G-SWM", year=2020, quarter=3, paradigm="generative_object", layer="arch", lane="obj_centric", row="structured_dynamics", path="trunk", size="sm", cited_by_count=9),
    EvolutionPaper(id="carformer", title="CarFormer", year=2024, quarter=3, paradigm="object_centric_driving", layer="arch", lane="obj_centric", row="structured_dynamics", path="driving", size="md", builds_on=["slotformer"], cited_by_count=4),
    EvolutionPaper(id="focus", title="FOCUS", year=2025, quarter=1, paradigm="robot_object_wm", layer="arch", lane="obj_centric", row="structured_dynamics", path="trunk", size="sm", builds_on=["slot_attention"], cited_by_count=0),

    # Row: ocrl
    EvolutionPaper(id="fioc_wm", title="FIOC-WM", year=2025, quarter=1, paradigm="interactive_object_rl", layer="arch", lane="obj_centric", row="ocrl", path="trunk", size="sm", builds_on=["slotformer"]),
    EvolutionPaper(id="objects_matter", title="Objects Matter", year=2025, quarter=1, paradigm="object_rl_benefits", layer="arch", lane="obj_centric", row="ocrl", path="trunk", size="sm", cited_by_count=120),
    EvolutionPaper(id="owm_meets_policy", title="OWM Meets Policy", year=2025, quarter=4, paradigm="object_policy", layer="arch", lane="obj_centric", row="ocrl", path="trunk", size="sm", builds_on=["slotformer"], cited_by_count=91),
    EvolutionPaper(id="oc_latent_action", title="OC Latent Action", year=2025, quarter=1, paradigm="object_latent_actions", layer="arch", lane="obj_centric", row="ocrl", path="trunk", size="sm", cited_by_count=0),

    # Row: causal_compositional
    EvolutionPaper(id="compositional_ocl", title="Compositional OCL", year=2024, quarter=1, paradigm="causal_object", layer="arch", lane="obj_centric", row="causal_compositional", path="trunk", size="sm", cited_by_count=8),
    EvolutionPaper(id="oc_repr_generalize", title="OC Repr Generalize", year=2025, quarter=1, paradigm="compositional_generalization", layer="arch", lane="obj_centric", row="causal_compositional", path="trunk", size="sm", builds_on=["slot_attention"], cited_by_count=10),

]

ITERATIONS = [
    IterationDef(
        id="jepa_evo",
        title="JEPA Evolution",
        subtitle="Joint Embedding → Video → Sequential Prediction",
        path="trunk",
        row="jepa_family",
        papers=["i_jepa", "v_jepa", "v_jepa_2"],
        mutations={
            "i_jepa": IterationMutation(
                summary="Image-level Joint Embedding Predictive Architecture",
                detail="在潜空间中预测masked patch表征，而非像素重建。",
                bottleneck="MAE等像素级重建学到低级纹理而非语义",
                result="ImageNet linear probe达到SOTA，学习高语义表征",
            ),
            "v_jepa": IterationMutation(
                summary="扩展至视频时序预测",
                detail="在视频中预测未来帧的潜空间表征，学习时序动力学。",
                bottleneck="I-JEPA仅处理静态图像，无法建模时序因果",
                result="视频理解任务zero-shot超越VideoMAE",
            ),
            "v_jepa_2": IterationMutation(
                summary="统一视觉+动作表征",
                detail="融合动作信号实现可交互的世界模型，支持规划。",
                bottleneck="V-JEPA是纯观测模型，无法做action-conditioned prediction",
                result="机器人操作任务实现sample-efficient planning",
            ),
        },
    ),
    IterationDef(
        id="dreamer_evo",
        title="Dreamer Evolution",
        subtitle="Imagination-Based RL: V1 → V2 → V3",
        path="trunk",
        row="dreamer_series",
        papers=["dreamer_v1", "dreamer_v2", "dreamer_v3"],
        mutations={
            "dreamer_v1": IterationMutation(
                summary="首个端到端想象力驱动策略学习",
                detail="在learned latent dynamics中rollout虚拟轨迹训练policy。",
                bottleneck="Model-free RL需要海量真实交互，sample efficiency极低",
                result="连续控制任务达到model-free方法同等性能但减少10×交互量",
            ),
            "dreamer_v2": IterationMutation(
                summary="离散化潜空间 + Actor-Critic",
                detail="将latent state改为categorical分布，增加image reconstruction稳定性。",
                bottleneck="V1的Gaussian latent在复杂环境中posterior collapse",
                result="Atari 200M benchmark首次超越model-free SOTA",
            ),
            "dreamer_v3": IterationMutation(
                summary="通用化 — 单一架构跨所有domain",
                detail="Symlog predictions + 固定超参数，不再需要per-domain调参。",
                bottleneck="V2每个新domain需要重新tuning，泛化性差",
                result="150+环境零调参达到或超越domain-specific baselines",
            ),
        },
    ),
    IterationDef(
        id="tdmpc_evo",
        title="TD-MPC Evolution",
        subtitle="Temporal Difference + Model Predictive Control",
        path="trunk",
        row="tdmpc_series",
        papers=["tdmpc", "tdmpc2", "pwm"],
        mutations={
            "tdmpc": IterationMutation(
                summary="TD学习 + 模型预测控制的首次融合",
                detail="联合学习value function和dynamics model，用MPC做planning。",
                bottleneck="纯model-based方法compound error，纯model-free需要大量交互",
                result="连续控制benchmark超越SAC/TD3等model-free基线",
            ),
            "tdmpc2": IterationMutation(
                summary="多任务规模化 + 鲁棒性",
                detail="统一的多任务world model，单一模型处理80+不同任务。",
                bottleneck="TD-MPC需要per-task training，无法泛化",
                result="80+任务单模型达到或超越per-task specialists",
            ),
            "pwm": IterationMutation(
                summary="Policy Learning with Multi-task World Models",
                detail="在TD-MPC2基础上进一步探索策略学习范式。",
                bottleneck="MPC在线计算开销大，需要高效策略提取",
                result="保持world model优势同时降低推理时计算开销",
            ),
        },
    ),
    IterationDef(
        id="slot_evo",
        title="Slot Attention Evolution",
        subtitle="Object Discovery → Dynamics → Language-guided",
        path="trunk",
        row="slot_attention",
        papers=["slot_attention", "slotformer", "lslotformer"],
        mutations={
            "slot_attention": IterationMutation(
                summary="注意力机制驱动的对象发现",
                detail="通过竞争性注意力将场景分解为对象级slot表征。",
                bottleneck="像素级表征无法捕捉对象边界和组合结构",
                result="无监督对象分割达到接近监督方法的性能",
            ),
            "slotformer": IterationMutation(
                summary="对象级动力学预测",
                detail="在slot空间上用Transformer预测未来状态演化。",
                bottleneck="Slot Attention是静态的，无法建模时序交互",
                result="视频预测任务比像素级方法更准确且可解释",
            ),
            "lslotformer": IterationMutation(
                summary="语言引导的对象操作世界模型",
                detail="融合语言指令来条件化对象级动力学预测。",
                bottleneck="SlotFormer无法接受高层语义指令",
                result="语言指导下的机器人操作场景预测",
            ),
        },
    ),
]
