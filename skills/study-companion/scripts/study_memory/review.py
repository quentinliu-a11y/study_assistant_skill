"""Recurring questions and spaced daily review. Selection is deterministic, not left to the assistant."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
from .model import parse_day, safe_course_id
from .store import connection, encode

INTERVALS = (1, 3, 7, 14, 30)  # days until the next review after each consecutive correct answer
STATUSES = ('unverified', 'needs_help', 'can_explain', 'can_apply')
OUTCOMES = ('correct', 'hinted', 'incorrect', 'skipped')
DAY_SKIP = ''  # question_id of a row meaning "the learner skipped today's review"


def question_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value):
        raise ValueError('Question id must be a lowercase slug: letters, digits, hyphens, at most 64 characters.')
    return value


def text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be nonempty text.')
    return value.strip()


def recurring(question: dict) -> bool:
    return len({o['source'] for o in question['occurrences']}) >= 2


def load(conn, course: str) -> list[dict]:
    return [json.loads(r['payload']) for r in conn.execute(
        'SELECT payload FROM questions WHERE course_id=? ORDER BY question_id', (course,))]


def save(conn, question: dict) -> None:
    conn.execute('INSERT INTO questions VALUES (?,?,?) ON CONFLICT(course_id, question_id) DO UPDATE SET payload=excluded.payload',
                 (question['course_id'], question['question_id'], encode(question)))


def add_question(db_path: Path, course: str, qid: str, confusion=None, prompt=None, concept_ids=None,
                 status=None, day=None, source=None, note='') -> dict:
    """Create a question, or record one more independent occurrence of an existing one."""
    safe_course_id(course); question_id(qid)
    if status is not None and status not in STATUSES:
        raise ValueError('Invalid status.')
    if (day is None) != (source is None):
        raise ValueError('An occurrence needs both its date and its source.')
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT payload FROM questions WHERE course_id=? AND question_id=?', (course, qid)).fetchone()
        if row:
            question = json.loads(row['payload'])
        else:
            question = dict(course_id=course, question_id=qid, confusion=text(confusion, 'confusion'),
                            prompt=text(prompt, 'prompt'), concept_ids=[], status='unverified',
                            occurrences=[], streak=0, due=None, last_reviewed=None)
        if row and confusion:
            question['confusion'] = text(confusion, 'confusion')
        if row and prompt:
            question['prompt'] = text(prompt, 'prompt')
        if concept_ids:
            question['concept_ids'] = sorted(set(question['concept_ids']) | {text(c, 'concept') for c in concept_ids})
        if status:
            question['status'] = status
        if day is not None:
            occurrence = dict(date=parse_day(day), source=text(source, 'source'), note=(note or '').strip())
            # The same source on the same day is one occurrence, however many files repeat it.
            if not any((o['date'], o['source']) == (occurrence['date'], occurrence['source']) for o in question['occurrences']):
                question['occurrences'].append(occurrence)
                question['occurrences'].sort(key=lambda o: (o['date'], o['source']))
        save(conn, question)
    return dict(question, recurring=recurring(question))


def list_questions(db_path: Path, course: str) -> list[dict]:
    safe_course_id(course)
    if not Path(db_path).exists():
        return []
    with connection(db_path) as conn:
        return [dict(q, recurring=recurring(q)) for q in load(conn, course)]


def review_history(db_path: Path, course: str) -> list[dict]:
    safe_course_id(course)
    if not Path(db_path).exists():
        return []
    with connection(db_path) as conn:
        return [dict(r) for r in conn.execute(
            'SELECT question_id, day, outcome, note, source, created_at FROM reviews WHERE course_id=? ORDER BY day, id', (course,))]


def record(conn, course, qid, day, outcome, note='', source=None) -> None:
    conn.execute('INSERT INTO reviews (course_id, question_id, day, outcome, note, source, created_at) VALUES (?,?,?,?,?,?,?)',
                 (course, qid, day, outcome, note, source, datetime.now(timezone.utc).isoformat()))


def pick_review(db_path: Path, course: str, day: str, limit: int = 2, again: bool = False) -> dict:
    """Choose today's review questions and mark them asked, once per course per day."""
    safe_course_id(course); day = parse_day(day)
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError('limit must be between 1 and 5.')
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        today = conn.execute('SELECT question_id, outcome FROM reviews WHERE course_id=? AND day=? ORDER BY id',
                             (course, day)).fetchall()
        questions = {q['question_id']: q for q in load(conn, course)}
        if today and not again:
            latest = {r['question_id']: r['outcome'] for r in today}
            return dict(day=day, already_started=True, skipped_day=DAY_SKIP in latest,
                        items=[dict(question_id=q, outcome=o, prompt=questions[q]['prompt'])
                               for q, o in latest.items() if q in questions])
        asked = {r['question_id'] for r in today}
        rank = lambda q: (0 if q['status'] == 'needs_help' and recurring(q) else
                          1 if q['status'] == 'needs_help' else 2 if q['status'] == 'unverified' else 3)
        due = [q for q in questions.values() if q['question_id'] not in asked and (q['due'] is None or q['due'] <= day)]
        chosen = sorted(due, key=lambda q: (rank(q), q['last_reviewed'] or '', q['question_id']))[:limit]
        for q in chosen:
            record(conn, course, q['question_id'], day, 'asked')
        return dict(day=day, already_started=False, skipped_day=False,
                    items=[dict(question_id=q['question_id'], prompt=q['prompt'], confusion=q['confusion'],
                                status=q['status'], recurring=recurring(q)) for q in chosen])


def skip_day(db_path: Path, course: str, day: str) -> dict:
    safe_course_id(course); day = parse_day(day)
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        if not conn.execute('SELECT 1 FROM reviews WHERE course_id=? AND day=? AND question_id=?', (course, day, DAY_SKIP)).fetchone():
            record(conn, course, DAY_SKIP, day, 'skipped')
    return dict(day=day, skipped_day=True)


def mark_review(db_path: Path, course: str, qid: str, outcome: str, day: str, note: str = '', source=None) -> dict:
    """Record the learner's actual answer and schedule the next review."""
    safe_course_id(course); question_id(qid); day = parse_day(day)
    if outcome not in OUTCOMES:
        raise ValueError(f'outcome must be one of: {", ".join(OUTCOMES)}.')
    note = (note or '').strip()
    if outcome == 'correct' and not note:
        raise ValueError("A correct answer needs --note with the learner's own words as evidence.")
    with connection(db_path) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT payload FROM questions WHERE course_id=? AND question_id=?', (course, qid)).fetchone()
        if not row:
            raise ValueError(f'Unknown question: {qid}. Add it first.')
        question = json.loads(row['payload'])
        if source is not None and conn.execute(
                'SELECT 1 FROM reviews WHERE course_id=? AND question_id=? AND day=? AND outcome=? AND source=?',
                (course, qid, day, outcome, source)).fetchone():
            return dict(question, recurring=recurring(question))  # replayed import
        record(conn, course, qid, day, outcome, note, source)
        if outcome == 'correct':
            wait = INTERVALS[min(question['streak'], len(INTERVALS) - 1)]
            question['streak'] += 1
            if question['status'] != 'can_apply':
                question['status'] = 'can_explain'
        elif outcome in ('hinted', 'incorrect'):
            wait, question['streak'], question['status'] = INTERVALS[0], 0, 'needs_help'
        if outcome != 'skipped':  # a skip is not a wrong answer and changes nothing
            question['due'] = (date.fromisoformat(day) + timedelta(days=wait)).isoformat()
            question['last_reviewed'] = day
        save(conn, question)
    return dict(question, recurring=recurring(question))
