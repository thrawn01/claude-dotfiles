# Standup Pipeline — Data Contract

This is the **locked interface** every component builds against. The pipeline is
`collect → merge → narrate → deliver`, joined on the **git branch name**, from which a
`DOM-id` is derived (`derrickwippler/dom-1608-...` → `DOM-1608`).

All intermediate artifacts are JSON. Timestamps are RFC3339 strings. The window
`(since, now)` is computed once and threaded everywhere.

---

## 1. Session extractor output — `standup-collect sessions --since T --now N`

Emits a JSON **array** of `SessionDigest`. One digest per in-scope, in-window session file.

```jsonc
SessionDigest {
  "branch":     string|null,    // gitBranch of the session, or null
  "domId":      string|null,    // "DOM-1608" derived from branch's dom-\d+ (case-insensitive), else null
  "firstTs":    string,         // RFC3339, earliest timestamped line
  "lastTs":     string,         // RFC3339, latest timestamped line
  "msgCount":   int,            // count of user+assistant message lines
  "humanTurns": string[],       // genuine human prompts (wrappers/reminders/hooks stripped); raw, untruncated
  "ciEvents":   [ { "pipeline": string, "failCount": int } ],  // failCount >= 1; zero-count events omitted
  "actions":    string[]        // detected actions: "git push", "gh pr create", "gh pr merge"
}
```

Rules (enforced by the extractor, covered by surface tests):
- **Attribution.** A session is in-scope iff its `cwd` OR `gitBranch` contains the owner
  substring (default `derrickwippler`, overridable with `--owner`). Out-of-scope sessions
  produce **no** digest.
- **Window.** A session is included iff `[firstTs,lastTs]` overlaps `[since,now]`.
- **No raw tool output** ever appears in any digest field.
- **CI heuristic** (per `tool_use_id` unit = one tool call's combined stdout+stderr):
  a CI event is emitted only when a **buildkite build URL**
  (`buildkite.com/<org>/<pipeline>/builds/<n>`) co-occurs in the same unit with a
  **failure-state signal** — one of: `"state":"failed"`, `"state":"blocked"`,
  `conclusion: failure` / `"conclusion":"failure"`, `❌`, or `build #<n> failed`.
  The bare word `FAIL`/`FAILED` in log text is **not** a signal. `pipeline` is the
  buildkite pipeline slug; `failCount` aggregates matching units per pipeline.

## 2. GitHub collector output — `standup-collect github`

(Commits come from two unioned, de-duplicated sources: each in-window PR's commits via
`gh`, and per-worktree `git log` so PR-less branches still surface. Both are windowed by
**author** date and attributed to the developer.)

```jsonc
{
  "prs": [ PR ],          // authored by @me, activity within window
  "commits": [ { "subject": string, "domId": string|null } ]  // in-window commits; domId from the branch
}
PR {
  "number": int,
  "url":    string,
  "title":  string,
  "branch": string,       // head branch
  "state":  string,       // "MERGED" | "OPEN" | "CLOSED"
  "domId":  string|null   // derived from branch, else null
}
```

## 3. Linear collector output (from MCP, normalized)

```jsonc
{
  "issues": [ {
    "domId":  string,     // "DOM-1597"
    "title":  string,
    "status": string,     // "In Review", "Done", ...
    "url":    string,
    "updatedAt": string   // RFC3339; used for in-window discovery
  } ]
}
```

## 4. Notes collector output

```jsonc
{ "notes": [ { "date": string, "text": string } ] }   // empty array if none
```

## 5. Merge output — `buckets.json` (produced by `merge(sessions, github, linear, notes, window)`)

`window` is the `{since, now}` dict computed once upstream and echoed into the output
(Invariant #2 — the same value reaches the report header).

```jsonc
{
  "window":   { "since": string, "now": string },
  "tickets":  [ Bucket ],   // ordered by lastActivity desc (most recent first)
  "otherPRs": [ PR ],       // PRs whose branch has no dom-id
  "notes":    [ { "date": string, "text": string } ]
}
Bucket {
  "domId":        string,         // never null in a ticket bucket (illegal state by construction)
  "title":        string,
  "status":       string|null,    // from Linear, else null
  "url":          string|null,    // Linear issue url, else null
  "prs":          [ PR ],
  "commits":      [ string ],
  "ciEvents":     [ { "pipeline": string, "failCount": int } ],
  "humanTurns":   string[],       // present ONLY when bucket has no PR and no commit; bounded (see below)
  "noPR":         bool,           // true when ticket has no PR (rendered "no PR")
  "lastActivity": string          // RFC3339, max across its sources
}
```

Merge rules (covered by surface tests):
- **Union on branch → domId.** Sessions, PRs, and Linear issues that share a `domId`
  merge into one ticket bucket.
- A PR whose branch has **no** dom-id routes to `otherPRs`, never a ticket bucket.
- A Linear issue assigned in-window with **no** branch/PR becomes its own bucket with
  `noPR: true`, `prs: []`.
- **Illegal state by construction:** a bucket is only ever created keyed by a `domId`;
  orphan PRs → `otherPRs`, orphan notes → `notes`. A ticket bucket with neither domId nor
  PR is not representable.
- **CI events** from matching-domId sessions attach to the bucket.
- **humanTurns** attach to a bucket **only when** it has no PR and no commit to describe it,
  bounded by named constants `MAX_TURNS` and `MAX_CHARS_PER_TURN` (truncation only shortens
  existing text — never invents).
- Ordering: tickets by `lastActivity` descending.

## 6. Narrated buckets

The model reads `buckets.json` and adds a `summary` string to each ticket bucket and to the
`otherPRs`/`notes` groups as needed. The summary is one grounded, first-person, past-tense
**arc line** — what was worked on, how it went, where it landed — at the altitude of spoken
standup, NOT a restatement of the commit log (see SKILL.md §4 for the voice + the
signal→tone heuristics that keep it derivable, never invented). The narrated object is
`buckets.json` with `summary` fields added; nothing else changes. The formatters consume
the narrated object.

## 7. Range clipboard format — `format_range(narrated) -> string`

The golden contract (from the blueprint). One group per ticket; bold ticket line with
inline Linear link + status in parens; then the narrated arc summary, an optional **single
collapsed stats line** (commit count + CI rounds, joined by ` · `), and the PR link(s) as
indented sub-bullets. Individual commit subjects are **never** enumerated; they inform the
summary only. `Other PRs` and `Meetings / Notes` are their own groups. Inline links use
markdown `[text](url)`. Example:

```
**[DOM-1608](https://linear.app/.../DOM-1608) · golangci-lint shards** (Done)
  - Got the lint shards green after a few rounds with CI.
  - CI: golangci-lint failed 3× before passing
  - PR [#206941](https://github.com/.../206941) merged

**[DOM-1597](https://linear.app/.../DOM-1597) · custody migration** (In Review)
  - Spent the session wrestling the migration green; daggerWatcherTest breakage and go.mod drift.
  - 2 commits
  - PR [#206900](https://github.com/.../206900) open
```

**No dashes (report-wide).** Punctuation dashes — em-dash `—`, en-dash `–`, and the spaced
hyphen clause break ` - ` — are banned from all rendered prose; only `;` `,` `(` `)` may join
clauses. Status is shown in parens `(Done)`, not after a dash. The model writes summaries this
way (SKILL.md §4) and the formatters defensively rewrite any stray dash to `; ` via
`_no_dashes()` before rendering. Hyphens inside identifiers and URLs (`DOM-1546`, kebab branch
names) are not clause-break punctuation and are preserved.

## 8. Report + delivery — `format_report(narrated) -> markdown`, `deliver(...)`

- `format_report` builds the full markdown report file, beginning with a window header
  `[since … now]` that **equals the window in `narrated.window`** (Invariant #2).
- `deliver(notes_dir, now, report_md, range_text, clipboard_cmd, last_run_path)`:
  1. ensure `notes_dir/<YYYY-MM>/` exists,
  2. write report to `notes_dir/<YYYY-MM>/standup-<YYYY-MM-DD>.md`,
  3. copy `range_text` via injected `clipboard_cmd` (None → return a copy-fence flag),
  4. **only then** write `now` to `last_run_path` (Invariant #1).
  Any error before step 4 aborts; `last_run_path` is left unchanged. Re-running the same
  window overwrites the same dated file (idempotent).
