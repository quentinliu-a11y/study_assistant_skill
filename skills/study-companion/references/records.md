# Records

## Sessions

A session starts when the learner confirms recording for one course and ends when they say so. Switching course starts a new session. Messages sent while paused are not counted. Re-reading old chat does not make it an approved study session; import old history only for the range the learner names.

## What counts as an exchange

One exchange is a study question plus a complete answer. A follow-up, or the learner's answer to a check question plus your feedback, is also one exchange. Small talk, setup, tool calls, failed or cut-off answers, and review questions that were asked but not answered do not count.

Exchanges are counted per course, per session, and per conversation, in batches of four. "Update my study record" and ending the session save a shorter final batch. Several conversations can feed one course, but their counts do not mix.

## What a saved event holds

Each event records the exchanges it came from, the concept ids, the learner's specific question or gap, whether it was explained, the mastery state with evidence, related concepts, and optionally the earlier event it corrects. Every exchange in a batch belongs to at least one event. If nothing new was understood, say so: "reviewed, no new evidence of mastery".

- Explanation: `not_explained`, `explained`, `corrected`.
- Mastery: `unverified`, `needs_help`, `can_explain`, `can_apply`. The last two need a quote of at least eight characters from the learner's own answer, with the exchange it came from.

A correction points at the old event and replaces it in the current state. The old event stays in the dated log.

## Dates

File records under the date the exchange happened, in the learner's timezone, not the date you saved them. A batch that crosses midnight is split by day. If the original time is unknown, say so; do not use today's date for old study.

## Saving, by mode

- **Full mode.** Use the commands in [Commands](cli.md). Say "saved" only after the command succeeded and you read the result back. If a write fails, keep the pending content and say so.
- **Project and Chat modes.** Follow [Portable records](portable.md). State that nothing has been written outside the conversation until the learner saves the files.

In every mode, do not claim background syncing, changes to project files, or a push to GitHub that you did not perform.
