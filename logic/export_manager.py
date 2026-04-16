"""
PDF Export Manager — generuje profesionálny PDF report projektu.
Obsahuje: hlavičku, štatistiky, tabuľku úloh, Gantt chart ako obrázok.
Fonty: DejaVu Sans (bundled v matplotlib) — plná podpora slovenčiny + Unicode.
"""
from __future__ import annotations

import csv
import io
import os
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image,
)

from logic.cpm_engine import CPMResult, calculate_health_score
from repositories import task_repo

# ── Registrácia DejaVu fontov (bundled v matplotlib) ──────────────────────────
_FONT_DIR     = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
_FONT_REGULAR = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
_FONT_BOLD    = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")

def _register_fonts() -> tuple[str, str]:
    """Zaregistruje DejaVu fonty a vráti (regular_name, bold_name)."""
    regular = "DejaVu"
    bold    = "DejaVu-Bold"
    try:
        pdfmetrics.registerFont(TTFont(regular, _FONT_REGULAR))
        pdfmetrics.registerFont(TTFont(bold,    _FONT_BOLD))
        pdfmetrics.registerFontFamily(
            "DejaVu", normal=regular, bold=bold,
        )
    except Exception:
        # Fallback na Helvetica (bez diakritiky) ak sa font nenájde
        regular = "Helvetica"
        bold    = "Helvetica-Bold"
    return regular, bold


# ── Farby ──────────────────────────────────────────────────────────────────────
RL_PRIMARY  = colors.HexColor("#1976D2")
RL_DANGER   = colors.HexColor("#D32F2F")
RL_WARNING  = colors.HexColor("#F57C00")
RL_SUCCESS  = colors.HexColor("#388E3C")
RL_BG_DARK  = colors.HexColor("#263238")
RL_BG_ROW   = colors.HexColor("#ECEFF1")
RL_BG_CRIT  = colors.HexColor("#FFEBEE")
RL_GRID     = colors.HexColor("#CFD8DC")
RL_TEXT     = colors.HexColor("#212121")
RL_TEXT_DIM = colors.HexColor("#546E7A")


# ── Štýly ──────────────────────────────────────────────────────────────────────

def _styles(F: str, FB: str) -> dict:
    """F = regular font name, FB = bold font name."""
    return {
        "title": ParagraphStyle(
            "title", fontSize=18, fontName=FB,
            textColor=colors.white, leading=22, spaceAfter=0,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=9, fontName=F,
            textColor=colors.HexColor("#B0BEC5"),
        ),
        "section": ParagraphStyle(
            "section", fontSize=12, fontName=FB,
            textColor=RL_PRIMARY, spaceBefore=12, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body", fontSize=9, fontName=F,
            textColor=RL_TEXT, leading=13,
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=7, fontName=F,
            textColor=RL_TEXT_DIM, alignment=TA_CENTER,
        ),
        "th": ParagraphStyle(
            "th", fontSize=8, fontName=FB,
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "cell": ParagraphStyle(
            "cell", fontSize=8, fontName=F, textColor=RL_TEXT,
        ),
        "cell_red": ParagraphStyle(
            "cell_red", fontSize=8, fontName=FB,
            textColor=RL_DANGER,
        ),
    }


# ── Gantt ako PNG ───────────────────────────────────────────────────────────────

def _gantt_image(cpm: CPMResult) -> io.BytesIO | None:
    tasks = cpm.tasks
    if not tasks:
        return None

    critical_ids = set(cpm.critical_path)
    sorted_tasks = sorted(tasks, key=lambda t: (t.es, t.id))
    n   = len(sorted_tasks)
    dur = cpm.project_duration

    fig_h = max(2.0, 0.38 * n + 0.7)
    fig_w = min(max(7.0, dur * 0.35 + 2.0), 13.0)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#F5F5F5")

    for i, t in enumerate(sorted_tasks):
        y   = n - 1 - i
        col = ("#43A047" if t.status == "completed"
               else "#E53935" if t.id in critical_ids
               else "#1976D2")

        if t.total_float > 0:
            ax.barh(y, t.total_float, left=t.ef,
                    height=0.22, color="#90CAF9", alpha=0.5, zorder=1)

        ax.barh(y, t.duration, left=t.es,
                height=0.55, color=col, alpha=0.88,
                edgecolor="#fff", linewidth=0.4, zorder=2)

        lbl = t.name[:15] + "..." if len(t.name) > 15 else t.name
        if t.duration >= 3:
            ax.text(t.es + t.duration / 2, y, lbl,
                    ha="center", va="center", fontsize=6,
                    color="white", fontweight="bold", zorder=3)
        else:
            ax.text(t.ef + 0.2, y, lbl,
                    ha="left", va="center", fontsize=6, color="#333", zorder=3)

    ax.set_yticks(range(n))
    ax.set_yticklabels(
        [sorted_tasks[n - 1 - i].name[:20] for i in range(n)],
        fontsize=6.5, color="#333",
    )
    ax.set_xlim(-0.5, dur + 1)
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_xlabel("Den", fontsize=7, color="#555")
    ax.tick_params(axis="x", labelsize=6.5, colors="#555")
    ax.xaxis.grid(True, color="#CCC", linestyle="--", linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#CCC")
        spine.set_linewidth(0.4)

    legend = [
        mpatches.Patch(color="#E53935", label="Kriticka"),
        mpatches.Patch(color="#1976D2", label="Normalna"),
        mpatches.Patch(color="#43A047", label="Dokoncena"),
        mpatches.Patch(color="#90CAF9", alpha=0.5, label="Float"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=6, framealpha=0.85)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


# ── Hlavná export funkcia ───────────────────────────────────────────────────────

def export_project_pdf(
    project_name: str,
    project_id: int,
    cpm_result: CPMResult,
    output_path: str,
) -> bool:
    """
    Vygeneruje PDF report projektu do output_path.
    Vracia True ak uspeje.
    """
    try:
        F, FB = _register_fonts()
        S = _styles(F, FB)
        page_w = A4[0] - 3.6 * cm

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            title=f"Projekt: {project_name}",
            author="ManagmentApp v1.0",
        )
        story = []

        # Načítaj dáta
        tasks_all = task_repo.get_tasks_for_project_with_cpm(project_id)
        total     = len(tasks_all)
        completed = sum(1 for t in tasks_all if t.get("status") == "completed")
        blocked   = sum(1 for t in tasks_all if t.get("status") == "blocked")
        pct       = int(completed / total * 100) if total else 0

        cpm      = cpm_result
        duration = cpm.project_duration if cpm and cpm.is_valid else 0
        delay    = cpm.total_project_delay if cpm and cpm.is_valid else 0
        crit_cnt = len(cpm.critical_path) if cpm and cpm.is_valid else 0

        if cpm and cpm.is_valid and cpm.tasks:
            h_score, h_label = calculate_health_score(
                cpm.tasks, cpm.project_duration,
                cpm.project_duration_without_delays + 5,
            )
        else:
            h_score, h_label = 100, "Healthy"

        h_hex = ("#388E3C" if h_label == "Healthy"
                 else "#F57C00" if h_label == "At Risk"
                 else "#D32F2F")

        # ── 1. Banner ──────────────────────────────────────────────────────────
        today_str = date.today().strftime("%d. %m. %Y")
        # Dvojriadkový banner: celá šírka pre názov (nikdy sa neorezáva),
        # druhý riadok — dátum vpravo. VALIGN=TOP zabraňuje vertikálnemu orezaniu.
        banner = Table(
            [
                [Paragraph(project_name, S["title"]), ""],
                ["", Paragraph(f"Vygenerovane: {today_str}", S["subtitle"])],
            ],
            colWidths=[page_w * 0.65, page_w * 0.35],
            rowHeights=[None, None],
        )
        banner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), RL_BG_DARK),
            ("TOPPADDING",    (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 14),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("ALIGN",         (1, 1), (1, 1),   "RIGHT"),
            # Názov sa roztiahne cez oba stĺpce
            ("SPAN",          (0, 0), (1, 0)),
        ]))
        story += [banner, Spacer(1, 0.4 * cm)]

        # ── 2. Štatistiky (2 riadky × 3 karty) ────────────────────────────────
        story.append(Paragraph("Prehlad projektu", S["section"]))

        def stat_para(label: str, value: str, hex_color: str) -> Paragraph:
            return Paragraph(
                f'<font size="7.5" color="#546E7A">{label}</font><br/>'
                f'<font size="15" color="{hex_color}"><b>{value}</b></font>',
                S["body"],
            )

        cw3    = [page_w / 3] * 3
        ts_card = TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), RL_BG_ROW),
            ("BOX",        (0, 0), (-1, -1), 0.5, RL_GRID),
            ("INNERGRID",  (0, 0), (-1, -1), 0.5, RL_GRID),
            ("PADDING",    (0, 0), (-1, -1), 10),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ])
        delay_hex = "#D32F2F" if delay > 0 else "#388E3C"
        delay_val = f"{delay} dni" if delay > 0 else "Ziadne"

        row1 = Table([[
            stat_para("Progress",       f"{pct}%",             "#1976D2"),
            stat_para("Dokoncene",      f"{completed}/{total}", "#388E3C"),
            stat_para("Kriticka cesta", f"{crit_cnt} uloh",    "#F57C00"),
        ]], colWidths=cw3)
        row1.setStyle(ts_card)

        row2 = Table([[
            stat_para("Trvanie",      f"{duration} dni", "#1976D2"),
            stat_para("Oneskorenie",  delay_val,          delay_hex),
            stat_para("Zdravie",      f"{h_score} – {h_label}", h_hex),
        ]], colWidths=cw3)
        row2.setStyle(ts_card)

        story += [row1, Spacer(1, 0.15 * cm), row2, Spacer(1, 0.25 * cm)]

        # ── 3. Upozornenia ─────────────────────────────────────────────────────
        alerts = []
        if blocked:
            alerts.append(f"{blocked} zablokovanych uloh")
        if delay > 0:
            alerts.append(f"Projekt oneskoreny o {delay} dni")
        if cpm and not cpm.is_valid:
            for err in cpm.errors:
                alerts.append(f"CPM chyba: {err}")

        if alerts:
            story.append(Paragraph("Upozornenia", S["section"]))
            for a in alerts:
                story.append(Paragraph(f"• {a}", S["body"]))
            story.append(Spacer(1, 0.2 * cm))

        # ── 4. Gantt chart ─────────────────────────────────────────────────────
        if cpm and cpm.is_valid and cpm.tasks:
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=RL_GRID, spaceAfter=6))
            story.append(Paragraph("Gantt Chart", S["section"]))
            buf = _gantt_image(cpm)
            if buf:
                story.append(Image(buf, width=page_w, height=page_w * 0.44))
                story.append(Spacer(1, 0.3 * cm))

        # ── 5. Tabuľka úloh ────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=RL_GRID, spaceAfter=6))
        story.append(Paragraph("Zoznam uloh", S["section"]))

        if tasks_all:
            cws = [
                page_w * 0.28,  # Názov
                page_w * 0.13,  # Stav
                page_w * 0.08,  # Trvanie
                page_w * 0.07,  # ES
                page_w * 0.07,  # EF
                page_w * 0.07,  # Float
                page_w * 0.15,  # Kategória
                page_w * 0.15,  # Kritická
            ]
            headers = ["Nazov", "Stav", "Trv.", "ES", "EF",
                       "Float", "Kategoria", "Kriticka"]
            data = [[Paragraph(h, S["th"]) for h in headers]]

            STATUS_SK = {
                "pending":     "Caka",
                "in_progress": "Prebieha",
                "completed":   "Hotova",
                "blocked":     "Blokovana",
            }
            row_bg = []
            for idx, t in enumerate(tasks_all):
                crit       = bool(t.get("is_critical"))
                ri         = idx + 1
                cell_style = S["cell_red"] if crit else S["cell"]
                crit_label = "[!] Ano" if crit else "Nie"
                data.append([
                    Paragraph(t.get("name", ""), cell_style),
                    Paragraph(STATUS_SK.get(t.get("status", ""), "—"), S["cell"]),
                    Paragraph(f"{t.get('duration') or 1}d",            S["cell"]),
                    Paragraph(str(t.get("es", 0)),                     S["cell"]),
                    Paragraph(str(t.get("ef", 0)),                     S["cell"]),
                    Paragraph(str(t.get("total_float", 0)),            S["cell"]),
                    Paragraph(t.get("category") or "—",                S["cell"]),
                    Paragraph(crit_label,                              cell_style),
                ])
                if crit:
                    row_bg.append(("BACKGROUND", (0, ri), (-1, ri), RL_BG_CRIT))

            tbl = Table(data, colWidths=cws, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",     (0, 0), (-1, 0),  RL_PRIMARY),
                ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
                ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
                ("ALIGN",          (0, 0), (0, -1),  "LEFT"),
                ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING",        (0, 0), (-1, -1), 5),
                ("GRID",           (0, 0), (-1, -1), 0.4, RL_GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, RL_BG_ROW]),
            ] + row_bg))
            story.append(tbl)

        # ── 6. Kritická cesta ──────────────────────────────────────────────────
        if cpm and cpm.is_valid and cpm.critical_path:
            story.append(Spacer(1, 0.35 * cm))
            story.append(Paragraph("Kriticka cesta", S["section"]))
            task_map = {t.id: t for t in cpm.tasks}
            path = " > ".join(
                task_map[tid].name for tid in cpm.critical_path if tid in task_map
            )
            story.append(Paragraph(
                f'<font color="#E53935"><b>{path}</b></font>', S["body"]
            ))
            delay_note = f" (oneskorenie: <b>{delay} dni</b>)" if delay > 0 else ""
            story.append(Paragraph(
                f"Celkove trvanie: <b>{cpm.project_duration} dni</b>{delay_note}",
                S["body"],
            ))

        # ── 7. Footer ──────────────────────────────────────────────────────────
        story += [
            Spacer(1, 0.5 * cm),
            HRFlowable(width="100%", thickness=0.5, color=RL_GRID),
            Spacer(1, 0.15 * cm),
            Paragraph(
                f"ManagmentApp v1.0  •  {today_str}  •  {project_name}",
                S["footer"],
            ),
        ]

        doc.build(story)
        return True

    except Exception as exc:
        import traceback
        print(f"PDF export chyba: {exc}")
        traceback.print_exc()
        return False


# ── CSV Export ────────────────────────────────────────────────────────────────

# Columns included in CSV export (in order)
CSV_FIELDS = [
    "id", "name", "status", "priority", "category",
    "duration", "due_date", "assigned_username",
    "es", "ef", "ls", "lf", "total_float", "is_critical",
    "description", "notes",
]

CSV_HEADERS = {
    "id": "ID", "name": "Názov", "status": "Stav", "priority": "Priorita",
    "category": "Kategória", "duration": "Trvanie (dni)", "due_date": "Deadline",
    "assigned_username": "Priradený", "es": "ES", "ef": "EF", "ls": "LS", "lf": "LF",
    "total_float": "Float", "is_critical": "Kritická cesta",
    "description": "Popis", "notes": "Poznámky",
}

# Import columns that must be present in an uploaded CSV
CSV_IMPORT_REQUIRED = ["name"]
CSV_IMPORT_OPTIONAL = ["status", "priority", "category", "duration", "due_date", "description", "notes"]

VALID_STATUSES  = {"pending", "in_progress", "completed", "blocked"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def export_tasks_csv(project_id: int, file_path: str) -> tuple[bool, str]:
    """Export all tasks for a project to a UTF-8 CSV file.

    Returns (success, message).
    """
    try:
        tasks = task_repo.get_tasks_for_project_with_cpm(project_id)
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=CSV_FIELDS,
                extrasaction="ignore",
            )
            # Write header row with human-readable names
            writer.writerow(CSV_HEADERS)
            for t in tasks:
                row = {k: t.get(k, "") for k in CSV_FIELDS}
                row["is_critical"] = "Áno" if row["is_critical"] else "Nie"
                writer.writerow(row)
        return True, f"Exportovaných {len(tasks)} úloh do {os.path.basename(file_path)}"
    except Exception as exc:
        return False, f"Chyba exportu: {exc}"


def import_tasks_csv(
    project_id: int,
    file_path: str,
    created_by: int,
) -> tuple[bool, str]:
    """Import tasks from a CSV file into a project.

    Expects UTF-8 (with or without BOM). First row = header.
    Returns (success, message) with count or error details.
    """
    from repositories.task_repo import create_task_from_template  # avoid circular at module level

    errors: list[str] = []
    imported = 0

    try:
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Map human-readable headers back to field names
            reverse_headers = {v: k for k, v in CSV_HEADERS.items()}

            for row_num, raw_row in enumerate(reader, start=2):
                # Normalise keys: strip whitespace, map translated headers → field names
                row = {}
                for k, v in raw_row.items():
                    key = (k or "").strip()
                    key = reverse_headers.get(key, key)
                    row[key] = (v or "").strip()

                # Validate required fields
                name = row.get("name", "").strip()
                if not name:
                    errors.append(f"Riadok {row_num}: chýba názov úlohy — preskočené")
                    continue

                # Sanitise optional fields
                status   = row.get("status", "pending")
                if status not in VALID_STATUSES:
                    status = "pending"

                priority = row.get("priority", "medium")
                if priority not in VALID_PRIORITIES:
                    priority = "medium"

                due_date = row.get("due_date") or None
                duration_raw = row.get("duration", "1")
                try:
                    duration = max(1, int(float(duration_raw)))
                except (ValueError, TypeError):
                    duration = 1

                description = row.get("description", "")
                notes = row.get("notes", "")
                category = row.get("category", "Other")

                # Insert via existing repo function
                try:
                    task_id = create_task_from_template(
                        project_id, name, description,
                        assigned_to=None, created_by=created_by, due_date=due_date,
                    )
                    # Update extra fields that create_task_from_template doesn't set
                    from repositories.base_repo import get_connection
                    conn = get_connection()
                    try:
                        conn.execute(
                            """UPDATE tasks SET status=?, priority=?, category=?,
                               duration=?, notes=? WHERE id=?""",
                            (status, priority, category, duration, notes, task_id),
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    imported += 1
                except Exception as exc:
                    errors.append(f"Riadok {row_num} ({name}): {exc}")

        msg = f"Importovaných {imported} úloh."
        if errors:
            msg += f"\nUpozornenia ({len(errors)}):\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... a {len(errors) - 5} ďalších"
        return True, msg

    except Exception as exc:
        return False, f"Chyba importu: {exc}"

