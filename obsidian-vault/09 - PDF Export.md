# 📄 PDF Export

#export #pdf #reportlab

## Prehľad

Funkcia umožňuje exportovať kompletný report projektu do **PDF súboru** jedným kliknutím.

**Súbor:** `logic/export_manager.py`
**Knižnica:** `reportlab 4.x`

## Čo obsahuje vygenerovaný PDF

1. **Farebný banner** — názov projektu + dátum generovania
2. **6 štatistických kariet** — Progress%, Dokončené, Kritická cesta, Trvanie, Oneskorenie, Zdravie
3. **Upozornenia** — blokované úlohy, oneskorenia, CPM chyby (ak sú)
4. **Gantt Chart** — vygenerovaný ako PNG a vložený do PDF
5. **Tabuľka úloh** — Názov, Stav, Trvanie, ES, EF, Float, Kategória, Kritická
6. **Kritická cesta** — textový reťazec Úloha A → B → C
7. **Footer** — ManagmentApp v1.0 + dátum + projekt

## Použitie v UI

V `project_detail.py` — tlačidlo **📄 Export PDF** v hlavičke vedľa "+ Pridať úlohu".

```python
# Po kliknutí:
# 1. Otvorí file dialog (asksaveasfilename)
# 2. Recalculuje CPM
# 3. Zavolá export_project_pdf()
# 4. Zobrazí messagebox (úspech / chyba)
# 5. Automaticky otvorí PDF (os.startfile)
```

## Hlavná funkcia

```python
export_project_pdf(
    project_name: str,
    project_id: int,
    cpm_result: CPMResult,
    output_path: str,
) -> bool
```

## Gantt ako obrázok

```python
_gantt_image(cpm_result) -> io.BytesIO | None
```

Generuje matplotlib figure do pamäte (BytesIO), bez ukladania na disk.
Potom sa vloží do PDF cez `reportlab.platypus.Image`.

## Farby (reportlab)

| Konštanta | Hex | Použitie |
|-----------|-----|----------|
| `RL_PRIMARY` | `#1976D2` | Banner, header tabuľky |
| `RL_DANGER` | `#D32F2F` | Kritické riadky, oneskorenie |
| `RL_SUCCESS` | `#388E3C` | Dokončené, zdravý projekt |
| `RL_BG_CRIT` | `#FFEBEE` | Pozadie kritických riadkov |
| `RL_BG_ROW` | `#ECEFF1` | Striedavé riadky tabuľky |

## Inštalácia

```bash
pip install reportlab
```

Pridaj do `requirements.txt`:
```
reportlab>=4.0.0
```

## Súvisiace

- [[02 - CPM Engine]]
- [[04 - UI Obrazovky#Project Detail]]
- [[05 - Gantt & Network]]
- [[08 - Roadmap v2.0#Reporting & Export]]
