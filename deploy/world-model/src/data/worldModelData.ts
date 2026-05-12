// World Model Evolution Map - Hardcoded Data
// This file contains all the data needed for the visualization

export interface Lane { id: string; title: string; subtitle: string; color: string }
export interface Row { id: string; lane: string; title: string; subtitle: string }
export interface Paper {
  id: string; title: string; year: number; quarter: number
  paradigm: string; layer: string; lane: string; row: string
  path: string; size: string; builds_on: string[]
}
export interface Mutation { summary: string; detail: string; bottleneck?: string; result?: string }
export interface Iteration {
  id: string; title: string; subtitle: string; path: string; row: string
  papers: string[]
  mutations: Record<string, Mutation>
}
export interface MapData { lanes: Lane[]; rows: Row[]; papers: Paper[]; iterations: Iteration[] }

export const LANES: Lane[] = [
  { id: "obs_gen", title: "观测层生成式世界模型", subtitle: "Observation-Level Generative", color: "#2563EB" },
  { id: "latent_wm", title: "潜空间世界模型", subtitle: "Latent-Space WMs", color: "#7C3AED" },
  { id: "rl_wm", title: "强化学习驱动世界模型", subtitle: "RL-Based WMs", color: "#059669" },
  { id: "obj_centric", title: "对象中心世界模型", subtitle: "Object-Centric WMs", color: "#EA580C" },
]

export const ROWS: Row[] = [
  // Lane A: RL-Based World Models
  { id: "dreamer_series", lane: "rl_wm", title: "A-1 Dreamer Series", subtitle: "Imagination → Policy" },
  { id: "dreamer_variants", lane: "rl_wm", title: "A-2 Dreamer Variants", subtitle: "Task-specific Extensions" },
  { id: "tdmpc_series", lane: "rl_wm", title: "A-3 TD-MPC Series", subtitle: "TD + Model Predictive Control" },
  { id: "hierarchical_wm", lane: "rl_wm", title: "A-4 Hierarchical WMs", subtitle: "Temporal Abstraction" },
  { id: "multi_agent", lane: "rl_wm", title: "A-5 Multi-Agent & Collaborative", subtitle: "Multi-agent Dynamics" },
  { id: "specialized_rl", lane: "rl_wm", title: "A-6 Specialized Variants", subtitle: "Memory / Offline / Robustness" },
  { id: "imagination_robotics", lane: "rl_wm", title: "A-7 Imagination for Robotics", subtitle: "Video Prediction → Action" },

  // Lane B: Observation-Level Generative
  { id: "language_wm", lane: "obs_gen", title: "B-1 Language WMs", subtitle: "LLM as World Simulator" },
  { id: "video_generation", lane: "obs_gen", title: "B-2 Video Generation", subtitle: "Diffusion Video" },
  { id: "autoregressive_video", lane: "obs_gen", title: "B-3 Autoregressive Video", subtitle: "AR Multimodal" },
  { id: "interactive_worlds", lane: "obs_gen", title: "B-4 Interactive Worlds", subtitle: "Playable / Game" },
  { id: "3d_4d_generation", lane: "obs_gen", title: "B-5 3D/4D Generation", subtitle: "Scene Synthesis" },
  { id: "embodied_generation", lane: "obs_gen", title: "B-6 Embodied Generation", subtitle: "4D Robotics Video/Physics" },

  // Lane C: Latent-Space World Models
  { id: "jepa_family", lane: "latent_wm", title: "C-1 JEPA Family", subtitle: "Joint Embedding Prediction" },
  { id: "dino_features", lane: "latent_wm", title: "C-2 DINO-based WMs", subtitle: "Pre-trained Visual Features" },
  { id: "structured_latent", lane: "latent_wm", title: "C-3 Structured Latent", subtitle: "Group / Tokenized" },

  // Lane D: Object-Centric World Models
  { id: "slot_attention", lane: "obj_centric", title: "D-1 Slot Attention", subtitle: "Object Discovery" },
  { id: "structured_dynamics", lane: "obj_centric", title: "D-2 Structured Dynamics", subtitle: "Object Interaction" },
  { id: "ocrl", lane: "obj_centric", title: "D-3 Object-Centric RL", subtitle: "OC + Policy Learning" },
  { id: "causal_compositional", lane: "obj_centric", title: "D-4 Causal & Compositional", subtitle: "Causal Object Repr" },
]

export const PAPERS: Paper[] = [
  // Lane A: RL-Based World Models
  { id: "planet", title: "PlaNet", year: 2019, quarter: 2, paradigm: "rssm", layer: "arch", lane: "rl_wm", row: "dreamer_series", path: "trunk", size: "lg", builds_on: [] },
  { id: "dreamer_v1", title: "Dreamer V1", year: 2020, quarter: 1, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_series", path: "trunk", size: "lg", builds_on: ["planet"] },
  { id: "dreamer_v2", title: "Dreamer V2", year: 2021, quarter: 1, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_series", path: "trunk", size: "lg", builds_on: ["dreamer_v1"] },
  { id: "dreamer_v3", title: "Dreamer V3", year: 2025, quarter: 1, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_series", path: "trunk", size: "lg", builds_on: ["dreamer_v2"] },
  { id: "dreamsmooth", title: "DreamSmooth", year: 2024, quarter: 1, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_variants", path: "trunk", size: "sm", builds_on: ["dreamer_v1"] },
  { id: "pigdreamer", title: "PIGDreamer", year: 2025, quarter: 3, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_variants", path: "trunk", size: "sm", builds_on: ["dreamer_v1"] },
  { id: "harmonydream", title: "HarmonyDream", year: 2024, quarter: 2, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_variants", path: "trunk", size: "sm", builds_on: ["dreamer_v1"] },
  { id: "dymodreamer", title: "DyMoDreamer", year: 2025, quarter: 4, paradigm: "imagination_rl", layer: "arch", lane: "rl_wm", row: "dreamer_variants", path: "trunk", size: "sm", builds_on: ["dreamer_v1"] },
  { id: "tdmpc", title: "TD-MPC", year: 2022, quarter: 2, paradigm: "model_based_rl", layer: "arch", lane: "rl_wm", row: "tdmpc_series", path: "trunk", size: "lg", builds_on: [] },
  { id: "tdmpc2", title: "TD-MPC2", year: 2024, quarter: 1, paradigm: "model_based_rl", layer: "arch", lane: "rl_wm", row: "tdmpc_series", path: "trunk", size: "lg", builds_on: ["tdmpc"] },
  { id: "pwm", title: "PWM", year: 2025, quarter: 1, paradigm: "model_based_rl", layer: "arch", lane: "rl_wm", row: "tdmpc_series", path: "trunk", size: "md", builds_on: ["tdmpc2"] },
  { id: "iq_mpc", title: "IQ-MPC", year: 2025, quarter: 2, paradigm: "model_based_rl", layer: "arch", lane: "rl_wm", row: "tdmpc_series", path: "trunk", size: "sm", builds_on: ["tdmpc"] },
  { id: "hieros", title: "Hieros", year: 2024, quarter: 2, paradigm: "hierarchical_rl", layer: "arch", lane: "rl_wm", row: "hierarchical_wm", path: "trunk", size: "md", builds_on: ["dreamer_v1"] },
  { id: "thick", title: "THICK", year: 2024, quarter: 1, paradigm: "hierarchical_rl", layer: "arch", lane: "rl_wm", row: "hierarchical_wm", path: "trunk", size: "md", builds_on: ["dreamer_v2"] },
  { id: "dima", title: "DIMA", year: 2025, quarter: 4, paradigm: "multi_agent_wm", layer: "arch", lane: "rl_wm", row: "multi_agent", path: "trunk", size: "md", builds_on: [] },
  { id: "coworld", title: "CoWorld", year: 2024, quarter: 4, paradigm: "collaborative_wm", layer: "arch", lane: "rl_wm", row: "multi_agent", path: "trunk", size: "md", builds_on: ["dreamer_v1"] },
  { id: "r2i", title: "R2I", year: 2024, quarter: 1, paradigm: "memory_augmented", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "md", builds_on: [] },
  { id: "leq", title: "LEQ", year: 2025, quarter: 1, paradigm: "offline_model_based", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "sm", builds_on: [] },
  { id: "pcm", title: "PCM", year: 2024, quarter: 2, paradigm: "generalization", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "sm", builds_on: [] },
  { id: "waker", title: "WAKER", year: 2024, quarter: 1, paradigm: "curriculum_learning", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "sm", builds_on: [] },
  { id: "rem", title: "REM", year: 2024, quarter: 2, paradigm: "tokenized_wm", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "sm", builds_on: [] },
  { id: "crssm", title: "cRSSM", year: 2024, quarter: 1, paradigm: "zero_shot", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "sm", builds_on: ["dreamer_v2"] },
  { id: "adaptive_wm", title: "Adaptive WM", year: 2024, quarter: 4, paradigm: "non_stationary", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "sm", builds_on: ["dreamer_v1"] },
  { id: "mosim", title: "MoSim", year: 2025, quarter: 2, paradigm: "simulation", layer: "arch", lane: "rl_wm", row: "specialized_rl", path: "trunk", size: "md", builds_on: [] },
  { id: "robodreamer", title: "RoboDreamer", year: 2024, quarter: 2, paradigm: "robot_imagination", layer: "arch", lane: "rl_wm", row: "imagination_robotics", path: "trunk", size: "md", builds_on: [] },
  { id: "vipra", title: "ViPRA", year: 2025, quarter: 4, paradigm: "video_prediction_rl", layer: "arch", lane: "rl_wm", row: "imagination_robotics", path: "trunk", size: "md", builds_on: [] },
  { id: "flowdreamer", title: "FlowDreamer", year: 2025, quarter: 2, paradigm: "flow_motion_wm", layer: "arch", lane: "rl_wm", row: "imagination_robotics", path: "trunk", size: "sm", builds_on: [] },

  // Lane B: Observation-Level Generative
  { id: "gpt4", title: "GPT-4", year: 2023, quarter: 1, paradigm: "llm_world_model", layer: "arch", lane: "obs_gen", row: "language_wm", path: "trunk", size: "lg", builds_on: [] },
  { id: "llama3", title: "LLaMA 3", year: 2024, quarter: 3, paradigm: "llm_world_model", layer: "arch", lane: "obs_gen", row: "language_wm", path: "trunk", size: "lg", builds_on: ["gpt4"] },
  { id: "llmcwm", title: "LLMCWM", year: 2025, quarter: 1, paradigm: "causal_llm", layer: "arch", lane: "obs_gen", row: "language_wm", path: "trunk", size: "md", builds_on: [] },
  { id: "rap", title: "RAP", year: 2023, quarter: 4, paradigm: "reasoning_planning", layer: "arch", lane: "obs_gen", row: "language_wm", path: "trunk", size: "md", builds_on: [] },
  { id: "bytesized32", title: "ByteSized32", year: 2024, quarter: 2, paradigm: "text_simulator", layer: "arch", lane: "obs_gen", row: "language_wm", path: "trunk", size: "sm", builds_on: [] },
  { id: "sora", title: "Sora", year: 2024, quarter: 1, paradigm: "diffusion_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "lg", builds_on: [] },
  { id: "gen3", title: "Gen-3 Alpha", year: 2024, quarter: 2, paradigm: "diffusion_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "lg", builds_on: ["sora"] },
  { id: "wan", title: "Wan (Alibaba)", year: 2025, quarter: 1, paradigm: "diffusion_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "lg", builds_on: ["sora"] },
  { id: "cosmos", title: "Cosmos (NVIDIA)", year: 2025, quarter: 1, paradigm: "diffusion_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "lg", builds_on: ["sora"] },
  { id: "t2v_turbo", title: "T2V-Turbo", year: 2024, quarter: 4, paradigm: "efficient_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "sm", builds_on: ["sora"] },
  { id: "spmem", title: "SPMEM", year: 2025, quarter: 4, paradigm: "memory_augmented_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "videocrafter2", title: "VideoCrafter2", year: 2024, quarter: 2, paradigm: "data_efficient_video", layer: "arch", lane: "obs_gen", row: "video_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "emu3", title: "Emu3", year: 2024, quarter: 3, paradigm: "ar_video", layer: "arch", lane: "obs_gen", row: "autoregressive_video", path: "trunk", size: "md", builds_on: [] },
  { id: "llava", title: "LLaVA", year: 2023, quarter: 4, paradigm: "vlm", layer: "arch", lane: "obs_gen", row: "autoregressive_video", path: "trunk", size: "md", builds_on: [] },
  { id: "genie2", title: "Genie 2", year: 2024, quarter: 4, paradigm: "interactive_video", layer: "arch", lane: "obs_gen", row: "interactive_worlds", path: "game", size: "lg", builds_on: ["sora"] },
  { id: "oasis", title: "Oasis", year: 2024, quarter: 3, paradigm: "game_world_model", layer: "arch", lane: "obs_gen", row: "interactive_worlds", path: "game", size: "md", builds_on: [] },
  { id: "teleworld", title: "TeleWorld", year: 2025, quarter: 3, paradigm: "long_video", layer: "sys", lane: "obs_gen", row: "interactive_worlds", path: "trunk", size: "md", builds_on: ["sora"] },
  { id: "vid2world", title: "Vid2World", year: 2025, quarter: 2, paradigm: "video_to_world", layer: "arch", lane: "obs_gen", row: "interactive_worlds", path: "trunk", size: "md", builds_on: ["sora"] },
  { id: "cola_world", title: "CoLA-World", year: 2025, quarter: 4, paradigm: "latent_action", layer: "arch", lane: "obs_gen", row: "interactive_worlds", path: "trunk", size: "sm", builds_on: [] },
  { id: "text2room", title: "Text2Room", year: 2023, quarter: 3, paradigm: "text_to_3d", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "4dfy", title: "4D-fy", year: 2024, quarter: 2, paradigm: "text_to_4d", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "md", builds_on: ["text2room"] },
  { id: "wonderjourney", title: "WonderJourney", year: 2024, quarter: 2, paradigm: "perpetual_3d", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "scenescape", title: "SceneScape", year: 2023, quarter: 4, paradigm: "scene_generation", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "wonderworld", title: "WonderWorld", year: 2025, quarter: 2, paradigm: "image_to_3d", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "lg", builds_on: ["wonderjourney", "text2room"] },
  { id: "lidar_crafter", title: "LiDARCrafter", year: 2025, quarter: 2, paradigm: "lidar_4d", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "invisible_stitch", title: "Invisible Stitch", year: 2024, quarter: 1, paradigm: "depth_inpainting", layer: "arch", lane: "obs_gen", row: "3d_4d_generation", path: "trunk", size: "sm", builds_on: [] },
  { id: "grounding_video", title: "Grounding Video", year: 2025, quarter: 1, paradigm: "video_to_action", layer: "arch", lane: "obs_gen", row: "embodied_generation", path: "trunk", size: "md", builds_on: ["sora"] },
  { id: "tesseract", title: "TesserAct", year: 2025, quarter: 2, paradigm: "4d_embodied", layer: "arch", lane: "obs_gen", row: "embodied_generation", path: "trunk", size: "md", builds_on: ["4dfy"] },
  { id: "orv", title: "ORV", year: 2025, quarter: 2, paradigm: "occupancy_4d", layer: "arch", lane: "obs_gen", row: "embodied_generation", path: "trunk", size: "md", builds_on: ["tesseract"] },
  { id: "wristworld", title: "WristWorld", year: 2025, quarter: 4, paradigm: "wrist_view_4d", layer: "arch", lane: "obs_gen", row: "embodied_generation", path: "trunk", size: "sm", builds_on: ["tesseract"] },
  { id: "irasim", title: "IRASim", year: 2025, quarter: 4, paradigm: "detailed_robot_wm", layer: "arch", lane: "obs_gen", row: "embodied_generation", path: "trunk", size: "md", builds_on: [] },
  { id: "wisa", title: "WISA", year: 2025, quarter: 4, paradigm: "physics_video_wm", layer: "arch", lane: "obs_gen", row: "embodied_generation", path: "trunk", size: "md", builds_on: [] },

  // Lane C: Latent-Space World Models
  { id: "i_jepa", title: "I-JEPA", year: 2023, quarter: 2, paradigm: "joint_embedding", layer: "arch", lane: "latent_wm", row: "jepa_family", path: "trunk", size: "lg", builds_on: [] },
  { id: "v_jepa", title: "V-JEPA", year: 2024, quarter: 1, paradigm: "joint_embedding_video", layer: "arch", lane: "latent_wm", row: "jepa_family", path: "trunk", size: "lg", builds_on: ["i_jepa"] },
  { id: "v_jepa_2", title: "V-JEPA 2", year: 2025, quarter: 2, paradigm: "jepa_planning", layer: "arch", lane: "latent_wm", row: "jepa_family", path: "trunk", size: "lg", builds_on: ["v_jepa"] },
  { id: "seq_jepa", title: "seq-JEPA", year: 2025, quarter: 4, paradigm: "sequential_jepa", layer: "arch", lane: "latent_wm", row: "jepa_family", path: "trunk", size: "md", builds_on: ["v_jepa"] },
  { id: "mc_jepa", title: "MC-JEPA", year: 2023, quarter: 3, paradigm: "motion_content", layer: "arch", lane: "latent_wm", row: "jepa_family", path: "trunk", size: "sm", builds_on: [] },
  { id: "dino_wm", title: "DINO-WM", year: 2025, quarter: 3, paradigm: "feature_world_model", layer: "arch", lane: "latent_wm", row: "dino_features", path: "trunk", size: "md", builds_on: [] },
  { id: "dino_world", title: "DINO-World", year: 2025, quarter: 3, paradigm: "dino_video_wm", layer: "arch", lane: "latent_wm", row: "dino_features", path: "trunk", size: "md", builds_on: ["dino_wm"] },
  { id: "dino_foresight", title: "DINO-Foresight", year: 2025, quarter: 4, paradigm: "dino_future_prediction", layer: "arch", lane: "latent_wm", row: "dino_features", path: "trunk", size: "md", builds_on: ["dino_wm"] },
  { id: "world_models_group_latents", title: "WM Group Latents", year: 2025, quarter: 2, paradigm: "group_structure", layer: "arch", lane: "latent_wm", row: "structured_latent", path: "trunk", size: "md", builds_on: [] },
  { id: "lwm", title: "LWM", year: 2025, quarter: 1, paradigm: "long_context_wm", layer: "arch", lane: "latent_wm", row: "structured_latent", path: "trunk", size: "md", builds_on: [] },

  // Lane D: Object-Centric World Models
  { id: "slot_attention", title: "Slot Attention", year: 2020, quarter: 3, paradigm: "object_discovery", layer: "arch", lane: "obj_centric", row: "slot_attention", path: "trunk", size: "lg", builds_on: [] },
  { id: "slotformer", title: "SlotFormer", year: 2023, quarter: 1, paradigm: "object_dynamics", layer: "arch", lane: "obj_centric", row: "slot_attention", path: "trunk", size: "md", builds_on: ["slot_attention"] },
  { id: "lslotformer", title: "LSlotFormer", year: 2025, quarter: 1, paradigm: "language_object_wm", layer: "arch", lane: "obj_centric", row: "slot_attention", path: "trunk", size: "md", builds_on: ["slotformer"] },
  { id: "mead", title: "MEAD", year: 2025, quarter: 1, paradigm: "exploration_object", layer: "arch", lane: "obj_centric", row: "slot_attention", path: "trunk", size: "md", builds_on: ["slotformer"] },
  { id: "dyn_o", title: "Dyn-O", year: 2025, quarter: 4, paradigm: "structured_object_wm", layer: "arch", lane: "obj_centric", row: "structured_dynamics", path: "trunk", size: "md", builds_on: ["slotformer"] },
  { id: "g_swm", title: "G-SWM", year: 2020, quarter: 3, paradigm: "generative_object", layer: "arch", lane: "obj_centric", row: "structured_dynamics", path: "trunk", size: "sm", builds_on: [] },
  { id: "carformer", title: "CarFormer", year: 2025, quarter: 2, paradigm: "object_centric_autonomous", layer: "arch", lane: "obj_centric", row: "ocrl", path: "trunk", size: "md", builds_on: [] },
  { id: "focus", title: "FOCUS", year: 2025, quarter: 1, paradigm: "oc_planning", layer: "arch", lane: "obj_centric", row: "ocrl", path: "trunk", size: "md", builds_on: [] },
  { id: "fioc_wm", title: "FIOC-WM", year: 2024, quarter: 4, paradigm: "oc_rl", layer: "arch", lane: "obj_centric", row: "ocrl", path: "trunk", size: "sm", builds_on: [] },
  { id: "objects_matter", title: "Objects Matter", year: 2024, quarter: 2, paradigm: "oc_robotics", layer: "arch", lane: "obj_centric", row: "ocrl", path: "trunk", size: "sm", builds_on: [] },
  { id: "owm_meets_policy", title: "OWM Meets Policy", year: 2024, quarter: 1, paradigm: "oc_policy", layer: "arch", lane: "obj_centric", row: "ocrl", path: "trunk", size: "sm", builds_on: [] },
  { id: "oc_latent_action", title: "OC Latent Action", year: 2025, quarter: 1, paradigm: "oc_action_space", layer: "arch", lane: "obj_centric", row: "ocrl", path: "trunk", size: "sm", builds_on: [] },
  { id: "compositional_ocl", title: "Compositional OCL", year: 2024, quarter: 1, paradigm: "causal_object", layer: "arch", lane: "obj_centric", row: "causal_compositional", path: "trunk", size: "sm", builds_on: [] },
  { id: "oc_repr_generalize", title: "OC Repr Generalize", year: 2025, quarter: 1, paradigm: "compositional_generalization", layer: "arch", lane: "obj_centric", row: "causal_compositional", path: "trunk", size: "sm", builds_on: ["slot_attention"] },
]

export const ITERATIONS: Iteration[] = [
  {
    id: "jepa_evo",
    title: "JEPA Evolution",
    subtitle: "Joint Embedding → Video → Sequential Prediction",
    path: "trunk",
    row: "jepa_family",
    papers: ["i_jepa", "v_jepa", "v_jepa_2"],
    mutations: {
      "i_jepa": {
        summary: "Image-level Joint Embedding Predictive Architecture",
        detail: "在潜空间中预测masked patch表征，而非像素重建。",
        bottleneck: "MAE等像素级重建学到低级纹理而非语义",
        result: "ImageNet linear probe达到SOTA，学习高语义表征",
      },
      "v_jepa": {
        summary: "扩展至视频时序预测",
        detail: "在视频中预测未来帧的潜空间表征，学习时序动力学。",
        bottleneck: "I-JEPA仅处理静态图像，无法建模时序因果",
        result: "视频理解任务zero-shot超越VideoMAE",
      },
      "v_jepa_2": {
        summary: "统一视觉+动作表征",
        detail: "融合动作信号实现可交互的世界模型，支持规划。",
        bottleneck: "V-JEPA是纯观测模型，无法做action-conditioned prediction",
        result: "机器人操作任务实现sample-efficient planning",
      },
    },
  },
  {
    id: "dreamer_evo",
    title: "Dreamer Evolution",
    subtitle: "Imagination-Based RL: V1 → V2 → V3",
    path: "trunk",
    row: "dreamer_series",
    papers: ["dreamer_v1", "dreamer_v2", "dreamer_v3"],
    mutations: {
      "dreamer_v1": {
        summary: "首个端到端想象力驱动策略学习",
        detail: "在learned latent dynamics中rollout虚拟轨迹训练policy。",
        bottleneck: "Model-free RL需要海量真实交互，sample efficiency极低",
        result: "连续控制任务达到model-free方法同等性能但减少10×交互量",
      },
      "dreamer_v2": {
        summary: "离散化潜空间 + Actor-Critic",
        detail: "将latent state改为categorical分布，增加image reconstruction稳定性。",
        bottleneck: "V1的Gaussian latent在复杂环境中posterior collapse",
        result: "Atari 200M benchmark首次超越model-free SOTA",
      },
      "dreamer_v3": {
        summary: "通用化 — 单一架构跨所有domain",
        detail: "Symlog predictions + 固定超参数，不再需要per-domain调参。",
        bottleneck: "V2每个新domain需要重新tuning，泛化性差",
        result: "150+环境零调参达到或超越domain-specific baselines",
      },
    },
  },
  {
    id: "tdmpc_evo",
    title: "TD-MPC Evolution",
    subtitle: "Temporal Difference + Model Predictive Control",
    path: "trunk",
    row: "tdmpc_series",
    papers: ["tdmpc", "tdmpc2", "pwm"],
    mutations: {
      "tdmpc": {
        summary: "TD学习 + 模型预测控制的首次融合",
        detail: "联合学习value function和dynamics model，用MPC做planning。",
        bottleneck: "纯model-based方法compound error，纯model-free需要大量交互",
        result: "连续控制benchmark超越SAC/TD3等model-free基线",
      },
      "tdmpc2": {
        summary: "多任务规模化 + 鲁棒性",
        detail: "统一的多任务world model，单一模型处理80+不同任务。",
        bottleneck: "TD-MPC需要per-task training，无法泛化",
        result: "80+任务单模型达到或超越per-task specialists",
      },
      "pwm": {
        summary: "Policy Learning with Multi-task World Models",
        detail: "在TD-MPC2基础上进一步探索策略学习范式。",
        bottleneck: "MPC在线计算开销大，需要高效策略提取",
        result: "保持world model优势同时降低推理时计算开销",
      },
    },
  },
  {
    id: "slot_evo",
    title: "Slot Attention Evolution",
    subtitle: "Object Discovery → Dynamics → Language-guided",
    path: "trunk",
    row: "slot_attention",
    papers: ["slot_attention", "slotformer", "lslotformer"],
    mutations: {
      "slot_attention": {
        summary: "注意力机制驱动的对象发现",
        detail: "通过竞争性注意力将场景分解为对象级slot表征。",
        bottleneck: "像素级表征无法捕捉对象边界和组合结构",
        result: "无监督对象分割达到接近监督方法的性能",
      },
      "slotformer": {
        summary: "对象级动力学预测",
        detail: "在slot空间上用Transformer预测未来状态演化。",
        bottleneck: "Slot Attention是静态的，无法建模时序交互",
        result: "视频预测任务比像素级方法更准确且可解释",
      },
      "lslotformer": {
        summary: "语言引导的对象操作世界模型",
        detail: "融合语言指令来条件化对象级动力学预测。",
        bottleneck: "SlotFormer无法接受高层语义指令",
        result: "语言指导下的机器人操作场景预测",
      },
    },
  },
]

// Application domain colors — 6 tracks, investor-first encoding
export const APPLICATION_COLORS: Record<string, string> = {
  video_gen: '#2563EB',
  autonomous_driving: '#EA580C',
  robotics: '#059669',
  spatial: '#7C3AED',
  game_vr: '#DC2626',
  drone: '#475569',
}

// Map paper IDs to application domain
export const PAPER_APPLICATION: Record<string, string> = {
  planet: 'robotics', dreamer_v1: 'robotics', dreamer_v2: 'robotics', dreamer_v3: 'robotics',
  dreamsmooth: 'robotics', pigdreamer: 'robotics', harmonydream: 'robotics', dymodreamer: 'robotics',
  tdmpc: 'robotics', tdmpc2: 'robotics', pwm: 'robotics', iq_mpc: 'robotics',
  hieros: 'robotics', thick: 'robotics',
  dima: 'robotics', coworld: 'robotics',
  r2i: 'robotics', leq: 'robotics', pcm: 'robotics', waker: 'robotics',
  rem: 'robotics', crssm: 'robotics', adaptive_wm: 'robotics', mosim: 'robotics',
  robodreamer: 'robotics', vipra: 'robotics', flowdreamer: 'robotics',
  gpt4: 'video_gen', llama3: 'video_gen',
  llmcwm: 'spatial', rap: 'spatial', bytesized32: 'game_vr',
  sora: 'video_gen', gen3: 'video_gen', wan: 'video_gen', cosmos: 'video_gen',
  t2v_turbo: 'video_gen', spmem: 'video_gen', videocrafter2: 'video_gen',
  emu3: 'video_gen', llava: 'video_gen',
  genie2: 'game_vr', oasis: 'game_vr',
  teleworld: 'video_gen', vid2world: 'video_gen', cola_world: 'video_gen',
  text2room: 'spatial', '4dfy': 'spatial', wonderjourney: 'spatial',
  scenescape: 'spatial', wonderworld: 'spatial',
  lidar_crafter: 'autonomous_driving', invisible_stitch: 'spatial',
  i_jepa: 'spatial', v_jepa: 'spatial', v_jepa_2: 'robotics',
  seq_jepa: 'spatial', mc_jepa: 'spatial',
  dino_wm: 'robotics', dino_world: 'robotics', dino_foresight: 'robotics',
  world_models_group_latents: 'spatial', lwm: 'video_gen',
  slot_attention: 'spatial', slotformer: 'spatial',
  lslotformer: 'robotics', mead: 'robotics',
  dyn_o: 'spatial', g_swm: 'spatial',
  carformer: 'autonomous_driving', focus: 'robotics',
  fioc_wm: 'robotics', objects_matter: 'robotics',
  owm_meets_policy: 'robotics', oc_latent_action: 'robotics',
  compositional_ocl: 'spatial', oc_repr_generalize: 'spatial',
  grounding_video: 'robotics', tesseract: 'robotics', orv: 'robotics',
  wristworld: 'robotics', irasim: 'robotics', wisa: 'robotics',
}

// Map paper IDs to player/org
export const PAPER_PLAYER: Record<string, string> = {
  planet: 'DeepMind', dreamer_v1: 'DeepMind', dreamer_v2: 'DeepMind', dreamer_v3: 'DeepMind',
  dreamsmooth: 'DeepMind', pigdreamer: 'DeepMind', harmonydream: 'DeepMind', dymodreamer: 'DeepMind',
  genie2: 'DeepMind', hieros: 'DeepMind', thick: 'DeepMind',
  sora: 'OpenAI', gpt4: 'OpenAI',
  i_jepa: 'Meta', v_jepa: 'Meta', v_jepa_2: 'Meta', seq_jepa: 'Meta', mc_jepa: 'Meta',
  llama3: 'Meta', dino_wm: 'Meta', dino_world: 'Meta', dino_foresight: 'Meta',
  cosmos: 'NVIDIA', gen3: 'Runway', wan: 'Alibaba', teleworld: 'Tencent',
  tdmpc: 'UC Berkeley', tdmpc2: 'UC Berkeley', pwm: 'UC Berkeley',
  slot_attention: 'Google Brain', slotformer: 'NUS',
  tesseract: 'MIT', llava: 'UW-Madison',
}

// Layer shapes
export const LAYER_SHAPES: Record<string, string> = {
  arch: 'circle', sys: 'square', infer: 'diamond', train: 'triangle', memory: 'hexagon',
}

// Time range
export const START_YEAR = 2020
export const END_YEAR = 2027
export const TOTAL_QUARTERS = (END_YEAR - START_YEAR) * 4

// Helper functions
export function qToX(year: number, quarter: number): number {
  return ((year - START_YEAR) * 4 + (quarter - 1)) / TOTAL_QUARTERS * 100
}

export function getNodeSize(size: string): number {
  return size === 'lg' ? 10 : size === 'md' ? 7 : 5
}

export function getNodeColor(paperId: string): string {
  const app = PAPER_APPLICATION[paperId]
  if (app) return APPLICATION_COLORS[app]
  return '#6B7280'
}

export function getPlayerLabel(paperId: string): string {
  return PAPER_PLAYER[paperId] || ''
}

export function yearRange(): string[] {
  const years: string[] = []
  for (let y = START_YEAR; y < END_YEAR; y++) years.push(String(y))
  return years
}

// Complete map data
export const MAP_DATA: MapData = {
  lanes: LANES,
  rows: ROWS,
  papers: PAPERS,
  iterations: ITERATIONS,
}
