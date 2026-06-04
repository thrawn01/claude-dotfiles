---
name: standup-to-linear
description: "Post each line item of a standup report as a comment on its Linear ticket. Reads the human-editable standup markdown report (produced by /standup), parses every ticket section, and posts the summary + stats as a comment on the matching Linear issue. Use when the user says 'post my standup to linear', 'update the tickets from my standup', 'comment my standup on linear', or '/standup-to-linear'."
argument-hint: "[path to standup-<date>.md — defaults to today's report]"
allowed-tools: Bash, Read, mcp__claude_ai_Linear__save_comment
disable-model-invocation: false
user-invocable: true
---

# /standup-to-linear

Post each ticket line item from a standup report as a comment on its Linear issue.

The **standup report markdown is the contract and the review gate.** The user edits
`~/Notes/<YYYY-MM>/standup-<date>.md` first — reword a summary, or DELETE any `##` section
they don't want posted — and those edits are the approval step. That is why there is **no
dry-run and no confirmation prompt**: by the time this runs, the file already reflects
exactly what should be posted. Post directly.

`/home/user/.claude/skills/standup-to-linear` is this skill's directory. Fallback:
`~/.claude/skills/standup-to-linear`.

## 1. Resolve the report path

`` is the report path if the user gave one. Otherwise default to **today's**
report, falling back to the most recent one:

Set `REPORT` to the path in `` if the user provided one; otherwise leave it empty
and let the fallback pick today's (then most recent) report.

```bash
SK="${CLAUDE_SKILL_DIR:-$HOME/.claude/skills/standup-to-linear}"
REPORT=""   # set to the `` path if one was given
if [ -z "$REPORT" ]; then
  TODAY="$HOME/Notes/$(date -u +%Y-%m)/standup-$(date -u +%Y-%m-%d).md"
  if [ -f "$TODAY" ]; then
    REPORT="$TODAY"
  else
    REPORT="$(ls -t "$HOME"/Notes/*/standup-*.md 2>/dev/null | head -1)"
  fi
fi
[ -f "$REPORT" ] || { echo "no standup report found (run /standup first)"; exit 1; }
echo "report: $REPORT"
```

## 2. Parse the report into comment payloads

The Python parser does no network I/O — it only turns the (possibly edited) markdown into
`{domId, status, title, body}` objects. Every `##` ticket section with a Linear id and at
least one bullet becomes one payload; `## Other PRs` / `## Meetings / Notes` and any deleted
section are dropped.

```bash
python3 "$SK/parse_report.py" "$REPORT" > /tmp/standup-linear.json
python3 -c "import json;d=json.load(open('/tmp/standup-linear.json'));print(len(d['comments']),'comments for',d['date'])"
```

Read `/tmp/standup-linear.json`. It is small and structured — read it directly (do NOT
re-parse the markdown yourself).

## 3. Post one comment per ticket — directly, via the Linear MCP

For **each** object in `comments`, call `save_comment` with the ticket identifier as
`issueId` and the prebuilt markdown `body` verbatim:

- `mcp__claude_ai_Linear__save_comment({ issueId: <domId>, body: <body> })`

Notes:
- `issueId` accepts the identifier form directly (e.g. `"DOM-1546"`) — no `get_issue`
  lookup is needed.
- Pass `body` exactly as parsed (literal newlines, no escaping). It already carries the
  `**Standup · <date>**` header and obeys the report's no-dash convention.
- **Append always:** create a new comment every run. There is no dedup, so re-running on an
  overlapping window will post again — the `**Standup · <date>**` header keeps comments
  self-labeling on the ticket timeline. (Standup advances `.standup-last-run`, so normal
  consecutive runs cover non-overlapping windows.)
- If a `save_comment` call fails (unknown id, no access), report that ticket as failed and
  continue with the rest — never abort the whole batch.

## 4. Report back

Print a one-line summary: `<N> comments posted (<M> failed) for <date>`, then list the
ticket ids posted (and any that failed, with the reason).

---

## Notes for the implementer

- **No markdown re-parsing by the model.** `parse_report.py` is the only reader of the
  report; the model consumes its JSON. Mirrors how `/standup` keeps log-parsing in its Go
  extractor.
- **Scope = whatever is in the (edited) report.** The parser posts every ticket section
  present, including "standing PR, no movement" sections that `/standup` still emits. To
  post only active tickets, delete the unwanted sections in the report before running — the
  edit is the filter.
- **Idempotency:** none by design (append-always). If duplicate comments become a problem,
  the cheapest guard is to tag the body with a stable marker and scan `list_comments` before
  posting; not implemented deliberately.
