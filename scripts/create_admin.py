"""Bootstrap admin — vytvorí alebo aktualizuje admin účet z env premenných.

Nahrádza pôvodný default admin/admin123 (bezpečnostné riziko). Uloží bcrypt hash.
Funguje pre SQLite aj Postgres podľa DB_BACKEND / DATABASE_URL.

Použitie:
    ADMIN_USERNAME=admin ADMIN_PASSWORD='silne-nahodne-heslo' python scripts/create_admin.py

Windows PowerShell:
    $env:ADMIN_PASSWORD='silne-nahodne-heslo'; python scripts/create_admin.py
"""
import os
import sys

# Repo root na sys.path (aby fungovali importy repositories.* / logic.*)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories import user_repo  # noqa: E402
from logic.passwords import hash_password  # noqa: E402


def main() -> int:
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD")

    if not password:
        print("CHYBA: nastav premennú ADMIN_PASSWORD (a voliteľne ADMIN_USERNAME).")
        return 1
    if len(password) < 8:
        print("CHYBA: heslo musí mať aspoň 8 znakov.")
        return 1

    hashed = hash_password(password)
    existing = user_repo.get_by_username(username)
    if existing:
        user_repo.update_password(existing["id"], hashed)
        print(f"OK: heslo admina '{username}' bolo aktualizované (bcrypt).")
    else:
        ok, msg = user_repo.create_user(username, hashed, "Administrator", "admin", None)
        if ok:
            print(f"OK: admin '{username}' bol vytvorený (bcrypt).")
        else:
            print(f"CHYBA pri vytváraní: {msg}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
