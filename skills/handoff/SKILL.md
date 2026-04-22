---
name: handoff
description: Write a brief capturing the current state of in-flight work so it can be resumed in a fresh context window. Use when the user says "write a handoff", "summarize this session", "I want to continue in a new context", or needs a continuation brief for PRs/investigations that aren't done yet.
---

You are tasked with producing a **handoff brief** for the current conversation.
The purpose is to capture enough state that a fresh conversation (new context
window) can resume the work without re-asking what's been done.

## Step 1: Extract Current-State Facts from the Conversation

Pull out concrete, verifiable facts — not discussion:

- **Active task(s):** what the user is working on right now
- **PR(s) in flight:** PR numbers, branch names, head SHAs, current CI/review
  state, outstanding review threads (with short rationale for any left
  intentionally unresolved)
- **Files touched:** the set of files modified across the session, with
  one-line descriptions of what changed in each
- **Key decisions made:** short bullets only — no rationale blocks. If a
  decision warrants deeper capture, direct the user to `decisions-capture`.
- **Unresolved items:** open review comments, failing checks, questions that
  didn't get answered, blockers encountered
- **What's left to do:** ordered, concrete next steps
- **Dependencies and ordering:** anything that must happen before/after
  something else (e.g., "merge PR X before applying Terraform Y")
- **Pointers for next session:** relevant file paths, scripts, slash
  commands, memory entries, or external URLs the next session will need

Do NOT invent state that wasn't observed in the conversation. If a fact is
uncertain, say so explicitly.

## Step 2: Determine Output Location and Filename

If the user supplied an explicit path as the argument, use that path.

Otherwise, pick a location using this priority:
1. `plans/` directory in the project root, if it exists
2. `~/plans/<month>-<year>/` if `~/plans/` exists (check for a current
   month-year subdirectory, create it if a sibling exists)
3. Project root

Default filename: `handoff-<topic>.md` where `<topic>` is a short, hyphenated
description of the work (e.g., `handoff-dds-ca-pools.md`,
`handoff-auth-migration.md`). Keep it specific — "handoff-dds" is too broad
when there may be multiple DDS workstreams.

If the user's argument is a directory, append `handoff-<topic>.md` to it.
If the user's argument is a full file path, use it verbatim.

## Step 3: Write the Handoff Document

Follow this structure. Omit sections that don't apply — don't invent content
to fill them.

```markdown
# Handoff: [Subject] — YYYY-MM-DD

Brief (one sentence) of what this work is and why you'd pick it up.

## What We Worked On

- Active task(s) in 1–3 bullets. Link to Linear/Jira ticket if present.

## PR(s) In Flight

### PR #NNNN — <short title>
- Branch: `<branch-name>`
- Head SHA: `<sha>`
- Linear: <URL or ticket ID, omit if none>
- **State:** green/red/pending — describe CI, SonarCloud, Copilot review state
- **Outstanding threads:** list any unresolved review threads, with whether
  they are Fix-pending, Disagree (with rationale), or Cannot-determine
- **Ready for:** merge / human review / more fixes / rebase / etc.

(Repeat per PR. Omit this section entirely if no PRs are in flight.)

## Files Changed

- `path/to/file.ext` — one-line description of the change
- ...

## Key Decisions (brief)

- Decision 1 — one line
- Decision 2 — one line

(No rationale blocks. If rationale matters, note "see decisions-capture
output" and invoke that skill separately.)

## Unresolved Items

- What's still open, who/what is blocking it, and what needs to happen to
  unblock it.

## What's Left to Do

Ordered, concrete steps. Use numbered list.

1. Step 1
2. Step 2
3. ...

## Dependencies & Ordering

- Anything that must happen before/after something else (e.g., "Terraform
  apply order: A → B → C", "merge PR X before starting PR Y").

## Pointers for Next Session

- File paths, scripts, slash commands, memory entries, or URLs the next
  session will need to pick up.
```

### Writing Guidelines

- **Be factual, not narrative.** "PR #123 has 2 unresolved Copilot threads,
  both Disagree with replies posted" beats "we went back and forth with
  Copilot."
- **Include SHAs, URLs, command strings.** The next session should be able
  to copy/paste and resume without guessing.
- **Short bullets over paragraphs.** This is a resume-from-here brief, not
  an essay.
- **Omit rationale.** A handoff explains *what state the work is in* and
  *what to do next*, not *why we made each choice*. Rationale belongs in
  ADRs or `decisions-capture`.
- **Date the doc.** Put today's date (UTC) in the title so stale handoffs
  are obvious.
- **Call out uncertainty.** If you're not sure whether a CI check is still
  running or has flaked, say so rather than guessing.

## Step 4: Present to User

After writing the file, tell the user:
1. The file path where the handoff was written
2. A 1-2 sentence summary of the most important next step
3. Ask if anything important is missing

## Boundaries

- DO NOT capture design decisions with rationale (use `decisions-capture`
  or `adr-write`).
- DO NOT write an implementation plan with phases/milestones (use
  `plan-from-context` or `plan-from-prompt`).
- DO NOT invent work that wasn't actually done.
- DO NOT pause for confirmation before writing. Extract, write, let the
  user review.
- DO NOT include Co-Authored-By or Claude attribution in the document.
