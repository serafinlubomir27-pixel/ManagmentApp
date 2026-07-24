"""AI-CPM Parser — natural language project description → structured tasks with CPM data.

Provider-agnostický: použije prvého poskytovateľa, ktorého API kľúč je nastavený,
v poradí GEMINI → ANTHROPIC (Claude) → OPENAI. Ak nie je žiadny kľúč (alebo volanie
zlyhá), spadne na rule-based heuristiku. Appka teda funguje aj bez AI kľúča.

ENV:
  GEMINI_API_KEY     + voliteľne GEMINI_MODEL     (default gemini-2.0-flash) — free tier
  ANTHROPIC_API_KEY  + voliteľne ANTHROPIC_MODEL  (default claude-haiku-4-5-20251001)
  OPENAI_API_KEY     + voliteľne OPENAI_MODEL     (default gpt-4o-mini)

Output format:
  {
    "tasks": [
      {
        "name": str,
        "duration": int,        # days
        "dependencies": [str],  # list of task names this task depends on
        "description": str,
        "priority": str,        # low | medium | high | critical
      }
    ],
    "source": "gemini" | "anthropic" | "openai" | "heuristic"
  }
"""
from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# ── Spoločný system prompt pre všetkých poskytovateľov ────────────────────────

_SYSTEM_PROMPT = """Si expert na projektový manažment a CPM (Critical Path Method).
Dostaneš popis projektu v prirodzenom jazyku (slovensky alebo anglicky).
Musíš extrahovať zoznam úloh s trvaním a závislosťami.

Pravidlá:
- Každá úloha má: name (krátky, max 5 slov), duration (dni, celé číslo 1-90), dependencies (zoznam mien iných úloh, môže byť prázdny), description (1-2 vety), priority (low/medium/high/critical)
- Závislosti sú mená iných úloh (presne ako sú pomenované v zozname)
- Logicky: testovanie závisí na implementácii, implementácia závisí na dizajne atď.
- Ak nie je poradie jasné, použij zdravý rozum
- Max 20 úloh na projekt
- VŽDY odpovídaj IBA platným JSON objektom, bez markdown, bez vysvetlenia

Formát odpovede:
{"tasks": [{"name": "...", "duration": N, "dependencies": ["..."], "description": "...", "priority": "medium"}]}"""


def parse_project(description: str) -> dict:
    """Parse natural language project description into a structured task list.

    Skúša poskytovateľov v poradí (podľa prítomného API kľúča); pri chybe skúsi
    ďalšieho, nakoniec heuristiku. `source` v návratovej hodnote hovorí, kto to spracoval.
    """
    providers = (
        ("gemini", "GEMINI_API_KEY", _parse_with_gemini),
        ("anthropic", "ANTHROPIC_API_KEY", _parse_with_anthropic),
        ("openai", "OPENAI_API_KEY", _parse_with_openai),
    )
    for name, env_key, fn in providers:
        api_key = os.environ.get(env_key, "").strip()
        if not api_key:
            continue
        try:
            return fn(description, api_key)
        except Exception as exc:
            logger.warning("[AI] provider '%s' zlyhal (%s) — skúšam ďalší / heuristiku", name, exc)

    return _parse_heuristic(description)


def _http_post_json(url: str, headers: dict, body: dict) -> dict:
    """POST JSON a vráť dekódovanú JSON odpoveď (urllib, bez extra závislostí)."""
    import urllib.request

    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_json(text: str) -> dict:
    """Vytiahne JSON objekt z odpovede modelu — znesie aj markdown ```json fence."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _parse_with_gemini(description: str, api_key: str) -> dict:
    """Google Gemini (AI Studio) — má free tier. Kľúč ide v hlavičke, nie v URL."""
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    result = _http_post_json(
        url,
        {"x-goog-api-key": api_key},
        {
            "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": description[:4000]}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        },
    )
    content = result["candidates"][0]["content"]["parts"][0]["text"]
    return {"tasks": _normalize_tasks(_extract_json(content).get("tasks", [])), "source": "gemini"}


def _parse_with_anthropic(description: str, api_key: str) -> dict:
    """Anthropic Claude (Messages API)."""
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    result = _http_post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        {
            "model": model,
            "max_tokens": 2000,
            "temperature": 0.2,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": description[:4000]}],
        },
    )
    content = result["content"][0]["text"]
    return {"tasks": _normalize_tasks(_extract_json(content).get("tasks", [])), "source": "anthropic"}


def _parse_with_openai(description: str, api_key: str) -> dict:
    """OpenAI Chat Completions (JSON mode)."""
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    result = _http_post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}"},
        {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": description[:4000]},
            ],
            "temperature": 0.2,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        },
    )
    content = result["choices"][0]["message"]["content"]
    return {"tasks": _normalize_tasks(_extract_json(content).get("tasks", [])), "source": "openai"}


def _normalize_tasks(tasks: list[dict]) -> list[dict]:
    """Normalize and validate task list from AI output."""
    normalized = []
    seen_names: set[str] = set()

    for t in tasks[:20]:  # Max 20 tasks
        name = str(t.get("name", "Úloha")).strip()[:60]
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        duration = max(1, min(90, int(t.get("duration", 1) or 1)))
        deps = [str(d).strip() for d in (t.get("dependencies") or []) if str(d).strip()]
        priority = t.get("priority", "medium")
        if priority not in ("low", "medium", "high", "critical"):
            priority = "medium"

        normalized.append({
            "name": name,
            "duration": duration,
            "dependencies": deps,
            "description": str(t.get("description", ""))[:500],
            "priority": priority,
        })

    return normalized


# ── Heuristic fallback ────────────────────────────────────────────────────────
# Simple keyword/pattern based parser when no API key

_DURATION_PATTERN = re.compile(
    r'(\d+)\s*(?:dní|dni|day|days|d\b|týždn\w*|week\w*)',
    re.IGNORECASE
)

_TASK_KEYWORDS = [
    # SK
    ('analýza', 'high', 3), ('návrh', 'medium', 3), ('dizajn', 'medium', 4),
    ('implementácia', 'high', 7), ('vývoj', 'high', 7), ('programovanie', 'high', 5),
    ('testovanie', 'medium', 3), ('kontrola', 'medium', 2), ('oprava', 'medium', 2),
    ('nasadenie', 'high', 2), ('deploy', 'high', 1), ('dokumentácia', 'low', 2),
    ('prezentácia', 'medium', 1), ('školenie', 'low', 2), ('meeting', 'low', 1),
    ('plánovanie', 'medium', 2), ('research', 'medium', 3), ('prieskum', 'medium', 3),
    # EN
    ('analysis', 'high', 3), ('design', 'medium', 4), ('implementation', 'high', 7),
    ('development', 'high', 7), ('testing', 'medium', 3), ('review', 'medium', 2),
    ('deployment', 'high', 2), ('documentation', 'low', 2), ('presentation', 'medium', 1),
    ('training', 'low', 2), ('planning', 'medium', 2),
]

# Simple sequential dependency: each task depends on the previous
def _parse_heuristic(description: str) -> dict:
    """Simple heuristic parser that extracts tasks from keywords."""
    desc_lower = description.lower()
    found_tasks = []

    # Try to find tasks from common keywords
    for keyword, priority, default_dur in _TASK_KEYWORDS:
        if keyword in desc_lower:
            # Try to find explicit duration near keyword
            surrounding = description[max(0, desc_lower.find(keyword)-20):desc_lower.find(keyword)+60]
            dur_match = _DURATION_PATTERN.search(surrounding)
            duration = int(dur_match.group(1)) if dur_match else default_dur
            if 'týžd' in surrounding.lower() or 'week' in surrounding.lower():
                duration *= 5  # Convert weeks to days

            found_tasks.append({
                "name": keyword.capitalize(),
                "duration": max(1, min(30, duration)),
                "priority": priority,
                "description": f"Fáza: {keyword}",
            })

    # If nothing found, create 3 generic tasks
    if not found_tasks:
        found_tasks = [
            {"name": "Plánovanie", "duration": 2, "priority": "high", "description": "Plánovanie projektu"},
            {"name": "Realizácia", "duration": 5, "priority": "high", "description": "Hlavná realizácia"},
            {"name": "Dokončenie", "duration": 1, "priority": "medium", "description": "Dokončenie a odovzdanie"},
        ]

    # Add sequential dependencies
    tasks_with_deps = []
    for i, t in enumerate(found_tasks):
        deps = [found_tasks[i - 1]["name"]] if i > 0 else []
        tasks_with_deps.append({**t, "dependencies": deps})

    return {"tasks": tasks_with_deps, "source": "heuristic"}
