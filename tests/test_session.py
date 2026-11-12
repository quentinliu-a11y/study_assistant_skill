import copy
import tempfile
import unittest
from pathlib import Path
import common  # noqa: F401
from study_memory.export import export_course
from study_memory.review import add_question, list_questions, review_history
from study_memory.session import import_session
from study_memory.store import pending_batches, read_course


def digest(**changes):
    value = dict(schema_version=1, kind='session_digest', course_id='ifm', date='2026-11-12', source='deepseek-web',
                 next_start='Derive the load factor in a level turn.',
                 items=[dict(question=f'Question {n}', learner_words='', concept_ids=[f'concept-{n}']) for n in range(1, 6)],
                 open_questions=[dict(id='turn-acceleration', confusion='constant speed but accelerating',
                                      prompt='Why is there acceleration at constant speed?')],
                 review_results=[dict(id='turn-acceleration', outcome='incorrect')])
    value.update(changes)
    return value


class SessionDigestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'db.sqlite3'

    def test_digest_becomes_events_questions_and_reviews_and_replay_is_harmless(self):
        first = import_session(self.db, digest(), 'Asia/Singapore')
        self.assertEqual((first['inserted_turns'], first['version']), (5, 2))  # five items: batches of 4 and 1
        again = import_session(self.db, digest(), 'Asia/Singapore')
        self.assertEqual((again['inserted_turns'], again['version'], again['thread_id']), (0, 2, first['thread_id']))
        state = read_course(self.db, 'ifm')
        self.assertEqual(sum(len(u['update']['events']) for u in state['updates']), 5)
        self.assertEqual(pending_batches(self.db, True), [])
        question = list_questions(self.db, 'ifm')[0]
        self.assertEqual((len(question['occurrences']), question['due']), (1, '2026-11-13'))
        self.assertEqual(len(review_history(self.db, 'ifm')), 1)

    def test_mastery_needs_the_learners_own_words_and_export_flags_the_source(self):
        with self.assertRaises(ValueError):
            import_session(self.db, digest(items=[dict(question='q', mastery='can_explain', concept_ids=['c'])]), 'UTC')
        words = 'lift tilts inward so its horizontal part bends the path'
        import_session(self.db, digest(items=[dict(question='q', mastery='can_explain', learner_words=words,
                                                   concept_ids=['turn'])], review_results=[]), 'UTC')
        out = Path(self.tmp.name) / 'out'
        export_course(self.db, 'ifm', out, 'UTC', 'en')
        current = (out / 'ifm/current-state.md').read_text(encoding='utf-8')
        self.assertIn(words, current)
        self.assertIn('not checked against the original messages', current)
        self.assertTrue((out / 'ifm/logs/2026-11-12.md').exists())

    def test_rejected_digest_writes_nothing(self):
        bad = [digest(kind='other'), digest(date='12 Nov'), digest(items=[]), digest(source=''),
               digest(items=[dict(question='q', concept_ids=[])]),
               digest(review_results=[dict(id='never-added', outcome='incorrect')]),
               digest(review_results=[dict(id='turn-acceleration', outcome='correct')]),
               digest(open_questions=[dict(id='new-one')])]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                import_session(self.db, value, 'UTC')
        with self.assertRaises(ValueError):
            import_session(self.db, digest(), 'Not/AZone')
        self.assertEqual(read_course(self.db, 'ifm')['version'], 0)
        self.assertEqual(pending_batches(self.db, True), [])
        self.assertEqual(list_questions(self.db, 'ifm'), [])

    def test_review_result_may_refer_to_an_existing_question(self):
        add_question(self.db, 'ifm', 'older', 'c', 'p')
        value = digest(open_questions=[], review_results=[dict(id='older', outcome='correct', note='said it in my own words')])
        import_session(self.db, value, 'UTC')
        self.assertEqual(list_questions(self.db, 'ifm')[0]['status'], 'can_explain')
