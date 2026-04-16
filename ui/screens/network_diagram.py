"""
CPM Network Diagram — matplotlib node-and-edge graph embedded in CTk.
Nodes show ES/EF/LS/LF in a 4-quadrant box (classic CPM style).
Critical path edges are solid red; others are dashed gray.
"""
from __future__ import annotations

import customtkinter as ctk
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from logic.cpm_engine import CPMResult, CPMTask
from ui.theme import (
    BG_MAIN, BG_CARD, BG_ROW, BORDER, PRIMARY,
    TEXT_PRIMARY, TEXT_SECONDARY,
    mode_color, get_font, FONT_SIZE_BASE,
)

# Brand colors — consistent in both modes
COLOR_CRITICAL       = "#EF5350"
COLOR_COMPLETED      = "#1DB86D"
COLOR_NORMAL_BORDER  = "#5A8FFF"

# Node dimensions (data coordinates)
NODE_W = 3.0
NODE_H = 2.2
H_GAP = 2.5   # horizontal gap between levels
V_GAP = 1.0   # vertical gap between nodes in same level


class NetworkDiagramView(ctk.CTkFrame):
    """Embeds a matplotlib CPM network diagram inside a CTk frame."""

    def __init__(self, parent, cpm_result: CPMResult):
        super().__init__(parent, fg_color="transparent")
        self.cpm_result = cpm_result
        self._mpl_canvas = None
        self._fig = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_diagram()

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

    # ------------------------------------------------------------------
    # Layout: assign topological level to each task
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_levels(tasks: list[CPMTask]) -> dict[int, int]:
        """Return {task_id: level} where level is based on dependency depth."""
        task_map = {t.id: t for t in tasks}
        valid_ids = set(task_map.keys())
        levels: dict[int, int] = {}

        def get_level(tid: int) -> int:
            if tid in levels:
                return levels[tid]
            deps = [d for d in task_map[tid].dependencies if d in valid_ids]
            if not deps:
                levels[tid] = 0
            else:
                levels[tid] = max(get_level(d) for d in deps) + 1
            return levels[tid]

        for t in tasks:
            get_level(t.id)

        return levels

    # ------------------------------------------------------------------
    # Build the diagram
    # ------------------------------------------------------------------

    def _build_diagram(self):
        tasks = self.cpm_result.tasks
        if not tasks:
            ctk.CTkLabel(
                self, text="Žiadne úlohy na zobrazenie",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, sticky="nsew")
            return

        # Resolve dual-mode colors at render time
        color_bg    = mode_color(BG_MAIN)
        color_card  = mode_color(BG_ROW)
        color_text  = mode_color(TEXT_PRIMARY)
        color_dim   = mode_color(TEXT_SECONDARY)
        color_border = mode_color(BORDER)

        critical_ids = set(self.cpm_result.critical_path)
        task_map = {t.id: t for t in tasks}

        # Compute levels
        levels = self._compute_levels(tasks)
        max_level = max(levels.values()) if levels else 0

        # Group tasks by level
        level_groups: dict[int, list[CPMTask]] = {}
        for t in tasks:
            lv = levels[t.id]
            level_groups.setdefault(lv, []).append(t)

        # Sort within each level by ES
        for lv in level_groups:
            level_groups[lv].sort(key=lambda t: t.es)

        max_tasks_in_level = max(len(g) for g in level_groups.values()) if level_groups else 1

        # Figure sizing
        fig_width = max(8, (max_level + 1) * (NODE_W + H_GAP) + 2)
        fig_height = max(4, max_tasks_in_level * (NODE_H + V_GAP) + 2)
        fig_width = min(fig_width, 22)
        fig_height = min(fig_height, 14)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor(color_bg)
        ax.set_facecolor(color_bg)
        ax.set_aspect("equal")

        self._fig = fig

        # Compute node positions {task_id: (cx, cy)}
        positions: dict[int, tuple[float, float]] = {}
        for lv in range(max_level + 1):
            group = level_groups.get(lv, [])
            n = len(group)
            total_height = n * NODE_H + (n - 1) * V_GAP
            start_y = total_height / 2

            for i, t in enumerate(group):
                x = lv * (NODE_W + H_GAP) + NODE_W / 2 + 1
                y = start_y - i * (NODE_H + V_GAP) - NODE_H / 2
                positions[t.id] = (x, y)

        # Draw edges first (behind nodes)
        for t in tasks:
            valid_deps = [d for d in t.dependencies if d in task_map and d in positions]
            for dep_id in valid_deps:
                dep_task = task_map[dep_id]
                x1 = positions[dep_id][0] + NODE_W / 2
                y1 = positions[dep_id][1]
                x2 = positions[t.id][0] - NODE_W / 2
                y2 = positions[t.id][1]

                is_critical_edge = dep_id in critical_ids and t.id in critical_ids

                arrow = FancyArrowPatch(
                    (x1, y1), (x2, y2),
                    arrowstyle="->,head_width=4,head_length=4",
                    color=COLOR_CRITICAL if is_critical_edge else color_dim,
                    linewidth=2.0 if is_critical_edge else 1.0,
                    linestyle="-" if is_critical_edge else "--",
                    connectionstyle="arc3,rad=0.08",
                    zorder=1,
                )
                ax.add_patch(arrow)

        # Draw nodes
        for t in tasks:
            cx, cy = positions[t.id]
            x0 = cx - NODE_W / 2
            y0 = cy - NODE_H / 2

            is_critical = t.id in critical_ids

            # Node background
            if is_critical:
                bg_color = color_card
                border_color = COLOR_CRITICAL
            elif t.status == "completed":
                bg_color = color_card
                border_color = COLOR_COMPLETED
            else:
                bg_color = color_card
                border_color = COLOR_NORMAL_BORDER

            box = FancyBboxPatch(
                (x0, y0), NODE_W, NODE_H,
                boxstyle="round,pad=0.1",
                facecolor=bg_color, edgecolor=border_color,
                linewidth=2 if is_critical else 1,
                zorder=2,
            )
            ax.add_patch(box)

            # Task name (top center)
            name = t.name
            if len(name) > 16:
                name = name[:14] + "…"
            ax.text(
                cx, cy + NODE_H / 2 - 0.35, name,
                ha="center", va="center", fontsize=7.5,
                fontweight="bold", color=color_text, zorder=3,
            )

            # 4-quadrant CPM values
            # Divider lines
            ax.plot(
                [cx, cx], [cy - NODE_H / 2 + 0.15, cy + NODE_H / 2 - 0.6],
                color=border_color, linewidth=0.5, alpha=0.5, zorder=3,
            )
            ax.plot(
                [x0 + 0.2, x0 + NODE_W - 0.2], [cy - 0.1, cy - 0.1],
                color=border_color, linewidth=0.5, alpha=0.5, zorder=3,
            )

            # ES (top-left)
            ax.text(cx - NODE_W / 4, cy + 0.25, f"ES:{t.es}",
                    ha="center", va="center", fontsize=6.5,
                    color=color_text, fontfamily="monospace", zorder=3)
            # EF (top-right)
            ax.text(cx + NODE_W / 4, cy + 0.25, f"EF:{t.ef}",
                    ha="center", va="center", fontsize=6.5,
                    color=color_text, fontfamily="monospace", zorder=3)
            # LS (bottom-left)
            ax.text(cx - NODE_W / 4, cy - 0.35, f"LS:{t.ls}",
                    ha="center", va="center", fontsize=6.5,
                    color=color_dim, fontfamily="monospace", zorder=3)
            # LF (bottom-right)
            ax.text(cx + NODE_W / 4, cy - 0.35, f"LF:{t.lf}",
                    ha="center", va="center", fontsize=6.5,
                    color=color_dim, fontfamily="monospace", zorder=3)

            # Float badge (bottom-left corner)
            float_color = COLOR_CRITICAL if t.total_float == 0 else "#20CFC8"
            ax.text(
                x0 + 0.3, y0 + 0.2, f"F:{t.total_float}",
                ha="center", va="center", fontsize=5.5,
                color=float_color, fontweight="bold", zorder=3,
            )

            # Duration badge (bottom-right corner)
            ax.text(
                x0 + NODE_W - 0.3, y0 + 0.2, f"{t.duration}d",
                ha="center", va="center", fontsize=5.5,
                color=color_dim, zorder=3,
            )

            # Delay indicator
            if t.delay_days > 0:
                ax.text(
                    cx, y0 + 0.2, f"+{t.delay_days}d",
                    ha="center", va="center", fontsize=5.5,
                    color="#FF9800", fontweight="bold", zorder=3,
                )

        # Axes cleanup
        all_x = [p[0] for p in positions.values()]
        all_y = [p[1] for p in positions.values()]
        margin = 2
        ax.set_xlim(min(all_x) - NODE_W / 2 - margin, max(all_x) + NODE_W / 2 + margin)
        ax.set_ylim(min(all_y) - NODE_H / 2 - margin, max(all_y) + NODE_H / 2 + margin)
        ax.axis("off")

        # Title
        ax.set_title(
            f"CPM Network Diagram  —  Kritická cesta: {len(critical_ids)} úloh  |  "
            f"Trvanie: {self.cpm_result.project_duration} dní",
            fontsize=11, color=color_text, pad=12, fontweight="bold",
        )

        fig.tight_layout()

        # Embed into CTk
        self._mpl_canvas = FigureCanvasTkAgg(fig, master=self)
        widget = self._mpl_canvas.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew")
        self._mpl_canvas.draw()
