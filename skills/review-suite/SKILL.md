---
name: review-suite
description: "Run the full post-implementation review/hardening pass as one headless pipeline in an
  isolated worktree: code-review -> review-validate -> green-gate -> invariant-test -> review-tests
  -> review-openapi -> review-for-reader, then stop and present a unified report + combined diff
  for you to merge into the PR branch. Each stage's intentionally-failing tests are t.Skip()'d in
  place so later stages see a green baseline. Use when the user says 'run the review suite',
  'review-suite', 'do the full review pass', or wants the tail of the workflow
  (validate/invariant/tests/openapi/reader) automated after a feature is built. Do NOT use for the
  design phase (blueprint/goal), for a single review skill (call it directly), or to fix a known
  list of bugs (use review-validate)."
argument-hint: "[feature-dir] [--skip a,b] [--only a,b] [--review-effort high]"
allowed-tools: [Bash, Read, Edit, Write, Glob, Grep, Agent, Skill]
---

# Review Suite

Automate the tail of the workflow — the review/hardening pass you run after a feature is built —
as one **headless** pipeline inside an **isolated git worktree**, then stop and hand you a unified
report + combined diff to approve before it merges into your PR branch.

The orchestrator is **this context** (it must stay in the main session so each sub-skill keeps its
own internal sub-agent fan-out). It runs the six existing skills **unchanged** via the `Skill`
tool, enforces a set of standing rules over them, does its own mechanical work (worktree, baseline,
green-gate, skip-on-red, report) via **Haiku** sub-agents and `Bash`, and never interrupts you
mid-run. The only stop is at the end, for the merge.

This skill does **not** edit the six sub-skills. They remain byte-for-byte intact and callable on
their own exactly as before. `review-suite` is purely additive.

`AskUserQuestion` is intentionally **absent** from `allowed-tools` — the suite cannot ask you
anything mid-run by construction. Every would-be question becomes a report entry with a safe default.

## Prerequisites

- A Go project (uses `go build` / `go test`; falls back to `make ci` for the full baseline if a
  `ci` target exists).
- Run **from the PR branch** (a non-default branch with a diff vs `main`/`master`). "Merge into the
  PR branch" means the branch you are on. Any uncommitted work on it is **committed to this branch**
  in Phase 0 before the review starts (see Phase 0.2), so the isolated worktree carries the whole
  feature.
- `git` with worktree support.

## Standing rules (these OVERRIDE any conflicting instruction in a sub-skill)

While running any stage below, these rules win over the sub-skill's own text:

1. **Work in the worktree.** All file edits, `git`, and `go` commands run with the worktree
   (Phase 0) as the working directory. Use the worktree's diff (`git diff <base>...HEAD`), never
   `gh pr diff`.
2. **Never stop for the user — by any means.** Not `AskUserQuestion`, not a "STOP and report"
   instruction, not a prose "ask the user". Wherever a sub-skill would pause, hard-stop, or hand
   something to you: take the **safe default** (revert any risky/partial change; leave the proving
   test red — it will be skipped), record the question/stop + the default taken in the suite
   report, and continue.
3. **The orchestrator owns commits.** Ignore any "do not commit" / "the user handles commits"
   instruction in a sub-skill. You commit each stage (Phase rules below). Commit messages carry
   **no Co-Authored-By and no Claude attribution**.
4. **Leave the suite-written `t.Skip("review-suite: ...")` reason strings alone** — they are
   suite-managed, not prose to rewrite.
5. **Capture ticket data at stage time, not report time.** The moment a stage confirms a finding
   (fixed or deferred), record everything the Report format (below) needs for that bug's ticket —
   assign the next `RS-NNN` id and write down the explainer, evidence (test output, code excerpt),
   blast radius, and the pause condition/default taken — while the finding's full context is still
   in front of you. Phase 8 only assembles these tickets; it must never have to re-research a bug.

## Skip-on-red (the mechanism that lets the stages run back-to-back)

The test-writing skills each assume a **green** baseline and reason "red now = live violation/gap".
To give every later stage that green baseline without editing the skills, after each test-writing
stage the orchestrator neutralizes that stage's new red tests by skipping them **in place**. Run
this precise procedure (delegate the mechanical parts to a **Haiku** sub-agent):

1. **Find the stage's own new test functions.**
   `git diff --unified=0 <stage-start-ref>..HEAD -- '*_test.go'`, parse only lines matching
   `^\+func (Test|Benchmark|Fuzz)\w+\(` (real entry points, not helpers). A *modified* test shows
   its new signature on a `+` line and is caught the same way.
2. **Run just those, per package.** Derive each package path from the changed file's directory
   (`internal/x/foo_test.go` -> `./internal/x/...`) and run
   `go test -v -count=1 -run "^(TestA|TestB|...)$" ./pkg/...`.
   - **If the test binary fails to COMPILE** (no runtime results), do NOT treat it as "no reds" —
     raise a **compile-failure HALT** immediately (a non-compiling `_test.go` breaks the whole
     package and would corrupt the baseline).
3. **Skip each red function.** Parse `--- FAIL: TestX` lines; strip any `/subtest` suffix so a
   failing subtest maps to its parent `TestX`; insert
   `t.Skip("review-suite: <one-line reason>; see review-suite.html")` as the **first statement** of
   that function's body. (Safe: `t.Skip` -> `runtime.Goexit`, not `return`, so nothing after it
   becomes unused — no compile errors from the insertion.)
4. **Inventory it** — test name, file, the violation/gap it proves — and link it to the bug's
   `RS-NNN` ticket (standing rule 5) for the report.

Notes: skipping a whole function over-skips a table-driven test whose other cases are green (rare
for these dedicated proving tests; log it). `review-tests` may write a duplicate test for a path
already proven+skipped by `invariant-test` (it shows zero coverage); that duplicate is also red ->
skipped -> inventoried twice — redundant, not wrong; note it.

**The `t.Skip` insertions are NOT removed before the merge** — they remain in the final branch
(this supersedes the alternative of landing the tests red). CI therefore stays green, and the
report's red-test inventory is your fix-before-merge-to-main checklist (un-skipping is a one-line
diff per test once you fix the underlying issue).

## Per-stage pre-commit tree-sanity check (crash safety)

Before committing each stage, verify (`git diff --name-only` / `--stat` from the worktree) that the
stage changed only the file *types* it is allowed to, else **HALT** and report:

- **code-review**: nothing (read-only).
- **review-validate**: source + test files; all `Temporary_` tests deleted; tree compiles.
- **invariant-test**: only added test files + its `.html` — **no source modification** (a leftover
  injected mutation shows up here -> halt).
- **review-tests**: test files + minimal additive testability source edits + its `.html`; tree
  **compiles** (`go build ./... && go vet ./...`) — broken compile -> halt; no leaked scratch tests.
- **review-openapi**: only OpenAPI spec file(s) edited — descriptions/examples, no schema, path,
  or field changes; the spec linter passes and the generated-code target still builds (doc-only,
  codegen-neutral) — either failing -> halt.
- **review-for-reader**: only comment/doc/prose edits, no logic changes.

The skip-on-red edits (test files only) are the orchestrator's and are allowed; run the sanity
check AFTER skip-on-red, before the commit.

## Report format (`review-suite.html`)

The report's purpose is that **neither a human nor an AI should ever have to re-construct a bug
from a one-line summary**. Every confirmed finding — deferred or auto-fixed — gets a full
**ticket**; deferred (not auto-fixed) tickets are indexed at the top. Write the report as a single
self-contained HTML file (inline CSS, no external assets); the structures below are shown as
markdown for brevity — render them as styled HTML. Unless the environment provides a report style
(a project skill, CLAUDE.md, or an existing styled report to match), default to a **dark theme**
(dark background, light text, severity badges adjusted for contrast).

### Ticket ids

`RS-NNN`, assigned in discovery order across the whole run, never reused or renumbered (a dropped
false positive leaves a gap — fine). Each ticket is an anchor (`id="rs-003"`) the index links to.

### The index (top of the report)

Open issues first, grouped by severity (HIGH → MEDIUM → LOW), each row linking to its ticket.
Auto-fixed tickets follow in a collapsed `<details>` section. Everything else in the report
(stages run, gates, deferred decisions, red-test inventory) comes after the index.

```
# Review Suite Report — <branch / feature>

## ⚠ Open issues (not auto-fixed) — <N>

### HIGH (<n>)
| ID | Title | Location | Test |
|----|-------|----------|------|
| [RS-003](#rs-003) | Cursor not validated | list.go:142 | skipped |

### MEDIUM (<n>) … ### LOW (<n>) …

## ✓ Auto-fixed (<N>)   <- collapsed <details>, same table shape, links to tickets
```

Severity is the orchestrator's judgment call: HIGH = correctness/data-loss/panic/race, MEDIUM =
wrong-but-bounded behavior, LOW = advisory/prose/doc findings.

### The ticket (one per confirmed finding)

```
## RS-003 · HIGH · Deferred (proving test skipped)
### <one-line title>

| Field        | Value                                          |
|--------------|------------------------------------------------|
| Found by     | <stage that surfaced it> (Phase N)             |
| Stage        | <stage that proved/acted on it>                |
| Location     | <file:line> (every relevant site, not just one)|
| Proving test | <TestName> (skipped) — <test file:line>        |
| Invariant    | <the rule/spec/ADR clause violated, if any>    |

**Summary** — one paragraph: what is wrong and where.

**Explainer** — multi-paragraph plain-language walkthrough written for a reader with ZERO
context for this branch: what the code does today (with the relevant code excerpt inline), why
that is incorrect — the exact failure scenario step by step (input → path → bad outcome), what
correct behavior looks like, and the blast radius (which callers/endpoints/consumers are
affected). After reading it, the reader should understand the bug without opening the codebase.

**Evidence** — the failing-test output verbatim, plus the code excerpt(s) the explainer refers
to, with file:line ranges. Include the exact repro command
(`go test -run '^TestX$' ./pkg/...`).

**Why it wasn't auto-fixed** — the pause condition or stop the sub-skill hit, and the safe
default the suite took (e.g. "behavior change for existing consumers → reverted partial fix,
proving test skipped"). For auto-fixed tickets this section becomes **Fix applied** — what was
changed and where (commit + files).

**Suggested fix** — concrete change description, with a sketch diff when the fix is obvious;
name the constraint that made it the user's call. End with the un-skip instruction: "remove the
`t.Skip` at <file:line> after applying."
```

Status values: `Deferred (proving test skipped)`, `Auto-fixed`, `Advisory` (no test — e.g.
review-for-reader pre-existing findings; they get a ticket too, with Explainer/Evidence scaled to
what exists). The ticket's content comes from the stage-time capture (standing rule 5) — never
reconstructed from memory at report time.

## Argument parsing

`$ARGUMENTS` may contain a feature-dir path and flags:
- bare path -> feature directory (for stages 4–5).
- `--skip a,b` / `--only a,b` -> stage selection over
  {`code-review`,`review-validate`,`invariant-test`,`review-tests`,`review-openapi`,
  `review-for-reader`}.
- `--review-effort low|medium|high` -> default `high`.

## Phase 0: Setup

1. Confirm a non-default branch with a diff vs `main`/`master`; if not, stop and explain.
2. **Commit outstanding work on the current branch first.** The worktree is created from a commit,
   so any uncommitted feature code — staged, unstaged, **or untracked** (new test files, new
   packages) — would be invisible to the review. If `git status` is not clean, stage everything
   (`git add -A`) and commit it to the current branch before creating the worktree, with a clear
   message (e.g. `review-suite: commit working tree before review`) and **no Co-Authored-By / no
   Claude attribution**. Record the SHA and report it (you committed the user's in-flight work — say
   so). If the tree is already clean, skip. This replaces any patch/stash transfer into the
   worktree: the feature must live in a commit the worktree can check out.
3. **Build gate:** `go clean -testcache && go build ./...`. If it does NOT build, **ABORT** — you
   cannot review a non-building branch.
4. **Baseline:** the project CI command if present (`make ci`), else `go test ./... -race -count=1`.
   Record the passing set. (Skipped tests count as green.)
5. Create the worktree on a **fresh review branch off the current branch's HEAD** and switch all
   subsequent work into it (the current branch itself cannot be checked out in a second worktree, so
   the review gets its own branch that you merge back in Phase 8):
   ```
   git worktree add -b review-suite-<branch> ../worktrees/review-suite-<branch> HEAD
   ```
   Replace any `/` in `<branch>` with `-` for the branch and directory names. Note `<base>` =
   `origin/main` (or `master`) and `<stage-start-ref>` = the worktree HEAD at the start of each
   stage. Bash cwd persists between calls — operate from the worktree path with absolute paths.
6. Resolve the feature directory: explicit arg > inference from conversation (like `goal-from-spec`)
   > none. If unresolved or ambiguous across multiple `docs/features/*`, mark stages 4–5 to
   **auto-skip** and note it.
7. Determine applicable stages (stage selection, below).

## Phase 1: code-review

Invoke `Skill(code-review)` at `--review-effort` (default `high`) so it reviews the **worktree
diff**. Collect its findings in context. If it reports **zero** confirmed bugs, **skip Phase 2** and
log it (do not run review-validate with an empty list — it would otherwise ask the user).

## Phase 2: review-validate  (only logic-mutating stage)

Hand the Phase 1 findings to `Skill(review-validate)` as an explicit list, one per line:
```
- <description> — <file:line>
```
(this matches review-validate's "description + location" input and avoids its "no identifiable
issues -> ask the user" path).

Apply the standing rules: prove every finding; auto-fix only the **unambiguous** ones; both of its
pause conditions (behavior change for existing consumers; signature/interface choice) AND its
"STOP on regression" instruction default to **revert + leave the proving test red + report**.

Then: **skip-on-red** the deferred/reverted proving tests -> tree-sanity check (Temporary_ deleted,
compiles) -> commit the stage.

## Phase 3: green-gate

Run the baseline command again (`make ci` or `go test ./... -race -count=1`). With the deferred
proofs skipped, anything RED can only be a regression from the applied fixes. **Re-run a failing
test once** (flake guard); if still red, **HALT** the suite and assemble the partial report.

## Phase 4: invariant-test  (auto-skip if no ADRs/declared invariants, or feature-dir unresolved)

Invoke `Skill(invariant-test)` scoped to the feature dir. Its baseline is green (skip-on-red from
Phase 2), so its "red now = live violation" discrimination is clean. Both native gates resolve to
report defaults (needs-observability -> "accept untestable, logged"; live-violation -> "leave red,
logged"; this does not retroactively invalidate Phase 3).

Then: **skip-on-red** the live-violation tests -> tree-sanity check (no source mutation left
behind) -> commit the stage.

## Phase 5: review-tests  (auto-skip if no `prd.md`/`tech-spec.md`/`user-stories.md`, or ambiguous)

Invoke `Skill(review-tests)` scoped to the feature dir. Its coverage baseline is green, so its gap
analysis and "did my testability edit break a test?" check are clean. All four native gates resolve
to report defaults; independent genuine gaps are still implemented.

Then: **skip-on-red** the behavior-gap tests -> tree-sanity check incl. **halting** compile check
-> commit the stage.

## Phase 6: review-openapi  (auto-skip if the accumulated diff touches no OpenAPI spec)

Gate: `git diff --name-only <base>...HEAD` from the worktree matches an `openapi.yaml` (any
`api/**` spec). No match -> auto-skip and log.

Invoke `Skill(review-openapi)` on the touched spec(s). It edits spec descriptions/examples in
place per its rules (consumer-self-containment, no self-correction machinery, per-endpoint
exhaustive error vocabularies verified against the error emitters, worked request/response example
pairs in one coherent example world). Findings become report tickets (Advisory or Auto-fixed) per
standing rule 5. A behavior doc/code disagreement it surfaces is a **Deferred** ticket, never a
silent doc edit.

Then: tree-sanity check (spec file(s) only; linter + codegen-neutral gate) -> commit the stage.

## Phase 7: review-for-reader

Invoke `Skill(review-for-reader)` on the **worktree diff** `git diff <base>...HEAD` (the full
accumulated diff incl. suite tests) — never `gh pr diff`. It auto-rewrites confident prose findings;
unclear-"why" findings are left as-is and logged; its "pre-existing (out of scope)" findings are
advisory and go into the report. Leave suite `t.Skip(...)` reasons untouched.

Then: tree-sanity check (prose/comment edits only) -> commit the stage.

## Phase 8: report, then stop for merge

1. Write per-skill HTML reports where the skills already place them, under
   `docs/features/<feature>/` (`invariant-test.html`, `review-tests.html`), and **commit them** so
   the skills' cross-run memory survives.
2. Assemble a unified **`review-suite.html`** (feature dir if present, else repo root) following
   the **Report format** section above, in this order:
   - the **index**: open (not-auto-fixed) issues grouped by severity, linking to their tickets;
     auto-fixed tickets in a collapsed section;
   - the **tickets** — one full ticket per confirmed finding, assembled verbatim from the
     stage-time captures (standing rule 5), never re-researched or summarized down;
   - stages run vs skipped (with reasons);
   - the build/baseline result, the green-gate result, and any per-stage sanity HALT;
   - every deferred decision/stop + the default the suite took (each linked to its ticket where
     one exists);
   - the **red-test inventory** — every `t.Skip()`'d test + a link to the ticket whose
     violation/gap it proves: this is your fix-before-merge-to-main checklist (un-skipping is a
     one-line diff per test);
   - links to the per-skill reports + a combined diff summary.
3. **Present** the combined diff + report and **STOP**. Do not merge yet.
4. Only on the user's explicit go: merge the worktree branch into the PR branch — fast-forward if it
   hasn't moved, otherwise a real merge that **reports conflicts rather than forcing** — then
   `git worktree remove` the worktree.

## Failure policy

- **HALT** conditions: the Phase 0 build gate; the Phase 3 green-gate regression; any per-stage
  tree-sanity or compile failure. On HALT, assemble the partial report and stop (leave the worktree
  for inspection).
- Any **other** stage that errors is logged and skipped; the suite continues and flags it.

## Models

- The six sub-skills run via `Skill` in this context and keep their own internal **Sonnet** fan-out
  (unchanged).
- The orchestrator's own mechanical work — baseline/green-gate runs, skip-on-red parsing+editing,
  tree-sanity checks, report assembly — is delegated to **Haiku** sub-agents.
- **No Opus** is requested anywhere in the suite.
