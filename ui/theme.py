"""
ManagmentApp Design System — v2.0
Duálne color tokeny (light, dark), font factory, spacing, border radius.
Inšpirované Lovable/PathFlow a 21.dev estetikou.

Použitie:
    fg_color=BG_CARD              → CTk automaticky vyberie light/dark variant
    font=get_font(FONT_SIZE_BASE) → Segoe UI, cached
"""
from __future__ import annotations
import customtkinter as ctk

# ══════════════════════════════════════════════════════════════════════════════
# POZADIA  (light, dark)
# ══════════════════════════════════════════════════════════════════════════════
BG_MAIN    = ("#F5F7FF", "#0A0E1A")   # stránka / okno
BG_SIDEBAR = ("#ECEEF8", "#080C17")   # sidebar panel
BG_CARD    = ("#FFFFFF", "#101629")   # karty, dialógy, elevované plochy
BG_ROW     = ("#F0F2FB", "#1A2040")   # list riadky, jemné plochy
BG_INPUT   = ("#FFFFFF", "#141930")   # vstupné polia, entry

# ══════════════════════════════════════════════════════════════════════════════
# OHRANIČENIA
# ══════════════════════════════════════════════════════════════════════════════
BORDER        = ("#E8E8ED", "#1E263A")   # default border kariet
BORDER_STRONG = ("#C8CCE0", "#2A3555")   # zvýraznený border (focus, hover)

# ══════════════════════════════════════════════════════════════════════════════
# BRAND FARBY  (light, dark)
# ══════════════════════════════════════════════════════════════════════════════
PRIMARY       = ("#4B7FFF", "#5A8FFF")
PRIMARY_HOVER = ("#3A6AE8", "#4B78F0")
PRIMARY_MUTED = ("#D6E4FF", "#0D1F4A")   # badge bg, active nav tint

ACCENT       = ("#1FBDA6", "#20CFC8")
ACCENT_HOVER = ("#18A890", "#18B8B0")
ACCENT_MUTED = ("#D0F5F0", "#0A2E2C")

# ══════════════════════════════════════════════════════════════════════════════
# SEMANTICKÉ FARBY
# ══════════════════════════════════════════════════════════════════════════════
SUCCESS       = ("#1DB86D", "#1DB86D")
SUCCESS_MUTED = ("#D4F5E5", "#0A2E1D")

DANGER        = ("#E53935", "#EF5350")
DANGER_HOVER  = ("#C62828", "#E53935")
DANGER_MUTED  = ("#FDECEA", "#2D0E0E")

WARNING       = ("#FFB700", "#FFB700")
WARNING_MUTED = ("#FFF8E1", "#2E2200")

# ══════════════════════════════════════════════════════════════════════════════
# TEXT
# ══════════════════════════════════════════════════════════════════════════════
TEXT_PRIMARY   = ("#1A2035", "#FFFFFF")
TEXT_SECONDARY = ("#64748B", "#8899BB")
TEXT_DISABLED  = ("#A0ABBE", "#3D4F6E")
TEXT_ON_PRIMARY = ("#FFFFFF", "#FFFFFF")   # text na PRIMARY ploche

# ══════════════════════════════════════════════════════════════════════════════
# GRADIENT TOKENY  pre stat karty
# Format: ((light_start, light_end), (dark_start, dark_end))
# ══════════════════════════════════════════════════════════════════════════════
GRAD_BLUE = (("#EBF0FF", "#E0EAFF"), ("#132054", "#0D1640"))
GRAD_TEAL = (("#E0FAF6", "#C5F5EE"), ("#0A2E35", "#071C22"))
GRAD_RED  = (("#FDECEA", "#FAD7D5"), ("#3A0E0E", "#220808"))

# ══════════════════════════════════════════════════════════════════════════════
# ZDIEĽANÉ STATUSOVÉ A ROLOVÉ FARBY  (odstránené z individuálnych screensov)
# ══════════════════════════════════════════════════════════════════════════════
STATUS_COLORS: dict[str, tuple[str, str]] = {
    "pending":     ("#9E9E9E", "#9E9E9E"),
    "in_progress": ("#1FBDA6", "#20CFC8"),
    "completed":   ("#1DB86D", "#1DB86D"),
    "blocked":     ("#E53935", "#EF5350"),
}

STATUS_LABELS_SK: dict[str, str] = {
    "pending":     "Čaká",
    "in_progress": "Prebieha",
    "completed":   "Hotová",
    "blocked":     "Blokovaná",
}

ROLE_COLORS: dict[str, tuple[str, str]] = {
    "admin":    ("#E53935", "#EF5350"),
    "manager":  ("#4B7FFF", "#5A8FFF"),
    "employee": ("#1FBDA6", "#20CFC8"),
}

PROJECT_STATUS_COLORS: dict[str, tuple[str, str]] = {
    "active":    ("#4B7FFF", "#5A8FFF"),
    "completed": ("#1DB86D", "#1DB86D"),
    "archived":  ("#64748B", "#8899BB"),
}

PROJECT_STATUS_LABELS: dict[str, str] = {
    "active":    "Aktívny",
    "completed": "Dokončený",
    "archived":  "Archivovaný",
}

# ══════════════════════════════════════════════════════════════════════════════
# TYPOGRAFIA
# ══════════════════════════════════════════════════════════════════════════════
FONT_FAMILY      = "Segoe UI"        # Windows — blízke DM Sans
FONT_FAMILY_MONO = "Consolas"        # pre CPM hodnoty, kód

FONT_SIZE_XS   = 9
FONT_SIZE_SM   = 11
FONT_SIZE_BASE = 13
FONT_SIZE_MD   = 15
FONT_SIZE_LG   = 18
FONT_SIZE_XL   = 22
FONT_SIZE_2XL  = 26
FONT_SIZE_3XL  = 32

_font_cache: dict[tuple, ctk.CTkFont] = {}


def get_font(size: int = FONT_SIZE_BASE, weight: str = "normal") -> ctk.CTkFont:
    """Vráti cached CTkFont objekt. Volaj až po ctk.CTk() init."""
    key = (size, weight, FONT_FAMILY)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)
    return _font_cache[key]


def get_mono_font(size: int = FONT_SIZE_SM) -> ctk.CTkFont:
    """Monospace font pre CPM hodnoty."""
    key = (size, "normal", FONT_FAMILY_MONO)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=FONT_FAMILY_MONO, size=size)
    return _font_cache[key]


# ══════════════════════════════════════════════════════════════════════════════
# SPACING & SIZING
# ══════════════════════════════════════════════════════════════════════════════
SPACE_XS  = 4
SPACE_SM  = 8
SPACE_MD  = 12
SPACE_LG  = 16
SPACE_XL  = 20
SPACE_2XL = 28
SPACE_3XL = 40

RADIUS_SM  = 6    # pills, tagy, malé tlačidlá
RADIUS_MD  = 10   # karty, modálne okná
RADIUS_LG  = 14   # login karta, veľké panely
RADIUS_XL  = 20   # hero plochy

HEIGHT_BTN_SM  = 32
HEIGHT_BTN_MD  = 40
HEIGHT_BTN_LG  = 48
HEIGHT_INPUT   = 40


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNKCIE
# ══════════════════════════════════════════════════════════════════════════════

def mode_color(token: tuple[str, str]) -> str:
    """Vráti správnu farbu podľa aktuálneho appearance mode."""
    return token[1] if ctk.get_appearance_mode() == "Dark" else token[0]


def color_blend(hex_color: str, alpha: float = 0.13,
                bg: str | None = None, dark: bool = True) -> str:
    """
    Blend hex_color s bg farbou pri danom alpha (0.0–1.0).
    Vracia #RRGGBB — náhrada za CSS rgba() ktoré Tkinter nepodporuje.

    Args:
        hex_color: Farba popredia (#RRGGBB)
        alpha:     Intenzita popredia (0=plné bg, 1=plné fg)
        bg:        Farba pozadia. Ak None, použije BG_MAIN podľa dark parametra.
        dark:      Ak True, použije dark variant BG_MAIN ako default bg.
    """
    if bg is None:
        bg = BG_MAIN[1] if dark else BG_MAIN[0]
    r1 = int(hex_color[1:3], 16)
    g1 = int(hex_color[3:5], 16)
    b1 = int(hex_color[5:7], 16)
    r2 = int(bg[1:3], 16)
    g2 = int(bg[3:5], 16)
    b2 = int(bg[5:7], 16)
    r = int(r1 * alpha + r2 * (1 - alpha))
    g = int(g1 * alpha + g2 * (1 - alpha))
    b = int(b1 * alpha + b2 * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


def color_blend_dual(hex_color_tuple: tuple[str, str],
                     alpha: float = 0.15) -> tuple[str, str]:
    """
    Vráti (light_blend, dark_blend) pre badge pozadia.
    Automaticky blenduje light farbu s BG_CARD[0] a dark s BG_CARD[1].
    """
    light = color_blend(hex_color_tuple[0], alpha, bg=BG_CARD[0], dark=False)
    dark  = color_blend(hex_color_tuple[1], alpha, bg=BG_CARD[1], dark=True)
    return (light, dark)
