# Portable records (Project and Chat modes)

Use this when you cannot run commands. Two pieces of text carry the learner's progress between sessions and between assistants.

<!-- portable:start -->
## At the start

Ask for the learner's latest `handoff.md` if it is not already in the conversation or project files. It holds the next starting point, the concepts not yet mastered, the review questions with their due dates, and the last review day. If the last review day is today, do not start another review round. Without a handoff, say so and do not make up earlier questions.

## At the end of a session, and when asked to update the record

Tell the learner that nothing has been saved outside this conversation yet, then output these two blocks for them to save.

**1. The new `handoff.md`, complete, replacing the old one:**

```markdown
# <course_id> study handoff

## Next start

<one or two sentences: where to resume>

## Concepts not yet mastered

- <concept_id>: <the learner's specific gap> (unverified | needs help)

## Questions to review

Last review day: <YYYY-MM-DD or none>

- <question-id> | <unverified | needs help | can explain | can apply> | next review: <YYYY-MM-DD or any time> | <short review question>
```

Review dates: after each unaided correct answer in a row, the next review is 1, 3, 7, 14, then 30 days later. A hinted or wrong answer makes it "needs help", due the next day. A skipped question keeps its date.

**2. A session digest, as JSON, for later import into the learner's local records:**

```json
{
  "schema_version": 1,
  "kind": "session_digest",
  "course_id": "aerodynamics",
  "date": "2026-11-12",
  "source": "name of this assistant or app",
  "next_start": "where to resume",
  "items": [
    {
      "question": "the learner's specific question or gap",
      "learner_words": "their own answer, quoted; empty if they gave none",
      "explanation_status": "explained",
      "mastery": "unverified",
      "concept_ids": ["concept-id"],
      "links": []
    }
  ],
  "open_questions": [
    {"id": "question-id", "confusion": "what is not understood", "prompt": "short review question", "status": "needs_help"}
  ],
  "review_results": [
    {"id": "question-id", "outcome": "correct", "note": "the learner's own words"}
  ]
}
```

`explanation_status` is `not_explained`, `explained`, or `corrected`. `mastery` is `unverified`, `needs_help`, `can_explain`, or `can_apply`; the last two require `learner_words`. `outcome` is `correct`, `hinted`, `incorrect`, or `skipped`; `correct` requires `note`. `date` is the day the study happened. Ids are lowercase letters, digits, and hyphens.
<!-- portable:end -->

## What these modes cannot promise

Counting to four and remembering to save depend on the assistant following instructions through a long conversation. Only Full mode enforces them with a tool. If you lose count, save early.
