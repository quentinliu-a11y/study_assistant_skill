"""Entry point for local learning records. Run with --help."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
from study_memory.export import export_course
from study_memory.io import read_json
from study_memory.profile import missing_profile_fields, save_profile
from study_memory.store import commit_update, import_turns, pending_batches, read_course


def require_profile(path: Path) -> dict:
    if not path.exists():
        raise ValueError('请先运行 profile，填写专业及本科/研究生阶段。')
    config = read_json(path)
    if not isinstance(config, dict) or missing_profile_fields(config):
        raise ValueError('profile 不完整：请补充专业及本科/研究生阶段。')
    if config.get('schema_version') != 1 or config.get('batch_size') != 4:
        raise ValueError('此版本需要 schema_version=1 与 batch_size=4。')
    return config


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description='学习伙伴：首次填写专业和学历，然后保存增量学习记录。无网络调用。')
    commands = cli.add_subparsers(dest='command', required=True)
    profile = commands.add_parser('profile', help='首次使用入口或修改个人学习资料')
    profile.add_argument('--config', type=Path, required=True)
    profile.add_argument('--major')
    profile.add_argument('--degree', choices=['undergraduate','masters','doctoral','postgraduate'])
    for command in ('import','pending','commit','export','state'):
        item = commands.add_parser(command)
        item.add_argument('--db', type=Path, required=True)
        if command in ('import','commit'):
            item.add_argument('--config', type=Path, required=True)
            item.add_argument('--input', type=Path, required=True)
        if command == 'pending':
            item.add_argument('--flush', action='store_true', help='包含不足四轮的批次')
        if command == 'commit':
            item.add_argument('--expected-version', type=int, required=True)
        if command in ('export','state'):
            item.add_argument('--course', required=True)
        if command == 'export':
            item.add_argument('--out', type=Path, required=True)
            item.add_argument('--timezone', default='Asia/Shanghai')
    return cli


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == 'profile':
            config = read_json(args.config) if args.config.exists() else {}
            if not isinstance(config, dict):
                raise ValueError('配置必须是 JSON 对象。')
            old = config.get('profile', {})
            if not isinstance(old, dict):
                old = {}
            major = args.major if args.major is not None else old.get('major', '')
            degree = args.degree if args.degree is not None else old.get('degree_level', '')
            missing = missing_profile_fields({'profile': {'major': major, 'degree_level': degree}})
            if 'major' in missing:
                major = input('使用前，请填写你的专业：').strip()
            if 'degree_level' in missing:
                value = input('学习阶段：1 本科 / 2 研究生（硕士） / 3 研究生（博士） / 4 研究生（不细分）：').strip()
                degree = {'1':'undergraduate','2':'masters','3':'doctoral','4':'postgraduate'}.get(value, value)
            result = save_profile(args.config, major, degree)
        elif args.command == 'import':
            require_profile(args.config)
            result = {'inserted': import_turns(args.db, read_json(args.input))}
        elif args.command == 'pending':
            batches = pending_batches(args.db, args.flush)
            courses = sorted({t['course_id'] for batch in batches for t in batch})
            result = {'batches': batches, 'course_versions': {c: read_course(args.db,c)['version'] for c in courses}}
        elif args.command == 'commit':
            require_profile(args.config)
            payload = read_json(args.input)
            if not isinstance(payload, dict) or not {'batch_ids','update'} <= payload.keys():
                raise ValueError('Commit input needs batch_ids and update.')
            result = {'version': commit_update(args.db, payload['batch_ids'], payload['update'], args.expected_version)}
        elif args.command == 'state':
            result = read_course(args.db, args.course)
        else:
            result = {'files': [str(p) for p in export_course(args.db,args.course,args.out,args.timezone)]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.DatabaseError, EOFError) as error:
        print(f'未完成：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
