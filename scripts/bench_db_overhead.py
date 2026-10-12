"""Zmeria réžiu prístupu k databáze pri vzdialenom PostgreSQL.

Výpočet kritickej cesty beží v pamäti a je rýchly (viď bench_cpm.py). Pri
nasadení proti vzdialenej databáze však odozvu rozhrania určuje niečo iné —
koľko kôl po sieti si vyžiada jedno volanie. Tento skript to meria v troch
stavoch, aby bolo vidieť, čo ktorý krok ušetril:

  1. nové spojenie na každý dotaz   (pôvodný stav)
  2. spojenie z poolu               (pool drží spojenia otvorené)
  3. jedno spojenie na celý request (odpadnú opakované ROLLBACKy)

Vyžaduje DATABASE_URL v .env. Výsledok sa ukladá do TEMP/db_overhead.json,
odkiaľ ho číta generátor textu práce.

    py scripts/bench_db_overhead.py
"""
from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(REPO, '.env'))

import psycopg2  # noqa: E402
from repositories import base_repo  # noqa: E402

REPEATS = 9


def _median_ms(fn, repeats: int = REPEATS) -> float:
    """Medián z opakovaní; prvý beh sa zahadzuje ako zahrievací."""
    xs = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        xs.append((time.perf_counter() - t0) * 1000)
    return round(statistics.median(xs[1:]), 1)


def main() -> int:
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('CHYBA: nastav DATABASE_URL (meranie má zmysel len proti vzdialenej DB).')
        return 1

    out: dict[str, float] = {}

    # 1. Samotné nadviazanie spojenia — TCP a TLS handshake.
    def otvor():
        psycopg2.connect(url, connect_timeout=15).close()
    out['open_connection'] = _median_ms(otvor, 5)

    # 2. Nové spojenie na každý dotaz — stav pred zavedením poolu.
    def bez_poolu():
        c = psycopg2.connect(url, connect_timeout=15)
        c.autocommit = False
        cur = c.cursor(); cur.execute('SELECT 1'); cur.fetchone()
        c.close()
    out['query_new_connection'] = _median_ms(bez_poolu, 5)

    # 3. Dotaz na už otvorenom spojení — čistá cena jedného kola po sieti.
    held = base_repo.get_connection()
    out['query_held_connection'] = _median_ms(
        lambda: held.execute('SELECT 1').fetchone())

    # 4. Dotaz + ROLLBACK. Čítacie funkcie necommitujú, takže psycopg2 pri
    #    vrátení spojenia do poolu rolluje — ďalšie kolo po sieti.
    raw = held._conn
    out['query_plus_rollback'] = _median_ms(
        lambda: (held.execute('SELECT 1').fetchone(), raw.rollback()))
    held.close()

    # 5. Samotné požičanie a vrátenie spojenia poolom, bez dotazu.
    pool = base_repo._get_pool()

    def pool_cyklus():
        c = pool.getconn(); pool.putconn(c)
    out['pool_borrow_return'] = _median_ms(pool_cyklus)

    # 6. Celý cyklus cez pool — tak, ako ho používa jedna funkcia repozitára.
    def cez_pool():
        c = base_repo.get_connection()
        c.execute('SELECT 1').fetchone()
        c.close()
    out['query_pooled'] = _median_ms(cez_pool)

    env = {
        'system': f'{platform.system()} {platform.release()}',
        'machine': platform.machine(),
        'python': platform.python_version(),
        'repeats': REPEATS,
        'backend': base_repo.get_backend(),
    }

    sirka = max(len(k) for k in out)
    print('réžia prístupu k databáze (medián, ms)')
    print('-' * (sirka + 12))
    for k, v in out.items():
        print(f'  {k:<{sirka}}  {v:7.1f}')
    print()
    print(f'prostredie: {env["system"]} | {env["machine"]} | Python {env["python"]}')

    dst = os.path.join(os.environ['TEMP'], 'db_overhead.json')
    json.dump({'env': env, 'ms': out}, open(dst, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('uložené:', dst)

    base_repo.close_pool()
    return 0


if __name__ == '__main__':
    sys.exit(main())
