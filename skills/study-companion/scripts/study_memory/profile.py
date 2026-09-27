"""Explicit first-use profile. A degree is a preference, not mastery evidence."""
from pathlib import Path
from .io import read_json, write_json

DEGREES = {'undergraduate', 'postgraduate', 'masters', 'doctoral'}


def missing_profile_fields(config: dict) -> list[str]:
    profile = config.get('profile', {})
    if not isinstance(profile, dict):
        return ['major', 'degree_level']
    missing = []
    if not isinstance(profile.get('major'), str) or not profile['major'].strip():
        missing.append('major')
    if profile.get('degree_level') not in DEGREES:
        missing.append('degree_level')
    return missing


def save_profile(path: Path, major: str, degree_level: str) -> dict:
    profile = {'major': major, 'degree_level': degree_level}
    if missing_profile_fields({'profile': profile}):
        raise ValueError('请填写专业，以及本科或研究生阶段。')
    profile['major'] = major.strip()
    path = Path(path)
    config = read_json(path) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('配置必须是 JSON 对象。')
    config.setdefault('schema_version', 1)
    config.setdefault('timezone', 'Asia/Shanghai')
    config.setdefault('batch_size', 4)
    config.setdefault('courses', [])
    config['profile'] = profile
    write_json(path, config)
    return config
