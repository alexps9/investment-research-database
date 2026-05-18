"""Export backend world_model_data.py → frontend JSON for Vercel deployment.

Runs impact scoring before export so frontend gets computed scores.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.data.world_model_data import ITERATIONS, LANES, PAPERS, ROWS
from app.services.impact_scoring import compute_impact_scores

# Compute impact scores
scored_papers = compute_impact_scores(PAPERS)

output = {
    "lanes": [{"id": l.id, "title": l.title, "subtitle": l.subtitle, "color": l.color} for l in LANES],
    "rows": [{"id": r.id, "lane": r.lane, "title": r.title, "subtitle": r.subtitle} for r in ROWS],
    "papers": [
        {
            "id": p.id, "title": p.title, "year": p.year, "quarter": p.quarter,
            "paradigm": p.paradigm, "layer": p.layer, "lane": p.lane, "row": p.row,
            "path": p.path, "size": p.size, "builds_on": p.builds_on or [],
            "impact_score": p.impact_score,
            "is_rising": p.is_rising,
            "is_weak_signal": p.is_weak_signal,
        }
        for p in scored_papers
    ],
    "iterations": [
        {
            "id": it.id, "title": it.title, "subtitle": it.subtitle,
            "path": it.path, "row": it.row, "papers": it.papers,
            "mutations": {
                k: {"summary": v.summary, "detail": v.detail, "bottleneck": v.bottleneck, "result": v.result}
                for k, v in it.mutations.items()
            },
        }
        for it in ITERATIONS
    ],
}

out_path = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "world-model-data.json"
out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))

# Print scoring summary
scores = [p.impact_score for p in scored_papers if p.impact_score is not None]
rising = sum(1 for p in scored_papers if p.is_rising)
weak = sum(1 for p in scored_papers if p.is_weak_signal)
print(f"Exported: {len(output['lanes'])} lanes, {len(output['rows'])} rows, {len(output['papers'])} papers, {len(output['iterations'])} iterations")
print(f"Impact scores: min={min(scores):.1f}, max={max(scores):.1f}, mean={sum(scores)/len(scores):.1f}")
print(f"Rising: {rising}, Weak signal: {weak}")
print(f"→ {out_path}")
