"""Repository for organizations — koreň multi-tenancy.

Každý používateľ, projekt a klient patrí práve jednej organizácii. Izolácia dát
sa vynucuje v backend/deps.py (assert_* helpery), tu je len čisté SQL.
"""
from __future__ import annotations

import re

from repositories.base_repo import get_connection, row_to_dict


def slugify(name: str) -> str:
    """Vyrobí URL-safe slug z názvu organizácie (bez diakritiky, malé písmená)."""
    translit = str.maketrans("áäčďéíĺľňóôŕšťúýžÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ", "aacdeillnoorstuyzAACDEILLNOORSTUYZ")
    base = name.translate(translit).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "org"


def create_organization(name: str, slug: str, plan: str = "free") -> int:
    """Vytvorí organizáciu a vráti jej id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO organizations (name, slug, plan) VALUES (?, ?, ?)",
            (name, slug, plan),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_organization(org_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_organization_by_slug(slug: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM organizations WHERE slug = ?", (slug,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def slug_exists(slug: str) -> bool:
    return get_organization_by_slug(slug) is not None


def unique_slug(name: str) -> str:
    """Vráti voľný slug — pri kolízii pripojí -2, -3, …"""
    base = slugify(name)
    candidate = base
    n = 2
    while slug_exists(candidate):
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def delete_organization(org_id: int) -> None:
    """Zmaž organizáciu (kompenzačná akcia — napr. keď signup zlyhá po vytvorení org)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
        conn.commit()
    finally:
        conn.close()


def update_plan(org_id: int, plan: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("UPDATE organizations SET plan = ? WHERE id = ?", (plan, org_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
