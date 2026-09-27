"""Validate external data before counting or writing it."""
from datetime import datetime, timezone
import hashlib
import json
import re

TURN_FIELDS = ('schema_version', 'course_id', 'session_id', 'thread_id', 'turn_id',
               'occurred_at', 'user_text', 'assistant_text', 'complete',
               'learning_confirmed', 'is_learning')


def safe_course_id(value: str) -> str:
    reserved = {'con', 'prn', 'aux', 'nul'} | {f'{p}{i}' for p in ('com','lpt') for i in range(1,10)}
    if (not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', value)
            or value in reserved):
        raise ValueError('course_id must be a safe lowercase course slug.')
    return value


def parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError('occurred_at must be an ISO timestamp with timezone.')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Invalid occurred_at timestamp.') from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('occurred_at needs an explicit timezone; do not guess the date.')
    return result.astimezone(timezone.utc)


def digest(value) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def validate_turn(raw: dict) -> dict:
    if not isinstance(raw, dict) or any(f not in raw for f in TURN_FIELDS):
        raise ValueError('Turn is missing required fields.')
    t = {f: raw[f] for f in TURN_FIELDS}
    if type(t['schema_version']) is not int or t['schema_version'] != 1:
        raise ValueError('Unsupported schema_version.')
    safe_course_id(t['course_id'])
    for field in ('session_id', 'thread_id', 'turn_id', 'user_text'):
        if not isinstance(t[field], str) or not t[field].strip():
            raise ValueError(f'{field} must be nonempty text.')
    for field in ('complete', 'learning_confirmed', 'is_learning'):
        if type(t[field]) is not bool:
            raise ValueError(f'{field} must be a boolean.')
    if not isinstance(t['assistant_text'], str) or (t['complete'] and not t['assistant_text'].strip()):
        raise ValueError('A completed turn needs its full assistant response.')
    t['occurred_at'] = parse_time(t['occurred_at']).isoformat()
    t['revision_hash'] = digest(t)
    if 'revision_hash' in raw and raw['revision_hash'] != t['revision_hash']:
        raise ValueError('Turn revision_hash does not match the content.')
    return t


def turn_key(t: dict) -> tuple[str, str]:
    return t['thread_id'], t['turn_id']


def eligible(t: dict) -> bool:
    return t['complete'] and t['learning_confirmed'] and t['is_learning']
