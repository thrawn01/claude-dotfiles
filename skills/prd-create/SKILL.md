---
name: prd-create
description: Run a back-and-forth product-discovery discussion and write a PRD (Product Requirements Document) to docs/features/{feature}/prd.md. Use when the user asks to "write a PRD", "create a PRD", "scope a feature", "write requirements for X", or otherwise signals they want to think through what a feature needs to do before any technical design work. Also use when revising an existing PRD based on new information or tech-spec findings. Do NOT use for technical/implementation design (that's spec-create), for bug fixes or tweaks too small to warrant a PRD, or when the user is brainstorming ideas without committing to a document.
---

# Create a Product Requirements Document

Have a back-and-forth discussion that elicits the product requirements for a feature or MVP, track decisions made along the way, and write the result to `docs/features/{feature}/prd.md` at the end.

## Environment

This skill runs in both Claude Code and Claude chat. Behavior differs in three places:

| | Claude Code | Claude chat |
|---|---|---|
| **Writing the PRD** | Write directly to `docs/features/{feature}/prd.md` | Produce as a markdown artifact; tell the user the intended path to place it |
| **Revising an existing PRD** | Read the file from disk | Ask the user to paste the current PRD into the conversation |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface ADR-worthy decisions clearly; tell the user to take them into Claude Code and run `adr-write` for each |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat. Everything else — the discussion, question list, suggested answers, and running log — is identical in both environments.

## Discussion process

Look for `CONTEXT.md` files in `docs/` directories relevant to the feature being discussed (see [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) for location rules). Read any that exist once and hold them in memory for the session — do not re-read. These are the project's domain glossaries; use them throughout to catch terminology conflicts.

Before generating the question list, list every file in `docs/adr/` and read each title (the top-level heading). For any title that sounds like it could cap product scope — e.g., mentions users, tenancy, regions, languages, roles, pricing, deployment targets — read the full ADR. Skip titles that are clearly purely technical (storage engines, serialization formats, library choices). The goal is to catch architectural guardrails that limit what the product can ask for — things like "no multi-tenancy," "English-only MVP." Frame questions so they don't invite answers the architecture has already ruled out; if the user seems to want something an ADR forbids, surface the ADR explicitly rather than silently narrowing the question.

At the start of the discussion, generate the full list of questions needed to produce a good PRD for this feature, present it to the user, then immediately start on the first question. Do not pause to ask whether to reorder, skip, or add questions — the user can redirect at any point as items come up, but the default is forward motion. Showing the list gives shape; asking permission to proceed just adds friction.

Then work through the questions one at a time. For each question:

- Offer a suggested answer or direction alongside it. The user reacts and refines rather than generating from scratch. "Who are the target users? My read from what you've described is primarily internal ops staff — is that right?" moves faster than an open question.
- When the question has multiple defensible answers with meaningfully different product implications, first score it against the high-impact trigger criteria in the `deliberate` skill. If 2+ signals fire, pause and ask the user whether to deliberate before recommending. If the user agrees, run the deliberation protocol — the synthesis replaces the standard options block below. If the user declines (or fewer than 2 signals fired), present the options using the `AskUserQuestion` tool with one option flagged as recommended (append "(Recommended)" to its label). Place the recommended option first. Use the `description` field on each option to explain trade-offs or implications. A bare list of options without a pick is never acceptable — the user came to you for a recommendation, so always include your reasoning in the question text.

    In Claude chat (where `AskUserQuestion` is not available), fall back to a numbered options block in text:

    ```
    **Option 1** (recommended) — ...
    **Option 2** — ...
    **Option 3** — ...

    I recommend Option 1 because <reason>. Pick one or propose another.
    ```

    The user can also say "deliberate on this" at any point during the discussion to trigger the deliberation protocol for the current question, bypassing trigger scoring.
- Resolve the question before moving to the next one. Stay on it until it is answered or the user explicitly defers it.
- When the user uses a vague or overloaded term, interrupt mid-question before continuing. Propose a precise alternative: "You said 'user' — do you mean the account owner or anyone with access?" Resolve the term before moving on.
- When a scope boundary or non-goal is stated, always follow up with one concrete scenario that tests it: "So if a customer cancels mid-billing-cycle, that's out of scope?" One scenario per boundary, framed as confirmation not challenge.

Keep a visible running list of decisions as they land. Show it on request, and whenever you finish a domain (problem → users → scope, etc.) before moving to the next. The user should be able to correct the log in real time.

Track resolved domain terms during the discussion. When writing the PRD at the end, also write all new or updated terms to the appropriate `docs/CONTEXT.md` in a single pass. If it does not exist, create it in the `docs/` directory closest to the code whose domain it describes. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

When the question list is exhausted, or the user calls it done, move to writing.

## What a PRD covers

Use these domains as the source when generating the initial question list. Not every feature needs every domain — tailor the list to what the feature actually requires. Do not pad the list with questions whose answers are already obvious from the user's input.

- **Problem and why.** What user or business problem does this solve? Why now?
- **Target users or personas.** Who is this for? If multiple, which is primary?
- **Mental model.** For platform, framework, or tooling products: how should users think about the system? What are the core concepts and their relationships? Often more clarifying than user stories for this type of product.
- **Core design principles.** The non-negotiable constraints that shape all decisions — what the product will always do, and what it will deliberately never do. Surface these early; they resolve many later questions.
- **User stories or use cases.** What does the user want to do? "As a X, I want Y, so that Z" works, but any clear narrative does.
- **Success metrics.** Measures of whether the *PRD was right* — outcomes observable after shipping, such as adoption, latency reduction, incidents avoided, task-completion-time reduction. Never a restatement of the scope list: "the capabilities were built" is execution, not a metric. If no plausible post-ship outcome exists to measure, omit the section rather than filling it. Many framework, tooling, and infrastructure MVPs have nothing to put here, and that is correct.
- **Scope.** What is in the first version?
- **Non-goals.** What this feature is deliberately not trying to do. Often more clarifying than scope.
- **Dependencies and constraints.** External systems, timelines, regulatory or compliance requirements, known technical limits.
- **Open questions.** Things that still need *product-level* resolution before tech-spec can begin: scope boundaries, user scenarios in/out, outcome thresholds, unresolved dependencies. Do not include questions whose answers would live in an interface signature, a config key, an exit code, or a middleware shape — those are tech-spec open questions and belong there.

## Feature naming

Infer the `{feature}` slug from the discussion — short, kebab-case, specific. Before writing the file, confirm in one line: "I'll write this to `docs/features/payment-retry/prd.md` — sound right?" Do not ask for the slug at the start; it will be much clearer at the end.

## Writing the document

Write a single markdown file at `docs/features/{feature}/prd.md`. Structure it around the domains actually covered in the discussion.

A reasonable skeleton:

```markdown
# <Feature Name> PRD

## Problem

## Users

## User Stories

## Success Metrics

## Scope

### In Scope

### Out of Scope / Non-Goals

## Dependencies and Constraints

## Open Questions
```

Use prose where prose is clearer; use lists for stories, metrics, and scope bullets. Do not over-format.

Write for a reader who was not in the discussion — a team member, stakeholder, or the engineer writing the tech-spec later. Do not reference ideas that were considered and dropped mid-conversation. Do not use deictic references ("the option we discussed", "what Alice suggested"). Name the actual thing.

## Linking

The PRD can link to:

- **ADRs in `docs/adr/`** — reference by number if the discussion touched an already-recorded architecture decision.
- **The sibling tech-spec at `docs/features/{feature}/tech-spec.md`** — once it exists.
- **Source files or directories in the repository** where directly relevant.
- **External URLs** for standards, RFCs, or other durable public references.

Do not link to other features' PRDs or tech-specs, chat transcripts, Slack threads, or meeting notes.

## At the end of the discussion

1. Confirm the file was written with its path.
2. Review the running decision log. For each decision — product or technical — apply this checklist. Only offer an ADR if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the PRD. Core design principles surfaced during the discussion are strong ADR candidates — they are often the most significant decisions made and the easiest to lose. Decisions resolved through the `deliberate` skill automatically satisfy "Hard to reverse" and "Result of a real trade-off" — only check "Surprising without context." These should already have been offered as ADR candidates immediately after deliberation resolved; do not re-offer them here.
3. For each decision that passes the checklist, offer to capture it as an ADR: "This looks ADR-worthy — want me to record it?" Invoke `adr-write` for the ones the user approves.
4. Do not commit. The user handles commits.

## Revising an existing PRD

Read the current `docs/features/{feature}/prd.md`. Run a focused discussion on what is changing — do not re-elicit the unchanged parts. Write the updated PRD. The running-log and end-of-discussion ADR offer still apply.
