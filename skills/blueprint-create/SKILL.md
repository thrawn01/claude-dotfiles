---
name: blueprint-create
description: Run one continuous back-and-forth design discussion — product definition and technical design together — and write a single Blueprint to docs/features/{feature}/blueprint.md. Use when the user asks to "write a blueprint", "create a blueprint", "design this feature", "scope and design X", or otherwise wants to think through both what a feature must do and how it will be built before implementation. Replaces the separate prd-create / spec-create / stories-create flow with one document and one conversation. Do NOT use for bug fixes or tweaks too small to warrant a design document, or when the user is brainstorming without committing to a document.
---

# Create a Blueprint

Have a single back-and-forth discussion that elicits both halves of a feature's design — the **product definition** (why it exists, what it must do, what correct means) and the **technical design** (the data, the interfaces, the architecture) — track decisions as they land, and write the result to `docs/features/{feature}/blueprint.md` at the end.

One document, one conversation, one author. The two halves are one continuous thought, not a handoff between two people. Keeping them together removes the drift that appears when a separate product doc and technical doc fall out of sync — the build then implements something the product never asked for. The AI build reads the whole Blueprint as one context.

The line-by-line **how** (how each function is written) is not the Blueprint's job. It is the build's, inferred from tests that exercise the design. The Blueprint defines what correct looks like; the tests prove the implementation meets it. The technical half fixes *contracts*, not *content*.

See `Handbook/Blueprint.md` for the canonical template and the architectural principles the technical half should apply.

## Environment

This skill runs in both Claude Code and Claude chat. Behavior differs in these places:

| | Claude Code | Claude chat |
|---|---|---|
| **Writing the Blueprint** | Write directly to `docs/features/{feature}/blueprint.md` | Produce as a markdown artifact; tell the user the intended path |
| **Revising an existing Blueprint** | Read the file (and any implementing code) from disk | Ask the user to paste the current Blueprint |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface ADR-worthy decisions clearly; tell the user to run `adr-write` for each in Claude Code |
| **Linear ticket + feature dir** | Resolve the id, then create/label/assign or reuse per the shared procedure | Create the Linear issue via MCP if the user supplies the repo; surface the dir + branch names |
| **Question options** | `AskUserQuestion` tool | Numbered options block in text |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat. Everything else — the discussion, question list, suggested answers, and running log — is identical in both environments.

## Starting the discussion

Do these once, up front, before generating any questions. The Blueprint is a single artifact, so each of these happens exactly once — not once per half.

1. **Resolve the Linear id and feature directory FIRST.** Follow the shared procedure in `~/.claude/skills/shared/linear-workflow.md` — check the §0 precondition (skip Linear entirely if it isn't in use here and take the plain-slug fallback), otherwise resolve-or-create the id, assign `me`, advance to `In Progress` (only if not already started), apply the `repo:` label from the git remote, name the directory `docs/features/<TEAM>-<NUM>-<slug>/`, and prepare to echo the `ticket/<TEAM>-<NUM>-<slug>` branch. Infer the `{feature}` slug from the discussion — short, kebab-case, specific; it is much clearer once you understand the feature, so do not block the start on it (you can name the dir at write time). Throughout this skill, `{feature}` denotes the full `<TEAM>-<NUM>-<slug>` directory name. Resolve the id once for the whole Blueprint; never create a second issue for the technical half.

2. **Read the domain glossary.** Look for `CONTEXT.md` files in `docs/` directories relevant to the feature (see [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) for location rules). Read any that exist once and hold them in memory for the whole session — do not re-read. These are the project's domain glossaries; use them throughout to catch terminology conflicts in both halves (problem framing, component names, data model terms, API naming).

3. **Scan the ADRs.** List every file in `docs/adr/` and read each title. Read the full ADR for two kinds of title:
   - **Scope-capping** titles — mention users, tenancy, regions, languages, roles, pricing, deployment targets. These limit what the *product* can ask for (e.g., "no multi-tenancy", "English-only MVP"). Frame product questions so they do not invite answers the architecture has ruled out; if the user wants something an ADR forbids, surface the ADR explicitly rather than silently narrowing.
   - **Topic** titles the feature's *technical* design touches — storage, API patterns, auth, error handling, deployment. These establish precedent the technical half must honor. Do not re-open questions an ADR has settled; a genuine departure is itself a decision that needs a new or superseding ADR.

   Skip titles that are clearly irrelevant to this feature.

4. **Scan the codebase.** Look at the areas this feature will live inside — existing patterns, related modules, the conventions it must fit, and prior art that shows how this kind of problem has been solved here before. Technical questions should interrogate where the feature fits into *this* codebase, not run a generic design checklist.

5. **Generate the full question list** across both halves — the product questions (problem, users, scope, correctness) and the technical questions (interfaces, data, failure modes, security, operations) the Blueprint needs to resolve. Tailor it to what the feature actually requires; do not pad with questions whose answers are already obvious from the user's input.

6. **Triage the technical questions.** Spawn a sub-agent that receives the full technical question list plus the PRD-equivalent context gathered so far (problem framing, relevant ADRs, CONTEXT.md content, codebase patterns). It classifies each technical question:
   - **Auto-resolve** — the answer is obvious, near-certain, or strongly implied by the problem framing, existing ADRs, codebase conventions, or standard practice for this stack. Provide the answer and a one-line rationale.
   - **Ask the user** — a genuine architectural choice, a meaningful trade-off, a policy decision, or anything where reasonable engineers would disagree.

   Hold the auto-resolved answers silently; they are surfaced at the end in the consolidated decision log. (Product questions are not triaged this way — they are the user's to answer.)

7. **Present the agenda and start.** Show the user the product question list and the technical questions that need their input, then immediately start on the first question. Do not pause to ask whether to reorder, skip, or add — the user can redirect at any point, but the default is forward motion. Showing the list gives shape; asking permission to proceed just adds friction.

## The discussion

Work the questions one at a time. Run the product half first, then the technical half — the technical design exists to satisfy the product intent, so the intent must be clear before designing for it. But this is one conversation: when a product answer obviously settles a technical question (or vice versa), record it and move on; do not re-litigate it when you reach the other half.

For each question:

- **Offer a suggested answer or direction.** The user reacts and refines rather than generating from scratch. "Who are the target users? My read is primarily internal ops staff — right?" moves faster than an open question. In the technical half, lean on established codebase patterns and relevant ADRs unless there is a reason to depart — when departing, name the reason and flag it as needing a superseding ADR.
- **When the answer is clear, a plain "I'd suggest X — sound good?" is enough.** When the question has multiple defensible answers with meaningfully different implications, first score it against the high-impact trigger criteria in the `deliberate` skill. If 2+ signals fire, pause and ask the user whether to deliberate before recommending. If the user agrees, run the deliberation protocol — the synthesis replaces the standard options block. If the user declines (or fewer than 2 signals fired), present the options using the `AskUserQuestion` tool with one option flagged as recommended (append "(Recommended)" to its label, place it first). Use the `description` field to explain trade-offs. A bare list of options without a pick is never acceptable — always include your reasoning in the question text.

    In Claude chat (no `AskUserQuestion`), fall back to a numbered options block:

    ```
    **Option 1** (recommended) — ...
    **Option 2** — ...
    **Option 3** — ...

    I recommend Option 1 because <reason>. Pick one or propose another.
    ```

    The user can say "deliberate on this" at any point to trigger the deliberation protocol for the current question, bypassing trigger scoring. When a decision is resolved by `deliberate`, offer to capture it as an ADR immediately (it auto-satisfies the "Hard to reverse" and "Real trade-off" ADR criteria — see *At the end*), not at session end.
- **Resolve the question before moving on.** Stay on it until it is answered or the user explicitly defers it.
- **Interrupt on vague or overloaded terms.** "You said 'user' — do you mean the account owner or anyone with access?" Propose a precise alternative grounded in the glossary and resolve the term before continuing. Track resolved terms for the single CONTEXT.md writeback at the end.
- **Test every scope boundary with one concrete scenario.** When a non-goal or boundary is stated: "So if a customer cancels mid-billing-cycle, that's out of scope?" One scenario per boundary, framed as confirmation, not challenge.

Keep a visible running decision log as decisions land — both halves, and the technical questions the triage sub-agent auto-resolved. Show it on request, and whenever you finish a domain (problem → users → scope; then data → API → failure handling) before moving to the next. The user should be able to correct the log in real time.

When the question list is exhausted, or the user calls it done, move to the pre-write passes and then write.

## What the product half covers

Use these as the source for the product questions. Not every feature needs every one — tailor to the feature.

- **Problem and why.** What user or business problem does this solve? Why now? What is the technical goal that follows?
- **Users or personas.** Who is this for? If multiple, which is primary?
- **Mental model.** For platform, framework, or tooling products: how should users think about the system? What are the core concepts and their relationships? Often more clarifying than user stories for developer-facing products.
- **Core design principles.** The non-negotiable constraints that shape all decisions — what the product will always do, and what it will deliberately never do. Surface these early; they resolve many later questions and are strong ADR candidates.
- **Correctness constraints.** Two subsections, elicited with three explicit prompts (see below).
- **User stories.** Optional — see *User stories* below for the necessity check.
- **Acceptance criteria.** The conditions that prove the feature is done, each mechanically verifiable. Ask "How would a test know this happened?" of every criterion; if the answer requires human judgment, rewrite it. Cover negative/failure cases explicitly for any domain where failure modes matter.
- **Success metrics.** Post-ship outcomes that show the feature worked (adoption, latency, incidents avoided). Never a restatement of scope — "the capabilities were built" is execution, not a metric. Omit the section entirely if no plausible post-ship outcome exists to measure; many infrastructure changes have none, and that is correct.
- **Scope and non-goals.** What is in the first version, and explicitly what is out. Non-goals are often more clarifying than the in-scope list.
- **Dependencies and constraints.** External systems, timelines, regulatory or compliance requirements, known technical limits.

### Correctness constraints (the highest-leverage product work)

Write a named **Correctness Constraints** section with two subsections:

- **State invariants** — always-true statements about data ("an account balance is never negative"). For each invariant, specify what violates it and what the system does when violation is attempted or detected. *An invariant without an enforcement mechanism is a comment in dead code.*
- **Behavioral constraints** — things the system must never do, even in failure ("never silently drop a message", "never hold a distributed lock for more than 100ms"). The most valuable behavioral constraints rule out entire implementation approaches before code is written.

Elicit these with three explicit prompts:
- **Concurrency**: "What happens when two users interact with the same resource simultaneously?"
- **Reversibility**: "Which operations can be undone? Which are permanent?"
- **Partial failure**: "What happens if this operation succeeds halfway?"

## User stories (optional section)

There is no separate stories file. When stories add value, they become a **User Stories** section inside `blueprint.md`.

**Necessity check.** Include stories when ANY of these hold:
- **Multiple personas with divergent workflows** — distinct roles whose paths through the feature differ.
- **Complex interactions with branching paths** — multi-step flows, approval chains, wizards.
- **Large definition-to-test gap** — many discrete behaviors to verify; no single engineer holds them all.
- **Team coordination** — multiple engineers building in parallel and needing work-unit boundaries.

Skip stories (they are overhead) when the feature is infrastructure/platform/library work (the "user" is another system or API consumer), when the correctness constraints and acceptance criteria are already at story granularity, when the feature is simple (single CRUD surface, config flag, small behavioral change), or when a solo developer holds the full context. If stories are clearly overhead, say so and move on; do not generate them just to fill the section.

**Generating stories**, when warranted, work these sources in order and number them continuously across all groups (Story 1, Story 2, … — do not restart per group):

1. **Workflow stories** — for each persona, trace their primary workflows; each discrete workflow is a story. Small enough to implement and verify independently, large enough to deliver meaningful behavior (not a task "add a button", not an epic "manage orders"). Format:

   ```markdown
   ### Story N: <short title>

   **As a** <persona>, **I want to** <action>, **so that** <outcome>.

   **Acceptance criteria:**
   - Given <precondition>, When <action>, Then <observable result>
   ```

2. **Correctness stories** (only when there is a Correctness Constraints section):
   - For each **state invariant**, a story for what happens when a user action would violate it; the acceptance criteria specify the rejection behavior and that state is unchanged.
   - For each **behavioral constraint** with a user-observable manifestation, a story for what the user observes under the constraint condition. If the constraint is purely architectural with no user-visible effect (e.g., "never hold a lock more than 100ms"), do NOT write a story — note it in a comment block instead: `<!-- Architectural constraint (no user-facing story): ... -->`. These are verified through technical enforcement and tests, not stories.

3. **Negative and persona-boundary stories** — for distinct access roles the product defines, stories for cross-persona boundaries (a regular user attempting an admin-only action). Only generate negative cases the product explicitly mentions or that a correctness constraint implies. A persona-boundary or access-control story belongs among the correctness stories; a generic workflow failure belongs alongside its workflow story.

4. **Edge case stories** — only when explicitly mentioned or implied by a correctness constraint. Do not invent edge cases.

Every acceptance criterion must be mechanically verifiable. Theater ("Then the user feels confident") is rejected; observable behavior ("Then a confirmation screen displays the amount, recipient, and new balance") is accepted. Annotate each story with the section it traces to (e.g., "from Scope item 3" or "from State Invariant: non-negative balance") so coverage is checkable.

Respect the scope-capping ADRs scanned at the start: do not write stories for personas, roles, or capabilities an ADR has ruled out (e.g., no admin-role stories under a "no multi-tenancy" ADR). When the product half has a Correctness Constraints section, structure the section as two named subsections — `### User Workflow Stories` and `### Correctness Stories` (workflow, then correctness/negative/persona-boundary). When there is no Correctness Constraints section, list the workflow stories directly under the single `## User Stories` heading with no split. An `### Edge Case Stories` subsection is optional — include it only if edge case stories were generated.

UI mockups stay as separate Excalidraw/image files in the feature directory, linked from the User Stories (or Mental Model) section — never redrawn in markdown.

## What the technical half covers

Think through the angles that matter for this feature: interfaces and contracts, data, dependencies, failure modes, security, PII, operations (observability, performance, deployment, scale), and whatever else the product half and codebase demand. The goal is to surface the decisions an engineer needs before writing code — not to complete a checklist. Apply the architectural principles in `Handbook/Blueprint.md` (domain-based services, shallow critical path, single source of truth, transactions around every DB operation, denormalize within a service, and the rest).

### Domain-boundary opacity

A problem domain must not contain logic that belongs to a domain it calls. The caller depends on the callee's interface contract — never on how the callee fulfills it. If a domain needs a guarantee from a dependency, that guarantee is a contract of the interface (every implementation provides it); the caller never branches on which implementation is active, inspects implementation-specific error types, or relies on an implementation-specific property for correctness.

During the technical discussion, actively probe for domain-boundary leaks:
- For each interface the design defines, ask: "Does the caller ever need to know which implementation is behind this?" If yes, either the interface contract is incomplete (the guarantee should be part of it) or the caller is absorbing concerns that belong to the callee.
- For each correctness invariant, ask: "Is enforcement above the interface, or does it depend on a property of a specific implementation?" If the latter, the invariant breaks when the next implementation ships.
- For operational concerns (health checks, setup/teardown, durability), ask: "Does the calling domain branch on the dependency's type?" If yes, the dependency's interface needs a method (e.g., `Healthy()`, `Setup()`) so the caller stays opaque.

When the design has multiple implementations of an interface (storage backends, transport layers, auth providers), this principle must be stated as a Core Design Principle in the Blueprint and the Invariant Preservation section must confirm that no invariant relies on an implementation-specific property without making it a contract of the interface.

### Correctness translation (the highest-leverage technical work)

If the product half has a Correctness Constraints section, the technical half must show how the design preserves it:

- **Invariant preservation** — for each state invariant, identify every operation that touches the invariant's data and show why it cannot violate the invariant given the design's constraints (transactions, validation order, type system, schema constraints). This is an argument about structural properties, not pseudocode.
- **Make illegal states unrepresentable** — the data model should make violating states impossible to represent where feasible: non-nullable fields, foreign keys, check constraints, state machines with only valid transitions, types that encode the constraint (`NonEmptyList` not `List`). Distinguish invariants enforced **structurally** (schema/types reject invalid states) from those enforced by **application logic** (code must get it right) — the latter need more test coverage.
- **Behavioral constraint feasibility** — for each behavioral constraint, show how the chosen architecture satisfies it, or flag a conflict with a soft flag (see below).
- **Component-boundary contracts** — make assumptions between modules explicit as preconditions and postconditions. This catches the bug class where both sides assume the other validates input.

### Testing (surface-testing decisions the design must lock in)

Testing follows the `surface-testing` skill. Surface testing prescribes *design* decisions the Blueprint is the right place to fix — once a component is shaped without them, tests cannot recover at write time. Identify:

- **The surface** — the testable entry point. A CLI's `Run(args, opts)` that `main()` delegates to; a service's `Start()`/`Shutdown()` lifecycle; a library's exported functions.
- **External dependencies and their substitutes** — every service, store, or API outside this deployment unit, with the substitute tier (in-process fake > testcontainers > hand-written fake). Name the library or image where one is picked.
- **Observability APIs for async behavior** — any effect not visible through the surface (periodic flushes, WAL writes, compaction, cache eviction) needs a `Stats()` or status endpoint. These serve production operators too; they are not test-only.
- **Time handling** — time-dependent behavior (retries, expiries, scheduled work) routes through an injectable clock; that is a component-design decision, not a test detail.
- **Data access shape** — if an in-memory store will exist alongside the real database, say so and pick a parity-testing model (full suite against both, or a store-contract suite).

### Level of detail — contracts, not content

The technical half fixes contracts, not content. Include what constrains what the engineer writes; exclude what they will write.

**Belongs in the Blueprint:** function/method/endpoint signatures; struct/class/type definitions; schema, tables, indexes, constraints; component interfaces and responsibilities; error *categories* and the codes/types clients switch on; text with an external consumer (user-facing error copy, API error codes, alert/runbook log lines); migration *strategy* (step order, backfill approach, rollback plan).

**Belongs in the code, not the Blueprint:** function bodies and step-by-step pseudocode; full SQL statement bodies (the schema stays; the `SELECT ... JOIN ... WHERE` does not); rendered config contents; internal debug/developer-only log text; import blocks and pinned versions; directory trees; test bodies (the testing surfaces stay; the test code does not); line-by-line migration DDL.

The litmus test: if a reader with the Blueprint could write this detail themselves without losing the contract, leave it out. If losing it would change a behavior a user, client, or operator depends on, it stays.

### Soft-flagging unresolved questions

Because both halves are in one conversation, most product gaps the technical design hits can be resolved inline — ask the user then and there. Only when a question genuinely cannot be settled in the moment, insert an inline flag and continue with the best available assumption:

```
[NEEDS CLARIFICATION: Who can delete a payment method — only the owner, or also admin roles?]
```

At the end, list all flags with their count. Three or more is a signal the Blueprint is not ready to build from — recommend resolving them before the build. One or two: note them and let the user decide.

## Pre-write passes

Before writing the file, run two mandatory passes over the discussion's conclusions:

1. **Correctness pass.** If there is a Correctness Constraints section, confirm: every state invariant has a preservation argument for each operation that touches it; the data model makes illegal states unrepresentable where feasible (and explicitly notes which invariants rely on application logic); every behavioral constraint is satisfied by the architecture (or soft-flagged as conflicting); component boundaries have explicit preconditions/postconditions; no invariant's enforcement relies on an implementation-specific property of a dependency without that property being a contract of the interface (domain-boundary opacity). Gaps here are design findings — resolve them before writing.
2. **Testability pass** against the `surface-testing` skill. Confirm: every named surface is reachable from a test; every external dependency has a substitute tier; every async behavior has an observable assertion path (downstream effect, fake capture, or exposed observability API); time-dependent behavior routes through an injectable clock; any in-memory store has a parity-testing model. Gaps here are design findings, not testing findings — resolve them before writing.

## Writing the document

Write a single markdown file at `docs/features/{feature}/blueprint.md`. Structure it around what the discussion actually covered — every section is optional; drop the ones the feature does not need and do not pad with empty headings. Order runs product half first, then technical half. Inline soft flags stay where they were placed.

A reasonable skeleton (drop what does not apply):

```markdown
# <Feature Name> Blueprint

## Objective

## Mental Model

## User Stories

## Correctness Constraints

### State Invariants

### Behavioral Constraints

## Acceptance Criteria

## Success Metrics

## Scope

### In Scope

### Out of Scope / Non-Goals

## Dependencies and Constraints

---

## Functional

## Architecture

## Data Design

### Invariant Preservation

### Illegal State Analysis

## Security

## PII

## Scale

## Testing

Testing follows the `surface-testing` skill.

Key surfaces:
- [integration: ...]
- [unit: ...]
- [fakes needed: ...]

## Limitations & Future Work

## Open Questions
```

Keep PII as its own section — do not fold it into Security. Mark anything unresolved with `TODO:` and a one-line description of what is missing; a silent gap reads as an oversight, a labeled gap reads as a known edge. Open Questions holds genuine unknowns that still need resolution but did not block writing — both product (scope boundaries, user scenarios, outcome thresholds) and technical (a spike, a benchmark, an undecided contract). It is distinct from inline `[NEEDS CLARIFICATION: ...]` soft flags, which mark a specific decision the build is waiting on; if a question is really a build blocker, make it a soft flag, not an open question.

Use prose where prose is clearer; lists for stories, metrics, and scope bullets. Err toward shorter — a section not driving a decision is noise. Write for a reader who was not in the discussion (a reviewer, an on-call engineer in two years, an LLM reading the Blueprint as the primary input to `plan-from-context` / `plan-from-prompt`). No deictic references ("the option we discussed"). "We considered X but chose Y because Z" is fine and useful; a bare reference to "the approach we rejected" is not.

**Write the glossary once.** If the discussion resolved or introduced any domain terms, write them to the appropriate `docs/CONTEXT.md` in a single pass alongside the Blueprint. Because the product and technical halves merge into one document, the glossary is written exactly once — not once per half. If the file does not exist, create it in the `docs/` directory closest to the code whose domain it describes, using the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md). In a monorepo, route terms to the per-service `docs/CONTEXT.md` they belong to.

## Linking

The Blueprint can link to:

- **ADRs in `docs/adr/`** — by number, where a decision has been recorded.
- **UI mockups** — the Excalidraw/image files in the feature directory.
- **Source files or directories** in the repository where directly relevant.
- **Other features' docs in `docs/`** when this feature genuinely builds on or integrates with another — the specific document, not a hand-wave.
- **External URLs** for standards, RFCs, or durable public references.

Only link what the reader is guaranteed to have access to — in-repo docs, committed ADRs, public URLs. Not chat transcripts, Slack threads, private wikis, or other features' working notes.

## At the end of the discussion

1. Confirm the file was written with its path. Report the Linear issue (id + URL, now In Progress and assigned) and the branch command `git checkout -b ticket/<TEAM>-<NUM>-<slug>`.
2. List any soft flags with their count. If three or more, recommend resolving them before the build.
3. If a User Stories section was written, print a brief coverage summary — `Stories: N total (N workflow, N correctness, N edge case)`, the product-half sections each story traces to, and any product-half section with no story (note whether that is intentional or a gap). Skip this when no stories were generated.
4. Present the complete decision log — both halves, plus the technical answers the triage sub-agent auto-resolved — as a single consolidated list. This is the user's first view of the auto-resolved answers; they can override any. Then apply the ADR checklist to each decision. Offer an ADR only if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the Blueprint. Core design principles and the richest technical decisions (storage choice, API patterns, auth strategy, error handling) are strong candidates. Decisions resolved through `deliberate` automatically satisfy "Hard to reverse" and "Result of a real trade-off" — only check "Surprising without context"; these should already have been offered immediately after deliberation resolved, so do not re-offer them here.
5. For each decision that passes, offer to capture it as an ADR: "This looks ADR-worthy — want me to record it?" Invoke `adr-write` for the ones the user approves.
6. Note that the Blueprint is the primary input to `plan-from-context` or `plan-from-prompt`, and is ready for `blueprint-review` when the user wants an adversarial check.
7. Do not commit. The user handles commits.

## Revising an existing Blueprint

Read the current `docs/features/{feature}/blueprint.md` *and* any code that already implements parts of it — the file on disk may have drifted from reality. Surface any conflicts between the Blueprint and the current code before discussing changes; those conflicts are usually the most important thing to resolve. Run a focused discussion on what is changing — do not re-elicit the unchanged parts. When code already exists for a section being revised, name what stays, what changes, and what gets removed. Preserve unchanged sections and their ordering. When the User Stories section is being revised, adopt and refine the stories already present rather than regenerating them from scratch; only generate new stories for workflows or correctness constraints the existing set does not cover. The running-log, soft-flag, CONTEXT.md-writeback, and end-of-discussion ADR mechanics all still apply.
