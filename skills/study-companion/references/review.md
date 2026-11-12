# Recurring questions and daily review

## What becomes a review question

Record a question when the learner says they do not understand something, explains it wrongly, or still fails a check after an explanation. Asking about a topic once is not a misunderstanding; that stays `unverified` in the ordinary record.

Each question has a stable id, the specific confusion, a short prompt to ask later, the concepts involved, and a list of occurrences. An occurrence is a date plus a source (a conversation or log reference). The same source on the same day counts once, however many files repeat it. A question is **recurring** when two different sources show the same confusion. A related but different sub-question gets its own id.

## The daily review

1. Run it once per course per day, at the first study session of the learner's local day. If today's review was already started or skipped, continue from there and do not start another round. The learner can ask for extra practice.
2. Choose one or two questions that are due. Order: recurring and `needs_help`, then `needs_help`, then `unverified`, then the rest; among equals, the one reviewed longest ago. If none is due, go straight to new material.
3. Ask only the short prompt and any conditions it needs. Do not give the answer in the same message.
4. Classify the learner's actual answer:
   - `correct`: answered unaided. Keep their words as evidence.
   - `hinted`: got there after a hint.
   - `incorrect`: still needs help.
   - `skipped`: no answer. Nothing changes.
5. Give feedback on what was right and what was missing, then return to where the study left off.

## Schedule

After each `correct` in a row the next review comes 1, 3, 7, 14, then 30 days later. `hinted` or `incorrect` sets the status to `needs_help` and brings the question back the next day, with the count of correct answers reset. A `correct` raises the status to `can_explain`.

## By mode

- **Full mode.** `review pick` chooses and records today's questions, `review mark` records each answer and schedules the next date, `review skip` records a skipped day, and `question add` adds a question or one more occurrence. See [Commands](cli.md). The command output decides what is due; do not choose by hand.
- **Project and Chat modes.** The questions, their due dates, and the last review day are in `handoff.md`. Apply the same order and schedule yourself and write the new dates into the updated handoff. See [Portable records](portable.md). Without a handoff file, say that you cannot tell whether today's review was done.

The trigger is the learner starting to study. This is not a reminder service and nothing runs in the background.
