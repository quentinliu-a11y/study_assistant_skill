"""Entry point for local study records. Run with --help. No network or model calls."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys
from study_memory.export import export_course
from study_memory.io import read_json
from study_memory.profile import DEFAULT_TIMEZONE, LANGUAGES, language_of, missing_profile_fields, save_profile
from study_memory.review import (OUTCOMES, STATUSES, add_question, list_questions, mark_review, pick_review,
                                 review_history, skip_day)
from study_memory.session import import_session, zone_of
from study_memory.store import commit_update, import_turns, pending_batches, read_course

PROMPTS = {
    'en': ('Before you start, what is your major? ',
           'Study level: 1 undergraduate / 2 masters / 3 doctoral / 4 postgraduate (unspecified): '),
    'zh': ('使用前，请填写你的专业：', '学习阶段：1 本科 / 2 研究生（硕士） / 3 研究生（博士） / 4 研究生（不细分）：'),
}


def load_config(path) -> dict:
    """An optional config supplies timezone and language defaults."""
    if path is None or not Path(path).exists():
        return {}
    config = read_json(path)
    if not isinstance(config, dict):
        raise ValueError('The config file must hold a JSON object.')
    return config


def require_profile(path: Path) -> dict:
    config = load_config(path)
    if missing_profile_fields(config):
        raise ValueError('Run profile first: the major and study level are missing.')
    if config.get('schema_version') != 1:
        raise ValueError('This version needs schema_version 1 in the config.')
    return config


def timezone_of(args) -> str:
    return args.timezone or load_config(args.config).get('timezone') or DEFAULT_TIMEZONE


def day_of(args) -> str:
    """The learner's local date decides what 'today' means for daily review."""
    return args.date or datetime.now(zone_of(timezone_of(args))).date().isoformat()


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description='Study companion: profile, incremental study records, spaced daily review.')
    commands = cli.add_subparsers(dest='command', required=True)

    def add(parent, name, help, db=True, config=None, course=False, zone=False):
        item = parent.add_parser(name, help=help)
        if db:
            item.add_argument('--db', type=Path, required=True)
        if config is not None:
            item.add_argument('--config', type=Path, required=config)
        if course:
            item.add_argument('--course', required=True)
        if zone:
            item.add_argument('--timezone', help='IANA name; defaults to the config, then Asia/Shanghai')
        return item

    profile = add(commands, 'profile', 'create or change the study profile', db=False, config=True)
    profile.add_argument('--major')
    profile.add_argument('--degree', choices=['undergraduate', 'masters', 'doctoral', 'postgraduate'])
    profile.add_argument('--lang', choices=LANGUAGES, help='language of prompts and exported Markdown')
    profile.add_argument('--timezone')
    add(commands, 'import', 'import complete turns with real ids and times', config=True).add_argument('--input', type=Path, required=True)
    add(commands, 'import-session', 'import a session digest from a chat without tools', config=True, zone=True
        ).add_argument('--input', type=Path, required=True)
    add(commands, 'pending', 'list unprocessed batches').add_argument('--flush', action='store_true', help='include a short final batch')
    commit = add(commands, 'commit', 'save the summary of one batch', config=True)
    commit.add_argument('--input', type=Path, required=True)
    commit.add_argument('--expected-version', type=int, required=True)
    add(commands, 'state', 'print one course with full event ids', course=True)
    export = add(commands, 'export', 'write Markdown: state, handoff, logs, review files', config=False, course=True, zone=True)
    export.add_argument('--out', type=Path, required=True)
    export.add_argument('--lang', choices=LANGUAGES)

    question = commands.add_parser('question', help='recurring questions').add_subparsers(dest='action', required=True)
    new = add(question, 'add', 'add a question, or one more occurrence of it', course=True)
    new.add_argument('--id', required=True)
    new.add_argument('--confusion', help='what exactly is not understood')
    new.add_argument('--prompt', help='the short question to ask at review time')
    new.add_argument('--concept', action='append', default=[])
    new.add_argument('--status', choices=STATUSES)
    new.add_argument('--date', help='YYYY-MM-DD the confusion appeared')
    new.add_argument('--source', help='where it appeared: a thread id or log reference')
    new.add_argument('--note', default='')
    add(question, 'list', 'list questions with schedule', course=True)

    review = commands.add_parser('review', help='daily review').add_subparsers(dest='action', required=True)
    pick = add(review, 'pick', "choose and record today's questions", config=False, course=True, zone=True)
    pick.add_argument('--limit', type=int, default=2)
    pick.add_argument('--again', action='store_true', help='the learner asked for extra practice today')
    mark = add(review, 'mark', "record the learner's answer", config=False, course=True, zone=True)
    mark.add_argument('--id', required=True)
    mark.add_argument('--outcome', choices=OUTCOMES, required=True)
    mark.add_argument('--note', default='', help="the learner's own words; required for correct")
    skip = add(review, 'skip', "record that today's review was skipped", config=False, course=True, zone=True)
    for item in (pick, mark, skip):
        item.add_argument('--date', help='YYYY-MM-DD; defaults to today in the timezone')
    add(review, 'history', 'list recorded reviews', course=True)
    return cli


def run_profile(args) -> dict:
    config = load_config(args.config)
    old = config.get('profile') if isinstance(config.get('profile'), dict) else {}
    major = args.major if args.major is not None else old.get('major', '')
    degree = args.degree if args.degree is not None else old.get('degree_level', '')
    missing = missing_profile_fields({'profile': {'major': major, 'degree_level': degree}})
    ask_major, ask_degree = PROMPTS[args.lang or (language_of(config) if config else 'en')]
    if 'major' in missing:
        major = input(ask_major).strip()
    if 'degree_level' in missing:
        value = input(ask_degree).strip()
        degree = {'1': 'undergraduate', '2': 'masters', '3': 'doctoral', '4': 'postgraduate'}.get(value, value)
    if args.timezone:
        zone_of(args.timezone)
    return save_profile(args.config, major, degree, args.lang, args.timezone)


def run(args):
    command = args.command
    if command == 'profile':
        return run_profile(args)
    if command == 'import':
        require_profile(args.config)
        return {'inserted': import_turns(args.db, read_json(args.input))}
    if command == 'import-session':
        require_profile(args.config)
        return import_session(args.db, read_json(args.input), timezone_of(args))
    if command == 'pending':
        batches = pending_batches(args.db, args.flush)
        courses = sorted({t['course_id'] for batch in batches for t in batch})
        return {'batches': batches, 'course_versions': {c: read_course(args.db, c)['version'] for c in courses}}
    if command == 'commit':
        require_profile(args.config)
        payload = read_json(args.input)
        if not isinstance(payload, dict) or not {'batch_ids', 'update'} <= payload.keys():
            raise ValueError('Commit input needs batch_ids and update.')
        return {'version': commit_update(args.db, payload['batch_ids'], payload['update'], args.expected_version)}
    if command == 'state':
        return read_course(args.db, args.course)
    if command == 'export':
        language = args.lang or language_of(load_config(args.config))
        return {'files': [str(p) for p in export_course(args.db, args.course, args.out, timezone_of(args), language)]}
    if command == 'question':
        if args.action == 'list':
            return {'questions': list_questions(args.db, args.course)}
        return add_question(args.db, args.course, args.id, args.confusion, args.prompt, args.concept,
                            args.status, args.date, args.source, args.note)
    if args.action == 'history':
        return {'reviews': review_history(args.db, args.course)}
    if args.action == 'pick':
        return pick_review(args.db, args.course, day_of(args), args.limit, args.again)
    if args.action == 'skip':
        return skip_day(args.db, args.course, day_of(args))
    return mark_review(args.db, args.course, args.id, args.outcome, day_of(args), args.note)


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.DatabaseError, EOFError) as error:
        print(f'Not saved: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
