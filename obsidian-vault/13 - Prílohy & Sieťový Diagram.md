# 📎 Fáza 1 & 2 — Prílohy súborov + Interaktívny sieťový diagram

#prílohy #modal #diagram #faza1 #faza2

## Fáza 1 — Prílohy súborov

### Problém
V pôvodnom v2.0 existovala len tabuľka `task_attachments` bez viditeľnosti a bez príloh na úrovni projektu. Nebolo možné prikladať dokumenty ku celému projektu ani kontrolovať kto čo vidí.

### Riešenie

#### Dátový model

```sql
-- Rozšírenie existujúcej tabuľky
ALTER TABLE task_attachments ADD COLUMN visibility TEXT DEFAULT 'team'

-- Nová tabuľka pre projektové prílohy
CREATE TABLE project_attachments (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  file_name   TEXT NOT NULL,
  file_path   TEXT NOT NULL,
  file_size   INTEGER,
  mime_type   TEXT,
  visibility  TEXT DEFAULT 'team',  -- 'team' | 'managers' | 'private'
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Tri úrovne viditeľnosti

| Úroveň | Ikona | Kto vidí |
|--------|-------|----------|
| `team` | 👥 Tím | Všetci členovia projektu |
| `managers` | 👔 Manažéri | Len admin a manager rola |
| `private` | 🔒 Len ja | Iba nahrávateľ |

Filtrovacia logika v `attachment_repo.py`:
```python
def _visibility_filter(user_role, user_id):
    if user_role in ("admin", "manager"):
        # vidí team + managers + vlastné private
        return "AND (a.visibility IN ('team','managers') OR a.user_id = ?)", [user_id]
    else:
        # vidí len team + vlastné private
        return "AND (a.visibility = 'team' OR a.user_id = ?)", [user_id]
```

#### API endpointy

| Metóda | Endpoint | Popis |
|--------|----------|-------|
| POST | `/projects/{id}/attachments` | Nahratie súboru (multipart) |
| GET | `/projects/{id}/attachments` | Zoznam príloh projektu |
| GET | `/projects/{id}/all-attachments` | Projektové + taskové prílohy |
| PATCH | `/project-attachments/{id}/visibility` | Zmena viditeľnosti |
| DELETE | `/project-attachments/{id}` | Zmazanie (vlastník alebo manažér) |
| POST | `/tasks/{id}/attachments` | Nahratie prílohy k tasku |
| GET | `/tasks/{id}/attachments` | Zoznam príloh tasku |
| PATCH | `/task-attachments/{id}/visibility` | Zmena viditeľnosti |
| DELETE | `/task-attachments/{id}` | Zmazanie |

#### Frontend komponenty

```
AttachmentSidebar.tsx
  └── AttachmentList.tsx        ← riadky so súbormi, badge visibility
  └── FileUploadDropzone.tsx    ← drag & drop + VisibilitySelector
        └── VisibilitySelector.tsx

ProjectDetailPage.tsx (tasks tab):
  ├── [task list — flex-1]
  └── [AttachmentSidebar — w-64]

TaskAttachmentSection (v expandovanom riadku tasku):
  ├── AttachmentList
  └── FileUploadDropzone
```

**Farebné kódovanie viditeľnosti:**
- `team` → zelená
- `managers` → fialová
- `private` → jantárová

Klik na badge cykluje viditeľnosť: `team → managers → private → team`

---

## Fáza 2 — Interaktívny sieťový diagram

### Problém
Uzly v `NetworkDiagram.tsx` boli len vizuálne. Na editáciu tasku bolo nutné opustiť diagram a ísť do task listu.

### Riešenie

**Klik na uzol → `TaskDetailModal`** (bez navigácie preč z diagramu)

#### Zmeny v NetworkDiagram.tsx

```tsx
const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)

// Na každom uzle <g>:
onClick={() => setSelectedTaskId(t.id)}
style={{ cursor: 'pointer' }}

// Modal renderovaný mimo SVG (React fragment):
return (
  <>
    <svg>...</svg>
    {selectedTaskId && (
      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        teamMembers={teamMembers}
      />
    )}
  </>
)
```

> ⚠️ Modal musí byť **mimo** `<svg>` elementu — HTML elementy (div, input) nie sú platné deti SVG.

#### TaskDetailModal — layout

```
┌─────────────────────────────────────────────────────┐
│ [Názov tasku]                   [Priorita] [✕]      │
├──────────────────────────┬──────────────────────────┤
│ ĽAVÝ STĹPEC              │ PRAVÝ STĹPEC             │
│                          │                          │
│ Status      [dropdown]   │ Komentáre                │
│ Pridelený   [select]     │ [zoznam komentárov]      │
│ Deadline    [date]       │ [textarea + Odoslať]     │
│ Priorita    [select]     │                          │
│                          │ Súbory                   │
│ Popis [textarea]         │ [AttachmentList]         │
│                          │ [FileUploadDropzone]     │
│ CPM info (read-only):    │                          │
│ ES / EF / Float / Krit.  │                          │
└──────────────────────────┴──────────────────────────┘
```

#### Nový backend endpoint

`GET /tasks/{task_id}` — vracia plný detail tasku vrátane `assigned_username`, `assigned_full_name` (JOIN s users tabuľkou).

#### Interakcie
- **Escape** alebo klik na backdrop → zatvoriť modal
- Editácia cez existujúci `PATCH /tasks/{id}`
- Komentáre cez `GET/POST /tasks/{id}/comments`
- Prílohy cez `GET/POST/DELETE /tasks/{id}/attachments`
- Polia `Status`, `Pridelený`, `Deadline`, `Priorita` — len manažér/admin (`disabled={!isManager}`)

---

## Súvisiace

- [[00 - Prehľad projektu]]
- [[12 - v2.0 Web Aplikácia]]
- [[14 - Klientský Modul]]
- [[05 - Gantt & Network]]
