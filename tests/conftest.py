"""Spoločné nastavenie pre testy — izolovaná dočasná SQLite DB + testovací JWT kľúč.

Kód beží PRED importom testových modulov (pytest importuje conftest ako prvé),
takže `base_repo` (ktoré číta cestu k DB pri importe) aj `setup.create_database()`
použijú tú istú dočasnú databázu. Bez toho by si jednotlivé test súbory navzájom
prepisovali SQLITE_PATH a repozitáre by čítali z inej DB, než v ktorej sú tabuľky.
"""
import os
import tempfile

_db_fd, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DB_BACKEND"] = "sqlite"
os.environ["SQLITE_PATH"] = _DB_PATH
os.environ.setdefault("APP_AUTH_KEY", "test-only-secret-key-min-32-characters-xx")

from database.setup import create_database  # noqa: E402

create_database()
