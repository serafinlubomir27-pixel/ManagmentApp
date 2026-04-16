"""
Calendar View — mesacny kalendar s task due-date bodkami a detail panelom.
Dual-mode: TODAY_CELL_BG ako tuple, STATUS_COLORS z theme, Segoe UI font.
"""
import calendar
import datetime

import customtkinter as ctk

from repositories.task_repo import get_tasks_with_due_dates
from ui.theme import (
    PRIMARY, PRIMARY_HOVER, DANGER, WARNING,
    BG_CARD, BG_ROW, BG_MAIN, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    STATUS_COLORS,
    get_font,
    FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG,
    RADIUS_SM, RADIUS_MD,
    HEIGHT_BTN_SM, HEIGHT_BTN_MD,
    SPACE_SM, SPACE_MD, SPACE_LG,
)

# ── Konštanty ──────────────────────────────────────────────────────────────────
MONTH_NAMES_SK = [
    "", "Januar", "Februar", "Marec", "April", "Maj", "Jun",
    "Jul", "August", "September", "Oktober", "November", "December",
]
DAY_HEADERS = ["Po", "Ut", "St", "St", "Pi", "So", "Ne"]

DOT_PAST   = DANGER
DOT_TODAY  = WARNING
DOT_FUTURE = PRIMARY

# Dual-mode tuple — CTk automaticky vyberie správny variant
TODAY_CELL_BG = ("#DCEEFF", "#0F2040")
EMPTY_CELL_BG = BG_MAIN           # priehľadné — rovnaká farba ako pozadie
SELECTED_BORDER = PRIMARY
CELL_HEIGHT = 60


class CalendarView(ctk.CTkFrame):
    """Mesačný kalendár s task due-date bodkami a pravostranným detail panelom."""

    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")

        self.user_id = user.get("id") if isinstance(user, dict) else user[0]

        today = datetime.date.today()
        self._year  = today.year
        self._month = today.month
        self._today = today
        self._selected_date: datetime.date | None = None
        self._day_cells: dict[datetime.date, ctk.CTkFrame] = {}
        self._tasks_by_date: dict[str, list[dict]] = {}

        self._reload_tasks()
        self._build_layout()
        self._render_calendar()

    # ── Dáta ───────────────────────────────────────────────────────────────────

    def _reload_tasks(self):
        self._tasks_by_date = {}
        rows = get_tasks_with_due_dates(self.user_id)
        for task in rows:
            key = str(task.get("due_date", ""))[:10]
            if key:
                self._tasks_by_date.setdefault(key, []).append(task)

    # ── Layout skeleton ────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # Ľavý panel — kalendár
        self._cal_outer = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        self._cal_outer.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE_SM))
        self._cal_outer.grid_rowconfigure(0, weight=0)
        self._cal_outer.grid_rowconfigure(1, weight=0)
        self._cal_outer.grid_rowconfigure(2, weight=1)
        self._cal_outer.grid_columnconfigure(0, weight=1)

        # Pravý panel — detail
        self._detail_frame = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        self._detail_frame.grid(row=0, column=1, sticky="nsew", padx=(SPACE_SM, 0))
        self._build_detail_panel()

    # ── Render kalendára ───────────────────────────────────────────────────────

    def _render_calendar(self):
        for attr in ("_cal_grid", "_nav_frame", "_header_frame"):
            if hasattr(self, attr) and getattr(self, attr) is not None:
                getattr(self, attr).destroy()

        self._day_cells = {}
        self._build_nav_header()
        self._build_day_headers()
        self._build_day_cells()

    def _build_nav_header(self):
        self._nav_frame = ctk.CTkFrame(self._cal_outer, fg_color="transparent")
        self._nav_frame.grid(row=0, column=0, sticky="ew", padx=SPACE_MD, pady=(SPACE_MD, SPACE_SM))
        self._nav_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            self._nav_frame, text="←", width=32, height=32,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_PRIMARY, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_MD),
            command=self._prev_month,
        ).grid(row=0, column=0, padx=(0, SPACE_SM))

        ctk.CTkLabel(
            self._nav_frame,
            text=f"{MONTH_NAMES_SK[self._month]} {self._year}",
            font=get_font(FONT_SIZE_LG, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1)

        ctk.CTkButton(
            self._nav_frame, text="→", width=32, height=32,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_PRIMARY, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_MD),
            command=self._next_month,
        ).grid(row=0, column=2, padx=(SPACE_SM, SPACE_MD))

        ctk.CTkButton(
            self._nav_frame, text="Dnes", width=64, height=HEIGHT_BTN_SM,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            corner_radius=RADIUS_SM, font=get_font(FONT_SIZE_BASE),
            command=self._goto_today,
        ).grid(row=0, column=3)

    def _build_day_headers(self):
        self._header_frame = ctk.CTkFrame(self._cal_outer, fg_color="transparent")
        self._header_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=(0, 2))
        for c in range(7):
            self._header_frame.grid_columnconfigure(c, weight=1)

        for col, name in enumerate(DAY_HEADERS):
            ctk.CTkLabel(
                self._header_frame, text=name,
                font=get_font(FONT_SIZE_SM, "bold"),
                text_color=TEXT_SECONDARY, anchor="center",
            ).grid(row=0, column=col, sticky="ew", padx=2)

    def _build_day_cells(self):
        self._cal_grid = ctk.CTkFrame(self._cal_outer, fg_color="transparent")
        self._cal_grid.grid(row=2, column=0, sticky="nsew", padx=2, pady=(0, SPACE_SM))

        weeks = calendar.monthcalendar(self._year, self._month)
        while len(weeks) < 6:
            weeks.append([0, 0, 0, 0, 0, 0, 0])

        for c in range(7):
            self._cal_grid.grid_columnconfigure(c, weight=1)
        for r in range(6):
            self._cal_grid.grid_rowconfigure(r, weight=1, uniform="cal_row")

        for row_idx, week in enumerate(weeks):
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    pad = ctk.CTkFrame(
                        self._cal_grid, fg_color=EMPTY_CELL_BG,
                        corner_radius=RADIUS_SM, height=CELL_HEIGHT,
                    )
                    pad.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
                else:
                    cell_date = datetime.date(self._year, self._month, day_num)
                    self._make_day_cell(row_idx, col_idx, cell_date)

    def _make_day_cell(self, grid_row: int, col: int, date: datetime.date):
        is_today    = (date == self._today)
        is_selected = (date == self._selected_date)

        bg = TODAY_CELL_BG if is_today else BG_ROW

        cell_kwargs = dict(fg_color=bg, corner_radius=RADIUS_SM, height=CELL_HEIGHT)
        if is_selected:
            cell_kwargs["border_color"] = SELECTED_BORDER
            cell_kwargs["border_width"] = 2

        cell = ctk.CTkFrame(self._cal_grid, **cell_kwargs)
        cell.grid(row=grid_row, column=col, sticky="nsew", padx=2, pady=2)
        cell.grid_rowconfigure(0, weight=0)
        cell.grid_rowconfigure(1, weight=1)
        cell.grid_columnconfigure(0, weight=1)

        self._day_cells[date] = cell

        num_label = ctk.CTkLabel(
            cell,
            text=str(date.day),
            font=get_font(FONT_SIZE_BASE, "bold" if is_today else "normal"),
            text_color=PRIMARY if is_today else TEXT_SECONDARY,
            anchor="ne",
        )
        num_label.grid(row=0, column=0, sticky="ne", padx=SPACE_SM, pady=(SPACE_SM, 0))

        callback = lambda e, d=date: self._on_day_click(d)
        cell.bind("<Button-1>", callback)
        num_label.bind("<Button-1>", callback)

        date_key = date.strftime("%Y-%m-%d")
        tasks_for_day = self._tasks_by_date.get(date_key, [])
        if tasks_for_day:
            self._add_dots(cell, date, tasks_for_day, callback)

    def _add_dots(self, cell, date, tasks, callback=None):
        dot_frame = ctk.CTkFrame(cell, fg_color="transparent")
        dot_frame.grid(row=1, column=0, sticky="sw", padx=3, pady=(0, 3))
        if callback:
            dot_frame.bind("<Button-1>", callback)

        visible = tasks[:3]
        extra   = len(tasks) - 3

        for i, task in enumerate(visible):
            color = self._dot_color(task, date)
            dot   = ctk.CTkLabel(
                dot_frame, text="●",
                font=get_font(FONT_SIZE_SM),
                text_color=color, fg_color="transparent", width=10,
            )
            dot.grid(row=0, column=i, padx=1)
            dot.bind("<Button-1>", lambda e, d=date: self._on_day_click(d))

        if extra > 0:
            ctk.CTkLabel(
                dot_frame, text=f"+{extra}",
                font=get_font(FONT_SIZE_SM),
                text_color=TEXT_SECONDARY, fg_color="transparent", width=20,
            ).grid(row=0, column=3, padx=1)

    def _dot_color(self, task: dict, date: datetime.date) -> tuple:
        if task.get("status") == "completed":
            return DOT_FUTURE
        if date < self._today:
            return DOT_PAST
        if date == self._today:
            return DOT_TODAY
        return DOT_FUTURE

    # ── Detail panel ───────────────────────────────────────────────────────────

    def _build_detail_panel(self):
        self._detail_frame.grid_rowconfigure(0, weight=0)
        self._detail_frame.grid_rowconfigure(1, weight=1)
        self._detail_frame.grid_columnconfigure(0, weight=1)

        self._detail_title = ctk.CTkLabel(
            self._detail_frame,
            text="Vyberte den",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY, anchor="w",
        )
        self._detail_title.grid(row=0, column=0, sticky="ew", padx=SPACE_LG, pady=(SPACE_LG, SPACE_SM))

        self._task_scroll = ctk.CTkScrollableFrame(
            self._detail_frame, fg_color="transparent",
        )
        self._task_scroll.grid(row=1, column=0, sticky="nsew", padx=SPACE_SM, pady=(0, SPACE_SM))
        self._task_scroll.grid_columnconfigure(0, weight=1)

    def _refresh_detail_panel(self, date: datetime.date):
        date_key     = date.strftime("%Y-%m-%d")
        date_display = date.strftime("%d. %m. %Y")
        self._detail_title.configure(text=f"Ulohy — {date_display}")

        for w in self._task_scroll.winfo_children():
            w.destroy()

        tasks = self._tasks_by_date.get(date_key, [])
        if not tasks:
            ctk.CTkLabel(
                self._task_scroll,
                text="Ziadne ulohy pre tento den.",
                text_color=TEXT_SECONDARY, font=get_font(FONT_SIZE_BASE), anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=SPACE_SM, pady=SPACE_SM)
            return

        for idx, task in enumerate(tasks):
            self._add_task_row(idx, task)

    def _add_task_row(self, idx: int, task: dict):
        status      = task.get("status", "pending")
        badge_color = STATUS_COLORS.get(status, STATUS_COLORS["pending"])

        row_frame = ctk.CTkFrame(
            self._task_scroll, fg_color=BG_ROW, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        row_frame.grid(row=idx, column=0, sticky="ew", padx=2, pady=3)
        row_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row_frame, text="  ", fg_color=badge_color,
            width=6, corner_radius=3,
        ).grid(row=0, column=0, rowspan=2, sticky="ns", padx=(SPACE_SM, SPACE_SM), pady=SPACE_SM)

        ctk.CTkLabel(
            row_frame, text=task.get("name", "—"),
            font=get_font(FONT_SIZE_BASE, "bold"),
            text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, SPACE_SM), pady=(SPACE_SM, 0))

        ctk.CTkLabel(
            row_frame, text=task.get("project_name", ""),
            font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY, anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, SPACE_SM), pady=(0, SPACE_SM))

    # ── Selection update ───────────────────────────────────────────────────────

    def _update_selection(self, old_date, new_date):
        if old_date and old_date in self._day_cells:
            old_cell = self._day_cells[old_date]
            old_cell.configure(
                fg_color=TODAY_CELL_BG if (old_date == self._today) else BG_ROW,
                border_width=0,
            )
        if new_date and new_date in self._day_cells:
            new_cell = self._day_cells[new_date]
            new_cell.configure(
                fg_color=TODAY_CELL_BG if (new_date == self._today) else BG_ROW,
                border_color=SELECTED_BORDER,
                border_width=2,
            )

    # ── Event handlers ─────────────────────────────────────────────────────────

    def _on_day_click(self, date: datetime.date):
        old = self._selected_date
        self._selected_date = date
        self._update_selection(old, date)
        self._refresh_detail_panel(date)

    def _prev_month(self):
        self._month, self._year = (12, self._year - 1) if self._month == 1 else (self._month - 1, self._year)
        self._selected_date = None
        self._render_calendar()

    def _next_month(self):
        self._month, self._year = (1, self._year + 1) if self._month == 12 else (self._month + 1, self._year)
        self._selected_date = None
        self._render_calendar()

    def _goto_today(self):
        self._year  = self._today.year
        self._month = self._today.month
        self._selected_date = self._today
        self._render_calendar()
        self._refresh_detail_panel(self._today)
