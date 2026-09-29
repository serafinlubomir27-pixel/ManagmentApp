"""Statická kontrola SQL na rozdiely medzi SQLite a PostgreSQL.

Testy bežia nad SQLite, ktorá je voľná v typovaní, takže časť chýb sa v nich
neprejaví a spadne až v produkcii na PostgreSQL. Tento test preto nespúšťa
dotazy, ale kontroluje ich text.

Reálny prípad: `WHERE is_template = 0` prechádzalo v SQLite, ale PostgreSQL ho
odmietlo chybou „operator does not exist: boolean = integer“, čím zlyhalo
zakladanie každého projektu.

Spustenie:
    py -m pytest tests/test_sql_portability.py -v
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent

# Stĺpce, ktoré sú v PostgreSQL schéme typu BOOLEAN.
BOOLEAN_COLUMNS = [
    'is_template', 'is_critical', 'is_read',
    'auto_notify', 'auto_calendar',
    'default_auto_notify', 'default_auto_calendar',
]

SEARCHED_DIRS = ['repositories', 'logic', 'backend', 'database']


def _python_files():
    for d in SEARCHED_DIRS:
        for path in (REPO / d).rglob('*.py'):
            if '__pycache__' in path.parts:
                continue
            yield path


def test_boolean_columns_are_not_compared_to_integers():
    """`is_read = 1` musí byť `is_read = TRUE`, inak PostgreSQL dotaz odmietne."""
    pattern = re.compile(
        r'\b(' + '|'.join(BOOLEAN_COLUMNS) + r')\s*(=|<>|!=)\s*[01]\b')
    hits = []
    for path in _python_files():
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            m = pattern.search(line)
            if m:
                hits.append(f'{path.relative_to(REPO)}:{lineno}: {m.group(0)}')

    assert not hits, (
        'Boolean stĺpec sa porovnáva s číslom — v SQLite to prejde, v PostgreSQL nie.\n'
        'Použi TRUE/FALSE namiesto 1/0:\n  ' + '\n  '.join(hits))


def test_no_sqlite_only_functions():
    """Funkcie dostupné len v SQLite by v produkcii na PostgreSQL zlyhali."""
    forbidden = ['strftime(', 'datetime(', 'julianday(', 'ifnull(']
    pattern = re.compile(r'|'.join(re.escape(f) for f in forbidden), re.IGNORECASE)
    hits = []
    for path in _python_files():
        text = path.read_text(encoding='utf-8')
        # Zaujímajú nás len reťazce s SQL, nie volania v Pythone.
        for lineno, line in enumerate(text.splitlines(), 1):
            if 'SELECT' not in line.upper() and 'WHERE' not in line.upper():
                continue
            m = pattern.search(line)
            if m:
                hits.append(f'{path.relative_to(REPO)}:{lineno}: {m.group(0)}')

    assert not hits, (
        'SQL používa funkciu, ktorú PostgreSQL nepozná:\n  ' + '\n  '.join(hits))
