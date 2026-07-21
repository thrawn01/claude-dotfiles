---
name: linear-start
description: "Pick up a Linear ticket and start working it. Fetch the ticket, verify the current
  branch matches Linear's own git branch name (the worktree is created before the session, e.g. by
  a claude-branch-style wrapper), then classify the ticket (bug / improvement / feature) from its
  Linear labels — falling back to its content when unlabeled. Bugs and trivial improvements start
  immediately; features with enough detail hand off to /blueprint-create. Use when the user says
  'pick up <TEAM>-<NUM>', 'work this ticket', 'start <ticket>', 'start working ENG-42',
  '/linear-start', or gives a Linear id/URL and asks to begin. This is greenfield only — to
  *resume* an in-flight build or long-running ticket from its latest handoff, use /linear-resume
  first. Do NOT use to merely create a ticket or to open a PR — those belong to the
  ticket-creation and PR skills."
argument-hint: "<linear-id-or-url>"
allowed-tools: [Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion, Skill]
---

# Start a Linear ticket

Take a Linear ticket from "assigned" to "actively being worked" — fetch it, verify the session is
on Linear's own branch name, decide what kind of work it is, and either start coding (bug /
trivial improvement) or kick off design (feature). The worktree is created before the session
starts (e.g. `claude-branch <gitBranchName>` or an equivalent wrapper) and this skill runs inside
it. This is the front-door skill that precedes implementation; it does not write code itself
beyond a straightforward bug/improvement fix.

## Prerequisites

- Linear MCP connected (the `mcp__claude_ai_Linear__*` tools). If absent, stop and tell the user
  this skill needs Linear.
- A git repository with remote `origin`.
- The session runs inside the worktree/checkout where the work will happen — typically created
  from the ticket's branch name before the session (e.g. `claude-branch <branch>`).

## 1. Resolve the Linear id

Resolve in order; stop at the first that yields an id:

1. **Supplied** — the user gave an id (`ENG-69`) or a Linear URL → use it.
2. **Current branch** — `git rev-parse --abbrev-ref HEAD` matches Linear's branch shape
   (`<user>/<team>-<num>-<slug>` or `ticket/<team>-<num>-<slug>`) → extract `<TEAM>-<NUM>`.

If neither yields an id, ask the user which ticket to start. Never guess.

## 2. Fetch the ticket

Call `mcp__claude_ai_Linear__get_issue` with the resolved id. This is the key step — its result
carries everything the rest of the skill needs:

- **`gitBranchName`** — Linear's own auto-generated branch name (e.g.
  `thrawn01/eng-69-slip-stream-design-baseline`). **This is the branch the work must happen on** —
  verify the current branch against it in §4. Never synthesize a `ticket/...` or `fix/...` name —
  matching what Linear shows on the ticket is what makes the PR auto-link.
- **labels** — drive the bug/improvement/feature classification (§5).
- **title + description** — used for classification fallback and, later, as context for the fix or
  for `/blueprint-create`.
- **state / assignee** — used in §3.

If `get_issue` reports the issue does not exist, stop and tell the user — do not fall through to
creating one (that's the ticket-creation skill's job, not this skill's).

If the ticket is already in a terminal state (Done / Canceled), surface that and ask whether to
continue before doing anything.

**This skill is greenfield only — starting a ticket, not resuming one.** It does not read prior
handoff state. If you are *continuing* an in-flight build or a long-running ticket, that's
`/linear-resume` (read the latest handoff → learn the reasoned next step), which then sends you here
only to set up the workspace. Run `/linear-resume <project-or-ticket>` first when resuming; use this
skill to begin a ticket whose next-step is already decided.

## 3. Advance the ticket status

Advancing the status is the whole point of starting a ticket — do it without asking. Follow the
shared advance-never-regress rules (`~/.claude/skills/shared/linear-workflow.md` §3):

- **Status:** if the current status type is `backlog` or `unstarted` (Backlog / Todo), set
  **In Progress**. If already `started`/`completed`, leave it.
- **Assignee:** if unassigned, set `me`. If assigned to someone else, leave it — never steal an
  assignee; this is the one case where you stop and ask before proceeding.

Use `mcp__claude_ai_Linear__save_issue` to apply the change. Report what you changed in the §Completion
handoff rather than asking for a nod first.

## 4. Verify the workspace

Verify the session is on the ticket's branch:

```bash
git rev-parse --abbrev-ref HEAD
```

- **Current branch matches `gitBranchName`** → proceed.
- **Mismatch** (still on `main`/`master`, or another ticket's branch) → stop and tell the user the
  expected branch: "This session isn't on the ticket's branch. Run `claude-branch <gitBranchName>`
  (or your worktree wrapper) and invoke `/linear-start` from that session."

**Freshness check (automatic):** a wrapper may have created the branch off a stale local HEAD.
After `git fetch origin`, if the branch has **no commits of its own** and is behind the default
branch (`git rev-list --count HEAD..origin/<main>` > 0), move it onto `origin/<main>`
(`git reset --hard origin/<main>`) without asking — always start on current main. Skip silently if
it's already current. If the branch **has commits of its own** and is behind, don't reset (that
would lose work) — surface it and ask.

## 5. Classify the work

Decide whether this is a **bug**, an **improvement**, or a **feature**. Labels first; content only
when labels don't settle it.

### 5a. From Linear labels (preferred)

Read the ticket's labels (already in the §2 result; use `list_issue_labels` only if you need to
inspect the team's label set). Map them:

- **bug** ← labels like `bug`, `fix`, `defect`, `regression`, `crash`, `error`
- **feature** ← labels like `feature`, `feat`, `new`, `epic`
- **improvement** ← labels like `improvement`, `enhancement`, `chore`, `refactor`, `tech-debt`,
  `cleanup`

If exactly one category matches, use it.

### 5b. From content (fallback when labels are absent or ambiguous)

When there are no type labels — or they conflict — infer from the title and description:

- **bug** — describes something broken: "fix", "broken", "fails", "crash", "incorrect", "doesn't
  work", "regression", a stack trace, or expected-vs-actual framing.
- **feature** — proposes something new and non-trivial: "add", "implement", "introduce", "support
  X", "new endpoint/page/capability", multiple acceptance criteria, design-level open questions.
- **improvement** — a bounded change to existing behavior: "tweak", "rename", "refactor",
  "clean up", "speed up", "bump", "adjust", a one-or-two-file change with an obvious shape.

If after both passes the category is genuinely unclear, ask the user (bug / improvement / feature)
rather than guessing — the routing in §6 depends on it.

## 6. Route

### Bug → start immediately

Begin work in the worktree now. Reproduce, then fix. If TDD rigor is warranted, write a failing
surface test first (see the `surface-testing` skill), then implement.
Keep the orchestration light — for a clear bug you do not need a design phase. Report the root
cause and the fix as you go.

### Trivial improvement → start immediately

If the improvement is small and the shape is obvious (a rename, a bounded refactor, a config bump,
a one-or-two-file change), just do it in the worktree. No blueprint.

If the "improvement" turns out to be larger than it looked once you open the code — touching many
packages, needing interface decisions, or carrying real ambiguity — treat it as a feature and fall
to the feature path instead.

### Feature → design first

A feature needs design before code. Decide whether the ticket carries **enough information to
start designing**:

- **Enough** = there is a clear problem statement and a sense of the desired outcome —
  `/blueprint-create` can run a productive design discussion from it.
- **Not enough** = the ticket is a one-liner or a vague idea with no outcome, constraints, or
  acceptance criteria.

**If enough information:** invoke `/blueprint-create`, passing the ticket id, title, and full
description as the starting context so the blueprint is written under
`docs/features/<TEAM>-<NUM>-<slug>/`.

```
Skill(skill: "blueprint-create")
```

**If not enough information:** do not start. Tell the user specifically what's missing (problem
statement? desired outcome? constraints? acceptance criteria?) and offer to either (a) ask the
ticket author for detail via a Linear comment, or (b) work through it together now and then run
`/blueprint-create`.

## Completion / handoff

After routing, leave a clear status:

```
## Started <TEAM>-<NUM> — <title>

**Type:** <bug | improvement | feature>
**Branch:** <gitBranchName> (verified current)
**Linear:** <status set to In Progress? assignee?>

**Next:** <"fixing now" | "implementing now" | "running /blueprint-create" | "blocked — need X from the author">
```

### Recording dated state when you finish or pause

When you finish or pause work that will be resumed later, the dated handoff goes in Linear, not a
checked-in file. Run **`/linear-handoff`** — it owns that procedure end to end and attaches the
handoff to the right container (a **project status update** for a multi-ticket build, or a
**`## Handoff` comment** on the epic/ticket for single-issue work), keeping any repo
`docs/**/handoff.md` to durable pointers only.

## Early exits

| Condition | Action |
|---|---|
| No Linear MCP available | Stop — this skill requires Linear |
| Id can't be resolved | Ask the user which ticket |
| `get_issue` says the id doesn't exist | Stop and report — do not create one |
| Ticket is Done / Canceled | Surface it, ask before continuing |
| Assigned to someone else | Note it, ask before taking it over |
| Current branch doesn't match the ticket's `gitBranchName` | Stop — point the user at their worktree wrapper (`claude-branch <gitBranchName>`) |
| Feature with insufficient detail | Don't start — report what's missing, offer to gather it |
| Category genuinely unclear after labels + content | Ask the user (bug / improvement / feature) |
