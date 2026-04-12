import customtkinter as ctk
from logic.task_manager import get_tasks_for_project, add_task, update_task_status
from logic.hierarchy import get_my_team
from ui.screens.task_edit_dialog import TaskEditDialog  # Nezabudni na tento import

FILTER_OPTIONS = ["Všetky", "pending", "in_progress", "completed", "blocked"]
FILTER_DISPLAY = {
    "Všetky": "Všetky",
    "pending": "Pending",
    "in_progress": "In Progress",
    "completed": "Completed",
    "blocked": "Blocked",
}


class ProjectDetailView(ctk.CTkFrame):
    def __init__(self, parent, project_data, user_data, back_callback):
        super().__init__(parent, fg_color="transparent")
        self.project_id, self.project_name, _, _ = project_data
        self.user_id = user_data[0]
        self.back_callback = back_callback
        self.active_filter = "Všetky"

        # --- HLAVIČKA ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        # Tlačidlo Späť
        btn_back = ctk.CTkButton(header, text="⬅ Späť", width=60, fg_color="gray", command=self.back_callback)
        btn_back.pack(side="left", padx=(0, 20))

        title = ctk.CTkLabel(header, text=f"Projekt: {self.project_name}", font=("Arial", 24, "bold"))
        title.pack(side="left")

        # Tlačidlo Nová Úloha
        btn_add = ctk.CTkButton(header, text="+ Pridať úlohu", command=self.open_add_task_dialog)
        btn_add.pack(side="right")

        # --- FILTER ---
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(filter_frame, text="Filter:", font=("Arial", 13)).pack(side="left", padx=(0, 8))

        display_values = [FILTER_DISPLAY[k] for k in FILTER_OPTIONS]
        self.filter_combo = ctk.CTkOptionMenu(
            filter_frame,
            values=display_values,
            command=self._on_filter_change,
        )
        self.filter_combo.set("Všetky")
        self.filter_combo.pack(side="left")

        # --- ZOZNAM ÚLOH ---
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.refresh_tasks()

    def _on_filter_change(self, display_value):
        # Map display label back to internal key
        reverse = {v: k for k, v in FILTER_DISPLAY.items()}
        self.active_filter = reverse.get(display_value, "Všetky")
        self.refresh_tasks()

    def refresh_tasks(self):
        # 1. Vyčistíme staré widgety
        for w in self.scroll.winfo_children():
            w.destroy()

        # 2. Načítame úlohy
        tasks = get_tasks_for_project(self.project_id)

        # 3. Filtrujeme podľa aktívneho filtra
        if self.active_filter != "Všetky":
            tasks = [t for t in tasks if t.get("status") == self.active_filter]

        if not tasks:
            ctk.CTkLabel(self.scroll, text="Žiadne úlohy.").pack(pady=20)
            return

        # 4. Vykreslíme riadky
        for t in tasks:
            self.create_task_row(t)

    def create_task_row(self, task_data):
        # task_data is a dict from rows_to_dicts
        tid = task_data.get("id")
        name = task_data.get("name", "")
        status = task_data.get("status", "pending")
        date = task_data.get("due_date")
        assigned_user = task_data.get("username")

        row = ctk.CTkFrame(self.scroll, fg_color="#2B2B2B")
        row.pack(fill="x", pady=2)

        # Checkbox — checked if completed
        is_completed = status == "completed"
        chk_var = ctk.IntVar(value=1 if is_completed else 0)

        def toggle_status(task_id=tid, var=chk_var):
            new_status = "completed" if var.get() == 1 else "pending"
            update_task_status(task_id, new_status, self.user_id)
            self.refresh_tasks()

        chk = ctk.CTkCheckBox(row, text="", width=20, variable=chk_var, command=toggle_status)
        chk.pack(side="left", padx=10)

        # Názov
        ctk.CTkLabel(row, text=name, font=("Arial", 14)).pack(side="left", padx=10)

        # TLAČIDLO EDIT (Ceruzka) ✏️
        btn_edit = ctk.CTkButton(row, text="✏️", width=40, fg_color="gray",
                                 command=lambda td=task_data: self.open_task_detail(td))
        btn_edit.pack(side="right", padx=10)

        # Komu je pridelená
        if assigned_user:
            ctk.CTkLabel(row, text=f"👤 {assigned_user}", text_color="lightblue").pack(side="right", padx=10)

        # Status
        color = "green" if status == "completed" else "orange"
        ctk.CTkLabel(row, text=status, text_color=color).pack(side="right", padx=10)

    def open_task_detail(self, task_data):
        # Otvoríme nové okno a po zavretí zavoláme refresh_tasks
        TaskEditDialog(self, task_data, self.user_id, on_close_callback=self.refresh_tasks)

    def open_add_task_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nová Úloha")
        dialog.geometry("400x400")

        ctk.CTkLabel(dialog, text="Názov úlohy:").pack(pady=10)
        entry_name = ctk.CTkEntry(dialog, width=250)
        entry_name.pack(pady=5)

        ctk.CTkLabel(dialog, text="Prideliť komu:").pack(pady=10)

        team = get_my_team(self.user_id)
        team_dict = {t[3]: t[0] for t in team}
        team_names = list(team_dict.keys())

        combo_assign = ctk.CTkComboBox(dialog, values=team_names)
        combo_assign.pack(pady=5)
        if not team_names:
            combo_assign.set("Nikto (Len ja)")

        def save():
            name = entry_name.get()
            chosen_user_name = combo_assign.get()
            assigned_id = team_dict.get(chosen_user_name, self.user_id)

            if name:
                add_task(self.project_id, name, assigned_id, self.user_id)
                dialog.destroy()
                self.refresh_tasks()

        ctk.CTkButton(dialog, text="Vytvoriť", command=save).pack(pady=20)
