"""Calendar feed — iCal (.ics) endpoint + token management.

Public endpoint:  GET /calendar/{token}.ics  → RFC 5545 iCal feed
Private endpoint: GET /me/calendar-token      → get current token
                  POST /me/calendar-token      → generate / regenerate token
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from backend.deps import get_current_user
from repositories import calendar_repo, task_repo

router = APIRouter(tags=["calendar"])

# ── iCal status mapping ──────────────────────────────────────────────────────
_ICAL_STATUS = {
    "pending":     "NEEDS-ACTION",
    "in_progress": "IN-PROCESS",
    "completed":   "COMPLETED",
    "blocked":     "CANCELLED",
}


def _ical_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to iCal DATE value (YYYYMMDD)."""
    return date_str.replace("-", "")


def _ical_escape(text: str) -> str:
    """Escape special characters for iCal text values."""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _build_ical(tasks: list[dict], calendar_name: str = "Nodus úlohy") -> str:
    """Build RFC 5545 iCal string from task list."""
    now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Nodus//ManagmentApp//SK",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ical_escape(calendar_name)}",
        "X-WR-TIMEZONE:Europe/Bratislava",
        "X-WR-CALDESC:Úlohy z aplikácie Nodus",
    ]

    for t in tasks:
        if not t.get("due_date"):
            continue
        due_ymd = t["due_date"][:10]
        ical_date = _ical_date(due_ymd)

        # DTEND = next day (DATE-only events are exclusive end)
        due_dt = datetime.strptime(due_ymd, "%Y-%m-%d")
        next_day = due_dt.replace(day=due_dt.day + 1) if due_dt.day < 28 else \
            datetime(due_dt.year + (due_dt.month // 12), (due_dt.month % 12) + 1, 1)
        end_date = next_day.strftime("%Y%m%d")

        uid = f"task-{t['id']}@nodus.app"
        status_str = _ICAL_STATUS.get(t.get("status", "pending"), "NEEDS-ACTION")
        summary = _ical_escape(t.get("name", "Úloha"))
        proj = _ical_escape(t.get("project_name", ""))
        description = f"Projekt: {proj}\\nStatus: {t.get('status', '')}\\nPrioritizácia: {t.get('priority', 'medium')}"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{ical_date}",
            f"DTEND;VALUE=DATE:{end_date}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"STATUS:{status_str}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/calendar/{token}.ics", response_class=PlainTextResponse, include_in_schema=True)
def get_ical_feed(token: str):
    """Public iCal feed for a user's tasks with due dates.
    Subscribe this URL in Google Calendar / Apple Calendar / Outlook.
    """
    user_id = calendar_repo.get_user_id_for_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid calendar token")

    tasks = task_repo.get_tasks_with_due_dates(user_id, only_auto_calendar=True)
    ical_content = _build_ical(tasks)

    return PlainTextResponse(
        content=ical_content,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=nodus-tasks.ics",
            "Cache-Control": "no-cache, no-store",
        },
    )


@router.get("/me/calendar-token")
def get_my_calendar_token(current_user: dict = Depends(get_current_user)):
    """Get the current user's iCal calendar token (null if not generated yet)."""
    token = calendar_repo.get_token_for_user(current_user["id"])
    return {"token": token}


@router.post("/me/calendar-token", status_code=status.HTTP_201_CREATED)
def generate_calendar_token(current_user: dict = Depends(get_current_user)):
    """Generate (or regenerate) the iCal calendar token for the current user."""
    token = calendar_repo.create_or_replace_token(current_user["id"])
    return {"token": token}
