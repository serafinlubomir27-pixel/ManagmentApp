import sqlite3
import os

# Názov databázy
DB_NAME = "my_project_app.db"

def create_database():
    # Zabezpečíme, aby sa databáza vytvorila v hlavnom priečinku projektu,
    # nie vo vnútri priečinka database/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, DB_NAME)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"🔄 Pracujem s databázou na ceste: {db_path}")

    # --- 1. TABUĽKA UŽÍVATEĽOV (Hierarchia + Roly) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,  
        full_name TEXT,
        role TEXT DEFAULT 'employee', -- admin, manager, employee
        manager_id INTEGER, -- Tvoj požiadavka: Kto je koho šéf
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (manager_id) REFERENCES users (id)
    )
    ''')

    # --- 2. TABUĽKA PROJEKTOV ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, -- Kto projekt vytvoril
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'active', -- active, completed, archived
        is_template BOOLEAN DEFAULT 0, -- Tvoj požiadavka: Šablóny procesov
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # --- 3. TABUĽKA ÚLOH (Tasks) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending', -- pending, in_progress, completed
        assigned_to INTEGER, -- Tvoj požiadavka: Delegovanie na kolegu
        created_by INTEGER,  
        due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to) REFERENCES users (id),
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    ''')

    # --- 4. TABUĽKA ACTIVITY LOG (Reporting pre Manažéra) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        user_id INTEGER, 
        user_name TEXT, 
        action TEXT,     -- napr. "Zmena statusu"
        old_value TEXT,
        new_value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # --- 5. TABUĽKA SÚBOROV (Document Management) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL, 
        uploaded_by INTEGER,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    ''')

    # --- 6. TABUĽKA KOMENTÁROV (Chat pri úlohe) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # --- 7. TABUĽKA ZÁVISLOSTÍ ÚLOH (task_dependencies) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_dependencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        depends_on_task_id INTEGER NOT NULL,
        type TEXT DEFAULT 'finish_to_start',
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
    )
    ''')

    # --- Bezpečná migrácia: nové stĺpce v tasks ---
    for column_sql in [
        "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'",
        "ALTER TABLE tasks ADD COLUMN estimated_hours REAL",
    ]:
        try:
            cursor.execute(column_sql)
        except Exception:
            pass  # Stĺpec už existuje, preskakujeme

    # --- Vytvorenie prvého ADMINA (aby si sa mal ako prihlásiť) ---
    try:
        # Heslo je zatiaľ v čistom texte pre testovanie: 'admin123'
        cursor.execute('''
        INSERT INTO users (username, password, full_name, role) 
        VALUES ('admin', 'admin123', 'Hlavný Admin', 'admin')
        ''')
        print("✅ Vytvorený užívateľ: admin / heslo: admin123")
    except sqlite3.IntegrityError:
        print("ℹ️ Admin už existuje, preskakujem vytváranie.")

    conn.commit()
    conn.close()
    print("✅ Databáza úspešne skontrolovaná/vytvorená!")

# Toto umožňuje spustiť súbor aj samostatne pre test
if __name__ == "__main__":
    create_database()