"""SQLite transactions keep summaries and successful checkpoints together."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from .batches import select_batches
from .model import digest, eligible, safe_course_id, turn_key, validate_turn
from .updates import reference, validate_update

SCHEMA = '''
CREATE TABLE IF NOT EXISTS turns (
  thread_id TEXT NOT NULL, turn_id TEXT NOT NULL, payload TEXT NOT NULL,
  processed TEXT, PRIMARY KEY(thread_id, turn_id));
CREATE TABLE IF NOT EXISTS versions (course_id TEXT PRIMARY KEY, version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS updates (
  batch_id TEXT PRIMARY KEY, course_id TEXT NOT NULL, version INTEGER NOT NULL,
  created_at TEXT NOT NULL, payload TEXT NOT NULL, batch_ids TEXT NOT NULL,
  update_hash TEXT NOT NULL);
'''


@contextmanager
def connection(path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
    finally:
        conn.close()


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def import_turns(db_path: Path, turns: list[dict]) -> int:
    if not isinstance(turns, list):
        raise ValueError('Import input must be a list of turns.')
    validated = [validate_turn(t) for t in turns]
    inserted = 0
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        for t in validated:
            key = turn_key(t)
            old = conn.execute('SELECT payload, processed FROM turns WHERE thread_id=? AND turn_id=?', key).fetchone()
            if old:
                before = json.loads(old['payload'])
                if before['revision_hash'] == t['revision_hash']:
                    continue
                identity = set(t) - {'assistant_text','complete','revision_hash'}
                if (old['processed'] or before['complete'] or not t['complete']
                        or any(before[f] != t[f] for f in identity)):
                    raise ValueError(f'Conflicting turn revision: {key}; review the branch before importing.')
                conn.execute('UPDATE turns SET payload=? WHERE thread_id=? AND turn_id=?', (encode(t), *key))
            else:
                conn.execute('INSERT INTO turns VALUES (?,?,?,NULL)', (*key, encode(t)))
                inserted += 1
    return inserted


def pending_batches(db_path: Path, flush: bool = False) -> list[list[dict]]:
    if not Path(db_path).exists():
        return []
    with connection(db_path) as conn:
        rows = conn.execute('SELECT payload FROM turns WHERE processed IS NULL').fetchall()
    return select_batches([json.loads(r['payload']) for r in rows], set(), flush)


def commit_update(db_path: Path, batch_ids: list[tuple[str,str]], update: dict, expected_version: int) -> int:
    if not isinstance(batch_ids, list) or not 1 <= len(batch_ids) <= 4:
        raise ValueError('A batch contains 1 to 4 completed learning turns.')
    keys = sorted(reference(k) for k in batch_ids)
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate source turn in batch.')
    if type(expected_version) is not int or expected_version < 0:
        raise ValueError('expected_version must be a nonnegative integer.')
    batch_id, update_hash = digest(keys), digest(update)
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        old = conn.execute('SELECT version, update_hash FROM updates WHERE batch_id=?', (batch_id,)).fetchone()
        if old:
            if old['update_hash'] != update_hash:
                raise ValueError('Batch was already committed with a different summary; append a correction.')
            return old['version']
        turns = []
        for key in keys:
            row = conn.execute('SELECT payload, processed FROM turns WHERE thread_id=? AND turn_id=?', key).fetchone()
            if not row or row['processed']:
                raise ValueError('Batch contains a missing or already processed turn.')
            t = json.loads(row['payload'])
            if not eligible(t):
                raise ValueError('Cannot commit incomplete, unconfirmed, or non-learning turns.')
            turns.append(t)
        group = {(t['course_id'],t['session_id'],t['thread_id']) for t in turns}
        if len(group) != 1:
            raise ValueError('A batch cannot mix courses, sessions, or threads.')
        course, session, thread = next(iter(group))
        pending = [json.loads(r['payload']) for r in conn.execute('SELECT payload FROM turns WHERE processed IS NULL')]
        same = [t for t in pending if eligible(t) and (t['course_id'],t['session_id'],t['thread_id']) == (course,session,thread)]
        earliest = sorted(same, key=lambda t: (t['occurred_at'], t['turn_id']))[:len(keys)]
        if set(keys) != {turn_key(t) for t in earliest}:
            raise ValueError('Commit the earliest unprocessed turns in this session first.')
        version_row = conn.execute('SELECT version FROM versions WHERE course_id=?', (course,)).fetchone()
        version = version_row['version'] if version_row else 0
        if version != expected_version:
            raise ValueError(f'Course version conflict: expected {expected_version}, found {version}; reread and merge.')
        known_events = {e['event_id'] for row in conn.execute('SELECT payload FROM updates WHERE course_id=?', (course,))
                        for e in json.loads(row['payload'])['events']}
        checked = validate_update(update, turns, known_events)
        for index, event in enumerate(checked['events']):
            event['event_id'] = f'{batch_id}:{index}'
        version += 1
        conn.execute('INSERT INTO updates VALUES (?,?,?,?,?,?,?)',
                     (batch_id, course, version, datetime.now(timezone.utc).isoformat(),
                      encode(checked), encode(keys), update_hash))
        conn.execute('INSERT INTO versions VALUES (?,?) ON CONFLICT(course_id) DO UPDATE SET version=excluded.version', (course, version))
        for key in keys:
            conn.execute('UPDATE turns SET processed=? WHERE thread_id=? AND turn_id=?', (batch_id, *key))
    return version


def read_course(db_path: Path, course_id: str) -> dict:
    safe_course_id(course_id)
    result = {'course_id': course_id, 'version': 0, 'updates': [], 'turns': []}
    if not Path(db_path).exists():
        return result
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN')
        row = conn.execute('SELECT version FROM versions WHERE course_id=?', (course_id,)).fetchone()
        result['version'] = row['version'] if row else 0
        for row in conn.execute('SELECT * FROM updates WHERE course_id=? ORDER BY version', (course_id,)):
            result['updates'].append(dict(batch_id=row['batch_id'], version=row['version'],
                                          created_at=row['created_at'], update=json.loads(row['payload'])))
        result['turns'] = [t for row in conn.execute('SELECT payload FROM turns WHERE processed IS NOT NULL')
                           if (t := json.loads(row['payload']))['course_id'] == course_id]
    return result
