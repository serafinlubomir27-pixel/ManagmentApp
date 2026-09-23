"""Overenie CPM enginu na referenčných príkladoch s ručne odvodenými hodnotami.

Každý prípad má očakávané hodnoty vypočítané nezávisle od implementácie, takže
test skutočne overuje algoritmus, nie sám seba. Výstup ide do JSON, z ktorého
sa sádže kapitola 7.3.
"""
import json
import os
import sys

sys.path.insert(0, r'C:\Users\loker\PyCharmMiscProject\ManagmentApp')
from logic.cpm_engine import CPMTask, calculate_cpm, detect_cycle  # noqa: E402

# Prípad: (názov, zámer, úlohy [(id, meno, trvanie, závislosti)], očakávanie)
CASES = [
    (
        'R1 — lineárna postupnosť',
        'Základné overenie dopredného a spätného prechodu bez vetvenia.',
        [(1, 'A', 3, []), (2, 'B', 2, [1]), (3, 'C', 4, [2])],
        {'duration': 9, 'critical': ['A', 'B', 'C'],
         'floats': {'A': 0, 'B': 0, 'C': 0}},
    ),
    (
        'R2 — vetvenie a zbiehanie',
        'Paralelné vetvy rôznej dĺžky; kratšia vetva musí dostať nenulovú rezervu.',
        [(1, 'A', 3, []), (2, 'B', 2, [1]), (3, 'C', 4, [1]), (4, 'D', 1, [2, 3])],
        {'duration': 8, 'critical': ['A', 'C', 'D'],
         'floats': {'A': 0, 'B': 2, 'C': 0, 'D': 0}},
    ),
    (
        'R3 — dve kritické cesty',
        'Dve vetvy rovnakej dĺžky — obe musia vyjsť ako kritické.',
        [(1, 'A', 2, []), (2, 'B', 5, [1]), (3, 'C', 5, [1]), (4, 'D', 3, [2, 3])],
        {'duration': 10, 'critical': ['A', 'B', 'C', 'D'],
         'floats': {'A': 0, 'B': 0, 'C': 0, 'D': 0}},
    ),
    (
        'R4 — izolovaná úloha',
        'Úloha bez väzieb nesmie predĺžiť projekt ani spadnúť na kritickú cestu, '
        'ak je kratšia než kritická cesta.',
        [(1, 'A', 4, []), (2, 'B', 4, [1]), (3, 'X', 2, [])],
        {'duration': 8, 'critical': ['A', 'B'],
         'floats': {'A': 0, 'B': 0, 'X': 6}},
    ),
    (
        'R5 — izolovaná úloha dlhšia než cesta',
        'Samostatná úloha určuje trvanie projektu a sama je kritická.',
        [(1, 'A', 2, []), (2, 'B', 2, [1]), (3, 'X', 9, [])],
        {'duration': 9, 'critical': ['X'],
         'floats': {'A': 5, 'B': 5, 'X': 0}},
    ),
    (
        'R6 — cyklus v sieti',
        'Cyklická závislosť musí byť odhalená a výpočet odmietnutý.',
        [(1, 'A', 2, [3]), (2, 'B', 2, [1]), (3, 'C', 2, [2])],
        {'cycle': True},
    ),
    (
        'R7 — závislosť mimo projektu',
        'Odkaz na neexistujúcu úlohu sa musí ignorovať, nie zhodiť výpočet.',
        [(1, 'A', 3, [99]), (2, 'B', 2, [1])],
        {'duration': 5, 'critical': ['A', 'B'],
         'floats': {'A': 0, 'B': 0}},
    ),
]


def run_case(tasks_spec):
    tasks = [CPMTask(id=i, name=n, duration=d, dependencies=list(deps))
             for i, n, d, deps in tasks_spec]
    return tasks, calculate_cpm(tasks)


def main() -> None:
    results = []
    for name, intent, spec, exp in CASES:
        tasks, res = run_case(spec)
        by_id = {t.id: t for t in res.tasks}

        if exp.get('cycle'):
            cycle = detect_cycle([CPMTask(id=i, name=n, duration=d, dependencies=list(dp))
                                  for i, n, d, dp in spec])
            ok = (cycle is not None) and (not res.is_valid)
            results.append({
                'name': name, 'intent': intent, 'cycle_case': True,
                'detected': cycle is not None,
                'is_valid': res.is_valid,
                'errors': res.errors,
                'ok': ok,
                'rows': [],
            })
            continue

        crit = sorted(by_id[i].name for i in res.critical_path)
        rows = []
        all_ok = True
        for t in sorted(res.tasks, key=lambda x: x.id):
            exp_f = exp['floats'][t.name]
            row_ok = t.total_float == exp_f and t.is_critical == (exp_f == 0)
            all_ok &= row_ok
            rows.append({
                'name': t.name, 'duration': t.duration,
                'es': t.es, 'ef': t.ef, 'ls': t.ls, 'lf': t.lf,
                'tf': t.total_float, 'expected_tf': exp_f,
                'critical': t.is_critical, 'ok': row_ok,
            })
        dur_ok = res.project_duration == exp['duration']
        crit_ok = crit == sorted(exp['critical'])
        all_ok &= dur_ok and crit_ok

        results.append({
            'name': name, 'intent': intent, 'cycle_case': False,
            'duration': res.project_duration, 'expected_duration': exp['duration'],
            'critical': crit, 'expected_critical': sorted(exp['critical']),
            'rows': rows, 'ok': all_ok,
        })

    dst = os.path.join(os.environ['TEMP'], 'cpm_verify.json')
    json.dump(results, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    for r in results:
        mark = 'OK   ' if r['ok'] else 'CHYBA'
        if r['cycle_case']:
            print(f"{mark} {r['name']}: cyklus odhalený={r['detected']}, is_valid={r['is_valid']}")
        else:
            print(f"{mark} {r['name']}: trvanie {r['duration']}"
                  f" (oč. {r['expected_duration']}), kritická cesta {'-'.join(r['critical'])}")
    print()
    print('prešlo:', sum(1 for r in results if r['ok']), '/', len(results))
    print('uložené:', dst)


if __name__ == '__main__':
    main()
