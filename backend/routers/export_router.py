"""Export projektu — GET /projects/{id}/export/{pdf|csv|xlsx}"""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.deps import assert_project_access, get_current_user
from logic import web_export
from repositories import task_repo, time_repo

router = APIRouter(tags=["export"])

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _safe_filename(name: str, ext: str) -> str:
    """ASCII fallback názov — diakritika sa prenáša cez filename* (RFC 5987)."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_name).strip("_")
    return f"{ascii_name or 'projekt'}.{ext}"


def _attachment(content: bytes, project_name: str, ext: str) -> Response:
    ascii_name = _safe_filename(project_name, ext)
    utf8_name = quote(f"{project_name}.{ext}")
    return Response(
        content=content,
        media_type=MEDIA_TYPES[ext],
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_name}'
            ),
            # Bez tohto si prehliadač cez CORS hlavičku neprečíta a stiahne súbor bez názvu.
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


def _load(project_id: int, current_user: dict) -> tuple[dict, list[dict], list[dict]]:
    project = assert_project_access(project_id, current_user)
    tasks = task_repo.get_tasks_for_project_with_cpm(project_id)
    time_summary = time_repo.get_time_summary_for_project(project_id)
    return project, tasks, time_summary


@router.get("/projects/{project_id}/export/pdf")
def export_pdf(project_id: int, current_user: dict = Depends(get_current_user)):
    """PDF report — súhrn, Ganttov diagram, kritická cesta a tabuľka úloh s CPM."""
    project, tasks, time_summary = _load(project_id, current_user)
    content = web_export.build_project_pdf(project, tasks, time_summary)
    return _attachment(content, project.get("name") or "projekt", "pdf")


@router.get("/projects/{project_id}/export/csv")
def export_csv(project_id: int, current_user: dict = Depends(get_current_user)):
    """CSV úloh (oddeľovač `;`, UTF-8 BOM) — otvoriteľné priamo v Exceli."""
    project, tasks, time_summary = _load(project_id, current_user)
    content = web_export.build_tasks_csv(tasks, time_summary)
    return _attachment(content, project.get("name") or "projekt", "csv")


@router.get("/projects/{project_id}/export/xlsx")
def export_xlsx(project_id: int, current_user: dict = Depends(get_current_user)):
    """Excel zošit — hárok úloh s filtrami a hárok so súhrnom projektu."""
    project, tasks, time_summary = _load(project_id, current_user)
    try:
        content = web_export.build_tasks_xlsx(project, tasks, time_summary)
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Export do Excelu nie je na serveri dostupný (chýba openpyxl). Použi CSV.",
        )
    return _attachment(content, project.get("name") or "projekt", "xlsx")
