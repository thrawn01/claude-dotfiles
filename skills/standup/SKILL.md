---
name: standup
description: "Reconstruct what you actually did over a time window from Claude session logs, GitHub, Linear, and daily notes; group it by Linear ticket; write a standup-ready markdown report to ~/Notes; and copy a Range.co-ready version to the clipboard. Use when the user says 'standup', '/standup', 'what did I do today', or 'write my standup'."
argument-hint: "[--since <YYYY-MM-DD or RFC3339>]"
allowed-tools: Bash, Read, Write, mcp__claude_ai_Linear__list_issues, mcp__claude_ai_Linear__get_issue, mcp__claude_ai_Linear__list_comments
disable-model-invocation: false
user-invocable: true
---

# /standup

A `collect → merge → narrate → deliver` pipeline keyed on the **git branch name**.
**Deterministic scripts read everything; you read almost nothing** — only the small
`buckets.json` of structured facts. Never open raw session logs; the Go extractor is their
only reader. The full data contract is in `CONTRACT.md` next to this file.

`${CLAUDE_SKILL_DIR}` is this skill's directory. Fallback: `~/.claude/skills/standup`.

## 0. Set up a run directory and build the extractor

```bash
SK="${CLAUDE_SKILL_DIR:-$HOME/.claude/skills/standup}"
RUN="$(mktemp -d)"
# Build the Go extractor on first use (hard dependency: Go toolchain).
( cd "$SK/extractor" && go build -o "$SK/standup-collect" ./cmd/standup-collect )
```

## 1. Resolve the window — compute `(since, now)` exactly ONCE

Compute both values a single time and pass that same pair to every collector and to the
report header (Correctness Invariant #2). `now` is the current time in RFC3339.

```bash
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LAST_RUN="$HOME/Notes/.standup-last-run"
# Priority: --since arg > .standup-last-run > 24h before now.
if [ -n "$SINCE_ARG" ]; then
  SINCE="$SINCE_ARG"                       # accept YYYY-MM-DD or full RFC3339
elif [ -f "$LAST_RUN" ]; then
  SINCE="$(cat "$LAST_RUN")"
else
  SINCE="$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)"
fi
# Normalize a bare date to start-of-day RFC3339.
case "$SINCE" in *T*) ;; *) SINCE="${SINCE}T00:00:00Z" ;; esac
echo "window: $SINCE .. $NOW"
```

`$SINCE_ARG` comes from `$ARGUMENTS` (strip a leading `--since`). If none, leave empty.

## 2. Collect (each emits structured JSON into `$RUN/`)

**Core sources — a failure here is a HARD ABORT** (Behavioral Constraint 3): do not write
`.standup-last-run`, so a later run re-captures this window.

```bash
# Sessions: the Go extractor is the ONLY reader of raw .jsonl logs.
"$SK/standup-collect" sessions --since "$SINCE" --now "$NOW" > "$RUN/sessions.json"

# GitHub + local commits: the Go collector fans out `gh` and per-worktree `git log`
# concurrently. PRs/commits are windowed and attributed to you; a gh failure is a
# HARD ABORT. (Pass --no-local to skip the worktree scan.)
"$SK/standup-collect" github --since "$SINCE" --now "$NOW" > "$RUN/github.json"
```

**Enrichment sources — degrade to a warning, never abort** (Behavioral Constraint 3):

- **Linear** (soft). Discover via the Linear MCP `list_issues(assignee="me", updatedAt>=since)`;
  for each discovered issue, enrich title/status (and `get_issue`/`list_comments` as needed).
  Normalize to `CONTRACT.md §3` and write `$RUN/linear.json`:
  `{ "issues": [ {domId,title,status,url,updatedAt} ] }`. If Linear is unreachable or auth
  fails, print a warning and write `{ "issues": [] }` and continue.
- **Notes** (soft). Read dated files under `~/Notes` within the window
  (`~/Notes/<YYYY-MM>/<YYYY-MM-DD>.md`). Write `$RUN/notes.json` =
  `{ "notes": [ {date,text} ] }`; empty array if none (silent).

```bash
# If you could not produce a Linear/notes file, fall back so merge still runs:
[ -f "$RUN/linear.json" ] || echo '{"issues":[]}' > "$RUN/linear.json"
[ -f "$RUN/notes.json" ]  || echo '{"notes":[]}'  > "$RUN/notes.json"
```

## 3. Merge → `buckets.json`

```bash
python3 "$SK/scripts/merge.py" \
  --sessions "$RUN/sessions.json" --github "$RUN/github.json" \
  --linear "$RUN/linear.json" --notes "$RUN/notes.json" \
  --since "$SINCE" --now "$NOW" > "$RUN/buckets.json"
```

`merge.py` unions on `branch → DOM-id`, routes orphan PRs to `otherPRs` and orphan notes to
`notes`, attaches CI sub-bullets, and orders tickets by recent activity (CONTRACT §5).

## 4. Narrate — read ONLY `buckets.json`

Read `$RUN/buckets.json` (never raw logs). For each ticket bucket, and for the `otherPRs`
and `notes` groups, write **one** grounded, first-person, past-tense line that is derivable
**solely** from the facts in that bucket — never invent work (Behavioral Constraint 1). Add
each line as a `summary` field (and `otherPRsSummary` / `notesSummary` for the two groups),
changing nothing else, and write the result to `$RUN/narrated.json`.

## 5. Deliver — write report, set clipboard, THEN advance `.standup-last-run`

```bash
python3 "$SK/scripts/deliver.py" --narrated "$RUN/narrated.json" \
  --notes-dir "$HOME/Notes" --now "$NOW" --last-run "$LAST_RUN"
```

`deliver.py` builds the report via `format_report`, the clipboard text via `format_range`,
writes `~/Notes/<YYYY-MM>/standup-<YYYY-MM-DD>.md`, copies the Range text to the clipboard
(`wl-copy` → `xclip` → `xsel`; if none, it prints a copy-fence block), and **only then**
writes `$NOW` to `.standup-last-run` (Invariant #1). Re-running the same window overwrites
the same dated file (idempotent).

## 6. Report back

Print a one-line TL;DR (ticket / PR / note counts) + the report file path + the clipboard
status to the chat.

---

## Correctness notes (for the implementer / reviewer)

- **Window consistency (Inv #2):** `(SINCE, NOW)` is computed once in step 1 and threaded
  through every collector, `merge.py`, and the report header. Never recompute `now`.
- **Last-run advances only on success (Inv #1):** only `deliver.py` writes `.standup-last-run`,
  as its final step, after the report file exists. Any earlier error (including a core-source
  hard abort) leaves the timestamp untouched.
- **Never fabricate (Constraint 1):** narration consumes only `buckets.json`; facts are
  attached verbatim as sub-bullets by the formatters.
- **No raw logs to the model (Constraint 2):** only `standup-collect` reads `.jsonl`.
- **Local-only (Constraint 4):** the sole side effects are writing the report file and
  setting the local clipboard.
