---
name: babysit-pr
description: "Monitor and fix automated review comments (Copilot, SonarCloud) and CI failures
  on the current branch's PR. Gets the PR into a human-reviewable state autonomously.
  Use when the user says 'babysit this PR', 'fix CI', 'handle the automated reviews',
  or 'get this PR green'."
argument-hint: "[pr-number]"
disable-model-invocation: true
allowed-tools: [Bash, Read, Edit, Glob, Grep, Agent]
---

# Babysit PR

You are an autonomous PR agent. Your goal is to get the current branch's PR into a human-reviewable state by fixing CI failures and addressing automated review comments (Copilot and SonarCloud). Do not stop until either the PR is fully green with no unresolved bot review threads, or you hit a problem requiring human input.

## Phase 1 — Assess PR Status

Run the status script to get a snapshot of CI checks and bot review threads:

```bash
${CLAUDE_SKILL_DIR}/scripts/pr-status.sh $ARGUMENTS
```

Fallback: `~/.claude/skills/babysit-pr/scripts/pr-status.sh $ARGUMENTS`

The script accepts an optional PR number argument. If `$ARGUMENTS` is empty, it auto-detects from the current branch.

Parse the JSON output and determine the current state:

- **All checks passed + no unresolved bot threads** → Skip to Phase 6 (Final Check)
- **Checks still pending** → Go to Phase 2 (Poll)
- **Checks failed** → Go to Phase 3 (Fix CI)
- **Checks passed but unresolved bot threads** → Go to Phase 4 (SonarCloud) or Phase 5 (Copilot)

## Phase 2 — Poll Until Checks Complete

Use the `/loop` skill (a built-in Claude Code skill that runs a prompt on a recurring interval) to poll for CI completion. Invoke it as `/loop 5m` with the polling logic below. On each iteration, run `pr-status.sh` and check:

- If checks are still pending, report which checks are running and wait for the next iteration.
- If a check has failed, stop the loop and proceed to Phase 3.
- If all checks have passed, stop the loop and proceed to Phase 4/5 for bot reviews.

**Important**: Do NOT act on Copilot or SonarCloud feedback until their analysis for the latest push has completed. Copilot and SonarCloud re-analyze after each push — acting on stale comments wastes effort.

To detect stale Copilot reviews, record the UTC time of your most recent push. The `pr-status.sh` output includes `copilot.latest_review_at` — only act on reviews where this timestamp is newer than your push time.

## Phase 3 — Fix CI Failures

For each failed check from the status output:

### 3a. Fetch the logs

```bash
${CLAUDE_SKILL_DIR}/scripts/fetch-failed-logs.sh "<check-name>" "<check-link>"
```

Fallback: `~/.claude/skills/babysit-pr/scripts/fetch-failed-logs.sh`

### 3b. Triage: flaky vs stale branch vs real failure

Before attempting a fix, determine the failure type:

1. **Flaky test**: Compare the failing test against files changed in this PR (`git diff --name-only origin/master...HEAD`). If the failing test is unrelated to any changed file, it is likely flaky.
   - Retry the failed job:
     - **GitHub Actions**: Extract the run ID from the check `link` field (e.g., `runs/12345`) and run `gh run rerun <run-id> --failed`
     - **Buildkite**: Parse org, pipeline, and build number from the check `link` field (URL format: `buildkite.com/<org>/<pipeline>/builds/<build>`). Then fetch the build to get the failed job UUID:
       ```bash
       source ~/env.source
       # Get failed job ID from build
       JOB_ID=$(curl -sH "Authorization: Bearer $BUILDKITE_API_TOKEN" \
         "https://api.buildkite.com/v2/organizations/<org>/pipelines/<pipeline>/builds/<build>" \
         | jq -r '.jobs[] | select(.state == "failed") | .id' | head -1)
       # Retry it
       curl -s -X PUT -H "Authorization: Bearer $BUILDKITE_API_TOKEN" \
         "https://api.buildkite.com/v2/organizations/<org>/pipelines/<pipeline>/builds/<build>/jobs/$JOB_ID/retry"
       ```
   - Return to Phase 2 to poll for the retry result.

2. **Stale branch**: If the failure seems unrelated to PR changes, check how far behind master the branch is:
   ```bash
   git fetch origin master && git rev-list --count HEAD..origin/master
   ```
   If more than 50 commits behind, merge master:
   ```bash
   git merge origin/master
   ```
   If the merge has conflicts, abort it (`git merge --abort`) and stop — report the conflicts to the user. Do not attempt to auto-resolve merge conflicts from a stale branch update.
   If the merge succeeds cleanly, push and return to Phase 2 to poll the new build.

3. **Real failure**: The failure is related to files changed in this PR. Proceed to 3c.

### 3c. Fix the failure

- Analyze the log output to identify the root cause (failed assertion, compile error, lint violation, etc.)
- Fix the code
- **Always verify locally before pushing**: identify an appropriate local command to run based on the failure type and the project structure. Run it and confirm it passes.
- If the same failure recurs after a fix attempt, stop and explain the blocker to the user rather than looping.

### 3d. Commit and push

1. Stage only the files you changed
2. Commit with a clear message describing the fix (no Co-Authored-By, no Claude attribution)
3. Push the branch
4. Record the push time (UTC) — needed for stale review detection in Phase 2
5. Return to Phase 2 to poll the new build

## Phase 4 — Resolve SonarCloud Issues

SonarCloud feedback appears in two places. Fetch both:

**Quality gate comment** (overall pass/fail):
```bash
gh api "repos/<owner>/<repo>/issues/<pr>/comments" \
  --jq '.[] | select(.user.login == "sonarqubecloud[bot]") | .body'
```

**Inline code comments** (specific file/line issues):
```bash
gh api "repos/<owner>/<repo>/pulls/<pr>/comments" \
  --jq '.[] | select(.user.login == "sonarqubecloud[bot]") | {path, line, body}'
```

Derive `<owner>/<repo>` from `gh repo view --json owner,name`.

For each issue:
- **Duplicated code** → Determine if the duplication is intentional:
  - **Test files**: Duplicated code in tests is expected (tests follow explicit patterns and avoid DRY).
  - **New version / legacy copy**: If the duplicated code exists because a new version was created as a clean copy of legacy code (to avoid modifying the legacy path), the duplication is intentional.
  - If the duplication is intentional, add the `skip-sonar-scan` label to the PR and move on:
    ```bash
    gh pr edit <pr-number> --add-label "skip-sonar-scan"
    ```
    The `skip-sonar-scan` label tells SonarCloud to ignore these warnings. Only add it once — check existing labels first.
  - If the duplication is NOT intentional (e.g., copy-paste in production code that should be refactored), fix it directly.
- **Coverage below threshold** → Write additional tests targeting the uncovered paths. Verify locally.
- **Code smell / bug / vulnerability** → Fix the flagged code directly.
- **Cannot resolve** → Flag to user and continue with other issues.

SonarCloud does not use GitHub review threads — fixing the code and pushing is what clears the issues. After fixes, return to Phase 3d (commit/push) then Phase 2 (poll).

**Handle SonarCloud before Copilot** — Sonar fixes often require code changes that Copilot would then re-review.

## Phase 5 — Resolve Copilot Review Comments

The `pr-status.sh` output includes unresolved Copilot threads with their thread IDs, file paths, line numbers, and comment bodies.

For each unresolved thread:

- **If you can address it**: Make the code change, then resolve the thread:
  ```bash
  gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "<thread-id>"}) {
      thread { isResolved }
    }
  }'
  ```

- **If you disagree or it's not actionable**: Post a brief reply explaining why, then resolve the thread:
  ```bash
  gh api graphql -f query='
  mutation {
    addPullRequestReviewThreadReply(input: {threadId: "<thread-id>", body: "<explanation>"}) {
      comment { id }
    }
  }'
  ```
  Then resolve it with the mutation above.

- **If you genuinely cannot determine the right fix**: Leave it unresolved and flag it to the user at the end.

After addressing Copilot comments, return to Phase 3d (commit/push) then Phase 2 (poll).

## Phase 6 — Final Check

Once all checks are green, SonarCloud quality gate passes, and all Copilot threads are resolved:

1. Run `pr-status.sh` one final time to confirm everything is clean.
2. Report a summary to the user:
   - What was fixed across all iterations
   - What was committed and pushed
   - Any issues left unresolved and why
   - Confirmation that the PR is ready for human review

## Rules

- Never stop between phases to ask for confirmation unless you are truly blocked.
- Never push without verifying the fix locally first.
- Never commit unrelated changes.
- Never force-push.
- If the same CI failure recurs after two fix attempts, stop and explain rather than looping.
- If a check is still in-progress, keep polling — do not give up early.
- Do not act on Copilot or SonarCloud feedback until their analysis for the latest push has completed.
- Handle SonarCloud issues before Copilot comments.
- Do NOT include "Co-Authored-By" or Claude attribution in commits.
- Clean up any downloaded build logs or temp files when done.

## Test Fix Policy

When attempting fixes:
- Evaluate confidence that the fix is correct before pushing.
- If confidence is low, run the relevant test locally to verify.
- If a fix does not help, revert the change before moving on.
- Goal: avoid leftover experimental changes in the PR.
