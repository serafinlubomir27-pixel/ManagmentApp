# 🚀 Roadmap v2.0

#roadmap #v2 #cloud #saas

## Vízia

v1.0 = solidný **desktop MVP** pre freelancerov a malé tímy.
v2.0 = **cloud/SaaS** pre korporácie — PostgreSQL, REST API, web frontend.

---

## PostgreSQL / Supabase ✅

[[01 - Architektúra#Repository Pattern|Repository Pattern]] bol navrhnutý práve pre túto migráciu.

### Implementované (v1.2)

Detaily: [[11 - Supabase Migrácia]]

```
✅ base_repo.py — duálny backend (SQLite / PostgreSQL)
✅ _PgCursorWrapper — ? → %s, RETURNING id auto-append, dict rows
✅ database/supabase_schema.sql — ENUM typy, 7 tabuliek, 10 indexov
✅ database/migrate_to_supabase.py — jednorazová migrácia dát
✅ .env.example — DB_BACKEND, DATABASE_URL dokumentácia
✅ requirements.txt — psycopg2-binary, python-dotenv
✅ 64 unit testov stále prechádza
```

### Zostáva

- Vytvoriť Supabase projekt a spustiť schema (manuálny krok užívateľa)
- Row Level Security (RLS) pre multi-tenant použitie

### Supabase výhody

- PostgreSQL (production-grade)
- Vstavaná autentifikácia
- Row Level Security
- REST API zadarmo
- Real-time subscriptions (notifications!)

---

## REST API / Backend

```
FastAPI backend (✅ implementované):
├── /auth               ← login, register, JWT
├── /projects           ← CRUD projektov
├── /tasks              ← CRUD úloh + CPM trigger + GET /tasks/{id} detail
├── /dependencies       ← správa závislostí
├── /team               ← hierarchia, workload
├── /projects/{id}/attachments     ← prílohy projektu (Fáza 1)
├── /projects/{id}/all-attachments ← všetky prílohy (projekt + tasky)
├── /tasks/{id}/attachments        ← prílohy úlohy (Fáza 1)
├── /project-attachments/{id}      ← PATCH visibility, DELETE
├── /task-attachments/{id}         ← PATCH visibility, DELETE
└── /clients                       ← klientský modul (Fáza 3)
    ├── /clients/{id}/meetings
    ├── /clients/{id}/compliance
    └── /clients/{id}/pipeline
```

[[02 - CPM Engine|CPM Engine]] (`cpm_engine.py`) je **čistý Python bez závislostí** → beží priamo na FastAPI backende.

---

## Web Frontend

✅ **Implementované:** React + TypeScript + Tailwind CSS + React Query

Hlavné stránky a komponenty:
- `ProjectDetailPage` — tasky, Gantt, sieťový diagram, PERT, Zdroje, Burndown
- `NetworkDiagram` — interaktívny SVG sieťový diagram (klik na uzol → modal)
- `TaskDetailModal` — dvojsĺpcový modal (info + komentáre + prílohy)
- `ClientsPage` / `ClientDetailPage` — klientský register (Fáza 3)

---

## Team Features

| Feature | Stav |
|---------|------|
| Správa používateľov (admin) | ✅ Hotovo |
| Rolový systém (admin/manager/employee) | ✅ Hotovo |
| Rekurzívna hierarchia (manager → podriadení) | ✅ Hotovo |
| Workload / time tracking | ✅ Hotovo |
| Kalendárna integrácia (.ics export) | ✅ Hotovo |

---

## Reporting & Export

| Feature | Stav |
|---------|------|
| Gantt SVG v prehliadači | ✅ Hotovo |
| PERT analýza (a/m/b, pravdepodobnosť) | ✅ Hotovo |
| Burndown chart | ✅ Hotovo |
| PDF report klienta | 🔜 Fáza 4 |
| Excel export | 🔜 Budúcnosť |

---

## Ďalšie features

### Prílohy súborov (Fáza 1) ✅
Detaily: [[13 - Prílohy & Sieťový Diagram]]
- Projektové prílohy + taskové prílohy
- 3 úrovne viditeľnosti: Tím / Manažéri / Len ja
- AttachmentSidebar v ProjectDetailPage

### Interaktívny sieťový diagram (Fáza 2) ✅
Detaily: [[13 - Prílohy & Sieťový Diagram]]
- Klik na uzol → `TaskDetailModal`
- Editácia úlohy bez opustenia diagramu

### Klientský modul (Fáza 3) ✅
Detaily: [[14 - Klientský Modul]]
- Klientský register s MiFID II kategóriami
- Deal pipeline (Kanban — 7 fáz)
- Compliance checklist (KYC, AML, suitability...)
- Log stretnutí s follow-up akciami

### Šablóny projektov
✅ **Implementované v v1.0** — `FromTemplateDialog`, `NewProjectDialog`

### Časové sledovanie
✅ Time log na úlohách (actual_hours vs estimated_hours)

---

## Technické dlhy v1.0 → v1.1

| Problém | Priorita | Stav |
|---------|----------|------|
| Admin vidí len priamych podriadených (nie celý strom) | Stredná | ✅ `get_full_tree()` — BFS rekurzia, toggle v TeamView |
| Žiadne unit testy | Vysoká | ✅ 64 testov — `tests/test_cpm_engine.py` + `tests/test_repositories.py` |
| matplotlib charts nie sú interaktívne (hover/click) | Nízka | 🔜 |
| Gantt nepodporuje scroll pre veľké projekty | Stredná | ✅ `tk.Canvas` viewport + CTkScrollbar (>12 úloh alebo >18" šírka) |
| Vyhľadávanie úloh v Task liste | Stredná | ✅ Live search entry — podľa názvu, assignee, kategórie |
| Notifikácie pri blížiacich sa deadlinoch | Stredná | ✅ Deadline banner na dashboarde (D-3, D-1, overdue) |
| Import/Export úloh cez CSV | Nízka | ✅ `export_tasks_csv()` + `import_tasks_csv()` v export_manager.py |

### Čo bolo vyriešené v priebehu v1.0

| Bug / Tech dlh | Riešenie |
|----------------|----------|
| `self._canvas` konflikt s CTkFrame | `_mpl_canvas` + `destroy()` override → [[07 - Bugy & Opravy#matplotlib canvas conflict]] |
| `#RRGGBBAA` farby v Tkinter | `color_blend()` funkcia v `theme.py` |
| `user_data[0]` dict/tuple | `isinstance()` defensive pattern |
| `border_color="transparent"` | Podmienečné nastavenie cez `**kwargs` |

---

## Súvisiace

- [[00 - Prehľad projektu]]
- [[01 - Architektúra]]
- [[02 - CPM Engine]]
- [[03 - Databáza & Repo]]
