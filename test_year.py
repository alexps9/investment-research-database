import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Check what year the paper shows as
        resp = await client.get("https://api.openalex.org/works/W2626778328", params={
            "select": "id,title,publication_year,cited_by_count,doi"
        })
        r = resp.json()
        print("=== Attention Is All You Need ===")
        print(f"Year in OpenAlex: {r.get('publication_year')}")
        print(f"Citations: {r.get('cited_by_count')}")
        print(f"DOI: {r.get('doi')}")
        
        # Check if filtering by year 2015-2024 would include it
        year = r.get('publication_year')
        if year and year > 2024:
            print(f"\n⚠️ PROBLEM: OpenAlex shows year={year}, but original was 2017!")
            print(f"This means the paper is filtered out by the filter: publication_year:2015-2024")

asyncio.run(main())
