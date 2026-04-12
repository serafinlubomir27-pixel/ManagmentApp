import datetime

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from logic.stats import get_dashboard_stats, get_task_status_breakdown
from ui.theme import (
    PRIMARY, ACCENT, DANGER, BG_CARD, BG_MAIN,
    TEXT_PRIMARY, TEXT_SECONDARY,
)


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")

        # Support both dict and legacy tuple user_data
        if isinstance(user, dict):
            self.user_id = user.get("id")
            self.user_name = user.get("full_name") or user.get("username", "Používateľ")
        else:
            self.user_id = user[0]
            self.user_name = user[3] if len(user) > 3 else "Používateľ"

        self.stats = get_dashboard_stats(self.user_id)
        self.breakdown = get_task_status_breakdown(self.user_id)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)

        today = datetime.date.today().strftime("%d. %m. %Y")
        ctk.CTkLabel(
            header,
            text=f"Vitaj, {self.user_name}!",
            font=("Arial", 26, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=today,
            font=("Arial", 13),
            text_color=TEXT_SECONDARY,
        ).grid(row=0, column=1, sticky="e")

        # ── Stat cards ──────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        for col in range(3):
            cards_frame.grid_columnconfigure(col, weight=1)

        card_data = [
            ("📁", str(self.stats["projects_count"]), "Aktívne projekty", PRIMARY),
            ("✅", str(self.stats["tasks_count"]),    "Moje úlohy",       ACCENT),
            ("⚠️", str(self.stats["critical_count"]), "Po termíne",       DANGER),
        ]
        for col, (icon, value, label, color) in enumerate(card_data):
            self._create_stat_card(cards_frame, icon, value, label, color, col)

        # ── Bottom section ───────────────────────────────────────────────
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 16))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_rowconfigure(0, weight=1)

        self._build_donut_section(bottom)
        self._build_activity_section(bottom)

    # ------------------------------------------------------------------
    # Stat card
    # ------------------------------------------------------------------

    def _create_stat_card(self, parent, icon, value, label, accent_color, col):
        """Card with a colored left-border accent strip."""
        outer = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        outer.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
        outer.grid_columnconfigure(1, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        # Left-border accent strip
        accent_strip = ctk.CTkFrame(outer, fg_color=accent_color, width=6, corner_radius=0)
        accent_strip.grid(row=0, column=0, sticky="ns", padx=0, pady=0)

        # Content area
        content = ctk.CTkFrame(outer, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=14, pady=16)

        # Top row: icon + number
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=icon,
            font=("Segoe UI Emoji", 28),
            text_color=accent_color,
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=value,
            font=("Arial", 32, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="right")

        # Label below
        ctk.CTkLabel(
            content,
            text=label,
            font=("Arial", 13),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------
    # Donut chart
    # ------------------------------------------------------------------

    def _build_donut_section(self, parent):
        chart_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        chart_frame.grid_rowconfigure(1, weight=1)
        chart_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            chart_frame,
            text="Stav úloh",
            font=("Arial", 15, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        bd = self.breakdown
        values = [bd["pending"], bd["in_progress"], bd["completed"], bd["blocked"]]
        total = sum(values)

        if total == 0:
            ctk.CTkLabel(
                chart_frame,
                text="Žiadne úlohy",
                font=("Arial", 14),
                text_color=TEXT_SECONDARY,
            ).grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
            return

        labels = ["Čakajúce", "Prebieha", "Dokončené", "Blokované"]
        colors = ["#90CAF9", "#4DB6AC", "#81C784", "#EF9A9A"]

        fig, ax = plt.subplots(figsize=(4, 3.2), dpi=96)
        fig.patch.set_facecolor(BG_MAIN)
        ax.set_facecolor(BG_MAIN)

        wedges, _ = ax.pie(
            values,
            labels=None,
            colors=colors,
            startangle=90,
            wedgeprops={"width": 0.55, "edgecolor": BG_MAIN, "linewidth": 2},
        )

        # Center total label
        ax.text(
            0, 0, str(total),
            ha="center", va="center",
            fontsize=22, fontweight="bold", color=TEXT_PRIMARY,
        )
        ax.text(
            0, -0.22, "úloh",
            ha="center", va="center",
            fontsize=10, color=TEXT_SECONDARY,
        )

        # Legend
        ax.legend(
            wedges,
            [f"{l}  {v}" for l, v in zip(labels, values)],
            loc="lower center",
            bbox_to_anchor=(0.5, -0.22),
            ncol=2,
            frameon=False,
            labelcolor=TEXT_SECONDARY,
            fontsize=9,
        )

        fig.tight_layout(pad=0.5)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        plt.close(fig)

    # ------------------------------------------------------------------
    # Recent activity
    # ------------------------------------------------------------------

    def _build_activity_section(self, parent):
        activity_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        activity_frame.grid(row=0, column=1, sticky="nsew")
        activity_frame.grid_rowconfigure(1, weight=1)
        activity_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            activity_frame,
            text="Nedávna aktivita",
            font=("Arial", 15, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        scroll = ctk.CTkScrollableFrame(
            activity_frame,
            fg_color="transparent",
            corner_radius=0,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        scroll.grid_columnconfigure(0, weight=1)

        logs = self.stats.get("recent_activity", [])

        if not logs:
            ctk.CTkLabel(
                scroll,
                text="Žiadna nedávna aktivita.",
                font=("Arial", 13),
                text_color=TEXT_SECONDARY,
            ).pack(pady=20)
            return

        for entry in logs:
            # entry is a dict: user_name, action, new_value, created_at
            if isinstance(entry, dict):
                user_name = entry.get("user_name", "")
                action = entry.get("action", "")
                detail = entry.get("new_value") or ""
                timestamp = str(entry.get("created_at", ""))[:16]
            else:
                user_name, action, detail, timestamp = entry[0], entry[1], entry[2], str(entry[3])[:16]

            row = ctk.CTkFrame(scroll, fg_color="#333333", corner_radius=8)
            row.pack(fill="x", pady=3, padx=2)
            row.grid_columnconfigure(1, weight=1)

            # Colored bullet
            ctk.CTkLabel(
                row,
                text="●",
                font=("Arial", 14),
                text_color=PRIMARY,
                width=20,
            ).grid(row=0, column=0, padx=(10, 4), pady=8, sticky="n")

            # Action text
            action_text = f"{user_name} • {action}"
            if detail:
                action_text += f": {detail}"

            ctk.CTkLabel(
                row,
                text=action_text,
                font=("Arial", 12),
                text_color=TEXT_PRIMARY,
                wraplength=220,
                justify="left",
                anchor="w",
            ).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(8, 2))

            ctk.CTkLabel(
                row,
                text=timestamp,
                font=("Arial", 10),
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(0, 6))
