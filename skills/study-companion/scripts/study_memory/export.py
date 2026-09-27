"""Rebuild readable Markdown from an immutable database snapshot."""
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .io import atomic_text
from .model import parse_time, safe_course_id, turn_key
from .store import read_course

MASTERY_LABEL = {'unverified':'待验证','needs_help':'需要帮助','can_explain':'可独立解释','can_apply':'可独立应用'}


def event_lines(event: dict) -> list[str]:
    lines = [f"### {', '.join(event['concept_ids'])}", '', f"- 疑问：{event['question']}",
             f"- 讲解状态：{event['explanation_status']}", f"- 掌握状态：{MASTERY_LABEL[event['mastery']]}",
             f"- 关联概念：{', '.join(event['links']) or '未新增'}", f"- 事件：{event['event_id']}"]
    if event['correction_of']:
        lines.append(f"- 更正此前事件：{event['correction_of']}")
    for evidence in event['mastery_evidence']:
        lines.append(f"- 作答证据（{' / '.join(evidence['source_turn_id'])}）：{evidence['quote']}")
    if not event['mastery_evidence']:
        lines.append('- 作答证据：尚无；讲解不等于掌握。')
    return lines


def export_course(db_path: Path, course_id: str, output_dir: Path, timezone: str) -> list[Path]:
    safe_course_id(course_id)
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as error:
        raise ValueError('Unknown timezone. On Windows install tzdata if IANA data is missing.') from error
    output_dir = Path(output_dir).resolve()
    base = (output_dir / course_id).resolve()
    if not base.is_relative_to(output_dir):
        raise ValueError('Course directory escapes output directory.')
    state = read_course(db_path, course_id)
    turns = {turn_key(t): t for t in state['turns']}
    days, latest = defaultdict(list), {}
    next_start, newest = '尚无学习记录。', ''
    for batch in state['updates']:
        update = batch['update']
        batch_latest = ''
        for event in update['events']:
            refs = [turns[tuple(r)] for r in event['source_turn_ids']]
            event_time = max(t['occurred_at'] for t in refs)
            batch_latest = max(batch_latest, event_time)
            for concept in event['concept_ids']:
                old = latest.get(concept)
                if old is None or event_time >= old[0]:
                    latest[concept] = (event_time, event)
            by_day = defaultdict(list)
            for t in refs:
                by_day[parse_time(t['occurred_at']).astimezone(zone).date().isoformat()].append(t)
            for day, day_turns in by_day.items():
                lines = event_lines(event) + ['', f"处理时间：{batch['created_at']}；课程版本：{batch['version']}", '']
                for t in sorted(day_turns, key=lambda t: (t['occurred_at'],t['turn_id'])):
                    lines.append(f"- 来源：{t['thread_id']} / {t['turn_id']}；学习时间：{parse_time(t['occurred_at']).astimezone(zone).isoformat()}")
                lines.extend(['', f"本批下次起点：{update['next_start']}", ''])
                days[day].append((min(t['occurred_at'] for t in day_turns), event['event_id'], lines))
        if batch_latest >= newest:
            newest, next_start = batch_latest, update['next_start']
    header = [f'# {course_id} 学习状态', '', f"课程版本：{state['version']}；时区：{timezone}",
              f"最近学习时间（UTC）：{newest or '无'}", '', '## 下次起点', '', next_start, '', '## 当前概念状态', '']
    seen = set()
    for _, event in sorted(latest.values(), key=lambda item: (item[0], item[1]['event_id'])):
        if event['event_id'] in seen:
            continue
        seen.add(event['event_id'])
        header.extend(event_lines(event) + ['', '- 来源轮次：' + '; '.join(' / '.join(r) for r in event['source_turn_ids']), ''])
    paths = []
    for day, sections in sorted(days.items()):
        path = base / 'logs' / f'{day}.md'
        if not path.resolve().is_relative_to(output_dir):
            raise ValueError('Log path escapes output directory.')
        lines = [f'# {course_id} · {day}', '', f"课程版本：{state['version']}；日期按 {timezone} 原始消息时间划分。", '']
        for _, _, section in sorted(sections):
            lines.extend(section)
        atomic_text(path, '\n'.join(lines) + '\n')
        paths.append(path)
    path = base / 'current-state.md'
    if not path.resolve().is_relative_to(output_dir):
        raise ValueError('State path escapes output directory.')
    # Publish current-state last. If any daily file fails, retry the whole export.
    atomic_text(path, '\n'.join(header) + '\n')
    paths.append(path)
    return paths
