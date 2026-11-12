import tempfile
import unittest
from pathlib import Path
import common  # noqa: F401  (adds the scripts directory to sys.path)
from study_memory.review import add_question, list_questions, mark_review, pick_review, review_history, skip_day


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'db.sqlite3'

    def add(self, qid, **kw):
        return add_question(self.db, 'ifm', qid, kw.pop('confusion', 'c'), kw.pop('prompt', f'ask {qid}'), **kw)

    def test_same_source_counts_once_and_two_sources_make_it_recurring(self):
        self.add('q', day='2026-10-14', source='thread-a')
        self.assertFalse(add_question(self.db, 'ifm', 'q', day='2026-10-14', source='thread-a')['recurring'])
        q = add_question(self.db, 'ifm', 'q', day='2026-10-16', source='thread-b')
        self.assertTrue(q['recurring']); self.assertEqual(len(q['occurrences']), 2)
        self.assertEqual(q['prompt'], 'ask q')  # an occurrence does not need the text again

    def test_new_question_needs_text_and_valid_id(self):
        for args in [('Bad Id', 'c', 'p'), ('q', '', 'p'), ('q', 'c', None)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                add_question(self.db, 'ifm', *args)
        with self.assertRaises(ValueError):
            add_question(self.db, 'ifm', 'q', 'c', 'p', day='2026-10-14')  # date without source

    def test_pick_prefers_recurring_help_then_help_then_unverified_and_runs_once_a_day(self):
        self.add('unverified')
        self.add('help', status='needs_help')
        self.add('recurring-help', status='needs_help', day='2026-10-14', source='a')
        add_question(self.db, 'ifm', 'recurring-help', day='2026-10-16', source='b')
        self.add('known', status='can_apply')
        first = pick_review(self.db, 'ifm', '2026-11-12')
        self.assertEqual([i['question_id'] for i in first['items']], ['recurring-help', 'help'])
        again = pick_review(self.db, 'ifm', '2026-11-12')
        self.assertTrue(again['already_started'])
        self.assertEqual({i['question_id'] for i in again['items']}, {'recurring-help', 'help'})
        extra = pick_review(self.db, 'ifm', '2026-11-12', again=True)
        self.assertEqual([i['question_id'] for i in extra['items']], ['unverified', 'known'])
        self.assertFalse(pick_review(self.db, 'aero', '2026-11-12')['already_started'])  # courses are separate

    def test_correct_answers_follow_1_3_7_14_30_and_a_miss_resets_to_one_day(self):
        self.add('q')
        days = ['2026-11-01', '2026-11-02', '2026-11-05', '2026-11-12', '2026-11-26', '2026-12-26']
        due = [mark_review(self.db, 'ifm', 'q', 'correct', d, 'explained it unaided')['due'] for d in days]
        self.assertEqual(due, ['2026-11-02', '2026-11-05', '2026-11-12', '2026-11-26', '2026-12-26', '2027-01-25'])
        q = mark_review(self.db, 'ifm', 'q', 'incorrect', '2027-01-25')
        self.assertEqual((q['due'], q['streak'], q['status']), ('2027-01-26', 0, 'needs_help'))
        q = mark_review(self.db, 'ifm', 'q', 'hinted', '2027-01-26')
        self.assertEqual((q['due'], q['status']), ('2027-01-27', 'needs_help'))

    def test_not_due_questions_wait_and_skip_changes_nothing(self):
        self.add('q')
        mark_review(self.db, 'ifm', 'q', 'correct', '2026-11-01', 'my own derivation')
        self.assertEqual(pick_review(self.db, 'ifm', '2026-11-01', again=True)['items'], [])
        before = list_questions(self.db, 'ifm')[0]
        self.assertEqual(before['status'], 'can_explain')
        mark_review(self.db, 'ifm', 'q', 'skipped', '2026-11-02')
        after = list_questions(self.db, 'ifm')[0]
        self.assertEqual((after['due'], after['streak'], after['status']), (before['due'], before['streak'], before['status']))

    def test_correct_needs_learner_words_and_unknown_question_is_rejected(self):
        self.add('q')
        with self.assertRaises(ValueError):
            mark_review(self.db, 'ifm', 'q', 'correct', '2026-11-01')
        with self.assertRaises(ValueError):
            mark_review(self.db, 'ifm', 'missing', 'incorrect', '2026-11-01')
        with self.assertRaises(ValueError):
            mark_review(self.db, 'ifm', 'q', 'incorrect', '11/01/2026')
        self.assertEqual(review_history(self.db, 'ifm'), [])

    def test_skipping_the_day_blocks_an_automatic_second_round(self):
        self.add('q')
        skip_day(self.db, 'ifm', '2026-11-12'); skip_day(self.db, 'ifm', '2026-11-12')
        result = pick_review(self.db, 'ifm', '2026-11-12')
        self.assertTrue(result['already_started']); self.assertTrue(result['skipped_day'])
        self.assertEqual(len(review_history(self.db, 'ifm')), 1)
        self.assertEqual(len(pick_review(self.db, 'ifm', '2026-11-13')['items']), 1)

    def test_no_database_means_no_questions(self):
        self.assertEqual(list_questions(self.db, 'ifm'), [])
        self.assertFalse(self.db.exists())
