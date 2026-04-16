"""
Project Detail View — tabbed interface: Dashboard | Tasks | Gantt | CPM Network
"""
import os
import shutil
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import customtkinter as ctk
from datetime import date

from logic.task_manager import get_tasks_for_project, add_task, update_task_status, add_comment, get_task_comments
from logic.hierarchy import get_my_team
from logic.cpm_manager import recalculate_project_cpm
from logic.cpm_engine import CPMResult, calculate_health_score
from logic.export_manager import export_project_pdf, export_tasks_csv, import_tasks_csv
from logic.file_manager import add_attachment, get_attachments_for_task, delete_attachment
from repositories import task_repo
from ui.theme import (
    PRIMARY, PRIMARY_HOVER, PRIMARY_MUTED, ACCENT, ACCENT_HOVER, DANGER, WARNING, SUCCESS,
    BG_CARD, BG_MAIN, BG_ROW, BG_INPUT, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    STATUS_COLORS, color_blend, color_blend_dual,
    get_font,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL, FONT_SIZE_2XL,
    RADIUS_SM, RADIUS_MD,
    HEIGHT_BTN_SM, HEIGHT_BTN_MD, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
)

# Priečinok pre prílohy
ATTACHMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "attachments"
)

FILTER_OPTIONS = ["Všetky", "pending", "in_progress", "completed", "blocked"]
FILTER_DISPLAY = {
    "Všetky": "Všetky",
    "pending": "Pending",
    "in_progress": "In Progress",
    "completed": "Completed",
    "blocked": "Blocked",
}

CATEGORY_OPTIONS = [
    "Planning", "Design", "Development", "Testing",
    "Documentation", "Deployment", "Review", "Other",
]


class ProjectDetailView(ctk.CTkFrame):
    def __init__(self, parent, project_data, user_data, back_callback):
        super().__init__(parent, fg_color="transparent")
        if isinstance(project_data, dict):
            self.project_id = project_data["id"]
            self.project_name = project_data.get("name", "Projekt")
        else:
            self.project_id = project_data[0]
            self.project_name = project_data[1]
        self.user_id = user_data["id"] if isinstance(user_data, dict) else user_data[0]
        self.user_data = user_data
        self.back_callback = back_callback
        self.active_filter = "Všetky"
        self._search_query: str = ""
        self._cpm_result: CPMResult | None = None

        self._build_ui()
        self._recalc_cpm()

    # ------------------------------------------------------------------
    # UI skeleton
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            header, text="Spat", width=80,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
            height=HEIGHT_BTN_SM, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=self.back_callback,
        ).grid(row=0, column=0, padx=(0, SPACE_MD))

        ctk.CTkLabel(
            header, text=self.project_name,
            font=get_font(FONT_SIZE_XL, "bold"), text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkButton(
            header, text="+ Pridat ulohu", width=130,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._open_add_task,
        ).grid(row=0, column=2, padx=(SPACE_MD, 0))

        ctk.CTkButton(
            header, text="Export PDF", width=120,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._export_pdf,
        ).grid(row=0, column=3, padx=(SPACE_SM, 0))

        ctk.CTkButton(
            header, text="CSV ↓", width=80,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=self._export_csv,
        ).grid(row=0, column=4, padx=(SPACE_SM, 0))

        ctk.CTkButton(
            header, text="CSV ↑", width=80,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=self._import_csv,
        ).grid(row=0, column=5, padx=(SPACE_SM, 0))

        # Tab bar
        tab_bar = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER, height=44,
        )
        tab_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(52, 0))

        self._tabs = {}
        self._tab_buttons = {}
        tab_names = [
            ("dashboard", "Dashboard"),
            ("tasks",     "Tasks"),
            ("gantt",     "Gantt"),
            ("cpm",       "CPM Network"),
        ]
        for i, (key, label) in enumerate(tab_names):
            btn = ctk.CTkButton(
                tab_bar, text=label, width=120, height=34,
                fg_color="transparent", hover_color=BG_ROW,
                text_color=TEXT_SECONDARY,
                font=get_font(FONT_SIZE_BASE),
                corner_radius=RADIUS_SM,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left", padx=4, pady=4)
            self._tab_buttons[key] = btn

        # Content area
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._switch_tab("dashboard")

    def _switch_tab(self, key: str):
        for k, btn in self._tab_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=PRIMARY_MUTED,
                    text_color=PRIMARY,
                    font=get_font(FONT_SIZE_BASE, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    font=get_font(FONT_SIZE_BASE),
                )

        # Clear content
        for w in self._content.winfo_children():
            w.destroy()

        if key == "dashboard":
            self._build_dashboard_tab()
        elif key == "tasks":
            self._build_tasks_tab()
        elif key == "gantt":
            self._build_gantt_tab()
        elif key == "cpm":
            self._build_cpm_tab()

    # ------------------------------------------------------------------
    # CPM
    # ------------------------------------------------------------------

    def _recalc_cpm(self):
        try:
            self._cpm_result = recalculate_project_cpm(self.project_id)
        except Exception:
            self._cpm_result = None

    # ------------------------------------------------------------------
    # TAB 1: Dashboard
    # ------------------------------------------------------------------

    def _build_dashboard_tab(self):
        scroll = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        tasks = task_repo.get_tasks_for_project_with_cpm(self.project_id)
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        pending = sum(1 for t in tasks if t.get("status") == "pending")
        in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
        blocked = sum(1 for t in tasks if t.get("status") == "blocked")
        progress = completed / total if total > 0 else 0.0
        critical_count = sum(1 for t in tasks if t.get("is_critical"))

        # Health
        cpm = self._cpm_result
        if cpm and cpm.is_valid and cpm.tasks:
            health_score, health_label = calculate_health_score(
                cpm.tasks, cpm.project_duration, cpm.project_duration_without_delays + 5
            )
        else:
            health_score, health_label = 100, "Healthy"

        health_color = SUCCESS if health_label == "Healthy" else WARNING if health_label == "At Risk" else DANGER

        # --- Stats row (4 cards) ---
        stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_row.pack(fill="x", padx=0, pady=(0, 12))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1)

        stats = [
            ("📊", "Progress", f"{int(progress * 100)}%", PRIMARY),
            ("✅", "Dokončené", f"{completed}/{total}", SUCCESS),
            ("⚡", "Kritická cesta", f"{critical_count} úloh", WARNING),
            ("📈", "Zdravie", health_label, health_color),
        ]

        for i, (icon, label, value, color) in enumerate(stats):
            card = ctk.CTkFrame(
                stats_row, fg_color=BG_CARD, corner_radius=RADIUS_MD,
                border_width=1, border_color=BORDER, height=90,
            )
            card.grid(row=0, column=i, sticky="nsew", padx=4, pady=0)
            card.grid_propagate(False)

            ctk.CTkLabel(card, text=label, font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY).place(x=14, y=12)
            ctk.CTkLabel(card, text=value, font=get_font(FONT_SIZE_XL, "bold"), text_color=color).place(x=14, y=36)

        # --- Progress bar ---
        prog_frame = ctk.CTkFrame(
            scroll, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        prog_frame.pack(fill="x", padx=0, pady=(0, 12))
        bar = ctk.CTkProgressBar(prog_frame, progress_color=SUCCESS, fg_color=BG_ROW)
        bar.set(progress)
        bar.pack(fill="x", padx=SPACE_LG, pady=SPACE_MD)

        # --- Timeline + Alerts row ---
        info_row = ctk.CTkFrame(scroll, fg_color="transparent")
        info_row.pack(fill="x", padx=0, pady=(0, 12))
        info_row.grid_columnconfigure(0, weight=1)
        info_row.grid_columnconfigure(1, weight=1)

        # Timeline card
        timeline_card = ctk.CTkFrame(
            info_row, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        timeline_card.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE_SM))

        ctk.CTkLabel(
            timeline_card, text="📅 Časová os projektu",
            font=get_font(FONT_SIZE_MD, "bold"), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=SPACE_LG, pady=(SPACE_MD, SPACE_SM))

        duration = cpm.project_duration if cpm and cpm.is_valid else 0
        delay = cpm.total_project_delay if cpm and cpm.is_valid else 0
        today_str = date.today().strftime("%d. %m. %Y")

        for label, val in [("Začiatok", today_str), ("Trvanie", f"{duration} dní"),
                            ("Oneskorenie", f"{delay} dní" if delay > 0 else "Žiadne")]:
            row = ctk.CTkFrame(timeline_card, fg_color="transparent")
            row.pack(fill="x", padx=SPACE_LG, pady=2)
            ctk.CTkLabel(row, text=label, text_color=TEXT_SECONDARY, font=get_font(FONT_SIZE_BASE)).pack(side="left")
            val_color = DANGER if "Oneskorenie" in label and delay > 0 else TEXT_PRIMARY
            ctk.CTkLabel(row, text=val, text_color=val_color, font=get_font(FONT_SIZE_BASE, "bold")).pack(side="right")

        ctk.CTkLabel(timeline_card, text="").pack()  # spacer

        # Alerts card
        alerts_card = ctk.CTkFrame(
            info_row, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        alerts_card.grid(row=0, column=1, sticky="nsew", padx=(SPACE_SM, 0))

        ctk.CTkLabel(
            alerts_card, text="⚠️ Upozornenia",
            font=get_font(FONT_SIZE_MD, "bold"), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=SPACE_LG, pady=(SPACE_MD, SPACE_SM))

        alerts = []
        if blocked > 0:
            alerts.append((f"🔴 {blocked} zablokovaných úloh", DANGER))
        if delay > 0:
            alerts.append((f"🟠 Projekt oneskorený o {delay} dní", WARNING))
        if cpm and not cpm.is_valid:
            for err in cpm.errors:
                alerts.append((f"❌ {err}", DANGER))
        if not alerts:
            alerts.append(("✅ Žiadne problémy. Projekt je na dobrej ceste!", SUCCESS))

        for text, color in alerts:
            ctk.CTkLabel(
                alerts_card, text=text, text_color=color,
                font=get_font(FONT_SIZE_BASE), anchor="w",
            ).pack(anchor="w", padx=SPACE_LG, pady=2)
        ctk.CTkLabel(alerts_card, text="").pack()

        # --- Status breakdown ---
        breakdown_card = ctk.CTkFrame(
            scroll, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        breakdown_card.pack(fill="x", padx=0, pady=(0, 12))

        ctk.CTkLabel(
            breakdown_card, text="Rozdelenie úloh podľa stavu",
            font=get_font(FONT_SIZE_MD, "bold"), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=SPACE_LG, pady=(SPACE_MD, SPACE_SM))

        bd_row = ctk.CTkFrame(breakdown_card, fg_color="transparent")
        bd_row.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_MD))
        for i in range(4):
            bd_row.grid_columnconfigure(i, weight=1)

        breakdown_data = [
            ("Pending",     pending,     STATUS_COLORS["pending"]),
            ("In Progress", in_progress, STATUS_COLORS["in_progress"]),
            ("Completed",   completed,   STATUS_COLORS["completed"]),
            ("Blocked",     blocked,     STATUS_COLORS["blocked"]),
        ]
        for i, (lbl, cnt, color_tuple) in enumerate(breakdown_data):
            box = ctk.CTkFrame(
                bd_row, fg_color=color_blend_dual(color_tuple, 0.15),
                corner_radius=RADIUS_SM,
            )
            box.grid(row=0, column=i, sticky="nsew", padx=4, pady=0)
            ctk.CTkLabel(box, text=str(cnt), font=get_font(FONT_SIZE_2XL, "bold"), text_color=color_tuple).pack(pady=(SPACE_SM, 0))
            ctk.CTkLabel(box, text=lbl, font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY).pack(pady=(0, SPACE_SM))

    # ------------------------------------------------------------------
    # TAB 2: Tasks
    # ------------------------------------------------------------------

    def _build_tasks_tab(self):
        self._search_query = ""
        container = ctk.CTkFrame(self._content, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Filter bar
        filter_bar = ctk.CTkFrame(container, fg_color="transparent")
        filter_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        filter_bar.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(filter_bar, text="Filter:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).grid(row=0, column=0, padx=(0, SPACE_SM))
        display_values = [FILTER_DISPLAY[k] for k in FILTER_OPTIONS]
        self._filter_combo = ctk.CTkOptionMenu(
            filter_bar, values=display_values,
            command=self._on_filter_change,
            fg_color=BG_CARD, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        self._filter_combo.set("Všetky")
        self._filter_combo.grid(row=0, column=1, padx=(0, SPACE_MD))

        # Search box
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_change())
        search_entry = ctk.CTkEntry(
            filter_bar,
            textvariable=self._search_var,
            placeholder_text="🔍  Hľadať úlohu...",
            fg_color=BG_INPUT, border_color=BORDER,
            text_color=TEXT_PRIMARY,
            height=HEIGHT_BTN_SM, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
        )
        search_entry.grid(row=0, column=2, sticky="ew")

        # Task list scroll
        self._task_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self._task_scroll.grid(row=1, column=0, sticky="nsew")
        self._task_scroll.grid_columnconfigure(0, weight=1)

        self._refresh_task_list()

    def _on_filter_change(self, display_value):
        reverse = {v: k for k, v in FILTER_DISPLAY.items()}
        self.active_filter = reverse.get(display_value, "Všetky")
        self._refresh_task_list()

    def _on_search_change(self):
        self._search_query = self._search_var.get().strip().lower()
        self._refresh_task_list()

    def _refresh_task_list(self):
        for w in self._task_scroll.winfo_children():
            w.destroy()

        tasks = task_repo.get_tasks_for_project_with_cpm(self.project_id)

        if self.active_filter != "Všetky":
            tasks = [t for t in tasks if t.get("status") == self.active_filter]

        if self._search_query:
            q = self._search_query
            tasks = [
                t for t in tasks
                if q in (t.get("name") or "").lower()
                or q in (t.get("assigned_username") or "").lower()
                or q in (t.get("category") or "").lower()
            ]

        if not tasks:
            empty_msg = "Žiadne výsledky pre daný filter/hľadanie." if (self.active_filter != "Všetky" or self._search_query) else "Žiadne úlohy."
            ctk.CTkLabel(
                self._task_scroll, text=empty_msg,
                text_color=TEXT_SECONDARY, font=get_font(FONT_SIZE_BASE),
            ).pack(pady=SPACE_XL)
            return

        for idx, t in enumerate(tasks):
            self._create_task_row(idx, t)

    def _create_task_row(self, idx: int, task: dict):
        tid = task.get("id")
        name = task.get("name", "")
        status = task.get("status", "pending")
        duration = task.get("duration") or 1
        es = task.get("es", 0)
        ef = task.get("ef", 0)
        ls = task.get("ls", 0)
        lf = task.get("lf", 0)
        total_float = task.get("total_float", 0)
        is_critical = task.get("is_critical", False)
        category = task.get("category", "")
        assigned = task.get("assigned_username", "")

        row = ctk.CTkFrame(
            self._task_scroll, fg_color=BG_CARD, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        row.grid(row=idx, column=0, sticky="ew", padx=0, pady=3)
        row.grid_columnconfigure(1, weight=1)

        # Checkbox
        is_completed = status == "completed"
        chk_var = ctk.IntVar(value=1 if is_completed else 0)

        def toggle(var=chk_var, task_id=tid):
            new_st = "completed" if var.get() == 1 else "pending"
            update_task_status(task_id, new_st, self.user_id)
            self._recalc_cpm()
            self._refresh_task_list()

        ctk.CTkCheckBox(row, text="", width=20, variable=chk_var, command=toggle
                         ).grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=8)

        # Name row
        name_frame = ctk.CTkFrame(row, fg_color="transparent")
        name_frame.grid(row=0, column=1, sticky="ew", padx=4, pady=(6, 0))

        ctk.CTkLabel(
            name_frame, text=name,
            font=get_font(FONT_SIZE_BASE, "bold"), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if is_critical:
            ctk.CTkLabel(
                name_frame, text="🔥 Critical",
                font=get_font(FONT_SIZE_XS),
                text_color=DANGER, fg_color=color_blend_dual(DANGER, 0.2),
                corner_radius=RADIUS_SM,
            ).pack(side="left", padx=(SPACE_SM, 0))

        if category:
            ctk.CTkLabel(
                name_frame, text=category,
                font=get_font(FONT_SIZE_XS),
                text_color=TEXT_SECONDARY, fg_color=BG_ROW,
                corner_radius=RADIUS_SM,
            ).pack(side="left", padx=(SPACE_SM, 0))

        # Details row
        detail_frame = ctk.CTkFrame(row, fg_color="transparent")
        detail_frame.grid(row=1, column=1, sticky="ew", padx=4, pady=(0, 6))

        info_parts = [
            f"⏱ {duration}d",
            f"ES:{es} EF:{ef} LS:{ls} LF:{lf}",
            f"Float:{total_float}",
        ]
        if assigned:
            info_parts.append(f"👤 {assigned}")

        ctk.CTkLabel(
            detail_frame, text="  |  ".join(info_parts),
            font=get_font(FONT_SIZE_XS), text_color=TEXT_SECONDARY,
        ).pack(side="left")

        # Status badge
        st_color = STATUS_COLORS.get(status, ("#9E9E9E", "#9E9E9E"))
        ctk.CTkLabel(
            row, text=status, font=get_font(FONT_SIZE_XS, "bold"),
            text_color=st_color, fg_color=color_blend_dual(st_color, 0.2),
            corner_radius=RADIUS_SM, width=80,
        ).grid(row=0, column=2, padx=SPACE_SM, pady=SPACE_SM)

        # Edit button
        ctk.CTkButton(
            row, text="✏️", width=36, height=28,
            fg_color=BG_ROW, hover_color=BG_MAIN,
            command=lambda t=task: self._open_task_editor(t),
        ).grid(row=0, column=3, rowspan=2, padx=(0, SPACE_SM), pady=SPACE_SM)

    # ------------------------------------------------------------------
    # TAB 3: Gantt (placeholder — will be implemented in Etapa 3)
    # ------------------------------------------------------------------

    def _build_gantt_tab(self):
        frame = ctk.CTkFrame(self._content, fg_color=BG_CARD, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew")

        if self._cpm_result and self._cpm_result.is_valid and self._cpm_result.tasks:
            try:
                from ui.screens.gantt_chart import GanttChartView
                gantt = GanttChartView(frame, self._cpm_result)
                gantt.pack(fill="both", expand=True)
            except ImportError:
                ctk.CTkLabel(
                    frame, text="📊 Gantt Chart — bude implementovaný v ďalšej etape",
                    font=get_font(FONT_SIZE_MD), text_color=TEXT_SECONDARY,
                ).pack(expand=True)
        else:
            ctk.CTkLabel(
                frame, text="Pridajte úlohy s dependencies pre Gantt zobrazenie",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).pack(expand=True)

    # ------------------------------------------------------------------
    # TAB 4: CPM Network (placeholder — will be implemented in Etapa 4)
    # ------------------------------------------------------------------

    def _build_cpm_tab(self):
        frame = ctk.CTkFrame(self._content, fg_color=BG_CARD, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew")

        if self._cpm_result and self._cpm_result.is_valid and self._cpm_result.tasks:
            try:
                from ui.screens.network_diagram import NetworkDiagramView
                net = NetworkDiagramView(frame, self._cpm_result)
                net.pack(fill="both", expand=True)
            except ImportError:
                ctk.CTkLabel(
                    frame, text="🔗 CPM Network — bude implementovaný v ďalšej etape",
                    font=get_font(FONT_SIZE_MD), text_color=TEXT_SECONDARY,
                ).pack(expand=True)
        else:
            ctk.CTkLabel(
                frame, text="Pridajte úlohy s dependencies pre CPM zobrazenie",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).pack(expand=True)

    # ------------------------------------------------------------------
    # Task Editor dialog
    # ------------------------------------------------------------------

    def _open_task_editor(self, task: dict):
        TaskEditorDialog(self, task, self.project_id, self.user_id, on_save=self._on_task_saved)

    def _on_task_saved(self):
        self._recalc_cpm()
        self._switch_tab("tasks")

    def _open_add_task(self):
        AddTaskDialog(self, self.project_id, self.user_id, on_save=self._on_task_saved)

    # ------------------------------------------------------------------
    # PDF Export
    # ------------------------------------------------------------------

    def _export_pdf(self):
        """Otvorí file dialog a exportuje projekt do PDF."""
        default_name = f"{self.project_name.replace(' ', '_')}_report.pdf"
        path = fd.asksaveasfilename(
            title="Uložiť PDF report",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF súbory", "*.pdf"), ("Všetky súbory", "*.*")],
        )
        if not path:
            return  # používateľ zrušil

        # Zobraz "načítavam" stav
        self._recalc_cpm()

        ok = export_project_pdf(
            project_name=self.project_name,
            project_id=self.project_id,
            cpm_result=self._cpm_result,
            output_path=path,
        )

        if ok:
            mb.showinfo(
                "Export úspešný",
                f"PDF report bol uložený do:\n{path}",
            )
            # Otvor PDF automaticky (Windows)
            try:
                os.startfile(path)
            except Exception:
                pass
        else:
            mb.showerror(
                "Chyba exportu",
                "PDF sa nepodarilo vygenerovať.\nSkontroluj konzolu pre detaily.",
            )

    # ------------------------------------------------------------------
    # CSV Export / Import
    # ------------------------------------------------------------------

    def _export_csv(self):
        """Exportuje úlohy projektu do CSV súboru."""
        default_name = f"{self.project_name.replace(' ', '_')}_ulohy.csv"
        path = fd.asksaveasfilename(
            title="Exportovať úlohy do CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV súbory", "*.csv"), ("Všetky súbory", "*.*")],
        )
        if not path:
            return

        ok, msg = export_tasks_csv(self.project_id, path)
        if ok:
            mb.showinfo("Export úspešný", msg)
        else:
            mb.showerror("Chyba exportu", msg)

    def _import_csv(self):
        """Importuje úlohy z CSV súboru do projektu."""
        path = fd.askopenfilename(
            title="Importovať úlohy z CSV",
            filetypes=[("CSV súbory", "*.csv"), ("Všetky súbory", "*.*")],
        )
        if not path:
            return

        ok, msg = import_tasks_csv(self.project_id, path, self.user_id)
        if ok:
            mb.showinfo("Import dokončený", msg)
            self._recalc_cpm()
            # Refresh task list if currently on tasks tab
            if hasattr(self, "_task_scroll"):
                self._refresh_task_list()
        else:
            mb.showerror("Chyba importu", msg)


# ======================================================================
# Task Editor Dialog (full CPM edit)
# ======================================================================

class TaskEditorDialog(ctk.CTkToplevel):
    """Edit task with CPM fields: name, description, duration, delay, category, status, notes, dependencies."""

    def __init__(self, parent, task: dict, project_id: int, user_id: int, on_save):
        super().__init__(parent)
        self.task = task
        self.project_id = project_id
        self.user_id = user_id
        self.on_save = on_save

        self.title(f"Úloha: {task.get('name', '')}")
        self.geometry("580x820")
        self.resizable(True, True)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        # --- Name ---
        ctk.CTkLabel(scroll, text="Názov úlohy", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.name_entry = ctk.CTkEntry(
            scroll, width=480, height=HEIGHT_INPUT,
            fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.name_entry.insert(0, task.get("name", ""))
        self.name_entry.pack(fill="x", pady=(0, SPACE_MD))

        # --- Description ---
        ctk.CTkLabel(scroll, text="Popis", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.desc_entry = ctk.CTkTextbox(
            scroll, height=60, width=480,
            fg_color=BG_INPUT, border_color=BORDER, border_width=1,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.desc_entry.insert("0.0", task.get("description") or "")
        self.desc_entry.pack(fill="x", pady=(0, SPACE_MD))

        # --- Duration + Delay row ---
        dur_row = ctk.CTkFrame(scroll, fg_color="transparent")
        dur_row.pack(fill="x", pady=(0, SPACE_MD))

        ctk.CTkLabel(dur_row, text="Trvanie (dni):", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(side="left")
        self.dur_entry = ctk.CTkEntry(
            dur_row, width=80, height=HEIGHT_INPUT,
            fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.dur_entry.insert(0, str(task.get("duration") or 1))
        self.dur_entry.pack(side="left", padx=(SPACE_SM, SPACE_XL))

        ctk.CTkLabel(dur_row, text="Oneskorenie (dni):", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(side="left")
        self.delay_entry = ctk.CTkEntry(
            dur_row, width=80, height=HEIGHT_INPUT,
            fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.delay_entry.insert(0, str(task.get("delay_days") or 0))
        self.delay_entry.pack(side="left", padx=(SPACE_SM, 0))

        # --- Category ---
        ctk.CTkLabel(scroll, text="Kategória", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.cat_combo = ctk.CTkOptionMenu(
            scroll, values=CATEGORY_OPTIONS, width=200,
            fg_color=BG_INPUT, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        self.cat_combo.set(task.get("category") or "Other")
        self.cat_combo.pack(anchor="w", pady=(0, SPACE_MD))

        # --- Status ---
        ctk.CTkLabel(scroll, text="Stav", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.status_combo = ctk.CTkOptionMenu(
            scroll, values=["pending", "in_progress", "completed", "blocked"], width=200,
            fg_color=BG_INPUT, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        self.status_combo.set(task.get("status") or "pending")
        self.status_combo.pack(anchor="w", pady=(0, SPACE_MD))

        # --- Assign to ---
        ctk.CTkLabel(scroll, text="Priradiť komu", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        team = get_my_team(self.user_id)
        self._team_map = {}
        team_names = ["Nepriradené"]
        if isinstance(team, list):
            for member in team:
                if isinstance(member, dict):
                    uname = member.get("username", "")
                    uid = member.get("id")
                else:
                    uname = member[3] if len(member) > 3 else str(member)
                    uid = member[0]
                self._team_map[uname] = uid
                team_names.append(uname)

        self.assign_combo = ctk.CTkOptionMenu(
            scroll, values=team_names, width=200,
            fg_color=BG_INPUT, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        current_assigned = task.get("assigned_username") or "Nepriradené"
        self.assign_combo.set(current_assigned)
        self.assign_combo.pack(anchor="w", pady=(0, SPACE_MD))

        # --- Notes ---
        ctk.CTkLabel(scroll, text="Poznámky", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.notes_entry = ctk.CTkTextbox(
            scroll, height=60, width=480,
            fg_color=BG_INPUT, border_color=BORDER, border_width=1,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.notes_entry.insert("0.0", task.get("notes") or "")
        self.notes_entry.pack(fill="x", pady=(0, SPACE_MD))

        # --- Dependencies ---
        ctk.CTkLabel(scroll, text="Závislosti (táto úloha závisí od)", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(
            anchor="w", pady=(0, 4))

        all_tasks = task_repo.get_tasks_for_project_with_cpm(self.project_id)
        current_deps = task_repo.get_task_dependencies(task.get("id"))
        current_dep_ids = {d["depends_on_task_id"] for d in current_deps}

        self._dep_vars: dict[int, ctk.IntVar] = {}
        dep_frame = ctk.CTkScrollableFrame(scroll, height=120, fg_color=BG_ROW, corner_radius=RADIUS_SM)
        dep_frame.pack(fill="x", pady=(0, SPACE_LG))

        for t in all_tasks:
            t_id = t.get("id")
            if t_id == task.get("id"):
                continue
            var = ctk.IntVar(value=1 if t_id in current_dep_ids else 0)
            self._dep_vars[t_id] = var
            ctk.CTkCheckBox(
                dep_frame, text=f"{t.get('name', '')} (ID:{t_id})",
                variable=var, font=get_font(FONT_SIZE_SM),
                text_color=TEXT_PRIMARY,
            ).pack(anchor="w", padx=SPACE_SM, pady=2)

        # --- Prílohy ---
        ctk.CTkLabel(scroll, text="📎 Prílohy", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(
            anchor="w", pady=(0, 4))

        self._attach_frame = ctk.CTkFrame(scroll, fg_color=BG_ROW, corner_radius=RADIUS_SM)
        self._attach_frame.pack(fill="x", pady=(0, 4))
        self._refresh_attachments()

        ctk.CTkButton(
            scroll, text="+ Pridať prílohu", width=160,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
            font=get_font(FONT_SIZE_SM), corner_radius=RADIUS_SM,
            command=self._add_attachment,
        ).pack(anchor="w", pady=(0, SPACE_MD))

        # --- Komentáre ---
        ctk.CTkLabel(scroll, text="💬 Komentáre", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(
            anchor="w", pady=(0, 4))

        self._comments_frame = ctk.CTkScrollableFrame(
            scroll, height=100, fg_color=BG_ROW, corner_radius=RADIUS_SM,
        )
        self._comments_frame.pack(fill="x", pady=(0, 4))
        self._refresh_comments()

        comment_row = ctk.CTkFrame(scroll, fg_color="transparent")
        comment_row.pack(fill="x", pady=(0, 12))

        self._comment_entry = ctk.CTkEntry(
            comment_row, placeholder_text="Napíš komentár...",
            fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self._comment_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACE_SM))
        self._comment_entry.bind("<Return>", lambda e: self._post_comment())

        ctk.CTkButton(
            comment_row, text="Odoslať", width=80, height=HEIGHT_BTN_SM,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            font=get_font(FONT_SIZE_BASE), corner_radius=RADIUS_SM,
            command=self._post_comment,
        ).pack(side="right")

        # --- CPM Info (read-only) ---
        cpm_frame = ctk.CTkFrame(
            scroll, fg_color=BG_CARD, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        cpm_frame.pack(fill="x", pady=(0, SPACE_LG))

        ctk.CTkLabel(
            cpm_frame, text="CPM Výsledky",
            font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=SPACE_MD, pady=(SPACE_SM, 4))

        cpm_text = (
            f"ES: {task.get('es', 0)}   EF: {task.get('ef', 0)}   "
            f"LS: {task.get('ls', 0)}   LF: {task.get('lf', 0)}   "
            f"Float: {task.get('total_float', 0)}   "
            f"Kritická: {'Áno' if task.get('is_critical') else 'Nie'}"
        )
        ctk.CTkLabel(
            cpm_frame, text=cpm_text,
            font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=SPACE_MD, pady=(0, SPACE_SM))

        # --- Save / Message ---
        self._msg_label = ctk.CTkLabel(scroll, text="", font=get_font(FONT_SIZE_SM))
        self._msg_label.pack(pady=(0, 4))

        ctk.CTkButton(
            scroll, text="Uložiť zmeny", fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            width=200, command=self._save,
        ).pack(pady=(0, SPACE_LG))

    # ------------------------------------------------------------------
    # Attachments
    # ------------------------------------------------------------------

    def _refresh_attachments(self):
        for w in self._attach_frame.winfo_children():
            w.destroy()

        attachments = get_attachments_for_task(self.task.get("id"))
        if not attachments:
            ctk.CTkLabel(
                self._attach_frame, text="Žiadne prílohy",
                font=get_font(FONT_SIZE_XS), text_color=TEXT_SECONDARY,
            ).pack(padx=SPACE_SM, pady=SPACE_SM)
            return

        for att in attachments:
            row = ctk.CTkFrame(self._attach_frame, fg_color="transparent")
            row.pack(fill="x", padx=SPACE_SM, pady=2)

            ctk.CTkLabel(
                row, text=f"📄 {att.get('file_name', '')}",
                font=get_font(FONT_SIZE_XS), text_color=TEXT_PRIMARY,
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=str(att.get("uploaded_at", ""))[:16],
                font=get_font(FONT_SIZE_XS), text_color=TEXT_SECONDARY,
            ).pack(side="left", padx=(SPACE_SM, 0))

            def open_file(path=att.get("file_path", "")):
                try:
                    os.startfile(path)
                except Exception:
                    pass

            ctk.CTkButton(
                row, text="Otvoriť", width=55, height=22,
                font=get_font(FONT_SIZE_XS),
                fg_color="transparent", hover_color=BG_ROW,
                text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
                corner_radius=RADIUS_SM, command=open_file,
            ).pack(side="right", padx=(4, 0))

            def remove(aid=att.get("id")):
                delete_attachment(aid)
                self._refresh_attachments()

            ctk.CTkButton(
                row, text="✕", width=24, height=22,
                font=get_font(FONT_SIZE_XS),
                fg_color=DANGER, hover_color=PRIMARY,
                text_color=("#FFFFFF", "#FFFFFF"), command=remove,
                corner_radius=RADIUS_SM,
            ).pack(side="right")

    def _add_attachment(self):
        file_path = fd.askopenfilename(
            title="Vybrať prílohu",
            filetypes=[("Všetky súbory", "*.*")],
        )
        if not file_path:
            return

        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
        file_name = os.path.basename(file_path)

        # Skopíruj súbor do attachments/
        dest = os.path.join(ATTACHMENTS_DIR, f"{self.task.get('id')}_{file_name}")
        try:
            shutil.copy2(file_path, dest)
        except Exception as e:
            print(f"Copy error: {e}")
            dest = file_path  # fallback — použij pôvodnú cestu

        add_attachment(self.task.get("id"), file_name, dest, self.user_id)
        self._refresh_attachments()

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def _refresh_comments(self):
        for w in self._comments_frame.winfo_children():
            w.destroy()

        comments = get_task_comments(self.task.get("id"))
        if not comments:
            ctk.CTkLabel(
                self._comments_frame, text="Zatiaľ žiadne komentáre",
                font=get_font(FONT_SIZE_XS), text_color=TEXT_SECONDARY,
            ).pack(padx=SPACE_SM, pady=SPACE_SM)
            return

        for c in comments:
            bubble = ctk.CTkFrame(
                self._comments_frame, fg_color=BG_CARD,
                corner_radius=RADIUS_SM, border_width=1, border_color=BORDER,
            )
            bubble.pack(fill="x", padx=SPACE_SM, pady=3)

            header = ctk.CTkFrame(bubble, fg_color="transparent")
            header.pack(fill="x", padx=SPACE_SM, pady=(4, 0))

            ctk.CTkLabel(
                header, text=f"👤 {c.get('username', '?')}",
                font=get_font(FONT_SIZE_XS, "bold"), text_color=PRIMARY,
            ).pack(side="left")

            ctk.CTkLabel(
                header, text=str(c.get("created_at", ""))[:16],
                font=get_font(FONT_SIZE_XS), text_color=TEXT_SECONDARY,
            ).pack(side="right")

            ctk.CTkLabel(
                bubble, text=c.get("content", ""),
                font=get_font(FONT_SIZE_SM), text_color=TEXT_PRIMARY,
                wraplength=450, justify="left",
            ).pack(anchor="w", padx=SPACE_SM, pady=(2, SPACE_SM))

    def _post_comment(self):
        text = self._comment_entry.get().strip()
        if not text:
            return
        add_comment(self.task.get("id"), self.user_id, text)
        self._comment_entry.delete(0, "end")
        self._refresh_comments()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            self._msg_label.configure(text="Názov nemôže byť prázdny!", text_color=DANGER)
            return

        desc = self.desc_entry.get("0.0", "end").strip()
        try:
            duration = max(1, int(self.dur_entry.get()))
        except ValueError:
            duration = 1
        try:
            delay = max(0, int(self.delay_entry.get()))
        except ValueError:
            delay = 0

        category = self.cat_combo.get()
        status = self.status_combo.get()
        notes = self.notes_entry.get("0.0", "end").strip()

        assign_name = self.assign_combo.get()
        assigned_to = self._team_map.get(assign_name)

        # Update task
        task_repo.update_task_full(
            self.task["id"], name, desc, duration, delay, category, status, notes, assigned_to
        )

        # Update dependencies
        old_deps = task_repo.get_task_dependencies(self.task["id"])
        old_dep_ids = {d["depends_on_task_id"] for d in old_deps}
        new_dep_ids = {tid for tid, var in self._dep_vars.items() if var.get() == 1}

        for dep_id in new_dep_ids - old_dep_ids:
            task_repo.add_dependency(self.task["id"], dep_id)
        for dep_id in old_dep_ids - new_dep_ids:
            task_repo.remove_dependency(self.task["id"], dep_id)

        self.on_save()
        self.destroy()


# ======================================================================
# Add Task Dialog (simplified)
# ======================================================================

class AddTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, project_id, user_id, on_save):
        super().__init__(parent)
        self.project_id = project_id
        self.user_id = user_id
        self.on_save = on_save

        self.title("Nová Úloha")
        self.geometry("500x580")
        self.resizable(True, True)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        pad = {"padx": 8, "anchor": "w"}

        ctk.CTkLabel(
            scroll, text="Nová úloha",
            font=get_font(FONT_SIZE_LG, "bold"), text_color=TEXT_PRIMARY,
        ).pack(**pad, pady=(0, SPACE_MD))

        # --- Názov ---
        ctk.CTkLabel(scroll, text="Názov úlohy:", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(**pad, pady=(0, 4))
        self.name_entry = ctk.CTkEntry(
            scroll, width=440, placeholder_text="Názov úlohy",
            height=HEIGHT_INPUT, fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.name_entry.pack(**pad)
        self.name_entry.focus_set()

        # --- Trvanie ---
        dur_row = ctk.CTkFrame(scroll, fg_color="transparent")
        dur_row.pack(fill="x", padx=SPACE_SM, pady=(SPACE_MD, 0))

        ctk.CTkLabel(dur_row, text="Trvanie (dni):", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(side="left")
        self.dur_entry = ctk.CTkEntry(
            dur_row, width=80, height=HEIGHT_INPUT,
            fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.dur_entry.insert(0, "1")
        self.dur_entry.pack(side="left", padx=(SPACE_SM, 0))

        # --- Kategória ---
        ctk.CTkLabel(scroll, text="Kategória:", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(**pad, pady=(SPACE_MD, 4))
        self.cat_combo = ctk.CTkOptionMenu(
            scroll, values=CATEGORY_OPTIONS, width=200,
            fg_color=BG_INPUT, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        self.cat_combo.set("Other")
        self.cat_combo.pack(**pad)

        # --- Priradiť komu ---
        ctk.CTkLabel(scroll, text="Priradiť komu:", font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY).pack(**pad, pady=(SPACE_MD, 4))
        team = get_my_team(self.user_id)
        self._team_map = {}
        team_names = ["Nepriradené"]
        if isinstance(team, list):
            for m in team:
                if isinstance(m, dict):
                    self._team_map[m.get("username", "")] = m.get("id")
                    team_names.append(m.get("username", ""))

        self.assign_combo = ctk.CTkOptionMenu(
            scroll, values=team_names, width=200,
            fg_color=BG_INPUT, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        self.assign_combo.set("Nepriradené")
        self.assign_combo.pack(**pad)

        # --- Závislosti ---
        all_tasks = task_repo.get_tasks_for_project_with_cpm(self.project_id)
        self._dep_vars: dict[int, ctk.IntVar] = {}

        if all_tasks:
            ctk.CTkLabel(
                scroll, text="Závisí na (vyber predchádzajúce úlohy):",
                font=get_font(FONT_SIZE_SM, "bold"), text_color=TEXT_SECONDARY,
            ).pack(**pad, pady=(SPACE_MD, 4))

            dep_frame = ctk.CTkScrollableFrame(scroll, height=110, fg_color=BG_ROW, corner_radius=RADIUS_SM)
            dep_frame.pack(fill="x", padx=SPACE_SM, pady=(0, SPACE_SM))

            for t in all_tasks:
                t_id = t.get("id")
                var = ctk.IntVar(value=0)
                self._dep_vars[t_id] = var
                ctk.CTkCheckBox(
                    dep_frame, text=f"{t.get('name', '')} (ID:{t_id})",
                    variable=var, font=get_font(FONT_SIZE_SM),
                    text_color=TEXT_PRIMARY,
                ).pack(anchor="w", padx=SPACE_SM, pady=2)

        # --- Správa + Tlačidlo ---
        self._msg = ctk.CTkLabel(scroll, text="", font=get_font(FONT_SIZE_SM))
        self._msg.pack(pady=(SPACE_SM, 0))

        ctk.CTkButton(
            scroll, text="Vytvoriť úlohu", fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            width=220, command=self._save,
        ).pack(pady=(SPACE_SM, SPACE_LG))

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            self._msg.configure(text="Zadaj názov úlohy!", text_color=DANGER)
            return

        try:
            duration = max(1, int(self.dur_entry.get()))
        except ValueError:
            duration = 1

        assign_name = self.assign_combo.get()
        assigned_to = self._team_map.get(assign_name, self.user_id)

        # Create task
        task_id = task_repo.create_task(self.project_id, name, assigned_to, self.user_id)

        if task_id:
            category = self.cat_combo.get()
            task_repo.update_task_full(
                task_id, name, "", duration, 0, category, "pending", "", assigned_to,
            )

            # Add dependencies
            for dep_id, var in self._dep_vars.items():
                if var.get() == 1:
                    task_repo.add_dependency(task_id, dep_id)

        self.on_save()
        self.destroy()
