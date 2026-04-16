# 🏗️ Architektúra aplikácie

#architektúra #patterns #python

## Hlavné vrstvy

```
┌─────────────────────────────┐
│         UI (CustomTkinter)   │  ← [[04 - UI Obrazovky]]
│   screens/, components/      │
├─────────────────────────────┤
│        Business Logic        │  ← logic/
│  cpm_engine, task_manager... │
├─────────────────────────────┤
│      Repository Pattern      │  ← [[03 - Databáza & Repo]]
│   task_repo, user_repo...    │
├─────────────────────────────┤
│         SQLite3 DB           │
│    my_project_app.db         │
└─────────────────────────────┘
```

## Repository Pattern

Zavedený kvôli **budúcej migrácii na cloud** ([[08 - Roadmap v2.0]]).
Celá DB logika je izolovaná v `repositories/` — UI nikdy nepíše SQL priamo.

```python
# Príklad: UI volá logic, logic volá repo
ui → logic.task_manager.add_task()
        → task_repo.create_task()
              → SQLite INSERT
```

### Prečo to zmení robenie na v2.0

Keď príde čas na PostgreSQL/Supabase, stačí **len vymeniť repo vrstvu** — UI a logika zostanú nedotknuté.

## Navigácia (main.py)

```python
handle_navigation("projects")  →  ProjectsView
handle_navigation("team")      →  TeamView
handle_navigation("calendar")  →  CalendarView
handle_navigation("settings")  →  SettingsScreen
handle_navigation("dashboard") →  DashboardScreen
```

## User data flow

```
LoginScreen → on_login(user_dict) → MainApp.current_user
                                         ↓
                              všetky obrazovky dostávajú user_data ako dict:
                              { id, username, full_name, role, manager_id, ... }
```

> ⚠️ Dôležité: `user_data` je vždy `dict` (nie tuple). Pozri [[07 - Bugy & Opravy#KeyError 0]].

## Farebná téma

Definovaná v `ui/theme.py`:

| Konštanta | Hex | Použitie |
|-----------|-----|----------|
| `PRIMARY` | `#1976D2` | Hlavné tlačidlá, aktívne prvky |
| `ACCENT` | `#00695C` | Sekundárne akcie |
| `DANGER` | `#D32F2F` | Chyby, kritická cesta |
| `WARNING` | `#F57C00` | Upozornenia, float |
| `BG_CARD` | `#2B2B2B` | Karty |
| `BG_MAIN` | `#1E1E1E` | Pozadie |
| `BG_ROW` | `#333333` | Riadky v listoch |

> ⚠️ Tkinter nepodporuje `#RRGGBBAA`. Treba `color_blend()`. Pozri [[07 - Bugy & Opravy#Invalid color name]].

## Súvisiace

- [[00 - Prehľad projektu]]
- [[03 - Databáza & Repo]]
- [[07 - Bugy & Opravy]]
