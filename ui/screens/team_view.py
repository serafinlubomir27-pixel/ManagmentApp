"""
Team Management View — member cards with workload stats, task details, role badges.
Dual-mode: ROLE_COLORS a STATUS_COLORS z theme, card borders, Segoe UI font.
"""
import customtkinter as ctk

from logic.hierarchy import get_my_team, add_new_member
from repositories import task_repo, user_repo
from ui.theme import (
    PRIMARY, PRIMARY_HOVER, ACCENT, DANGER, WARNING, SUCCESS,
    BG_CARD, BG_ROW, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    ROLE_COLORS, STATUS_COLORS,
    color_blend_dual,
    get_font,
    FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL, FONT_SIZE_2XL,
    RADIUS_SM, RADIUS_MD,
    HEIGHT_BTN_SM, HEIGHT_BTN_MD, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
)

ROLE_LABELS = {
    "admin":    "Admin",
    "manager":  "Manazér",
    "employee": "Zamestnanec",
}


class TeamView(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.user_id   = user_data["id"]   if isinstance(user_data, dict) else user_data[0]
        self.user_role = user_data["role"]  if isinstance(user_data, dict) else user_data[4]
        self.user_data = user_data

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_content()

    # ── Header ─────────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, SPACE_MD))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Tímový Dashboard",
            font=get_font(FONT_SIZE_XL, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        if self.user_role in ("admin", "manager"):
            ctk.CTkButton(
                header, text="+ Pridat clena", width=140,
                fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
                font=get_font(FONT_SIZE_BASE, "bold"),
                command=self._open_add_dialog,
            ).grid(row=0, column=2, padx=(SPACE_MD, 0))

    # ── Content ────────────────────────────────────────────────────────────────

    def _build_content(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
        self._refresh()

    def _refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        members = get_my_team(self.user_id)

        if not members:
            ctk.CTkLabel(
                self._scroll,
                text="V time zatial nie su ziadni clenovia.\nPridajte prveho clena tlacidlom hore.",
                font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY,
            ).pack(pady=SPACE_XL * 2)
            return

        self._build_team_summary(members)
        for m in members:
            self._build_member_card(m)

    # ── Team summary ───────────────────────────────────────────────────────────

    def _build_team_summary(self, members):
        summary = ctk.CTkFrame(
            self._scroll, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        summary.pack(fill="x", pady=(0, SPACE_LG))

        inner = ctk.CTkFrame(summary, fg_color="transparent")
        inner.pack(fill="x", padx=SPACE_LG, pady=SPACE_MD)
        for i in range(4):
            inner.grid_columnconfigure(i, weight=1)

        total_members   = len(members)
        total_tasks     = 0
        total_completed = 0
        total_in_progress = 0

        for m in members:
            mid = m["id"] if isinstance(m, dict) else m[0]
            wl  = task_repo.get_workload_for_user(mid)
            total_tasks       += wl["total"]
            total_completed   += wl["completed"]
            total_in_progress += wl["in_progress"]

        stats = [
            ("Clenovia",    str(total_members),       PRIMARY),
            ("Celkom uloh", str(total_tasks),          ACCENT),
            ("Prebieha",    str(total_in_progress),    WARNING),
            ("Dokoncene",   str(total_completed),      SUCCESS),
        ]

        for i, (label, value, color) in enumerate(stats):
            box = ctk.CTkFrame(inner, fg_color="transparent")
            box.grid(row=0, column=i, sticky="nsew", padx=SPACE_SM)

            ctk.CTkLabel(
                box, text=label,
                font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY,
            ).pack(anchor="w")

            ctk.CTkLabel(
                box, text=value,
                font=get_font(FONT_SIZE_2XL, "bold"), text_color=color,
            ).pack(anchor="w")

    # ── Member card ────────────────────────────────────────────────────────────

    def _build_member_card(self, member):
        if isinstance(member, dict):
            mid       = member.get("id")
            full_name = member.get("full_name", "")
            username  = member.get("username", "")
            role      = member.get("role", "employee")
        else:
            mid, full_name, role, username = member[0], member[1], member[2], member[3]

        wl = task_repo.get_workload_for_user(mid)

        card = ctk.CTkFrame(
            self._scroll, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        card.pack(fill="x", pady=4)

        main_row = ctk.CTkFrame(card, fg_color="transparent")
        main_row.pack(fill="x", padx=SPACE_LG, pady=SPACE_MD)
        main_row.grid_columnconfigure(1, weight=1)

        # Avatar kruh
        avatar_color = ROLE_COLORS.get(role, ("gray", "gray"))
        initials     = "".join(w[0].upper() for w in full_name.split()[:2]) if full_name else "?"

        avatar = ctk.CTkFrame(
            main_row, width=48, height=48,
            fg_color=avatar_color, corner_radius=24,
        )
        avatar.grid(row=0, column=0, rowspan=2, padx=(0, SPACE_LG))
        avatar.grid_propagate(False)
        ctk.CTkLabel(
            avatar, text=initials,
            font=get_font(FONT_SIZE_LG, "bold"),
            text_color=("#FFFFFF", "#FFFFFF"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Meno + rola
        info = ctk.CTkFrame(main_row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")

        name_frame = ctk.CTkFrame(info, fg_color="transparent")
        name_frame.pack(anchor="w")

        ctk.CTkLabel(
            name_frame, text=full_name or username,
            font=get_font(FONT_SIZE_MD, "bold"), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        role_label = ROLE_LABELS.get(role, role)
        role_color = ROLE_COLORS.get(role, ("gray", "gray"))
        badge_bg   = color_blend_dual(role_color, 0.15)

        ctk.CTkLabel(
            name_frame, text=role_label,
            font=get_font(FONT_SIZE_SM, "bold"),
            text_color=role_color, fg_color=badge_bg,
            corner_radius=RADIUS_SM, padx=SPACE_SM, pady=2,
        ).pack(side="left", padx=(SPACE_SM, 0))

        ctk.CTkLabel(
            info, text=f"@{username}",
            font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        # Workload štatistiky
        stats_frame = ctk.CTkFrame(main_row, fg_color="transparent")
        stats_frame.grid(row=0, column=2, rowspan=2, padx=(SPACE_MD, 0))

        wl_data = [
            ("Ulohy",   str(wl["total"]),       TEXT_PRIMARY),
            ("Aktivne", str(wl["in_progress"]),  WARNING),
            ("Hotove",  str(wl["completed"]),    SUCCESS),
        ]
        for j, (lbl, val, color) in enumerate(wl_data):
            cell = ctk.CTkFrame(stats_frame, fg_color="transparent", width=60)
            cell.grid(row=0, column=j, padx=SPACE_SM)
            ctk.CTkLabel(cell, text=val, font=get_font(FONT_SIZE_LG, "bold"), text_color=color).pack()
            ctk.CTkLabel(cell, text=lbl, font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY).pack()

        # Progress
        if wl["total"] > 0:
            prog_frame = ctk.CTkFrame(main_row, fg_color="transparent")
            prog_frame.grid(row=0, column=3, rowspan=2, padx=(SPACE_LG, 0))

            prog_pct   = int(wl["progress"] * 100)
            prog_color = SUCCESS if prog_pct >= 70 else WARNING if prog_pct >= 40 else DANGER

            ctk.CTkLabel(
                prog_frame, text=f"{prog_pct}%",
                font=get_font(FONT_SIZE_MD, "bold"), text_color=prog_color,
            ).pack()

            bar = ctk.CTkProgressBar(
                prog_frame, width=80, height=8,
                progress_color=prog_color, fg_color=BG_ROW,
            )
            bar.set(wl["progress"])
            bar.pack(pady=(SPACE_SM, 0))

        # Rozbalovateľný zoznam úloh
        tasks = task_repo.get_tasks_assigned_to_user(mid)
        if tasks:
            self._build_task_list(card, tasks)

    # ── Task list v member karte ───────────────────────────────────────────────

    def _build_task_list(self, parent, tasks):
        task_container = ctk.CTkFrame(parent, fg_color="transparent")
        task_container.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_MD))

        is_expanded = ctk.BooleanVar(value=False)
        task_frame  = ctk.CTkFrame(task_container, fg_color="transparent")

        def toggle():
            if is_expanded.get():
                task_frame.pack_forget()
                is_expanded.set(False)
                toggle_btn.configure(text=f"Zobrazit ulohy ({len(tasks)})")
            else:
                task_frame.pack(fill="x", pady=(SPACE_SM, 0))
                is_expanded.set(True)
                toggle_btn.configure(text=f"Skryt ulohy ({len(tasks)})")

        toggle_btn = ctk.CTkButton(
            task_container,
            text=f"Zobrazit ulohy ({len(tasks)})",
            font=get_font(FONT_SIZE_SM),
            fg_color="transparent", hover_color=BG_ROW,
            text_color=TEXT_SECONDARY,
            border_width=1, border_color=BORDER,
            height=HEIGHT_BTN_SM, corner_radius=RADIUS_SM,
            anchor="w",
            command=toggle,
        )
        toggle_btn.pack(anchor="w")

        for t in tasks:
            name        = t.get("name", "")
            status      = t.get("status", "pending")
            project     = t.get("project_name", "")
            category    = t.get("category", "")
            is_critical = t.get("is_critical", False)
            duration    = t.get("duration") or 1

            row = ctk.CTkFrame(
                task_frame, fg_color=BG_ROW, corner_radius=RADIUS_SM,
                border_width=1, border_color=BORDER, height=32,
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=SPACE_MD, pady=SPACE_SM)

            st_color = STATUS_COLORS.get(status, ("gray", "gray"))
            ctk.CTkLabel(
                inner, text="●",
                font=get_font(FONT_SIZE_SM), text_color=st_color, width=14,
            ).pack(side="left")

            ctk.CTkLabel(
                inner, text=name,
                font=get_font(FONT_SIZE_SM), text_color=TEXT_PRIMARY,
            ).pack(side="left", padx=(SPACE_SM, 0))

            if is_critical:
                ctk.CTkLabel(
                    inner, text="Critical",
                    font=get_font(FONT_SIZE_SM, "bold"),
                    text_color=DANGER, fg_color=color_blend_dual(DANGER, 0.18),
                    corner_radius=3, padx=4,
                ).pack(side="left", padx=(SPACE_SM, 0))

            ctk.CTkLabel(
                inner, text=f"{duration}d",
                font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY,
            ).pack(side="right", padx=(SPACE_SM, 0))

            if category:
                ctk.CTkLabel(
                    inner, text=category,
                    font=get_font(FONT_SIZE_SM), text_color=TEXT_SECONDARY,
                    fg_color=BG_CARD, corner_radius=3, padx=4,
                ).pack(side="right", padx=(SPACE_SM, 0))

            ctk.CTkLabel(
                inner, text=project,
                font=get_font(FONT_SIZE_SM), text_color=PRIMARY,
            ).pack(side="right", padx=(SPACE_SM, 0))

    # ── Add member dialog ──────────────────────────────────────────────────────

    def _open_add_dialog(self):
        AddMemberDialog(self, self.user_id, on_save=self._refresh)


class AddMemberDialog(ctk.CTkToplevel):
    def __init__(self, parent, manager_id: int, on_save):
        super().__init__(parent)
        self.manager_id = manager_id
        self.on_save    = on_save

        self.title("Novy clen timu")
        self.geometry("400x430")
        self.resizable(False, False)

        pad = {"padx": SPACE_XL, "anchor": "w"}

        ctk.CTkLabel(
            self, text="Pridat noveho clena",
            font=get_font(FONT_SIZE_LG, "bold"), text_color=TEXT_PRIMARY,
        ).pack(pady=(SPACE_XL, SPACE_LG), **pad)

        for lbl, attr, show, ph in [
            ("Meno a priezvisko:", "name_entry",  "",  "Jan Novak"),
            ("Prihlasovacie meno:", "user_entry", "",  "jan.novak"),
            ("Heslo:",             "pass_entry",  "*", "Min. 4 znaky"),
        ]:
            ctk.CTkLabel(self, text=lbl, font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(0, SPACE_SM))
            e = ctk.CTkEntry(
                self, width=340, height=HEIGHT_INPUT, show=show,
                placeholder_text=ph, corner_radius=RADIUS_SM,
                font=get_font(FONT_SIZE_BASE), border_color=BORDER,
            )
            e.pack(**pad, pady=(0, SPACE_MD))
            setattr(self, attr, e)

        ctk.CTkLabel(self, text="Rola:", font=get_font(FONT_SIZE_BASE), text_color=TEXT_SECONDARY).pack(**pad, pady=(0, SPACE_SM))
        self.role_combo = ctk.CTkOptionMenu(
            self, values=["employee", "manager"], width=220,
            height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            font=get_font(FONT_SIZE_BASE),
        )
        self.role_combo.set("employee")
        self.role_combo.pack(**pad)

        self._msg = ctk.CTkLabel(self, text="", font=get_font(FONT_SIZE_BASE))
        self._msg.pack(pady=(SPACE_MD, 0))

        ctk.CTkButton(
            self, text="Vytvorit ucet",
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            width=200, height=HEIGHT_BTN_MD, corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._save,
        ).pack(pady=(SPACE_SM, SPACE_XL))

    def _save(self):
        name     = self.name_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        role     = self.role_combo.get()

        if not name or not username or not password:
            self._msg.configure(text="Vyplnte vsetky polia!", text_color=DANGER)
            return
        if len(password) < 4:
            self._msg.configure(text="Heslo musi mat aspon 4 znaky!", text_color=DANGER)
            return

        success, msg = add_new_member(self.manager_id, name, username, password, role)
        if success:
            self.on_save()
            self.destroy()
        else:
            self._msg.configure(text=msg, text_color=DANGER)
