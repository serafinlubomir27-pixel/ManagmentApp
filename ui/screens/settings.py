import hashlib
import json
import os

import customtkinter as ctk

from repositories import user_repo
from ui.theme import PRIMARY, PRIMARY_HOVER, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.json")


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
        pass  # Non-critical: theme preference not saved, but app continues


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Page title
        ctk.CTkLabel(
            self,
            text="Nastavenia",
            font=("Arial", 26, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 12))

        # Section 1 – Profile
        self._build_profile_section(row=1)

        # Section 2 – Change password
        self._build_password_section(row=2)

        # Section 3 – Appearance
        self._build_appearance_section(row=3)

    # ------------------------------------------------------------------
    # Section 1: Profile
    # ------------------------------------------------------------------

    def _build_profile_section(self, row: int):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 14))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="👤 Profil",
            font=("Arial", 16, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        fields = [
            ("Celé meno", self.user.get("full_name", "")),
            ("Používateľské meno", self.user.get("username", "")),
            ("Rola", self.user.get("role", "")),
        ]
        for i, (label, value) in enumerate(fields, start=1):
            ctk.CTkLabel(
                card,
                text=label + ":",
                font=("Arial", 13),
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).grid(row=i, column=0, sticky="w", padx=(16, 8), pady=6)

            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 13),
                text_color=TEXT_PRIMARY,
                anchor="w",
            ).grid(row=i, column=1, sticky="w", padx=(0, 16), pady=6)

        # Bottom padding row
        ctk.CTkLabel(card, text="").grid(row=len(fields) + 1, column=0, pady=(0, 6))

    # ------------------------------------------------------------------
    # Section 2: Change password
    # ------------------------------------------------------------------

    def _build_password_section(self, row: int):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 14))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="🔒 Zmena hesla",
            font=("Arial", 16, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        pw_labels = ["Aktuálne heslo", "Nové heslo", "Potvrdiť heslo"]
        self._pw_entries = []
        for i, lbl in enumerate(pw_labels, start=1):
            ctk.CTkLabel(
                card,
                text=lbl + ":",
                font=("Arial", 13),
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).grid(row=i, column=0, sticky="w", padx=(16, 8), pady=6)

            entry = ctk.CTkEntry(card, show="*", width=260)
            entry.grid(row=i, column=1, sticky="w", padx=(0, 16), pady=6)
            self._pw_entries.append(entry)

        ctk.CTkButton(
            card,
            text="Uložiť heslo",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self._save_password,
        ).grid(row=len(pw_labels) + 1, column=0, columnspan=2, padx=16, pady=(8, 6), sticky="w")

        self._pw_msg = ctk.CTkLabel(card, text="", font=("Arial", 12), anchor="w")
        self._pw_msg.grid(row=len(pw_labels) + 2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

    def _save_password(self):
        old_pw = self._pw_entries[0].get()
        new_pw = self._pw_entries[1].get()
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
        # Keep in-memory user object in sync so re-validation works
        self.user["password"] = new_hashed

        for entry in self._pw_entries:
            entry.delete(0, "end")

        self._set_pw_msg("Heslo bolo úspešne zmenené.", error=False)

    def _set_pw_msg(self, text: str, error: bool):
        self._pw_msg.configure(
            text=text,
            text_color=("#D32F2F" if error else "#4CAF50"),
        )

    # ------------------------------------------------------------------
    # Section 3: Appearance
    # ------------------------------------------------------------------

    def _build_appearance_section(self, row: int):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 14))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="🎨 Vzhľad",
            font=("Arial", 16, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            card,
            text="Tmavý režim",
            font=("Arial", 13),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(16, 8), pady=10)

        # Determine current setting from config
        current_theme = _load_config().get("theme", "dark")
        self._theme_switch_var = ctk.StringVar(value="on" if current_theme == "dark" else "off")

        switch = ctk.CTkSwitch(
            card,
            text="",
            variable=self._theme_switch_var,
            onvalue="on",
            offvalue="off",
            command=self._toggle_theme,
        )
        switch.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=10)

        # Bottom padding
        ctk.CTkLabel(card, text="").grid(row=2, column=0, pady=(0, 6))

    def _toggle_theme(self):
        is_dark = self._theme_switch_var.get() == "on"
        mode = "dark" if is_dark else "light"
        ctk.set_appearance_mode(mode)
        cfg = _load_config()
        cfg["theme"] = mode
        _save_config(cfg)
