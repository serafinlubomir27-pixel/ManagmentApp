# 📊 Gantt Chart & CPM Network Diagram

#vizualizácia #matplotlib #gantt #network #cpm

Oba grafy sú postavené na **matplotlib** vloženej do CustomTkinter cez `FigureCanvasTkAgg`.

## Gantt Chart

**Súbor:** `ui/screens/gantt_chart.py`
**Trieda:** `GanttChartView(ctk.CTkFrame)`

### Ako funguje

Horizontálny bar chart kde každá úloha = pruh.

```
Pozícia = ES * dayWidth
Šírka   = duration * dayWidth
```

Obsah je zoradený podľa `ES` (najskôr začínajúce úlohy hore).

### Farby pruhov

| Podmienka | Farba |
|-----------|-------|
| `status == completed` | 🟢 `#66BB6A` |
| `id in critical_path` | 🔴 `#E53935` |
| ostatné | 🔵 `#1976D2` |

### Float vizualizácia

Ak `total_float > 0`, za hlavným pruhom sa zobrazí **svetlomodrý polotransparentný pruh** — ukazuje časovú rezervu.

```
[══════ task ══════][░░░░ float ░░░░]
  ES          EF          EF+float
```

### Dependency šípky

`FancyArrowPatch` medzi `EF` predchodcu a `ES` nasledovníka.
- Kritická hrana: plná červená
- Nekritická: šedá

### Legenda

Automaticky generovaná: Kritická cesta / Normálna úloha / Dokončená / Float

### Cleanup

```python
def destroy(self):
    """Override CTkFrame.destroy() — uvoľní matplotlib resources."""
    if self._mpl_canvas:
        self._mpl_canvas.get_tk_widget().destroy()
    if self._fig:
        plt.close(self._fig)
    super().destroy()
```

> ⚠️ Musí sa používať `self._mpl_canvas` — nie `self._canvas`!
> CTkFrame interne používa `self._canvas` pre vlastný Tk canvas.
> Konflikt spôsoboval `AttributeError: 'FigureCanvasTkAgg' object has no attribute 'bind'`.
> Pozri [[07 - Bugy & Opravy#matplotlib canvas conflict]].

---

## CPM Network Diagram

**Súbor:** `ui/screens/network_diagram.py`
**Trieda:** `NetworkDiagramView(ctk.CTkFrame)`

### Topologické levely

```python
@staticmethod
def _compute_levels(tasks) → dict[int, int]:
    # Rekurzívne: level(t) = max(level(dep)) + 1
    # Úlohy bez dependencies → level 0
```

```
Level 0    Level 1    Level 2    Level 3
[Planning] → [Design] → [Frontend] → [Testing]
           → [Backend] ──────────────────↗
```

### Uzol — 4-kvadrantový CPM box

```
┌─────────────────────┐
│   Názov úlohy       │
├─────────┬───────────┤
│  ES: 0  │  EF: 3   │
├─────────┼───────────┤
│  LS: 0  │  LF: 3   │
├─────────┴───────────┤
│ F:0         3d      │
└─────────────────────┘
```

- `ES/EF` — biela (svetlá)
- `LS/LF` — šedá (dimmed)
- `F:0` — červená (kritická), tyrkysová (nekritická)
- Delay badge `+Xd` — oranžová

### Farby uzlov

| Podmienka | Pozadie | Border |
|-----------|---------|--------|
| `is_critical` | tmavočervená | `#E53935` |
| `completed` | tmavozelená | `#66BB6A` |
| ostatné | `#37474F` | `#546E7A` |

### Hrany (šípky)

`FancyArrowPatch` s `connectionstyle="arc3,rad=0.08"`

| Typ hrany | Farba | Čiara |
|-----------|-------|-------|
| Kritická | `#E53935` | plná, 2px |
| Nekritická | `#78909C` | prerušovaná, 1px |

### Cleanup

Rovnaký `destroy()` override pattern ako Gantt — pozri [[07 - Bugy & Opravy#matplotlib canvas conflict]].

---

## Inšpirácia — Lovable (PathFlow)

Oba grafy sú inšpirované webovou verziou PathFlow:
- `GanttChart.tsx` — 40px/deň, float vizualizácia, hover tooltips
- `NetworkDiagram.tsx` — Bézier hrany, 4-kvadrantové uzly, SVG markers

Pythonovská implementácia je ekvivalentná, prispôsobená pre matplotlib/Tkinter.

## Súvisiace

- [[02 - CPM Engine]]
- [[04 - UI Obrazovky#Project Detail]]
- [[08 - Roadmap v2.0]]
