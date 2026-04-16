"""
Project List View — project cards with progress, search, new project dialog, templates.
Dual-mode dizajn: card borders, PROJECT_STATUS_COLORS z theme, Segoe UI font.
"""
import customtkinter as ctk

from logic.project_manager import get_user_projects
from logic.template_manager import get_templates, create_project_from_template
from repositories import project_repo, task_repo
from ui.screens.project_detail import ProjectDetailView
from ui.theme import (
    PRIMARY, PRIMARY_HOVER, ACCENT, ACCENT_HOVER, DANGER,
    BG_CARD, BG_ROW, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    PROJECT_STATUS_COLORS, PROJECT_STATUS_LABELS,
    color_blend_dual,
    get_font,
    FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_XL,
    RADIUS_SM, RADIUS_MD,
    HEIGHT_BTN_SM, HEIGHT_BTN_MD, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
)


class ProjectsView(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.parent_app = parent
        self.user_data  = user_data
        self.user_id    = user_data["id"] if isinstance(user_data, dict) else user_data[0]
        self._search_query = ""

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_search_bar()
        self._build_list()

    # ── Header ─────────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, SPACE_SM))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Projekty",
            font=get_font(FONT_SIZE_XL, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2)

        ctk.CTkButton(
            btn_frame, text="Zo šablóny", width=120,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=self._open_from_template,
        ).pack(side="left", padx=(0, SPACE_SM))

        ctk.CTkButton(
            btn_frame, text="+ Nový projekt", width=130,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._open_new_project,
        ).pack(side="left")

    # ── Search bar ─────────────────────────────────────────────────────────────

    def _build_search_bar(self):
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, SPACE_SM))

        self._search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Hľadať projekt...",
            width=300, height=HEIGHT_BTN_MD,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            border_color=BORDER,
        )
        self._search_entry.pack(side="left")
        self._search_entry.bind("<KeyRelease>", self._on_search)

        self._status_filter = ctk.CTkOptionMenu(
            search_frame,
            values=["Všetky", "Aktívne", "Dokončené", "Archivované"],
            width=150, height=HEIGHT_BTN_MD,
            corner_radius=RADIUS_SM,
            button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            font=get_font(FONT_SIZE_BASE),
            command=self._on_filter,
        )
        self._status_filter.set("Všetky")
        self._status_filter.pack(side="left", padx=(SPACE_MD, 0))

    def _on_search(self, event=None):
        self._search_query = self._search_entry.get().strip().lower()
        self._refresh()

    def _on_filter(self, value):
        self._refresh()

    # ── Project list ───────────────────────────────────────────────────────────

    def _build_list(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
        self._refresh()

    def _refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        projects = get_user_projects(self.user_id)

        if self._search_query:
            projects = [
                p for p in projects
                if self._search_query in (p.get("name", "") if isinstance(p, dict) else str(p)).lower()
                or self._search_query in (p.get("description", "") if isinstance(p, dict) else "").lower()
            ]

        status_map = {"Aktívne": "active", "Dokončené": "completed", "Archivované": "archived"}
        status_filter = self._status_filter.get() if hasattr(self, "_status_filter") else "Všetky"
        if status_filter in status_map:
            fval = status_map[status_filter]
            projects = [
                p for p in projects
                if (p.get("status") if isinstance(p, dict) else "active") == fval
            ]

        if not projects:
            ctk.CTkLabel(
                self._scroll,
                text="Žiadne projekty nenájdené.\nVytvorte nový projekt tlačidlom hore.",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).pack(pady=SPACE_XL * 2)
            return

        for proj in projects:
            self._create_project_card(proj)

    def _create_project_card(self, project_data):
        if isinstance(project_data, dict):
            pid    = project_data["id"]
            name   = project_data["name"]
            desc   = project_data.get("description", "")
            status = project_data.get("status", "active")
        else:
            pid, name, desc, status = project_data

        strip_color  = PROJECT_STATUS_COLORS.get(status, ("gray", "gray"))
        badge_bg     = color_blend_dual(strip_color, 0.15)
        status_label = PROJECT_STATUS_LABELS.get(status, status)

        # Karta s borderom
        card = ctk.CTkFrame(
            self._scroll, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        card.pack(fill="x", pady=4, padx=2)

        # Farebný ľavý strip (stav)
        strip = ctk.CTkFrame(card, width=4, fg_color=strip_color, corner_radius=0)
        strip.pack(side="left", fill="y")
        strip.pack_propagate(False)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)

        # Akčné tlačidlá vpravo
        btn_col = ctk.CTkFrame(card, fg_color="transparent")
        btn_col.pack(side="right", padx=SPACE_MD, pady=SPACE_MD)

        ctk.CTkButton(
            btn_col, text="Otvoriť", width=80,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            height=HEIGHT_BTN_SM, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=lambda p=project_data: self._open_detail(p),
        ).pack(pady=(0, SPACE_SM))

        ctk.CTkButton(
            btn_col, text="⚙", width=36, height=28,
            fg_color="transparent", hover_color=BG_ROW,
            border_width=1, border_color=BORDER,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=lambda p=project_data: self._open_project_menu(p),
        ).pack()

        # Názov + badge
        name_row = ctk.CTkFrame(content, fg_color="transparent")
        name_row.pack(anchor="w", padx=SPACE_LG, pady=(SPACE_MD, 0))

        ctk.CTkLabel(
            name_row, text=name,
            font=get_font(FONT_SIZE_MD, "bold"), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            name_row, text=status_label,
            font=get_font(FONT_SIZE_SM, "bold"),
            text_color=strip_color,
            fg_color=badge_bg,
            corner_radius=RADIUS_SM,
            padx=SPACE_SM, pady=2,
        ).pack(side="left", padx=(SPACE_SM, 0))

        # Popis
        desc_text = desc if desc else "Bez popisu"
        if len(desc_text) > 90:
            desc_text = desc_text[:88] + "…"
        ctk.CTkLabel(
            content, text=desc_text,
            text_color=TEXT_SECONDARY, font=get_font(FONT_SIZE_SM),
        ).pack(anchor="w", padx=SPACE_LG, pady=(2, SPACE_SM))

        # Progress bar
        try:
            bd = task_repo.get_status_breakdown_for_project(pid)
            total, completed_t, progress = bd["total"], bd["completed"], bd["progress"]
        except Exception:
            total, completed_t, progress = 0, 0, 0.0

        prog_frame = ctk.CTkFrame(content, fg_color="transparent")
        prog_frame.pack(anchor="w", padx=SPACE_LG, pady=(0, SPACE_MD), fill="x")

        bar = ctk.CTkProgressBar(
            prog_frame, width=160, height=6,
            progress_color=ACCENT,
            fg_color=BG_ROW,
        )
        bar.set(progress)
        bar.pack(side="left", padx=(0, SPACE_SM))

        pct = int(progress * 100)
        ctk.CTkLabel(
            prog_frame, text=f"{pct}%  •  {completed_t}/{total} úloh",
            text_color=TEXT_SECONDARY, font=get_font(FONT_SIZE_SM),
        ).pack(side="left")

    # ── Detail view ────────────────────────────────────────────────────────────

    def _open_detail(self, project_data):
        self.grid_forget()
        self.detail_view = ProjectDetailView(
            self.master, project_data, self.user_data,
            back_callback=self._show_list,
        )
        self.detail_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def _show_list(self):
        if hasattr(self, "detail_view"):
            self.detail_view.destroy()
        self.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self._refresh()

    # ── Project menu ───────────────────────────────────────────────────────────

    def _open_project_menu(self, project_data):
        if isinstance(project_data, dict):
            pid, name, status = project_data["id"], project_data["name"], project_data.get("status", "active")
        else:
            pid, name, status = project_data[0], project_data[1], project_data[3]

        menu = ctk.CTkToplevel(self)
        menu.title(f"Projekt: {name}")
        menu.geometry("300x270")
        menu.resizable(False, False)

        ctk.CTkLabel(
            menu, text=name,
            font=get_font(FONT_SIZE_MD, "bold"), text_color=TEXT_PRIMARY,
        ).pack(pady=(SPACE_LG, SPACE_MD), padx=SPACE_LG, anchor="w")

        def set_status(new_status):
            project_repo.update_project_status(pid, new_status)
            menu.destroy()
            self._refresh()

        if status != "completed":
            ctk.CTkButton(
                menu, text="Oznacit ako dokonceny", width=260,
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
                font=get_font(FONT_SIZE_BASE, "bold"),
                command=lambda: set_status("completed"),
            ).pack(pady=4, padx=SPACE_LG)

        if status != "active":
            ctk.CTkButton(
                menu, text="Nastavit ako aktivny", width=260,
                fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
                font=get_font(FONT_SIZE_BASE, "bold"),
                command=lambda: set_status("active"),
            ).pack(pady=4, padx=SPACE_LG)

        if status != "archived":
            ctk.CTkButton(
                menu, text="Archivovat", width=260,
                fg_color="transparent", hover_color=BG_ROW,
                text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
                height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
                font=get_font(FONT_SIZE_BASE),
                command=lambda: set_status("archived"),
            ).pack(pady=4, padx=SPACE_LG)

        ctk.CTkButton(
            menu, text="Ulozit ako sablonu", width=260,
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=lambda: self._save_as_template(pid, name, menu),
        ).pack(pady=4, padx=SPACE_LG)

    def _save_as_template(self, pid, name, parent_dialog):
        try:
            orig = project_repo.get_project_by_id(pid)
            if orig:
                project_repo.create_project(
                    self.user_id, f"[Sablona] {name}",
                    orig.get("description", ""),
                    status="active", is_template=True,
                )
                tasks = task_repo.get_tasks_for_project_with_cpm(pid)
                new_templates = project_repo.get_templates(self.user_id)
                if new_templates:
                    new_tid = new_templates[-1]["id"]
                    for t in tasks:
                        task_repo.create_task_from_template(
                            new_tid, t.get("name", ""), t.get("description", ""),
                            None, self.user_id, None,
                        )
        except Exception as e:
            print(f"Chyba pri ukladani sablony: {e}")

        parent_dialog.destroy()
        self._refresh()

    # ── Dialógy ────────────────────────────────────────────────────────────────

    def _open_new_project(self):
        NewProjectDialog(self, self.user_id, on_save=self._refresh)

    def _open_from_template(self):
        FromTemplateDialog(self, self.user_id, on_save=self._refresh)


# ══════════════════════════════════════════════════════════════════════════════
# New Project Dialog
# ══════════════════════════════════════════════════════════════════════════════

class NewProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent, user_id, on_save):
        super().__init__(parent)
        self.user_id = user_id
        self.on_save = on_save
        self.title("Novy projekt")
        self.geometry("460x430")
        self.resizable(False, False)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACE_SM, pady=SPACE_SM)

        pad = {"padx": SPACE_LG, "anchor": "w"}

        ctk.CTkLabel(
            scroll, text="Vytvorit novy projekt",
            font=get_font(FONT_SIZE_LG, "bold"), text_color=TEXT_PRIMARY,
        ).pack(pady=(SPACE_MD, SPACE_LG), **pad)

        ctk.CTkLabel(scroll, text="Nazov projektu:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(0, SPACE_SM))
        self.name_entry = ctk.CTkEntry(scroll, width=400, height=HEIGHT_INPUT, corner_radius=RADIUS_SM, font=get_font(FONT_SIZE_BASE), border_color=BORDER, placeholder_text="Moj novy projekt")
        self.name_entry.pack(**pad)
        self.name_entry.focus_set()

        ctk.CTkLabel(scroll, text="Popis:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(SPACE_MD, SPACE_SM))
        self.desc_entry = ctk.CTkTextbox(scroll, height=80, width=400, font=get_font(FONT_SIZE_BASE), border_color=BORDER, border_width=1)
        self.desc_entry.pack(**pad)

        ctk.CTkLabel(scroll, text="Stav:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(SPACE_MD, SPACE_SM))
        self.status_combo = ctk.CTkOptionMenu(scroll, values=["active", "completed", "archived"], width=200, height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER, font=get_font(FONT_SIZE_BASE))
        self.status_combo.set("active")
        self.status_combo.pack(**pad)

        self._msg = ctk.CTkLabel(scroll, text="", font=get_font(FONT_SIZE_BASE))
        self._msg.pack(pady=(SPACE_MD, 0))

        ctk.CTkButton(
            scroll, text="Vytvorit projekt",
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            width=220, height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._save,
        ).pack(pady=(SPACE_SM, SPACE_LG))

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            self._msg.configure(text="Zadaj nazov projektu!", text_color=DANGER)
            return
        desc   = self.desc_entry.get("0.0", "end").strip()
        status = self.status_combo.get()
        try:
            project_repo.create_project(self.user_id, name, desc, status=status)
            self.on_save()
            self.destroy()
        except Exception as e:
            self._msg.configure(text=f"Chyba: {e}", text_color=DANGER)


# ══════════════════════════════════════════════════════════════════════════════
# From Template Dialog
# ══════════════════════════════════════════════════════════════════════════════

class FromTemplateDialog(ctk.CTkToplevel):
    def __init__(self, parent, user_id, on_save):
        super().__init__(parent)
        self.user_id = user_id
        self.on_save = on_save
        self.title("Vytvorit zo sablony")
        self.geometry("450x350")
        self.resizable(False, False)

        pad = {"padx": SPACE_XL, "anchor": "w"}

        ctk.CTkLabel(
            self, text="Vybrat sablonu",
            font=get_font(FONT_SIZE_LG, "bold"), text_color=TEXT_PRIMARY,
        ).pack(pady=(SPACE_XL, SPACE_MD), **pad)

        templates = get_templates(self.user_id)
        self._template_map = {}

        if not templates:
            ctk.CTkLabel(
                self, text="Nemas ziadne sablony.\n\nSablonu vytvoris cez menu projektu\n-> 'Ulozit ako sablonu'.",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).pack(pady=SPACE_XL, padx=SPACE_XL)
            return

        names = []
        for t in templates:
            tname = t.get("name", "Sablona")
            self._template_map[tname] = t["id"]
            names.append(tname)

        ctk.CTkLabel(self, text="Sablona:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(0, SPACE_SM))
        self.tmpl_combo = ctk.CTkOptionMenu(self, values=names, width=380, height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER, font=get_font(FONT_SIZE_BASE))
        self.tmpl_combo.set(names[0])
        self.tmpl_combo.pack(**pad)

        ctk.CTkLabel(self, text="Nazov noveho projektu:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(SPACE_LG, SPACE_SM))
        self.name_entry = ctk.CTkEntry(self, width=380, height=HEIGHT_INPUT, corner_radius=RADIUS_SM, font=get_font(FONT_SIZE_BASE), border_color=BORDER, placeholder_text="Nazov projektu")
        self.name_entry.pack(**pad)
        self.name_entry.focus_set()

        self._msg = ctk.CTkLabel(self, text="", font=get_font(FONT_SIZE_BASE))
        self._msg.pack(pady=(SPACE_MD, 0))

        ctk.CTkButton(
            self, text="Vytvorit z sablony",
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            width=220, height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._create,
        ).pack(pady=(SPACE_SM, SPACE_XL))

    def _create(self):
        if not hasattr(self, "tmpl_combo"):
            return
        name = self.name_entry.get().strip()
        if not name:
            self._msg.configure(text="Zadaj nazov projektu!", text_color=DANGER)
            return
        tmpl_name = self.tmpl_combo.get()
        tmpl_id   = self._template_map.get(tmpl_name)
        if not tmpl_id:
            self._msg.configure(text="Vyber sablonu!", text_color=DANGER)
            return
        result = create_project_from_template(tmpl_id, name, self.user_id)
        if result:
            self.on_save()
            self.destroy()
        else:
            self._msg.configure(text="Chyba pri vytvarani projektu.", text_color=DANGER)
