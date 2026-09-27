import json
import tempfile
import unittest
from pathlib import Path
from common import ROOT
from study_memory.profile import missing_profile_fields, save_profile


class ProfileTests(unittest.TestCase):
    def test_asks_both_required_fields_and_only_missing(self):
        self.assertEqual(missing_profile_fields({}), ['major', 'degree_level'])
        self.assertEqual(missing_profile_fields({'profile': {'major': '航空航天工程'}}), ['degree_level'])

    def test_save_and_edit_preserve_course_settings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / '个人资料.json'
            p.write_text(json.dumps({'courses': [{'course_id': 'aero'}], 'timezone': 'UTC'}))
            config = save_profile(p, '航空航天工程', 'undergraduate')
            self.assertEqual(missing_profile_fields(config), [])
            save_profile(p, '机械工程', 'masters')
            data = json.loads(p.read_text(encoding='utf-8'))
            self.assertEqual(data['profile'], {'major': '机械工程', 'degree_level': 'masters'})
            self.assertEqual(data['courses'], [{'course_id': 'aero'}])
            self.assertEqual(data['timezone'], 'UTC')

    def test_unknown_or_empty_values_not_guessed(self):
        with tempfile.TemporaryDirectory() as d:
            for major, degree in [('', 'masters'), ('Engineering', 'TUM'), ('Engineering', '')]:
                with self.subTest(major=major, degree=degree), self.assertRaises(ValueError):
                    save_profile(Path(d) / 'config.json', major, degree)
