---
name: fix-issue
description: "Reproduce and fix a GitHub issue end-to-end: parse the issue, assess reproducibility
  (comment if insufficient info), create a worktree, explore the codebase, reproduce the bug,
  write surface tests proving it, implement the fix via TDD, self-review, submit a PR, and babysit
  CI until green. Handles both bugs and features. Trigger on 'fix issue #N', 'fix this issue',
  '/fix-issue', or when user provides a GitHub issue URL/number and asks to fix it."
argument-hint: "<issue-number-or-url>"
allowed-tools: [Bash, Read, Edit, Write, Glob, Grep, Agent, AskUserQuestion, Skill]
---

# Fix Issue

Reproduce and fix a GitHub issue, from triage through green CI. The orchestrator (this context,
Opus) stays lightweight — it parses the issue, makes gate decisions (reproducibility, test
validity, exit points), and delegates all heavy work to sub-agents and skills with
purpose-matched models.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Git repository with remote `origin`
- A `Makefile` with a `ci` target (used for verification)

## Phase 1: Fetch & Parse Issue

Spawn a **Sonnet** sub-agent to fetch and parse the issue. This is structured extraction — low reasoning load.

```
Agent(model: "sonnet", description: "Parse GitHub issue")
```

**Sub-agent prompt:**

```
Fetch and parse a GitHub issue. Return structured JSON — nothing else.

ISSUE: <issue-number-or-URL from $ARGUMENTS>

Run:
  gh issue view <number> --json title,body,labels,state,comments,url

Parse the result and return this exact JSON structure:

{
  "number": <int>,
  "url": "<string>",
  "title": "<string>",
  "state": "<string>",
  "type": "bug" | "feature" | "unknown",
  "type_signals": "<explain what signals led to the type classification>",
  "reproduction_steps": [
    {"step": 1, "description": "<string>", "command": "<shell command if present, else null>"},
    ...
  ],
  "expected_behavior": "<string or null>",
  "actual_behavior": "<string or null>",
  "environment": "<string or null — OS, version, config mentioned>",
  "has_sufficient_repro_info": <boolean>,
  "missing_info": ["<what's missing if has_sufficient_repro_info is false>"],
  "key_comments": [
    {"author": "<string>", "body_summary": "<string — one sentence>"}
  ]
}

Type classification rules:
- Bug signals in labels: bug, fix, defect, error, regression, crash
- Feature signals in labels: enhancement, feature, feat, new, improvement, request
- Bug signals in title/body: "fix", "broken", "error", "fail", "crash", "doesn't work", "regression", "incorrect"
- Feature signals in title/body: "add", "implement", "create", "new", "support", "enable", "introduce", "enhance"
- Labels take priority over title/body patterns
- If still unclear, set type to "unknown"

Reproduction step parsing:
- Look for numbered lists, "steps to reproduce", "how to reproduce", code blocks with commands
- Extract shell commands when present (e.g., lines starting with $ or in ```bash blocks)
- If no explicit steps exist but the issue describes a scenario, extract the implicit steps
- If the issue has no reproduction information at all, set reproduction_steps to [] and has_sufficient_repro_info to false

has_sufficient_repro_info is true when ALL of:
- At least one reproduction step exists (explicit or inferred from context)
- Expected behavior is stated or clearly implied
- Actual behavior is stated or clearly implied

If the issue is a feature request, has_sufficient_repro_info is always true (features don't need repro steps).
```

### Reproducibility Gate

After the parsing sub-agent returns, the orchestrator evaluates the result:

**If the issue is closed:** Report to the user and stop.

**If type is "unknown":** Ask the user whether this is a bug or feature before continuing.

**If type is "bug" AND has_sufficient_repro_info is false:**

Post a comment on the issue requesting more information, then stop:

```bash
gh issue comment <number> --body "$(cat <<'EOF'
Thanks for reporting this issue. We'd like to reproduce this but need a bit more information:

<list each item from missing_info as a bullet>

Once we have these details, we'll investigate further.
EOF
)"
```

Tell the user: "Commented on issue #N requesting more information. The issue doesn't have enough detail to reproduce. Here's what's missing: <missing_info>."

**If has_sufficient_repro_info is true (or type is "feature"):** Continue to Phase 2.

## Phase 2: Create Worktree

Always isolate work in a worktree. No asking — just do it.

```bash
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
```

Determine branch name from the issue type and number:
- Bugs: `fix/<number>-<short-description>` (e.g., `fix/42-null-pointer-on-empty-input`)
- Features: `feat/<number>-<short-description>` (e.g., `feat/55-add-webhook-support`)

Short description: lowercase, hyphens, max 5 words, derived from the issue title.

```bash
BRANCH="<type>/<number>-<short-description>"
WORKTREE_PATH="../worktrees/$BRANCH"
git worktree add -b "$BRANCH" "$WORKTREE_PATH" "origin/$MAIN_BRANCH"
```

After creating the worktree, all subsequent work happens from `$WORKTREE_PATH`. Tell the user:
"Created worktree at `$WORKTREE_PATH` on branch `$BRANCH`."

## Phase 3: Explore Codebase

Spawn a **Sonnet** Explore agent to search the codebase for relevant code. Search-heavy, moderate reasoning.

```
Agent(subagent_type: "Explore", model: "sonnet", description: "Explore codebase for issue context")
```

**Sub-agent prompt:**

```
Search the codebase for code relevant to this GitHub issue. Report file paths, function names,
and existing test files that relate to the problem.

ISSUE SUMMARY:
Title: <title>
Type: <bug|feature>
Description: <body summary>
Reproduction steps: <parsed steps>

FIND:
1. Files and functions most likely involved in the reported behavior
2. Existing tests that cover the affected code paths
3. For bugs: the likely root cause location (file:line if possible)
4. For features: similar implementations or integration points to model after
5. Entry points / surface area — how does a user interact with this code? (HTTP endpoint, CLI command, exported function, etc.)

Report findings as a structured list. Include file paths and line numbers.
```

The orchestrator reads the exploration results and uses them to inform subsequent phases.

## Phase 4: Design Approach

### For bugs

Skip this phase unless the bug is complex (affects multiple packages, has multiple possible root causes, or the fix approach is ambiguous). For straightforward bugs with a clear root cause from Phase 3, proceed directly to Phase 5.

If the bug IS complex, invoke the `/deliberate` skill with the bug context, root cause hypotheses from Phase 3, and possible fix approaches.

### For features

Always run design for features. Invoke the `/deliberate` skill:

```
Skill(skill: "deliberate")
```

Provide the deliberation with:
- The full issue body and comments
- Codebase exploration results from Phase 3
- 2-3 concrete implementation approaches with trade-offs

The user picks an approach (or proposes a new one) before implementation proceeds.

## Phase 5: Reproduce (Bugs Only)

Skip this phase for features.

Spawn an **Opus** sub-agent to attempt reproduction. This requires complex multi-step reasoning —
interpreting error descriptions, executing commands, and comparing actual vs expected behavior.

```
Agent(model: "opus", description: "Reproduce reported bug")
```

**Sub-agent prompt:**

```
You are attempting to reproduce a bug reported in a GitHub issue. Your goal is to trigger the
exact failure described by the reporter and confirm the bug exists in the current codebase.

ISSUE:
Title: <title>
Reproduction steps: <parsed reproduction_steps JSON>
Expected behavior: <expected_behavior>
Actual behavior: <actual_behavior>
Environment: <environment or "not specified">

CODEBASE CONTEXT (from exploration):
<paste exploration results — relevant files, entry points, existing tests>

WORKTREE PATH: <worktree_path>
All commands must run from this directory.

INSTRUCTIONS:

1. Translate reproduction steps into executable actions:
   - Shell commands: run them directly
   - API calls: use curl or the appropriate client
   - Code snippets: create a temporary test file or script
   - "Run the server and do X": start the server in background, execute the action, capture output, tear down

2. Execute each step and capture output/errors.

3. Compare the result against the reported actual behavior:
   - REPRODUCED: the failure matches what the reporter described
   - PARTIAL: a failure occurs but differs from the report (describe the difference)
   - NOT_REPRODUCED: the code works correctly — the bug may be fixed, environment-specific, or the report is inaccurate

4. If REPRODUCED or PARTIAL, identify:
   - The exact error message or incorrect output
   - The code path that produces the failure (file:line)
   - A minimal trigger — the simplest action that causes the bug

5. Clean up: remove any temporary files, stop any background processes.

Report format:
{
  "status": "REPRODUCED" | "PARTIAL" | "NOT_REPRODUCED",
  "evidence": "<what happened when steps were executed>",
  "error_output": "<exact error message or incorrect output, if any>",
  "root_cause_file": "<file:line>",
  "root_cause_explanation": "<what the code does wrong>",
  "minimal_trigger": "<simplest way to trigger the bug>",
  "notes": "<anything unexpected, environment differences, etc.>"
}

IMPORTANT:
- Do NOT fix the bug — only reproduce it
- If a step requires a running server or service, start it, reproduce, then stop it
- If reproduction requires specific test data or fixtures, create them
- If the environment is too different to reproduce (e.g., requires a specific OS), report NOT_REPRODUCED with explanation
```

### Reproduction Gate

After the reproduction sub-agent returns:

**REPRODUCED:** Label the issue and continue to Phase 6 with the reproduction evidence and root cause.

```bash
gh issue edit <number> --add-label "reproduced"
```

If the `reproduced` label doesn't exist yet, create it first:

```bash
gh label create "reproduced" --description "Bug has been independently reproduced" --color "D93F0B" 2>/dev/null || true
gh issue edit <number> --add-label "reproduced"
```

**PARTIAL:** Label as reproduced (the bug is real, even if slightly different). Tell the user what was found vs what was expected. Ask whether to proceed with the partial reproduction or investigate further.

**NOT_REPRODUCED:** Tell the user the bug couldn't be reproduced. Offer two options:
1. Comment on the issue asking for clarification
2. Proceed to Phase 6 anyway, writing tests based on the issue description (best-effort)

If the user chooses option 1:

```bash
gh issue comment <number> --body "$(cat <<'EOF'
We attempted to reproduce this issue but were unable to trigger the described behavior.

**What we tried:**
<summarize reproduction attempt>

**What we observed:**
<summarize actual behavior seen>

Could you provide additional details? Specifically:
- Exact version/commit you're running
- Full error output (if applicable)
- Any configuration that might differ from defaults

This will help us track down the issue. Thanks!
EOF
)"
```

## Phase 6: TDD Red — Write Failing Tests

This phase has two steps, tried in strict order. **Step A is mandatory. Step B is the fallback
only when Step A is impossible.**

### Step A: Surface Test (REQUIRED — always try this first)

Invoke the `/surface-testing` skill to write a test that proves the bug exists (or defines the
expected behavior for features) **through the public interface**.

```
Skill(skill: "surface-testing")
```

The surface test enters through the same boundary a real user would: an HTTP endpoint, a CLI
`Run()` function, an exported library function. It never calls internal/private functions. Read
the `/surface-testing` skill for the full philosophy — this is non-negotiable.

Provide the skill with:
- For bugs: reproduction evidence from Phase 5, root cause location, the minimal trigger, and expected vs actual behavior
- For features: the approved design from Phase 4, the entry points and integration points from Phase 3
- The entry points / surface area identified during Phase 3 exploration — the skill needs to know HOW a user reaches this code
- The existing test file(s) and naming conventions (see Test Placement below)

After the skill completes, verify the test is actually a surface test by checking:
1. The test calls a public entry point (HTTP request, exported function, CLI `Run()`)
2. The test does NOT import internal/unexported packages
3. The test does NOT call private/unexported functions directly
4. The test file uses `package xxx_test` (Go)

If the test violates any of these, **reject it and re-invoke the skill** with explicit correction:
"The test you wrote calls internal function X directly. Rewrite it to enter through the public
surface: <describe the entry point from Phase 3>."

Run the surface test to confirm it fails for the right reason:

```bash
cd <worktree_path>
go test -run <TestName> ./path/to/package/... 2>&1 || true
```

If the test FAILS as expected — **Step A succeeded.** This test is permanent, will be committed,
and serves as the regression test. Proceed to Phase 7.

If the test PASSES (bug not reproducible via surface) — proceed to Step B.

### Step B: Temporary Internal Test (FALLBACK ONLY)

Only reach this step when the bug **cannot** be proven through the public interface. Examples:
- Panic/crash in a goroutine that's recovered before reaching the surface
- Memory leak that doesn't manifest as observable behavior
- Race condition only visible under `-race` with internal state inspection
- Internal state corruption that hasn't (yet) produced a user-visible symptom

If none of these apply and the surface test simply passed, the bug may already be fixed or the
issue description is inaccurate. **Do not write a temporary test as a shortcut for a surface test
that was hard to write.** Instead, report to the user that the bug couldn't be proven via surface
test, and ask how to proceed.

If a temporary test IS justified, write it directly (without the surface-testing skill):
- Prefix the test name with `Temporary_` (e.g., `Temporary_RaceOnConcurrentWrite`)
- Add a comment: `// temporary — not for commit, proves issue #<number>`
- Place it in a separate file (e.g., `temporary_issue_<number>_test.go`)
- These tests are deleted before any commit (the orchestrator owns cleanup in Phase 9)

Run the temporary test to confirm it demonstrates the issue:

```bash
cd <worktree_path>
go test -run Temporary_ ./path/to/package/... 2>&1 || true
```

If even the temporary test passes, the bug cannot be proven. Report to the user and exit early.

### Test Placement Rules

**Surface tests (from Step A)** — permanent regression tests — MUST be placed alongside existing tests:

1. Find the existing test file for the package/component being tested (e.g., if fixing code in `server.go`, look for `server_test.go`)
2. Add the new test to that file, grouped with similar tests (e.g., if testing an HTTP endpoint, place it near other endpoint tests)
3. Follow the naming and organization conventions already present in that test file
4. Only create a new test file if no existing test file covers the relevant package/component

Tell the `/surface-testing` skill explicitly which existing test file to add to and what grouping pattern to follow. Include in the prompt:
- The path to the existing test file(s) found during Phase 3 exploration
- Example test names from that file showing the naming convention
- Where in the file the new test should be placed (after which existing test, or in which test group)

**Temporary tests (from Step B)** — always in separate files, always deleted before commit.

## Phase 7: TDD Green — Implement

Spawn a **Sonnet** sub-agent to implement the minimal code change. The tests from Phase 6 define exactly what needs to change — this is guided implementation work.

```
Agent(model: "sonnet", description: "Implement fix/feature to pass tests")
```

**Sub-agent prompt:**

```
Implement the minimal code change to make failing tests pass. Do NOT add anything beyond
what the tests require.

CONTEXT:
Issue: <title> (#<number>)
Type: <bug|feature>
Branch: <branch name>
Worktree: <worktree_path>

ROOT CAUSE (bugs):
<root cause file:line and explanation from Phase 5>

DESIGN (features):
<approved approach from Phase 4>

FAILING TESTS:
<list each test name, file path, and what it asserts>

CODEBASE PATTERNS (from exploration):
<relevant patterns — error handling style, naming conventions, package organization>

INSTRUCTIONS:
1. Read the failing test(s) to understand exactly what behavior is expected
2. Read the source code that needs to change
3. Make the minimum change to pass the tests
4. Run the tests to confirm they pass:
   go test -run <TestName> ./path/to/package/...
5. If tests still fail, iterate — read the failure output and adjust
6. Do NOT refactor, add features, or clean up surrounding code
7. Follow all coding guidelines from CLAUDE.md

Report what you changed (file paths and a one-sentence summary per file).
```

After the sub-agent reports, the orchestrator verifies:

```bash
cd <worktree_path>
go test -run <TestName> ./path/to/package/...
```

If tests still fail, send the failure output back to the sub-agent for another iteration (max 3 attempts). If still failing after 3 attempts, report the blocker to the user.

## Phase 8: Verify

Run the full project verification:

```bash
cd <worktree_path>
git add <changed-files>
make ci
```

If `make ci` fails:
- Spawn a **Sonnet** sub-agent to analyze and fix the failure
- Re-run `make ci` after the fix
- Max 3 attempts — if still failing, report the blocker to the user

## Phase 9: Self-Review

Before committing or creating a PR, run the `/review` skill in a sub-agent to catch issues
early — code quality problems, missed edge cases, or convention violations that would be caught
in human review. Fixing these now means a cleaner first commit and fewer CI round-trips.

Spawn an **Opus** sub-agent (in the worktree) to review the uncommitted changes:

```
Agent(model: "opus", description: "Self-review changes before commit")
```

**Sub-agent prompt:**

```
You are reviewing code changes before they are committed and submitted as a PR. Review the
diff of all uncommitted changes for issues that would be caught in code review.

WORKTREE PATH: <worktree_path>
BRANCH: <branch>

Run `git diff` to see all changes, then review them. For each finding, categorize as:
- MUST_FIX: bugs, security issues, correctness problems — fix these before proceeding
- SHOULD_FIX: convention violations, test gaps, code quality — fix these too
- MINOR: style nits, optional improvements — skip these

Fix all MUST_FIX and SHOULD_FIX issues directly. Do not fix MINOR issues.

After fixing, run `make ci` to verify nothing broke.

Report:
- What the review found
- What was fixed
- What was skipped (MINOR items)
```

After the sub-agent completes and any fixes are applied, re-run `make ci` to confirm everything
still passes before proceeding to commit.

## Phase 10: Submit

Commit and create the PR. This is mechanical — no sub-agent needed.

### Commit

```bash
cd <worktree_path>
git add <all-changed-files>
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

Fixes #<issue-number>
EOF
)"
```

Commit message rules:
- Type: `fix` for bugs, `feat` for features
- Scope: the primary package or component changed
- Subject: imperative mood, lowercase, no period, under 50 chars
- No Co-Authored-By or Claude attribution (per CLAUDE.md)

### Push

```bash
git push -u origin "$(git branch --show-current)"
```

### Create PR

```bash
gh pr create --title "<type>(<scope>): <subject>" --body "$(cat <<'EOF'
### Purpose
<1-2 sentences: what this change does and why, referencing the issue>

### Implementation
<bullet list of major code changes>

Fixes #<issue-number>
EOF
)"
```

PR format follows CLAUDE.md conventions (Purpose + Implementation sections, no Claude attribution).

## Phase 11: Watch CI

**You MUST invoke the `/babysit-pr` skill. Do NOT run `gh pr checks` or any other CI status
command yourself.** The babysit-pr skill handles polling, waiting for checks to appear, retrying
flaky tests, fixing failures, and addressing automated review comments. It knows that checks take
time to start after a push — "no checks reported" means "wait and poll", not "no CI configured."

```
Skill(skill: "babysit-pr")
```

Pass the PR number as an argument so babysit-pr knows which PR to monitor.

The skill autonomously fixes CI failures, addresses SonarCloud/Copilot comments, and gets the PR
into a human-reviewable state. It handles its own polling, retries, and model selection.

**Never short-circuit this phase.** Even if `gh pr checks` returns empty immediately after push,
that just means CI hasn't started yet. The babysit-pr skill will wait for it.

## Completion

When babysit-pr reports the PR is green and ready for human review, report to the user:

```
## Issue #<number> Complete

**Branch:** <branch>
**PR:** <pr-url>
**Worktree:** <worktree_path>

### What was done
- <one-line summary of the bug fix or feature>

### Tests added
- <list test names and what they verify>

### Files changed
- <list files with one-sentence description of change>
```

## Early Exit Points

The skill can exit before completion at several points. Each exit must leave a clear status:

| Exit point | Condition | Action |
|---|---|---|
| Phase 1 | Issue is closed | Report to user |
| Phase 1 | Insufficient repro info (bugs) | Comment on issue, report to user |
| Phase 5 | Cannot reproduce | Comment on issue or proceed best-effort (user choice) |
| Phase 6 | Tests pass (bug not provable) | Report to user — bug may be fixed or not reproducible |
| Phase 7 | Implementation fails after 3 attempts | Report blocker to user |
| Phase 8 | `make ci` fails after 3 attempts | Report blocker to user |

At any early exit, if a worktree was created but no useful work was done, offer to clean it up:

```bash
cd <original_directory>
git worktree remove <worktree_path>
```

## Model Assignment Summary

| Phase | Work | Model | Rationale |
|---|---|---|---|
| 1. Fetch & Parse | Structured extraction from GitHub API | **Sonnet** | Low reasoning, high structure |
| 2. Worktree | Bash commands | None (orchestrator) | Mechanical |
| 3. Explore | Codebase search | **Sonnet** (Explore agent) | Search-heavy |
| 4. Design | `/deliberate` skill | Skill-managed (**Opus** advocates) | Multi-perspective reasoning |
| 5. Reproduce | Execute repro steps, interpret results | **Opus** | Complex judgment |
| 6. TDD Red | `/surface-testing` skill | Skill-managed | Deep interface understanding |
| 7. TDD Green | Implement to pass tests | **Sonnet** | Guided by clear test targets |
| 8. Verify | `make ci` + fix failures | **Sonnet** (if fixes needed) | Mechanical + fix loop |
| 9. Self-Review | Review uncommitted diff, fix issues | **Opus** | Catches issues before commit |
| 10. Submit | Commit, push, PR | None (orchestrator) | Mechanical |
| 11. Watch CI | `/babysit-pr` skill | Skill-managed | Autonomous |
| Orchestrator | Gate decisions, user communication | **Opus** (main context) | Judgment, coordination |
