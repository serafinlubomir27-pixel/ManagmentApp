import sqlite3
import os

# Cesta k databáze (rovnaká ako v auth.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "my_project_app.db")


def get_user_projects(user_id):
    """
    Vráti projekty:
    1. Ktoré som vytvoril JA (ako manažér)
    2. ALEBO v ktorých mám pridelenú aspoň jednu úlohu (ako zamestnanec)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT DISTINCT p.id, p.name, p.description, p.status
                       FROM projects p
                                LEFT JOIN tasks t ON p.id = t.project_id
                       WHERE p.user_id = ?     -- Projekty, ktoré vlastním
                          OR t.assigned_to = ? -- Projekty, kde mám úlohu
                       ORDER BY p.created_at DESC
                       """, (user_id, user_id))

        projekty = cursor.fetchall()
        conn.close()
        return projekty
    except Exception as e:
        print(f"Chyba pri načítaní projektov: {e}")
        return []


def create_test_project(user_id):
    """Pomocná funkcia na vytvorenie testovacieho projektu (aby si tam niečo videl)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO projects (user_id, name, description, status)
                       VALUES (?, ?, ?, ?)
                       """,
                       (user_id, "Nový Projekt 2025", "Toto je automaticky vytvorený testovací projekt.", "active"))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(e)
        return False