---
name: review-behavior-change
description: Review code changes for undocumented behavioral/surface changes. Flags modifications to public interfaces, API contracts, or observable behavior that lack justification in an ADR, PRD, tech spec, or implementation plan. Use when the user asks to "check for breaking changes", "review surface changes", "audit behavioral changes", or "validate contract compliance".
allowed-tools: Read, Edit, Bash, Agent, AskUserQuestion
---

# Surface Change Review

## Execution Model

Delegate the ENTIRE workflow below to a single top-level sub-agent (Agent tool, **foreground**, `model: "sonnet"`). The main context must not perform the analysis itself — this prevents conversation history from biasing the review. Pass the sub-agent the full skill instructions (everything below this section), the `$ARGUMENTS`, and the repository path. The sub-agent performs all phases and returns the final report. The main context relays the report to the user and handles any follow-up (CHANGELOG approval, etc.).

---

Review recent code changes (uncommitted, commit, or branch diff) for behavioral changes at the system's surface — the outermost layer consumers interact with (HTTP endpoints, CLI entry points, exported functions, library public APIs). Flag any surface-level behavioral change that is not explicitly justified in a docs/ artifact (ADR, PRD, tech spec, or implementation plan).

## Change Severity: ADR vs CHANGELOG

Not every surface change warrants an ADR. Classify each unjustified change by severity:

**ADR-required** (architectural/breaking changes):
- Removing or renaming a public endpoint, function, or field
- Changing a function signature in a way that breaks existing callers
- Changing the semantics of an existing API (same inputs produce fundamentally different outputs)
- Switching protocols, storage backends, or communication patterns
- Changes that require consumers to update their code

**CHANGELOG-only** (minor behavioral improvements):
- Improving error messages (better wording, adding context/field names)
- Tightening validation (rejecting previously-accepted invalid input)
- Returning more specific error codes where a generic one was used before
- Adding fields to a response (non-breaking addition)
- Fixing a status code to be more semantically correct (e.g., 500 → 422 for bad input)
- Improving output formatting without changing data content
- Any change that makes the API "more correct" without breaking existing valid usage

The key distinction: if existing consumers of the API **would break** or **get different results for the same valid inputs**, it's ADR-worthy. If the change only affects error paths, invalid inputs, or adds information — it's a CHANGELOG entry.

## CHANGELOG Format

When suggesting changelog entries, use this format (entries go in `CHANGELOG.md` at the repo root under `## Behavioral Changes`):

```
- **YYYY-MM-DD** `<surface identifier>` — <what changed>: <new behavior> (was: <old behavior>)
```

Examples:
```
- **2026-05-17** `POST /enroll` — Improved error: now returns field name in validation errors (was: generic "invalid request")
- **2026-05-17** `GET /items` — Tightened: malformed cursor now returns 400 with message (was: empty 200)
- **2026-05-15** `Run()` — Fixed: negative qty now returns exit code 1 with message (was: panic)
```

## Human vs Agent Invocation

When this skill is invoked directly by a human (the default — no `--agent` flag in `$ARGUMENTS`), suggest CHANGELOG entries for minor behavioral changes. Present the suggested entries and let the user approve before any file is modified.

When invoked with `--agent` in `$ARGUMENTS` (called from another skill or automation), only report violations — do not suggest changelog entries or prompt for approval.

## What Counts as "The Surface"

The surface is defined by the same philosophy as the `surface-testing` skill:

- **HTTP/gRPC API**: endpoints, request/response shapes, status codes, error codes, headers
- **CLI**: flags, subcommands, output format, exit codes
- **Library public API**: exported function signatures, return types, error types, exported struct fields
- **Internal library boundaries**: packages that expose a complete, self-contained API (could be extracted independently)

## Quick Signal: Test File Changes

Before deep analysis, check whether existing test files were **modified** (not just added). This is the fastest indicator of a surface change:

- **Only new test files or only additive changes** (new test functions, new test cases added to existing tables): likely a new feature — no violation.
- **Modified or deleted assertions in existing tests**: the surface likely changed. This triggers deep analysis.
- **Renamed test functions or restructured test tables**: could be refactoring OR a behavioral change — triggers deep analysis.

If no existing test assertions were modified/deleted, AND the deep analysis (Phase 1) finds no other surface changes, report clean and exit early.

## Inputs

Determine the diff to review based on `$ARGUMENTS`:

- No arguments: use uncommitted changes (`git diff` + `git diff --cached`)
- `--commit <sha>`: diff that specific commit against its parent
- `--branch` or no flag with a branch name: diff current branch against main (`git diff main...HEAD`)
- A file path: diff only that file (uncommitted changes)

Also locate the docs directory:
- Look for `docs/` at the repository root
- Within docs, look for: `adr/`, `features/` (containing PRDs, tech specs), and any `*-plan.md` or `implementation-plan.md` files
- List all doc files found (paths only — don't read them yet)

## Phase 1: Change Analysis Agent

Spawn a sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to analyze the diff and classify changes.

**Prompt structure:**

```
You are analyzing a code diff for surface-level behavioral changes. Your job is to identify changes that alter the system's public interface or observable behavior — NOT internal refactoring.

DIFF:
<full diff content>

TEST FILE CHANGES (if any):
<subset of diff that touches test files — show full hunks>

Classify each meaningful change as one of:

### Surface Change <N>: <short title>
**Type**: <one of: endpoint-added, endpoint-removed, endpoint-modified, signature-changed, return-type-changed, error-behavior-changed, field-added, field-removed, field-renamed, status-code-changed, flag-added, flag-removed, output-format-changed, breaking-removal>
**Severity**: <ADR — breaking/semantic change to valid usage | CHANGELOG — improvement to error paths, validation, or non-breaking addition>
**File**: <path:line>
**Before**: <what it was (quote old code or describe)>
**After**: <what it is now (quote new code or describe)>
**Breaking**: <yes/no — would existing consumers break without code changes?>
**Test impact**: <were existing tests modified to accommodate this change? cite the test file and what changed>

SEVERITY RULES:
- If existing valid inputs would produce different outputs or errors → ADR
- If a public symbol is removed or renamed → ADR
- If only invalid inputs are now handled differently (better errors, tighter validation) → CHANGELOG
- If a response adds new fields without removing/changing existing ones → CHANGELOG
- If an error message text changed but error type/code is the same → CHANGELOG
- If a wrong status code is corrected (e.g., 500→422 for invalid input) → CHANGELOG

CLASSIFICATION RULES:
- Adding a new endpoint/function/field with no modifications to existing ones = additive, NOT a surface change (skip it)
- Adding a new optional parameter with a default = additive, NOT a surface change (skip it)
- Renaming an internal/unexported function = refactoring, NOT a surface change (skip it)
- Changing internal implementation while preserving the same inputs/outputs = refactoring, skip
- Changing documentation/comments only = skip
- Changing error messages (string content) WITHOUT changing error codes/types = CHANGELOG-severity surface change (improved error reporting)
- Tightening validation (rejecting previously-accepted invalid input) = CHANGELOG-severity surface change
- Correcting a wrong status code (e.g., 500→422 for bad input) = CHANGELOG-severity surface change
- ANY modification to an existing public function signature, response shape, error type, status code for valid inputs, or removal of a public symbol = ADR-severity surface change, REPORT IT

For test file analysis:
- If existing test assertions were MODIFIED (expected values changed, assertions removed, assertion logic altered): flag as "test-confirmed surface change" — the test had to change because behavior changed
- If existing tests were DELETED: flag — behavior may have been removed
- If only NEW test functions/cases were added: this is additive, do not flag
- If test refactoring only (renaming, restructuring without changing assertion values): note but do not flag

If you find ZERO surface changes, state "No surface changes detected" and explain why the changes are internal/additive only.
```

Include the full diff content in the prompt. If the diff is very large (>500 lines), summarize the non-test portions and include full test file hunks.

## Phase 2: Documentation Cross-Reference Agent

If Phase 1 found surface changes, spawn a second sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to check whether each is documented.

**Prompt structure:**

```
You are checking whether identified surface changes are justified by existing documentation. A surface change is "justified" if a docs/ artifact explicitly describes or mandates the behavioral change.

SURFACE CHANGES IDENTIFIED:
<paste all findings from Phase 1>

DOCUMENTATION FILES AVAILABLE:
<list all files found in docs/ with paths>

For EACH surface change, search the docs for justification:
1. Read ADR files that might be relevant (check titles/filenames first)
2. Read PRD files in the relevant feature directory
3. Read tech spec files in the relevant feature directory
4. Read implementation plan files
5. Check CHANGELOG.md at the repo root for an existing entry describing this change

A change is JUSTIFIED if ANY of these docs:
- Explicitly states the old behavior should change to the new behavior
- Defines a new API contract that matches the change
- Records an architectural decision that necessitates the change
- Specifies requirements that can only be met by the observed change
- Has a CHANGELOG entry describing the behavioral change (for CHANGELOG-severity items only)

A change is NOT JUSTIFIED if:
- No doc mentions the behavioral change at all
- Docs describe the OLD behavior as correct (contradiction)
- Docs are ambiguous — they don't clearly mandate either the old or new behavior

SEVERITY-AWARE JUSTIFICATION:
- **ADR-severity changes**: require justification in an ADR, PRD, tech spec, or implementation plan. A CHANGELOG entry alone is NOT sufficient for ADR-severity changes.
- **CHANGELOG-severity changes**: require either a docs/ artifact OR a CHANGELOG.md entry. If neither exists, recommend a CHANGELOG entry (not an ADR).

For each surface change, report:

### Change <N>: <title from Phase 1>
**Severity**: <ADR or CHANGELOG — carried from Phase 1>
**Justified**: <yes/no/ambiguous>
**Evidence**: <if yes: quote the doc and cite file:line. if no: state what you searched and didn't find. if ambiguous: explain the gap>
**Recommendation**: <if ADR-severity and not justified: "Requires ADR or explicit documentation before merge". If CHANGELOG-severity and not justified: "Needs CHANGELOG entry". If ambiguous: "Clarify in PRD/spec whether this behavioral change is intentional">

IMPORTANT:
- "Justified" means the docs EXPLICITLY call for this change. Implicit compatibility ("the docs don't say you can't") is NOT justification.
- A change can be justified by docs that were added IN THE SAME diff/branch — check for new ADRs or spec updates included in the changes.
- If the diff itself includes a new or updated ADR/spec that documents the change, that counts as justified.
- Do NOT recommend an ADR for CHANGELOG-severity changes. These are minor improvements that only need a changelog entry.
```

Pass the list of doc file paths. The agent should read relevant docs on demand (not all of them).

## Phase 3: Violation Report

After Phase 2 completes, compile the results. Separate ADR-severity violations from CHANGELOG-severity suggestions.

```
## Surface Change Review Complete

### Violations (Require ADR): N

<for each ADR-severity unjustified change>
#### <N>. <title>
- **Type**: <change type>
- **File**: <path:line>
- **Breaking**: yes
- **What changed**: <brief description>
- **Test confirmed**: <yes/no — were tests modified to match?>
- **Action required**: Document this change in an ADR or update the relevant PRD/spec before merge.
<end for each>

### Needs CHANGELOG Entry: N

<for each CHANGELOG-severity unjustified change>
#### <N>. <title>
- **Type**: <change type>
- **File**: <path:line>
- **What changed**: <brief description>
<end for each>

### Justified Changes: N
<brief list — title + which doc justified it>

### Ambiguous: N
<brief list — title + what's unclear>

### Additive (No Review Needed): N
<count of new features that don't modify existing surface>
```

### Suggesting CHANGELOG Entries (Human Invocation Only)

If this skill was invoked by a human (no `--agent` flag) AND there are CHANGELOG-severity changes without entries, suggest the entries using this format:

```
### Suggested CHANGELOG Entries

Add these to `CHANGELOG.md` under `## Behavioral Changes`:

- **YYYY-MM-DD** `<surface>` — <description>: <new behavior> (was: <old behavior>)
- ...
```

Use today's date. Present the suggestions and ask the user if they'd like to add them. Do NOT auto-write to the file.

If invoked with `--agent`, omit changelog suggestions entirely — only report violations.

### Clean Report

If there are ZERO violations AND zero CHANGELOG-needing changes, report:

```
## Surface Change Review Complete

No undocumented surface changes detected.

- Changes analyzed: N files
- Surface changes found: N (all justified) OR 0
- Additive changes: N (new features, no existing surface modified)
```

## Handling Edge Cases

- **Entire new feature with no existing surface modified**: Report clean — additive changes don't need retroactive documentation (though a PRD/spec SHOULD exist; note if missing but don't flag as violation).
- **Pure refactoring (tests unchanged, signatures unchanged)**: Report clean immediately after Phase 1.
- **Dependency version bump that changes transitive behavior**: Only flag if it surfaces through the public API (e.g., a library update changes the error type your function returns).
- **Generated code changes** (protobuf, OpenAPI codegen): Flag only if the source spec (.proto, openapi.yaml) was modified without a corresponding docs update.

## What This Skill Does NOT Do

- Does not judge whether a change is *good* — only whether it's *documented*
- Does not require documentation for internal refactoring
- Does not require documentation for purely additive changes (new endpoints, new functions)
- Does not require ADRs for minor improvements (better errors, tighter validation) — those get CHANGELOG entries
- Does not auto-write CHANGELOG entries — only suggests them for human approval
- Does not enforce documentation format — any ADR, PRD, spec, or plan that explicitly describes the change counts
