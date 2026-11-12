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
        result = self.run_cli('profile', '--config', self.config, '--lang', 'zh', input='航空航天工程\n2\n')
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

    def test_new_profile_defaults_to_english_and_legacy_config_stays_chinese(self):
        result = self.run_cli('profile', '--config', self.config, input='Aerospace Engineering\n2\n')
        self.assertIn('major', result.stdout)
        self.assertEqual(json.loads(self.config.read_text(encoding='utf-8'))['language'], 'en')
        legacy = self.root/'legacy.json'
        legacy.write_text(json.dumps(dict(schema_version=1, batch_size=4, timezone='Asia/Shanghai', courses=[],
                                          profile=dict(major='机械工程', degree_level='masters'))), encoding='utf-8')
        source = self.root/'turns.json'; source.write_text(json.dumps([turn()]), encoding='utf-8')
        self.assertEqual(self.run_cli('import','--config',legacy,'--db',self.db,'--input',source).returncode, 0)
        ids = dict(batch_ids=[['thread-1','turn-1']], update=summary([turn()]))
        payload = self.root/'update.json'; payload.write_text(json.dumps(ids), encoding='utf-8')
        self.run_cli('commit','--config',legacy,'--db',self.db,'--input',payload,'--expected-version','0')
        self.run_cli('export','--db',self.db,'--config',legacy,'--course','aerodynamics','--out',self.root/'exports')
        self.assertIn('学习状态', (self.root/'exports/aerodynamics/current-state.md').read_text(encoding='utf-8'))

    def test_export_reads_timezone_and_language_from_config(self):
        self.run_cli('profile','--config',self.config,'--major','Aerospace','--degree','masters','--timezone','UTC')
        t = turn(1, occurred_at='2026-09-27T00:30:00+08:00')
        source = self.root/'turns.json'; source.write_text(json.dumps([t]), encoding='utf-8')
        self.run_cli('import','--config',self.config,'--db',self.db,'--input',source)
        payload = self.root/'update.json'
        payload.write_text(json.dumps(dict(batch_ids=[['thread-1','turn-1']], update=summary([t]))), encoding='utf-8')
        self.run_cli('commit','--config',self.config,'--db',self.db,'--input',payload,'--expected-version','0')
        result = self.run_cli('export','--db',self.db,'--config',self.config,'--course','aerodynamics','--out',self.root/'exports')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root/'exports/aerodynamics/logs/2026-09-26.md').exists())  # UTC day, not Shanghai
        self.assertIn('study state', (self.root/'exports/aerodynamics/current-state.md').read_text(encoding='utf-8'))

    def test_review_commands_round_trip(self):
        add = ('question','add','--db',self.db,'--course','ifm','--id','thrust-power','--confusion','T vs P',
               '--prompt','Why is jet thrust roughly constant?','--date','2026-10-14','--source','log-1')
        self.assertEqual(self.run_cli(*add).returncode, 0)
        picked = json.loads(self.run_cli('review','pick','--db',self.db,'--course','ifm','--date','2026-11-12').stdout)
        self.assertEqual([i['question_id'] for i in picked['items']], ['thrust-power'])
        bad = self.run_cli('review','mark','--db',self.db,'--course','ifm','--id','thrust-power','--outcome','correct','--date','2026-11-12')
        self.assertEqual(bad.returncode, 2)
        good = self.run_cli('review','mark','--db',self.db,'--course','ifm','--id','thrust-power','--outcome','correct',
                            '--date','2026-11-12','--note','thrust is set by mass flow, not speed')
        self.assertEqual(json.loads(good.stdout)['due'], '2026-11-13')

    def test_pending_shows_versions_to_support_read_merge(self):
        result = self.run_cli('pending','--db',self.db)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['course_versions'], {})
