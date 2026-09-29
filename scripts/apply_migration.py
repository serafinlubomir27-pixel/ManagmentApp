"""Aplikuje SQL migráciu na databázu podľa DATABASE_URL v .env.

    py scripts/apply_migration.py database/migrations/009_client_crm.sql
    py scripts/apply_migration.py database/migrations/009_client_crm.sql --apply

Bez --apply iba vypíše, čo by sa spustilo. Celá migrácia beží v jednej
transakcii, takže pri chybe sa nezapíše nič.
"""
from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from dotenv import load_dotenv

load_dotenv(os.path.join(REPO, '.env'))

import psycopg2  # noqa: E402


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit('Použitie: py scripts/apply_migration.py <súbor.sql> [--apply]')
    path = args[0]
    if not os.path.isabs(path):
        path = os.path.join(REPO, path)
    if not os.path.exists(path):
        sys.exit(f'Súbor sa nenašiel: {path}')

    sql = open(path, encoding='utf-8').read()

    def strip_comments(block: str) -> str:
        """Odstráni komentárové riadky; príkazu často predchádza hlavička."""
        return '\n'.join(ln for ln in block.splitlines()
                         if ln.strip() and not ln.strip().startswith('--')).strip()

    statements = [c for c in (strip_comments(s) for s in sql.split(';')) if c]
    print(f'{os.path.basename(path)}: {len(statements)} príkazov')

    if '--apply' not in sys.argv:
        for s in statements:
            print('  ', s.splitlines()[0].strip()[:90])
        print('\nSkúšobný beh — nič sa nespustilo. Pre zápis pridaj --apply')
        return

    conn = psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=30)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        print('migrácia aplikovaná')
    except Exception as exc:
        conn.rollback()
        sys.exit(f'CHYBA, nič sa nezmenilo: {exc}')

    cur.execute("""select table_name from information_schema.tables
                   where table_schema='public'
                     and table_name in ('client_activities','client_tasks','deal_stage_history')
                   order by table_name""")
    print('tabuľky v databáze:', ', '.join(r[0] for r in cur.fetchall()) or 'žiadne')
    conn.close()


if __name__ == '__main__':
    main()
