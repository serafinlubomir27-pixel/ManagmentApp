# ⚡ CPM Engine (Critical Path Method)

#cpm #algoritmus #python #grafy

## Čo je CPM

Critical Path Method je technika projektového manažmentu, ktorá identifikuje **najdlhšiu cestu** cez sieť závislých úloh — to je **kritická cesta**. Každé oneskorenie na nej predĺži celý projekt.

## Súbory

| Súbor | Popis |
|-------|-------|
| `logic/cpm_engine.py` | Čistý algoritmus — žiadna DB, žiadne UI |
| `logic/cpm_manager.py` | Bridge: načíta z DB → spustí engine → uloží výsledky |

## Dátové štruktúry

```python
@dataclass
class CPMTask:
    id: int
    name: str
    duration: int          # trvanie v dňoch
    dependencies: list[int] # ID úloh, na ktorých závisí
    delay_days: int         # manuálne oneskorenie
    status: str             # pending / in_progress / completed / blocked
    # Vypočítané CPM polia:
    es: int   # Earliest Start
    ef: int   # Earliest Finish
    ls: int   # Latest Start
    lf: int   # Latest Finish
    total_float: int   # časová rezerva
    is_critical: bool  # True ak je na kritickej ceste

@dataclass
class CPMResult:
    tasks: list[CPMTask]
    critical_path: list[int]           # IDs úloh na kritickej ceste
    project_duration: int              # celkové trvanie (s oneskoreniami)
    project_duration_without_delays: int
    total_project_delay: int
    is_valid: bool
    errors: list[str]
```

## Algoritmus krok za krokom

### 1. Detekcia cyklov (DFS)
```python
detect_cycle(tasks) → list[int] | None
```
Prechádza graf do hĺbky. Ak nájde spätnú hranu (GRAY→GRAY), cyklus existuje.
Cyklus = neplatný plán → CPMResult(is_valid=False).

### 2. Topologické triedenie (Kahn)
```python
topological_sort(tasks) → list[CPMTask]
```
Triedi úlohy podľa závislostí — každá úloha príde za všetkými svojimi predchodcami.

### 3. Forward Pass (Dopredu)
```python
forward_pass(sorted_tasks) → None  # mutuje tasks
```
- Úloha bez dependencies: `ES = 0 + delay_days`
- Ostatné: `ES = max(EF predchodcov) + delay_days`
- `EF = ES + duration`

### 4. Backward Pass (Dozadu)
```python
backward_pass(sorted_tasks, project_duration) → None
```
- Posledná úloha: `LF = project_duration`
- Ostatné: `LF = min(LS nasledovníkov)`
- `LS = LF - duration`

### 5. Float a kritickosť
```python
total_float = ls - es
is_critical = (total_float == 0)
```

### 6. Baseline porovnanie
CPM sa spúšťa dvakrát:
1. S `delay_days` → `project_duration`
2. Bez `delay_days` → `project_duration_without_delays`

`total_project_delay = project_duration - project_duration_without_delays`

## Overený testovací prípad

```
A(3d) ──► B(2d) ──┐
│                  ▼
└─────► C(4d) ──► D(1d)
```

| Úloha | ES | EF | LS | LF | Float | Kritická |
|-------|----|----|----|----|-------|---------|
| A | 0 | 3 | 0 | 3 | 0 | ✅ |
| B | 3 | 5 | 5 | 7 | 2 | ❌ |
| C | 3 | 7 | 3 | 7 | 0 | ✅ |
| D | 7 | 8 | 7 | 8 | 0 | ✅ |

**Kritická cesta:** A → C → D = **8 dní**

## Health Score

```python
calculate_health_score(tasks, project_duration, planned_end_days)
→ (score: int, label: str)
```

| Podmienka | Penalizácia |
|-----------|-------------|
| Každá zablokovaná úloha | -10 |
| Kritická úloha po termíne | -15 |
| Každý deň sklzu projektu | -2 |
| Každý deň delay_days | -3 |

| Score | Label |
|-------|-------|
| ≥ 80 | 🟢 Healthy |
| ≥ 60 | 🟡 At Risk |
| < 60 | 🔴 Critical |

## Pomocné funkcie

```python
would_create_cycle(tasks, from_id, to_id) → bool
# Overí pred pridaním dependency, či nevznikne cyklus

calculate_dates(tasks, project_start: date) → dict[int, (date, date)]
# Prevedie ES/EF na reálne dátumy
```

## Vizualizácia

- [[05 - Gantt & Network#Gantt Chart]] — horizontálne pruhy podľa ES/EF
- [[05 - Gantt & Network#CPM Network Diagram]] — uzly s 4 kvadrantmi (ES/EF/LS/LF)

## Súvisiace

- [[03 - Databáza & Repo#CPM tabuľky]]
- [[04 - UI Obrazovky#Project Detail]]
- [[05 - Gantt & Network]]
