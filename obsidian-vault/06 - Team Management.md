# 👥 Team Management

#team #hierarchia #ui

## Koncept

Aplikácia podporuje **3-úrovňovú hierarchiu**:

```
admin
  └── manager
        └── employee
```

Každý užívateľ má `manager_id` → FK na `users.id`. Manažér vidí len svojich priamych podriadených.

## TeamView

**Súbor:** `ui/screens/team_view.py`

### Čo zobrazuje

1. **Team Summary bar** — agregované štatistiky celého tímu:
   - Celkový počet členov
   - Celkový počet úloh
   - Aktívne (in_progress)
   - Dokončené

2. **Member karty** — pre každého člena tímu:
   - Avatar (farebný kruh s iniciálkami, farba podľa roly)
   - Meno + role badge + @username
   - Workload mini-štatistiky (Úlohy / Aktívne / Hotové)
   - Progress bar (% dokončenia)
   - **Expandovateľný task list** — kliknutím sa rozbalí zoznam úloh člena

### Role badges

| Rola | Farba |
|------|-------|
| admin | 🔴 `#E53935` |
| manager | 🔵 `#1976D2` |
| employee | 🟢 `#00897B` |

### Task list (expand/collapse)

```
▶ Zobraziť úlohy (5)     ← kliknutím sa rozbalí
▼ Skryť úlohy (5)        ← po rozbalení

● Názov úlohy  [Critical]  Projekt  Kategória  3d
● Ďalšia úloha            Projekt2             1d
```

## AddMemberDialog

Tlačidlo **+ Pridať člena** (viditeľné len pre admin/manager).

Polia:
- Meno a priezvisko
- Prihlasovacie meno (username)
- Heslo (min. 4 znaky)
- Rola (employee / manager)

Po uložení → `add_new_member()` → `user_repo.create_user()` → SHA-256 hash hesla.

## Workload funkcie (task_repo.py)

```python
get_workload_for_user(user_id) → dict:
    # { total, pending, in_progress, completed, blocked, progress }

get_tasks_assigned_to_user(user_id) → list[dict]:
    # úlohy s názvom projektu, kategóriou, is_critical, duration
```

## Hierarchia — get_my_team()

```python
# logic/hierarchy.py
def get_my_team(manager_id):
    return user_repo.get_team_by_manager(manager_id)

# user_repo.py
def get_team_by_manager(manager_id):
    SELECT id, full_name, role, username
    FROM users WHERE manager_id = ?
```

> Admin vidí len svojich priamych podriadených (nie celý strom). Pre v2.0 — rekurzívny dotaz.

## Nastavenia (SettingsScreen)

Zmena vlastného hesla:
```python
# Validácia:
# 1. Staré heslo musí súhlasiť
# 2. Nové heslo min. 6 znakov
# 3. Potvrdenie musí súhlasiť
# → user_repo.update_password(user_id, sha256(new_pass))
```

## Súvisiace

- [[03 - Databáza & Repo#users]]
- [[04 - UI Obrazovky]]
- [[07 - Bugy & Opravy#KeyError 0]]
- [[08 - Roadmap v2.0#Team Features]]
