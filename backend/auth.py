"""JWT helper — vydávanie a overovanie tokenov."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY = os.environ.get("APP_AUTH_KEY")
if not SECRET_KEY:
    # V produkcii (Postgres/Supabase) je APP_AUTH_KEY POVINNÝ — bez neho by boli
    # JWT tokeny falšovateľné cez známy default. Fail-fast pri štarte.
    if os.environ.get("DB_BACKEND", "sqlite").strip().lower() == "postgres":
        raise RuntimeError(
            "APP_AUTH_KEY nie je nastavený. V produkcii (DB_BACKEND=postgres) je povinný — "
            "nastav ho v prostredí (napr. Railway) na min. 32 náhodných znakov."
        )
    # Len pre lokálny vývoj so SQLite — NIKDY nepoužívať v produkcii.
    SECRET_KEY = "dev-only-insecure-secret-do-not-use-in-production-0123456789"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hodín


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Vráti payload alebo vyhodí JWTError."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
