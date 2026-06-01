from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import sources, signals, entities, search, wiki, runs, dashboard, graph

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI Intelligence Knowledge Base — Backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_prefix

app.include_router(sources.router, prefix=prefix)
app.include_router(signals.router, prefix=prefix)
app.include_router(entities.router, prefix=prefix)
app.include_router(search.router, prefix=prefix)
app.include_router(wiki.router, prefix=prefix)
app.include_router(runs.router, prefix=prefix)
app.include_router(dashboard.router, prefix=prefix)
app.include_router(graph.router, prefix=prefix)


@app.get("/health")
async def health():
    return {"status": "ok"}
