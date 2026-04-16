# 🖥️ UI Obrazovky

#ui #customtkinter #screens

## Prehľad obrazoviek

```
main.py (MainApp)
├── LoginScreen              ← prvé okno
└── MainLayout (sidebar + content)
    ├── DashboardScreen      ← /dashboard
    ├── ProjectsView         ← /projects
    │   └── ProjectDetailView ← po kliknutí Otvoriť
    │       ├── Tab: Dashboard
    │       ├── Tab: Tasks
    │       ├── Tab: Gantt      ← [[05 - Gantt & Network#Gantt Chart]]
    │       └── Tab: CPM Network ← [[05 - Gantt & Network#CPM Network Diagram]]
    ├── TeamView             ← /team → [[06 - Team Management]]
    ├── CalendarView         ← /calendar
    └── SettingsScreen       ← /settings
```

## LoginScreen

- Centrovaná karta, branding (📋 + názov)
- SHA-256 heslá, Enter navigácia medzi poľami
- Validácia pred odoslaním

## DashboardScreen

- 3 stat karty: Aktívne projekty / Moje úlohy / Po termíne
- Matplotlib **donut chart** — rozdelenie stavov úloh
- Scrollovateľný activity feed (posledné akcie)
- `_on_destroy` hook — `plt.close("all")` aby nedochádzalo k memory leaku

## ProjectsView

- **Search bar** — živé filtrovanie podľa názvu projektu
- **Filter dropdown** — Všetky / Aktívne / Dokončené / Archivované
- Scrollovateľný zoznam projektov
- Každý projekt = karta s:
  - farebným pásom stavu (modrá/zelená/šedá)
  - progress barom (dokončené/celkové úlohy)
  - tlačidlom **Otvoriť** a menu ⚙️
- Menu ⚙️ obsahuje: Zmena stavu, Uložiť ako šablónu
- Tlačidlo **+ Nový Projekt** → `NewProjectDialog` (scrollovateľný, 460×430)
- Tlačidlo **📋 Zo šablóny** → `FromTemplateDialog` (výber existujúcej šablóny)

## Project Detail

Tabbed rozhranie — 4 záložky. Hlavička obsahuje tlačidlo **📄 Export PDF** → [[09 - PDF Export]].

### Tab 1: Dashboard
- 4 stat karty: Progress% / Dokončené / Kritická cesta / Zdravie
- Progress bar celého projektu
- **Časová os** — trvanie, oneskorenie
- **Upozornenia** — blokované úlohy, oneskorenie, CPM chyby
- Rozdelenie úloh podľa stavu (4 farebné boxy)

### Tab 2: Tasks
- Filter podľa stavu (Všetky / pending / in_progress / completed / blocked)
- Každá úloha zobrazuje:
  - Checkbox (toggle completed)
  - Názov + `[!]` Critical badge + kategória badge
  - `ES | EF | LS | LF | Float` hodnoty
  - Status badge, tlačidlo ✏️ Edit
- `TaskEditorDialog` — plný editor:
  - Názov, popis, trvanie, oneskorenie, kategória, stav, priradenie
  - Checkboxy dependencies (závislosť na iných úlohách)
  - Sekcia **Komentáre** — pridanie/zobrazenie komentárov
  - Sekcia **Prílohy** — upload súborov, download, delete
  - CPM výsledky (read-only)
- `AddTaskDialog` — rýchle pridanie s checkboxmi závislostí

### Tab 3: Gantt
→ [[05 - Gantt & Network#Gantt Chart]]

### Tab 4: CPM Network
→ [[05 - Gantt & Network#CPM Network Diagram]]

## CalendarView

- Vlastný mesačný kalendár (bez externých knižníc)
- Kliknutie na deň zobrazí úlohy s due_date
- `uniform="cal_row"` — konzistentné výšky riadkov (fix pre nerovnomerné rozloženie)
- `_update_selection()` — len rekonfiguruje border 2 buniek (bez re-renderu = bez blikania)
- `CELL_HEIGHT=60` px

> ⚠️ `border_color="transparent"` nefunguje v CTkFrame — pozri [[07 - Bugy & Opravy#CTkFrame transparent border]].

## SettingsScreen

- Profil (read-only): meno, username, rola
- Zmena hesla: staré → nové → potvrdenie + validácia
- Dark/Light mode toggle → ukladá do `config.json`

## Sidebar

```python
Sidebar(parent, callback_funkcia=handle_navigation)
# Tlačidlá: Dashboard | Projekty | Kalendár | Môj Tím | Nastavenia | Logout
sidebar.set_active("projects")  # zvýrazní aktívnu položku
```

## Farebná téma

Všetky farby z `ui/theme.py`:
```python
from ui.theme import PRIMARY, ACCENT, DANGER, WARNING, BG_CARD, BG_MAIN, BG_ROW, TEXT_PRIMARY, TEXT_SECONDARY, color_blend
```

`color_blend(hex, alpha)` — nahrádza CSS `rgba()` / 8-znakové hex (Tkinter ich nepodporuje).

## Súvisiace

- [[01 - Architektúra]]
- [[02 - CPM Engine]]
- [[05 - Gantt & Network]]
- [[06 - Team Management]]
- [[07 - Bugy & Opravy]]
