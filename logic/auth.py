import sqlite3
import os

# Musíme Pythonu povedať, kde presne leží naša databáza
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "my_project_app.db")


def login_user(username, password):
    """
    Funkcia overí meno a heslo v databáze.
    Ak sú správne, vráti informácie o užívateľovi.
    Ak nie, vráti None.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # SQL príkaz: Nájdi užívateľa s týmto menom a heslom
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()  # Vytiahne prvý nájdený riadok

        conn.close()
        return user

    except Exception as e:
        print(f"Chyba pri prihlasovaní: {e}")
        return None