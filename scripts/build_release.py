"""Package only known public files, never an entire user's workspace.

Each archive holds one skill folder, ready to unpack into a skills directory or upload as a skill.
"""
import argparse
from pathlib import Path
import zipfile

SKILL_FILES = (
    'SKILL.md', 'agents/openai.yaml',
    'references/teaching.md', 'references/records.md', 'references/review.md',
    'references/courses.md', 'references/cli.md', 'references/portable.md',
    'scripts/study_store.py', 'scripts/study_memory/__init__.py', 'scripts/study_memory/io.py',
    'scripts/study_memory/profile.py', 'scripts/study_memory/model.py', 'scripts/study_memory/batches.py',
    'scripts/study_memory/updates.py', 'scripts/study_memory/store.py', 'scripts/study_memory/review.py',
    'scripts/study_memory/session.py', 'scripts/study_memory/export.py',
)
EDITIONS = ('study-companion', 'study-companion-zh')
# source path in the repository -> path inside the archive. Each archive is one installable skill folder.
PUBLIC_FILES = {edition: {'LICENSE': f'{edition}/LICENSE',
                          **{f'skills/{edition}/{f}': f'{edition}/{f}' for f in SKILL_FILES}}
                for edition in EDITIONS}


def build_release(repo_dir: Path, out_dir: Path) -> list[Path]:
    root = Path(repo_dir).resolve()
    for files in PUBLIC_FILES.values():
        for name in files:
            source = root / name
            if not source.is_file() or not source.resolve().is_relative_to(root):
                raise ValueError(f'Missing or external public resource: {name}')
    if not (root / 'VERSION').is_file():
        raise ValueError('Missing VERSION file.')
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = []
    for edition, files in PUBLIC_FILES.items():
        target = out_dir / f'{edition}-v{version}.zip'
        temporary = target.with_suffix('.zip.tmp')
        try:
            with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, member in files.items():
                    archive.write(root / name, member)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        targets.append(target)
    return targets


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, default=Path('dist'))
    args = cli.parse_args()
    for path in build_release(Path(__file__).resolve().parents[1], args.out):
        print(path)
