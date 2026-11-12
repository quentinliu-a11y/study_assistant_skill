# Courses and personal data

## Config file

The learner's config is a JSON file kept outside this skill, for example `personal/config.json`:

```json
{
  "schema_version": 1,
  "profile": {"major": "Aerospace Engineering", "degree_level": "masters"},
  "language": "en",
  "timezone": "Asia/Singapore",
  "courses": [
    {"course_id": "aerodynamics", "resource_dir": "courses/aerodynamics", "state_dir": "courses/aerodynamics"}
  ]
}
```

- `degree_level` is `undergraduate`, `masters`, `doctoral`, or `postgraduate`.
- `language` (`en` or `zh`) sets the language of prompts and exported Markdown. `timezone` is an IANA name and decides what "today" is.
- `course_id` is lowercase letters, digits, and hyphens, starting with a letter, at most 64 characters.
- Paths are relative to the config file. `resource_dir` holds `overview.md`, `knowledge-map.md`, and optionally a course rules file. `state_dir` receives the exported records; if it is absent, look in `exports/<course_id>/` and report when there is no state yet.

## Choosing the course

Use the course the learner names, or the one this workspace is clearly set up for. A technical term in a message does not mean the learner is studying that course. For a new course with thin materials, list what is missing first.

When a session starts, read the course's `overview.md` and `knowledge-map.md`, then `handoff.md` (or `current-state.md` and the newest dated log). Read only the sources the current question needs.

## Course-specific rules

Rules for one course, such as its notation, its usual traps, or how its lecturer defines a quantity, go in a rules file inside that course's `resource_dir`. Read it when the course starts. It adds to this skill and cannot override the core rules.

## Privacy

Profiles, course materials, questions, logs, and the database are personal. Keep them in a folder outside this skill and outside any public repository. A folder inside a public GitHub repository cannot be made private on its own, so check that the target repository is private before syncing records to it.
