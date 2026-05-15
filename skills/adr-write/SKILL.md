---
name: adr-write
description: Record a single architecture decision as a numbered ADR. Use when the user says "record this as an ADR", "log this decision", "capture this as an ADR", or "create an ADR"; or when another skill has surfaced a decision at the end of a discussion and the user has approved turning it into an ADR; or when a significant architectural call has been made mid-implementation and the user wants it preserved. 
---

# Create an Architecture Decision Record

Record architecture decisions as numbered ADR files in `docs/adr/`, following the Michael Nygard template.

The skill supports three operations, and more than one can happen in a single invocation: creating a new ADR, making a minor edit to an existing one, and superseding an older ADR with a new one. Follow the corresponding sections below for whichever operations the invoker asks for. For example, "record that we're switching to Redis, and fix the typo in ADR-0003 while you're at it" is a create plus an edit in one turn — do both.

If the request is ambiguous, ask before proceeding: which decision to record if several candidates surfaced in a long discussion, or whether a change to an existing ADR is a minor edit versus a supersession. Do not guess.

## Conciseness and decision focus

ADRs record *decisions*, not designs. Every sentence earns its place or gets cut.

- **State the decision and the forces behind it. Stop.** Implementation details, API shapes, data models, and component interactions belong in code and tech specs, not here.
- **One idea per sentence.** No filler, hedging, or throat-clearing.
- **No restatement.** The decision appears once, in the Decision section. Context sets up the problem; Consequences describe effects. Neither repeats the decision in different words.
- **Bullets over prose** when listing forces, alternatives, or consequences.

## Write for a reader who was not in the conversation

The ADR must stand alone. The only context a future reader has is the codebase and the other ADRs in `docs/adr/`. They will not have the discussion that produced this decision, and they will read it months or years later.

Concretely, this means:

- **No conversation artifacts.** Don't reference abandoned ideas by name, in-conversation pronouns ("the approach we discussed"), or conversational authority ("as agreed in chat"). Name real technologies and state reasoning directly.
- **Alternatives must be recognizable.** "Considered PostgreSQL and DynamoDB" works. "Considered the prototype approach" does not — unless the prototype exists in the repo.
- **Consequences describe system effects, not process.** "Locks us into relational modeling" is a consequence. "No need to revisit this discussion" is not.

Test: strip every proper noun introduced only in conversation. Does the ADR still make sense? If not, rewrite.

## Numbering

1. List `docs/adr/` to find existing ADRs. If the directory does not exist, create it.
2. Find the highest `NNNN-` prefix currently in use.
3. The new ADR is `NNNN+1`, zero-padded to 4 digits.
4. If `docs/adr/` is empty, start at `0001`. The conventional first ADR is "Record architecture decisions" itself — if the directory is empty and the user is recording a different decision, mention this and offer to create the meta-ADR first.

## Filename

`docs/adr/NNNN-kebab-case-title.md`

The title should be short, declarative, and match the decision. "Use PostgreSQL for primary storage" → `0007-use-postgresql-for-primary-storage.md`. Avoid vague titles like "Database choice".

## Template

Use this exact structure:

```markdown
# N. Title

Date: YYYY-MM-DD

## Status

Accepted

## Context

[Forces motivating this decision. Factual, value-neutral. Call out tensions.]

## Decision

[What we are doing. Active voice: "We will..." Be specific.]

## Consequences

[What becomes easier, harder, or riskier. Both positive and negative.]
```

Notes on the template:

- `N` in the heading is the decimal number (no leading zeros: `# 7. Use PostgreSQL...`, not `# 0007. ...`).
- `Date` is today's ISO date. When editing, do not change the Date.
- `Status` defaults to `Accepted`. Other valid values: `Proposed`, `Deprecated`, `Superseded by ADR-NNNN`. Only deviate if the user asks. The Status field is not a changelog — do not append amendment notes, dates of edits, or summaries of what changed. An ADR is a decision record, not a log book; its history lives in version control.
- **Context** states forces and tensions. Name rejected alternatives only if they are recognizable technologies. Do not restate the decision.
- **Decision** is active voice ("We will..."), specific, stated exactly once. Single source of truth for what was chosen.
- **Consequences** lists effects — positive and negative. No sales pitch, no restatement of the decision.
- Thin source material → ask the user rather than pad.
- Do not add sections beyond these four (no "See Also", "References", "Notes", etc.). ADRs are minimal by design.

## Linking

The only links allowed are external URLs to standards, specifications, or documentation (e.g., an RFC, a library's docs, a protocol spec). Place them inline where they support a claim in Context or Consequences.

Do not link to or cross-reference:

- **Other ADRs.** No "See Also" sections, no "builds on ADR-0007" prose. Each ADR stands alone. The sole exception is the `Superseded by ADR-NNNN` status marker, which is a mechanical pointer, not a content reference.
- **PRDs, tech specs, internal docs, or wiki pages.** Restate relevant context in the ADR directly.
- **Chat transcripts, Slack threads, meeting notes, ticket numbers, branches, PRs, or commits.**

## Supersession

When a new decision reverses an earlier one, handle it as a single operation:

1. Create the new ADR normally (next number, today's date, Status `Accepted`). Its Context describes why the previous approach is being revisited — state the forces directly. The reader should understand the problem without consulting the old ADR.
2. Edit the old ADR's Status line from `Accepted` to `Superseded by ADR-NNNN`. Change nothing else. Do not change its Date.

Both steps happen in the same invocation. Confirm with the user first: "This will mark ADR-NNNN as superseded and create ADR-MMMM in its place. Proceed?"

## After the operation

Applies to all three operations — create, edit, supersede.

1. **Review for conciseness.** Spawn a sub-agent (Agent tool) to review the ADR against the review checklist below. If it flags issues, apply the fixes. One review pass only — do not re-review after fixes.
2. Confirm what was written or changed, with the file path(s). For supersession, confirm both files.
3. Do not commit. The user handles commits.

### Review checklist

Spawn a sub-agent with the following prompt. Replace `{file_path}` with the actual path.

> Review the ADR at `{file_path}` for conciseness and decision-focus. Read the file, then check every item below. For each violation, quote the offending text and suggest a replacement. If clean, say "No issues."
>
> Guiding principles:
> - Retain all standard sections: Context, Decision, Consequences
> - Trim verbose prose, not vital content
> - Remove content that doesn't belong in an ADR
> - Consequences and anti-patterns are important — trim only restatements of the decision
> - Remove ADR cross-references; keep only external URLs to documentation
>
> Checklist:
> 1. **Restatement** — Decision appears exactly once in the Decision section. Context and Consequences must not echo it.
> 2. **Design details** — Implementation specifics (API shapes, data models, component interactions, sequence flows) belong in code or tech specs, not the ADR.
> 3. **Extra sections** — Only Status, Date, Context, Decision, Consequences are allowed. Flag "See Also", "References", "Notes", "Alternatives", or any additions.
> 4. **ADR cross-references** — No mentions of other ADRs ("see ADR-0003", "builds on ADR-0007"). Exception: `Superseded by ADR-NNNN` in the Status field.
> 5. **Non-external links** — No links to PRDs, tech specs, internal docs, wiki pages, Slack, tickets, branches, PRs, or commits. Only external URLs allowed.
> 6. **Verbose prose** — Paragraphs that should be bullets, filler phrases, hedging, throat-clearing.
> 7. **Process language** — Consequences describe system effects, not team process.
> 8. **Conversation artifacts** — No references to abandoned ideas, in-conversation pronouns, or conversational authority.

## What this skill does not do

- Does not batch-create ADRs for multiple unrelated new decisions in one invocation. Each new decision gets its own turn, so the Context and Consequences can be captured with focus rather than lumped together. (This is about *new* decisions only — combining a create with an unrelated edit or supersession in the same invocation is fine.)
- Does not decide for the user whether something is ADR-worthy. If they asked to record it, record it.
