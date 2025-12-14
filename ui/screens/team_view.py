import customtkinter as ctk
from logic.hierarchy import get_my_team, add_new_member


class TeamView(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_data[0]  # Moje ID
        self.user_role = user_data[4]  # Moja rola

        # --- HLAVIČKA ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 20))

        self.title = ctk.CTkLabel(self.header, text="Môj Tím", font=("Arial", 24, "bold"))
        self.title.pack(side="left")

        # Tlačidlo Pridať člena (Vidí ho len Admin alebo Manager)
        if self.user_role in ["admin", "manager"]:
            self.btn_add = ctk.CTkButton(self.header, text="+ Pridať člena",
                                         fg_color="#0288D1", hover_color="#01579B",
                                         command=self.open_add_dialog)
            self.btn_add.pack(side="right")

        # --- ZOZNAM ĽUDÍ ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        self.refresh_team()

    def refresh_team(self):
        # Vyčistiť
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Načítať dáta
        members = get_my_team(self.user_id)

        if not members:
            lbl = ctk.CTkLabel(self.scroll_frame, text="Zatiaľ nemáte v tíme nikoho.", text_color="gray")
            lbl.pack(pady=50)
            return

        # Vykresliť karty
        for m in members:
            self.create_member_card(m)

    def create_member_card(self, member_data):
        mid, name, role, username = member_data

        card = ctk.CTkFrame(self.scroll_frame, fg_color="#2B2B2B", corner_radius=10)
        card.pack(fill="x", pady=5, padx=5)

        # Ikona / Avatar (len text)
        lbl_icon = ctk.CTkLabel(card, text="👤", font=("Arial", 24))
        lbl_icon.pack(side="left", padx=15, pady=10)

        # Meno a Rola
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both")

        lbl_name = ctk.CTkLabel(info_frame, text=name, font=("Arial", 16, "bold"))
        lbl_name.pack(anchor="w")

        lbl_role = ctk.CTkLabel(info_frame, text=f"{role.upper()} (@{username})", text_color="gray70",
                                font=("Arial", 12))
        lbl_role.pack(anchor="w")

    def open_add_dialog(self):
        # Jednoduché vyskakovacie okno na pridanie zamestnanca
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pridať nového člena")
        dialog.geometry("300x350")

        ctk.CTkLabel(dialog, text="Meno a Priezvisko:").pack(pady=5)
        entry_name = ctk.CTkEntry(dialog)
        entry_name.pack(pady=5)

        ctk.CTkLabel(dialog, text="Username (Login):").pack(pady=5)
        entry_user = ctk.CTkEntry(dialog)
        entry_user.pack(pady=5)

        ctk.CTkLabel(dialog, text="Heslo:").pack(pady=5)
        entry_pass = ctk.CTkEntry(dialog)
        entry_pass.pack(pady=5)

        def save():
            name = entry_name.get()
            username = entry_user.get()
            password = entry_pass.get()

            if name and username and password:
                success, msg = add_new_member(self.user_id, name, username, password)
                if success:
                    dialog.destroy()
                    self.refresh_team()  # Obnoviť zoznam
                else:
                    lbl_err.configure(text=msg)
            else:
                lbl_err.configure(text="Vyplňte všetky polia!")

        ctk.CTkButton(dialog, text="Uložiť", command=save).pack(pady=20)
        lbl_err = ctk.CTkLabel(dialog, text="", text_color="red")
        lbl_err.pack()