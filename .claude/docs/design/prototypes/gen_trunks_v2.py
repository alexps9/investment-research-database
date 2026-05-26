#!/usr/bin/env python3
"""Generate trunks-v2-fork-confluence prototype HTML.

Key visual pattern (from topic-view-exploration.html #1):
- Each lane has a TRUNK LINE (thick horizontal path)
- Forks peel off from trunk with tight Bezier then continue horizontal
- Cross-lane arcs are dashed with labels
- Confluence = diamond node where multiple lines merge
"""

W = 1200
H = 580
MARGIN_L = 90
MARGIN_R = 30
YEAR_MIN = 2019
YEAR_MAX = 2026.5

LANES = [
    {"id": "video_gen", "title": "Video-Generative", "color": "#2563EB", "y": 90},
    {"id": "rl_based", "title": "RL-Based", "color": "#059669", "y": 230},
    {"id": "latent_space", "title": "Latent-Space", "color": "#7C3AED", "y": 370},
    {"id": "vla", "title": "Policy/VLA", "color": "#EA580C", "y": 500},
]

def year_to_x(year):
    return MARGIN_L + (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN) * (W - MARGIN_L - MARGIN_R)

def node_r(impact):
    if impact >= 80: return 7
    if impact >= 60: return 5
    return 4

# Each trunk is a named path with nodes on it
# trunk_y = lane center Y; fork branches get offset Y
TRUNKS = {
    # --- video_gen ---
    "vg_diffusion": {
        "lane": "video_gen", "y_off": 0, "color": "#2563EB",
        "width": 3, "opacity": 1,
        "nodes": [
            {"id": "sora", "title": "Sora", "year": 2024.0, "impact": 78},
            {"id": "drive_wm", "title": "Drive-WM", "year": 2024.2, "impact": 72},
            {"id": "wan", "title": "Wan", "year": 2025.2, "impact": 45},
            {"id": "cosmos", "title": "Cosmos", "year": 2025.0, "impact": 56},
        ],
    },
    "vg_video_policy": {
        "lane": "video_gen", "y_off": -30, "color": "#2563EB",
        "width": 1.8, "opacity": 0.5,
        "nodes": [
            {"id": "unipi", "title": "UniPi", "year": 2023.5, "impact": 81},
        ],
    },
    "vg_interactive": {
        "lane": "video_gen", "y_off": 30, "color": "#2563EB",
        "width": 2, "opacity": 0.5,
        "nodes": [
            {"id": "gamenngen", "title": "GameNGen", "year": 2024.5, "impact": 57},
            {"id": "genie2", "title": "Genie 2", "year": 2024.8, "impact": 55},
            {"id": "oasis", "title": "Oasis", "year": 2025.0, "impact": 40},
        ],
    },
    "vg_ar": {
        "lane": "video_gen", "y_off": -25, "color": "#2563EB",
        "width": 1.5, "opacity": 0.4,
        "nodes": [
            {"id": "emu3", "title": "Emu3", "year": 2024.7, "impact": 45},
            {"id": "lwm", "title": "LWM", "year": 2024.5, "impact": 67},
        ],
    },
    # --- rl_based ---
    "rl_rssm": {
        "lane": "rl_based", "y_off": 0, "color": "#059669",
        "width": 3, "opacity": 1,
        "nodes": [
            {"id": "planet", "title": "PlaNet", "year": 2019.5, "impact": 91},
            {"id": "dreamer_v1", "title": "Dreamer V1", "year": 2020.0, "impact": 89},
            {"id": "dreamer_v2", "title": "Dreamer V2", "year": 2021.0, "impact": 88},
            {"id": "dreamer_v3", "title": "Dreamer V3", "year": 2025.0, "impact": 84},
        ],
    },
    "rl_mpc": {
        "lane": "rl_based", "y_off": -28, "color": "#059669",
        "width": 2, "opacity": 0.5,
        "nodes": [
            {"id": "tdmpc", "title": "TD-MPC", "year": 2022.5, "impact": 74},
            {"id": "tdmpc2", "title": "TD-MPC2", "year": 2024.5, "impact": 71},
        ],
    },
    "rl_diffusion": {
        "lane": "rl_based", "y_off": 28, "color": "#059669",
        "width": 2, "opacity": 0.5,
        "nodes": [
            {"id": "diffuser", "title": "Diffuser", "year": 2022.5, "impact": 80},
            {"id": "decision_diffuser", "title": "DecisionDiff", "year": 2023.5, "impact": 67},
        ],
    },
    # --- latent_space ---
    "ls_jepa": {
        "lane": "latent_space", "y_off": 0, "color": "#7C3AED",
        "width": 3, "opacity": 1,
        "nodes": [
            {"id": "i_jepa", "title": "I-JEPA", "year": 2023.0, "impact": 85},
            {"id": "v_jepa", "title": "V-JEPA", "year": 2024.0, "impact": 80},
            {"id": "v_jepa2", "title": "V-JEPA 2", "year": 2025.0, "impact": 51},
        ],
    },
    "ls_slot": {
        "lane": "latent_space", "y_off": -28, "color": "#7C3AED",
        "width": 2, "opacity": 0.5,
        "nodes": [
            {"id": "slotattention", "title": "SlotAttn", "year": 2020.5, "impact": 92},
            {"id": "slotformer", "title": "SlotFormer", "year": 2023.5, "impact": 74},
        ],
    },
    # --- vla ---
    "vla_main": {
        "lane": "vla", "y_off": 0, "color": "#EA580C",
        "width": 3, "opacity": 1,
        "nodes": [
            {"id": "diffusion_policy", "title": "Diff Policy", "year": 2023.0, "impact": 88},
            {"id": "pi0", "title": "π0", "year": 2024.5, "impact": 70},
            {"id": "pi0_5", "title": "π0.5", "year": 2025.0, "impact": 55},
        ],
    },
    "vla_llm": {
        "lane": "vla", "y_off": -25, "color": "#EA580C",
        "width": 2, "opacity": 0.5,
        "nodes": [
            {"id": "rt2", "title": "RT-2", "year": 2023.5, "impact": 73},
            {"id": "octo", "title": "Octo", "year": 2024.0, "impact": 72},
        ],
    },
}

# Fork origins: (fork_trunk_id, from_trunk_id, fork_at_year)
# Only genuine forks (shared ancestor, then diverged)
FORKS = [
    ("rl_mpc", "rl_rssm", 2021.0),
    ("rl_diffusion", "rl_rssm", 2021.0),
]

# Confluence nodes (diamond, receives from multiple trunks)
# These are the "Two Threads Converging" nodes from 2024-2026
CONFLUENCES = [
    {
        "id": "unisim", "title": "UniSim", "year": 2024.2,
        "lane": "rl_based", "y_off": 35,
        "from_nodes": ["dreamer_v3", "sora"],
        "subtitle": "RL inside video WM",
    },
    {
        "id": "ar_dit", "title": "AR-DiT", "year": 2025.2,
        "lane": "video_gen", "y_off": 35,
        "from_nodes": ["dreamer_v3", "sora"],
        "subtitle": "diffusion goes causal",
    },
    {
        "id": "dreamgen", "title": "DreamGen", "year": 2025.3,
        "lane": "rl_based", "y_off": 35,
        "from_nodes": ["dreamer_v3", "cosmos"],
        "subtitle": "22 behaviors from 1 demo",
    },
    {
        "id": "dreamzero", "title": "DreamDojo/Zero", "year": 2025.8,
        "lane": "vla", "y_off": 20,
        "from_nodes": ["dreamer_v3", "cosmos"],
        "subtitle": "44K hrs + actions",
    },
]

# Cross-lane borrows (dashed arcs with label)
CROSS_BORROWS = [
    ("gamenngen", "sora", "borrows diffusion"),
]

# ---------- BUILD SVG ----------
lines = []
lines.append(f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px">')

# Lane bands
for lane in LANES:
    y = lane["y"] - 45
    lines.append(f'<rect x="0" y="{y}" width="{W}" height="90" fill="{lane["color"]}" opacity="0.02"/>')
    lines.append(f'<text x="10" y="{lane["y"]-32}" font-size="9" fill="{lane["color"]}" font-weight="700">{lane["title"]}</text>')

# Year grid
for yr in range(2019, 2027):
    x = year_to_x(yr)
    lines.append(f'<line x1="{x}" y1="15" x2="{x}" y2="{H-15}" stroke="#e4e4e7" stroke-width="0.5"/>')
    lines.append(f'<text x="{x}" y="{H-4}" text-anchor="middle" font-size="8" fill="#a1a1aa">{yr}</text>')

# Helper: get lane Y for a trunk
def trunk_y(trunk):
    lane = next(l for l in LANES if l["id"] == trunk["lane"])
    return lane["y"] + trunk["y_off"]

# Draw trunk lines (horizontal paths through nodes)
node_positions = {}  # id -> (x, y)

for tid, trunk in TRUNKS.items():
    ty = trunk_y(trunk)
    nodes = sorted(trunk["nodes"], key=lambda n: n["year"])
    if not nodes:
        continue
    x_start = year_to_x(nodes[0]["year"])
    x_end = year_to_x(nodes[-1]["year"])
    color = trunk["color"]
    # Trunk line
    lines.append(f'<path d="M{x_start},{ty} L{x_end},{ty}" stroke="{color}" stroke-width="{trunk["width"]}" fill="none" stroke-linecap="round" opacity="{trunk["opacity"]}"/>')
    # Nodes on trunk
    for n in nodes:
        x = year_to_x(n["year"])
        r = node_r(n["impact"])
        node_positions[n["id"]] = (x, ty)
        op = 0.8 if n["impact"] >= 70 else 0.5
        lines.append(f'<circle cx="{x}" cy="{ty}" r="{r}" fill="{color}" opacity="{op}" stroke="#fff" stroke-width="1.5"/>')
        lines.append(f'<text x="{x}" y="{ty+r+11}" text-anchor="middle" font-size="7" fill="{color}">{n["title"]}</text>')

# Draw fork arcs (peel off from parent trunk)
for fork_tid, parent_tid, fork_year in FORKS:
    fork_trunk = TRUNKS[fork_tid]
    parent_trunk = TRUNKS[parent_tid]
    parent_y = trunk_y(parent_trunk)
    fork_y_val = trunk_y(fork_trunk)
    fork_x = year_to_x(fork_year)
    first_node = sorted(fork_trunk["nodes"], key=lambda n: n["year"])[0]
    first_x = year_to_x(first_node["year"])
    color = fork_trunk["color"]
    # Bezier: start at fork point on parent trunk, curve to first node on fork
    # Tight arc style: horizontal first, then peel
    mid_x = fork_x + (first_x - fork_x) * 0.4
    lines.append(f'<path d="M{fork_x},{parent_y} C{mid_x},{parent_y} {mid_x},{fork_y_val} {first_x},{fork_y_val}" stroke="{color}" stroke-width="{fork_trunk["width"]}" fill="none" stroke-linecap="round" opacity="{fork_trunk["opacity"]}"/>')

# Draw confluence nodes (diamond) and their incoming arcs
for conf in CONFLUENCES:
    lane = next(l for l in LANES if l["id"] == conf["lane"])
    cx = year_to_x(conf["year"])
    cy = lane["y"] + conf["y_off"]
    node_positions[conf["id"]] = (cx, cy)
    color = lane["color"]
    # Draw arcs from source nodes to confluence FIRST (behind diamond)
    for src_node_id in conf["from_nodes"]:
        if src_node_id in node_positions:
            sx, sy = node_positions[src_node_id]
            mx = (sx + cx) / 2
            # Determine source color
            src_color = "#71717a"
            for tid2, trunk2 in TRUNKS.items():
                for nd in trunk2["nodes"]:
                    if nd["id"] == src_node_id:
                        src_color = trunk2["color"]
                        break
            lines.append(f'<path d="M{sx},{sy} C{mx},{sy} {mx},{cy} {cx},{cy}" stroke="{src_color}" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.4" stroke-dasharray="6,3"/>')
    # Diamond shape
    lines.append(f'<rect x="{cx-8}" y="{cy-8}" width="16" height="16" rx="2" fill="#fff" stroke="{color}" stroke-width="2" transform="rotate(45,{cx},{cy})"/>')
    lines.append(f'<text x="{cx}" y="{cy+20}" text-anchor="middle" font-size="7" fill="{color}" font-weight="600">{conf["title"]}</text>')
    # Subtitle
    if conf.get("subtitle"):
        lines.append(f'<text x="{cx}" y="{cy+29}" text-anchor="middle" font-size="6" fill="#71717a">{conf["subtitle"]}</text>')

# Draw cross-lane borrows (dashed)
for src_id, tgt_id, label in CROSS_BORROWS:
    if src_id in node_positions and tgt_id in node_positions:
        sx, sy = node_positions[src_id]
        tx, ty_val = node_positions[tgt_id]
        mx = (sx + tx) / 2
        my = (sy + ty_val) / 2
        lines.append(f'<path d="M{tx},{ty_val} C{mx},{ty_val} {mx},{sy} {sx},{sy}" stroke="#71717a" stroke-width="1.2" fill="none" stroke-dasharray="5,3" opacity="0.5"/>')
        lines.append(f'<text x="{mx}" y="{my-4}" text-anchor="middle" font-size="7" fill="#71717a" opacity="0.7">{label}</text>')

lines.append('</svg>')

# ---------- ASSEMBLE HTML ----------
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Trunks V2 — Fork & Confluence</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'IBM Plex Sans', -apple-system, sans-serif; background: #fff; color: #18181b; }}
.header {{ padding: 16px 24px; border-bottom: 1px solid #e4e4e7; }}
.header h1 {{ font-size: 16px; font-weight: 700; }}
.header p {{ font-size: 11px; color: #71717a; margin-top: 2px; }}
.container {{ padding: 20px; overflow-x: auto; }}
svg {{ display: block; width: 100%; }}
svg text {{ font-family: 'IBM Plex Sans', sans-serif; }}
.legend {{ padding: 12px 24px; border-top: 1px solid #e4e4e7; display: flex; gap: 24px; font-size: 11px; color: #52525b; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; }}
</style>
</head>
<body>
<div class="header">
  <h1>Trunks V2 — 技术路径分叉与合流</h1>
  <p>主干=实线水平延续 · 分叉=贝塞尔弧剥离 · 合流=菱形汇入 · 跨lane=虚线弧</p>
</div>
<div class="container">
{chr(10).join(lines)}
</div>
<div class="legend">
  <div class="legend-item"><svg width="24" height="10"><line x1="0" y1="5" x2="24" y2="5" stroke="#475569" stroke-width="3" stroke-linecap="round"/></svg> 主干 (inherits)</div>
  <div class="legend-item"><svg width="24" height="10"><path d="M0,8 C8,8 8,2 16,2 L24,2" stroke="#475569" stroke-width="2" fill="none" stroke-linecap="round"/></svg> 分叉 (competes)</div>
  <div class="legend-item"><svg width="24" height="10"><line x1="0" y1="5" x2="24" y2="5" stroke="#71717a" stroke-width="1.2" stroke-dasharray="5,3"/></svg> 借鉴 (borrows)</div>
  <div class="legend-item"><svg width="16" height="16"><rect x="2" y="2" width="10" height="10" rx="1" fill="#fff" stroke="#475569" stroke-width="1.5" transform="rotate(45,8,8)"/></svg> 合流 (confluence)</div>
</div>
</body>
</html>'''

with open('trunks-v2-fork-confluence.html', 'w') as f:
    f.write(html)
print("Generated: trunks-v2-fork-confluence.html")
