---
name: review-status
description: "One-shot status pass over every PR review-captain is tracking in its privileged-reviews channel — nudges idle workers to re-fetch their PR's current GitHub state, then reports what's waiting on the operator, unassigned, or updated via Slack since the last tick. Read-only against the ledger; never launches a worker or writes state, that stays review-captain's job."
---

# Review status — ad hoc report on in-flight reviews

You give the operator a snapshot of every PR under `/review-captain`'s watch, on demand, instead of
making them wait for the hourly tick. You **read, nudge, and report** — you never write the ledger,
launch a worker, approve, or merge.

## Why this exists

A worker that posted findings and is now watching a PR for resolution has no way to subscribe to
GitHub notifications. It only re-checks the PR when something wakes it: its own
`pr-feedback-watch.sh` polling loop, an idle notice, or a nudge. If that loop dies, or the event
that should have triggered it never fires, the worker sits there believing stale state — "still
waiting on the author" — long after the author pushed a fix or someone else approved. The nudge
step forces every idle worker to look again, the way a human would just glance at the PR.

## Preconditions

- review-captain's ledger at `~/captain-notes/privileged-reviews.json` exists. If it doesn't,
  review-captain hasn't ticked yet — say so and stop; there's nothing to report on.
- `gh`, `herdr`, and the Slack read tool are reachable. Degrade per-section (§5) rather than
  stopping entirely if one is down.
- Runs from anywhere. A `[captain]`-prefixed pane injection carries its own authority regardless
  of which session sends it, so this doesn't need to run inside the review captain's session
  itself — though that's the common case, since the operator will usually type it there.

## 1. Load the ledger (read-only)

Read `~/captain-notes/privileged-reviews.json`. **Never write to it** — review-captain is the
ledger's single writer, and a second writer racing its hourly tick is how entries get lost. Note
`last_seen_ts` and every ask's `state` and `worker`.

## 2. Catch anything since the last tick

`slack_read_channel` on the ledger's `channel_id`, `oldest` = ledger's `last_seen_ts`. For each message not
already in the ledger:

- A PR URL with no matching ledger entry → **no worker assigned** bucket. Don't add it to the
  ledger and don't launch it — that's review-captain's next tick, within the hour, or the operator's
  explicit go.
- A reply on an existing ask's thread → `slack_read_thread` it for anything that changes the
  picture (author says fixed/closed, someone approved in-channel, a new blocker) → **Slack
  updated** bucket, one line, only when it's new information GitHub doesn't already show.

## 3. Re-poll GitHub for every non-settled entry

Non-settled = ledger state in `new`, `launched`, `reviewing`, `findings-posted`,
`awaiting-resolution`, `ready-to-approve`, `disputed`, or `halted:*`. Skip `merged` / `closed` /
`approved` — they're done, and re-verifying them on every ad hoc call defeats the point of an
index-first read.

```bash
gh pr view <n> --repo <org>/<repo> --json state,isDraft,mergedAt,headRefOid,reviewDecision,reviews,statusCheckRollup,url,title,author
```

Fall back to REST (`gh api repos/.../pulls/<n>`, `.../pulls/<n>/reviews`,
`.../commits/<sha>/check-runs`) on a GraphQL rate limit — same as review-captain's own step 2 —
and never read that as a red build. Classify the same way: merged, closed, human-approved-at-head,
draft, or genuinely open and unresolved. A `new` entry that's open, not draft, and unapproved is
**no worker assigned** too — it means the tick hasn't reached it yet, not that anything's broken.

## 4. Nudge idle workers only

For each non-settled entry with a worker on record, find its pane (`ListAgents`, or
`herdr agent list` matching the ticket id). Check liveness by reading the pane's tail
(`herdr agent read <pane> --source visible --lines 30`): if it shows an active tool call or
mid-generation output, **leave it alone** — injecting into a busy worker interrupts real work for
no gain. If it's sitting at rest:

```
herdr agent prompt <pane> "[captain] status check — re-read PR #<n>'s current state on GitHub right now (gh pr view, checks, reviews, comments) as if you're looking at it fresh, even if you think nothing changed, and re-run your risk classification against the current head. Then SendMessage your captain (your launch's first argument) a normal ## Worker report with your Stage and Risk."
```

Record which panes got nudged this pass so the operator knows which workers might report back in the
next few minutes. That reply goes to the worker's captain (its launch's first argument), not to
this ad hoc run — and if it changes the PR's ledger state, review-captain's own step 4/6 rule fires
a full table in the captain's pane the moment it lands, unprompted. A nudge from here can produce
an update the operator sees over there rather than in this report.

## 5. Compile the report

Print directly — don't `SendMessage` yourself, don't write the ledger. The report is one table,
needs-your-call rows first:

```
| PR    | status            | risk   | worker says                                                      | why                                                 |
|-------|-------------------|--------|------------------------------------------------------------------|-----------------------------------------------------|
| #4333 | needs your call   | high   | no objection — flags the tradeoff as yours, not a recommendation | rewrites the money-path merge gate                  |
| #4350 | waiting on author | medium | holds a blocking finding                                         | cards.md:35 still names a trigger this diff retires |
| #4310 | no worker yet     | —      | —                                                                | asked 09:14, next tick picks it up                  |
```

`status` uses only these fixed values — never internal ledger vocabulary like `ready-to-approve`
or `findings-posted`, which nobody reading the table should have to know:

- **needs your call** — high risk, or medium with a judgment call or dispute open. The only rows
  that ask the operator anything.
- **waiting on author** — findings posted, not yet resolved at the current head.
- **reviewing** — a worker is on it, nothing posted yet.
- **stuck** — halted and unanswered; `why` carries the halt type and the one unblocking action.
- **no worker yet** — no ledger entry or state `new`; `why` says when it was asked.

Settled PRs (merged / approved / closed) get no row at all unless something about them changed
since the last tick. **`worker says` is mandatory on every row that has a worker**, even one word
("clean", "no objection") — an unlabeled blank is how a bare "approve #4333?" once read as a
recommendation instead of a relay. `risk` is the worker's own tier. `why` is one line of
substance: the top finding, what makes it high-risk, or the halt. A slot with nothing pending
gets `—`, never prose.

Below the table, one line each, only when non-empty — `Nudged: #4236, #4260 (were idle)` and
`Slack: #4245 author says fix pushed, worker not yet re-verified`. If a section degraded (Slack
or `gh` unreachable), say so above the table instead of silently omitting it.

## Guardrails

- **Never launches a worker.** An unassigned PR is reported, not dispatched — that's
  review-captain's tick or the operator's explicit go.
- **Never writes the ledger.** review-captain is the single writer; this skill only reads it and
  reads GitHub/Slack fresh.
- **Never nudges a busy pane.** Idle only — a worker mid-review doesn't need a status ping.
- **Never approves, merges, or injects an approval.** A nudge asks a worker to re-check state,
  nothing more; `[captain] approve <sha>` stays review-captain's own action after the operator's yes.
- **Skip settled entries.** `merged` / `closed` / `approved` ledger states don't get re-polled —
  the report is for what's still moving.
