import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError
from app.core.config import get_settings
from app.core.seed import seed_users
from app.routers import (
    sources, signals, entities, search, wiki, runs, dashboard, graph,
    export, ai, daily, funding, tags, organizations, auth,
)

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
app.include_router(export.router, prefix=prefix)
app.include_router(ai.router, prefix=prefix)
app.include_router(daily.router, prefix=prefix)
app.include_router(funding.router, prefix=prefix)
app.include_router(tags.router, prefix=prefix)
app.include_router(organizations.router, prefix=prefix)
app.include_router(auth.router, prefix=prefix)


def _pg_sqlstate(exc: BaseException) -> str | None:
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


@app.exception_handler(DBAPIError)
async def _serialization_handler(request: Request, exc: DBAPIError):
    # REPEATABLE READ surfaces write/write conflicts as 40001 (serialization
    # failure) or 40P01 (deadlock). These are transient — tell the client to retry.
    if _pg_sqlstate(exc) in {"40001", "40P01"}:
        return JSONResponse(
            status_code=409,
            content={"detail": "数据库并发冲突，请重试 (serialization failure)"},
        )
    raise exc


@app.exception_handler(IntegrityError)
async def _integrity_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "数据冲突：违反唯一约束或外键"})


@app.on_event("startup")
async def _startup_seed_users():
    try:
        await seed_users()
    except Exception:  # pragma: no cover - never block startup on seeding
        logging.getLogger(__name__).exception("User seeding failed")


@app.get("/health")
async def health():
    return {"status": "ok"}
