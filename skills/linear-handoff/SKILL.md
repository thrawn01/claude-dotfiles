---
name: linear-handoff
description: "Record the dated state of in-flight work in Linear — not a checked-in file — so the
  next session resumes from Linear. The handoff goes in whichever container spans the work: a Linear
  PROJECT (a coordinated multi-ticket build) gets a status update; an ISSUE (an epic, or a single
  long-running ticket) gets a `## Handoff` comment. Use when you finish or pause work that will be
  resumed later, or when the user says 'post a status update', 'record where the build is', 'hand
  off the build', 'write a handoff', 'update the project status'. This is the redirect target from
  the generic /handoff skill for Linear-tracked work. Do NOT use for work not tracked in Linear at
  all (use /handoff to write a file), or for design rationale (use /decisions-capture or
  /adr-write)."
argument-hint: "[project-name | epic-or-ticket-id]"
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion]
---

# Hand off in-flight work via Linear

Capture *where the work is and what to do next* in Linear, so that — not a checked-in handoff file —
is the durable resume point. Handoffs are timestamped and append-only: the newest is the next
session's starting line, the history is the phase trail. A repo `docs/**/handoff.md` (or a
service-level `CLAUDE.md`) carries only durable pointers (required reading, invariant policy,
where-things-live), never dated "current state / what's next" prose — that prose is the stale
anti-pattern this workflow replaces.

This is the **write** counterpart to `/linear-resume` (which reads the handoff back).

## The container model (project vs. issue)

A handoff lives in whichever Linear container spans the work — and Linear gives exactly two places:

| The work is… | Handoff goes in | Written with |
|---|---|---|
| a **project** — a coordinated, multi-ticket build | a **status update** on the project | `save_status_update` `type:"project"` |
| an **issue** — an **epic/parent**, *or* one **long-running ticket** | a **`## Handoff` comment** on the issue | `save_comment` |

Epic-vs-standalone makes no difference to the mechanism — both are issues, both take a comment. The
only question is *project or issue?* Resolve that in §1, then everything branches on it.

A handoff comment is identified by convention so `/linear-resume` can find it among ordinary
discussion: **its body begins with a `## Handoff` heading.** Always write that heading.

## Prerequisites

- Linear MCP connected (the `mcp__claude_ai_Linear__*` tools). If absent, stop and tell the user
  this skill needs Linear — offer `/handoff` (file-based) instead.
- The work is tracked in Linear (a project or an issue). If it is a one-off not tracked in Linear at
  all, this is the wrong skill — fall back to `/handoff`.

Reuse the shared precondition + id-resolution rules in `~/.claude/skills/shared/linear-workflow.md`
(§0 "is Linear in use here?", §1 "resolve the id"); this skill does not re-derive them.

## 1. Resolve the container

Find what to attach the handoff to, and decide **project or issue**. Resolve in order; stop at the
first hit:

1. **Supplied** — the user named a project, or gave a ticket/epic id or URL.
   - A **project name** → project handoff (§ status update).
   - A **ticket/epic id or URL** → `get_issue` it. Then decide (below).
2. **Current branch** — `git rev-parse --abbrev-ref HEAD` matches Linear's branch shape
   (`<user>/<team>-<num>-<slug>`) → extract `<TEAM>-<NUM>`, `get_issue` it, decide (below).
3. **Recent work** — the ticket touched this session (from the conversation) → `get_issue` it,
   decide (below).

**Deciding project vs. issue when you have an issue:** ask what the dated state is *about*.

- It's about a **coordinated build that spans many tickets** and the issue carries a `project` →
  attach the handoff to that **project** (status update). This is the common case for a sliced
  feature: the per-ticket work merged, but "where the build is + what's next" is a project-level
  fact.
- It's about **this one issue's own multi-session progress** (a long-running ticket, or an epic you
  track at the epic level) → attach a **`## Handoff` comment** to that **issue**.

When ambiguous — the issue has a project *and* you could reasonably mean either — ask the user which
they're handing off: the **build** (→ project status update) or **this ticket** (→ ticket comment).
Never guess silently; the resume point depends on it.

## 2. Read the latest existing handoff first (continuity)

Before composing, fetch the newest prior handoff for the chosen container so yours continues the
trail rather than repeating it:

- **Project** → `get_status_updates` with `type:"project"`, the project name, `orderBy:"createdAt"`,
  `limit:1` (or a few).
- **Issue** → `list_comments` for the issue, newest first; the most recent comment beginning with
  `## Handoff`.

Read it: it tells you what the *last* resume point was, so your handoff is the **diff** — what
changed since, what merged, what's now next. If there is no prior handoff, this is the first; say so.

## 3. Compose the handoff

A good handoff is a resume-from-here brief. Cover these, in order (omit one only when it truly
doesn't apply):

1. **Where the work is + what just merged** — the slice/ticket completed, its PR number + merge
   SHA, the conformance/test state. Concrete, with ids.
2. **Work in flight, if you're pausing (not finishing)** — for any *open* PR: number, branch, head
   SHA, current CI/review state, and **unresolved review threads with their disposition**
   (Fix-pending / Disagree + one-line rationale / Cannot-determine), and what it's ready for
   (merge / human review / more fixes / rebase). Skip this whole item on a clean merge.
3. **Open loose ends** — anything deferred, skipped, or left red on purpose (with the tracking
   handle — a skipped test name, a follow-up ticket), and any unresolved decision.
4. **The reasoned next task** — *the* most important part. Choose it by **readiness + closing a
   known gap**, NOT by incrementing the slice number. Say why it is next (what it unblocks / what
   gap it closes), so the next session doesn't re-derive the sequencing.
5. **Pointers** — the file paths, docs/reports, scripts, slash commands, and the verify command the
   next session needs to pick up (e.g. the feature dir, the test command and any scoping caveat).

Keep it factual and short — bullets over paragraphs, SHAs/URLs/ticket-ids inline. Omit rationale
for *past* choices (that belongs in ADRs / `decisions-capture`); this is about state and next step.

**Never assert state you did not verify.** "Merged / green / these tests pass" must reflect what you
actually observed this session, not what you assume. If a CI run is still going or may have flaked,
if a merge is unconfirmed, or any fact is uncertain — say so explicitly rather than guessing. The
next session resumes on these claims; a wrong "green" is worse than an honest "unverified".

Pick **health**: `onTrack` (normal progress), `atRisk` (a loose end or unknown threatens the next
step), `offTrack` (blocked / a regression). Default `onTrack` unless a loose end says otherwise. For
a **project** handoff this is the status update's `health` field. A **comment** has no health field,
so record it as a `**Health:** <…>` line in the body instead.

### Template

For an **issue comment**, start with the `## Handoff` heading; a **project status update** carries
its own title in Linear, so the heading is optional there.

```markdown
## Handoff · <UTC date>        ← required for issue comments; sets the marker

**Merged:** <TEAM>-<NUM> <title> — #<PR> (`<sha>`). <one line on what shipped + test state>.

**In flight (if pausing):** #<PR> `<branch>` (`<sha>`) — CI <state>; threads: <disposition>;
ready for <…>.

**Open:** <deferred/skipped items with their tracking handle; "none" if clean>

**Next:** <TEAM>-<NUM or "TBD"> — <task>. Chosen because <readiness / gap it closes>.

**Pointers:** <feature dir / reports / verify command + caveats>.

**Health:** <onTrack | atRisk | offTrack>   ← comment only; projects use the status-update field
```

## 4. Post

The instruction to write the handoff is the go-ahead — post directly. Do **not** display the body
for approval or wait for a nod first.

- **Project** → `save_status_update` with `type:"project"`, `project:"<name>"`, `health:"<…>"`,
  `body:"<…>"`. Omit `id` to create a new one — always create; never overwrite a prior update, the
  history is the trail.
- **Issue** → `save_comment` with the issue id and `body:"<…>"`, where the body **begins with
  `## Handoff`**. Always a new comment — never edit a prior handoff comment; the trail is the
  history.

After posting, give the user the link (project Updates URL, or the issue/comment URL) and a one-line
summary of what you posted, so they can review or edit it if they want.

## 5. Keep the repo handoff pointer durable-only

If the repo has a `docs/**/handoff.md` or a service-level `CLAUDE.md` carrying resume pointers,
verify it still holds **only** durable pointers. If you (or a prior `/handoff` run) left dated
"current state / what's next" prose in it — or in a gitignored `plans/handoff-*.md` — that state now
lives in the Linear handoff; trim the file back to pointers and tell the user the dated content
moved to Linear. Do not leave two competing sources of "where we are."

## Boundaries

- DO NOT write the dated state into a checked-in file. It goes in the Linear handoff (project status
  update, or `## Handoff` comment on the issue).
- DO NOT put a project-spanning build's state in a single ticket's comment, or one ticket's progress
  in a project status update — match the handoff to the container that spans the work (§1).
- DO NOT capture design rationale here (use `decisions-capture` / `adr-write`).
- DO NOT ask the user to make follow-up/ticket decisions during the handoff — record each follow-up
  in the handoff with enough detail (behavior, fix shape, tracking handle) and defer the decision.
- DO NOT include Co-Authored-By or Claude attribution in the handoff body.

## Early exits

| Condition | Action |
|---|---|
| No Linear MCP available | Stop — offer `/handoff` (file-based) instead |
| Work isn't tracked in Linear at all | Wrong skill — fall back to `/handoff`, say why |
| Issue handed off but you meant the build (or vice-versa) is unclear | Ask: the build (→ project) or this ticket (→ comment)? |
| Issue has a project but you're handing off the build, and the project link is missing | Surface it; offer to post a ticket comment or to link the project — don't guess |
| No prior handoff for this container | Fine — this is the first; note it and proceed |
