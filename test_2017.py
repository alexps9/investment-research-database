import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search specifically for 2017 paper
        resp = await client.get("https://api.openalex.org/works", params={
            "filter": "publication_year:2017,cited_by_count:>10000",
            "per-page": 20,
            "sort": "cited_by_count:desc",
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        print("=== High-cited 2017 papers ===")
        for r in data.get("results", [])[:15]:
            # Check if has Transformer concept
            tr_score = None
            for c in r.get("concepts", []):
                if c["id"].endswith("C66322947"):
                    tr_score = c.get("score")
                    break
            if tr_score:
                print(f"  {r['cited_by_count']:>5} cite | {r['publication_year']} | {r['title'][:60]}... (tr_score:{tr_score})")

asyncio.run(main())
