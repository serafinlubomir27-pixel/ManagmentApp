"""Pool spojení pre PostgreSQL.

Testy bežia na SQLite, takže skutočný pool sa pri nich nepoužije. Práve preto
sú tu — logika okolo vracania spojení sa inak nikdy nespustí a pritom sú to
miesta, kde sa dá ticho pokaziť veľa: vrátiť spojenie dvakrát znamená vydať ho
dvom volajúcim naraz.
"""
import pytest

from repositories import base_repo
from repositories.base_repo import _PgConnectionWrapper


class FakePool:
    """Minimálny pool — zaznamenáva, čo doň prišlo späť."""

    def __init__(self, conns=None):
        self.returned = []
        self.closed_on_return = []
        self._conns = list(conns or [])
        self.handed_out = []

    def getconn(self):
        conn = self._conns.pop(0) if self._conns else FakeConn()
        self.handed_out.append(conn)
        return conn

    def putconn(self, conn, close=False):
        self.returned.append(conn)
        if close:
            self.closed_on_return.append(conn)


class FakeConn:
    def __init__(self, closed=False):
        self.closed = closed
        self.autocommit = True
        self.hard_closed = False

    def close(self):
        self.hard_closed = True


# ── Vracanie do poolu ───────────────────────────────────────────────────────

def test_close_returns_connection_instead_of_closing_it():
    pool, conn = FakePool(), FakeConn()
    wrapper = _PgConnectionWrapper(conn, pool)

    wrapper.close()

    assert pool.returned == [conn], "spojenie sa nevrátilo do poolu"
    assert conn.hard_closed is False, "spojenie sa zatvorilo, pool z neho nič nemá"


def test_double_close_returns_connection_only_once():
    """Repozitáre volajú close() vo finally — dá sa sem doraziť dvakrát.

    Druhé vrátenie by znamenalo, že pool vydá to isté spojenie dvom volajúcim
    naraz a začnú si prepisovať transakcie.
    """
    pool, conn = FakePool(), FakeConn()
    wrapper = _PgConnectionWrapper(conn, pool)

    wrapper.close()
    wrapper.close()
    wrapper.close()

    assert pool.returned == [conn]


def test_close_without_pool_really_closes():
    """Núdzové spojenie mimo poolu sa musí naozaj zatvoriť, inak uniká socket."""
    conn = FakeConn()
    _PgConnectionWrapper(conn, None).close()
    assert conn.hard_closed is True


def test_broken_pool_falls_back_to_closing():
    class ExplodingPool(FakePool):
        def putconn(self, conn, close=False):
            raise RuntimeError("pool je preč")

    conn = FakeConn()
    _PgConnectionWrapper(conn, ExplodingPool()).close()
    assert conn.hard_closed is True, "pri zlyhaní poolu sa spojenie nezatvorilo"


# ── Mŕtve spojenia ──────────────────────────────────────────────────────────

def test_dead_connections_are_discarded(monkeypatch):
    """Supabase nečinné spojenia zatvára. Prvý request po prestávke nesmie spadnúť."""
    dead, alive = FakeConn(closed=True), FakeConn()
    pool = FakePool([dead, alive])
    monkeypatch.setattr(base_repo, "_get_pool", lambda: pool)

    wrapper = base_repo._get_pg_connection()

    assert pool.closed_on_return == [dead], "mŕtve spojenie sa nezahodilo"
    assert wrapper._conn is alive
    assert alive.autocommit is False, "autocommit sa musí vypnúť pre transakcie"


def test_all_dead_falls_back_to_direct_connection(monkeypatch):
    """Keď pool vracia samé mŕtve spojenia, request má aj tak prejsť."""
    pool = FakePool([FakeConn(closed=True) for _ in range(5)])
    monkeypatch.setattr(base_repo, "_get_pool", lambda: pool)

    direct = FakeConn()

    class FakePsycopg2:
        @staticmethod
        def connect(*a, **kw):
            return direct

    monkeypatch.setitem(__import__("sys").modules, "psycopg2", FakePsycopg2)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/test")

    wrapper = base_repo._get_pg_connection()

    assert wrapper._conn is direct
    assert wrapper._pool is None, "núdzové spojenie nesmie skončiť v poole"
    assert len(pool.closed_on_return) == 3, "malo sa skúsiť trikrát"


# ── Konfigurácia ────────────────────────────────────────────────────────────

def test_pool_size_is_configurable(monkeypatch):
    """Render aj Supabase majú na bezplatnej úrovni strop na počet spojení."""
    captured = {}

    class FakeThreadedPool:
        def __init__(self, minconn, maxconn, dsn, **kw):
            captured.update(min=minconn, max=maxconn, dsn=dsn, kw=kw)

    class FakePoolModule:
        ThreadedConnectionPool = FakeThreadedPool

    monkeypatch.setattr(base_repo, "_pg_pool", None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/test")
    monkeypatch.setenv("DB_POOL_MIN", "2")
    monkeypatch.setenv("DB_POOL_MAX", "5")
    monkeypatch.setitem(__import__("sys").modules, "psycopg2.pool", FakePoolModule)

    try:
        base_repo._get_pool()
        assert captured["min"] == 2 and captured["max"] == 5
    finally:
        base_repo._pg_pool = None


def test_max_is_never_below_min(monkeypatch):
    captured = {}

    class FakeThreadedPool:
        def __init__(self, minconn, maxconn, dsn, **kw):
            captured.update(min=minconn, max=maxconn)

    class FakePoolModule:
        ThreadedConnectionPool = FakeThreadedPool

    monkeypatch.setattr(base_repo, "_pg_pool", None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test/test")
    monkeypatch.setenv("DB_POOL_MIN", "6")
    monkeypatch.setenv("DB_POOL_MAX", "2")
    monkeypatch.setitem(__import__("sys").modules, "psycopg2.pool", FakePoolModule)

    try:
        base_repo._get_pool()
        assert captured["max"] >= captured["min"], "pool s max < min sa nedá vytvoriť"
    finally:
        base_repo._pg_pool = None


def test_missing_database_url_is_reported(monkeypatch):
    monkeypatch.setattr(base_repo, "_pg_pool", None)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        base_repo._get_pool()
    base_repo._pg_pool = None


# ── SQLite sa nepooluje ─────────────────────────────────────────────────────

def test_sqlite_connections_are_really_closed():
    """SQLite sa zámerne nepooluje — a close() tam musí naozaj zatvárať."""
    if base_repo.get_backend() != "sqlite":
        pytest.skip("beží proti PostgreSQL")

    conn = base_repo.get_connection()
    conn.execute("SELECT 1").fetchone()
    conn.close()

    import sqlite3
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


# ── Jedno spojenie na request ───────────────────────────────────────────────

def _as_postgres(monkeypatch, pool):
    """Prepne base_repo do režimu PostgreSQL s podstrčeným poolom."""
    monkeypatch.setattr(base_repo, "_BACKEND", "postgres")
    monkeypatch.setattr(base_repo, "_get_pool", lambda: pool)


def test_request_shares_one_connection(monkeypatch):
    """Celý request má dostať to isté spojenie — inak každé volanie
    repozitára zaplatí vlastný ROLLBACK pri vracaní do poolu."""
    pool = FakePool()
    _as_postgres(monkeypatch, pool)

    holder, token = base_repo.begin_request_scope()
    try:
        a = base_repo.get_connection()
        b = base_repo.get_connection()
        c = base_repo.get_connection()
        assert a._inner is b._inner is c._inner
        assert len(pool.handed_out) == 1, "z poolu sa brali ďalšie spojenia"
    finally:
        base_repo.end_request_scope(holder, token)


def test_close_inside_request_does_not_return_connection(monkeypatch):
    """Repozitáre volajú close() vo finally. Keby sa tým spojenie vrátilo,
    ďalšie volanie v tom istom requeste by dostalo iné."""
    pool = FakePool()
    _as_postgres(monkeypatch, pool)

    holder, token = base_repo.begin_request_scope()
    try:
        conn = base_repo.get_connection()
        conn.close()
        conn.close()
        assert pool.returned == [], "spojenie sa vrátilo už počas requestu"
        assert base_repo.get_connection()._inner is conn._inner
    finally:
        base_repo.end_request_scope(holder, token)

    assert len(pool.returned) == 1, "na konci requestu sa spojenie nevrátilo"


def test_connection_is_taken_lazily(monkeypatch):
    """Nie každý request sa databázy dotkne — brať spojenie dopredu by
    zbytočne držalo miesto v poole."""
    pool = FakePool()
    _as_postgres(monkeypatch, pool)

    holder, token = base_repo.begin_request_scope()
    assert pool.handed_out == []
    base_repo.end_request_scope(holder, token)

    assert pool.handed_out == [] and pool.returned == []


def test_connection_released_even_when_request_fails(monkeypatch):
    pool = FakePool()
    _as_postgres(monkeypatch, pool)

    holder, token = base_repo.begin_request_scope()
    try:
        base_repo.get_connection()
        raise RuntimeError("endpoint spadol")
    except RuntimeError:
        pass
    finally:
        base_repo.end_request_scope(holder, token)

    assert len(pool.returned) == 1, "spojenie ostalo visieť po chybe"


def test_outside_request_behaves_as_before(monkeypatch):
    """Skripty a migrácie bežia mimo requestu — tam si každé volanie berie
    a vracia spojenie samostatne."""
    pool = FakePool()
    _as_postgres(monkeypatch, pool)

    conn = base_repo.get_connection()
    assert isinstance(conn, base_repo._PgConnectionWrapper)
    conn.close()
    assert len(pool.returned) == 1


def test_commit_passes_through_to_real_connection(monkeypatch):
    """Zapisovacie funkcie commitujú samy za seba — proxy to nesmie prehltnúť."""
    class CountingConn(FakeConn):
        def __init__(self):
            super().__init__()
            self.commits = 0

    raw = CountingConn()
    raw.commit = lambda: setattr(raw, "commits", raw.commits + 1)
    pool = FakePool([raw])
    _as_postgres(monkeypatch, pool)

    holder, token = base_repo.begin_request_scope()
    try:
        base_repo.get_connection().commit()
        base_repo.get_connection().commit()
    finally:
        base_repo.end_request_scope(holder, token)

    assert raw.commits == 2
