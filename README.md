# Study Companion

[中文说明](README.zh.md)

A study skill for AI assistants. It teaches a course from your own materials, asks you again about what you got wrong, and keeps records that tell apart what you asked, what was explained, and what you showed you can do.

It comes in two editions with the same rules: `study-companion` (English) and `study-companion-zh` (Chinese). Install one.

## Pick the setup that matches your assistant

What you get depends on what your assistant can do, not on who makes it.

| Your assistant can | Mode | Setup |
|---|---|---|
| run commands and load skill folders (Claude Code, Codex CLI, and other agents that read `SKILL.md`) | Full | Copy `skills/study-companion` or `skills/study-companion-zh` into the agent's skills folder, for example `~/.claude/skills/`, `~/.codex/skills/`, or `~/.agents/skills/`. |
| accept an uploaded skill (apps with a skills setting) | Full, if it can also run code | Upload the zip from `python scripts/build_release.py`. |
| keep project instructions and read uploaded files (project features in chat apps) | Project | Paste the [starter prompt](templates/starter-prompt.en.md) into the project instructions and upload your `handoff.md`. |
| only chat (DeepSeek's web chat, or any other plain chat) | Chat | Paste the [starter prompt](templates/starter-prompt.en.md) as the first message, then paste your `handoff.md`. |

In Full mode a local tool counts exchanges, chooses the daily review questions, and schedules the next review. In Project and Chat modes the assistant does this by following instructions, and you save two pieces of text it gives you at the end of each session. You can move between assistants: `handoff.md` is the same file in every mode.

Only Full mode is covered by the automated tests. How closely a given assistant follows the starter prompt has not been verified; try it and check the handoff it produces.

## First use

Tell the assistant your major and whether you are an undergraduate, masters, or doctoral student, then name the course:

> Use the study companion. My major is ____ and I am a ____ student. I want to study ____. Check which course materials you can read, then start studying and recording.

Things you can say later:

- "Start studying and record aerodynamics."
- "Update my study record."
- "Add what I just got wrong to my review questions."
- "Skip today's review."
- "Exam mode: give me a mock paper on chapters 3 to 5."
- "Pause recording." / "That's all for today, save the rest."

## How it studies with you

- Each day's first session for a course opens with one or two review questions that are due. A correct answer pushes the next review out to 1, 3, 7, 14, then 30 days; a wrong or hinted answer brings it back the next day.
- Explanations go in a fixed order: inputs, outputs, and purpose; assumptions; derivation; one example; one check question.
- Being told something is recorded as "explained". Only your own answer, quoted, is recorded as mastery.
- Records are filed under the day you studied, not the day they were saved.

The full rules are in the skill: [teaching](skills/study-companion/references/teaching.md), [records](skills/study-companion/references/records.md), [review](skills/study-companion/references/review.md).

## Local records (Full mode)

Python 3.11 or later; on Windows run `python -m pip install -r requirements.txt` for timezone data. The assistant runs the commands for you. They are documented in [commands](skills/study-companion/references/cli.md), and `python skills/study-companion/scripts/study_store.py --help` lists them.

Keep your profile, materials, database, and exports in a folder such as `personal/`, which this repository ignores. Never commit them to a public repository. Back up the database: the Markdown exports can be rebuilt from it, but not the other way round.

To bring a session from Project or Chat mode into the local records, save the session digest the assistant gave you and run `import-session`.

### Upgrading from 0.1

- The database is upgraded in place the first time any command opens it.
- `recurring-questions.md` and `review-history.md` are now generated from the database. Hand-written copies are renamed to `*.manual-backup.md` on the first export once a question exists. Re-enter your existing questions with `question add`.
- `batch_size` in the config is ignored. Exports use the config's `timezone` and `language`.
- Project instructions are replaced by the starter prompt.

## Repository layout

```text
skills/study-companion/       English skill: SKILL.md, references/, scripts/
skills/study-companion-zh/    Chinese skill, same structure; scripts are a copy
templates/                    starter prompts, config example, course templates
scripts/sync.py               regenerates the Chinese scripts copy and the starter prompts
scripts/build_release.py      builds one zip per edition
tests/                        unit tests on synthetic data
```

## Development

```sh
python -m unittest discover -s tests -v
python scripts/sync.py            # after editing scripts, core rules, or portable.md
python scripts/build_release.py --out dist
```

Edit scripts only under `skills/study-companion/scripts`. When you change a rule, change it in both editions; a test checks that the two have the same structure. Design notes are in [generated-docs](generated-docs/README.md).

## License

[MIT](LICENSE)
