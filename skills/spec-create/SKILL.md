---
name: spec-create
description: Run a back-and-forth technical design discussion informed by the PRD and write a tech spec to 
  docs/features/{feature}/tech-spec.md. Use when a PRD exists for a feature and the user is ready to work through technical
  implementation decisions — "write a tech spec", "design the implementation for X", "let's do the technical design
  for Y". Also use when revising an existing tech spec.
---

# Create a Technical Spec

Read the PRD for the feature, run a back-and-forth technical design discussion, and write the result to `docs/features/{feature}/tech-spec.md`. The spec translates the PRD's "what" into the implementation's "how" — component design, data model, API shape, and the decisions an engineer needs before writing code.

## Environment

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the PRD** | Read from `docs/features/{feature}/prd.md` | Ask the user to paste the PRD |
| **Writing the spec** | Write to `docs/features/{feature}/tech-spec.md` | Produce as markdown artifact; tell user the intended path |
| **Revising an existing spec** | Read from disk | Ask user to paste |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface decisions clearly; user takes them to Claude Code |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat.

## Starting the discussion

Read the PRD before generating any questions. Look for `CONTEXT.md` files in `docs/` directories relevant to the feature (see the CONTEXT-FORMAT.md in the prd-create skill for location rules). Read any that exist once and hold them in memory for the session. Use them to ensure the spec's terminology — component names, data model terms, API naming — is consistent with the domain glossary.

Then list every file in `docs/adr/` and read each title. Read the full ADR for any title that names a topic the feature touches — storage, API patterns, auth, error handling, deployment, and similar cross-cutting concerns. These establish precedent the spec must honor; do not re-open questions an ADR has already settled. If the feature genuinely requires departing from an ADR, that departure is itself a decision that needs a new or superseding ADR. Then scan the relevant areas of the codebase — existing patterns, related modules, the conventions this feature must live inside, and any prior art that suggests how this kind of problem has been solved here before. Questions should interrogate where the feature fits into *this* codebase, not run a generic design checklist.

Generate the full list of technical questions and decisions the spec needs to resolve. Before presenting this list, spawn a sub-agent to triage the questions. The sub-agent receives the full question list along with the PRD, relevant ADRs, CONTEXT.md content, and codebase patterns already gathered. It classifies each question into one of two categories:

- **Auto-resolve** — the answer is obvious, near-certain, or strongly implied by the PRD, existing ADRs, codebase conventions, or standard practice for this stack. The sub-agent provides the answer and a one-line rationale.
- **Ask the user** — the question involves a genuine architectural choice, a meaningful tradeoff, a policy decision, or anything where reasonable engineers would disagree. These are the questions worth the user's time.

Present only the questions that need the user's input — these become the discussion agenda. Hold the auto-resolved answers silently; they will be surfaced at the end alongside all other decisions in a consolidated decision log. Immediately start on the first user-facing question. Work through the user-facing questions in order, one at a time. Cluster a question with the next one only when the two are so tightly coupled that answering one alone would force re-opening the other (e.g., "which store backs this?" and "what's the key shape?"). Offer a suggested answer or design direction alongside each question. Lean on established codebase patterns and relevant ADRs unless there is a reason to depart — when departing, name the reason and flag the departure as requiring a superseding ADR.

When the answer is clear, a plain "I'd suggest X — sound good?" is enough. When the question has multiple defensible approaches with meaningfully different tradeoffs, first score it against the high-impact trigger criteria in the `deliberate` skill. If 2+ signals fire, pause and ask the user whether to deliberate before recommending. If the user agrees, run the deliberation protocol — the synthesis replaces the standard options block below. If the user declines (or fewer than 2 signals fired), present the options using the `AskUserQuestion` tool with one option flagged as recommended (append "(Recommended)" to its label). Place the recommended option first. Use the `description` field on each option to explain trade-offs or implications. A bare list of options without a pick is never acceptable — the user came to you for a recommendation, so always include your reasoning in the question text.

In Claude chat (where `AskUserQuestion` is not available), fall back to a numbered options block in text:

```
**Option 1** (recommended) — ...
**Option 2** — ...
**Option 3** — ...

I recommend Option 1 because <reason>. Pick one or propose another.
```

The user can also say "deliberate on this" at any point during the discussion to trigger the deliberation protocol for the current question, bypassing trigger scoring.

## What a tech spec covers

Think through the angles that matter for this feature: interfaces and contracts, data, dependencies, failure modes, security, operations (observability, performance, deployment), and whatever else the PRD and codebase demand. Any unresolved technical questions that need a spike or benchmark also belong in the spec as open items. The goal is to surface the decisions an engineer needs before writing code — not to complete a checklist.

### Correctness

If the PRD has a Correctness Constraints section (state invariants and behavioral constraints), the spec must show how the design preserves them. This is the highest-leverage correctness work in the spec.

- **Invariant preservation** — for each state invariant in the PRD, identify every operation that touches the invariant's data and show why it cannot violate the invariant given the design's constraints (transactions, validation order, type system, schema constraints). This is not pseudocode — it is an argument about structural properties of the design.
- **Making illegal states unrepresentable** — the data model should make PRD-violating states impossible to represent where feasible: non-nullable fields, foreign key constraints, check constraints, state machines with valid transitions only, types that encode the constraint (e.g., `NonEmptyList` instead of `List`). Distinguish between invariants enforced structurally (schema/types reject invalid states) and those enforced by application logic (code must get it right) — the latter need more test coverage.
- **Behavioral constraint feasibility** — for each behavioral constraint in the PRD ("never hold a lock for more than 100ms"), show how the chosen architecture satisfies it, or flag that the constraint conflicts with the design and needs product resolution via a soft flag.
- **Contracts at component boundaries** — make assumptions between modules explicit as preconditions and postconditions. What must be true before calling a component (preconditions) and what it guarantees on return (postconditions). This catches the class of bugs where both sides assume the other validates input.

### Testing

Testing follows the `surface-testing` skill methodology. Surface testing prescribes *design* decisions the spec is the right place to lock in — once the component is shaped without these, tests can't recover at write-time. The spec must identify:

- **The surface itself** — the testable entry point. For a CLI, a `Run(args, opts)` function that `main()` delegates to. For a service, a `Start()`/`Shutdown()` lifecycle. For a library, the exported functions consumers call.
- **External dependencies and their substitutes** — every service, store, or API outside this deployment unit, with the chosen substitute tier (in-process fake > testcontainers > hand-written fake). Name the library or image where one is picked.
- **Observability APIs for async behavior** — any behavior whose effect isn't visible through the surface (periodic flushes, WAL writes, compaction, cache eviction) needs a `Stats()` or status endpoint. These serve production operators too; they are not test-only.
- **Time handling** — if behavior depends on time (retries, expiries, scheduled work), an injectable clock is a component-design decision, not a test detail.
- **Data access shape** — if an in-memory store will exist alongside the real database, the spec must say so and pick a parity-testing model (full suite against both, or a dedicated store-contract suite).

`surface-testing` governs how tests are written; the spec records the decisions that make those tests possible.

## Level of detail

A tech spec fixes *contracts*, not *content*. Include what constrains what the engineer writes; exclude what they will write.

**Belongs in the spec:**

- Function, method, and endpoint signatures
- Struct, class, and type definitions
- Schema, tables, indexes, and constraints
- Component interfaces and responsibilities
- Error *categories* and the codes or types that clients switch on
- Text with an external consumer — user-facing error copy, API error codes, log lines that alerts or runbooks depend on
- Migration *strategy* — order of steps, backfill approach, rollback plan

**Belongs in the code, not the spec:**

- Function bodies and step-by-step pseudocode
- Full SQL statement bodies (the schema stays; the `SELECT ... JOIN ... WHERE` does not)
- Rendered config file contents
- Internal debug or developer-only log and exception text with no external consumer
- Import blocks and pinned dependency versions
- Directory tree listings
- Test bodies (the testing surfaces stay; the test code does not)
- Line-by-line migration DDL

The test: if a reader with the spec could write this detail themselves without losing the contract, leave it out. If losing it would change a behavior a user, client, or operator depends on, it stays.

## Soft-flagging product gaps

When a technical decision requires product clarity that is not in the PRD, do not stop. Insert an inline flag and continue with the best available assumption:

```
[NEEDS PRD CLARIFICATION: Who can delete a payment method — only the owner, or also admin roles?]
```

At the end of the discussion, list all flags with their count. If there are three or more, recommend a PRD revision pass before the spec is used — too many unresolved product assumptions in a tech spec creates rework risk. If there are one or two, note them and let the user decide whether to proceed.

## Running decision log

Keep a visible running list of technical decisions as they land — both those resolved during the discussion and those auto-resolved by the triage sub-agent. Show it on request, and whenever you finish a topic area (data model → API → error handling, etc.) before moving to the next. Decisions made during a tech spec discussion are the richest source of ADRs in the whole pipeline — choices about storage, API design, auth strategy, error handling patterns, and cross-cutting technical constraints are exactly what ADRs are for.

## Writing the document

Write a single markdown file at `docs/features/{feature}/tech-spec.md`. Structure it around what the discussion actually covered. Inline soft-flags stay in the document where they were placed.

Write for an engineer who was not in the discussion — including an LLM reading the spec as the primary input to `plan-from-context` or `plan-from-prompt`. No deictic references. Abandoned approaches from the conversation should not appear unless they are worth preserving as explicit context — "We considered X but chose Y because Z" is fine and useful; a bare reference to "the approach we rejected" is not.

Err toward shorter. A section that is not driving an implementation decision is noise — drop it. The goal is enough detail for a planner to produce phases, not an exhaustive design document.

A reasonable skeleton — drop sections that do not apply, add sections the discussion demanded:

```markdown
# {Feature Name} Tech Spec

_PRD: docs/features/{feature}/prd.md_

## Overview

## Component Design

## Data Model

## Correctness

### Invariant Preservation

### Illegal State Analysis

## API Design

## Dependencies

## Error Handling

## Security

## Observability

## Performance and Scale

## Testing

Testing follows the `surface-testing` skill.

Key surfaces:
- [integration: ...]
- [unit: ...]
- [fakes needed: ...]

## Migration and Deployment

## Open Questions
```

## Linking

- **PRD at `docs/features/{feature}/prd.md`** — link at the top as the source document.
- **ADRs in `docs/adr/`** — reference by number where a decision has been formally recorded.
- **Source files or directories in the repository** where directly relevant.
- **Other features' docs in `docs/`** when this feature genuinely builds on or integrates with another — link the specific document, not a hand-wave.
- **External URLs** for standards, RFCs, or public documentation.

Only link what the reader is guaranteed to have access to — in-repo docs, committed ADRs, public URLs. Not chat transcripts, Slack threads, private wikis, or anything behind a login the reader may not have.

## At the end of the discussion

1. Run a correctness pass. If the PRD has a Correctness Constraints section, re-read the Data Model and Component Design sections and confirm: every state invariant has a preservation argument for each operation that touches it, the data model makes illegal states unrepresentable where feasible (and explicitly notes which invariants rely on application logic), every behavioral constraint is satisfied by the chosen architecture (or soft-flagged as conflicting), and component boundaries have explicit preconditions/postconditions. Gaps here are design findings — resolve them before writing the spec.
2. Run a testability pass against the `surface-testing` skill. Re-read the Component Design and API Design sections and confirm: every surface named is reachable from a test, every external dependency has a substitute tier chosen, every async behavior has an observable assertion path (downstream effect, fake capture, or exposed observability API), time-dependent behavior routes through an injectable clock, and any in-memory store has a parity-testing model. Gaps here are design findings, not testing findings — resolve them before writing the spec.
3. Write the spec file (or produce the artifact in chat).
4. If the discussion resolved or introduced any domain terms, write them to the appropriate `docs/CONTEXT.md` in a single pass alongside the spec. If the file does not exist, create it in the `docs/` directory closest to the code whose domain it describes.
5. List any soft flags with their count. If three or more, recommend a PRD revision pass.
6. Present the complete decision log — auto-resolved answers from triage and decisions made during the discussion — as a single consolidated list. This is the user's first view of the auto-resolved answers; they can override any before the spec is written. Then, for each decision, apply this checklist. Only offer an ADR if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the spec. Decisions made here — storage choice, API patterns, auth approach, error handling strategy — are strong ADR candidates when they pass the checklist. Decisions resolved through the `deliberate` skill automatically satisfy "Hard to reverse" and "Result of a real trade-off" — only check "Surprising without context." These should already have been offered as ADR candidates immediately after deliberation resolved; do not re-offer them here.
7. For each decision that passes the checklist, offer to capture it as an ADR: "This looks ADR-worthy — want me to record it?" Invoke `adr-write` for the ones the user approves.
8. Note that the spec is the primary input to `plan-from-context` or `plan-from-prompt` when the user is ready to plan implementation.
9. Do not commit. The user handles commits.

## Revising an existing tech spec

Read the current spec *and* any code that already implements parts of it — the spec on disk may have drifted from reality. Surface any conflicts between the spec and the current code before discussing changes; those conflicts are usually the most important thing to resolve.

Run a focused discussion on what is changing. Preserve unchanged sections and their ordering. The soft-flag and ADR mechanics still apply. When code already exists for a section being revised, name what stays, what changes, and what gets removed — vague revisions produce vague implementations.
