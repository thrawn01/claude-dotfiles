---
name: adr-write
description: Record a single architecture decision as a numbered ADR. Use when the user says "record this as an ADR", "log this decision", "capture this as an ADR", or "create an ADR"; or when another skill has surfaced a decision at the end of a discussion and the user has approved turning it into an ADR; or when a significant architectural call has been made mid-implementation and the user wants it preserved. 
---

# Create an Architecture Decision Record

Record architecture decisions as numbered ADR files in `docs/adr/`, following the Michael Nygard template.

The skill supports three operations, and more than one can happen in a single invocation: creating a new ADR, making a minor edit to an existing one, and superseding an older ADR with a new one. Follow the corresponding sections below for whichever operations the invoker asks for. For example, "record that we're switching to Redis, and fix the typo in ADR-0003 while you're at it" is a create plus an edit in one turn — do both.

If the request is ambiguous, ask before proceeding: which decision to record if several candidates surfaced in a long discussion, or whether a change to an existing ADR is a minor edit versus a supersession. Do not guess.

## Write for a reader who was not in the conversation

The ADR must stand alone. The only context a future reader has is the codebase and the other ADRs in `docs/adr/`. They will not have the discussion that produced this decision, and they will read it months or years later.

Concretely, this means:

- **No references to abandoned ideas that never existed in the code.** If the conversation considered and rejected `FeatureX`, and `FeatureX` was never built, do not mention it by name. "We considered a queue-based approach and rejected it because..." is fine; "We will not use FeatureX" is not, because the reader has no idea what FeatureX was.
- **No pronouns or deictic references that only resolve in-conversation.** "The approach we discussed earlier," "the option Alice preferred," "the thing from the meeting" — all cut. Name the actual technical choice.
- **No appeals to conversational authority.** "Per the discussion on Tuesday" or "as agreed in chat" tell the reader nothing. State the reasoning itself.
- **Alternatives get named only if they are real and comprehensible.** "Considered PostgreSQL and DynamoDB; chose PostgreSQL because..." works — both are recognizable technologies. "Considered the approach from the prototype" does not work unless the prototype still exists and is referenced somewhere discoverable.
- **Consequences are about the system, not the team's process.** "This locks us into relational modeling" is a consequence. "This means we do not need to revisit the discussion" is not.

A useful test before writing: if you stripped every proper noun introduced only in the conversation, would the ADR still make sense? If not, rewrite until it does.

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

[What is the issue that we're seeing that is motivating this decision or change? Describe the forces at play, including technological, political, social, and project-local. These forces are probably in tension, and should be called out as such. The language in this section is value-neutral. It is simply describing facts.]

## Decision

[What is the change that we're actually proposing or doing? Stated in full sentences, active voice: "We will..."]

## Consequences

[What becomes easier or more difficult to do and any risks introduced by the change that will need to be mitigated. Include both positive and negative consequences. Be honest about tradeoffs.]
```

Notes on the template:

- `N` in the heading is the decimal number matching the filename prefix (no leading zeros in the heading itself: `# 7. Use PostgreSQL for primary storage`, not `# 0007. ...`).
- `Date` is today's date in ISO format. When editing an existing ADR, do not change the Date — it records when the decision was made, not when the file was last touched.
- `Status` defaults to `Accepted`. Other valid values: `Proposed`, `Deprecated`, `Superseded by ADR-NNNN`. Only use something other than `Accepted` if the user asks.
- **Decision** is stated in active voice, "We will...", declarative and specific enough that a reader knows what was chosen.
- **Context** describes the forces, constraints, and tradeoffs. If alternatives were considered and rejected, name them here (subject to the rules in "Write for a reader who was not in the conversation").
- **Consequences** covers follow-on effects, positive and negative. Honest about tradeoffs, not a sales pitch.
- If a section would be thin because the source material is thin, ask the user rather than pad.
- Do not add sections beyond these four. ADRs are deliberately minimal; extra sections dilute them.

## Linking

Links are allowed only to artifacts the reader is guaranteed to have: other ADRs in `docs/adr/`, source files in the repository, and external URLs for referenced standards or articles. Nothing else.

Do not link to:

- **PRDs, tech specs, or other `docs/<feature>/` files.** These may not be checked into the repository, may live in a separate wiki or doc tool, or may have been deleted or moved by the time someone reads the ADR. The ADR cannot assume they exist.
- **Chat transcripts, Slack threads, or meeting notes.** The reader does not have access.
- **Ticket numbers,** unless the project has an explicit convention of preserving them and the tracker will still be reachable.
- **Branches, PRs, or commits by hash.** These are points in time, not durable references. If you need to point at code, reference the resulting file path.

The ADR captures the decision, its context, and its consequences directly in the file. If context from a PRD or tech spec matters to the decision, restate it in the ADR's Context section in the ADR's own words — do not rely on an external pointer to carry the meaning.

Inline references to other ADRs are fine and encouraged where genuinely useful: "supersedes ADR-0003" or "builds on the storage choice in ADR-0007". Those are the one kind of cross-reference we know will resolve, because they live in the same directory as this file.

## Supersession

When a new decision reverses an earlier one, handle it as a single operation:

1. Create the new ADR normally (next number, today's date, Status `Accepted`). In its Context, reference the ADR it replaces: "Supersedes ADR-NNNN, which chose X; this ADR revisits that decision because..."
2. Edit the old ADR's Status line from `Accepted` to `Superseded by ADR-NNNN` (where NNNN is the new ADR's number). Do not change anything else in the old ADR — its Context, Decision, and Consequences remain as a record of what was once believed. Do not change its Date.

Both steps happen in the same invocation. A half-done supersession — new ADR written, old one still marked Accepted — leaves the ADR log internally inconsistent, which is worse than not superseding at all.

Before doing a supersession, confirm with the user: "This will mark ADR-NNNN as superseded and create ADR-MMMM in its place. Proceed?" Supersession is a deliberate act; the skill should not infer it from ambiguous phrasing.

## After the operation

Applies to all three operations — create, edit, supersede.

1. Confirm what was written or changed, with the file path(s). For supersession, confirm both files.
2. Do not commit. The user handles commits.

## What this skill does not do

- Does not batch-create ADRs for multiple unrelated new decisions in one invocation. Each new decision gets its own turn, so the Context and Consequences can be captured with focus rather than lumped together. (This is about *new* decisions only — combining a create with an unrelated edit or supersession in the same invocation is fine.)
- Does not decide for the user whether something is ADR-worthy. If they asked to record it, record it.
