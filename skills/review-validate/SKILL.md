---
name: review-validate
description: Validate reported bugs/issues via sub-agents, write surface tests proving each one, then present findings for review before fixing. Use when bugs have been identified (by bug-detector, code review, or discussion) and you want to confirm they're real, prove them with tests, and fix them safely. Trigger phrases include "validate these issues", "prove these bugs", "test and fix these", "validate and test", or "review-validate".
allowed-tools: Read, Edit, Write, Bash, Agent, AskUserQuestion
---

# Review Validate

Validate identified bugs or issues from the current conversation context. For each issue: confirm it's real via a sub-agent, write a surface test that demonstrates the problem, then present all findings for user review before applying any fixes.

## Inputs

This skill assumes the issues/bugs to validate are already present in the conversation context — from a prior bug-detector run, code review, discussion, or any other source. Parse the context for actionable issues: each needs at minimum a description and a location (file path or component).

If the context contains no identifiable issues, ask the user what they'd like validated.

## Phase 1: Validate Each Issue (Parallel Sub-Agents)

Spawn one sub-agent per issue (Agent tool, **foreground**, run in parallel where independent) to determine whether the issue is real.

**Sub-agent prompt structure:**

```
You are validating whether a reported bug/issue is real. Your job is to confirm or reject it by reading the relevant code and tracing the logic.

REPORTED ISSUE:
<issue description, file path, line numbers if available>

INSTRUCTIONS:
1. Read the relevant source code
2. Trace the execution path that would trigger this issue
3. Determine if the issue is:
   - CONFIRMED: The bug is real and can be triggered under described conditions
   - REJECTED: The code is actually correct — explain why the report is wrong
   - PARTIAL: The issue exists but is less severe or narrower than reported
4. If CONFIRMED or PARTIAL, describe:
   - The exact trigger conditions
   - What currently happens (the bug)
   - What should happen (expected behavior)
   - Whether this is a behavioral change (existing consumers rely on current behavior) or a pure bug (current behavior violates documented/intended contract)

IMPORTANT:
- Do NOT fix the issue — only validate it
- Be skeptical — many reported issues turn out to be false positives
- Check for existing tests that cover this path — if tests pass and assert the current behavior, this might be intentional
- Note if the "fix" would change observable behavior for existing consumers
```

## Phase 2: Surface Test Writing

For each CONFIRMED or PARTIAL issue from Phase 1, attempt to write a surface test that demonstrates the bug. Follow the `surface-testing` skill philosophy — test through the public interface only.

**For each confirmed issue, evaluate testability:**

1. **Can it be tested through the surface?** Identify the public entry point (HTTP endpoint, exported function, CLI command) that exercises the buggy code path.
2. **Write the test.** The test should:
   - FAIL with the current buggy behavior (proving the bug exists)
   - PASS once the fix is applied (defining the correct behavior)
   - Follow all testing patterns from CLAUDE.md
3. **If untestable from the surface**, report this to the user with an explanation of why — don't test internals as a workaround.

Run the test to confirm it fails as expected. If it passes (bug not reproducible via surface), downgrade the issue to UNCONFIRMED and note the discrepancy.

## Phase 3: Findings Report

Present all findings to the user before any fixes are applied.

```
## Bug Validation Report

### Confirmed & Test-Proven: N

<for each confirmed issue with a failing test>
#### <N>. <issue title>
- **Status**: Confirmed
- **File**: <path:line>
- **Trigger**: <how to trigger the bug>
- **Test**: <test file path> — currently FAILS as expected
- **Behavioral change?**: <yes/no — does the fix change what existing consumers observe?>
- **Proposed fix**: <1-2 sentence description of the fix approach>
<end for each>

### Confirmed, Not Testable from Surface: N

<for each confirmed issue that can't be surface-tested>
#### <N>. <issue title>
- **Status**: Confirmed (no surface test possible)
- **File**: <path:line>
- **Why untestable**: <explanation — e.g., internal optimization, unreachable via public API>
- **Recommendation**: <remove dead code / expose observability / accept risk>
<end for each>

### Rejected: N

<for each rejected issue>
#### <N>. <issue title>
- **Status**: Rejected
- **Reason**: <why the reported issue is not actually a bug>
<end for each>

### Behavioral Changes Requiring Review: N

<issues where the fix would change observable behavior>
#### <N>. <issue title>
- **Current behavior**: <what consumers see today>
- **Proposed behavior**: <what they'd see after fix>
- **Risk**: <who might be affected>
```

**After presenting the report, ask the user:**
- Which confirmed issues to proceed with fixing
- Whether behavioral changes are acceptable
- Whether to skip any issues

## Phase 4: Apply Fixes (Only After User Approval)

Only proceed after explicit user approval. For each approved fix:

1. Apply the fix
2. Run the surface test — confirm it now PASSES
3. Run the full test suite — confirm no regressions
4. If fixing causes other tests to fail, STOP and report to the user — this indicates a behavioral change that needs review

## Rules

- **Never fix without proving first.** Every fix must be preceded by a test that demonstrates the bug (unless the issue is confirmed-but-untestable, in which case the user explicitly approved proceeding).
- **Behavioral changes always need review.** If existing tests assert the "buggy" behavior, that behavior may be intentional. Flag it, don't override it.
- **Prefer fixing implementation over changing tests.** When a fix causes existing tests to fail, assume the tests encode correct business requirements (per CLAUDE.md). Investigate before changing tests.
- **One fix per issue.** Don't bundle fixes — each issue gets its own discrete change so the user can approve/reject individually.
- **Surface tests only.** Never write tests that call internal/private functions. If you can't prove the bug from the surface, say so.
