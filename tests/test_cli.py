import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from common import SCRIPTS, turn, summary


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root/'config.json'; self.db = self.root/'study.sqlite3'

    def run_cli(self, *args, input=None):
        return subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPTS/'study_store.py'), *map(str,args)],
                              input=input, text=True, encoding='utf-8', capture_output=True)

    def test_entrypoint_prompts_for_major_and_degree(self):
        result = self.run_cli('profile', '--config', self.config, input='航空航天工程\n2\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(self.config.read_text(encoding='utf-8'))
        self.assertEqual(config['profile'], dict(major='航空航天工程', degree_level='masters'))
        self.assertIn('专业', result.stdout); self.assertIn('本科', result.stdout)

    def test_profile_missing_refuses_import_without_creating_db(self):
        source = self.root/'turns.json'; source.write_text(json.dumps([turn()]), encoding='utf-8')
        result = self.run_cli('import','--config',self.config,'--db',self.db,'--input',source)
        self.assertEqual(result.returncode, 2)
        self.assertIn('profile', result.stderr)
        self.assertFalse(self.db.exists())

    def test_end_to_end_commands_and_repeat(self):
        result = self.run_cli('profile','--config',self.config,'--major','航空航天工程','--degree','masters')
        self.assertEqual(result.returncode, 0, result.stderr)
        ts = [turn(n) for n in range(1,5)]
        source = self.root/'turns.json'; source.write_text(json.dumps(ts), encoding='utf-8')
        result = self.run_cli('import','--config',self.config,'--db',self.db,'--input',source)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cli('pending','--db',self.db)
        self.assertEqual(len(json.loads(result.stdout)['batches'][0]), 4)
        payload = self.root/'update.json'
        payload.write_text(json.dumps(dict(batch_ids=[[t['thread_id'],t['turn_id']] for t in ts], update=summary(ts))), encoding='utf-8')
        for _ in range(2):
            result = self.run_cli('commit','--config',self.config,'--db',self.db,'--input',payload,'--expected-version','0')
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cli('export','--db',self.db,'--course','aerodynamics','--out',self.root/'exports','--timezone','UTC')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root/'exports/aerodynamics/current-state.md').exists())
        result = self.run_cli('pending','--db',self.db)
        self.assertEqual(json.loads(result.stdout)['batches'], [])

    def test_pending_shows_versions_to_support_read_merge(self):
        result = self.run_cli('pending','--db',self.db)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['course_versions'], {})
