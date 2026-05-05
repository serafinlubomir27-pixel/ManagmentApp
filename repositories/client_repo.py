"""Repository for client module: clients, meetings, compliance, deal stages."""
from __future__ import annotations
from repositories.base_repo import get_connection, rows_to_dicts, row_to_dict

# ── Clients ────────────────────────────────────────────────────────────────────

def create_client(
    name: str,
    advisor_id: int,
    email: str | None = None,
    phone: str | None = None,
    category: str = "retail",
    risk_profile: str = "balanced",
    notes: str | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO clients (name, email, phone, category, risk_profile, advisor_id, notes) VALUES (?,?,?,?,?,?,?)",
            (name, email, phone, category, risk_profile, advisor_id, notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_clients(advisor_id: int | None = None) -> list[dict]:
    """Return clients. If advisor_id given, filter by it (for employee role)."""
    conn = get_connection()
    try:
        if advisor_id:
            rows = conn.execute(
                "SELECT * FROM clients WHERE archived = 0 AND advisor_id = ? ORDER BY name",
                (advisor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM clients WHERE archived = 0 ORDER BY name"
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


def get_all_deals_for_advisor(advisor_id: int | None = None) -> list[dict]:
    """Return all deals joined with client info for pipeline view."""
    conn = get_connection()
    try:
        if advisor_id:
            rows = conn.execute(
                """
                SELECT ds.*, c.name AS client_name, c.category, c.email
                FROM deal_stages ds
                JOIN clients c ON ds.client_id = c.id
                WHERE c.advisor_id = ? AND c.archived = 0
                ORDER BY ds.updated_at DESC
                """,
                (advisor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ds.*, c.name AS client_name, c.category, c.email
                FROM deal_stages ds
                JOIN clients c ON ds.client_id = c.id
                WHERE c.archived = 0
                ORDER BY ds.updated_at DESC
                """,
            ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()
