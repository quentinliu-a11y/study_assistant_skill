"""Import a session digest written by an assistant that cannot run this tool (web chat, no file access)."""
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .model import digest, parse_day, safe_course_id, validate_turn
from .review import OUTCOMES, STATUSES, add_question, list_questions, mark_review, question_id, text
from .store import commit_update, import_turns, read_course
from .updates import validate_update

NO_ANSWER = '(session digest: the full explanation was not recorded)'


def zone_of(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as error:
        raise ValueError('Unknown timezone. On Windows install tzdata if IANA data is missing.') from error


def import_session(db_path: Path, raw: dict, timezone: str) -> dict:
    """Digest items become marked turns and events; re-importing the same digest changes nothing."""
    if not isinstance(raw, dict) or raw.get('schema_version') != 1 or raw.get('kind') != 'session_digest':
        raise ValueError("A digest is an object with schema_version 1 and kind 'session_digest'.")
    course, day = safe_course_id(raw.get('course_id')), parse_day(raw.get('date'))
    text(raw.get('source'), 'source'); next_start = text(raw.get('next_start'), 'next_start')
    items = raw.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 40:
        raise ValueError('A digest needs 1 to 40 items.')
    zone, thread = zone_of(timezone), 'digest-' + digest(raw)[:12]
    start = datetime.combine(date.fromisoformat(day), time(12), zone)  # digests carry a date, not message times
    turns, events = [], []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError('Each digest item must be an object.')
        words = item.get('learner_words') or ''
        if not isinstance(words, str):
            raise ValueError('learner_words must be text.')
        question, mastery = text(item.get('question'), 'question'), item.get('mastery', 'unverified')
        if mastery in ('can_explain', 'can_apply') and not words.strip():
            raise ValueError("Mastery in a digest needs learner_words: the learner's own answer.")
        ref = [thread, f'item-{index + 1}']
        turns.append(dict(schema_version=1, course_id=course, session_id=thread, thread_id=thread, turn_id=ref[1],
                          occurred_at=(start + timedelta(minutes=index)).isoformat(),
                          user_text=words.strip() or question, assistant_text=item.get('explanation') or NO_ANSWER,
                          complete=True, learning_confirmed=True, is_learning=True, source_kind='digest'))
        evidence = [dict(source_turn_id=ref, quote=words.strip())] if mastery in ('can_explain', 'can_apply') else []
        events.append(dict(source_turn_ids=[ref], concept_ids=item.get('concept_ids'), question=question,
                           explanation_status=item.get('explanation_status', 'explained'), mastery=mastery,
                           mastery_evidence=evidence, links=item.get('links', []), correction_of=None))
    open_questions, results = raw.get('open_questions', []), raw.get('review_results', [])
    if not isinstance(open_questions, list) or not isinstance(results, list):
        raise ValueError('open_questions and review_results must be lists.')
    for entry in open_questions + results:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str):
            raise ValueError('Each open question and review result needs an id.')
    if any(q.get('status', 'unverified') not in STATUSES for q in open_questions) or any(
            r.get('outcome') not in OUTCOMES for r in results):
        raise ValueError('Invalid question status or review outcome in digest.')
    # Check everything before the first write, so a rejected digest leaves no half-imported turns.
    for offset in range(0, len(turns), 4):
        validate_update(dict(course_id=course, session_id=thread, events=events[offset:offset + 4], next_start=next_start),
                        [validate_turn(t) for t in turns[offset:offset + 4]], set())
    known = {q['question_id'] for q in list_questions(db_path, course)}
    for q in open_questions:
        question_id(q['id'])
        if q['id'] not in known:
            text(q.get('confusion'), 'confusion'); text(q.get('prompt'), 'prompt')
    for r in results:
        if r['id'] not in known | {q['id'] for q in open_questions}:
            raise ValueError(f"Review result refers to an unknown question: {r['id']}.")
        if r['outcome'] == 'correct' and not (r.get('note') or '').strip():
            raise ValueError("A correct review result needs a note with the learner's own words.")
    inserted = import_turns(db_path, turns)
    version = read_course(db_path, course)['version']
    for offset in range(0, len(turns), 4):
        chunk = range(offset, min(offset + 4, len(turns)))
        update = dict(course_id=course, session_id=thread, events=[events[i] for i in chunk], next_start=next_start)
        version = commit_update(db_path, [[thread, turns[i]['turn_id']] for i in chunk], update,
                                read_course(db_path, course)['version'])
    for q in open_questions:
        add_question(db_path, course, q['id'], q.get('confusion'), q.get('prompt'), q.get('concept_ids'),
                     q.get('status'), day, thread, q.get('note', ''))
    for r in results:
        mark_review(db_path, course, r['id'], r['outcome'], day, r.get('note', ''), source=thread)
    return dict(thread_id=thread, inserted_turns=inserted, version=version,
                questions=len(open_questions), review_results=len(results))
