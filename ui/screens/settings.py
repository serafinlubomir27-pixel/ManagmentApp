"""
Settings Screen — profil, zmena hesla, vzhľad.
Dual-mode: karty s border, Segoe UI font, BG_INPUT polia.
"""
import hashlib
import json
import os

import customtkinter as ctk

from repositories import user_repo
from ui.theme import (
    PRIMARY, PRIMARY_HOVER,
    DANGER, SUCCESS,
    BG_CARD, BG_INPUT, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    get_font,
    FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_2XL,
    RADIUS_SM, RADIUS_MD,
    HEIGHT_BTN_MD, HEIGHT_INPUT,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
)

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.json"
)


def _load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_config(data: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Nadpis stránky (fixný — mimo scrollu)
        ctk.CTkLabel(
            self,
            text="Nastavenia",
            font=get_font(FONT_SIZE_2XL, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=SPACE_XL, pady=(SPACE_LG, SPACE_MD))

        # Scrollovateľná plocha pre sekcie
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._build_profile_section(scroll, row=0)
        self._build_password_section(scroll, row=1)
        self._build_appearance_section(scroll, row=2)

    # ── Sekcia 1: Profil ───────────────────────────────────────────────────

    def _build_profile_section(self, parent, row: int):
        card = ctk.CTkFrame(
            parent, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_MD))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Profil",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=SPACE_LG, pady=(SPACE_LG, SPACE_MD))

        fields = [
            ("Celé meno",          self.user.get("full_name", "")),
            ("Používateľské meno", self.user.get("username", "")),
            ("Rola",               self.user.get("role", "")),
        ]
        for i, (label, value) in enumerate(fields, start=1):
            ctk.CTkLabel(
                card, text=label + ":",
                font=get_font(FONT_SIZE_BASE),
                text_color=TEXT_SECONDARY, anchor="w",
            ).grid(row=i, column=0, sticky="w", padx=(SPACE_LG, SPACE_SM), pady=SPACE_SM)

            ctk.CTkLabel(
                card, text=value,
                font=get_font(FONT_SIZE_BASE, "bold"),
                text_color=TEXT_PRIMARY, anchor="w",
            ).grid(row=i, column=1, sticky="w", padx=(0, SPACE_LG), pady=SPACE_SM)

        ctk.CTkLabel(card, text="").grid(row=len(fields) + 1, column=0, pady=(0, SPACE_SM))

    # ── Sekcia 2: Zmena hesla ──────────────────────────────────────────────

    def _build_password_section(self, parent, row: int):
        card = ctk.CTkFrame(
            parent, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_MD))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Zmena hesla",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=SPACE_LG, pady=(SPACE_LG, SPACE_MD))

        pw_labels = ["Aktuálne heslo", "Nové heslo", "Potvrdiť heslo"]
        self._pw_entries: list[ctk.CTkEntry] = []
        for i, lbl in enumerate(pw_labels, start=1):
            ctk.CTkLabel(
                card, text=lbl + ":",
                font=get_font(FONT_SIZE_BASE),
                text_color=TEXT_SECONDARY, anchor="w",
            ).grid(row=i, column=0, sticky="w", padx=(SPACE_LG, SPACE_SM), pady=SPACE_SM)

            entry = ctk.CTkEntry(
                card,
                show="*",
                width=280,
                height=HEIGHT_INPUT,
                corner_radius=RADIUS_SM,
                font=get_font(FONT_SIZE_BASE),
                fg_color=BG_INPUT,
                border_color=BORDER,
            )
            entry.grid(row=i, column=1, sticky="w", padx=(0, SPACE_LG), pady=SPACE_SM)
            self._pw_entries.append(entry)

        n = len(pw_labels)
        ctk.CTkButton(
            card,
            text="Uložiť heslo",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            height=HEIGHT_BTN_MD,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE, "bold"),
            command=self._save_password,
        ).grid(row=n + 1, column=0, columnspan=2, padx=SPACE_LG, pady=(SPACE_SM, SPACE_SM), sticky="w")

        self._pw_msg = ctk.CTkLabel(
            card, text="",
            font=get_font(FONT_SIZE_BASE), anchor="w",
        )
        self._pw_msg.grid(row=n + 2, column=0, columnspan=2, sticky="w", padx=SPACE_LG, pady=(0, SPACE_MD))

    def _save_password(self):
        old_pw     = self._pw_entries[0].get()
        new_pw     = self._pw_entries[1].get()
        confirm_pw = self._pw_entries[2].get()

        if not old_pw or not new_pw or not confirm_pw:
            self._set_pw_msg("Vyplňte všetky polia.", error=True)
            return
        old_hashed = hashlib.sha256(old_pw.encode()).hexdigest()
        if old_hashed != self.user.get("password", ""):
            self._set_pw_msg("Aktuálne heslo je nesprávne.", error=True)
            return
        if new_pw == old_pw:
            self._set_pw_msg("Nové heslo musí byť iné ako aktuálne.", error=True)
            return
        if len(new_pw) < 6:
            self._set_pw_msg("Nové heslo musí mať aspoň 6 znakov.", error=True)
            return
        if new_pw != confirm_pw:
            self._set_pw_msg("Nové heslá sa nezhodujú.", error=True)
            return

        new_hashed = hashlib.sha256(new_pw.encode()).hexdigest()
        user_repo.update_password(self.user["id"], new_hashed)
        self.user["password"] = new_hashed
        for entry in self._pw_entries:
            entry.delete(0, "end")
        self._set_pw_msg("Heslo bolo úspešne zmenené.", error=False)

    def _set_pw_msg(self, text: str, error: bool):
        self._pw_msg.configure(
            text=text,
            text_color=DANGER if error else SUCCESS,
        )

    # ── Sekcia 3: Vzhľad ───────────────────────────────────────────────────

    def _build_appearance_section(self, parent, row: int):
        card = ctk.CTkFrame(
            parent, fg_color=BG_CARD, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=SPACE_XL, pady=(0, SPACE_MD))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Vzhľad",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=SPACE_LG, pady=(SPACE_LG, SPACE_MD))

        ctk.CTkLabel(
            card, text="Tmavý / Svetlý režim",
            font=get_font(FONT_SIZE_BASE),
            text_color=TEXT_SECONDARY, anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(SPACE_LG, SPACE_SM), pady=SPACE_MD)

        current_theme = _load_config().get("theme", "dark")
        self._theme_switch_var = ctk.StringVar(value="on" if current_theme == "dark" else "off")

        ctk.CTkSwitch(
            card,
            text="",
            variable=self._theme_switch_var,
            onvalue="on",
            offvalue="off",
            progress_color=PRIMARY,
            command=self._toggle_theme,
        ).grid(row=1, column=1, sticky="w", padx=(0, SPACE_LG), pady=SPACE_MD)

        ctk.CTkLabel(card, text="").grid(row=2, column=0, pady=(0, SPACE_SM))

    def _toggle_theme(self):
        is_dark = self._theme_switch_var.get() == "on"
        mode = "dark" if is_dark else "light"
        ctk.set_appearance_mode(mode)
        cfg = _load_config()
        cfg["theme"] = mode
        _save_config(cfg)
