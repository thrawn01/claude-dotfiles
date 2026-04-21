---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

Interview the user relentlessly about every aspect of their plan or design until all branches of the decision tree are resolved.

If no plan, design, or idea is provided, ask the user to specify what they want to be grilled on before starting.

## Questioning approach

- Start with the highest-risk or most ambiguous decisions first — things that would be expensive to change later.
- Ask questions one at a time, resolving dependencies between decisions before moving on.
- For each question, state your recommended answer with a brief rationale, then ask if the user agrees or wants to go a different direction.
- If the user disagrees, probe why — they may have context you don't. Don't just accept their answer; push back if you see a real risk.
- If a question can be answered by exploring the codebase, explore the codebase instead of asking.

## Finishing

- After all branches are resolved, produce a numbered summary of every decision made with rationale, suitable for pasting into a design doc or plan.
- Confirm with the user that the summary is accurate before ending.
