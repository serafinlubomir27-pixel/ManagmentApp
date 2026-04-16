"""
Dashboard Screen — štatistiky, donut chart, activity feed.
Gradient stat karty, matplotlib dual-mode, Segoe UI font.
"""
import datetime

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from logic.stats import get_dashboard_stats, get_task_status_breakdown
from repositories.task_repo import get_tasks_with_due_dates
from ui.theme import (
    PRIMARY, ACCENT, DANGER, WARNING,
    BG_CARD, BG_MAIN, BG_ROW, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    GRAD_BLUE, GRAD_TEAL, GRAD_RED,
    get_font, mode_color,
    FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_2XL, FONT_SIZE_3XL,
    RADIUS_MD, RADIUS_SM,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
)

# Konfigurácia stat kariet: (ikona, kľúč, label, gradient, akcentová farba)
_STAT_CONFIGS = [
    ("📁", "projects_count", "Aktívne projekty", GRAD_BLUE, PRIMARY),
    ("✅", "tasks_count",    "Moje úlohy",        GRAD_TEAL, ACCENT),
    ("⚠️", "critical_count", "Po termíne",        GRAD_RED,  DANGER),
]

# Farby donut chartu
_DONUT_COLORS = ["#7EB3FF", "#20CFC8", "#1DB86D", "#EF5350"]


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")

        if isinstance(user, dict):
            self.user_id   = user.get("id")
            self.user_name = user.get("full_name") or user.get("username", "Používateľ")
        else:
            self.user_id   = user[0]
            self.user_name = user[3] if len(user) > 3 else "Používateľ"

        self.stats     = get_dashboard_stats(self.user_id)
        self.breakdown = get_task_status_breakdown(self.user_id)
        self._chart_canvas = None

        self._build_ui()
        self.bind("<Destroy>", self._on_destroy)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def _on_destroy(self, event):
        if event.widget is self and self._chart_canvas:
            try:
                self._chart_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            plt.close("all")

    # ── Builder ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header (fixný — mimo scrollu) ─────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACE_XL, pady=(SPACE_LG, SPACE_SM))
        header.grid_columnconfigure(0, weight=1)

        today = datetime.date.today().strftime("%d. %m. %Y")

        ctk.CTkLabel(
            header,
            text=f"Vitaj, {self.user_name}!",
            font=get_font(FONT_SIZE_2XL, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=today,
            font=get_font(FONT_SIZE_BASE),
            text_color=TEXT_SECONDARY,
        ).grid(row=0, column=1, sticky="e")

        # ── Notifikácie — deadline banner ────────────────────────────────
        self._build_deadline_notifications(row=1)

        # ── Scrollovateľné telo ───────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Stat karty ──────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.grid(row=0, column=0, sticky="ew", padx=SPACE_XL, pady=(SPACE_SM, SPACE_MD))
        for col in range(3):
            cards_frame.grid_columnconfigure(col, weight=1)

        for col, (icon, key, label, grad, accent) in enumerate(_STAT_CONFIGS):
            value = str(self.stats.get(key, 0))
            self._create_stat_card(cards_frame, icon, value, label, grad, accent, col)

        # ── Spodná sekcia ────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_LG))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)

        self._build_donut_section(bottom)
        self._build_activity_section(bottom)

    # ── Deadline notifikácie ───────────────────────────────────────────────────

    def _build_deadline_notifications(self, row: int):
        """Build a compact notification banner for tasks due in the next 3 days.

        Shows nothing if there are no upcoming deadlines or all tasks are completed.
        """
        today = datetime.date.today()
        try:
            all_tasks = get_tasks_with_due_dates(self.user_id)
        except Exception:
            return

        alerts = []
        for t in all_tasks:
            if t.get("status") == "completed":
                continue
            raw = t.get("due_date")
            if not raw:
                continue
            try:
                due = datetime.date.fromisoformat(str(raw)[:10])
            except ValueError:
                continue
            days_left = (due - today).days
            if days_left < 0:
                alerts.append(("overdue", t, days_left))
            elif days_left <= 3:
                alerts.append(("soon", t, days_left))

        if not alerts:
            return

        # Banner frame
        banner = ctk.CTkFrame(
            self, fg_color=BG_CARD,
            corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        banner.grid(row=row, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_SM))
        banner.grid_columnconfigure(1, weight=1)

        # Icon column
        ctk.CTkLabel(
            banner, text="🔔",
            font=get_font(FONT_SIZE_LG),
            text_color=WARNING,
        ).grid(row=0, column=0, rowspan=max(1, len(alerts)), padx=(SPACE_MD, SPACE_SM), pady=SPACE_SM, sticky="n")

        # Alert rows
        for i, (kind, task, days_left) in enumerate(alerts[:5]):  # max 5 shown
            task_name = task.get("name", "Úloha")
            project_name = task.get("project_name", "")

            if kind == "overdue":
                label_text = f"⚠️  {task_name}"
                sub_text = f"{project_name}  •  Po termíne o {abs(days_left)} {'deň' if abs(days_left) == 1 else 'dní'}"
                color = DANGER
            elif days_left == 0:
                label_text = f"🔴  {task_name}"
                sub_text = f"{project_name}  •  Dnes!"
                color = DANGER
            elif days_left == 1:
                label_text = f"🟠  {task_name}"
                sub_text = f"{project_name}  •  Zajtra"
                color = WARNING
            else:
                label_text = f"🟡  {task_name}"
                sub_text = f"{project_name}  •  Za {days_left} dni"
                color = WARNING

            row_frame = ctk.CTkFrame(banner, fg_color="transparent")
            row_frame.grid(row=i, column=1, sticky="ew", padx=(0, SPACE_MD), pady=(SPACE_SM if i == 0 else 2, 2))

            ctk.CTkLabel(
                row_frame, text=label_text,
                font=get_font(FONT_SIZE_BASE, "bold"),
                text_color=color, anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                row_frame, text=sub_text,
                font=get_font(FONT_SIZE_SM),
                text_color=TEXT_SECONDARY, anchor="w",
            ).pack(anchor="w")

        # "... a X ďalších" ak ich je viac
        if len(alerts) > 5:
            ctk.CTkLabel(
                banner,
                text=f"  ... a {len(alerts) - 5} ďalších úloh s blížiacim sa termínom",
                font=get_font(FONT_SIZE_SM),
                text_color=TEXT_SECONDARY,
            ).grid(row=5, column=1, sticky="w", pady=(0, SPACE_SM))

    # ── Stat karta s gradientom ────────────────────────────────────────────────

    def _create_stat_card(self, parent, icon, value, label, grad, accent_color, col):
        """Gradient-tinted karta s farebným ľavým stripom."""
        # Gradient — použijeme start farbu ako bg a border na zvýraznenie
        is_dark = ctk.get_appearance_mode() == "Dark"
        grad_colors = grad[1] if is_dark else grad[0]   # (start, end)

        outer = ctk.CTkFrame(
            parent,
            fg_color=grad_colors[0],      # gradient start
            corner_radius=RADIUS_MD,
            border_width=1,
            border_color=accent_color,
        )
        outer.grid(
            row=0, column=col, sticky="ew",
            padx=(0 if col == 0 else SPACE_SM, 0)
        )
        outer.grid_columnconfigure(1, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        # Ľavý farebný strip
        ctk.CTkFrame(
            outer,
            fg_color=accent_color,
            width=4,
            corner_radius=0,
        ).grid(row=0, column=0, sticky="ns")

        # Obsah
        content = ctk.CTkFrame(outer, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=SPACE_LG, pady=SPACE_LG)

        # Ikona + číslo
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=icon,
            font=ctk.CTkFont(family="Segoe UI Emoji", size=24),
            text_color=accent_color,
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=value,
            font=get_font(FONT_SIZE_3XL, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="right")

        # Popis
        ctk.CTkLabel(
            content,
            text=label,
            font=get_font(FONT_SIZE_SM),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(SPACE_SM, 0))

    # ── Donut chart ────────────────────────────────────────────────────────────

    def _build_donut_section(self, parent):
        chart_frame = ctk.CTkFrame(
            parent, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE_SM))
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            chart_frame,
            text="Stav úloh",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=SPACE_LG, pady=(SPACE_MD, SPACE_SM))

        bd     = self.breakdown
        values = [bd["pending"], bd["in_progress"], bd["completed"], bd["blocked"]]
        total  = sum(values)

        if total == 0:
            ctk.CTkLabel(
                chart_frame,
                text="Žiadne úlohy",
                font=get_font(FONT_SIZE_BASE),
                text_color=TEXT_SECONDARY,
            ).grid(row=1, column=0, sticky="nsew", padx=SPACE_LG, pady=SPACE_LG)
            return

        labels = ["Čakajúce", "Prebieha", "Dokončené", "Blokované"]

        # Dual-mode farby pre matplotlib
        bg_col   = mode_color(BG_MAIN)
        text_col = mode_color(TEXT_PRIMARY)
        sec_col  = mode_color(TEXT_SECONDARY)

        fig, ax = plt.subplots(figsize=(4, 3.2), dpi=96)
        fig.patch.set_facecolor(bg_col)
        ax.set_facecolor(bg_col)

        wedges, _ = ax.pie(
            values,
            labels=None,
            colors=_DONUT_COLORS,
            startangle=90,
            wedgeprops={"width": 0.55, "edgecolor": bg_col, "linewidth": 2},
        )

        ax.text(0, 0, str(total),
                ha="center", va="center",
                fontsize=20, fontweight="bold", color=text_col)
        ax.text(0, -0.25, "úloh",
                ha="center", va="center",
                fontsize=9, color=sec_col)

        ax.legend(
            wedges,
            [f"{lbl}  {v}" for lbl, v in zip(labels, values)],
            loc="lower center",
            bbox_to_anchor=(0.5, -0.22),
            ncol=2,
            frameon=False,
            labelcolor=sec_col,
            fontsize=9,
        )

        fig.tight_layout(pad=0.5)

        self._chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=SPACE_SM, pady=(0, SPACE_SM))
        plt.close(fig)

    # ── Activity feed ──────────────────────────────────────────────────────────

    def _build_activity_section(self, parent):
        activity_frame = ctk.CTkFrame(
            parent, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        activity_frame.grid(row=0, column=1, sticky="nsew")
        activity_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            activity_frame,
            text="Nedávna aktivita",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=SPACE_LG, pady=(SPACE_MD, SPACE_SM))

        scroll = ctk.CTkScrollableFrame(
            activity_frame, fg_color="transparent", corner_radius=0,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=SPACE_SM, pady=(0, SPACE_SM))
        scroll.grid_columnconfigure(0, weight=1)

        logs = self.stats.get("recent_activity", [])

        if not logs:
            ctk.CTkLabel(
                scroll,
                text="Žiadna nedávna aktivita.",
                font=get_font(FONT_SIZE_BASE),
                text_color=TEXT_SECONDARY,
            ).pack(pady=SPACE_XL)
            return

        for entry in logs:
            if isinstance(entry, dict):
                user_name = entry.get("user_name", "")
                action    = entry.get("action", "")
                detail    = entry.get("new_value") or ""
                timestamp = str(entry.get("created_at", ""))[:16]
            else:
                user_name, action, detail, timestamp = (
                    entry[0], entry[1], entry[2], str(entry[3])[:16]
                )

            row = ctk.CTkFrame(
                scroll, fg_color=BG_ROW, corner_radius=RADIUS_SM,
                border_width=1, border_color=BORDER,
            )
            row.pack(fill="x", pady=3, padx=2)
            row.grid_columnconfigure(1, weight=1)

            # Bullet
            ctk.CTkLabel(
                row, text="●",
                font=get_font(FONT_SIZE_BASE),
                text_color=PRIMARY, width=20,
            ).grid(row=0, column=0, padx=(SPACE_MD, SPACE_SM), pady=SPACE_SM, sticky="n")

            # Akcia
            action_text = f"{user_name} • {action}"
            if detail:
                action_text += f": {detail}"

            ctk.CTkLabel(
                row, text=action_text,
                font=get_font(FONT_SIZE_BASE),
                text_color=TEXT_PRIMARY,
                justify="left", anchor="w",
            ).grid(row=0, column=1, sticky="w", padx=(0, SPACE_SM), pady=(SPACE_SM, 2))

            ctk.CTkLabel(
                row, text=timestamp,
                font=get_font(FONT_SIZE_SM),
                text_color=TEXT_SECONDARY, anchor="w",
            ).grid(row=1, column=1, sticky="w", padx=(0, SPACE_SM), pady=(0, SPACE_SM))
