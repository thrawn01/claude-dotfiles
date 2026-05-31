---
name: linear-create
description: The general "create a Linear ticket" skill. Use when the user says "create a linear ticket", "make a ticket for this", "track this in Linear", "log this to Linear", "send this to Linear", or when ad-hoc work (a question that became a small edit, a chore, a bug) needs a tracking issue but doesn't warrant a PRD or tech-spec. Works in both Claude Code (uses git — repo label, branch name) and claude.ai chat (Linear connector only, no repo). Reuses or creates the id (never duplicates), assigns it to you, sets status by intent (In Progress when working, Backlog when capturing), and labels the codebase. For a significant feature use prd-create/spec-create (which embed this logic); for a PR use open-pr; for a decisions document use decisions-capture.
---

# Create a Linear ticket

The general path for putting a unit of work into Linear when a full PRD/tech-spec is overkill. Two situations:

- **Work-first in a repo (Claude Code).** A question turned into a small edit, a chore, or a bug fix, and you want a ticket to track it. Mint the issue, label the codebase from the git remote, and get the `ticket/<id>-<slug>` branch.
- **Capture in chat (claude.ai, phone/web).** A conversation reached a decision or task that would otherwise leave no artifact. Capture it as a lazy issue so it isn't invisible to the report.

**Always preserve the *why*** — a title and a diff never recover the reasoning.

For a significant feature, use `prd-create` / `spec-create` instead — they run this same ticket logic while writing the docs. This skill is for work too small for that, or for pure capture.

## Environment

| | Claude Code (in a repo) | claude.ai chat |
|---|---|---|
| Tools | git + filesystem + Linear connector | Linear connector only |
| Id resolution | Follow `~/.claude/skills/shared/linear-workflow.md` | Inline rules below |
| Codebase label | From `git remote` via `docs/repos.md` | From existing `repo` labels in Linear |
| Branch | Echo `ticket/<id>-<slug>`; offer to create it | n/a |
| Feature dir | None for small work; a real feature belongs in prd-create/spec-create | n/a |

Detect the environment: if Read/Write/Edit and git are available you are in Claude Code; otherwise claude.ai chat.

## 1. Resolve the id — reuse or create (never duplicate)

In order, stop at the first that yields an id:

1. **Supplied** — the user gave an id (`ENG-42`) or a Linear URL → reuse it.
2. **Branch** (Claude Code) — the current branch is `ticket/<TEAM>-<NUM>-<slug>` → reuse that id.
3. **Create** — otherwise create a new issue.

This skill follows the shared procedure's id-resolution, label, and branch rules (`~/.claude/skills/shared/linear-workflow.md`) but **deliberately skips its feature-dir step** — small work gets no `docs/features/` directory. The shorter order above is that procedure minus the feature-dir resolution; if the work turns out to be a real feature, switch to `prd-create`/`spec-create`, which run the full version.

Reusing an existing id? Do not create a duplicate — add a comment or update it, and apply the status/label rules below without regressing anything.

## 2. Create the issue

- **Team:** the sole team is auto-selected (today `Engineering`/`ENG`); ask only if more than one.
- **Title:** short and specific. **Description (Markdown):** the *why* plus what's being done — a few lines; other fields optional.
- **assignee:** `me`.
- **Status — by intent:**
  - **In Progress** when the work is underway or about to start — the usual work-first-in-a-repo case ("I'm making this edit now"). Same rule as `prd-create`/`spec-create`: starting the work is what creates the ticket.
  - **Backlog** when this is a capture for later with no active work — the usual phone/chat case.
  - When it's genuinely unclear, ask which.
- Leave priority, estimate, and cycle unset unless the user asks.

## 3. Codebase label

- **Claude Code:** read `git remote get-url origin`, parse `<org>/<repo>`, and apply the repo-name label per `docs/repos.md` — creating the Linear label and adding a registry row if the repo is new. See the shared procedure.
- **chat:** list existing labels (`list_issue_labels`) and apply the matching `repo` label; ask if unsure, or leave it unlabeled. Do not invent a `repo` label here.

## 4. Branch (Claude Code only)

- Echo `git checkout -b ticket/<TEAM>-<NUM>-<slug>`. If on `main` or a `no-ticket/` branch and you just started this work, offer to create the branch and carry the changes onto it. Never rename or switch away from an existing `ticket/...` branch without asking. The `pre-push` hook validates the shape at push.
- **No feature directory for small work** — that is a deliberate judgment call (see `CONTRIBUTING.md`). If the work turns out to be a real feature, switch to `prd-create`/`spec-create`.

## 5. Confirm, then create

Creating (or commenting on) a Linear issue is an outward write — show the drafted title, description, and chosen label/assignee/status, get a nod, then create. Report the issue id and URL, and (Claude Code) the branch command.

## Multiple items

If the conversation produced several distinct tasks, offer one issue per item rather than one big issue. Default to a single issue for a single unit of work.
