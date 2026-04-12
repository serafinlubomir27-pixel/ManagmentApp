import customtkinter as ctk
from logic.task_manager import update_task_status, add_comment, get_task_comments


class TaskEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, task_data, user_id, on_close_callback):
        super().__init__(parent)
        if isinstance(task_data, dict):
            self.task_id = task_data.get("id")
            self.task_name = task_data.get("name", "")
            self.task_status = task_data.get("status", "pending")
        else:
            self.task_id, self.task_name, self.task_status, _, _ = task_data
        self.user_id = user_id
        self.on_close = on_close_callback

        self.title(f"Detail úlohy: {self.task_name}")
        self.geometry("500x600")

        # --- ZMENA STATUSU ---
        frame_status = ctk.CTkFrame(self)
        frame_status.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(frame_status, text="Aktuálny stav:", font=("Arial", 14, "bold")).pack(side="left", padx=10)

        self.status_var = ctk.StringVar(value=self.task_status)
        self.combo_status = ctk.CTkComboBox(frame_status, values=["pending", "in_progress", "completed", "blocked"],
                                            variable=self.status_var, command=self.save_status)
        self.combo_status.pack(side="right", padx=10, pady=10)

        # --- CHAT / KOMENTÁRE ---
        ctk.CTkLabel(self, text="Poznámky a Diskusia:", font=("Arial", 14, "bold")).pack(anchor="w", padx=20)

        self.chat_frame = ctk.CTkScrollableFrame(self, height=300, fg_color="#212121")
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Vstup pre novú správu
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=20)

        self.entry_comment = ctk.CTkEntry(input_frame, placeholder_text="Napíš poznámku...")
        self.entry_comment.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_send = ctk.CTkButton(input_frame, text="Odoslať", width=80, command=self.send_comment)
        btn_send.pack(side="right")

        self.load_comments()

    def save_status(self, new_val):
        # Automaticky uloží zmenu statusu, keď vyberieš inú možnosť
        update_task_status(self.task_id, new_val, self.user_id)
        # (Voliteľné: Tu by sme mohli zavrieť okno alebo zobraziť fajku)

    def load_comments(self):
        # Vyčistíme chat
        for w in self.chat_frame.winfo_children(): w.destroy()

        comments = get_task_comments(self.task_id)
        for c in comments:
            if isinstance(c, dict):
                msg = c.get("content", "")
                time = c.get("created_at", "")
                author = c.get("username", "")
            else:
                msg, time, author = c
            self.create_chat_bubble(author, msg, time)

    def create_chat_bubble(self, author, msg, time):
        # Bublina správy
        bubble = ctk.CTkFrame(self.chat_frame, fg_color="#3E3E3E")
        bubble.pack(fill="x", pady=5, padx=5)

        header = ctk.CTkLabel(bubble, text=f"{author} ({time[:16]})", font=("Arial", 10), text_color="gray")
        header.pack(anchor="w", padx=10, pady=(5, 0))

        body = ctk.CTkLabel(bubble, text=msg, font=("Arial", 12), wraplength=400, justify="left")
        body.pack(anchor="w", padx=10, pady=(0, 5))

    def send_comment(self):
        text = self.entry_comment.get()
        if text:
            add_comment(self.task_id, self.user_id, text)
            self.entry_comment.delete(0, "end")
            self.load_comments()  # Obnoviť chat

    def destroy(self):
        # Keď zavrieme okno, povieme rodičovi (ProjectDetail), nech sa obnoví
        self.on_close()
        super().destroy()