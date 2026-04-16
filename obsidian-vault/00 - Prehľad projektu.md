# 🗂️ ManagmentApp v1.0

#projekt #python #desktop #mvp

## Čo to je

Desktopová **projektová manažérska aplikácia** postavená v Pythone s CustomTkinter.
Pôvodne vznikla ako webová app na platforme **Lovable** (PathFlow), následne prepísaná do Pythonu cez Gemini a dokončená s Claudom.

## Cieľová skupina

- Freelanceri a solopodnikatelia
- Malé tímy (5–20 ľudí)
- Manažéri s podriadenými
- Finančný poradcovia, konzultanti

## Stav projektu

| Etapa | Popis | Stav |
|-------|-------|------|
| Etapa 1 | [[02 - CPM Engine]] + DB schéma | ✅ Hotovo |
| Etapa 2 | [[04 - UI Obrazovky#Project Detail]] + Task Editor | ✅ Hotovo |
| Etapa 3 | [[05 - Gantt & Network#Gantt Chart]] | ✅ Hotovo |
| Etapa 4 | [[05 - Gantt & Network#CPM Network Diagram]] | ✅ Hotovo |
| Etapa 5 | [[06 - Team Management]] | ✅ Hotovo |
| Etapa 6 | [[09 - PDF Export]] (reportlab) | ✅ Hotovo |
| Etapa 7 | UI: šablóny, search, komentáre, prílohy, závislosti | ✅ Hotovo |
| Bugfixy | [[07 - Bugy & Opravy]] — canvas conflict, farby, dict/tuple | ✅ Hotovo |
| **v1.0 MVP** | **Kompletné** | 🎉 **Vydané** |
| v1.1 | Unit testy, search, Gantt scroll, notifikácie, CSV, strom hierarchie | ✅ Hotovo |
| v1.2 | [[11 - Supabase Migrácia]] — duálny backend SQLite/PostgreSQL | ✅ Hotovo |
| v2.0 | [[08 - Roadmap v2.0]] — FastAPI + React web frontend | 🔜 Plánované |

## Technologický stack

- **GUI:** `customtkinter 5.2+`
- **Databáza:** `SQLite3` (lokálna) **alebo** `PostgreSQL / Supabase` — [[11 - Supabase Migrácia|duálny backend cez DB_BACKEND env var]]
- **Grafy:** `matplotlib 3.7+` (FigureCanvasTkAgg)
- **Obrázky:** `Pillow 10+`
- **PDF Export:** `reportlab 4.x` → [[09 - PDF Export]]
- **Algoritmus:** [[02 - CPM Engine|CPM — Critical Path Method]]

## Súbory projektu

```
ManagmentApp/
├── main.py                    ← Entry point, navigácia
├── database/setup.py          ← Tvorba tabuliek, migrácie
├── repositories/              ← [[03 - Databáza & Repo|Repository Pattern]]
├── logic/                     ← Business logika
│   ├── cpm_engine.py          ← [[02 - CPM Engine|Čistý CPM algoritmus]]
│   ├── cpm_manager.py         ← Bridge CPM ↔ DB
│   ├── auth.py
│   ├── task_manager.py
│   └── ...
├── ui/
│   ├── theme.py               ← Farby, color_blend()
│   ├── components/sidebar.py
│   └── screens/               ← [[04 - UI Obrazovky]]
└── obsidian-vault/            ← Tento trezor
```

## Súvisiace poznámky

- [[01 - Architektúra]]
- [[02 - CPM Engine]]
- [[03 - Databáza & Repo]]
- [[04 - UI Obrazovky]]
- [[05 - Gantt & Network]]
- [[06 - Team Management]]
- [[07 - Bugy & Opravy]]
- [[08 - Roadmap v2.0]]
- [[09 - PDF Export]]
- [[10 - v1.1 Featury]]
- [[11 - Supabase Migrácia]]
