"""
Sidebar — navigačný panel aplikácie.
Moderný SaaS štýl: brand mark, muted active state, ghost logout.
"""
import customtkinter as ctk
from ui.theme import (
    PRIMARY, PRIMARY_HOVER, PRIMARY_MUTED,
    DANGER, DANGER_MUTED,
    BG_SIDEBAR, BG_ROW, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    get_font,
    FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL,
    RADIUS_SM, HEIGHT_BTN_MD, HEIGHT_BTN_SM,
)

# Nav položky: (ikona, label, kľúč)
_NAV_ITEMS = [
    ("📊", "Prehľad",   "dashboard"),
    ("📁", "Projekty",  "projects"),
    ("👥", "Môj Tím",   "team"),
    ("📅", "Kalendár",  "calendar"),
    ("⚙️", "Nastavenia","settings"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, callback_funkcia):
        super().__init__(
            parent,
            width=220,
            corner_radius=0,
            fg_color=BG_SIDEBAR,
            border_width=0,
        )
        self.callback = callback_funkcia
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self._build()

    # ── Builder ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Brand mark ──────────────────────────────────────────────────────
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(pady=(SPACE_2XL, SPACE_LG), padx=SPACE_LG, fill="x")

        # Farebná bodka (brand accent)
        dot = ctk.CTkFrame(
            brand_frame,
            width=12, height=12,
            fg_color=PRIMARY,
            corner_radius=6,
        )
        dot.pack(side="left", padx=(0, SPACE_SM))
        dot.pack_propagate(False)

        ctk.CTkLabel(
            brand_frame,
            text="ManagmentApp",
            font=get_font(FONT_SIZE_MD, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        # ── Separator ───────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=SPACE_LG, pady=(0, SPACE_SM)
        )

        # ── Nav tlačidlá ────────────────────────────────────────────────────
        for icon, label, key in _NAV_ITEMS:
            self._make_nav_btn(icon, label, key)

        # ── Spacer ──────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="").pack(expand=True)

        # ── Separator pred logout ────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(
            fill="x", padx=SPACE_LG, pady=(0, SPACE_SM)
        )

        # ── Logout — ghost danger štýl ───────────────────────────────────────
        self.btn_logout = ctk.CTkButton(
            self,
            text="  ↩  Odhlásiť sa",
            fg_color="transparent",
            text_color=DANGER,
            hover_color=DANGER_MUTED,
            border_width=1,
            border_color=BORDER,
            anchor="w",
            height=HEIGHT_BTN_SM,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=lambda: self.callback("logout"),
        )
        self.btn_logout.pack(pady=(0, SPACE_XL), padx=SPACE_LG, fill="x")

    # ── Nav tlačidlo factory ────────────────────────────────────────────────

    def _make_nav_btn(self, icon: str, label: str, key: str) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            self,
            text=f"  {icon}  {label}",
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            hover_color=BG_ROW,
            anchor="w",
            height=HEIGHT_BTN_MD,
            corner_radius=RADIUS_SM,
            font=get_font(FONT_SIZE_BASE),
            command=lambda k=key: self.callback(k),
        )
        btn.pack(pady=2, padx=SPACE_LG, fill="x")
        self._nav_buttons[key] = btn
        return btn

    # ── Aktívny stav ────────────────────────────────────────────────────────

    def set_active(self, key: str):
        """Zvýrazní aktívne nav tlačidlo, ostatné vráti do neaktívneho stavu."""
        for btn_key, btn in self._nav_buttons.items():
            if btn_key == key:
                btn.configure(
                    fg_color=PRIMARY_MUTED,       # jemný tint — nie solid fill
                    text_color=PRIMARY,
                    font=get_font(FONT_SIZE_BASE, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    font=get_font(FONT_SIZE_BASE),
                )
