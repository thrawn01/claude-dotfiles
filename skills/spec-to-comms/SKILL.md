---
name: spec-to-comms
description: >
  Turn a feature's design document (its blueprint, or a legacy tech spec) into a human-facing
  overview document for developers impacted by the change. Use when you want to communicate a
  technical change to the broader engineering org: "write a developer communication", "create
  an overview for devs", "make this accessible to impacted engineers", "create an overview from
  the blueprint".
---

# Create a Developer Communication from a Blueprint

Read the feature's design document and write a human-facing overview document at
`docs/features/{feature}/overview.md`. The overview translates the design's implementation
detail into what impacted engineers need to know: why the change is happening, what is
moving, and what their code will look like after.

**Source document:** the feature's `blueprint.md` (or, for older features, `tech-spec.md`).
"The spec" throughout this skill means whichever of these exists.

## Environment

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the spec** | Read from `docs/features/{feature}/blueprint.md` (or the legacy `tech-spec.md`) | Ask the user to paste the design doc |
| **Writing the overview** | Write to `docs/features/{feature}/overview.md` | Produce as markdown artifact; tell user the intended path |
| **Supporting docs** | Read any analysis docs in the same `docs/features/{feature}/` directory | Ask the user to paste relevant summaries |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise
you are in Claude chat.

## Before writing

Read the design document. Also read any supporting analysis documents in the same directory (e.g.,
dependency analysis, spike outputs). These often contain findings that clarify domain
boundaries or constraints that are relevant to impacted developers.

Identify the audience: developers whose code will be changed by this work. They are not the
implementers. They need to understand the impact on their service, not how the migration tool
works.

Ask the user one question before drafting if the answer is not clear from the spec:

- Does this change require the reader to take any manual action, or is their code migrated
  automatically?

If the spec makes this clear (e.g., "a migration tool rewrites all consumers atomically"),
skip the question and proceed.

## What to include

**Lead with why and what.** Structure the overview with a `### Why` and `### What` subsection
under the top-level `## Overview`. The Why explains the technical or business problem being
solved (cache invalidation, build times, blast radius, etc.). The What states what is
happening at a high level.

**What's changing and when.** A concise numbered list of phases from the consumer's
perspective. Each phase entry names what moves and what that means for the reader. Skip
internal implementation details (tool names, algorithm choices, PR sequencing steps).

**What changes in your code.** For any phase that changes import paths, type qualifiers, or
mock usage, include concrete before/after code examples. Examples should be copy-paste-ready
and use the actual import paths from the spec. If multiple domains are involved, show a
multi-domain example.

**Domain boundary lists.** Show which types or interfaces move to which packages as bullet
lists, not tables. Single-column tables do not paste well into Notion and other tools. Use a
bold label with a colon for the package name and description, followed by a bullet list of
type names. Collapse file-level detail into type-level summaries; the audience cares about
type names, not source files.

**Migration order.** If the spec defines a migration order (e.g., hottest domain first),
include it. Developers need to know when their service will be affected.

**Backward compatibility (or lack thereof).** If the spec explicitly states there are no
re-exports or compatibility shims, call this out clearly as a prominent paragraph. Developers
mid-PR during a domain migration need to know their imports will be rewritten atomically.

## What to omit

Leave out anything that is only relevant to the people doing the migration:

- How the migration is implemented (tool internals, algorithm choices, invocation steps)
- Internal PR sequencing steps that have no consumer-visible effect
- Test infrastructure details (harness mechanics, generated file movement, test helper changes)
- Open questions that are blockers for implementers but not for consumers
- Design decisions that are TBD for later phases and have no current consumer impact

Examples of things to omit: migration tool location and dependencies, symbol map structure,
`go:generate` directive details, SCC/cycle-detection mechanics, `analysistest` harness usage.

If the spec has an Open Questions section, omit it entirely. Consumers do not act on
unresolved implementation questions.

## Style rules

- Use plain prose. No em dashes (`--` or Unicode em dash). Use a single hyphen (`-`), a
  semicolon (`;`), or parentheses where an em dash would appear.
- A table with only one column is never a table. Use a bullet list instead.
- Headers use title-style separators with a single hyphen, e.g. `## Phase 1 - Interface Split`.
- Bold labels followed by descriptions use a colon, e.g. `**Interface imports:** the qualifier
  changes...`.
- List items that are label-description pairs use a colon separator, not a dash.
- Keep sentences short. The reader is skimming to understand impact, not reading a design doc.
- Do not add comments to code examples.

## Document structure

Use this skeleton; drop sections that do not apply, add sections the spec demands:

```markdown
# {Feature or Change Name}

## Overview

{One paragraph summary of the package or system being changed.}

### Why

{Why this change is happening: the technical or business problem it solves.}

### What

{What is being done at a high level, and that it is phased.}

## What's Changing and When

{Numbered list of phases from the consumer's perspective.}

{Paragraph on whether the reader's code is migrated automatically or requires manual action.}

{Paragraph on backward compatibility (or lack thereof).}

## Phase 1 - {Name}

### New Import Paths (or equivalent heading for the change type)

{Bullet list of what moves where.}

### What Changes in Your Code

{Before/after code examples.}

### Migration Order (if applicable)

{Ordered list of domains or services, with rationale.}

## Phase 2 - {Name}

### What Changes in Your Code

{Before/after code examples.}

### Domain Boundaries (or equivalent)

{Reference tables of types/interfaces by domain.}

## Phase 3 - {Name} (if applicable)

{Brief summary. If design is TBD, say so in one sentence.}

## Validation (if meaningful to consumers)

{What success looks like and how it will be measured. One paragraph.}
```

## After writing

Do not commit. The user handles commits.

If you added any before/after code examples, verify the import paths match the actual module
path from the spec (not a placeholder like `github.com/example/...`).
