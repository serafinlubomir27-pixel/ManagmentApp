"""Rate limiting (slowapi) — zdieľaný limiter pre routery aj app.

Chráni verejné/citlivé endpointy (login, signup, reset hesla) pred zneužitím
(brute-force, spam účtov, e-mail bombing cez forgot-password).

Vypnutie: nastav RATE_LIMIT_ENABLED=0 (používajú testy, aby ich stovky volaní
nenarazili na limit). V produkcii nechaj zapnuté.

Pozn.: in-memory úložisko stačí pre single-instance nasadenie (Railway). Pri
škálovaní na viac inštancií treba pridať zdieľané úložisko (Redis) cez storage_uri.
"""
from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_enabled = os.environ.get("RATE_LIMIT_ENABLED", "1") != "0"


def _client_ip(request) -> str:
    """Reálna IP klienta — za proxy (Railway) číta X-Forwarded-For, inak priamu IP.

    Bez tohto by za reverznou proxy všetky requesty vyzerali z jednej IP (proxy)
    a limit by sa zdieľal medzi všetkých používateľov naraz.
    """
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_client_ip, enabled=_enabled)
