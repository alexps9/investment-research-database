"""
Batch fetch cited_by_count from OpenAlex for all papers in world_model_data.py.

Usage:
  python scripts/fetch_citations.py          # fetch and print results
  python scripts/fetch_citations.py --apply  # fetch and update data file
"""

import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.data.world_model_data import PAPERS

BASE_URL = "https://api.openalex.org"
HEADERS = {"User-Agent": "SignalPaperAnalysis/1.0 (mailto:dev@example.com)"}


FULL_TITLES = {
    "planet": "Learning Latent Dynamics for Planning from Pixels",
    "dreamer_v1": "Dream to Control: Learning Behaviors by Latent Imagination",
    "dreamer_v2": "Mastering Atari with Discrete World Models",
    "dreamer_v3": "Mastering Diverse Domains through World Models",
    "tdmpc": "Temporal Difference Learning for Model Predictive Control",
    "tdmpc2": "TD-MPC2: Scalable, Robust World Models for Continuous Control",
    "sora": "Sora: A Review on Background, Technology, Limitations",
    "gpt4": "GPT-4 Technical Report",
    "llama3": "LLaMA: Open and Efficient Foundation Language Models",
    "i_jepa": "Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture",
    "v_jepa": "V-JEPA: Revisiting Feature Prediction for Learning Visual Representations from Video",
    "v_jepa_2": "V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning",
    "genie2": "Genie 2: A Large-Scale Foundation World Model",
    "oasis": "OASIS: A Large-Scale Dataset for Single Image 3D in the Wild",
    "slot_attention": "Object-Centric Learning with Slot Attention",
    "thick": "Think Hierarchically, Act Dynamically",
    "pwm": "Predictive World Models",
    "cosmos": "Cosmos World Foundation Model",
    "gen3": "Gen-3",
    "wan": "Wan: Open and Advanced Large-Scale Video Generative Models",
    "llava": "Visual Instruction Tuning",
    "text2room": "Text2Room: Extracting Textured 3D Meshes from 2D Text-to-Image Models",
    "dino_wm": "DINO-WM: World Models on Pre-trained Visual Features",
}


def search_paper(paper_id: str, title: str, year: int, retries: int = 3) -> dict | None:
    """Search OpenAlex for a paper by title and year, return best match."""
    import urllib.parse
    search_title = FULL_TITLES.get(paper_id, title)
    query = urllib.parse.quote(search_title)
    url = f"{BASE_URL}/works?search={query}&filter=publication_year:{year-1}-{year+1}&per-page=3&select=id,title,cited_by_count,publication_year,authorships"

    for attempt in range(retries):
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                results = data.get("results", [])
                if results:
                    return results[0]
                return None
        except HTTPError as e:
            print(f"  Error searching '{search_title}': HTTP {e.code}")
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  Network error for '{search_title}': {e}")
    return None


def main():
    apply_mode = "--apply" in sys.argv
    print(f"Fetching citations for {len(PAPERS)} papers...")
    if apply_mode:
        print("Mode: --apply (will update data file)\n")
    else:
        print("Mode: dry run (use --apply to update data file)\n")

    results = {}
    for i, paper in enumerate(PAPERS):
        match = search_paper(paper.id, paper.title, paper.year)
        if match:
            cited = match["cited_by_count"]
            results[paper.id] = {
                "cited_by_count": cited,
                "openalex_title": match["title"],
                "institutions": _extract_institutions(match),
            }
            print(f"  [{i+1}/{len(PAPERS)}] {paper.title} → {cited} citations")
        else:
            results[paper.id] = {"cited_by_count": 0, "openalex_title": None, "institutions": []}
            print(f"  [{i+1}/{len(PAPERS)}] {paper.title} → NOT FOUND")

        # Rate limiting: ~5 req/s
        time.sleep(0.2)

    # Summary
    found = sum(1 for r in results.values() if r["openalex_title"])
    print(f"\nFound: {found}/{len(PAPERS)}")
    print(f"Total citations: {sum(r['cited_by_count'] for r in results.values())}")

    # Top 10
    top = sorted(results.items(), key=lambda x: x[1]["cited_by_count"], reverse=True)[:10]
    print("\nTop 10 by citations:")
    for pid, info in top:
        print(f"  {pid}: {info['cited_by_count']}")

    # Save results
    out_path = Path(__file__).parent / "citation-results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nResults saved to {out_path}")

    if apply_mode:
        _apply_to_data(results)


def _extract_institutions(work: dict) -> list[str]:
    """Extract institution names from OpenAlex work."""
    institutions = []
    seen = set()
    for authorship in work.get("authorships", []):
        for inst in authorship.get("institutions", []):
            name = inst.get("display_name", "")
            if name and name not in seen:
                institutions.append(name)
                seen.add(name)
    return institutions[:5]


def _apply_to_data(results: dict):
    """Update world_model_data.py with cited_by_count values."""
    data_file = Path(__file__).parent.parent / "backend" / "app" / "data" / "world_model_data.py"
    content = data_file.read_text()

    updated = 0
    for paper_id, info in results.items():
        cited = info["cited_by_count"]
        if cited > 0:
            # Find the paper definition and add/update cited_by_count
            # Pattern: id="paper_id", ... size="xx")
            # We need to add cited_by_count before the closing paren
            import re
            pattern = rf'(EvolutionPaper\(id="{paper_id}"[^)]*?)(\))'
            match = re.search(pattern, content)
            if match:
                paper_str = match.group(1)
                if "cited_by_count=" in paper_str:
                    # Update existing
                    paper_str = re.sub(r'cited_by_count=\d+', f'cited_by_count={cited}', paper_str)
                else:
                    # Add before closing paren
                    paper_str += f', cited_by_count={cited}'
                content = content[:match.start()] + paper_str + ")" + content[match.end():]
                updated += 1

    data_file.write_text(content)
    print(f"\nUpdated {updated} papers in {data_file}")


if __name__ == "__main__":
    main()
