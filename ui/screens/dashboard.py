import customtkinter as ctk
from logic.stats import get_dashboard_stats


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.user_id = user_data[0]
        self.user_name = user_data[3]

        # Načítame čerstvé dáta
        self.stats = get_dashboard_stats(self.user_id)

        # Nadpis
        self.lbl_title = ctk.CTkLabel(self, text=f"Vitaj späť, {self.user_name}!", font=("Arial", 28, "bold"))
        self.lbl_title.pack(pady=20, padx=20, anchor="w")

        # --- KARTY (Grid) ---
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(pady=10, padx=20, fill="x")

        # Karta 1: Projekty
        p_count = self.stats["projects_count"]
        self.create_stat_card("Aktívne Projekty", str(p_count), "#1976D2").pack(side="left", padx=10, expand=True,
                                                                                fill="x")

        # Karta 2: Úlohy
        t_count = self.stats["tasks_count"]
        self.create_stat_card("Moje Úlohy", str(t_count), "#388E3C").pack(side="left", padx=10, expand=True, fill="x")

        # Karta 3: Info
        self.create_stat_card("Systém", "Online", "#7B1FA2").pack(side="left", padx=10, expand=True, fill="x")

        # --- SEKCIA: NEDÁVNA AKTIVITA ---
        ctk.CTkLabel(self, text="Nedávna aktivita:", font=("Arial", 18, "bold")).pack(anchor="w", padx=30,
                                                                                      pady=(30, 10))

        self.activity_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=200)
        self.activity_frame.pack(fill="x", padx=20)

        self.show_activities()

    def create_stat_card(self, title, value, color):
        frame = ctk.CTkFrame(self.stats_frame, fg_color=color, corner_radius=10)

        lbl_val = ctk.CTkLabel(frame, text=value, font=("Arial", 30, "bold"), text_color="white")
        lbl_val.pack(pady=(15, 0))

        lbl_title = ctk.CTkLabel(frame, text=title, font=("Arial", 14), text_color="white")
        lbl_title.pack(pady=(0, 15))

        return frame

    def show_activities(self):
        logs = self.stats["recent_activity"]

        if not logs:
            ctk.CTkLabel(self.activity_frame, text="Žiadna nedávna aktivita.").pack(pady=20)
            return

        for log in logs:
            user_name, action, detail, time = log

            # Riadok logu
            row = ctk.CTkFrame(self.activity_frame, fg_color="#2B2B2B")
            row.pack(fill="x", pady=2)

            # Čas
            ctk.CTkLabel(row, text=time[:16], text_color="gray", width=120).pack(side="left", padx=10)

            # Text: "Jožo - Zmena statusu: In Progress"
            text = f"{user_name} • {action}: {detail}"
            ctk.CTkLabel(row, text=text, font=("Arial", 13)).pack(side="left", padx=10)