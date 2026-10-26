"""Package only known public files, never an entire user's workspace."""
import argparse
from pathlib import Path
import zipfile

PUBLIC_FILES = (
    'README.md', 'START_HERE.md', 'requirements.txt',
    'templates/config.example.json', 'templates/project-instructions.md',
    'templates/course/overview.md', 'templates/course/knowledge-map.md',
    'templates/course/recurring-questions.md', 'templates/course/review-history.md',
    'skills/study-companion/SKILL.md', 'skills/study-companion/agents/openai.yaml',
    'skills/study-companion/references/courses.md',
    'skills/study-companion/references/ifm.md',
    'skills/study-companion/references/learning-protocol.md',
    'skills/study-companion/references/recurring-review.md',
    'skills/study-companion/references/data-contract.md',
    'skills/study-companion/scripts/study_store.py',
    'skills/study-companion/scripts/study_memory/__init__.py',
    'skills/study-companion/scripts/study_memory/io.py',
    'skills/study-companion/scripts/study_memory/profile.py',
    'skills/study-companion/scripts/study_memory/model.py',
    'skills/study-companion/scripts/study_memory/batches.py',
    'skills/study-companion/scripts/study_memory/updates.py',
    'skills/study-companion/scripts/study_memory/store.py',
    'skills/study-companion/scripts/study_memory/export.py',
)


def build_release(repo_dir: Path, out_dir: Path) -> Path:
    root = Path(repo_dir).resolve()
    for name in PUBLIC_FILES:
        source = root / name
        if not source.is_file() or not source.resolve().is_relative_to(root):
            raise ValueError(f'Missing or external public resource: {name}')
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / 'study-companion-v0.1.0.zip'
    temporary = out_dir / 'study-companion-v0.1.0.zip.tmp'
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in PUBLIC_FILES:
                archive.write(root/name, name)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, default=Path('dist'))
    args = cli.parse_args()
    print(build_release(Path(__file__).resolve().parents[1], args.out))
