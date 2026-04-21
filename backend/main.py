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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth_router, projects_router, tasks_router, team_router, comments_router, notifications_router
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

# CORS — dev + produkčná Vercel URL cez env premenné
_extra_origins = os.environ.get("CORS_ORIGINS", "")
_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
] + [o.strip() for o in _extra_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
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


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "version": "1.2.0", "docs": "/docs"}

