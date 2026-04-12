"""Custom monthly calendar screen — pure CustomTkinter, no tkcalendar."""
import calendar
import datetime

import customtkinter as ctk

from repositories.task_repo import get_tasks_with_due_dates
from ui.theme import (
    PRIMARY, DANGER, WARNING,
    BG_CARD, BG_MAIN,
    TEXT_PRIMARY, TEXT_SECONDARY,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MONTH_NAMES_SK = [
    "", "Január", "Február", "Marec", "Apríl", "Máj", "Jún",
    "Júl", "August", "September", "Október", "November", "December",
]
DAY_HEADERS = ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"]

DOT_PAST = DANGER          # #D32F2F  — overdue
DOT_TODAY = WARNING        # #F57C00  — due today
DOT_FUTURE = PRIMARY       # #1976D2  — future

TODAY_CELL_BG = "#1A2F4A"  # today highlight (dark mode)
EMPTY_CELL_BG = "#1A1A1A"  # padding / out-of-month cells
SELECTED_BORDER = PRIMARY

STATUS_COLORS = {
    "pending":     "#9E9E9E",
    "in_progress": "#4DB6AC",
    "completed":   "#81C784",
    "blocked":     "#EF9A9A",
}


class CalendarView(ctk.CTkFrame):
    """Monthly calendar with task due-date dots and a right-side task detail panel."""

    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")

        # Support both dict and legacy tuple user_data
        if isinstance(user, dict):
            self.user_id = user.get("id")
        else:
            self.user_id = user[0]

        today = datetime.date.today()
        self._year = today.year
        self._month = today.month
        self._today = today
        self._selected_date: datetime.date | None = None

        # Tasks keyed by date string "YYYY-MM-DD"
        self._tasks_by_date: dict[str, list[dict]] = {}
        self._reload_tasks()

        self._build_layout()
        self._render_calendar()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _reload_tasks(self):
        self._tasks_by_date = {}
        rows = get_tasks_with_due_dates(self.user_id)
        for task in rows:
            key = task.get("due_date", "")
            if key:
                # normalise to "YYYY-MM-DD" in case there's a time component
                key = str(key)[:10]
                self._tasks_by_date.setdefault(key, []).append(task)

    # ------------------------------------------------------------------
    # Layout skeleton (called once)
    # ------------------------------------------------------------------

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)   # calendar (2/3)
        self.grid_columnconfigure(1, weight=1)   # detail panel (1/3)

        # Left: calendar container
        self._cal_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        self._cal_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        # Right: detail panel
        self._detail_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        self._detail_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        self._build_detail_panel()

    # ------------------------------------------------------------------
    # Calendar rendering (re-called on month change)
    # ------------------------------------------------------------------

    def _render_calendar(self):
        """Destroy and rebuild only the calendar grid content."""
        for w in self._cal_frame.winfo_children():
            w.destroy()

        self._cal_frame.grid_rowconfigure(0, weight=0)   # header row
        self._cal_frame.grid_rowconfigure(1, weight=0)   # day-name row
        for r in range(2, 8):
            self._cal_frame.grid_rowconfigure(r, weight=1)
        for c in range(7):
            self._cal_frame.grid_columnconfigure(c, weight=1)

        self._build_nav_header()
        self._build_day_headers()
        self._build_day_cells()

    def _build_nav_header(self):
        nav = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
        nav.grid(row=0, column=0, columnspan=7, sticky="ew", padx=10, pady=(10, 4))
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav, text="←", width=32, height=32,
            fg_color="transparent", hover_color=BG_MAIN,
            text_color=TEXT_PRIMARY,
            command=self._prev_month,
        ).grid(row=0, column=0, padx=(0, 4))

        month_label = f"{MONTH_NAMES_SK[self._month]} {self._year}"
        ctk.CTkLabel(
            nav, text=month_label,
            font=("Arial", 16, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1)

        ctk.CTkButton(
            nav, text="→", width=32, height=32,
            fg_color="transparent", hover_color=BG_MAIN,
            text_color=TEXT_PRIMARY,
            command=self._next_month,
        ).grid(row=0, column=2, padx=(4, 8))

        ctk.CTkButton(
            nav, text="Dnes", width=64, height=28,
            fg_color=PRIMARY, hover_color="#1565C0",
            text_color=TEXT_PRIMARY, font=("Arial", 12),
            command=self._goto_today,
        ).grid(row=0, column=3, padx=(0, 0))

    def _build_day_headers(self):
        for col, name in enumerate(DAY_HEADERS):
            ctk.CTkLabel(
                self._cal_frame, text=name,
                font=("Arial", 12, "bold"),
                text_color=TEXT_SECONDARY,
                fg_color="transparent",
                anchor="center",
            ).grid(row=1, column=col, sticky="ew", padx=2, pady=(0, 4))

    def _build_day_cells(self):
        # calendar.monthcalendar returns weeks as lists of 7 ints (Mon=0);
        # 0 means the cell belongs to prev/next month.
        weeks = calendar.monthcalendar(self._year, self._month)

        # Ensure exactly 6 rows so the grid height stays stable
        while len(weeks) < 6:
            weeks.append([0, 0, 0, 0, 0, 0, 0])

        for row_idx, week in enumerate(weeks):
            for col_idx, day_num in enumerate(week):
                grid_row = row_idx + 2
                if day_num == 0:
                    # Empty padding cell
                    pad = ctk.CTkFrame(
                        self._cal_frame,
                        fg_color=EMPTY_CELL_BG,
                        corner_radius=6,
                    )
                    pad.grid(row=grid_row, column=col_idx, sticky="nsew", padx=2, pady=2)
                else:
                    cell_date = datetime.date(self._year, self._month, day_num)
                    self._make_day_cell(grid_row, col_idx, cell_date)

    def _make_day_cell(self, grid_row: int, col: int, date: datetime.date):
        is_today = (date == self._today)
        is_selected = (date == self._selected_date)

        if is_today:
            bg = TODAY_CELL_BG
        else:
            bg = BG_MAIN

        border_color = SELECTED_BORDER if is_selected else "transparent"
        border_width = 2 if is_selected else 0

        cell = ctk.CTkFrame(
            self._cal_frame,
            fg_color=bg,
            corner_radius=6,
            border_color=border_color,
            border_width=border_width,
        )
        cell.grid(row=grid_row, column=col, sticky="nsew", padx=2, pady=2)
        cell.grid_rowconfigure(0, weight=0)
        cell.grid_rowconfigure(1, weight=1)
        cell.grid_columnconfigure(0, weight=1)

        # Day number label
        num_label = ctk.CTkLabel(
            cell,
            text=str(date.day),
            font=("Arial", 12, "bold" if is_today else "normal"),
            text_color=TEXT_PRIMARY if is_today else TEXT_SECONDARY,
            anchor="ne",
        )
        num_label.grid(row=0, column=0, sticky="ne", padx=4, pady=(3, 0))

        # Click bindings — bind on cell + all children
        callback = lambda e, d=date: self._on_day_click(d)
        cell.bind("<Button-1>", callback)
        num_label.bind("<Button-1>", callback)

        # Dots row
        date_key = date.strftime("%Y-%m-%d")
        tasks_for_day = self._tasks_by_date.get(date_key, [])
        if tasks_for_day:
            self._add_dots(cell, date, tasks_for_day, callback)

    def _add_dots(self, cell: ctk.CTkFrame, date: datetime.date, tasks: list[dict], callback=None):
        dot_frame = ctk.CTkFrame(cell, fg_color="transparent")
        dot_frame.grid(row=1, column=0, sticky="sw", padx=3, pady=(0, 3))
        if callback:
            dot_frame.bind("<Button-1>", callback)

        visible = tasks[:3]
        extra = len(tasks) - 3

        for i, task in enumerate(visible):
            color = self._dot_color(task, date)
            dot = ctk.CTkLabel(
                dot_frame,
                text="●",
                font=("Arial", 8),
                text_color=color,
                fg_color="transparent",
                width=10,
            )
            dot.grid(row=0, column=i, padx=1)
            dot.bind("<Button-1>", lambda e, d=date: self._on_day_click(d))

        if extra > 0:
            more = ctk.CTkLabel(
                dot_frame,
                text=f"+{extra}",
                font=("Arial", 8),
                text_color=TEXT_SECONDARY,
                fg_color="transparent",
                width=20,
            )
            more.grid(row=0, column=3, padx=1)
            more.bind("<Button-1>", lambda e, d=date: self._on_day_click(d))

    def _dot_color(self, task: dict, date: datetime.date) -> str:
        if task.get("status") == "completed":
            return DOT_FUTURE  # completed tasks are never "overdue"
        if date < self._today:
            return DOT_PAST
        if date == self._today:
            return DOT_TODAY
        return DOT_FUTURE

    # ------------------------------------------------------------------
    # Detail panel (right side)
    # ------------------------------------------------------------------

    def _build_detail_panel(self):
        self._detail_frame.grid_rowconfigure(0, weight=0)
        self._detail_frame.grid_rowconfigure(1, weight=1)
        self._detail_frame.grid_columnconfigure(0, weight=1)

        self._detail_title = ctk.CTkLabel(
            self._detail_frame,
            text="Vyberte deň",
            font=("Arial", 14, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self._detail_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 6))

        self._task_scroll = ctk.CTkScrollableFrame(
            self._detail_frame,
            fg_color="transparent",
        )
        self._task_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._task_scroll.grid_columnconfigure(0, weight=1)

    def _refresh_detail_panel(self, date: datetime.date):
        date_key = date.strftime("%Y-%m-%d")
        date_display = date.strftime("%d. %m. %Y")
        self._detail_title.configure(text=f"Úlohy — {date_display}")

        # Clear old rows
        for w in self._task_scroll.winfo_children():
            w.destroy()

        tasks = self._tasks_by_date.get(date_key, [])
        if not tasks:
            ctk.CTkLabel(
                self._task_scroll,
                text="Žiadne úlohy pre tento deň.",
                text_color=TEXT_SECONDARY,
                font=("Arial", 12),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=6, pady=8)
            return

        for idx, task in enumerate(tasks):
            self._add_task_row(idx, task)

    def _add_task_row(self, idx: int, task: dict):
        status = task.get("status", "pending")
        badge_color = STATUS_COLORS.get(status, STATUS_COLORS["pending"])

        row_frame = ctk.CTkFrame(
            self._task_scroll,
            fg_color=BG_MAIN,
            corner_radius=6,
        )
        row_frame.grid(row=idx, column=0, sticky="ew", padx=2, pady=3)
        row_frame.grid_columnconfigure(1, weight=1)

        # Colored status badge
        ctk.CTkLabel(
            row_frame,
            text="  ",
            fg_color=badge_color,
            width=6,
            corner_radius=3,
        ).grid(row=0, column=0, rowspan=2, sticky="ns", padx=(6, 6), pady=6)

        # Task name
        ctk.CTkLabel(
            row_frame,
            text=task.get("name", "—"),
            font=("Arial", 12, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=(6, 0))

        # Project name
        ctk.CTkLabel(
            row_frame,
            text=task.get("project_name", ""),
            font=("Arial", 11),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=(0, 6))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_day_click(self, date: datetime.date):
        self._selected_date = date
        self._render_calendar()
        self._refresh_detail_panel(date)

    def _prev_month(self):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._render_calendar()

    def _next_month(self):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._render_calendar()

    def _goto_today(self):
        self._year = self._today.year
        self._month = self._today.month
        self._selected_date = self._today
        self._render_calendar()
        self._refresh_detail_panel(self._today)
