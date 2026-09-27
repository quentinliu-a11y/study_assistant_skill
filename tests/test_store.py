import copy
from contextlib import closing
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import turn, summary
from study_memory.store import import_turns, pending_batches, commit_update, read_course


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / '学习.sqlite3'
        self.ts = [turn(n) for n in range(1, 5)]
        self.ids = [(t['thread_id'], t['turn_id']) for t in self.ts]

    def test_atomic_idempotent_commit(self):
        self.assertEqual(import_turns(self.db, self.ts), 4)
        self.assertEqual(import_turns(self.db, self.ts), 0)
        update = summary(self.ts)
        self.assertEqual(commit_update(self.db, self.ids, update, 0), 1)
        self.assertEqual(pending_batches(self.db, True), [])
        self.assertEqual(commit_update(self.db, self.ids, update, 0), 1)
        state = read_course(self.db, 'aerodynamics')
        self.assertEqual(state['version'], 1)
        self.assertEqual(len(state['updates']), 1)
        changed = summary(self.ts, next_start='changed')
        with self.assertRaises(ValueError):
            commit_update(self.db, self.ids, changed, 1)

    def test_conflicting_import_rolls_back_all_new_rows(self):
        import_turns(self.db, self.ts)
        with self.assertRaises(ValueError):
            import_turns(self.db, [turn(5), turn(1, user_text='edited')])
        self.assertEqual(sum(map(len, pending_batches(self.db, True))), 4)

    def test_incomplete_snapshot_can_finish_before_counting(self):
        import_turns(self.db, [turn(1, complete=False, assistant_text='')])
        self.assertEqual(pending_batches(self.db, True), [])
        import_turns(self.db, [turn(1)])
        self.assertEqual(len(pending_batches(self.db, True)[0]), 1)

    def test_failed_transaction_leaves_pending_and_version_unchanged(self):
        import_turns(self.db, self.ts)
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("CREATE TRIGGER fail_write BEFORE UPDATE OF processed ON turns BEGIN SELECT RAISE(ABORT, 'disk simulation'); END")
        with self.assertRaises(sqlite3.DatabaseError):
            commit_update(self.db, self.ids, summary(self.ts), 0)
        self.assertEqual(len(pending_batches(self.db)[0]), 4)
        self.assertEqual(read_course(self.db, 'aerodynamics')['version'], 0)

    def test_concurrent_different_sessions_detect_stale_version(self):
        other = [turn(n, session_id='second', thread_id='second') for n in range(1,5)]
        import_turns(self.db, self.ts + other)
        def write(ts):
            try:
                return commit_update(self.db, [(t['thread_id'],t['turn_id']) for t in ts], summary(ts), 0)
            except ValueError:
                return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(write, [self.ts, other]))
        self.assertCountEqual(result, [1, 'conflict'])
        self.assertEqual(sum(map(len, pending_batches(self.db, True))), 4)

    def test_flush_resets_only_committed_turns(self):
        import_turns(self.db, self.ts[:2])
        commit_update(self.db, self.ids[:2], summary(self.ts[:2]), 0)
        import_turns(self.db, self.ts[2:])
        self.assertEqual(pending_batches(self.db), [])
        self.assertEqual(len(pending_batches(self.db, True)[0]), 2)

    def test_invalid_events_and_batch_cannot_advance_checkpoint(self):
        import_turns(self.db, self.ts)
        invalid = []
        a = summary(self.ts); a['events'][0]['source_turn_ids'] = [['other','bad']]; invalid.append(a)
        a = summary(self.ts); a['events'] = []; invalid.append(a)
        a = summary(self.ts); a['events'][0]['mastery'] = 'can_apply'; invalid.append(a)
        a = summary(self.ts); a['events'][0]['correction_of'] = 'missing'; invalid.append(a)
        a = summary(self.ts); a['events'][0]['mastery'] = 'can_explain'; a['events'][0]['mastery_evidence'] = [dict(source_turn_id=self.ids[0], quote='not said')]; invalid.append(a)
        for update in invalid:
            with self.subTest(update=update), self.assertRaises(ValueError):
                commit_update(self.db, self.ids, update, 0)
        with self.assertRaises(ValueError):
            commit_update(self.db, self.ids[1:], summary(self.ts[1:]), 0)
        self.assertEqual(read_course(self.db, 'aerodynamics')['version'], 0)

    def test_real_user_quote_required_for_mastery_and_corrections_preserved(self):
        import_turns(self.db, self.ts)
        update = summary(self.ts)
        update['events'][0]['mastery'] = 'can_explain'
        update['events'][0]['mastery_evidence'] = [dict(source_turn_id=self.ids[0], quote=self.ts[0]['user_text'])]
        commit_update(self.db, self.ids, update, 0)
        event_id = read_course(self.db, 'aerodynamics')['updates'][0]['update']['events'][0]['event_id']
        new_turn = turn(5)
        import_turns(self.db, [new_turn])
        corrected = summary([new_turn]); corrected['events'][0]['correction_of'] = event_id
        commit_update(self.db, [('thread-1','turn-5')], corrected, 1)
        self.assertEqual(len(read_course(self.db, 'aerodynamics')['updates']), 2)
