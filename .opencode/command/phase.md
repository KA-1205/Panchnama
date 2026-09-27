---
description: Implement one BUILD_ORDER phase end to end, then update Current State
agent: phase-implementer
---

Implement **Phase $ARGUMENTS** of this project.

1. Use the `spec-reader` subagent to pull the Phase $ARGUMENTS section of
   `BUILD_ORDER.md` and whichever spec files it references. Do not read spec
   files into your own context wholesale.
2. Confirm all dependency phases have passed their gates. Check the Current
   State table at the top of `BUILD_ORDER.md` and honour any carry-over
   decisions recorded there.
3. Implement only the tasks in that phase's table. Note, do not do, work that
   belongs to a later phase.
4. Run the phase's full gate. A partial pass is a failure.
5. Update the Current State table in `BUILD_ORDER.md` to reflect the real
   outcome, and set Last updated to today.
6. Report the result. Do **not** commit — committing is handled separately by
   `/commit`, which gates on both `/gate` and `/audit` passing.

Stop and report rather than working around any `AGENTS.md` §8 stop condition.
