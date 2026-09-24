"""Presun projektov a úloh na iného používateľa a do jeho organizácie.

Spúšťa sa proti databáze podľa DATABASE_URL v .env. Všetko beží v jednej
transakcii — pri akejkoľvek chybe sa nezapíše nič.

    py scripts/migrate_projects_to_user.py --to 4 --projects 1,2,3
    py scripts/migrate_projects_to_user.py --to 4 --projects 1,2,3 --apply

Bez --apply iba vypíše, čo by sa zmenilo.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import psycopg2  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--to', type=int, required=True, help='ID cieľového používateľa')
    ap.add_argument('--projects', required=True, help='ID projektov oddelené čiarkou')
    ap.add_argument('--apply', action='store_true', help='skutočne zapísať zmeny')
    args = ap.parse_args()

    pids = [int(x) for x in args.projects.split(',') if x.strip()]
    conn = psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=30)
    cur = conn.cursor()

    cur.execute('select id, username, email, organization_id from users where id = %s', (args.to,))
    target = cur.fetchone()
    if not target:
        sys.exit(f'Používateľ id={args.to} neexistuje.')
    uid, uname, uemail, org_id = target
    if org_id is None:
        sys.exit(f'Používateľ {uname} nemá organizáciu — presun by vytvoril osirelé projekty.')

    cur.execute('select name, plan from organizations where id = %s', (org_id,))
    org_name, plan = cur.fetchone()

    print(f'Cieľ: {uname} <{uemail}>  (user_id={uid}, org={org_name!r} id={org_id}, plan={plan})')
    print()

    cur.execute(
        'select id, name, user_id, organization_id from projects where id = any(%s) order by id',
        (pids,),
    )
    rows = cur.fetchall()
    if len(rows) != len(pids):
        found = {r[0] for r in rows}
        sys.exit(f'Nenájdené projekty: {sorted(set(pids) - found)}')

    total_tasks = 0
    for pid, name, old_uid, old_org in rows:
        cur.execute('select count(*) from tasks where project_id = %s', (pid,))
        n = cur.fetchone()[0]
        total_tasks += n
        print(f'  projekt {pid}: {name!r}  {n} úloh   user {old_uid} -> {uid}, org {old_org} -> {org_id}')

    cur.execute('select count(*) from tasks where project_id = any(%s)', (pids,))
    print(f'\núloh spolu: {total_tasks}')
    cur.execute(
        'select count(*) from task_dependencies where task_id in '
        '(select id from tasks where project_id = any(%s))', (pids,))
    print(f'závislostí medzi úlohami: {cur.fetchone()[0]} (presúvajú sa s úlohami)')

    if not args.apply:
        print('\nSkúšobný beh — nič sa nezapísalo. Pre zápis pridaj --apply')
        conn.close()
        return

    try:
        cur.execute(
            'update projects set user_id = %s, organization_id = %s where id = any(%s)',
            (uid, org_id, pids))
        moved_p = cur.rowcount
        # Úlohy odkazujú na používateľov pôvodnej organizácie; bez prepísania by
        # vznikli medziorganizačné väzby (priradený človek z cudzej organizácie).
        cur.execute(
            'update tasks set assigned_to = %s where project_id = any(%s) and assigned_to is not null',
            (uid, pids))
        moved_a = cur.rowcount
        cur.execute(
            'update tasks set created_by = %s where project_id = any(%s)', (uid, pids))
        moved_c = cur.rowcount
        conn.commit()
    except Exception as exc:
        conn.rollback()
        sys.exit(f'CHYBA, nič sa nezapísalo: {exc}')

    print(f'\nZapísané: {moved_p} projektov, {moved_a} priradení, {moved_c} tvorcov úloh.')

    cur.execute(
        'select id, name, user_id, organization_id from projects where id = any(%s) order by id', (pids,))
    print('\nStav po presune:')
    for r in cur.fetchall():
        print(f'  projekt {r[0]}: {r[1]!r}  user_id={r[2]}  org={r[3]}')
    conn.close()


if __name__ == '__main__':
    main()
