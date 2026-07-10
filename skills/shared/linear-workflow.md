# Linear Workflow — shared procedure

Canonical procedure for the Linear-id-driven feature workflow, shared by
`blueprint-create`, `linear-start`, `linear-handoff`, and the ticket-creation
and PR skills. Behavior lives here; skills reference this file instead of
copying it.

Human-facing contract (when present in the target repo): `CONTRIBUTING.md` at the
repo root, and `docs/features/ENG-1-linear-workflow/board-report-system-spec.md`
in the mono-repo.

## When to run

At the point a skill needs to name the feature directory (`blueprint-create`:
when locating or creating the feature dir). First check the
section 0 precondition — if Linear isn't in use here, take the plain-slug fallback
and skip the rest. Otherwise **resolve the Linear id FIRST** — the directory and
branch are named from it.

## 0. Precondition — is Linear in use here?

This procedure is opt-in. **Skip it entirely** when any of these hold:

- No Linear MCP is connected/available in this environment.
- The user says they don't track this work in Linear (or asks to skip the ticket).
- The target repo shows no sign of the workflow — no `ticket/<TEAM>-<NUM>-<slug>`
  branches, no `<TEAM>-<NUM>-<slug>` feature dirs, and no `CONTRIBUTING.md`
  describing it.

When skipping: name the feature directory `docs/features/<slug>/` (plain inferred
slug, no id) and the branch `no-ticket/<slug>`, tell the user you skipped Linear
and why, and continue. Never block the calling skill on creating an issue, and
never fail because the MCP is absent. `{feature}` then denotes the plain `<slug>`.

Otherwise (Linear is available and used here), resolve the id below.

## 1. Resolve the Linear id (never create a duplicate)

Resolve in order; stop at the first that yields an id:

1. **Supplied** — the user gave an id (`ENG-42`) or a Linear URL. Use it.
2. **Branch** — the current branch matches `ticket/<TEAM>-<NUM>-<slug>`
   (`git rev-parse --abbrev-ref HEAD`). Extract `<TEAM>-<NUM>`.
3. **Feature dir** — an existing `docs/features/<TEAM>-<NUM>-<slug>/` already holds
   this feature's docs (the common case when revisiting a blueprint). Extract
   the id from the directory name.
4. **Create** — none of the above matched: create a new issue (section 2).

A supplied or derived id is **reused**. Verify it exists (`get_issue`); if it does
not, fall through to create.

## 2. Create a new issue (only when section 1 reached "create")

- **Team:** the sole team is auto-selected (today: `Engineering`, key `ENG`). Ask
  which team only if the workspace has more than one.
- **Title:** a plain description of the work — `<project> <what>`, nothing else.
  **Hard test:** if it contains `(`, `)`, `—`, a separator `-`, `:`, `+`, or `/`,
  it is WRONG — that punctuation smuggles in a second idea or metadata (lineage,
  `slice N`/`phase N`, ids). Cut to one plain phrase; the project name's own hyphen
  (`git-server`) is fine. **Description:** one or two lines of intent (lineage and
  schedule context go here, never the title) — the PRD/spec carries the detail.
- **assignee:** `me` — per-developer MCP auth resolves to the acting developer.
- **state:** `In Progress` — creating the ticket *is* the act of starting work.
- **labels:** the repo label (section 4).

## 3. Reuse an existing issue (supplied or derived id)

- Do **not** create a new issue.
- **Status — advance, never regress:** if the current status type is `backlog` or
  `unstarted` (Backlog/Todo), set `In Progress`. If already `started` or
  `completed` (In Progress/In Review/Done) or canceled, leave it.
- **Assignee:** if unassigned, set `me`; if assigned to someone else, leave it —
  never steal an assignee.
- **Label:** ensure the repo label (section 4) is present; add it if missing.

## 4. Repo label (codebase identity)

- Read `git remote get-url origin` and parse the trailing `<org>/<repo>` (strip a
  `.git` suffix and any `git@host:` or `https://host/` prefix).
- The Linear label is the **repo name only** (e.g. `mono-repo`), under the `repo`
  label group. The GitHub org is recorded in `docs/repos.md`, not in Linear.
- Look the repo up in the target repo's `docs/repos.md`:
  - **Present** → apply its `repo:` label.
  - **Absent** → add a row to `docs/repos.md` (`<repo>` → `<org>/<repo>`), create
    the Linear label (`create_issue_label` `name:<repo>` `parent:"repo"`), then
    apply it.
- **No git remote** (rare): skip the label and say so.

## 5. Feature directory

- Name it `docs/features/<TEAM>-<NUM>-<slug>/`. `<slug>` is the kebab feature slug
  the calling skill already infers.
- If a directory for this id already exists (any slug), **reuse it** — never create
  a second. If its slug differs from a freshly inferred one, keep the existing
  directory and note the difference: the id is the identity, not the slug.
- Throughout the calling skill, `{feature}` denotes this `<TEAM>-<NUM>-<slug>`.

## 6. Branch

- The branch mirrors the directory: `ticket/<TEAM>-<NUM>-<slug>`.
- Echo the exact command: `git checkout -b ticket/<TEAM>-<NUM>-<slug>`.
- If currently on a non-ticket base branch (e.g. `main`) and this is brand-new
  work, you may create it. Never rename or switch away from an existing
  `ticket/...` or `no-ticket/...` branch without asking.
- The shape-only `pre-push` hook (when installed) validates this at push — a
  backstop, not a dependency.

## Environment

- **Claude Code** (Read/Write/Edit present): the full procedure — git, the
  filesystem directory, and the Linear MCP — *when Linear is in use here* (§0). If
  the MCP is absent or Linear isn't used, take the §0 plain-slug fallback.
- **Claude chat** (no filesystem/git): skip the git, directory, branch, and
  remote-label steps. You may still create the Linear issue via MCP if the user
  supplies the repo; surface the intended `docs/features/<id>-<slug>/` path and
  `ticket/<id>-<slug>` branch for the user to create back in Claude Code.

## Safety

Never create a duplicate issue, never regress an issue's status, never steal an
assignee, never overwrite an existing feature directory or branch. When unsure
whether an id already exists, look it up before creating.
