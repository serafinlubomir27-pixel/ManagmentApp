"""Repository for organizations — koreň multi-tenancy.

Každý používateľ, projekt a klient patrí práve jednej organizácii. Izolácia dát
sa vynucuje v backend/deps.py (assert_* helpery), tu je len čisté SQL.
"""
from __future__ import annotations

import re

from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


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


def export_organization(org_id: int) -> dict:
    """GDPR — právo na prístup/prenositeľnosť. Vráti všetky dáta organizácie ako dict.

    Heslá ani tokeny sa NEexportujú (bezpečnosť).
    """
    conn = get_connection()
    try:
        def q(sql, params=()):
            return rows_to_dicts(conn.execute(sql, params).fetchall())

        proj_sub = "SELECT id FROM projects WHERE organization_id = ?"
        task_sub = f"SELECT id FROM tasks WHERE project_id IN ({proj_sub})"
        client_sub = "SELECT id FROM clients WHERE organization_id = ?"
        return {
            "organization": row_to_dict(
                conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
            ),
            "users": q(
                "SELECT id, username, email, full_name, role, manager_id, created_at "
                "FROM users WHERE organization_id = ?", (org_id,)
            ),
            "projects": q("SELECT * FROM projects WHERE organization_id = ?", (org_id,)),
            "tasks": q(f"SELECT * FROM tasks WHERE project_id IN ({proj_sub})", (org_id,)),
            "task_dependencies": q(
                f"SELECT * FROM task_dependencies WHERE task_id IN ({task_sub})", (org_id,)
            ),
            "comments": q(f"SELECT * FROM comments WHERE task_id IN ({task_sub})", (org_id,)),
            "time_logs": q(f"SELECT * FROM time_logs WHERE task_id IN ({task_sub})", (org_id,)),
            "clients": q("SELECT * FROM clients WHERE organization_id = ?", (org_id,)),
            "client_meetings": q(
                f"SELECT * FROM client_meetings WHERE client_id IN ({client_sub})", (org_id,)
            ),
            "compliance_items": q(
                f"SELECT * FROM compliance_items WHERE client_id IN ({client_sub})", (org_id,)
            ),
            "deal_stages": q(
                f"SELECT * FROM deal_stages WHERE client_id IN ({client_sub})", (org_id,)
            ),
        }
    finally:
        conn.close()


def delete_organization_cascade(org_id: int) -> bool:
    """GDPR — právo na výmaz. Zmaže organizáciu a VŠETKY jej dáta (naprieč tabuľkami).

    Manuálny cascade — SQLite má FK enforcement vypnuté a ON DELETE pravidlá nie sú
    všade konzistentné, tak deti mažeme explicitne v poradí. Vráti True ak org zmazaná.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM projects WHERE organization_id = ?", (org_id,))
        project_ids = [r["id"] for r in cur.fetchall()]
        cur.execute("SELECT id FROM users WHERE organization_id = ?", (org_id,))
        user_ids = [r["id"] for r in cur.fetchall()]
        cur.execute("SELECT id FROM clients WHERE organization_id = ?", (org_id,))
        client_ids = [r["id"] for r in cur.fetchall()]
        task_ids: list[int] = []
        if project_ids:
            ph = ",".join("?" for _ in project_ids)
            cur.execute(f"SELECT id FROM tasks WHERE project_id IN ({ph})", project_ids)
            task_ids = [r["id"] for r in cur.fetchall()]

        if task_ids:
            ph = ",".join("?" for _ in task_ids)
            conn.execute(
                f"DELETE FROM task_dependencies WHERE task_id IN ({ph}) OR depends_on_task_id IN ({ph})",
                task_ids + task_ids,
            )
            for tbl in ("task_comments", "comments", "task_attachments", "time_logs", "activity_logs"):
                conn.execute(f"DELETE FROM {tbl} WHERE task_id IN ({ph})", task_ids)
        if client_ids:
            ph = ",".join("?" for _ in client_ids)
            for tbl in ("client_meetings", "compliance_items", "deal_stages"):
                conn.execute(f"DELETE FROM {tbl} WHERE client_id IN ({ph})", client_ids)
        if user_ids:
            ph = ",".join("?" for _ in user_ids)
            for tbl in ("notifications", "calendar_tokens", "password_resets"):
                conn.execute(f"DELETE FROM {tbl} WHERE user_id IN ({ph})", user_ids)
        if project_ids:
            ph = ",".join("?" for _ in project_ids)
            conn.execute(f"DELETE FROM project_attachments WHERE project_id IN ({ph})", project_ids)

        conn.execute("DELETE FROM tasks WHERE project_id IN (SELECT id FROM projects WHERE organization_id = ?)", (org_id,))
        conn.execute("DELETE FROM clients WHERE organization_id = ?", (org_id,))
        conn.execute("DELETE FROM projects WHERE organization_id = ?", (org_id,))
        conn.execute("DELETE FROM invite_tokens WHERE organization_id = ?", (org_id,))
        conn.execute("DELETE FROM users WHERE organization_id = ?", (org_id,))
        deleted = conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
        conn.commit()
        return deleted.rowcount > 0
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
