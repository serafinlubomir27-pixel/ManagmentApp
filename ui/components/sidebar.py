import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, callback_funkcia):
        super().__init__(parent, width=200, corner_radius=0)
        self.callback = callback_funkcia # Funkcia, ktorá prepína obrazovky

        # Farba pozadia (trochu tmavšia ako zvyšok)
        self.configure(fg_color="#2B2B2B")

        # --- Logo / Názov ---
        self.logo_label = ctk.CTkLabel(self, text="MANAŽÉR APP", font=("Arial", 20, "bold"))
        self.logo_label.pack(pady=30, padx=20)

        # --- Tlačidlá Menu ---
        self.btn_dashboard = self.create_menu_btn("📊 Prehľad", "dashboard")
        self.btn_projects = self.create_menu_btn("📁 Projekty", "projects")
        self.btn_team = self.create_menu_btn("👥 Môj Tím", "team")
        self.btn_settings = self.create_menu_btn("⚙️ Nastavenia", "settings")

        # --- Medzera a Odhlásenie ---
        # Spacer vytlačí odhlasovanie dolu
        self.spacer = ctk.CTkLabel(self, text="")
        self.spacer.pack(expand=True)

        self.btn_logout = ctk.CTkButton(self, text="Odhlásiť sa",
                                        fg_color="#D32F2F", hover_color="#B71C1C",
                                        command=lambda: self.callback("logout"))
        self.btn_logout.pack(pady=20, padx=20, side="bottom")

    def create_menu_btn(self, text, hodnota):
        """Pomocná funkcia na výrobu pekných tlačidiel"""
        btn = ctk.CTkButton(self, text=text,
                            fg_color="transparent",
                            text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30"),
                            anchor="w", # Zarovnanie textu doľava
                            command=lambda: self.callback(hodnota))
        btn.pack(pady=5, padx=10, fill="x")
        return btn