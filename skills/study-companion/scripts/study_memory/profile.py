"""Explicit first-use profile. A degree is a preference, not mastery evidence."""
from pathlib import Path
from .io import read_json, write_json

DEGREES = {'undergraduate', 'postgraduate', 'masters', 'doctoral'}
LANGUAGES = ('en', 'zh')
DEFAULT_TIMEZONE = 'Asia/Shanghai'


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


def language_of(config: dict) -> str:
    """Configs written before 0.2 have no language and were Chinese."""
    return config.get('language') if config.get('language') in LANGUAGES else 'zh'


def save_profile(path: Path, major: str, degree_level: str, language: str | None = None,
                 timezone: str | None = None) -> dict:
    profile = {'major': major, 'degree_level': degree_level}
    if missing_profile_fields({'profile': profile}):
        raise ValueError('Give a major and a study level: undergraduate, masters, doctoral or postgraduate.')
    if language is not None and language not in LANGUAGES:
        raise ValueError('language must be en or zh.')
    profile['major'] = major.strip()
    path = Path(path)
    existed = path.exists()
    config = read_json(path) if existed else {}
    if not isinstance(config, dict):
        raise ValueError('The config file must hold a JSON object.')
    config.setdefault('schema_version', 1)
    config.setdefault('timezone', DEFAULT_TIMEZONE)
    config.setdefault('language', 'zh' if existed else 'en')
    config.setdefault('courses', [])
    config.pop('batch_size', None)  # fixed at four turns; no longer configurable
    if language:
        config['language'] = language
    if timezone:
        config['timezone'] = timezone
    config['profile'] = profile
    write_json(path, config)
    return config
