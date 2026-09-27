"""UTF-8 file operations; replacement never truncates an existing record."""
import json
import os
import tempfile
from pathlib import Path


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
