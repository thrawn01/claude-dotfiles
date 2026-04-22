---
name: decisions-capture
description: Capture decisions, rationale, and context from the current conversation into a referenceable document
---

You are tasked with capturing the decisions from the current conversation. Your
job is to extract all context, decisions, rationale, and concrete examples into
a clear, referenceable document that fully captures what was discussed and
decided.

## Step 1: Extract Everything from the Conversation

Thoroughly analyze the entire conversation to extract:
- **The feature or system being designed** — what is being built and why
- **Every topic discussed** — each area of discussion becomes a section
- **The outcome of each topic** — what was decided, including API shapes, naming choices, behavioral semantics, patterns adopted
- **The rationale behind each outcome** — why one option was chosen, what alternatives were considered and rejected
- **Concrete code examples** — function signatures, interface definitions, usage patterns that were agreed upon
- **Research findings** — anything discovered through investigation that informed decisions
- **Open questions** — anything explicitly deferred or left unresolved

Do NOT ask the user to validate your extraction — they may not remember every
detail. Extract comprehensively, write the document, and let them review the
output.

## Step 2: Determine Output Location

Check if a `plans/` directory exists in the project root. If it does, write the
document there. If it does not, write to the project root.

The filename MUST follow the convention: `decisions-<topic>.md` where `<topic>`
is a short, hyphenated description of the subject (e.g.,
`decisions-streaming.md`, `decisions-auth-middleware.md`,
`decisions-batch-processing.md`).

## Step 3: Write the Decisions Document

```markdown
# Decisions: [Subject]

This document captures the decisions and context from our discussion on [subject].
These decisions represent the agreed-upon approach.

## [Topic 1 Title]

[What was discussed, what was decided, and concrete code examples if applicable.]

**Rationale:** [Why this approach. What alternatives were considered and why
they were rejected.]

## [Topic 2 Title]

[Continue for each topic discussed in the conversation.]

## Open Questions

[Anything explicitly deferred or unresolved. Omit this section if there are
none.]
```

Each topic discussed in the conversation becomes its own section. The section
title describes the topic (e.g., "Server-Side API", "Retry Semantics",
"Package Structure"). The body captures the outcome and rationale.

### Writing Guidelines

- **Lead with code.** Show the agreed-upon API shape (signatures, interfaces,
  types) before explaining it. Readers should see what the thing looks like
  before reading why.
- **Capture rejected alternatives.** For every non-obvious decision, note what
  was considered and why it was rejected. This prevents future re-litigation of
  settled questions.
- **Use rationale blocks.** Start rationale paragraphs with `**Rationale:**` or
  `**Rationale: [short label].**` so they are scannable.
- **Be specific.** "We chose X over Y because Z" is useful. "We discussed
  several options" is not.
- **Include usage examples.** Show what handler code, client code, or test code
  looks like under the design. These examples anchor the design to real
  developer experience.
- **No implementation details.** The document captures *what* and *why*, not
  *how*. Function bodies, internal algorithms, and step-by-step implementation
  instructions belong in an implementation plan, not here.
- **Reference existing code.** When the design extends or mirrors existing
  patterns in the codebase, reference them (e.g., "consistent with how
  `Client.Do` works today").
- **Preserve nuance.** If a decision had caveats, edge cases, or "this might
  change if X," capture that. A design doc that only records the happy path
  will be re-litigated when someone hits the edge case.

## Step 4: Present to User

After writing the file, tell the user:
1. The file path where the document was written
2. Ask if anything needs adjusting or is missing

## Boundaries

- DO NOT create an implementation plan. This is a decisions capture.
- DO NOT add sections for timeline, milestones, or phases.
- DO NOT invent decisions that weren't made in the conversation. If something
  was discussed but not resolved, list it under the "Open Questions" section.
- DO NOT include implementation details like function bodies or algorithms.
- DO NOT pause for confirmation before writing. Extract, write, then let the
  user review.
