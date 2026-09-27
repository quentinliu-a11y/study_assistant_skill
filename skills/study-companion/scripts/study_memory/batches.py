"""Deterministic per-course, per-session, per-thread four-turn batching."""
from collections import defaultdict
from .model import eligible, turn_key, validate_turn


def select_batches(turns: list[dict], processed: set[tuple[str, str]],
                   flush: bool = False) -> list[list[dict]]:
    unique = {}
    for raw in turns:
        t = validate_turn(raw)
        key = turn_key(t)
        if key in unique and unique[key]['revision_hash'] != t['revision_hash']:
            raise ValueError(f'Conflicting turn revision: {key}')
        unique[key] = t
    groups = defaultdict(list)
    for key, t in unique.items():
        if key not in processed and eligible(t):
            groups[(t['course_id'], t['session_id'], t['thread_id'])].append(t)
    batches = []
    for group in sorted(groups):
        ordered = sorted(groups[group], key=lambda t: (t['occurred_at'], t['turn_id']))
        for offset in range(0, len(ordered), 4):
            batch = ordered[offset:offset + 4]
            if len(batch) == 4 or flush:
                batches.append(batch)
    return batches
