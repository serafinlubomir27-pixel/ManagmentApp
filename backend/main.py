"""ManagmentApp — FastAPI backend.

Spustenie (development):
    py -m uvicorn backend.main:app --reload

Swagger UI:  http://127.0.0.1:8000/docs
ReDoc:       http://127.0.0.1:8000/redoc
"""
from __future__ import annotations

import sys
import os

# Pridaj koreňový adresár projektu do Python path
# (aby importy repositories.*, logic.* fungovali z backend/ podsložky)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ── Sentry (observability) ────────────────────────────────────────────────────
# Aktivuje sa len keď je nastavený SENTRY_DSN. Import je chránený, takže appka
# funguje aj bez nainštalovaného sentry-sdk (napr. v testoch).
_sentry_dsn = os.environ.get("SENTRY_DSN", "").strip()
if _sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.environ.get("SENTRY_ENV", os.environ.get("DB_BACKEND", "sqlite")),
            send_default_pii=False,
        )
    except Exception as _exc:  # pragma: no cover — nezhadzuj štart appky
        print(f"[Sentry] init preskočený: {_exc}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from backend.routers import auth_router, projects_router, tasks_router, team_router, comments_router, notifications_router, calendar_router, invite_router, ai_router, attachments_router, clients_router, org_router
from backend.ratelimit import limiter
from repositories.base_repo import get_backend

# ── Inicializácia databázy ───────────────────────────────────────────────────
# SQLite: automaticky vytvor tabuľky pri štarte
# PostgreSQL: schema je už vytvorená cez supabase_schema.sql
if get_backend() == "sqlite":
    from database.setup import create_database
    create_database()
else:
    print("[DB] PostgreSQL backend — Supabase schema sa používa")

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ManagmentApp API",
    description="REST API pre ManagmentApp — projektový manažment s CPM.",
    version="1.2.0",
)

# Rate limiting (slowapi) — limiter je zdieľaný v backend/ratelimit.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — dev + produkčná Vercel URL cez env premenné
_extra_origins = os.environ.get("CORS_ORIGINS", "")
_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "https://managmentapp.surge.sh",
    "https://managmentapps.netlify.app",
] + [o.strip() for o in _extra_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    # Povoľ všetky Vercel deploye (prod aj preview) — frontend beží na Vercel.
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routery ──────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(projects_router.router)
app.include_router(tasks_router.router)
app.include_router(team_router.router)
app.include_router(comments_router.router, prefix="")
app.include_router(notifications_router.router, prefix="")
app.include_router(calendar_router.router, prefix="")
app.include_router(invite_router.router, prefix="")
app.include_router(ai_router.router, prefix="")
app.include_router(attachments_router.router, prefix="")
app.include_router(clients_router.router, prefix="")
app.include_router(org_router.router)

# ── Static files (uploaded attachments) ──────────────────────────────────────
from fastapi.staticfiles import StaticFiles
import os as _os
_uploads_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "uploads")
_os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "version": "1.2.0", "docs": "/docs"}

