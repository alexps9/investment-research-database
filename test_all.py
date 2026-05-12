import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Get papers sorted by citation, NO score filter
        resp = await client.get("https://api.openalex.org/works", params={
            "filter": "concepts.id:C66322947,publication_year:2015-2024,concepts.id:C41008148",
            "per-page": 30,
            "sort": "cited_by_count:desc",
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        print("=== Top 30 Transformer papers (no score filter) ===")
        for i, r in enumerate(data.get("results", [])[:30]):
            tr_score = None
            for c in r.get("concepts", []):
                if c["id"].endswith("C66322947"):
                    tr_score = c.get("score")
                    break
            marker = " ⚠️" if tr_score and tr_score < 0.4 else ""
            print(f"{i+1:>2}. {r['cited_by_count']:>5} cite | {r['publication_year']} | {r['title'][:50]}... (score:{tr_score}){marker}")

asyncio.run(main())
