import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from common import turn, summary
from study_memory.store import import_turns, commit_update
from study_memory.export import export_course


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'db.sqlite3'
        self.out = Path(self.tmp.name) / '个人记录'
        self.ts = [turn(1, occurred_at='2026-09-26T23:59:00+08:00'),
                   turn(2, occurred_at='2026-09-27T00:01:00+08:00')]
        import_turns(self.db, self.ts)
        commit_update(self.db, [('thread-1','turn-1'),('thread-1','turn-2')], summary(self.ts), 0)

    def test_cross_day_uses_source_times_and_reexport_is_identical(self):
        paths = export_course(self.db, 'aerodynamics', self.out, 'Asia/Shanghai')
        self.assertEqual({p.name for p in paths}, {'current-state.md','2026-09-26.md','2026-09-27.md'})
        contents = {p: p.read_bytes() for p in paths}
        export_course(self.db, 'aerodynamics', self.out, 'Asia/Shanghai')
        self.assertEqual(contents, {p: p.read_bytes() for p in paths})
        self.assertIn('待验证', (self.out/'aerodynamics/current-state.md').read_text(encoding='utf-8'))
        self.assertIn('thread-1 / turn-1', (self.out/'aerodynamics/logs/2026-09-26.md').read_text(encoding='utf-8'))

    def test_interrupted_export_recovers(self):
        with patch('study_memory.export.atomic_text', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                export_course(self.db, 'aerodynamics', self.out, 'Asia/Shanghai')
        self.assertEqual(len(export_course(self.db, 'aerodynamics', self.out, 'Asia/Shanghai')), 3)

    def test_second_batch_keeps_same_day_history_and_previous_concepts(self):
        t = turn(3)
        import_turns(self.db, [t])
        update = summary([t]); update['events'][0]['concept_ids'] = ['lift']
        commit_update(self.db, [('thread-1','turn-3')], update, 1)
        export_course(self.db, 'aerodynamics', self.out, 'Asia/Shanghai')
        current = (self.out/'aerodynamics/current-state.md').read_text(encoding='utf-8')
        day = (self.out/'aerodynamics/logs/2026-09-27.md').read_text(encoding='utf-8')
        self.assertIn('pressure-gradient', current)
        self.assertIn('lift', current)
        self.assertIn('turn-2', day)
        self.assertIn('turn-3', day)

    def test_bad_course_and_unknown_timezone_rejected(self):
        for course, tz in [('../escape','UTC'), ('CON','UTC'), ('aerodynamics','Invalid/Zone')]:
            with self.subTest(course=course, tz=tz), self.assertRaises(ValueError):
                export_course(self.db, course, self.out, tz)
