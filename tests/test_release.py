import importlib.util
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from common import ROOT


class ReleaseTests(unittest.TestCase):
    def builder(self):
        path = ROOT/'scripts/build_release.py'
        self.assertTrue(path.exists(), 'Release builder is not implemented yet')
        spec = importlib.util.spec_from_file_location('release_builder',path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_package_uses_explicit_public_allowlist(self):
        module = self.builder()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'repo'; root.mkdir()
            for name in module.PUBLIC_FILES:
                dest=root/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/name,dest)
            for name in ['personal/private.md','docs/notes.md','.env','skills/study-companion/private.json']:
                p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('PRIVATE-CANARY-963',encoding='utf-8')
            archive=module.build_release(root,Path(d)/'out')
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(set(z.namelist()),set(module.PUBLIC_FILES))
                self.assertFalse(any(b'PRIVATE-CANARY-963' in z.read(n) for n in z.namelist()))

    def test_missing_required_resources_refuse_partial_package(self):
        module = self.builder()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                module.build_release(Path(d),Path(d)/'out')
