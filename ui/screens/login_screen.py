"""
Login Screen — centrovaná prihlasovacia karta.
Moderný dizajn: brand mark, čistá typografia, dual-mode.
"""
import customtkinter as ctk
from logic.auth import login_user
from ui.theme import (
    PRIMARY, PRIMARY_HOVER,
    DANGER, SUCCESS,
    BG_MAIN, BG_CARD, BG_INPUT, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    get_font,
    FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL,
    RADIUS_SM, RADIUS_LG,
    HEIGHT_BTN_LG, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_3XL,
)


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color=BG_MAIN)
        self.on_login_success = on_login_success
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Centrovacia mriežka
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # ── Karta ──────────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=BORDER,
            width=400,
            height=500,
        )
        card.grid(row=1, column=1, padx=SPACE_XL, pady=SPACE_XL)
        card.grid_propagate(False)

        # ── Brand mark ─────────────────────────────────────────────────────
        brand_frame = ctk.CTkFrame(card, fg_color="transparent")
        brand_frame.pack(pady=(SPACE_3XL, 0))

        dot = ctk.CTkFrame(
            brand_frame,
            width=14, height=14,
            fg_color=PRIMARY,
            corner_radius=7,
        )
        dot.pack(side="left", padx=(0, SPACE_SM))
        dot.pack_propagate(False)

        ctk.CTkLabel(
            brand_frame,
            text="ManagmentApp",
            font=get_font(FONT_SIZE_XL, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        # ── Podtitulok ─────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="Prihlás sa do svojho konta",
            font=get_font(FONT_SIZE_BASE),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(SPACE_SM, SPACE_XL))

        # ── Username entry ─────────────────────────────────────────────────
        self.username_entry = ctk.CTkEntry(
            card,
            placeholder_text="Užívateľské meno",
            width=320,
            height=HEIGHT_INPUT,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            fg_color=BG_INPUT,
            border_color=BORDER,
        )
        self.username_entry.pack(pady=(0, SPACE_MD))

        # ── Password entry ─────────────────────────────────────────────────
        self.password_entry = ctk.CTkEntry(
            card,
            placeholder_text="Heslo",
            show="*",
            width=320,
            height=HEIGHT_INPUT,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            fg_color=BG_INPUT,
            border_color=BORDER,
        )
        self.password_entry.pack(pady=(0, SPACE_XL))

        # ── Login button ───────────────────────────────────────────────────
        self.login_btn = ctk.CTkButton(
            card,
            text="Prihlásiť sa",
            command=self.handle_login,
            width=320,
            height=HEIGHT_BTN_LG,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_MD, "bold"),
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
        )
        self.login_btn.pack(pady=(0, SPACE_MD))

        # ── Stavová hláška ─────────────────────────────────────────────────
        self.msg_label = ctk.CTkLabel(
            card,
            text="",
            font=get_font(FONT_SIZE_BASE),
            text_color=DANGER,
            wraplength=300,
        )
        self.msg_label.pack(pady=(0, SPACE_XL))

        # ── Key bindings ───────────────────────────────────────────────────
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.handle_login())
        self.after(100, self.username_entry.focus)

    # ── Handlers ───────────────────────────────────────────────────────────────

    def handle_login(self):
        user_val = self.username_entry.get().strip()
        pass_val = self.password_entry.get()

        if not user_val or not pass_val:
            self.msg_label.configure(
                text="Vyplň užívateľské meno aj heslo.",
                text_color=DANGER,
            )
            return

        self.login_btn.configure(state="disabled", text="Prihlasujem...")
        self.after(50, lambda: self._do_login(user_val, pass_val))

    def _do_login(self, user_val, pass_val):
        user_data = login_user(user_val, pass_val)

        if user_data:
            self.msg_label.configure(
                text="Úspech! Načítavam...",
                text_color=SUCCESS,
            )
            self.after(200, lambda: self.on_login_success(user_data))
        else:
            self.msg_label.configure(
                text="Nesprávne meno alebo heslo.",
                text_color=DANGER,
            )
            self.login_btn.configure(state="normal", text="Prihlásiť sa")
            self.password_entry.delete(0, "end")
            self.password_entry.focus()
