# AGENTS.md — AI Knowledge Base Coding Conventions

## Project Overview

This is an **AI Intelligence Knowledge Base** system consisting of:
- `backend/` — FastAPI + SQLAlchemy 2.x + Alembic + PostgreSQL
- `frontend/` — Next.js 14 + TypeScript + Tailwind CSS
- `docker-compose.yml` — local development orchestration

Knowledge chain: **Source → Signal → Entity → Relation → Wiki/Search**

---

## Backend Conventions

### Technology Stack
- Python 3.12+
- FastAPI 0.111+
- SQLAlchemy 2.x (async via `asyncpg`)
- Alembic for migrations
- Pydantic v2 for schemas
- PostgreSQL 16 as source of truth

### Code Structure
```
backend/
├── app/
│   ├── main.py           # FastAPI app, CORS, router registration
│   ├── database.py       # Engine, session, Base
│   ├── models/           # SQLAlchemy ORM models (all in __init__.py)
│   ├── schemas/          # Pydantic request/response schemas
│   ├── repositories/     # DB query logic (all in __init__.py)
│   ├── routers/          # FastAPI route handlers
│   └── core/
│       └── config.py     # Settings via pydantic-settings
├── alembic/              # Migrations
├── tests/                # pytest tests
├── seed.py               # One-shot seed script
├── requirements.txt
├── Dockerfile
└── alembic.ini
```

### Rules
- All DB access goes through `repositories/` — routers call repos, not direct SQL.
- Use `selectinload` for related data; avoid N+1 queries.
- Pydantic `model_dump(exclude_unset=True)` for PATCH operations.
- `relation_type` must be validated against `VALID_RELATION_TYPES` in `models/__init__.py`.
- Never add arbitrary relation types — extend `VALID_RELATION_TYPES` explicitly.
- `metadata` DB columns are mapped to `metadata_` in Python to avoid keyword conflict.
- pgvector embedding column is optional — the app must start without it.
- Neo4j is **not** required in this milestone.

### API Conventions
- All routes prefixed with `/api`
- HTTP 201 for POST, 204 for DELETE
- Validation errors return HTTP 422
- 404 for missing resources

---

## Frontend Conventions

### Technology Stack
- Next.js 14 App Router
- TypeScript (strict)
- Tailwind CSS
- No external component library required (simple custom components in `src/components/ui/`)

### Code Structure
```
frontend/src/
├── app/
│   ├── layout.tsx          # Root layout with Sidebar
│   ├── page.tsx            # Redirects to /dashboard
│   ├── dashboard/          # Stats + latest signals/runs
│   ├── sources/            # Source management table
│   ├── signals/            # Signal card list
│   ├── entities/           # Entity table
│   ├── wiki/               # Search page + entity wiki detail
│   └── graph-lite/         # Relation graph (table view)
├── components/
│   ├── Sidebar.tsx
│   └── ui/
│       ├── Badge.tsx
│       └── Card.tsx
└── lib/
    ├── api.ts              # Fetch wrapper
    └── types.ts            # TypeScript types matching backend schemas
```

### Rules
- API calls via `src/lib/api.ts` — all requests proxy through Next.js rewrites to backend.
- Server components for read-only pages (dashboard, wiki, graph-lite).
- Client components (`'use client'`) for pages with forms/state.
- Types in `src/lib/types.ts` mirror backend Pydantic schemas.

---

## Test Commands

### Unit tests (no DB required)
```bash
cd backend
pip install -r requirements.txt
pytest tests/test_models.py -v
```

### API smoke tests (requires running PostgreSQL + backend)
```bash
# Start DB and backend first (see README), then:
cd backend
pytest tests/test_api.py -v
```

### Frontend type-check
```bash
cd frontend
npm run type-check
```

### Frontend lint
```bash
cd frontend
npm run lint
```

---

## Migration Commands

```bash
cd backend
# Apply all migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "describe change"

# Rollback one step
alembic downgrade -1
```

---

## Seed Data

```bash
cd backend
python seed.py
```

Idempotency: seed script will fail on duplicate unique constraints if run twice. Reset with `alembic downgrade base && alembic upgrade head` before re-seeding.

---

## Environment Variables

Copy `.env.example` to `backend/.env` and adjust:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy URL (asyncpg) |
| `DATABASE_URL_SYNC` | Sync URL for Alembic (psycopg2) |
| `DEBUG` | Enable SQL echo |
| `NEXT_PUBLIC_API_URL` | Backend base URL for frontend |

---

## What NOT to build (current milestone)

- Daily report generation
- Subscriber / publishing features  
- Neo4j integration (design schema for future sync only)
- Twitter as a direct source field (use `source_accounts` table)
