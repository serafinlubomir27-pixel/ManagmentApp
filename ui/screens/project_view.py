import customtkinter as ctk
from logic.project_manager import get_user_projects, create_test_project
from ui.screens.project_detail import ProjectDetailView


class ProjectsView(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.parent_app = parent
        self.user_data = user_data
        self.user_id = user_data[0]

        # --- HLAVIČKA ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 20))

        self.title = ctk.CTkLabel(self.header, text="Zoznam Projektov", font=("Arial", 24, "bold"))
        self.title.pack(side="left")

        # Tlačidlo + Nový projekt (len pre Admina/Managera, alebo pre všetkých podľa nastavenia)
        # Ak chceš, aby Skladník nemohol tvoriť projekty, daj sem podmienku if self.user_data[4] != 'employee':
        self.btn_new = ctk.CTkButton(self.header, text="+ Nový Projekt",
                                     fg_color="#2E7D32", hover_color="#1B5E20",
                                     command=self.pridat_testovaci_projekt)
        self.btn_new.pack(side="right")

        # --- ZOZNAM PROJEKTOV ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        self.refresh_projects()

    def refresh_projects(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        projekty = get_user_projects(self.user_id)

        if not projekty:
            lbl = ctk.CTkLabel(self.scroll_frame, text="Zatiaľ nemáte žiadne projekty.", text_color="gray")
            lbl.pack(pady=50)
            return

        for proj in projekty:
            self.create_project_card(proj)

    def create_project_card(self, project_data):
        pid, name, desc, status = project_data

        card = ctk.CTkFrame(self.scroll_frame, fg_color="#2B2B2B", corner_radius=10)
        card.pack(fill="x", pady=5, padx=5)

        # TLAČIDLO OTVORIŤ
        btn_open = ctk.CTkButton(card, text="Otvoriť", width=80,
                                 command=lambda p=project_data: self.open_project_detail(p))
        btn_open.pack(side="right", padx=20, pady=20)

        # Názov
        lbl_name = ctk.CTkLabel(card, text=name, font=("Arial", 16, "bold"))
        lbl_name.pack(anchor="w", padx=15, pady=(10, 0))

        # Popis
        desc_text = desc if desc else "Bez popisu"
        lbl_desc = ctk.CTkLabel(card, text=desc_text, text_color="gray70", font=("Arial", 12))
        lbl_desc.pack(anchor="w", padx=15, pady=(0, 10))

    def open_project_detail(self, project_data):
        """Prepne zobrazenie na detail projektu"""
        # 1. Skryjeme zoznam projektov (používame grid_forget, lebo v main.py sme použili grid)
        self.grid_forget()

        # 2. Vytvoríme a zobrazíme detail
        self.detail_view = ProjectDetailView(self.master, project_data, self.user_data,
                                             back_callback=self.show_list_again)
        self.detail_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_list_again(self):
        """Návrat z detailu späť na zoznam"""
        # 1. Zničíme detail view
        if hasattr(self, 'detail_view'):
            self.detail_view.destroy()

        # 2. Znova zobrazíme tento zoznam (musíme použiť rovnaké parametre ako v main.py)
        self.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Pre istotu refreshneme dáta, ak sa niečo zmenilo
        self.refresh_projects()

    def pridat_testovaci_projekt(self):
        create_test_project(self.user_id)
        self.refresh_projects()