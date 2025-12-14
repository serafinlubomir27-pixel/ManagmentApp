import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "my_project_app.db")


def get_tasks_for_project(project_id):
    """Vráti všetky úlohy pre konkrétny projekt aj s menom človeka, ktorý ju má na starosti"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT t.id, t.name, t.status, t.due_date, u.username
                       FROM tasks t
                                LEFT JOIN users u ON t.assigned_to = u.id
                       WHERE t.project_id = ?
                       ORDER BY t.created_at DESC
                       """, (project_id,))

        tasks = cursor.fetchall()
        conn.close()
        return tasks
    except Exception as e:
        print(f"Chyba: {e}")
        return []


def add_task(project_id, name, assigned_to, created_by, due_date=None):
    """Vytvorí úlohu a zapíše to do Activity Logu"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Vložíme úlohu
        cursor.execute("""
                       INSERT INTO tasks (project_id, name, assigned_to, created_by, due_date)
                       VALUES (?, ?, ?, ?, ?)
                       """, (project_id, name, assigned_to, created_by, due_date))

        new_task_id = cursor.lastrowid

        # 2. Získame mená pre log
        cursor.execute("SELECT username FROM users WHERE id = ?", (created_by,))
        user_name = cursor.fetchone()[0]

        # 3. Zapíšeme do Activity Logu
        cursor.execute("""
                       INSERT INTO activity_logs (task_id, user_id, user_name, action, new_value)
                       VALUES (?, ?, ?, ?, ?)
                       """, (new_task_id, created_by, user_name, "Vytvoril úlohu", name))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Chyba pri vytváraní úlohy: {e}")
        return False


# --- NOVÉ FUNKCIE PRE DETAIL ÚLOHY ---

def update_task_status(task_id, new_status, user_id):
    """Zmení stav úlohy a zapíše to do histórie"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Získame starý status pre log
        cursor.execute("SELECT status, name FROM tasks WHERE id = ?", (task_id,))
        old_data = cursor.fetchone()
        if not old_data: return False
        old_status, task_name = old_data

        # Aktualizujeme status
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))

        # Získame meno užívateľa
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user_name = cursor.fetchone()[0]

        # Zápis do Activity Logu
        cursor.execute("""
                       INSERT INTO activity_logs (task_id, user_id, user_name, action, old_value, new_value)
                       VALUES (?, ?, ?, ?, ?, ?)
                       """, (task_id, user_id, user_name, "Zmena statusu", old_status, new_status))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Chyba status: {e}")
        return False


def add_comment(task_id, user_id, content):
    """Pridá komentár k úlohe"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
                       INSERT INTO task_comments (task_id, user_id, content)
                       VALUES (?, ?, ?)
                       """, (task_id, user_id, content))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Chyba komentár: {e}")
        return False


def get_task_comments(task_id):
    """Načíta históriu chatu pre úlohu"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT c.content, c.created_at, u.username
                       FROM task_comments c
                                JOIN users u ON c.user_id = u.id
                       WHERE c.task_id = ?
                       ORDER BY c.created_at ASC
                       """, (task_id,))

        return cursor.fetchall()
    except Exception as e:
        print(e)
        return []