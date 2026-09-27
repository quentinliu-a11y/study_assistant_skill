import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills' / 'study-companion' / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def turn(n=1, **changes):
    value = dict(schema_version=1, course_id='aerodynamics', session_id='session-1',
                 thread_id='thread-1', turn_id=f'turn-{n}',
                 occurred_at=f'2026-09-27T10:{n:02d}:00+08:00',
                 user_text=f'问题 {n}', assistant_text=f'解释 {n}', complete=True,
                 learning_confirmed=True, is_learning=True)
    value.update(changes)
    return value


def summary(turns, **changes):
    value = dict(course_id=turns[0]['course_id'], session_id=turns[0]['session_id'],
                 events=[dict(source_turn_ids=[[t['thread_id'], t['turn_id']] for t in turns],
                              concept_ids=['pressure-gradient'], question='为什么会分离？',
                              explanation_status='explained', mastery='unverified',
                              mastery_evidence=[], links=['boundary-layer'], correction_of=None)],
                 next_start='检验逆压梯度的理解')
    value.update(changes)
    return value
