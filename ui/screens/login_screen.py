import customtkinter as ctk
from logic.auth import login_user


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success

        # --- Dizajn okna ---
        # Vycentrujeme rámček do stredu
        self.place(relx=0.5, rely=0.5, anchor="center")

        # Nadpis
        self.label = ctk.CTkLabel(self, text="Prihlásenie", font=("Arial", 24, "bold"))
        self.label.pack(pady=20, padx=50)

        # Vstup pre Meno
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Užívateľské meno", width=200)
        self.username_entry.pack(pady=10)

        # Vstup pre Heslo (show="*" skryje znaky)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Heslo", show="*", width=200)
        self.password_entry.pack(pady=10)

        # Tlačidlo Prihlásiť
        self.login_btn = ctk.CTkButton(self, text="Prihlásiť sa", command=self.handle_login)
        self.login_btn.pack(pady=20)

        # Chybová hláška (zatiaľ prázdna)
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=5)

    def handle_login(self):
        # 1. Získame údaje z políčok
        user_val = self.username_entry.get()
        pass_val = self.password_entry.get()

        # 2. Zavoláme našu logiku z auth.py
        user_data = login_user(user_val, pass_val)

        if user_data:
            # Ak sú údaje správne, spustíme funkciu "úspech" (prepnutie do appky)
            self.error_label.configure(text="Úspech! Načítavam...", text_color="green")
            # user_data obsahuje (id, username, pass, full_name, role...)
            # My pošleme ďalej celý objekt užívateľa
            self.on_login_success(user_data)
        else:
            self.error_label.configure(text="Nesprávne meno alebo heslo!", text_color="red")