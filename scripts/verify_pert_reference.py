"""Overenie PERT enginu na referenčných príkladoch s ručne odvodenými hodnotami.

Očakávané hodnoty sú spočítané nezávisle od implementácie zo vzorcov:
    E = (a + 4m + b) / 6        σ = (b − a) / 6        V = σ²
    E_proj = Σ E_i,  V_proj = Σ V_i   (len úlohy na kritickej ceste)
    P(T ≤ D) = Φ((D − E_proj) / σ_proj)

Výstup ide do JSON, z ktorého sa sádže kapitola o overení PERT.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.cpm_engine import CPMTask  # noqa: E402
from logic.pert_engine import calculate_pert  # noqa: E402

TOL = 0.01


def phi(z: float) -> float:
    """Distribučná funkcia normálneho rozdelenia."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# (názov, zámer, úlohy [(id, meno, závislosti, a, m, b)], deadline)
CASES = [
    (
        'P1 — jedna úloha, symetrický odhad',
        'Overenie základných vzorcov. Pri symetrickom rozpätí sa očakávané '
        'trvanie rovná najpravdepodobnejšiemu.',
        [(1, 'A', [], 2.0, 4.0, 6.0)],
        None,
    ),
    (
        'P2 — jedna úloha, zošikmený odhad',
        'Pesimistický odhad je vzdialenejší než optimistický, takže očakávané '
        'trvanie musí byť vyššie než najpravdepodobnejšie.',
        [(1, 'A', [], 2.0, 4.0, 12.0)],
        None,
    ),
    (
        'P3 — lineárna postupnosť',
        'Sčítanie očakávaných trvaní a rozptylov pozdĺž kritickej cesty.',
        [(1, 'A', [], 1.0, 3.0, 5.0),
         (2, 'B', [1], 2.0, 4.0, 12.0),
         (3, 'C', [2], 3.0, 3.0, 3.0)],
        None,
    ),
    (
        'P4 — vetvenie, rozptyl len z kritickej cesty',
        'Nekritická vetva má rezervu, preto do rozptylu projektu nevstupuje.',
        [(1, 'A', [], 1.0, 2.0, 3.0),
         (2, 'B', [1], 1.0, 2.0, 9.0),
         (3, 'C', [1], 3.0, 5.0, 7.0),
         (4, 'D', [2, 3], 1.0, 1.0, 1.0)],
        None,
    ),
    (
        'P5 — pravdepodobnosť dodržania termínu',
        'Pre deadline rovný očakávanému trvaniu musí vyjsť 50 %; pre dlhší viac.',
        [(1, 'A', [], 2.0, 5.0, 8.0),
         (2, 'B', [1], 3.0, 6.0, 15.0)],
        14,
    ),
    (
        'P6 — nulová neistota',
        'Ak a = m = b, rozptyl je nulový a PERT musí dať rovnaký výsledok ako CPM.',
        [(1, 'A', [], 4.0, 4.0, 4.0),
         (2, 'B', [1], 6.0, 6.0, 6.0)],
        10,
    ),
]


def expected_for(tasks_spec, critical_names):
    """Ručný výpočet očakávaných hodnôt zo vzorcov."""
    rows, e_proj, v_proj = [], 0.0, 0.0
    for _id, name, _deps, a, m, b in tasks_spec:
        e = (a + 4 * m + b) / 6
        s = (b - a) / 6
        rows.append({'name': name, 'a': a, 'm': m, 'b': b,
                     'e': round(e, 3), 'sd': round(s, 3), 'var': round(s * s, 3)})
        if name in critical_names:
            e_proj += e
            v_proj += s * s
    return rows, e_proj, v_proj


def main() -> None:
    results = []
    for name, intent, spec, deadline in CASES:
        cpm_tasks = [CPMTask(id=i, name=n, duration=int(round(m)), dependencies=list(d))
                     for i, n, d, a, m, b in spec]
        pert_data = {i: (a, m, b) for i, n, d, a, m, b in spec}
        res = calculate_pert(cpm_tasks, pert_data, deadline_days=deadline)

        by_id = {t.id: t for t in res.cpm_result.tasks}
        crit_names = {by_id[i].name for i in res.critical_path_ids}
        exp_rows, exp_e, exp_v = expected_for(spec, crit_names)
        exp_sd = math.sqrt(exp_v)

        got = {t.name: t for t in res.pert_tasks}
        rows, ok = [], True
        for er in exp_rows:
            g = got[er['name']]
            row_ok = (abs(g.pert_expected - er['e']) < TOL
                      and abs(g.pert_std_dev - er['sd']) < TOL
                      and abs(g.pert_variance - er['var']) < TOL)
            ok &= row_ok
            rows.append({**er,
                         'got_e': round(g.pert_expected, 3),
                         'got_sd': round(g.pert_std_dev, 3),
                         'got_var': round(g.pert_variance, 3),
                         'critical': er['name'] in crit_names,
                         'ok': row_ok})

        e_ok = abs(res.project_expected_duration - exp_e) < TOL
        sd_ok = abs(res.project_std_dev - exp_sd) < TOL
        ok &= e_ok and sd_ok

        prob = None
        if deadline is not None:
            exp_p = 1.0 if exp_sd == 0 and deadline >= exp_e else (
                0.0 if exp_sd == 0 else phi((deadline - exp_e) / exp_sd))
            got_p = res.probability_by_deadline.get(deadline)
            p_ok = got_p is not None and abs(got_p - exp_p) < 0.02
            ok &= p_ok
            prob = {'deadline': deadline, 'expected': round(exp_p, 4),
                    'got': round(got_p, 4) if got_p is not None else None, 'ok': p_ok}

        results.append({
            'name': name, 'intent': intent, 'rows': rows,
            'critical': sorted(crit_names),
            'e_proj': round(exp_e, 3), 'got_e_proj': round(res.project_expected_duration, 3),
            'sd_proj': round(exp_sd, 3), 'got_sd_proj': round(res.project_std_dev, 3),
            'prob': prob, 'ok': ok,
        })

    dst = os.path.join(os.environ['TEMP'], 'pert_verify.json')
    json.dump(results, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    for r in results:
        mark = 'OK   ' if r['ok'] else 'CHYBA'
        extra = ''
        if r['prob']:
            extra = f"  P(T<={r['prob']['deadline']})={r['prob']['got']:.4f} (oc. {r['prob']['expected']:.4f})"
        print(f"{mark} {r['name']}: E={r['got_e_proj']} (oc. {r['e_proj']}), "
              f"sigma={r['got_sd_proj']} (oc. {r['sd_proj']}){extra}")
    print()
    print('preslo:', sum(1 for r in results if r['ok']), '/', len(results))
    print('ulozene:', dst)


if __name__ == '__main__':
    main()
