#!/usr/bin/env bash
# fetch-failed-logs.sh — Fetches logs for a failed CI check from either GitHub Actions or Buildkite.
#
# Usage: fetch-failed-logs.sh <check-name> <check-link>
#   check-name: The name of the failed check (for display)
#   check-link: The URL of the failed check (used to determine GHA vs Buildkite)
#
# Requires:
#   - gh CLI authenticated (for GitHub Actions)
#   - BUILDKITE_API_TOKEN in environment or ~/env.source (for Buildkite)
#
# Output: Failed job logs to stdout, prefixed with job/step names.

set -euo pipefail

CHECK_NAME="${1:?Usage: fetch-failed-logs.sh <check-name> <check-link>}"
CHECK_LINK="${2:?Usage: fetch-failed-logs.sh <check-name> <check-link>}"

echo "=== Fetching logs for: $CHECK_NAME ==="
echo "=== Link: $CHECK_LINK ==="
echo ""

# --- Detect CI system from the check link ---

if echo "$CHECK_LINK" | grep -q "github.com.*actions\|github.com.*/runs/"; then
  # ---- GitHub Actions ----
  # Extract run ID from URL patterns like:
  #   https://github.com/org/repo/actions/runs/12345
  #   https://github.com/org/repo/actions/runs/12345/jobs/67890
  RUN_ID=$(echo "$CHECK_LINK" | grep -oP 'runs/\K[0-9]+')

  if [ -z "$RUN_ID" ]; then
    echo "ERROR: Could not extract GHA run ID from link: $CHECK_LINK" >&2
    exit 1
  fi

  echo "--- GitHub Actions run: $RUN_ID ---"
  echo ""
  LOG_OUTPUT=$(gh run view "$RUN_ID" --log-failed 2>/dev/null || true)

  if [ -z "$LOG_OUTPUT" ]; then
    LOG_OUTPUT=$(gh run view "$RUN_ID" --log 2>/dev/null | tail -200 || true)
  fi

  if [ -z "$LOG_OUTPUT" ]; then
    echo "ERROR: Could not fetch logs for GHA run $RUN_ID. Check the link manually: $CHECK_LINK" >&2
    exit 1
  fi

  echo "$LOG_OUTPUT"

elif echo "$CHECK_LINK" | grep -q "buildkite.com"; then
  # ---- Buildkite ----
  # Load token if not already set
  if [ -z "${BUILDKITE_API_TOKEN:-}" ] && [ -f ~/env.source ]; then
    source ~/env.source
  fi

  if [ -z "${BUILDKITE_API_TOKEN:-}" ]; then
    echo "ERROR: BUILDKITE_API_TOKEN not set and ~/env.source not found." >&2
    echo "Set BUILDKITE_API_TOKEN or create ~/env.source with: export BUILDKITE_API_TOKEN=<token>" >&2
    exit 1
  fi

  # Extract org, pipeline, and build number from URL patterns like:
  #   https://buildkite.com/anchor-labs/anchorage/builds/12345
  #   https://buildkite.com/anchor-labs/anchorage/builds/12345#job-uuid
  BK_ORG=$(echo "$CHECK_LINK" | grep -oP 'buildkite.com/\K[^/]+')
  BK_PIPELINE=$(echo "$CHECK_LINK" | grep -oP 'buildkite.com/[^/]+/\K[^/]+')
  BK_BUILD=$(echo "$CHECK_LINK" | grep -oP 'builds/\K[0-9]+')

  if [ -z "$BK_ORG" ] || [ -z "$BK_PIPELINE" ] || [ -z "$BK_BUILD" ]; then
    echo "ERROR: Could not parse Buildkite URL: $CHECK_LINK" >&2
    exit 1
  fi

  echo "--- Buildkite build: $BK_ORG/$BK_PIPELINE#$BK_BUILD ---"
  echo ""

  # Fetch build JSON to find failed jobs
  BUILD_JSON=$(curl -sH "Authorization: Bearer $BUILDKITE_API_TOKEN" \
    "https://api.buildkite.com/v2/organizations/$BK_ORG/pipelines/$BK_PIPELINE/builds/$BK_BUILD")

  # Extract failed/timed_out job IDs and names, fetch their logs
  FAILED_JOBS=$(echo "$BUILD_JSON" | jq -r '
    .jobs[]
    | select(.type == "script")
    | select(.state == "failed" or .state == "timed_out")
    | "\(.id)\t\(.name)"
  ')

  if [ -z "$FAILED_JOBS" ]; then
    echo "No failed jobs found in build $BK_BUILD. States:" >&2
    echo "$BUILD_JSON" | jq -r '.jobs[] | select(.type == "script") | "\(.name): \(.state)"' >&2
    exit 1
  fi

  # Cap at 5 failed jobs to avoid flooding context with log output
  MAX_JOBS=5
  JOB_COUNT=0
  TOTAL_FAILED=$(echo "$FAILED_JOBS" | wc -l)

  # Persist logs in /tmp so Claude can inspect the full log if the tail isn't enough.
  # Files are cleaned up when the workstation restarts nightly.
  LOG_DIR="/tmp/ci-logs-build-${BK_BUILD}"
  mkdir -p "$LOG_DIR"

  while IFS=$'\t' read -r JOB_ID JOB_NAME; do
    JOB_COUNT=$((JOB_COUNT + 1))
    if [ "$JOB_COUNT" -gt "$MAX_JOBS" ]; then
      echo "--- Skipping remaining $((TOTAL_FAILED - MAX_JOBS)) failed jobs (capped at $MAX_JOBS) ---"
      break
    fi

    # Download full log to /tmp for later inspection
    SAFE_NAME=$(echo "$JOB_NAME" | tr ' /:' '___')
    LOG_FILE="$LOG_DIR/${SAFE_NAME}.log"
    curl -sH "Authorization: Bearer $BUILDKITE_API_TOKEN" \
      "https://api.buildkite.com/v2/organizations/$BK_ORG/pipelines/$BK_PIPELINE/builds/$BK_BUILD/jobs/$JOB_ID/log.txt" \
      -o "$LOG_FILE"

    # Strip ANSI escape codes in-place for easier reading
    sed -i 's/\x1b\[[0-9;]*m//g' "$LOG_FILE"

    LOG_SIZE=$(wc -c < "$LOG_FILE")
    LOG_LINES=$(wc -l < "$LOG_FILE")

    echo "--- Failed job: $JOB_NAME ($JOB_ID) ---"
    echo "--- Log: ${LOG_LINES} lines, ${LOG_SIZE} bytes (showing last 300) ---"
    echo "--- Full log: $LOG_FILE ---"
    echo ""
    tail -300 "$LOG_FILE"
    echo ""
    echo "--- End: $JOB_NAME ---"
    echo ""
  done <<< "$FAILED_JOBS"

else
  echo "WARN: Unknown CI system for link: $CHECK_LINK" >&2
  echo "Cannot determine if this is GitHub Actions or Buildkite." >&2
  echo "Try opening the link manually: $CHECK_LINK" >&2
  exit 1
fi
