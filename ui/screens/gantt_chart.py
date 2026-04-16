"""
Gantt Chart View — matplotlib horizontal bar chart embedded in CTk.
Shows tasks positioned by ES/EF, float bars, critical path highlighting.
"""
from __future__ import annotations

import customtkinter as ctk
import matplotlib

matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyArrowPatch

from logic.cpm_engine import CPMResult, CPMTask
from ui.theme import (
    PRIMARY, DANGER, WARNING, BG_CARD, BG_MAIN, BG_ROW, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    mode_color, get_font, FONT_SIZE_BASE,
)

# Matplotlib brand colors — consistent in both modes (brand palette)
COLOR_CRITICAL  = "#EF5350"   # red for critical tasks
COLOR_NORMAL    = "#5A8FFF"   # blue for normal tasks
COLOR_COMPLETED = "#1DB86D"   # green for completed
COLOR_FLOAT     = "#90CAF9"   # light blue for float bar


class GanttChartView(ctk.CTkFrame):
    """Embeds a matplotlib Gantt chart inside a CTk frame."""

    def __init__(self, parent, cpm_result: CPMResult):
        super().__init__(parent, fg_color="transparent")
        self.cpm_result = cpm_result
        self._mpl_canvas = None
        self._fig = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_chart()

    def destroy(self):
        """Cleanup matplotlib resources before destroying widget."""
        if self._mpl_canvas:
            try:
                self._mpl_canvas.get_tk_widget().destroy()
            except Exception:
                pass
        if self._fig:
            plt.close(self._fig)
        super().destroy()

    def _build_chart(self):
        tasks = self.cpm_result.tasks
        if not tasks:
            ctk.CTkLabel(
                self, text="Žiadne úlohy na zobrazenie",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, sticky="nsew")
            return

        # Resolve dual-mode colors at render time
        color_bg   = mode_color(BG_MAIN)
        color_card = mode_color(BG_ROW)
        color_grid = mode_color(BORDER)
        color_text = mode_color(TEXT_PRIMARY)
        color_dim  = mode_color(TEXT_SECONDARY)

        critical_ids = set(self.cpm_result.critical_path)

        # Sort tasks by ES (top = earliest)
        sorted_tasks = sorted(tasks, key=lambda t: (t.es, t.id))

        n = len(sorted_tasks)
        project_duration = self.cpm_result.project_duration

        # Dynamic figure sizing
        fig_height = max(3.5, 0.5 * n + 1.2)
        fig_width = max(8, project_duration * 0.4 + 3)
        fig_width = min(fig_width, 20)  # cap at 20 inches

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor(color_bg)
        ax.set_facecolor(color_card)

        self._fig = fig

        y_positions = list(range(n))
        bar_height = 0.6
        float_height = 0.3

        for i, task in enumerate(sorted_tasks):
            y = n - 1 - i  # reverse so first task is at top

            # Determine bar color
            if task.status == "completed":
                color = COLOR_COMPLETED
            elif task.id in critical_ids:
                color = COLOR_CRITICAL
            else:
                color = COLOR_NORMAL

            # Float bar (behind, semi-transparent)
            if task.total_float > 0:
                ax.barh(
                    y, task.total_float, left=task.ef,
                    height=float_height, color=COLOR_FLOAT, alpha=0.35,
                    edgecolor="none", zorder=1,
                )

            # Main task bar
            ax.barh(
                y, task.duration, left=task.es,
                height=bar_height, color=color, alpha=0.9,
                edgecolor="#ffffff22", linewidth=0.5, zorder=2,
            )

            # Task label on bar
            label = task.name
            if len(label) > 18:
                label = label[:16] + "…"

            # Place text inside bar if wide enough, else to the right
            if task.duration >= 3:
                ax.text(
                    task.es + task.duration / 2, y, label,
                    ha="center", va="center", fontsize=7.5,
                    color="white", fontweight="bold", zorder=3,
                )
            else:
                ax.text(
                    task.ef + 0.2, y, label,
                    ha="left", va="center", fontsize=7.5,
                    color=color_text, zorder=3,
                )

            # Duration text
            ax.text(
                task.es - 0.3, y, f"{task.duration}d",
                ha="right", va="center", fontsize=7,
                color=color_dim, zorder=3,
            )

            # Critical path indicator
            if task.id in critical_ids:
                ax.text(
                    task.ef + 0.2, y + 0.25, "*",
                    ha="left", va="center", fontsize=8,
                    color=COLOR_CRITICAL, fontweight="bold", zorder=3,
                )

        # Draw dependency arrows
        task_y_map = {}
        for i, task in enumerate(sorted_tasks):
            task_y_map[task.id] = n - 1 - i

        task_map = {t.id: t for t in sorted_tasks}

        for task in sorted_tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map and dep_id in task_y_map:
                    dep_task = task_map[dep_id]
                    from_x = dep_task.ef
                    from_y = task_y_map[dep_id]
                    to_x = task.es
                    to_y = task_y_map[task.id]

                    arrow = FancyArrowPatch(
                        (from_x, from_y), (to_x, to_y),
                        arrowstyle="->,head_width=3,head_length=3",
                        color=color_dim, linewidth=0.8, alpha=0.55,
                        connectionstyle="arc3,rad=0.15",
                        zorder=1,
                    )
                    ax.add_patch(arrow)

        # Axes styling
        ax.set_yticks(range(n))
        ax.set_yticklabels(
            [sorted_tasks[n - 1 - i].name[:20] for i in range(n)],
            fontsize=8, color=color_text,
        )
        ax.set_xlim(-2, project_duration + 2)
        ax.set_ylim(-0.5, n - 0.5)

        # X-axis: day labels
        ax.set_xlabel("Deň", fontsize=9, color=color_dim)
        ax.tick_params(axis="x", colors=color_dim, labelsize=8)

        # Grid
        ax.xaxis.grid(True, color=color_grid, linestyle="--", linewidth=0.5, alpha=0.5)
        ax.yaxis.grid(False)
        ax.set_axisbelow(True)

        # Spines
        for spine in ax.spines.values():
            spine.set_color(color_grid)
            spine.set_linewidth(0.5)

        # Title
        ax.set_title(
            f"Gantt Chart  —  Trvanie: {project_duration} dní  |  "
            f"Oneskorenie: {self.cpm_result.total_project_delay} dní",
            fontsize=11, color=color_text, pad=12, fontweight="bold",
        )

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=COLOR_CRITICAL, label="Kritická cesta"),
            Patch(facecolor=COLOR_NORMAL, label="Normálna úloha"),
            Patch(facecolor=COLOR_COMPLETED, label="Dokončená"),
            Patch(facecolor=COLOR_FLOAT, alpha=0.35, label="Float (voľnosť)"),
        ]
        leg = ax.legend(
            handles=legend_elements, loc="upper right",
            fontsize=7, facecolor=color_card, edgecolor=color_grid,
            labelcolor=color_text,
        )
        leg.get_frame().set_alpha(0.9)

        fig.tight_layout()

        # Embed into CTk
        self._mpl_canvas = FigureCanvasTkAgg(fig, master=self)
        widget = self._mpl_canvas.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew")
        self._mpl_canvas.draw()
