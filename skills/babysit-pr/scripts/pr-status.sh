#!/usr/bin/env bash
# pr-status.sh — Fetches CI check status and unresolved bot review threads for the current branch's PR.
# Outputs a single JSON object with all status info.
#
# Usage: pr-status.sh [pr-number | pr-url | branch]
#   If a selector is provided, uses that PR (owner/repo derived from it).
#   Otherwise auto-detects from the current branch.
# Requires: gh CLI authenticated

set -euo pipefail

# PR selector: number, URL, or branch may be passed as $1; otherwise auto-detect.
# Fetch the PR including its url so owner/repo can be derived from the PR itself
# (the URL/number may point at a repo other than the current directory).
# Always derive PR_NUMBER from the returned .number so downstream consumers
# (GraphQL query, jq tonumber) get a bare integer regardless of input form.
if [ -n "${1:-}" ]; then
  PR_JSON=$(gh pr view "$1" --json number,headRefName,headRefOid,state,url 2>/dev/null || echo '{}')
else
  PR_JSON=$(gh pr view --json number,headRefName,headRefOid,state,url 2>/dev/null || echo '{}')
fi
PR_NUMBER=$(echo "$PR_JSON" | jq -r '.number // empty')

if [ -z "$PR_NUMBER" ]; then
  echo '{"error": "No PR found for current branch"}' >&2
  exit 1
fi

# Derive repo owner/name from the PR url (authoritative for which repo the PR
# lives in), falling back to the current directory's repo.
PR_URL=$(echo "$PR_JSON" | jq -r '.url // empty')
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
else
  REPO_INFO=$(gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"')
  OWNER=$(echo "$REPO_INFO" | cut -d/ -f1)
  REPO=$(echo "$REPO_INFO" | cut -d/ -f2)
fi

BRANCH=$(echo "$PR_JSON" | jq -r '.headRefName')
HEAD_SHA=$(echo "$PR_JSON" | jq -r '.headRefOid')

# --- Fetch CI checks, Copilot reviews, SonarCloud comments in parallel ---

CHECKS_FILE=$(mktemp)
COPILOT_FILE=$(mktemp)
SONAR_COMMENTS_FILE=$(mktemp)
SONAR_CHECKS_FILE=$(mktemp)
trap 'rm -f "$CHECKS_FILE" "$COPILOT_FILE" "$SONAR_COMMENTS_FILE" "$SONAR_CHECKS_FILE"' EXIT

# CI checks (all checks for the PR)
(gh pr checks "$PR_NUMBER" --repo "$OWNER/$REPO" --json name,state,link,bucket,startedAt,completedAt \
  2>/dev/null || echo '[]') > "$CHECKS_FILE" &

# Unresolved Copilot review threads via GraphQL (includes submitted_at for stale detection and rateLimit)
(GRAPHQL_RESPONSE=$(gh api graphql -f query="
{
  rateLimit { remaining resetAt }
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    pullRequest(number: $PR_NUMBER) {
      reviews(last: 50) {
        nodes {
          author { login }
          submittedAt
        }
      }
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 5) {
            nodes { author { login } body path line createdAt }
          }
        }
      }
    }
  }
}") && echo "$GRAPHQL_RESPONSE" | jq 'if .errors then error("GraphQL errors: \(.errors | tostring)") else . end' | jq '{
  threads: [.data.repository.pullRequest.reviewThreads.nodes[]
    | select(.isResolved == false)
    | select(.comments.nodes[0].author.login == "copilot-pull-request-reviewer")
  ],
  latest_review_at: (
    [.data.repository.pullRequest.reviews.nodes[]
     | select(.author.login == "copilot-pull-request-reviewer")
     | .submittedAt
    ] | sort | last // null
  ),
  graphql_rate_limit: {
    remaining: .data.rateLimit.remaining,
    reset_at: .data.rateLimit.resetAt
  }
}' || echo '{"threads": [], "latest_review_at": null, "graphql_rate_limit": {"remaining": null, "reset_at": null}}') > "$COPILOT_FILE" &

# SonarCloud PR-level comment (quality gate result)
(gh api "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" \
  --jq '[.[] | select(.user.login == "sonarqubecloud[bot]") | {id, body, updated_at}]' \
  2>/dev/null || echo '[]') > "$SONAR_COMMENTS_FILE" &

# SonarCloud check-run status
(gh api "repos/$OWNER/$REPO/commits/$HEAD_SHA/check-runs" \
  --jq '{sonar: [.check_runs[] | select(.app.slug == "sonarqubecloud") | {name, status, conclusion}]}' \
  2>/dev/null || echo '{"sonar": []}') > "$SONAR_CHECKS_FILE" &

wait

# --- Read files with fallback for empty/corrupt content ---

read_json_or_default() {
  local file="$1" default="$2"
  if [ -s "$file" ] && jq empty "$file" 2>/dev/null; then
    cat "$file"
  else
    echo "$default"
  fi
}

CHECKS=$(read_json_or_default "$CHECKS_FILE" '[]')
COPILOT_DATA=$(read_json_or_default "$COPILOT_FILE" '{"threads": [], "latest_review_at": null, "graphql_rate_limit": {"remaining": null, "reset_at": null}}')
SONAR_COMMENTS=$(read_json_or_default "$SONAR_COMMENTS_FILE" '[]')
SONAR_CHECKS=$(read_json_or_default "$SONAR_CHECKS_FILE" '{"sonar": []}')

# Extract copilot fields
COPILOT_THREADS=$(echo "$COPILOT_DATA" | jq '.threads')
COPILOT_REVIEW_AT=$(echo "$COPILOT_DATA" | jq -r '.latest_review_at // empty')
GRAPHQL_RATE_LIMIT=$(echo "$COPILOT_DATA" | jq '.graphql_rate_limit')

# Summarize check states
FAILED=$(echo "$CHECKS" | jq '[.[] | select(.state == "FAILURE" or .state == "ERROR")] | length')
PENDING=$(echo "$CHECKS" | jq '[.[] | select(.state == "PENDING" or .state == "QUEUED" or .state == "IN_PROGRESS")] | length')
PASSED=$(echo "$CHECKS" | jq '[.[] | select(.state == "SUCCESS")] | length')
TOTAL=$(echo "$CHECKS" | jq 'length')

jq -n \
  --arg pr "$PR_NUMBER" \
  --arg branch "$BRANCH" \
  --arg owner "$OWNER" \
  --arg repo "$REPO" \
  --arg head_sha "$HEAD_SHA" \
  --arg copilot_review_at "${COPILOT_REVIEW_AT:-null}" \
  --argjson failed "$FAILED" \
  --argjson pending "$PENDING" \
  --argjson passed "$PASSED" \
  --argjson total "$TOTAL" \
  --argjson checks "$CHECKS" \
  --argjson copilot_threads "$COPILOT_THREADS" \
  --argjson sonar_comments "$SONAR_COMMENTS" \
  --argjson sonar_checks "$SONAR_CHECKS" \
  --argjson graphql_rate_limit "$GRAPHQL_RATE_LIMIT" \
  '{
    pr_number: ($pr | tonumber),
    branch: $branch,
    owner: $owner,
    repo: $repo,
    head_sha: $head_sha,
    checks: {
      summary: { total: $total, passed: $passed, failed: $failed, pending: $pending },
      failed_checks: [($checks // [])[] | select(.state == "FAILURE" or .state == "ERROR") | {name, state, link}],
      pending_checks: [($checks // [])[] | select(.state == "PENDING" or .state == "QUEUED" or .state == "IN_PROGRESS") | {name, state}],
      all_checks: ($checks // [])
    },
    copilot: {
      unresolved_count: ($copilot_threads | length),
      latest_review_at: (if $copilot_review_at == "null" then null else $copilot_review_at end),
      unresolved_threads: $copilot_threads
    },
    sonar: {
      checks: $sonar_checks,
      comments: $sonar_comments
    },
    graphql_rate_limit: $graphql_rate_limit
  }'
