import customtkinter as ctk
from ui.screens.team_view import TeamView
from ui.screens.project_view import ProjectsView
from database.setup import create_database
from ui.screens.login_screen import LoginScreen
from ui.screens.dashboard import DashboardScreen  # <-- Importujeme nový Dashboard
from ui.components.sidebar import Sidebar  # <-- Importujeme Sidebar


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Management System v1.0")
        self.geometry("1100x700")  # Zväčšíme okno
        ctk.set_appearance_mode("Dark")

        self.current_user = None
        self.show_login()

    def show_login(self):
        # Vyčistiť všetko
        for widget in self.winfo_children():
            widget.destroy()
        LoginScreen(self, on_login_success=self.on_login)

    def on_login(self, user_data):
        self.current_user = user_data
        self.show_main_layout()

    def show_main_layout(self):
        # Vyčistiť login
        for widget in self.winfo_children():
            widget.destroy()

        # 1. Konfigurácia Gridu (Mriežky)
        # Stĺpec 0 = Sidebar (úzky), Stĺpec 1 = Obsah (široký)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 2. Vytvorenie Sidebaru (Vľavo)
        self.sidebar = Sidebar(self, callback_funkcia=self.handle_navigation)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 3. Vytvorenie Hlavného obsahu (Vpravo)
        # Na začiatku tam vložíme Dashboard
        self.content_area = DashboardScreen(self, self.current_user)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def handle_navigation(self, kam_ist):
        if kam_ist == "logout":
            self.current_user = None
            self.show_login()
            return

        # Zničíme starý obsah
        if self.content_area:
            self.content_area.destroy()

        # --- TU JE ZMENA ---
        if kam_ist == "dashboard":
            self.content_area = DashboardScreen(self, self.current_user)

        elif kam_ist == "projects":
            # Už nie Label, ale naša nová trieda ProjectsView
            self.content_area = ProjectsView(self, self.current_user)

        elif kam_ist == "team":
            self.content_area = TeamView(self, self.current_user)

        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)


def main():
    create_database()
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    main()