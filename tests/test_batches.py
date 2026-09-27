import unittest
from common import turn
from study_memory.batches import select_batches


class BatchTests(unittest.TestCase):
    def test_four_eight_and_flush(self):
        ts = [turn(n) for n in range(1, 9)]
        self.assertEqual([len(b) for b in select_batches(ts, set())], [4, 4])
        self.assertEqual(select_batches(ts[:3], set()), [])
        self.assertEqual([len(b) for b in select_batches(ts[:3], set(), True)], [3])

    def test_duplicates_nonlearning_incomplete_and_unconfirmed(self):
        ts = [turn(n) for n in range(1, 5)]
        extras = [turn(5, is_learning=False), turn(6, complete=False), turn(7, learning_confirmed=False)]
        self.assertEqual([len(b) for b in select_batches(ts + ts + extras, set(), True)], [4])

    def test_sessions_and_threads_do_not_mix(self):
        ts = [turn(1), turn(2), turn(3, session_id='s2'), turn(4, session_id='s2')]
        self.assertEqual(select_batches(ts, set()), [])
        ts += [turn(1, thread_id='other'), turn(2, thread_id='other')]
        self.assertEqual([len(b) for b in select_batches(ts, set(), True)], [2, 2, 2])

    def test_order_is_stable_and_processed_not_repeated(self):
        ts = [turn(n) for n in range(1, 7)]
        done = {('thread-1', 'turn-1'), ('thread-1', 'turn-2')}
        self.assertEqual(select_batches(ts, done), select_batches(list(reversed(ts)), done))
        self.assertEqual([t['turn_id'] for t in select_batches(ts, done)[0]], ['turn-3','turn-4','turn-5','turn-6'])

    def test_conflicting_revision_rejected(self):
        with self.assertRaises(ValueError):
            select_batches([turn(), turn(user_text='edited')], set(), True)
