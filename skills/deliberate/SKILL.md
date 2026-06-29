---
name: deliberate
description: Spawn parallel advocate sub-agents to deliberate on a high-impact decision, then synthesize
  their arguments into a structured comparison with a recommendation. Use when a decision is central to
  the design, cascades to many other decisions, is hard to reverse, or genuinely uncertain. Triggered
  automatically by blueprint-create and blueprint-review when they detect a high-impact
  decision, or invoked directly by the user with "deliberate on this" or "/deliberate".
allowed-tools: Read, Agent, AskUserQuestion
---

# Deliberation Protocol

Some decisions are high-impact — central to the design, cascading to other decisions, hard to reverse, or genuinely uncertain. This skill spawns parallel advocate sub-agents to argue for different approaches, synthesizes their arguments into a structured comparison, and presents the result with a recommendation.

## Standalone use

When invoked directly (via `/deliberate` or "deliberate on this" outside of another skill), gather context before running:

1. Ask the user to state the decision and the approaches they see.
2. Look for a PRD, tech spec, ADRs, CONTEXT.md, and user stories in the current project's `docs/` directories. Read any that exist.
3. Scan relevant codebase areas if the decision touches implementation patterns.
4. Run the protocol below (Steps 1-4).

## Trigger Criteria

Score the decision against four signals. If **2 or more** are true, the decision qualifies for deliberation.

| Signal | Definition |
|---|---|
| **Cascading** | Resolving this constrains or re-opens 2+ other decisions already in scope |
| **Hard to reverse** | Changing direction later requires significant rework of the document, code, or user expectations |
| **Genuine uncertainty** | After consulting ADRs and codebase patterns, 2+ options look equally defensible — the recommendation would require significant hedging |
| **Design-central** | This choice defines the conceptual model other decisions reason about (data model shape, primary user flow, auth strategy, API style) |

### User-initiated trigger

The user can say "deliberate on this" (or similar) at any point during a discussion or review. This bypasses trigger scoring — the protocol runs immediately for the current question or finding.

### False-positive guardrails

- Do **not** trigger deliberation when one option is clearly better given ADRs and codebase patterns. Uncertainty must be genuine.
- Do **not** trigger deliberation for P2 findings in review skills — only P0 and P1.
- Do **not** nest deliberation. Advocate agents never trigger deliberation themselves.

## Running the Protocol

### Step 1: Enumerate approaches

Before spawning advocates, enumerate the viable approaches (minimum 2, maximum 3). Each must be meaningfully distinct — not a minor variant of another. If only two approaches exist, use two advocates. Do not force a third.

State the approaches to the user in one line each before spawning, so they can redirect if an approach is missing.

### Step 2: Spawn advocate agents (parallel)

Spawn one advocate agent per approach **in a single message with parallel Agent tool calls** (use `model: "opus"`). Each agent argues FOR its assigned approach and is honest about weaknesses.

Every advocate receives the same full context block. Paste the full text of each document — do not pass file paths alone. Sub-agents cannot read files the orchestrator has not provided.

**Advocate agent prompt:**

```
You are an advocate for a specific design approach. Your job is to make the strongest possible case FOR your assigned approach and be honest about its weaknesses.

DECISION UNDER DELIBERATION:
<the exact question or finding being deliberated>

YOUR ASSIGNED APPROACH:
<approach name and one-line description>

FULL CONTEXT:
PRD:
<paste full PRD text, or "not found">

TECH SPEC:
<paste full tech spec text, or "not found">

USER STORIES:
<paste full text, or "not found">

CONTEXT.md (domain glossary):
<paste full text, or "not found">

ADRs available (read on demand if needed):
<list each ADR filename and path, or "none found">

Codebase patterns:
<paste relevant code snippets, existing patterns, or "not examined">

OTHER APPROACHES BEING ADVOCATED (for contrast, not for you to argue against):
<list the other 1-2 approaches by name only>

Produce your advocacy in this exact format:

## Advocate Report: <Approach Name>

**Core Idea** — <one sentence: what this approach actually does>

**Strongest Arguments**
<3-5 concrete reasons this approach is right for this specific project and context. Reference the PRD, ADRs, codebase patterns, or domain glossary — not generic engineering principles.>

**Cascading Implications**
<What downstream decisions does this approach constrain or unlock? Name specific questions from the discussion or spec and say how they resolve under this approach.>

**Biggest Risk**
<One paragraph on the most serious way this approach could fail or create pain. Be specific to this project.>

**Reversal Cost**
<Low / Medium / High — one sentence on what changing your mind looks like after committing: scope of code rewrite, data migration, user-facing impact.>

**Honest Weaknesses**
<1-3 weaknesses you cannot argue away. Do not minimize. A future reader should trust this section.>
```

### Step 3: Synthesize

After all advocates complete, synthesize their reports into a comparison. The synthesis is what the user sees — keep it scannable.

**Synthesis format:**

```
## Deliberation: <Decision Title>

<1-2 sentences framing why this decision is high-impact and what's at stake.>

| | <Approach A> | <Approach B> | <Approach C (if present)> |
|---|---|---|---|
| **Core idea** | ... | ... | ... |
| **Strongest argument** | ... | ... | ... |
| **Cascading implications** | ... | ... | ... |
| **Biggest risk** | ... | ... | ... |
| **Reversal cost** | Low/Med/High | Low/Med/High | Low/Med/High |

**Recommendation**: <Approach N> — <2-3 sentences explaining why, referencing project context, ADRs, or PRD goals specifically. Not generic principles.>

**Strongest dissent**: <One sentence — the best argument against the recommended approach, drawn from a competing advocate's report.>

Pick the recommended approach, choose a different one, or propose another direction.
```

The synthesis must always include a recommendation. A bare comparison table without a pick is never acceptable.

### Step 4: Resolve

The user picks an approach (or proposes a new one). The decision is recorded in the running decision log and marked as a deliberation outcome.

## Post-Deliberation: ADR Handling

A decision that went through deliberation has already demonstrated two of the three ADR criteria:

- **Hard to reverse** — this was a trigger signal
- **Result of a real trade-off** — multiple advocates argued for genuinely different approaches

The skill checks only the third criterion: **Surprising without context** — would a future reader wonder "why did they do it this way?"

If it passes, offer the ADR **immediately** after the deliberation resolves — do not defer to end-of-discussion. The deliberation context is freshest now and produces richer ADR content.

## Integration: Create Skills (blueprint-create)

Deliberation integrates into the back-and-forth discussion flow. When the skill is about to present a numbered options block for a question, it first scores the 4 trigger criteria. If 2+ fire:

1. Pause and tell the user: "This decision looks high-impact — it [name the specific signals that fired, e.g., 'cascades to the data model and API design, and I'm genuinely uncertain which approach is better']. Should I deliberate before recommending?"
2. If the user agrees (or if the user proactively said "deliberate on this"), run the protocol (Steps 1-4 above).
3. The deliberation synthesis replaces the standard options block. The question is resolved through deliberation rather than a simple recommendation.
4. Continue to the next question in the list.

If the user declines deliberation, present the standard options block with a recommendation as usual.

## Integration: Review Skills (blueprint-review)

Deliberation integrates into Phase 5 (Apply Fixes and Surface Decisions). When the orchestrator is about to present a **design-decision finding** (verdict: Upheld or Confirmed, routed as surface-to-user, priority P0 or P1), it scores the finding against the 4 trigger criteria. If 2+ fire:

1. Tell the user: "This finding looks high-impact — deliberating before presenting options."
2. Run the protocol (Steps 1-4 above), using the finding's fix options as the starting point for approach enumeration.
3. Present the deliberation synthesis instead of the standard finding options block.
4. Apply the user's chosen approach to the document as usual.

Clarification findings (verdict: Needs clarification or Downgraded to clarification) do not trigger deliberation — they are product decisions that need user input, not technical trade-offs that benefit from advocate analysis.
