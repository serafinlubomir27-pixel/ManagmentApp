"""Meranie výkonu CPM enginu v závislosti od veľkosti siete.

Generuje sa reťazec úloh s priečnymi väzbami, aby sieť nebola triviálna.
Každá veľkosť sa meria opakovane, reportuje sa medián.
"""
import json
import os
import platform
import statistics
import sys
import time

sys.path.insert(0, r'C:\Users\loker\PyCharmMiscProject\ManagmentApp')
from logic.cpm_engine import CPMTask, calculate_cpm  # noqa: E402

SIZES = [10, 25, 50, 100, 250, 500, 1000]
REPEATS = 15


def make_network(n: int) -> list[CPMTask]:
    """Reťazec s priečnymi väzbami — každá úloha závisí od predchádzajúcej
    a od úlohy o tri pozície späť, takže vznikne vetvenie aj zbiehanie."""
    tasks = []
    for i in range(1, n + 1):
        deps = []
        if i > 1:
            deps.append(i - 1)
        if i > 3:
            deps.append(i - 3)
        tasks.append(CPMTask(id=i, name=f'T{i}', duration=(i % 7) + 1, dependencies=deps))
    return tasks


def main() -> None:
    rows = []
    for n in SIZES:
        times = []
        for _ in range(REPEATS):
            tasks = make_network(n)
            t0 = time.perf_counter()
            res = calculate_cpm(tasks)
            times.append((time.perf_counter() - t0) * 1000)
        assert res.is_valid, f'sieť {n} vyšla ako neplatná'
        rows.append({
            'tasks': n,
            'median_ms': round(statistics.median(times), 2),
            'min_ms': round(min(times), 2),
            'max_ms': round(max(times), 2),
            'duration': res.project_duration,
            'critical_count': len(res.critical_path),
        })

    env = {
        'python': platform.python_version(),
        'system': f'{platform.system()} {platform.release()}',
        'machine': platform.machine(),
        'processor': platform.processor(),
        'repeats': REPEATS,
    }
    dst = os.path.join(os.environ['TEMP'], 'cpm_bench.json')
    json.dump({'env': env, 'rows': rows}, open(dst, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f"{'úloh':>6} {'medián [ms]':>12} {'min':>8} {'max':>8} {'kritických':>11}")
    for r in rows:
        print(f"{r['tasks']:>6} {r['median_ms']:>12} {r['min_ms']:>8} "
              f"{r['max_ms']:>8} {r['critical_count']:>11}")
    print()
    print('prostredie:', env['system'], '|', env['machine'], '| Python', env['python'])
    print('uložené:', dst)


if __name__ == '__main__':
    main()
