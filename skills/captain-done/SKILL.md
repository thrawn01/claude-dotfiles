---
name: captain-done
description: "Finish a Linear ticket from inside its worktree and hand it back to the captain: verify
  the PR merged, set the ticket to Done, and post a `## Ticket Done` entry to the ticket's PROJECT
  status-update timeline (never a ticket comment) so the orchestrating /captain picks it up on its
  next re-hydrate. Use when a ticket's PR is merged and you're closing it out — 'captain done',
  '/captain-done', 'finish this ticket and tell the captain', 'mark this done for the captain', 'hand
  this back to the captain'. This is the worker-side finishing counterpart to /captain (the
  orchestrator) and a specialization of /linear-handoff for the merged-and-closed moment. Do NOT use
  to pause mid-ticket (use /linear-handoff), to hand off one long-running ticket's own progress as a
  ticket comment (that's /linear-handoff issue mode), or when the work isn't part of a captain-managed
  project."
argument-hint: "[ticket-id]  (defaults to the current branch's ticket)"
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion]
---

# Hand a finished ticket back to the captain

You are a **worker** closing out a ticket whose PR has merged. Your job is to leave the one signal the
orchestrating `/captain` reads on its next re-hydrate: the ticket is **Done** in Linear, and a
**`## Ticket Done` entry on the project's status-update timeline** says it merged and closed, plus any
follow-up the captain should sequence. This is the specialization of `/linear-handoff` for the
merged-and-closed moment — it removes that skill's project-vs-issue guess by **always** targeting the
project.

## Why the project, not a ticket comment

`/linear-handoff`, run from a ticket branch, often guesses an **issue** `## Handoff` comment — a
resume note for *this ticket*. That's the wrong container for "I'm finished, sequence the next thing":
the captain's memory and the human-visible build status both live on the **project** status-update
timeline. A finish note buried in a ticket comment is invisible to the captain's synthesis. So
`captain-done` writes to the project, unconditionally.

## Interop with the captain's memory — the title convention

The project status-update timeline is **shared** between two writers, distinguished by heading:

| Writer | Heading | The captain treats it as… |
|---|---|---|
| `/captain` (orchestrator) | `## Captain — <date>` | its **memory** (the newest one = last synthesis) |
| `/captain-done` (worker) | `## Ticket Done — <TEAM>-<NUM> — <date>` | a **completion signal** to fold in and reconcile |

**Always** begin your update body with the `## Ticket Done — <TEAM>-<NUM> — <UTC date>` heading. It
is load-bearing: it's how the captain avoids mistaking your finish note for its own last synthesis.
Never post a `## Captain —` heading (that's the captain's) and never omit the heading.

## Prerequisites

- **Linear MCP** connected (`mcp__claude_ai_Linear__*`). If absent, stop and say so.
- Run from **the ticket's worktree/branch** (or pass the ticket id). The ticket must carry a
  `project` — that's the captain's timeline. No project ⇒ this is the wrong skill; use
  `/linear-handoff`.
- The PR is **actually merged** (you verify it in §2 — never assume).

## 1. Resolve the ticket and its project

Resolve in order; stop at the first hit:

1. **Supplied** — the user gave a ticket id/URL → `get_issue` it.
2. **Current branch** — `git rev-parse --abbrev-ref HEAD` matches Linear's shape
   (`<user>/<team>-<num>-<slug>`) → extract `<TEAM>-<NUM>` → `get_issue` it.

From `get_issue`, record the **project** (name/id) and the current **status**. If there is no
project, stop: `captain-done` has no captain timeline to write to — tell the user to use
`/linear-handoff` instead.

## 2. Verify the merge — do not assume

Confirm the PR actually merged before you claim it. Prefer `gh`:

```
gh pr view <branch-or-number> --json number,state,mergedAt,mergeCommit
```

- **Merged** → capture the PR number and merge SHA for the note.
- **Not merged / no PR / uncertain** → **stop.** Do not set the ticket Done and do not post a "merged"
  note. Tell the user what you found (open PR, failing CI, no PR) and let them decide. A wrong "merged"
  is the worst outcome here — the captain sequences the next work on it.

If there's genuinely no PR because the ticket shipped another way, say so and confirm with the user
before proceeding; the note must describe how it actually shipped, not a PR that doesn't exist.

## 3. Set the ticket to Done (idempotent)

The Linear ticket status is the captain's **truth** signal. Ensure it is **Done**:

- Already Done (e.g. Linear's GitHub integration auto-closed it on merge) → leave it, note it.
- Otherwise → `save_issue` with the ticket id and state **Done**.

This is the one place a worker owns the ticket lifecycle (consistent with the captain guardrail
"ticket lifecycle stays with the worker").

## 4. Read the latest project update for continuity

`get_status_updates` (`type:"project"`, the project, newest few) so your note continues the trail
rather than repeating it. You may see the captain's last `## Captain —` synthesis and/or earlier
`## Ticket Done —` entries; write the **diff** since then.

## 5. Compose and post the `## Ticket Done` entry

Compose per `/linear-handoff` §3 (the compose rules there apply — factual, short, ids inline, never
assert unverified state), but with the fixed heading and the merged/closed framing. Cover:

- **Merged + closed** — `<TEAM>-<NUM> <title>` — #<PR> (`<sha>`), one line on what shipped + test
  state; and that the ticket is now Done.
- **Follow-up / discovered work** — anything the captain should sequence, each with a tracking handle
  (a follow-up ticket id if you created one; otherwise a concrete description so the captain can). If
  a handoff comment on the ticket already spells out follow-ups, point to it rather than restating.
- **Branch** — the ticket's branch/worktree, so the captain can reconcile (offer worktree cleanup).
  Do **not** remove the worktree yourself — worktree cleanup is the captain's reconcile step.

Pick **health**: `onTrack` normally; `atRisk`/`offTrack` only if you're flagging a regression or a
loose end the captain must act on.

### Template

```markdown
## Ticket Done — <TEAM>-<NUM> — <UTC date>

**Merged + closed:** <TEAM>-<NUM> <title> — #<PR> (`<sha>`). <what shipped + test state>. Ticket → Done.

**Follow-up:** <ticket id or concrete description; "none" if clean>

**Branch:** <branch name> — worktree can be reconciled.
```

Post with `save_status_update` (`type:"project"`, `project:"<name>"`, `health:"<…>"`, `body:"<…>"`).
**Omit `id` — always create a new entry; never overwrite a prior update** (the timeline is the trail).
Posting is the go-ahead — don't display the body for approval first.

## 6. Report

Give the user the project Updates URL and a one-line summary: ticket set Done, `## Ticket Done` posted
to the project, PR #/sha, and any follow-up you flagged for the captain.

## Boundaries

- DO NOT write the finish note as a **ticket `## Handoff` comment** — that's the mistake this skill
  exists to prevent. It goes on the **project** timeline.
- DO NOT post a `## Captain —` heading or overwrite the captain's synthesis updates — use the
  `## Ticket Done —` heading and always create a new entry.
- DO NOT set the ticket Done or claim "merged" without verifying the merge in §2.
- DO NOT remove the worktree — point at it; the captain reconciles cleanup on confirm.
- DO NOT capture design rationale here (use `/decisions-capture` or `/adr-write`).
- DO NOT include Co-Authored-By or Claude attribution in the body.

## Early exits

| Condition | Action |
|---|---|
| No Linear MCP | Stop — this skill requires Linear |
| Ticket has no project | Wrong skill — use `/linear-handoff`; say why |
| PR not merged / no PR / merge uncertain | Stop — report what you found; don't set Done or claim merged |
| No prior project update | Fine — yours may be the first; note it and proceed |
