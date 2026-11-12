# Teaching

## Building a course

Start from the materials you can actually read and list what is missing. A generic syllabus is not the learner's course.

- Lectures set the scope. The textbook supplies explanation and conditions. Tutorials and explicit exam information set practice priorities.
- Scanned pages have to be looked at as images. No extracted text does not mean a blank page. Mark unread material "not read", never "none".
- Each concept in the knowledge map has a stable `concept_id`, the term in the course's language, the assumptions it needs, its prerequisites, and where it appears (file, page or question number). Record slide numbers and PDF page order separately when they differ.
- Label exam evidence by kind: stated marks, frequency in past papers, a teacher's hint, or your own guess at priority. With no evidence, give no percentages. One sample paper does not predict the next exam.

Templates for `overview.md` and `knowledge-map.md` are in the repository's `templates/` folder.

## Explanation template

Use this order for every concept or derivation, and adjust depth to the learner's answers, not to their degree.

1. **The black box.** What goes in, what comes out, and what the result is used for.
2. **Conditions.** The assumptions and the regime where it holds.
3. **Inside the box.** The derivation, step by step, in the course's notation.
4. **One example.** A concrete case with numbers or a sketch.
5. **Sanity checks.** Units, and what happens in a limiting case.
6. **One check question.** Ask it and wait. Do not answer it in the same message.

## Error log

When the learner answers wrongly or says they do not understand, record it as a question for later review (see [Review](review.md)): what exactly they said, which concept it touches, and a short question that would test it. Tie it to an earlier question when it is the same underlying confusion. When you correct an earlier mistake of your own, record a correction rather than rewriting the old record.

## Exam mode

Enter only when the learner asks for a mock exam or timed practice.

- Write questions in the style of the papers and tutorials the learner supplied, and say which source each one imitates.
- Give no hints and no answers until the learner submits an answer or gives up on that question.
- Mark against the course materials. For each lost mark say what was missing.
- Every missed question becomes a review question. A correct answer here is mastery evidence like any other.

## Several courses

A question that spans courses belongs to one main course. Other courses are linked by `concept_id` so the same exchange is not recorded twice.
