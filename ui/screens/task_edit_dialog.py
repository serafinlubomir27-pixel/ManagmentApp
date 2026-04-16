import customtkinter as ctk
from logic.task_manager import update_task_status, add_comment, get_task_comments
from ui.theme import (
    PRIMARY, PRIMARY_HOVER, DANGER,
    BG_CARD, BG_ROW, BG_INPUT, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    get_font,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD,
    RADIUS_SM, RADIUS_MD,
    HEIGHT_BTN_SM, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG,
)


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
        self.configure(fg_color=BG_CARD)

        # --- ZMENA STATUSU ---
        frame_status = ctk.CTkFrame(
            self, fg_color=BG_ROW, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        frame_status.pack(fill="x", padx=SPACE_LG, pady=SPACE_LG)

        ctk.CTkLabel(
            frame_status, text="Aktuálny stav:",
            font=get_font(FONT_SIZE_BASE, "bold"), text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=SPACE_MD)

        self.status_var = ctk.StringVar(value=self.task_status)
        self.combo_status = ctk.CTkComboBox(
            frame_status,
            values=["pending", "in_progress", "completed", "blocked"],
            variable=self.status_var,
            command=self.save_status,
            fg_color=BG_INPUT, border_color=BORDER,
            button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
            text_color=TEXT_PRIMARY, font=get_font(FONT_SIZE_BASE),
        )
        self.combo_status.pack(side="right", padx=SPACE_MD, pady=SPACE_MD)

        # --- CHAT / KOMENTÁRE ---
        ctk.CTkLabel(
            self, text="Poznámky a Diskusia:",
            font=get_font(FONT_SIZE_BASE, "bold"), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=SPACE_LG)

        self.chat_frame = ctk.CTkScrollableFrame(
            self, height=300, fg_color=BG_ROW, corner_radius=RADIUS_SM,
        )
        self.chat_frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_MD)

        # Vstup pre novú správu
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=SPACE_LG, pady=SPACE_LG)

        self.entry_comment = ctk.CTkEntry(
            input_frame, placeholder_text="Napíš poznámku...",
            fg_color=BG_INPUT, border_color=BORDER,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
        )
        self.entry_comment.pack(side="left", fill="x", expand=True, padx=(0, SPACE_SM))

        btn_send = ctk.CTkButton(
            input_frame, text="Odoslať", width=80, height=HEIGHT_BTN_SM,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            font=get_font(FONT_SIZE_BASE), corner_radius=RADIUS_SM,
            command=self.send_comment,
        )
        btn_send.pack(side="right")

        self.load_comments()

    def save_status(self, new_val):
        update_task_status(self.task_id, new_val, self.user_id)

    def load_comments(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()

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
        bubble = ctk.CTkFrame(
            self.chat_frame, fg_color=BG_CARD,
            corner_radius=RADIUS_SM, border_width=1, border_color=BORDER,
        )
        bubble.pack(fill="x", pady=4, padx=4)

        header = ctk.CTkLabel(
            bubble, text=f"{author} ({str(time)[:16]})",
            font=get_font(FONT_SIZE_XS), text_color=TEXT_SECONDARY,
        )
        header.pack(anchor="w", padx=SPACE_SM, pady=(SPACE_SM, 0))

        body = ctk.CTkLabel(
            bubble, text=msg,
            font=get_font(FONT_SIZE_BASE), text_color=TEXT_PRIMARY,
            wraplength=400, justify="left",
        )
        body.pack(anchor="w", padx=SPACE_SM, pady=(0, SPACE_SM))

    def send_comment(self):
        text = self.entry_comment.get()
        if text:
            add_comment(self.task_id, self.user_id, text)
            self.entry_comment.delete(0, "end")
            self.load_comments()

    def destroy(self):
        self.on_close()
        super().destroy()
