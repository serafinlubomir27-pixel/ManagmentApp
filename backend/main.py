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

from backend.routers import auth_router, projects_router, tasks_router, team_router
from database.setup import create_database

# ── Inicializácia databázy ───────────────────────────────────────────────────
create_database()

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ManagmentApp API",
    description="REST API pre ManagmentApp — projektový manažment s CPM.",
    version="1.2.0",
)

# CORS — povolí React frontend (v dev móde na localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routery ──────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(projects_router.router)
app.include_router(tasks_router.router)
app.include_router(team_router.router)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "version": "1.2.0", "docs": "/docs"}
