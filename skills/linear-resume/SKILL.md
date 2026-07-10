---
name: linear-resume
description: "Resume in-flight work tracked in Linear by reading the latest handoff and surfacing
  where things stand + the reasoned next step. READ-ONLY: it reads, it does not branch, set up a
  worktree, change ticket status, or post anything. Use when the user says 'resume <project>',
  'where did we leave off', 'pick up the git-server build', 'what's next on this ticket',
  '/linear-resume', or hands a Linear project/epic/ticket link and wants to continue. Two modes:
  (1) hand it a PROJECT or EPIC to learn which ticket is next, then run /linear-start <ticket>;
  (2) hand it a single TICKET to re-hydrate a long-running, multi-session effort on that one ticket.
  Do NOT use to start work on a fresh ticket (that's /linear-start, run inside the ticket's
  worktree) or to write a handoff (that's /linear-handoff)."
argument-hint: "[project-name | epic-or-ticket-id-or-url]"
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion]
---

# Resume Linear-tracked work

Read the **latest handoff** for whatever the user is resuming and turn it into a resume-from-here
brief: where the build/ticket is, the open loose ends, and the reasoned next step. This skill is the
**read** counterpart to `/linear-handoff` (which writes the handoff) and the step that usually
precedes `/linear-start` (which begins the ticket). It is strictly **read-only** — it never
branches, creates a worktree, advances a ticket's status, or posts a comment/update.

## Prerequisites

- Linear MCP connected (the `mcp__claude_ai_Linear__*` tools). If absent, stop and tell the user
  this skill needs Linear.

## The container model (project vs. issue)

Linear stores a handoff in one of two places, and that is the only distinction this skill makes:

| Resuming… | Handoff lives as | Read with |
|---|---|---|
| a **project** (a coordinated multi-ticket build) | the newest **status update** | `get_status_updates` `type:"project"` |
| an **issue** — an **epic/parent** *or* a **standalone ticket** | the newest **handoff comment** | `list_comments` |

Epic-vs-standalone makes no difference to the mechanism — both are issues, both store handoffs as
comments. The only question is *project or issue?*

A **handoff comment** is identified by convention: its body begins with a `## Handoff` heading
(see `/linear-handoff`). When scanning an issue's comments, treat only those as handoffs; ignore
ordinary discussion.

## 1. Resolve what to resume

Resolve in order; stop at the first hit:

1. **Supplied** — the user named a project, or gave a ticket/epic id or Linear URL → use it. If it
   is an id/URL, `get_issue` it to learn its title, its `project`, and its `parent`.
2. **Current branch** — `git rev-parse --abbrev-ref HEAD` matches Linear's branch shape
   (`<user>/<team>-<num>-<slug>` or `ticket/<team>-<num>-<slug>`) → extract `<TEAM>-<NUM>`,
   `get_issue` it.

If neither yields anything, ask the user which project/epic/ticket to resume. Never guess.

**Decide project vs. issue:**

- The user named a **project** (or you only have a project) → §2a.
- The user handed an **issue** → §2b. (This is the same-ticket / epic-level case.)

## 2a. Read the latest project status update

`get_status_updates` with `type:"project"`, the project name, `orderBy:"createdAt"`, `limit:1` (pull
a few if you want the recent trail). The newest update is the resume point.

If the project has **no** status updates, say so and fall back to listing the project's in-progress
/ recently-updated issues so the user can choose — there is no recorded handoff yet.

## 2b. Read the latest handoff comment on the issue

`list_comments` for the issue, newest first. Find the first whose body begins with a `## Handoff`
heading — that is the latest handoff.

- **Found** → that comment is the resume point.
- **None, but the issue has a `project`** → there is no per-ticket handoff; the coordinated build's
  state lives at the project level. Tell the user and offer to resume the **project** instead
  (re-run §2a against `issue.project`).
- **None and no project** → there is no recorded handoff. Fall back to the issue's own description +
  most recent comments and say plainly that you are reconstructing from the ticket itself, not from
  a handoff.

## 3. Surface the resume brief

Render what you read as a short, factual brief — do not dump the raw update/comment verbatim, distil
it:

- **Where it stands** — what last merged / what state the ticket is in (with ids/SHAs as written).
- **In flight** — any open PR + its CI/review state, as recorded.
- **Open loose ends** — deferred/skipped items, unresolved decisions, anything left red on purpose.
- **The reasoned next step** — the next task and *why* it was chosen, copied from the handoff. If the
  handoff is stale or self-contradictory, say so rather than papering over it.

If you read a project update naming the next **ticket**, name that ticket explicitly. If you read a
single ticket's handoff, frame the next step as continuing *that* ticket.

**Do not assert state the handoff did not claim.** If the handoff says "CI unverified," carry that
caveat forward — do not upgrade it to "green."

## 4. Hand off to the next action (suggest, never execute)

End by pointing at the next command — but **do not run it**; the user drives:

- **Cross-ticket** (you resumed a project/epic and the next step is a *different* ticket) → give
  the ticket's `gitBranchName` and suggest creating its worktree with the user's wrapper (e.g.
  `claude-branch <gitBranchName>`), then running `/linear-start <TEAM>-<NUM>` inside it.
- **Same-ticket** (you resumed one ticket to continue it) → if a worktree/branch for it already
  exists, give the user its path or branch to reopen (e.g. via `claude-branch <branch>`); if not,
  suggest creating it the same way. Either way, this skill does not touch git.

## Boundaries

- **READ-ONLY.** Never `git worktree add` / branch / checkout, never `save_issue` (no status or
  assignee change), never `save_comment` / `save_status_update`. Resume informs the next action; it
  is not the next action.
- Do not invoke `/linear-start` or `/linear-handoff` for the user — suggest the command and let them
  decide.
- Do not re-derive sequencing the handoff already reasoned out — carry its "next" forward; only flag
  it if it's stale or wrong.

## Early exits

| Condition | Action |
|---|---|
| No Linear MCP available | Stop — this skill requires Linear |
| Nothing resolvable to resume | Ask the user which project/epic/ticket |
| Project has no status updates | Say so; list in-progress issues to choose from |
| Issue has no handoff comment but has a project | Offer to resume the project instead |
| Issue has no handoff comment and no project | Reconstruct from the ticket; say you're doing so |
