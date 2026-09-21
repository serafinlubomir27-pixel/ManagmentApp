"""Testy hashovania hesiel (Fáza 0 — P0-5).

Overujú bcrypt hashovanie, kompatibilitu so starými SHA-256 heslami a
transparentnú migráciu SHA-256 → bcrypt pri prihlásení.

Spustenie:
    py -m pytest tests/test_passwords.py -v
"""
import hashlib

# DB pripraví conftest.py (spoločná testová SQLite DB).
from logic.passwords import hash_password, verify_password, needs_rehash
from repositories import user_repo, org_repo

_ORG_ID = org_repo.get_organization_by_slug("default")["id"]


def _sha(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


# ── Jednotkové testy password helpera ────────────────────────────────────────

def test_bcrypt_roundtrip():
    h = hash_password("tajneheslo")
    assert h != "tajneheslo"
    assert h.startswith("$2")           # bcrypt prefix
    assert verify_password("tajneheslo", h)
    assert not verify_password("zle", h)
    assert not needs_rehash(h)


def test_legacy_sha256_verifies():
    stored = _sha("staré")
    assert verify_password("staré", stored)
    assert not verify_password("iné", stored)
    assert needs_rehash(stored)          # starý hash → treba migrovať


def test_empty_stored_is_rejected():
    assert not verify_password("čokoľvek", "")


# ── Migrácia pri prihlásení (SHA-256 → bcrypt) ───────────────────────────────

def test_login_migrates_sha256_to_bcrypt():
    # Vytvor používateľa priamo so starým SHA-256 hashom
    user_repo.create_user("legacy", _sha("heslo123"), "Legacy User", "employee", None, _ORG_ID)
    before = user_repo.get_by_username("legacy")["password"]
    assert needs_rehash(before)          # uložený ako SHA-256

    # Prihlásenie starým heslom funguje...
    row = user_repo.get_by_username_and_password("legacy", "heslo123")
    assert row is not None

    # ...a heslo je teraz migrované na bcrypt
    after = user_repo.get_by_username("legacy")["password"]
    assert after.startswith("$2")
    assert not needs_rehash(after)

    # Prihlásenie po migrácii stále funguje, zlé heslo nie
    assert user_repo.get_by_username_and_password("legacy", "heslo123") is not None
    assert user_repo.get_by_username_and_password("legacy", "zle") is None


def test_bcrypt_user_login():
    user_repo.create_user("modern", hash_password("silne456"), "Modern User", "employee", None, _ORG_ID)
    assert user_repo.get_by_username_and_password("modern", "silne456") is not None
    assert user_repo.get_by_username_and_password("modern", "zle") is None


# ── Regresia: create_database() nesmie poškodiť bcrypt hashe ─────────────────

def test_create_database_preserves_bcrypt_passwords():
    """create_database() beží pri KAŽDOM štarte na SQLite.

    Jeho migrácia plaintextu kedysi rozhodovala podľa dĺžky ("!= 64 znamená
    plaintext"). Bcrypt má 60 znakov, takže si ho vyhodnotila ako plaintext a
    prepísala na sha256(bcrypt_hash) — používateľ sa už nikdy neprihlásil.
    """
    from database.setup import create_database

    user_repo.create_user("restart", hash_password("preziRestart1"), "Restart User", "employee", None, _ORG_ID)
    before = user_repo.get_by_username("restart")["password"]
    assert before.startswith("$2")

    create_database()          # simuluj reštart aplikácie

    after = user_repo.get_by_username("restart")["password"]
    assert after == before, "create_database() prepísal bcrypt hash"
    assert user_repo.get_by_username_and_password("restart", "preziRestart1") is not None


def test_create_database_preserves_legacy_sha256():
    """Starý sha256 hash musí prejsť nedotknutý — inak by sa dvojito zahashoval."""
    from database.setup import create_database

    user_repo.create_user("stary", _sha("legacyHeslo"), "Stary User", "employee", None, _ORG_ID)
    before = user_repo.get_by_username("stary")["password"]

    create_database()

    assert user_repo.get_by_username("stary")["password"] == before
    assert user_repo.get_by_username_and_password("stary", "legacyHeslo") is not None
