"""Repository for client module: clients, meetings, compliance, deal stages."""
from __future__ import annotations
from repositories.base_repo import get_connection, rows_to_dicts, row_to_dict

# ── Clients ────────────────────────────────────────────────────────────────────

def create_client(
    name: str,
    advisor_id: int,
    organization_id: int,
    email: str | None = None,
    phone: str | None = None,
    category: str = "retail",
    risk_profile: str = "balanced",
    notes: str | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO clients (name, email, phone, category, risk_profile, advisor_id, notes, organization_id)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (name, email, phone, category, risk_profile, advisor_id, notes, organization_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_clients(organization_id: int, advisor_id: int | None = None) -> list[dict]:
    """Return clients OF THE GIVEN ORGANIZATION. If advisor_id given, filter by it too."""
    conn = get_connection()
    try:
        if advisor_id:
            rows = conn.execute(
                "SELECT * FROM clients WHERE archived = 0 AND organization_id = ? AND advisor_id = ? ORDER BY name",
                (organization_id, advisor_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM clients WHERE archived = 0 AND organization_id = ? ORDER BY name",
                (organization_id,),
            ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def get_client_by_id(client_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def update_client(client_id: int, fields: dict) -> bool:
    allowed = {"name", "email", "phone", "category", "risk_profile", "advisor_id", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_connection()
    try:
        cur = conn.execute(
            f"UPDATE clients SET {set_clause} WHERE id = ?",
            list(updates.values()) + [client_id],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def archive_client(client_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("UPDATE clients SET archived = 1 WHERE id = ?", (client_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_client_projects(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM projects WHERE client_id = ? ORDER BY created_at DESC",
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def link_project_to_client(project_id: int, client_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE projects SET client_id = ? WHERE id = ?",
            (client_id, project_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Meetings ───────────────────────────────────────────────────────────────────

def add_meeting(
    client_id: int,
    user_id: int,
    meeting_date: str,
    notes: str = "",
    follow_ups: str = "[]",
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO client_meetings (client_id, user_id, meeting_date, notes, follow_ups) VALUES (?,?,?,?,?)",
            (client_id, user_id, meeting_date, notes, follow_ups),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_meetings(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT m.*, u.username, u.full_name
            FROM client_meetings m
            JOIN users u ON m.user_id = u.id
            WHERE m.client_id = ?
            ORDER BY m.meeting_date DESC, m.created_at DESC
            """,
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def delete_meeting(meeting_id: int, user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM client_meetings WHERE id = ? AND user_id = ?",
            (meeting_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Compliance ─────────────────────────────────────────────────────────────────

COMPLIANCE_TYPES = [
    "kyc", "suitability", "aml", "id_document",
    "risk_questionnaire", "contract", "mifid_disclosure", "other",
]


def add_compliance_item(
    client_id: int,
    item_type: str,
    due_date: str | None = None,
    notes: str | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO compliance_items (client_id, item_type, due_date, notes) VALUES (?,?,?,?)",
            (client_id, item_type, due_date, notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_compliance_item(item_id: int) -> dict | None:
    """Return a single compliance item (incl. its client_id) or None — pre kontrolu prístupu."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM compliance_items WHERE id = ?", (item_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_compliance_items(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM compliance_items WHERE client_id = ? ORDER BY created_at ASC",
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def update_compliance_item(item_id: int, fields: dict) -> bool:
    allowed = {"status", "due_date", "completed_by", "completed_at", "document_path", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_connection()
    try:
        cur = conn.execute(
            f"UPDATE compliance_items SET {set_clause} WHERE id = ?",
            list(updates.values()) + [item_id],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Deal stages ────────────────────────────────────────────────────────────────

DEAL_STAGES = ["lead", "contact", "analysis", "proposal", "signed", "active", "lost"]

STAGE_LABELS: dict[str, str] = {
    "lead":     "Potenciálny",
    "contact":  "Prvý kontakt",
    "analysis": "Analýza potrieb",
    "proposal": "Návrh",
    "signed":   "Podpis",
    "active":   "Aktívny klient",
    "lost":     "Stratený",
}


def get_deal(client_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM deal_stages WHERE client_id = ? ORDER BY id DESC LIMIT 1",
            (client_id,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def upsert_deal(
    client_id: int,
    stage: str,
    deal_value: float | None = None,
    commission_expected: float | None = None,
    commission_received: float | None = None,
    currency: str = "EUR",
    notes: str | None = None,
) -> int:
    """Create or update the deal record for a client. Returns id."""
    existing = get_deal(client_id)
    conn = get_connection()
    try:
        if existing:
            conn.execute(
                """UPDATE deal_stages SET stage=?, deal_value=?, commission_expected=?,
                   commission_received=?, currency=?, notes=?,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (stage, deal_value, commission_expected, commission_received,
                 currency, notes, existing["id"]),
            )
            conn.commit()
            return existing["id"]
        else:
            cur = conn.execute(
                """INSERT INTO deal_stages
                   (client_id, stage, deal_value, commission_expected, commission_received, currency, notes)
                   VALUES (?,?,?,?,?,?,?)""",
                (client_id, stage, deal_value, commission_expected, commission_received, currency, notes),
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_all_deals_for_advisor(organization_id: int, advisor_id: int | None = None) -> list[dict]:
    """Return deals (joined with client info) for the pipeline view, scoped to one organization."""
    conn = get_connection()
    try:
        if advisor_id:
            rows = conn.execute(
                """
                SELECT ds.*, c.name AS client_name, c.category, c.email
                FROM deal_stages ds
                JOIN clients c ON ds.client_id = c.id
                WHERE c.organization_id = ? AND c.advisor_id = ? AND c.archived = 0
                ORDER BY ds.updated_at DESC
                """,
                (organization_id, advisor_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ds.*, c.name AS client_name, c.category, c.email
                FROM deal_stages ds
                JOIN clients c ON ds.client_id = c.id
                WHERE c.organization_id = ? AND c.archived = 0
                ORDER BY ds.updated_at DESC
                """,
                (organization_id,),
            ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


# ── CRM: história interakcií ──────────────────────────────────────────────────

ACTIVITY_TYPES = ["note", "call", "email", "meeting", "document", "other"]


def add_activity(
    client_id: int,
    user_id: int,
    activity_type: str = "note",
    subject: str = "",
    body: str = "",
    occurred_at: str | None = None,
) -> int:
    """Zapíše interakciu s klientom. Bez occurred_at sa použije aktuálny čas."""
    conn = get_connection()
    try:
        if occurred_at:
            cur = conn.execute(
                """INSERT INTO client_activities
                   (client_id, user_id, activity_type, subject, body, occurred_at)
                   VALUES (?,?,?,?,?,?)""",
                (client_id, user_id, activity_type, subject, body, occurred_at),
            )
        else:
            cur = conn.execute(
                """INSERT INTO client_activities
                   (client_id, user_id, activity_type, subject, body)
                   VALUES (?,?,?,?,?)""",
                (client_id, user_id, activity_type, subject, body),
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_activities(client_id: int, limit: int = 100) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT a.*, u.username, u.full_name
            FROM client_activities a
            JOIN users u ON a.user_id = u.id
            WHERE a.client_id = ?
            ORDER BY a.occurred_at DESC, a.id DESC
            LIMIT ?
            """,
            (client_id, limit),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def delete_activity(activity_id: int, user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM client_activities WHERE id = ? AND user_id = ?",
            (activity_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── CRM: naplánované úlohy ku klientovi ───────────────────────────────────────

def add_client_task(
    client_id: int,
    created_by: int,
    title: str,
    due_date: str | None = None,
    priority: str = "medium",
    assigned_to: int | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO client_tasks
               (client_id, created_by, title, due_date, priority, assigned_to)
               VALUES (?,?,?,?,?,?)""",
            (client_id, created_by, title, due_date or None, priority,
             assigned_to if assigned_to else created_by),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_client_tasks(client_id: int, include_done: bool = True) -> list[dict]:
    conn = get_connection()
    try:
        # `done` je BOOLEAN — porovnanie s 0 by v PostgreSQL zlyhalo.
        where = "" if include_done else " AND t.done = FALSE"
        rows = conn.execute(
            f"""
            SELECT t.*, u.username AS assignee_username, u.full_name AS assignee_name
            FROM client_tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.client_id = ?{where}
            ORDER BY t.done, t.due_date, t.id
            """,
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def set_client_task_done(task_id: int, done: bool) -> bool:
    conn = get_connection()
    try:
        if done:
            cur = conn.execute(
                "UPDATE client_tasks SET done = TRUE, done_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,),
            )
        else:
            cur = conn.execute(
                "UPDATE client_tasks SET done = FALSE, done_at = NULL WHERE id = ?",
                (task_id,),
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_client_task(task_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM client_tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_upcoming_client_tasks(organization_id: int, advisor_id: int | None = None) -> list[dict]:
    """Nesplnené úlohy naprieč klientmi — podklad pre prehľad poradcu."""
    conn = get_connection()
    try:
        sql = """
            SELECT t.*, c.name AS client_name, c.id AS client_id
            FROM client_tasks t
            JOIN clients c ON t.client_id = c.id
            WHERE c.organization_id = ? AND t.done = FALSE
        """
        params: list = [organization_id]
        if advisor_id:
            sql += " AND c.advisor_id = ?"
            params.append(advisor_id)
        sql += " ORDER BY t.due_date, t.id"
        rows = conn.execute(sql, tuple(params)).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


# ── CRM: história posunov obchodu ─────────────────────────────────────────────

def add_stage_change(client_id: int, from_stage: str | None, to_stage: str, changed_by: int) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO deal_stage_history (client_id, from_stage, to_stage, changed_by) VALUES (?,?,?,?)",
            (client_id, from_stage, to_stage, changed_by),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_stage_history(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT h.*, u.username, u.full_name
            FROM deal_stage_history h
            JOIN users u ON h.changed_by = u.id
            WHERE h.client_id = ?
            ORDER BY h.changed_at DESC, h.id DESC
            """,
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()
