"""Testy provider-agnostického AI parsera (task #6).

Bez siete — testujú výber poskytovateľa, fallback na heuristiku a parsovanie JSON.
Reálne API volania (Gemini/Claude/OpenAI) sa monkeypatchujú.
"""
import pytest

from logic import ai_parser


# ── _extract_json ────────────────────────────────────────────────────────────

def test_extract_json_plain():
    assert ai_parser._extract_json('{"tasks": []}') == {"tasks": []}


def test_extract_json_markdown_fence():
    txt = '```json\n{"tasks": [{"name": "A"}]}\n```'
    assert ai_parser._extract_json(txt)["tasks"][0]["name"] == "A"


def test_extract_json_with_surrounding_prose():
    txt = 'Tu je výsledok:\n{"tasks": []}\nDúfam že pomôže.'
    assert ai_parser._extract_json(txt) == {"tasks": []}


# ── Výber poskytovateľa / fallback ───────────────────────────────────────────

def _clear_keys(mp):
    for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        mp.delenv(k, raising=False)


def test_falls_back_to_heuristic_without_keys(monkeypatch):
    _clear_keys(monkeypatch)
    result = ai_parser.parse_project("Projekt: analýza, implementácia, testovanie a nasadenie")
    assert result["source"] == "heuristic"
    assert len(result["tasks"]) >= 1


def test_provider_precedence_gemini_before_openai(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "y")
    monkeypatch.setattr(ai_parser, "_parse_with_gemini", lambda d, k: {"tasks": [], "source": "gemini"})
    monkeypatch.setattr(ai_parser, "_parse_with_openai", lambda d, k: {"tasks": [], "source": "openai"})
    assert ai_parser.parse_project("čokoľvek")["source"] == "gemini"


def test_provider_failure_falls_through_to_heuristic(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    def boom(d, k):
        raise RuntimeError("api down")

    monkeypatch.setattr(ai_parser, "_parse_with_gemini", boom)
    result = ai_parser.parse_project("analýza a testovanie")
    assert result["source"] == "heuristic"


# ── Normalizácia výstupu ─────────────────────────────────────────────────────

def test_normalize_caps_duration_and_dedups():
    tasks = [
        {"name": "A", "duration": 999},
        {"name": "A", "duration": 5},   # duplikát mena → vynechá sa
        {"name": "", "duration": 1},    # prázdne meno → vynechá sa
    ]
    out = ai_parser._normalize_tasks(tasks)
    assert len(out) == 1
    assert out[0]["duration"] == 90     # 999 orezané na max 90
