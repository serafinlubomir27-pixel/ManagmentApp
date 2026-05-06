# 🗂️ ManagmentApp — Prehľad projektu

#projekt #python #desktop #web #mvp #bp

## Čo to je

**Nodus** — projektová manažérska aplikácia s natívnym CPM (Critical Path Method) algoritmom.
Vznikla ako bakalárska práca Ľubomíra Serafína. Prešla tromi vývojovými etapami:

- **v1.x** — Python desktopová app (CustomTkinter, SQLite, CPM, Gantt, PDF export)
- **v2.0** — Web rewrite: FastAPI + React + SQLite, deploynuté na Railway + Surge.sh

## Cieľová skupina

- Freelanceri a solopodnikatelia
- Malé tímy (5–20 ľudí)
- Manažéri s podriadenými
- **Finanční poradcovia a makléri** (MiFID II compliance, klientský modul)

## Stav projektu

### v1.x — Desktopová aplikácia

| Etapa | Popis | Stav |
|-------|-------|------|
| Etapa 1 | [[02 - CPM Engine]] + DB schéma | ✅ Hotovo |
| Etapa 2 | [[04 - UI Obrazovky#Project Detail]] + Task Editor | ✅ Hotovo |
| Etapa 3 | [[05 - Gantt & Network#Gantt Chart]] | ✅ Hotovo |
| Etapa 4 | [[05 - Gantt & Network#CPM Network Diagram]] | ✅ Hotovo |
| Etapa 5 | [[06 - Team Management]] | ✅ Hotovo |
| Etapa 6 | [[09 - PDF Export]] (reportlab) | ✅ Hotovo |
| Etapa 7 | UI: šablóny, search, komentáre, prílohy, závislosti | ✅ Hotovo |
| **v1.0 MVP** | **Kompletné** | 🎉 **Vydané** |
| v1.1 | Unit testy, search, Gantt scroll, notifikácie, CSV, strom hierarchie | ✅ Hotovo |
| v1.2 | [[11 - Supabase Migrácia]] — duálny backend SQLite/PostgreSQL | ✅ Hotovo |

### v2.0 — Web aplikácia (FastAPI + React)

| Fáza | Popis | Stav |
|------|-------|------|
| Základ | FastAPI + React + JWT auth, CRUD projektov/úloh | ✅ Hotovo |
| CPM Web | CPM engine na backende, sieťový diagram SVG | ✅ Hotovo |
| Gantt | SVG Gantt chart | ✅ Hotovo |
| PERT | Probabilistická analýza (a/m/b odhady) | ✅ Hotovo |
| Tím | Správa používateľov, rolí, hierarchia | ✅ Hotovo |
| Fáza 1 | [[13 - Prílohy & Sieťový Diagram\|Prílohy súborov]] — projektové + taskové, 3 úrovne viditeľnosti | ✅ Hotovo |
| Fáza 2 | [[13 - Prílohy & Sieťový Diagram\|Interaktívny sieťový diagram]] — klik na uzol → TaskDetailModal | ✅ Hotovo |
| Fáza 3 | [[14 - Klientský Modul]] — klientský register, pipeline, compliance, stretnutia | ✅ Hotovo |

## Technologický stack

### v2.0 (aktuálny)

| Vrstva | Technológia |
|--------|-------------|
| Backend | FastAPI (Python), SQLite, JWT auth |
| Frontend | React 18, TypeScript, Tailwind CSS, React Query |
| Diagramy | SVG (vlastný renderer — CPM sieťový diagram, Gantt) |
| Deployment | Railway (backend) + Surge.sh (frontend) |
| Produkčné URL | `https://web-production-b865.up.railway.app` / `https://managmentapp.surge.sh` |

### v1.x (historický)

- **GUI:** `customtkinter 5.2+`
- **Databáza:** `SQLite3` / `PostgreSQL` cez duálny backend
- **Grafy:** `matplotlib 3.7+`
- **PDF Export:** `reportlab 4.x`

## Štruktúra repozitára (v2.0)

```
ManagmentApp/
├── backend/
│   ├── main.py                  ← FastAPI app, CORS, StaticFiles
│   ├── routers/                 ← API routery (projects, tasks, clients, attachments...)
│   ├── repositories/            ← Repository pattern (task_repo, client_repo, attachment_repo...)
│   ├── database/setup.py        ← SQLite schéma + migrácie
│   └── uploads/                 ← Nahrané súbory (lokálne)
├── frontend/
│   ├── src/
│   │   ├── pages/               ← ProjectDetailPage, ClientsPage, ClientDetailPage...
│   │   ├── components/          ← NetworkDiagram, TaskDetailModal, AttachmentSidebar...
│   │   └── api/client.ts        ← Axios API klient
│   ├── .env.production          ← VITE_API_URL pre produkčný build
│   └── vercel.json              ← SPA rewrite pravidlá
└── obsidian-vault/              ← Táto dokumentácia
```

## Súvisiace poznámky

### v1.x
- [[01 - Architektúra]]
- [[02 - CPM Engine]]
- [[03 - Databáza & Repo]]
- [[04 - UI Obrazovky]]
- [[05 - Gantt & Network]]
- [[06 - Team Management]]
- [[07 - Bugy & Opravy]]
- [[09 - PDF Export]]
- [[10 - v1.1 Featury]]
- [[11 - Supabase Migrácia]]

### v2.0
- [[08 - Roadmap v2.0]]
- [[12 - v2.0 Web Aplikácia]]
- [[13 - Prílohy & Sieťový Diagram]]
- [[14 - Klientský Modul]]
