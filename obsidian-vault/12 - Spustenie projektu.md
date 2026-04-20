# Spustenie projektu — ManagmentApp

## Predpoklady
- Python 3.12+
- Node.js 22 LTS
- `.env` súbor v koreni projektu (obsahuje `DB_BACKEND`, `DATABASE_URL`, `JWT_SECRET`)

---

## Backend (FastAPI + uvicorn)

```powershell
cd C:\Users\loker\PyCharmMiscProject\ManagmentApp
py -m uvicorn backend.main:app --reload
```

- Beží na: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Frontend (React + Vite)

```powershell
cd C:\Users\loker\PyCharmMiscProject\ManagmentApp\frontend
npm run dev
```

- Beží na: http://localhost:5173
- Proxy `/api` → `http://127.0.0.1:8000` (nakonfigurovaný vo Vite)

---

## Oboje naraz (dva terminály)

**Terminál 1 — Backend:**
```powershell
cd C:\Users\loker\PyCharmMiscProject\ManagmentApp
py -m uvicorn backend.main:app --reload
```

**Terminál 2 — Frontend:**
```powershell
cd C:\Users\loker\PyCharmMiscProject\ManagmentApp\frontend
npm run dev
```

---

## Prihlasovacie údaje (vývojové)

| Používateľ | Heslo    | Rola  |
|------------|----------|-------|
| admin      | admin123 | admin |

---

## Databáza

- **Backend:** PostgreSQL (Supabase)
- **Supabase projekt:** `nphqwfgglmiaqacdxwne`
- **Table Editor:** https://supabase.com/dashboard/project/nphqwfgglmiaqacdxwne/editor

---

## Testovanie backendu bez frontendu

Swagger UI → http://127.0.0.1:8000/docs  
1. `POST /auth/login` → zadaj `username=admin`, `password=admin123`
2. Skopíruj `access_token`
3. Klikni **Authorize** (vpravo hore) → vlož token

---

## Poznámky

- `.env` súbor **nesmie ísť do gitu** (je v `.gitignore`)
- Pri zmene routerov stačí uložiť — `--reload` reštartuje automaticky
- Port 8000 musí byť voľný — ak nie, ukonči predchádzajúci proces
