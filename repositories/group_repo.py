"""Etapy — zoskupenie úloh projektu pre prehľad.

Skupina je organizačný pohľad, nie prvok harmonogramu. CPM ďalej počíta
výhradne s jednotlivými úlohami a ich závislosťami; skupina nemá vlastné
trvanie ani väzby. Všetko, čo o nej vidno — postup, rozsah, či je hotová —
sa odvodzuje z detí pri čítaní. Nič z toho sa neukladá, takže to nemôže
rozísť s realitou.
"""
from __future__ import annotations

from repositories.base_repo import get_connection, rows_to_dicts, row_to_dict

# Farba sa drží ako názov, nie ako hex — o vzhľad sa stará frontend, takže
# zmena palety neznamená prepisovanie údajov v databáze.
PALETTE = ["brand", "violet", "emerald", "amber", "rose", "cyan"]


def _next_color(project_id: int, conn) -> str:
    """Prvá farba z palety, ktorú projekt ešte nepoužíva."""
    used = {r["color"] for r in conn.execute(
        "SELECT color FROM task_groups WHERE project_id = ?", (project_id,)
    ).fetchall()}
    for c in PALETTE:
        if c not in used:
            return c
    return PALETTE[len(used) % len(PALETTE)]


def create_group(project_id: int, name: str, task_ids: list[int] | None = None) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 AS n FROM task_groups WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        order = row_to_dict(row)["n"]

        cur = conn.execute(
            "INSERT INTO task_groups (project_id, name, color, sort_order) VALUES (?, ?, ?, ?)",
            (project_id, name.strip() or "Etapa", _next_color(project_id, conn), order),
        )
        group_id = cur.lastrowid

        if task_ids:
            _assign(conn, project_id, group_id, task_ids)

        conn.commit()
        return group_id
    finally:
        conn.close()


def _assign(conn, project_id: int, group_id: int | None, task_ids: list[int]) -> None:
    """Zaradí úlohy do skupiny. Filtrovanie podľa project_id bráni tomu, aby sa
    do etapy dostala úloha z cudzieho projektu podstrčeným identifikátorom."""
    if not task_ids:
        return
    ph = ",".join("?" for _ in task_ids)
    conn.execute(
        f"UPDATE tasks SET group_id = ? WHERE project_id = ? AND id IN ({ph})",
        (group_id, project_id, *task_ids),
    )


def assign_tasks(project_id: int, group_id: int, task_ids: list[int]) -> None:
    conn = get_connection()
    try:
        _assign(conn, project_id, group_id, task_ids)
        conn.commit()
    finally:
        conn.close()


def remove_tasks(project_id: int, task_ids: list[int]) -> None:
    """Vyradí úlohy z etapy. Úlohy ostávajú, len sa vrátia medzi nezaradené."""
    conn = get_connection()
    try:
        _assign(conn, project_id, None, task_ids)
        conn.commit()
    finally:
        conn.close()


def rename_group(group_id: int, name: str) -> None:
    conn = get_connection()
    try:
        conn.execute("UPDATE task_groups SET name = ? WHERE id = ?",
                     (name.strip() or "Etapa", group_id))
        conn.commit()
    finally:
        conn.close()


def set_color(group_id: int, color: str) -> None:
    if color not in PALETTE:
        return
    conn = get_connection()
    try:
        conn.execute("UPDATE task_groups SET color = ? WHERE id = ?", (color, group_id))
        conn.commit()
    finally:
        conn.close()


def delete_group(group_id: int) -> None:
    """Zruší etapu. Úlohy sa NEMAŽÚ — vrátia sa medzi nezaradené.

    Odpojenie je tu výslovne, nie cez ON DELETE SET NULL: SQLite kontrolu
    cudzích kľúčov štandardne nevynucuje, takže by na nej úlohy ostali visieť
    s neplatným group_id.
    """
    conn = get_connection()
    try:
        conn.execute("UPDATE tasks SET group_id = NULL WHERE group_id = ?", (group_id,))
        conn.execute("DELETE FROM task_groups WHERE id = ?", (group_id,))
        conn.commit()
    finally:
        conn.close()


def get_group_by_id(group_id: int) -> dict | None:
    conn = get_connection()
    try:
        return row_to_dict(
            conn.execute("SELECT * FROM task_groups WHERE id = ?", (group_id,)).fetchone()
        )
    finally:
        conn.close()


def get_groups_for_project(project_id: int) -> list[dict]:
    """Etapy aj s odvodeným súhrnom.

    `done` je pravda, keď má etapa aspoň jednu úlohu a všetky sú hotové — presne
    to, čo si používateľ predstaví pod „etapa je uzavretá". Prázdna etapa hotová
    nie je, inak by sa za hotovú vyhlásila hneď po založení.
    """
    conn = get_connection()
    try:
        groups = rows_to_dicts(conn.execute(
            "SELECT * FROM task_groups WHERE project_id = ? ORDER BY sort_order, id",
            (project_id,),
        ).fetchall())
        if not groups:
            return []

        stats = rows_to_dicts(conn.execute(
            """
            SELECT group_id,
                   COUNT(*)                                             AS total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN is_critical THEN 1 ELSE 0 END)          AS critical,
                   MIN(es)                                              AS start_day,
                   MAX(ef)                                              AS end_day
            FROM tasks
            WHERE project_id = ? AND group_id IS NOT NULL
            GROUP BY group_id
            """,
            (project_id,),
        ).fetchall())
        by_id = {s["group_id"]: s for s in stats}

        out = []
        for g in groups:
            s = by_id.get(g["id"], {})
            total = int(s.get("total") or 0)
            completed = int(s.get("completed") or 0)
            out.append({
                **g,
                "total_tasks": total,
                "completed_tasks": completed,
                "critical_tasks": int(s.get("critical") or 0),
                "progress": round(completed / total, 3) if total else 0.0,
                "done": total > 0 and completed == total,
                "start_day": s.get("start_day"),
                "end_day": s.get("end_day"),
            })
        return out
    finally:
        conn.close()
