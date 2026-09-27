"""Validate summary provenance; pedagogical interpretation remains human/agent work."""
import copy
from .model import turn_key

MASTERY = {'unverified', 'needs_help', 'can_explain', 'can_apply'}


def reference(value) -> tuple[str, str]:
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or any(not isinstance(v, str) or not v.strip() for v in value)):
        raise ValueError('A source reference must be [thread_id, turn_id].')
    return tuple(value)


def text_list(value, name: str, nonempty: bool = False):
    if (not isinstance(value, list) or (nonempty and not value)
            or any(not isinstance(v, str) or not v.strip() for v in value)):
        raise ValueError(f'{name} must be a list of nonempty strings.')


def validate_update(raw: dict, turns: list[dict], known_events: set[str]) -> dict:
    if not isinstance(raw, dict):
        raise ValueError('Update must be an object.')
    update = copy.deepcopy(raw)
    course, session = turns[0]['course_id'], turns[0]['session_id']
    if update.get('course_id') != course or update.get('session_id') != session:
        raise ValueError('Update course/session does not match its source batch.')
    if not isinstance(update.get('next_start'), str) or not update['next_start'].strip():
        raise ValueError('next_start is required.')
    if not isinstance(update.get('events'), list) or not update['events']:
        raise ValueError('An update needs at least one learning event.')
    source = {turn_key(t): t for t in turns}
    covered = set()
    for event in update['events']:
        required = {'source_turn_ids','concept_ids','question','explanation_status',
                    'mastery','mastery_evidence','links','correction_of'}
        if not isinstance(event, dict) or not required <= event.keys() or 'event_id' in event:
            raise ValueError('Event is missing required fields or contains a generated event_id.')
        if not isinstance(event['source_turn_ids'], list) or not event['source_turn_ids']:
            raise ValueError('Event requires source_turn_ids.')
        refs = {reference(r) for r in event['source_turn_ids']}
        if not refs <= source.keys():
            raise ValueError('Event references a turn outside this batch.')
        covered |= refs
        text_list(event['concept_ids'], 'concept_ids', True)
        text_list(event['links'], 'links')
        if not isinstance(event['question'], str) or not event['question'].strip():
            raise ValueError('Event needs the concrete question or learning gap.')
        if event['explanation_status'] not in ('not_explained','explained','corrected'):
            raise ValueError('Invalid explanation_status.')
        if event['mastery'] not in MASTERY:
            raise ValueError('Invalid mastery state.')
        evidence = event['mastery_evidence']
        if not isinstance(evidence, list):
            raise ValueError('mastery_evidence must be a list.')
        if event['mastery'] in ('can_explain','can_apply') and not evidence:
            raise ValueError('Mastery requires evidence from the user, not the assistant.')
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError('Evidence must contain source_turn_id and quote.')
            ref = reference(item.get('source_turn_id'))
            quote = item.get('quote')
            if (ref not in refs or not isinstance(quote, str) or not quote.strip()
                    or quote not in source[ref]['user_text']):
                raise ValueError('Evidence quote must occur in a referenced user message.')
            if event['mastery'] in ('can_explain','can_apply') and quote.strip(' 。.!！') in ('好','懂了','明白了','OK','ok'):
                raise ValueError('Acknowledgement alone does not establish mastery.')
        correction = event['correction_of']
        if correction is not None and (not isinstance(correction,str) or correction not in known_events):
            raise ValueError('correction_of must reference an existing event in this course.')
    if covered != source.keys():
        raise ValueError('Events must cover every turn in the committed batch.')
    return update
