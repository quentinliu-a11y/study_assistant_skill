# Commands (Full mode)

Python 3.11 or later. On Windows, `pip install tzdata` if timezone names are not found. Paths below are relative to this skill's folder. The tool makes no network or model calls and does not read browser data.

Every command prints JSON and exits 0 on success. On failure it prints `Not saved: ...` and exits 2, and nothing is written.

## Profile

```sh
python scripts/study_store.py profile --config personal/config.json --major "Aerospace Engineering" --degree masters --lang en --timezone Asia/Singapore
```

Without `--major` or `--degree` it asks. Running it again changes the profile and keeps courses and history.

## Daily review

```sh
python scripts/study_store.py review pick --db personal/study.sqlite3 --config personal/config.json --course aerodynamics
python scripts/study_store.py review mark --db personal/study.sqlite3 --config personal/config.json --course aerodynamics --id separation --outcome correct --note "the learner's own words"
python scripts/study_store.py review skip --db personal/study.sqlite3 --config personal/config.json --course aerodynamics
python scripts/study_store.py question add --db personal/study.sqlite3 --course aerodynamics --id separation --confusion "why an adverse pressure gradient separates the flow" --prompt "What happens to near-wall fluid in an adverse pressure gradient?" --concept boundary-layer-separation --date 2026-11-12 --source thread-id
python scripts/study_store.py question list --db personal/study.sqlite3 --course aerodynamics
```

- `review pick` returns `already_started: true` with today's questions if a round exists, otherwise it chooses up to `--limit` (default 2) due questions and records them as asked. `--again` adds an extra round on request.
- `review mark` takes `--outcome correct|hinted|incorrect|skipped`. `correct` requires `--note`.
- `question add` on an existing id only needs `--date` and `--source` to record another occurrence.
- "Today" is the current date in `--timezone`, else the config's timezone, else Asia/Shanghai. `--date YYYY-MM-DD` overrides it.

## Saving study exchanges

```sh
python scripts/study_store.py import --config personal/config.json --db personal/study.sqlite3 --input personal/turns.json
python scripts/study_store.py pending --db personal/study.sqlite3
python scripts/study_store.py commit --config personal/config.json --db personal/study.sqlite3 --input personal/update.json --expected-version 0
python scripts/study_store.py export --db personal/study.sqlite3 --config personal/config.json --course aerodynamics --out personal/exports
```

`import` takes a JSON list of complete exchanges. Use it only when you have real message ids and times:

```json
{
  "schema_version": 1,
  "course_id": "aerodynamics",
  "session_id": "confirmed-session-1",
  "thread_id": "source-thread-id",
  "turn_id": "source-turn-id",
  "occurred_at": "2026-09-27T10:00:00+08:00",
  "user_text": "Why does near-wall fluid separate in an adverse pressure gradient?",
  "assistant_text": "The full answer, not a summary.",
  "complete": true,
  "learning_confirmed": true,
  "is_learning": true
}
```

`occurred_at` is when the question was asked, with a timezone. Do not invent ids or times; if you lack them, use `import-session` below. A completed exchange cannot be rewritten; an incomplete one can be completed once.

`pending` returns batches of four and each course's version. `pending --flush` also returns a shorter final batch.

`commit` takes the summary of one batch:

```json
{
  "batch_ids": [["source-thread-id", "source-turn-id"]],
  "update": {
    "course_id": "aerodynamics",
    "session_id": "confirmed-session-1",
    "events": [{
      "source_turn_ids": [["source-thread-id", "source-turn-id"]],
      "concept_ids": ["boundary-layer-separation"],
      "question": "Unclear how an adverse pressure gradient slows near-wall fluid",
      "explanation_status": "explained",
      "mastery": "unverified",
      "mastery_evidence": [],
      "links": ["adverse-pressure-gradient"],
      "correction_of": null
    }],
    "next_start": "Ask the learner to tell the no-slip condition from the separation criterion"
  }
}
```

- A batch has one to four exchanges and must be the earliest unsaved ones of that conversation. Events must cover every exchange in the batch.
- `mastery_evidence` items are `{"source_turn_id": [thread_id, turn_id], "quote": "..."}`. The quote must appear in that learner message.
- `correction_of` takes a full `event_id` from `state --db ... --course ...`.
- `--expected-version` is the course version from `pending` or `state`. On a version conflict, read the state again and merge; do not just change the number.
- Committing the same batch with the same summary again is harmless. A different summary for a saved batch is refused; add a correction instead.

## Importing a session digest

```sh
python scripts/study_store.py import-session --config personal/config.json --db personal/study.sqlite3 --input personal/digest.json
```

Takes the digest that an assistant without tools writes at the end of a session ([format](portable.md)). Its items are stored as exchanges marked "session digest" because they cannot be checked against original messages, and exports say so. Importing the same digest twice changes nothing. A digest that fails any check writes nothing.

## Export

`export` writes into `<out>/<course>/`:

| File | Content |
|---|---|
| `handoff.md` | next start, concepts not yet mastered, review questions with due dates. Give this to any assistant. |
| `current-state.md` | the latest event for every concept |
| `logs/YYYY-MM-DD.md` | history by the day it was studied |
| `recurring-questions.md`, `review-history.md` | written once at least one review question exists |

All of them are rebuilt from the database, so keep notes of your own in other files. A hand-written `recurring-questions.md` or `review-history.md` from an earlier version is renamed to `*.manual-backup.md` the first time, not overwritten. Markdown shows event ids shortened to eight characters. `--lang` and `--timezone` override the config.

Back up the database: Markdown alone cannot restore the original exchanges. After a successful commit, a failed export only needs `export` again.
