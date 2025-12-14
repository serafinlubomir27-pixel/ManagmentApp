import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "my_project_app.db")

def get_my_team(manager_id):
    """Vráti zoznam ľudí, ktorí majú v stĺpci manager_id tvoje ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Ak je manager_id None (napr. Admin vidí všetkých), upravíme dotaz
        # Ale pre jednoduchosť predpokladajme, že hľadáme priamych podriadených
        cursor.execute("""
            SELECT id, full_name, role, username 
            FROM users 
            WHERE manager_id = ?
        """, (manager_id,))

        team = cursor.fetchall()
        conn.close()
        return team
    except Exception as e:
        print(f"Chyba pri načítaní tímu: {e}")
        return []

def add_new_member(manager_id, full_name, username, password, role="employee"):
    """Vytvorí nového užívateľa a priradí ho pod aktuálneho manažéra"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (username, password, full_name, role, manager_id)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password, full_name, role, manager_id))

        conn.commit()
        conn.close()
        return True, "Užívateľ vytvorený"
    except sqlite3.IntegrityError:
        return False, "Užívateľské meno už existuje!"
    except Exception as e:
        return False, str(e)