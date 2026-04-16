# 🐛 Bugy & Opravy

#bugy #debugging #opravy

Záznam všetkých nájdených bugov, ich príčin a riešení.

---

## KeyError 0

**Kedy:** Po zavedení [[01 - Architektúra#Repository Pattern|Repository Pattern]]
**Kde:** `project_view.py`, `team_view.py`, `project_detail.py`

### Príčina

Repo funkcie začali vracať `dict` (cez `sqlite3.Row` → `rows_to_dicts()`), ale UI kód stále pristupoval cez numerický index:

```python
# STARÝ KÓD — padá s KeyError: 0
self.user_id = user_data[0]
self.user_role = user_data[4]

# OPRAVENÝ KÓD
self.user_id = user_data["id"]
self.user_role = user_data["role"]
```

### Postihnuté súbory

| Súbor | Riadok | Starý kód | Nový kód |
|-------|--------|-----------|----------|
| `project_view.py` | 18 | `user_data[0]` | `user_data["id"]` |
| `project_view.py` | 55 | `pid, name, desc, status = project_data` | `isinstance()` check |
| `team_view.py` | 8–9 | `user_data[0]`, `user_data[4]` | `user_data["id"]`, `user_data["role"]` |
| `team_view.py` | 49 | `mid, name, role, username = member_data` | `member.get("id")` atď. |

### Riešenie — defensive pattern

```python
# Bezpečný prístup — funguje pre dict aj tuple (legacy)
self.user_id = user_data["id"] if isinstance(user_data, dict) else user_data[0]
```

---

## Invalid color name

**Error:** `_tkinter.TclError: invalid color name "#00897B22"`

**Kedy:** Otvorenie TeamView, ProjectDetail
**Kde:** `team_view.py:186`, `project_detail.py:275,372,398`

### Príčina

Tkinter **nepodporuje** 8-znakové hex farby (`#RRGGBBAA`) — to je CSS/HTML formát.

```python
# NEFUNGUJE v Tkinter:
fg_color=role_color + "22"    # napr. "#00897B22"
fg_color=DANGER + "33"        # napr. "#D32F2F33"
```

### Riešenie — color_blend()

Pridaná do `ui/theme.py`:

```python
def color_blend(hex_color: str, alpha: float = 0.13, bg: str = BG_MAIN) -> str:
    """Blend hex_color with bg — nahrádza CSS rgba() pre Tkinter."""
    r1, g1, b1 = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
    r2, g2, b2 = int(bg[1:3],16), int(bg[3:5],16), int(bg[5:7],16)
    r = int(r1 * alpha + r2 * (1 - alpha))
    g = int(g1 * alpha + g2 * (1 - alpha))
    b = int(b1 * alpha + b2 * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"

# Použitie:
fg_color=color_blend(role_color)        # ~13% alfa
fg_color=color_blend(DANGER, 0.2)       # ~20% alfa
```

---

## CTkFrame transparent border

**Error:** `ValueError: transparency not allowed`

**Kde:** `calendar_view.py:192`

### Príčina

```python
# NEFUNGUJE:
border_color = SELECTED_BORDER if is_selected else "transparent"
```

CTkFrame akceptuje `"transparent"` len ako `fg_color`, nie ako `border_color`.

### Riešenie

```python
# Podmienene nastav border_color len keď je selected:
cell_kwargs = {"fg_color": BG_CARD, "corner_radius": 4}
if is_selected:
    cell_kwargs["border_color"] = SELECTED_BORDER
    cell_kwargs["border_width"] = 2

cell = ctk.CTkFrame(parent, **cell_kwargs)
```

---

## Kalendár — nekonzistentné výšky riadkov

**Kde:** `calendar_view.py`

### Príčina

Grid riadky s `weight=1` ale bez `uniform` constraint — riadky s viac widgetmi boli vyššie.

### Riešenie

```python
for row in range(6):
    grid_frame.grid_rowconfigure(row, weight=1, uniform="cal_row")

CELL_HEIGHT = 60  # fixná výška bunky
```

---

## Kalendár — blikanie pri kliknutí

**Kde:** `calendar_view.py`

### Príčina

`_on_day_click()` volal `_render_calendar()` ktorý zničil a znovu vytvoril **všetky widgety** = viditeľné blikanie.

### Riešenie

```python
def _update_selection(self, old_day, new_day):
    """Len zmení border na 2 bunkách — žiadne re-renderovanie."""
    if old_day and old_day in self._day_cells:
        self._day_cells[old_day].configure(border_width=0)
    if new_day in self._day_cells:
        self._day_cells[new_day].configure(border_width=2, border_color=SELECTED_BORDER)
```

---

## Prihlásenie — admin/admin123 nefungovalo

**Kedy:** Po refactore na SHA-256 heslá

### Príčina

Existujúci admin v DB mal uložené **plaintext** heslo `"admin123"`. Nový kód hashoval pri porovnaní → hash(`"admin123"`) ≠ `"admin123"`.

### Riešenie

1. Manuálny UPDATE v DB
2. Trvalý fix v `setup.py` — migrácia pri každom štarte:

```python
plain_users = cursor.execute(
    "SELECT id, password FROM users WHERE length(password) != 64"
).fetchall()
for uid, pwd in plain_users:
    hashed = hashlib.sha256(pwd.encode()).hexdigest()
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, uid))
```

---

## matplotlib canvas conflict

**Error:** `AttributeError: 'FigureCanvasTkAgg' object has no attribute 'bind'`

**Kedy:** Otvorenie záložky Gantt Chart alebo CPM Network v ProjectDetail
**Kde:** `gantt_chart.py:48`, `network_diagram.py:51`

### Príčina

`CTkFrame` interne udržuje **vlastný Tk canvas** v atribúte `self._canvas`.
Ak uložíme matplotlib `FigureCanvasTkAgg` do rovnakého mena:

```python
self._canvas = FigureCanvasTkAgg(fig, master=self)  # ← prepíše CTkFrame._canvas!
```

...a potom zavoláme `self.bind("<Destroy>", ...)`:

```python
# CTkFrame.bind() interne volá self._canvas.bind(...)
# ale self._canvas je teraz FigureCanvasTkAgg, ktorý nemá .bind()
```

→ crash.

### Riešenie — dve zmeny

**1. Premenovať atribút:**

```python
# Všade nahradiť:
self._canvas = FigureCanvasTkAgg(...)
# Na:
self._mpl_canvas = FigureCanvasTkAgg(...)
```

**2. Nahradiť `bind("<Destroy>")` za `destroy()` override:**

```python
# STARÁ (nefungujúca) metóda:
self.bind("<Destroy>", self._on_destroy)

# NOVÁ (správna) metóda:
def destroy(self):
    if self._mpl_canvas:
        try:
            self._mpl_canvas.get_tk_widget().destroy()
        except Exception:
            pass
    if self._fig:
        plt.close(self._fig)
    super().destroy()
```

### Postihnuté súbory

| Súbor | Oprava |
|-------|--------|
| `gantt_chart.py` | `_canvas` → `_mpl_canvas` (replace_all), destroy() override |
| `network_diagram.py` | `_canvas` → `_mpl_canvas` (replace_all), destroy() override |

---

## matplotlib memory leak

**Kde:** `dashboard.py`

### Príčina

Každé otvorenie Dashboardu vytvorilo novú matplotlib figúru, ale stará sa nezavrela.

### Riešenie

```python
def _on_destroy(self, event):
    if event.widget is self:
        self._chart_canvas.get_tk_widget().destroy()
        plt.close("all")
```

Rovnaký pattern v `gantt_chart.py` a `network_diagram.py`.

---

---

## pack vs grid konflikt v dashboard.py

**Error:** `_tkinter.TclError: cannot use geometry manager pack inside ... which already has slaves managed by grid`

**Kedy:** Po pridaní `CTkScrollableFrame` do dashboardu (responsiveness refactor)
**Kde:** `dashboard.py._build_donut_section()`

### Príčina

`chart_frame` používal `.grid()` pre label (row=0), ale matplotlib canvas bol embedovaný cez `.pack()` po refactore.

### Riešenie

```python
# Zmeniť z:
self._chart_canvas.get_tk_widget().pack(fill="x", ...)
# Na:
self._chart_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", ...)
# + pridať:
chart_frame.grid_rowconfigure(1, weight=1)
```

---

## AttributeError: content_area

**Error:** `AttributeError: '_tkinter.tkapp' object has no attribute 'content_area'`

**Kedy:** Keď DashboardScreen crashne pri inicializácii, každý ďalší klik na sidebar vyhodí tento error.

### Príčina

`self.content_area` sa nastavoval až v `show_main_layout()`. Ak Dashboard crashol pred tým — atribút neexistoval.

### Riešenie

```python
# V MainApp.__init__() PRED show_login():
self.content_area = None   # defensive init

# V handle_navigation():
if getattr(self, 'content_area', None):   # namiesto if self.content_area:
    self.content_area.destroy()
```

---

## Unit testy — in-memory SQLite a conn.close()

**Problém:** Repozitáre volajú `conn.close()` v `finally` blokoch. Pre in-memory DB to zničí databázu.

**Riešenie:** `_NoCloseConn` wrapper — deleguje všetko okrem `.close()`:

```python
class _NoCloseConn:
    def __init__(self, conn): self._conn = conn
    def close(self): pass   # no-op
    def __getattr__(self, name): return getattr(self._conn, name)
```

**Ďalší problém:** Repos používajú `from repositories.base_repo import get_connection` — lokálna kópia mena. Patch `base_repo.get_connection` nestačí.

**Riešenie:** Patchovať každý modul priamo:
```python
monkeypatch.setattr("repositories.user_repo.get_connection", make_conn)
monkeypatch.setattr("repositories.project_repo.get_connection", make_conn)
monkeypatch.setattr("repositories.task_repo.get_connection", make_conn)
```

---

## Súvisiace

- [[01 - Architektúra]]
- [[03 - Databáza & Repo]]
- [[04 - UI Obrazovky]]
