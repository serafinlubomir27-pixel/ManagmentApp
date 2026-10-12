"""Base repository — dual-mode database connection.

Supports two backends controlled by the DB_BACKEND environment variable:

  DB_BACKEND=sqlite   (default) — local SQLite file, no setup required
  DB_BACKEND=postgres            — PostgreSQL via DATABASE_URL (Supabase or any PG host)

Usage:
  Copy .env.example to .env and set DB_BACKEND + DATABASE_URL.

All repos call get_connection() and receive a connection object that exposes
the same interface regardless of backend:
  - .cursor()       — returns a cursor
  - .execute()      — shorthand execute on connection
  - .commit()       — commit transaction
  - .close()        — SQLite zatvorí, PostgreSQL vráti spojenie do poolu

Row access: both backends return rows accessible by column name (dict-like).
Use row_to_dict() / rows_to_dicts() to convert to plain dicts.

Pooling (len PostgreSQL)
------------------------
Každá funkcia repozitára si berie spojenie a na konci ho „zatvára". Kým sa
pri každom volaní otváralo nové, platilo sa za TCP a TLS handshake k Supabase
— namerané 251 ms na spojenie oproti 34 ms na samotný dotaz, teda asi 88 %
réžie na triviálnom dotaze. Request, ktorý sa pýtal päťkrát, tak premárnil
viac než sekundu.

Pool spojenia necháva otvorené a `close()` ich iba vracia naspäť. Volajúci
kód sa nemenil ani na jednom mieste. Transakčné správanie ostáva rovnaké:
každá funkcia repozitára dostane spojenie samostatne a commituje sama za seba.

SQLite sa nepooluje zámerne — otvorenie súboru stojí mikrosekundy, takže by
to nič nezrýchlilo, a sqlite3 spojenia navyše neprechádzajú medzi vláknami.
"""
from __future__ import annotations

import os
import sqlite3

# Load .env if present (optional — app works without it for SQLite mode)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — use system env vars or defaults

# ── Backend selection ──────────────────────────────────────────────────────

_BACKEND = os.environ.get("DB_BACKEND", "sqlite").strip().lower()

# ── SQLite path ────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, os.environ.get("SQLITE_PATH", "my_project_app.db"))


# ── PostgreSQL connection wrapper ──────────────────────────────────────────

class _PgCursorWrapper:
    """Wraps a psycopg2 cursor so column values are accessible by name (like sqlite3.Row)."""

    def __init__(self, cursor):
        self._cur = cursor
        self._columns: list[str] = []
        self._last_id = None

    def execute(self, sql: str, params=None):
        # Translate SQLite ? placeholders to psycopg2 %s
        pg_sql = sql.replace("?", "%s")
        # Auto-append RETURNING id for INSERT statements so lastrowid works
        stripped_upper = pg_sql.strip().upper()
        if stripped_upper.startswith("INSERT") and "RETURNING" not in stripped_upper:
            pg_sql = pg_sql.rstrip().rstrip(";") + " RETURNING id"
        if params is None:
            self._cur.execute(pg_sql)
        else:
            self._cur.execute(pg_sql, params)
        if self._cur.description:
            self._columns = [d[0] for d in self._cur.description]
            # Capture the inserted id immediately so lastrowid works after commit
            if self._columns == ["id"]:
                row = self._cur.fetchone()
                self._last_id = row[0] if row else None
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return dict(zip(self._columns, row))

    def fetchall(self):
        rows = self._cur.fetchall()
        return [dict(zip(self._columns, r)) for r in rows]

    @property
    def lastrowid(self):
        return self._last_id

    @property
    def rowcount(self):
        return self._cur.rowcount


class _PgConnectionWrapper:
    """Wraps a psycopg2 connection so it behaves like sqlite3 for our repos.

    Key adaptations:
    - cursor() returns a _PgCursorWrapper
    - execute() is a shorthand that creates a cursor, executes, returns cursor
    - RETURNING id clause added automatically for INSERT to support lastrowid
    - close() is kept as-is (psycopg2 connections should be closed)
    """

    def __init__(self, conn, pool=None):
        self._conn = conn
        self._pool = pool
        self._released = False

    def cursor(self):
        return _PgCursorWrapper(self._conn.cursor())

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        """Vráti spojenie do poolu namiesto zatvorenia.

        Repozitáre volajú close() vo `finally`, takže sa sem dá doraziť aj
        dvakrát — druhé volanie musí byť bez účinku, inak by pool dostal to
        isté spojenie dvakrát a vydal by ho dvom volajúcim naraz.

        Prípadnú otvorenú transakciu rieši psycopg2 v putconn sám: nečinné
        spojenie vráti, rozpracované odroluje a rozbité zahodí.
        """
        if self._released:
            return
        self._released = True
        if self._pool is None:
            self._conn.close()
            return
        try:
            self._pool.putconn(self._conn)
        except Exception:
            # Pool medzitým zanikol alebo spojenie nepatrí doňho — radšej
            # socket zavrieť, než ho nechať visieť.
            try:
                self._conn.close()
            except Exception:
                pass

    def rollback(self):
        self._conn.rollback()


# ── Pool spojení (PostgreSQL) ──────────────────────────────────────────────
# Render aj Supabase majú na bezplatnej úrovni strop na počet spojení, preto
# je pool zámerne malý. Dá sa posunúť cez DB_POOL_MIN / DB_POOL_MAX.

_pg_pool = None
_pg_pool_lock = None


def _get_pool():
    """Vytvorí pool pri prvom použití. Thread-safe — FastAPI púšťa synchrónne
    endpointy v threadpoole, takže sem môže doraziť viac vlákien naraz."""
    global _pg_pool, _pg_pool_lock
    if _pg_pool is not None:
        return _pg_pool

    import threading
    if _pg_pool_lock is None:
        _pg_pool_lock = threading.Lock()

    with _pg_pool_lock:
        if _pg_pool is not None:
            return _pg_pool

        from psycopg2 import pool as pg_pool

        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            raise RuntimeError(
                "DATABASE_URL is not set. Add it to your .env file.\n"
                "See .env.example for the format."
            )
        minconn = int(os.environ.get("DB_POOL_MIN", "1"))
        maxconn = max(minconn, int(os.environ.get("DB_POOL_MAX", "8")))
        _pg_pool = pg_pool.ThreadedConnectionPool(
            minconn, maxconn, db_url, connect_timeout=15,
        )
    return _pg_pool


def _get_pg_connection() -> _PgConnectionWrapper:
    """Vezme spojenie z poolu.

    Supabase nečinné spojenia po čase zatvára, takže vrátené spojenie môže byť
    mŕtve. Taká sa zahodí a skúsi sa ďalšia — inak by prvý request po dlhšej
    prestávke spadol.
    """
    pool = _get_pool()
    for _ in range(3):
        raw = pool.getconn()
        if raw.closed:
            pool.putconn(raw, close=True)
            continue
        raw.autocommit = False
        return _PgConnectionWrapper(raw, pool)

    # Pool vracia samé mŕtve spojenia — obíď ho, nech request radšej prejde.
    import psycopg2
    raw = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=15)
    raw.autocommit = False
    return _PgConnectionWrapper(raw, None)


def close_pool() -> None:
    """Zatvorí všetky spojenia. Pre skripty a vypínanie aplikácie."""
    global _pg_pool
    if _pg_pool is not None:
        try:
            _pg_pool.closeall()
        finally:
            _pg_pool = None


# ── Jedno spojenie na request ──────────────────────────────────────────────
# Pool urobil získanie spojenia zadarmo (getconn + putconn = 0,0 ms), ale
# čítacie funkcie necommitujú, takže nechávajú otvorenú transakciu a putconn
# za ne posiela ROLLBACK — ďalšie kolo po sieti. Namerané: SELECT 1 stojí
# 32 ms, SELECT 1 + ROLLBACK 101 ms. Request s devätnástimi volaniami tak
# zaplatí osemnásť zbytočných rollbackov.
#
# Preto si request drží jedno spojenie a vráti ho až na konci. Transakčné
# správanie sa tým nemení: každá zapisovacia funkcia commituje sama za seba
# (overené staticky — žiadna zapisovacia funkcia commit nevynecháva).

import contextvars  # noqa: E402

# V premennej je zámerne meniteľný obal, nie spojenie. FastAPI púšťa synchrónne
# endpointy v threadpoole, ktorý kontext iba KOPÍRUJE — zápis do premennej vo
# vlákne by sa do middleware nevrátil. Mutácia spoločného slovníka áno.
_request_scope: contextvars.ContextVar = contextvars.ContextVar(
    "nodus_db_request_scope", default=None,
)


class _ScopedConnection:
    """Spojenie požičané na dobu requestu — close() ho nevracia.

    Repozitáre volajú close() vo `finally`; keby sa tu spojenie naozaj
    vracalo, ďalšie volanie v tom istom requeste by dostalo iné.
    """

    def __init__(self, inner: _PgConnectionWrapper):
        self._inner = inner

    def cursor(self):
        return self._inner.cursor()

    def execute(self, sql: str, params=None):
        return self._inner.execute(sql, params)

    def commit(self):
        self._inner.commit()

    def rollback(self):
        self._inner.rollback()

    def close(self):
        pass  # uvoľní ho end_request_scope na konci requestu


def begin_request_scope():
    """Otvorí rozsah. Spojenie sa berie až pri prvom dotaze — nie každý
    request sa databázy vôbec dotkne."""
    holder: dict = {"conn": None}
    return holder, _request_scope.set(holder)


def end_request_scope(holder, token) -> None:
    """Vráti spojenie do poolu a zatvorí rozsah."""
    conn = holder.get("conn") if holder else None
    if holder is not None:
        holder["conn"] = None
    if token is not None:
        try:
            _request_scope.reset(token)
        except ValueError:
            pass  # iný kontext (threadpool) — premenná zanikne sama
    if conn is not None:
        conn.close()


# ── SQLite row wrapper ─────────────────────────────────────────────────────

class _SqliteCursorWrapper:
    """Thin wrapper around sqlite3 cursor that stores lastrowid properly."""

    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor()

    def execute(self, sql: str, params=None):
        if params is None:
            self._cur.execute(sql)
        else:
            self._cur.execute(sql, params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount


class _SqliteConnectionWrapper:
    """Wraps sqlite3 connection with the same interface as _PgConnectionWrapper."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _SqliteCursorWrapper(self._conn)

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def rollback(self):
        self._conn.rollback()


def _get_sqlite_connection() -> _SqliteConnectionWrapper:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return _SqliteConnectionWrapper(conn)


# ── Public API ─────────────────────────────────────────────────────────────

def get_connection():
    """Return a database connection for the configured backend.

    SQLite:   lightweight, file-based, no config needed
    Postgres: z poolu; počas requestu vráti to isté spojenie všetkým volajúcim
    """
    if _BACKEND != "postgres":
        return _get_sqlite_connection()

    holder = _request_scope.get()
    if holder is None:
        # Mimo requestu — skripty, migrácie, testy. Spojenie sa berie
        # a vracia po jednom, presne ako doteraz.
        return _get_pg_connection()

    conn = holder.get("conn")
    if conn is None:
        conn = _get_pg_connection()
        holder["conn"] = conn
    return _ScopedConnection(conn)


def get_backend() -> str:
    """Return the active backend name: 'sqlite' or 'postgres'."""
    return _BACKEND


def row_to_dict(row) -> dict | None:
    """Convert a row to a plain dict (handles None, sqlite3.Row, and plain dict)."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


def rows_to_dicts(rows) -> list[dict]:
    """Convert a list of rows to a list of plain dicts."""
    result = []
    for r in rows:
        if isinstance(r, dict):
            result.append(r)
        else:
            result.append(dict(r))
    return result
