"""Hashovanie hesiel — bcrypt s transparentnou migráciou zo starých SHA-256 hashov.

Pôvodne boli heslá uložené ako holé SHA-256 (64 hex znakov, bez soli) — zraniteľné
na rainbow-table a rýchly bruteforce. Nové heslá sa ukladajú ako bcrypt (salted,
pomalé). `verify_password` akceptuje OBA formáty, takže existujúci používatelia sa
vedia prihlásiť; `needs_rehash` označí staré hashe, ktoré vrstva user_repo pri
prihlásení automaticky prehashuje na bcrypt (migrácia bez zásahu používateľa).
"""
from __future__ import annotations

import hashlib

import bcrypt


def hash_password(plain: str) -> str:
    """Vytvor bcrypt hash (salted). Vráti utf-8 string vhodný na uloženie do DB."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _is_legacy_sha256(stored: str) -> bool:
    """True ak hash vyzerá ako starý SHA-256 (64 hex znakov)."""
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower())


def verify_password(plain: str, stored: str) -> bool:
    """Over heslo proti uloženému hashu — podporuje bcrypt aj starý SHA-256."""
    if not stored:
        return False
    if _is_legacy_sha256(stored):
        return hashlib.sha256(plain.encode("utf-8")).hexdigest() == stored
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def needs_rehash(stored: str) -> bool:
    """True ak je uložený hash starý SHA-256 a treba ho pri prihlásení migrovať na bcrypt."""
    return _is_legacy_sha256(stored)
