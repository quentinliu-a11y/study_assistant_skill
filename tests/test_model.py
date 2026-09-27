import unittest
from common import turn
from study_memory.model import validate_turn


class ModelTests(unittest.TestCase):
    def test_normalizes_time_and_computes_revision(self):
        t = validate_turn(turn())
        self.assertEqual(t['occurred_at'], '2026-09-27T02:01:00+00:00')
        self.assertEqual(len(t['revision_hash']), 64)
        self.assertEqual(validate_turn(t), t)

    def test_rejects_bad_timestamp_and_unsafe_course(self):
        for changes in [dict(occurred_at='2026-09-27T12:00:00'), dict(occurred_at=''),
                        dict(course_id='../escape'), dict(course_id='CON'),
                        dict(complete='false'), dict(turn_id=''), dict(schema_version=True),
                        dict(assistant_text=''), dict(revision_hash='fake')]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_turn(turn(**changes))

    def test_incomplete_response_can_be_empty(self):
        self.assertFalse(validate_turn(turn(complete=False, assistant_text=''))['complete'])
