"""Cenové plány (tiers) a ich limity.

Zodpovedá návrhu z bakalárky §7.4.2. None = neobmedzené.
Limity sa vynucujú pri vytváraní projektov a používateľov (viď routery).
"""
from __future__ import annotations

PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "free":       {"max_projects": 2,    "max_users": 5},
    "starter":    {"max_projects": None, "max_users": 15},
    "team":       {"max_projects": None, "max_users": None},
    "enterprise": {"max_projects": None, "max_users": None},
}

PLAN_LABELS: dict[str, str] = {
    "free": "Free",
    "starter": "Starter",
    "team": "Team",
    "enterprise": "Enterprise",
}


def _limits(plan: str) -> dict[str, int | None]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def project_limit(plan: str) -> int | None:
    return _limits(plan)["max_projects"]


def user_limit(plan: str) -> int | None:
    return _limits(plan)["max_users"]


def can_add_project(plan: str, current_count: int) -> bool:
    limit = project_limit(plan)
    return limit is None or current_count < limit


def can_add_user(plan: str, current_count: int) -> bool:
    limit = user_limit(plan)
    return limit is None or current_count < limit
