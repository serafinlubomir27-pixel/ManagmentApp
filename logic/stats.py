import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "my_project_app.db")


def get_dashboard_stats(user_id):
    """Vráti počty projektov, úloh a posledné aktivity"""
    stats = {
        "projects_count": 0,
        "tasks_count": 0,
        "critical_count": 0,
        "recent_activity": []
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Počet aktívnych projektov (kde som vlastník alebo mám úlohu)
        cursor.execute("""
                       SELECT COUNT(DISTINCT p.id)
                       FROM projects p
                                LEFT JOIN tasks t ON p.id = t.project_id
                       WHERE (p.user_id = ? OR t.assigned_to = ?)
                         AND p.status = 'active'
                       """, (user_id, user_id))
        stats["projects_count"] = cursor.fetchone()[0]

        # 2. Počet mojich nedokončených úloh
        cursor.execute("""
                       SELECT COUNT(*)
                       FROM tasks
                       WHERE assigned_to = ?
                         AND status != 'completed'
                       """, (user_id,))
        stats["tasks_count"] = cursor.fetchone()[0]

        # 3. Posledných 5 aktivít (Čo sa stalo v mojich projektoch?)
        # Toto je zložitejšie query, spája logy s projektmi, ktoré vidím
        cursor.execute("""
                       SELECT al.user_name, al.action, al.new_value, al.created_at
                       FROM activity_logs al
                                JOIN tasks t ON al.task_id = t.id
                                JOIN projects p ON t.project_id = p.id
                       WHERE p.user_id = ?
                          OR t.assigned_to = ?
                       ORDER BY al.created_at DESC LIMIT 5
                       """, (user_id, user_id))

        stats["recent_activity"] = cursor.fetchall()

        conn.close()
    except Exception as e:
        print(f"Chyba stats: {e}")

    return stats