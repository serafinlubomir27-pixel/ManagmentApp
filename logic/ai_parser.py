"""AI-CPM Parser — natural language project description → structured tasks with CPM data.

Uses OpenAI GPT-4o-mini when OPENAI_API_KEY is set.
Falls back to rule-based heuristics if no API key is available or call fails.

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
    "source": "openai" | "heuristic"
  }
"""
from __future__ import annotations

import json
import os
import re

# ── OpenAI system prompt ──────────────────────────────────────────────────────

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
    """Parse natural language project description into structured task list."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if api_key:
        try:
            return _parse_with_openai(description, api_key)
        except Exception as e:
            print(f"[AI] OpenAI call failed: {e} — falling back to heuristics")

    return _parse_heuristic(description)


def _parse_with_openai(description: str, api_key: str) -> dict:
    """Call OpenAI API to parse project description."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": description[:4000]},  # Limit input tokens
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    content = result["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    tasks = parsed.get("tasks", [])

    return {"tasks": _normalize_tasks(tasks), "source": "openai"}


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
