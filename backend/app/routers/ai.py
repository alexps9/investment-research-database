from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import llm, semantic

router = APIRouter(prefix="/ai", tags=["ai"])


# ── schemas ───────────────────────────────────────────────────────────────────

class AIStatus(BaseModel):
    embeddings_enabled: bool
    chat_enabled: bool
    embedding_model: str
    llm_model: str


class ReindexRequest(BaseModel):
    object_types: Optional[list[str]] = None


class SearchHit(BaseModel):
    object_type: str
    object_id: str
    name: str
    description: Optional[str] = None
    score: float


class AskRequest(BaseModel):
    question: str
    object_types: Optional[list[str]] = None
    top_k: int = 8


class AskResponse(BaseModel):
    answer: str
    sources: list[SearchHit]


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", response_model=AIStatus)
async def ai_status():
    from app.core.config import get_settings
    s = get_settings()
    return AIStatus(
        embeddings_enabled=llm.embeddings_enabled(),
        chat_enabled=llm.chat_enabled(),
        embedding_model=s.embedding_model,
        llm_model=s.llm_model,
    )


@router.post("/reindex")
async def reindex(req: ReindexRequest, db: AsyncSession = Depends(get_db)):
    try:
        counts = await semantic.reindex(db, req.object_types)
    except llm.LLMNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # surface upstream API errors clearly
        raise HTTPException(status_code=502, detail=f"Embedding provider error: {e}")
    return {"status": "ok", "indexed": counts}


@router.get("/search", response_model=list[SearchHit])
async def semantic_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, le=50),
    types: Optional[str] = Query(default=None, description="comma-separated: entity,source,signal"),
    db: AsyncSession = Depends(get_db),
):
    object_types = [t.strip() for t in types.split(",")] if types else None
    try:
        return await semantic.semantic_search(db, q, object_types=object_types, limit=limit)
    except llm.LLMNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embedding provider error: {e}")


SYSTEM_PROMPT = (
    "You are an AI research-intelligence assistant for an AI knowledge base. "
    "Answer the user's question using ONLY the provided context entries about "
    "researchers, organisations, and signals. If the context is insufficient, "
    "say so honestly. Reply in the same language as the question. Be concise and "
    "cite the relevant entity/organisation names you used."
)


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, db: AsyncSession = Depends(get_db)):
    if not llm.chat_enabled():
        raise HTTPException(status_code=400, detail="DEEPSEEK_API_KEY is not set; Q&A disabled.")
    if not llm.embeddings_enabled():
        raise HTTPException(status_code=400, detail="EMBEDDING_API_KEY is not set; retrieval disabled.")

    try:
        hits = await semantic.semantic_search(
            db, req.question, object_types=req.object_types, limit=req.top_k
        )
    except llm.LLMNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embedding provider error: {e}")

    context_lines = []
    for i, h in enumerate(hits, 1):
        desc = f" — {h['description']}" if h.get("description") else ""
        context_lines.append(f"[{i}] ({h['object_type']}) {h['name']}{desc}")
    context = "\n".join(context_lines) if context_lines else "(no relevant context found)"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {req.question}"},
    ]
    try:
        answer = await llm.chat(messages)
    except llm.LLMNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {e}")

    return AskResponse(answer=answer, sources=[SearchHit(**h) for h in hits])
