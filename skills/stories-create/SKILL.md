---
name: stories-create
description: Generate user stories from a PRD, including correctness-derived stories. Use when the user asks to "write stories", "create user stories", "generate stories from the PRD", or when prd-create recommended stories for this feature. Do NOT use when the PRD's acceptance criteria are already at story granularity, for infrastructure/library work, or for simple features where stories would just restate the PRD.
---

# Create User Stories from a PRD

Read the PRD for the feature, generate user stories with observable acceptance criteria, and write the result to `docs/features/{feature}/user-stories.md`. Stories translate the PRD's requirements into discrete user workflows that an engineer can implement and verify independently.

## Environment

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the PRD** | Read from `docs/features/{feature}/prd.md` | Ask the user to paste the PRD |
| **Writing stories** | Write to `docs/features/{feature}/user-stories.md` | Produce as markdown artifact; tell user the intended path |
| **Revising existing stories** | Read from disk | Ask user to paste |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat.

## Inputs

If `$ARGUMENTS` is provided, treat it as a path to the PRD file. Otherwise, search for `prd.md` in `docs/features/` directories under the current working directory.

Before starting, locate and read these files:
- The PRD file (required)
- `CONTEXT.md` — look in the `docs/` directory at the service root. This is the domain glossary. Optional — skip if not found.

If the PRD file cannot be found, ask the user for the path.

Additionally, list files in the `adr/` directory at the service docs root (e.g., `docs/adr/`). Read titles and scan for any that cap product scope (users, tenancy, roles, access). These constrain what stories can describe.

Derive the `{feature}` slug from the PRD file path — the directory name under `docs/features/`.

## Before generating: check whether stories are needed

Evaluate the PRD against the criteria. Stories are needed when ANY of these are true:
- **Multiple user personas with divergent workflows** — the PRD describes distinct roles whose interactions follow different paths.
- **Complex user-facing interactions with branching paths** — multi-step flows, approval chains, wizards.
- **Large PRD-to-test gap** — many discrete behaviors to verify, no single engineer holds them all.
- **Team coordination** — multiple engineers will work on this feature in parallel.

Stories are overhead when:
- Infrastructure, platform, or library work (the "user" is another system or API consumer).
- The PRD's correctness constraints and acceptance criteria are already at story granularity.
- Simple feature (single CRUD surface, config flag, small behavioral change).
- Solo developer holding full context.

If stories are clearly overhead, say so: "This PRD's acceptance criteria are precise enough to go straight to the tech spec — stories would just restate what's here. Want to proceed anyway?" Only continue if the user confirms.

## Generating stories

Read the PRD end-to-end. If the PRD already contains a User Stories section with partial stories, use those as a starting point — adopt, refine, or expand them rather than generating a parallel list. Note which stories came from the PRD vs. which were generated.

Generate stories by working through these sources in order:

### 1. User workflow stories

For each user persona identified in the PRD, trace their primary workflows through the feature. Each discrete workflow becomes a story. A story should be small enough to implement and verify independently, but large enough to deliver a meaningful behavior — not a task ("add a button") and not an epic ("manage orders").

Format each story as:

```markdown
### Story N: <short descriptive title>

**As a** <persona>, **I want to** <action>, **so that** <outcome>.

**Acceptance criteria:**
- Given <precondition>, When <action>, Then <observable result>
- Given <precondition>, When <action>, Then <observable result>
```

### 2. Negative and failure stories (from correctness constraints)

If the PRD has a Correctness Constraints section, derive stories from it:

- For each **state invariant**, write a story that describes what happens when a user action would violate the invariant. The acceptance criteria must specify the system's rejection behavior.

  Example: If the PRD says "an account balance is never negative," write:
  ```
  ### Story N: Transfer rejected when insufficient balance

  **As a** customer, **I want** the system to reject a transfer that would
  overdraw my account, **so that** my balance never goes negative.

  **Acceptance criteria:**
  - Given my balance is $100, When I transfer $150, Then the transfer is
    rejected with an insufficient-funds error and my balance remains $100
  - Given my balance is $0, When I transfer any amount, Then the transfer
    is rejected
  ```

- For each **behavioral constraint** that has a user-observable manifestation, write a story that describes the system's behavior under the constraint condition. Focus on what the user observes. If the behavioral constraint is purely architectural with no user-visible effect (e.g., "never hold a distributed lock for more than 100ms"), do not generate a story — instead, note it in a comment block at the end of the Correctness Stories section: `<!-- Architectural constraint (no user-facing story): ... -->`. These constraints are verified through tech spec enforcement and testing, not user stories.

  Example: If the PRD says "never silently drop a message," write:
  ```
  ### Story N: Message delivery failure is surfaced to sender

  **As a** user, **I want** to be notified when my message cannot be
  delivered, **so that** I can retry or take alternative action.

  **Acceptance criteria:**
  - Given the messaging service is unavailable, When I send a message,
    Then I receive an error indicating the message was not delivered
  - Given the messaging service recovers, When I retry, Then the message
    is delivered successfully
  ```

### 3. Negative case and persona-boundary stories

For each workflow story, consider: does the PRD specify what happens when this workflow fails or is attempted by the wrong persona? If the PRD defines distinct access roles, generate stories for cross-persona boundaries (e.g., a regular user attempting an admin-only action). Only generate negative cases the PRD explicitly mentions or that are implied by correctness constraints.

Place these in the document by where they belong, not in a separate section: a persona-boundary or access-control story goes under **Correctness Stories**; a generic failure of a specific workflow goes alongside that workflow under **User Workflow Stories**.

### 4. Edge case stories

For each user workflow story, consider: what happens at the boundaries? Derive edge case stories only when the PRD explicitly mentions the edge case or when the edge case is implied by a correctness constraint. Do not invent edge cases the PRD doesn't address.

### Acceptance criteria rules

Every acceptance criterion must be **mechanically verifiable** — a test can assert the result without human judgment.

- **Theater** (reject): "Then the user feels confident the transfer succeeded"
- **Real** (accept): "Then a confirmation screen displays the transfer amount, recipient, and new balance"

For each criterion, mentally ask: "How would a test know this happened?" If the answer requires looking at a screen and making a subjective judgment, rewrite the criterion to specify the observable system behavior.

Use the `CONTEXT.md` domain glossary (if present) for terminology. Do not introduce terms that conflict with the glossary.

## Presenting stories for review

After generating, present the full story list to the user. Group stories by persona if multiple personas exist, otherwise present in workflow order.

For each story, briefly note which PRD section it traces to (e.g., "from Scope item 3" or "from State Invariant: non-negative balance"). This traceability helps the user verify coverage.

Ask the user to review. Handle feedback:
- **Split a story** — if the user says a story is too large, split it into smaller stories that each deliver independently verifiable behavior.
- **Merge stories** — if two stories are so tightly coupled they can't be implemented independently, merge them.
- **Remove a story** — if the user says a story is out of scope or already covered by the PRD's acceptance criteria, remove it.
- **Add a story** — if the user identifies a missing workflow, add it.
- **Adjust criteria** — if acceptance criteria are vague or wrong, rewrite them.

Iterate until the user is satisfied.

## Writing the document

Write a single markdown file at `docs/features/{feature}/user-stories.md`.

Structure:

```markdown
# <Feature Name> User Stories

_PRD: docs/features/{feature}/prd.md_

## User Workflow Stories

### Story 1: <title>
...

### Story 2: <title>
...

## Correctness Stories

### Story N: <title>
...

## Edge Case Stories

### Story N: <title>
...
```

Use the two-section split (User Workflow Stories / Correctness Stories) only when the PRD has a Correctness Constraints section. Otherwise, drop the `## Correctness Stories` heading and list the workflow stories directly under a single `## User Stories` heading. Edge Case Stories is optional — include only if edge case stories were generated.

Number stories continuously across all sections (Story 1, Story 2 … do not restart at 1 per section), so each story has a stable unique id that `/stories-review` can cite.

Write for an engineer who was not in the discussion. No deictic references.

## At the end

1. Confirm the file was written with its path.
2. Print a brief coverage summary:
   ```
   Stories: N total (N workflow, N correctness, N edge case)
   PRD sections covered: [list]
   PRD sections with no stories: [list, if any — note whether intentional]
   ```
3. If any PRD requirements have no corresponding story, ask the user whether that's intentional or a gap.
4. Note that the stories are ready for validation with `/stories-review`.
5. Do not commit. The user handles commits.

## Revising existing stories

Read the current `docs/features/{feature}/user-stories.md` and the PRD. Run a focused discussion on what is changing — do not regenerate unchanged stories. If the PRD's Correctness Constraints section was added or modified since the stories were written, generate new correctness stories for the added constraints.
