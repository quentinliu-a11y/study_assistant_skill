import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Event
from pathlib import Path
from unittest.mock import patch
from common import turn, summary
from study_memory.store import import_turns, commit_update
from study_memory.export import export_course
from study_memory.io import atomic_text


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

    def test_concurrent_exports_cannot_regress_to_old_snapshot(self):
        paused, release = Event(), Event()
        def pause_old(path, text):
            if path.name == 'current-state.md' and '课程版本：1；' in text:
                paused.set()
                if not release.wait(5):
                    raise RuntimeError('Test did not release old export')
            atomic_text(path, text)
        with patch('study_memory.export.atomic_text', side_effect=pause_old), ThreadPoolExecutor(max_workers=2) as pool:
            old = pool.submit(export_course,self.db,'aerodynamics',self.out,'Asia/Shanghai')
            try:
                self.assertTrue(paused.wait(3))
                t = turn(3)
                import_turns(self.db,[t])
                commit_update(self.db,[('thread-1','turn-3')],summary([t]),1)
                new = pool.submit(export_course,self.db,'aerodynamics',self.out,'Asia/Shanghai')
                try:
                    new.result(timeout=0.25)
                except TimeoutError:
                    pass  # Correct implementation serializes behind the paused export.
            finally:
                release.set()
            old.result(timeout=5); new.result(timeout=5)
        current=(self.out/'aerodynamics/current-state.md').read_text(encoding='utf-8')
        self.assertIn('课程版本：2；',current)
        self.assertIn('turn-3',current)

    def test_multiconcept_event_only_renders_still_current_concepts(self):
        t=turn(3); import_turns(self.db,[t])
        both=summary([t]); both['events'][0]['concept_ids']=['lift','drag']
        commit_update(self.db,[('thread-1','turn-3')],both,1)
        t=turn(4); import_turns(self.db,[t])
        newer=summary([t]); newer['events'][0].update(concept_ids=['lift'],mastery='can_apply',
            mastery_evidence=[dict(source_turn_id=['thread-1','turn-4'],quote=t['user_text'])])
        commit_update(self.db,[('thread-1','turn-4')],newer,2)
        export_course(self.db,'aerodynamics',self.out,'Asia/Shanghai')
        current=(self.out/'aerodynamics/current-state.md').read_text(encoding='utf-8')
        headings=[line for line in current.splitlines() if line.startswith('### ')]
        self.assertEqual(sum('lift' in line for line in headings),1)
        self.assertIn('### drag',headings)
        self.assertIn('可独立应用',current.split('### lift')[1])

    def test_timezone_change_removes_only_obsolete_managed_logs(self):
        export_course(self.db,'aerodynamics',self.out,'Asia/Shanghai')
        manual=self.out/'aerodynamics/logs/my-notes.md'; manual.write_text('keep',encoding='utf-8')
        export_course(self.db,'aerodynamics',self.out,'UTC')
        self.assertFalse((self.out/'aerodynamics/logs/2026-09-27.md').exists())
        self.assertTrue((self.out/'aerodynamics/logs/2026-09-26.md').exists())
        self.assertEqual(manual.read_text(encoding='utf-8'),'keep')

    def test_timezone_change_does_not_delete_manually_edited_old_log(self):
        export_course(self.db,'aerodynamics',self.out,'Asia/Shanghai')
        edited=self.out/'aerodynamics/logs/2026-09-27.md'; edited.write_text('personal annotation',encoding='utf-8')
        with self.assertRaises(ValueError):
            export_course(self.db,'aerodynamics',self.out,'UTC')
        self.assertEqual(edited.read_text(encoding='utf-8'),'personal annotation')
