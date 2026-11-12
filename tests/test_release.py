import importlib.util
import re
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from common import ROOT


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class ReleaseTests(unittest.TestCase):
    def test_each_edition_uses_its_explicit_public_allowlist(self):
        module = load('build_release')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'repo'; root.mkdir()
            for name in {n for files in module.PUBLIC_FILES.values() for n in files} | {'VERSION'}:
                dest = root/name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT/name, dest)
            for name in ['personal/private.md', 'docs/notes.md', '.env', 'skills/study-companion/private.json']:
                p = root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('PRIVATE-CANARY-963', encoding='utf-8')
            archives = module.build_release(root, Path(d)/'out')
            version = (ROOT/'VERSION').read_text(encoding='utf-8').strip()
            self.assertEqual([a.name for a in archives],
                             [f'study-companion-v{version}.zip', f'study-companion-zh-v{version}.zip'])
            for archive, files in zip(archives, module.PUBLIC_FILES.values()):
                with zipfile.ZipFile(archive) as z:
                    self.assertEqual(set(z.namelist()), set(files.values()))
                    self.assertIn(f'{archive.name.split("-v")[0]}/SKILL.md', z.namelist())
                    self.assertFalse(any(b'PRIVATE-CANARY-963' in z.read(n) for n in z.namelist()))

    def test_missing_required_resources_refuse_partial_package(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                load('build_release').build_release(Path(d), Path(d)/'out')

    def test_allowlist_covers_every_file_in_both_skill_folders(self):
        module = load('build_release')
        for edition, files in module.PUBLIC_FILES.items():
            base = ROOT/'skills'/edition
            on_disk = {f'skills/{edition}/{p.relative_to(base).as_posix()}' for p in base.rglob('*')
                       if p.is_file() and '__pycache__' not in p.parts}
            self.assertEqual(on_disk, {f for f in files if f.startswith('skills/')})


class SyncTests(unittest.TestCase):
    def test_chinese_scripts_and_starter_prompts_match_their_sources(self):
        self.assertEqual(load('sync').stale(), [], 'run: python scripts/sync.py')

    def test_starter_prompt_carries_the_rules_and_the_digest_format(self):
        sync = load('sync')
        for language, rule, key in [('en', 'Explained is not mastered', '"kind": "session_digest"'),
                                    ('zh', '讲过不等于掌握', '"kind": "session_digest"')]:
            text = sync.starter(ROOT, language)
            self.assertIn(rule, text); self.assertIn(key, text)
            self.assertLessEqual(len(text), sync.STARTER_LIMIT)

    def test_both_editions_have_the_same_structure(self):
        en, zh = ROOT/'skills/study-companion', ROOT/'skills/study-companion-zh'
        names = lambda base: sorted(p.relative_to(base).as_posix() for p in base.rglob('*.md'))
        self.assertEqual(names(en), names(zh))
        count = lambda p, pattern: len(re.findall(pattern, p.read_text(encoding='utf-8'), re.M))
        for name in names(en):
            for pattern in (r'^#+ ', r'^```', r'^\d+\. ', r'^\|'):
                self.assertEqual(count(en/name, pattern), count(zh/name, pattern), f'{name}: {pattern}')

    def test_rules_do_not_name_a_vendor_and_links_resolve(self):
        for skill in ('study-companion', 'study-companion-zh'):
            for path in (ROOT/'skills'/skill).rglob('*.md'):
                text = path.read_text(encoding='utf-8')
                self.assertIsNone(re.search(r'chatgpt|codex|claude|deepseek|openai|gemini', text, re.I), path)
                for target in re.findall(r'\]\(([^)#]+)\)', text):
                    if not target.startswith('http'):
                        self.assertTrue((path.parent/target).exists(), f'{path}: {target}')

    def test_handoff_format_in_the_docs_matches_the_exporter(self):
        import common  # noqa: F401
        from study_memory.export import TEXT
        for language, skill in (('en', 'study-companion'), ('zh', 'study-companion-zh')):
            doc = (ROOT/'skills'/skill/'references/portable.md').read_text(encoding='utf-8')
            t = TEXT[language]
            for key in ('next_heading', 'open_concepts', 'open_questions'):
                self.assertIn(t[key], doc)
            self.assertIn(t['handoff_title'].format('<course_id>'), doc)
            self.assertIn(t['last_day'].split('{')[0], doc)
