#!/bin/bash
# Claude Code Statusline
# Renders a 2-line status bar from JSON piped to stdin by Claude Code.
# All output is buffered into $OUT and flushed with a single printf to
# prevent rendering artifacts when Claude Code's TUI redraws the terminal.
#
# LINE 1: ⏳ CacheExpiry | 🤖 Model | 📟 Version | 📁 Dir | 🌿 Branch [wt]
# LINE 2: 🧠 Context | 📦 Read · ✨ Write · ⚠️ Next | 💰 Cost | [5h%] [7d%]
#
# Platform: macOS (darwin) and Linux. macOS uses BSD tools natively;
# Linux uses GNU tools (tac, GNU date) that ship in every distro's base.
# Requires: jq, date, grep, tail, sed, git (plus tac on Linux)
# Input:    JSON object on stdin (see --help for full field reference)

show_help() {
cat <<'HELP'
CLAUDE CODE STATUSLINE — Segment Reference
============================================

Claude Code invokes this script after each API response, piping a JSON
object to stdin. The script renders a 2-line status bar and exits.

LINE 1 — Session identity & cache
──────────────────────────────────
  ⏳ CacheExpiry    Local wall-clock time when the prompt cache expires.
                     The TTL is read from the last assistant message in the
                     session transcript:
                       ephemeral_5m_input_tokens > 0 → 5 minutes (300s)
                       ephemeral_1h_input_tokens > 0 → 1 hour    (3600s)
                       neither                       → no expiry shown
                     Shows "--" when there is no transcript yet (session just
                     started), no cache-creation tokens on the last turn, or
                     the cache has already expired.

  🤖 Model          Active model display name (e.g. "Opus 4.6 (1M context)").
                     Source: .model.display_name

  📟 Version        Claude Code CLI version (e.g. "2.1.108").
                     Source: .version

  📁 Dir            Current working directory ($HOME shortened to ~).
                     Source: .workspace.current_dir // .cwd

  🌿 Branch [wt]   Current git branch (or short SHA in detached HEAD).
                     Branch is cached for 5s keyed on session_id.
                     Appends [wt] when workspace.git_worktree is set.
                     Hidden entirely outside a git repository.

LINE 2 — Token economics & rate limits
───────────────────────────────────────
  🧠 Context        Context window utilization.
                     Progress bar: filled proportional to used_percentage.
                     Bar color: green below 75%, gradient to red 75–100%.
                     Token count: total tokens in this request / window size.
                       total = input_tokens + cache_creation + cache_read
                     Shows "⚠ N%" warning when remaining_percentage < 30%.

  📦 Read           Tokens served from the prompt cache on the LAST API call.
                     Billed at 0.1x the base input token price.

  ✨ Write          Tokens written to the prompt cache on the LAST API call.
                     Billed at 1.25x (5-min TTL) or 2x (1-hour TTL).

  ⚠️ Next           Known minimum new cache writes on the NEXT API call.
                     Equals the last call's output_tokens — the model's response
                     is now conversation history and will be written to cache.
                     Your next prompt adds to this, but its size is unknown.

  💰 Cost           Session cost in USD from Claude Code.
                     Source: .cost.total_cost_usd

  [N% · Xh]        5-hour rolling rate-limit window: utilization % and reset.
                     Source: .rate_limits.five_hour.{used_percentage,resets_at}

  [N% · Xd]        7-day rolling rate-limit window: utilization % and reset.
                     Source: .rate_limits.seven_day.{used_percentage,resets_at}

FLAGS
─────
  --12h              Use 12-hour AM/PM format for cache expiry
                     (e.g. "02:32:07 PM" instead of default "14:32:07").

                     Example:
                       "command": "~/.claude/statusline.sh --12h"

DEPENDENCIES
────────────
  Required: jq  date  grep  tail  sed  git  (plus tac on Linux)
  On macOS: uses BSD date (-u -jf, -r) and tail -r for reverse read.
  On Linux: uses GNU date (-d) and tac for reverse read — both ship in
  every mainstream distro's base (coreutils), including Alpine/BusyBox.
  The check enforces jq/git (often not pre-installed) and the shared
  utilities; if any is missing the script prints a one-line checklist
  (tool:v = present, tool:x = missing) and exits cleanly.

DEBUG
─────
  Set DEBUG=1 near the top of the script to capture the raw JSON input:
    /tmp/statusline_debug.json       — latest invocation (overwritten)
    /tmp/statusline_render_*.json    — timestamped history (appended)
HELP
exit 0
}

[ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] && show_help

# ==========================================================================
# Configuration
# ==========================================================================

DEBUG=0
TIME_FMT="%H:%M:%S"

for arg in "$@"; do
  case "$arg" in
    --12h) TIME_FMT="%I:%M:%S %p" ;;
  esac
done

# ==========================================================================
# Platform detection & dependency check
# ==========================================================================

IS_MACOS=0
[[ "$OSTYPE" == "darwin"* ]] && IS_MACOS=1

all_ok=1
dep_status=""
for cmd in jq date grep tail sed git; do
  if command -v "$cmd" >/dev/null 2>&1; then
    dep_status+=" ${cmd}:v"
  else
    dep_status+=" ${cmd}:x"
    all_ok=0
  fi
done
if [ "$all_ok" -eq 0 ]; then
  printf 'statusline deps:%s\n' "$dep_status"
  exit 0
fi

# ==========================================================================
# Platform-aware date helpers
# ==========================================================================

# Parse an ISO 8601 UTC timestamp (e.g. "2026-04-14T17:24:07.599Z") to
# a Unix epoch. Returns nothing on parse failure.
#   macOS: strip fractional seconds, parse with BSD date -u -jf.
#   Linux: GNU date handles ISO 8601 + Z suffix natively.
parse_ts_to_epoch() {
  if [ "$IS_MACOS" -eq 1 ]; then
    date -u -jf "%Y-%m-%dT%H:%M:%SZ" "$(echo "$1" | sed 's/\.[0-9]*Z$/Z/')" +%s 2>/dev/null
  else
    date -d "$1" +%s 2>/dev/null
  fi
}

# Format a Unix epoch as a local-time string (e.g. "%H:%M:%S").
#   macOS: date -r <epoch>    Linux: date -d @<epoch>
format_epoch() {
  if [ "$IS_MACOS" -eq 1 ]; then
    date -r "$1" "+$2" 2>/dev/null
  else
    date -d "@$1" "+$2" 2>/dev/null
  fi
}

# Return a file's mtime as Unix epoch, or 0 on failure.
#   macOS: stat -f %m    Linux: stat -c %Y
file_mtime() {
  if [ "$IS_MACOS" -eq 1 ]; then
    stat -f %m "$1" 2>/dev/null || echo 0
  else
    stat -c %Y "$1" 2>/dev/null || echo 0
  fi
}

# ==========================================================================
# Read JSON from stdin
# ==========================================================================

if ! input=$(timeout 5 cat 2>/dev/null || cat); then
  printf 'statusline: stdin read failed\n'
  exit 0
fi

if [ "$DEBUG" -eq 1 ]; then
  echo "$input" >/tmp/statusline_debug.json
  echo "$input" >"/tmp/statusline_render_$(date +%Y%m%d_%H%M%S).json"
fi

# ==========================================================================
# Color setup (respects NO_COLOR — see https://no-color.org)
# ==========================================================================

use_color=1
[ "${NO_COLOR+set}" = "set" ] && use_color=0

RST="" C_DIM="" C_GRAY="" C_RED=""
V_MODEL="" V_VER="" V_DIR="" V_GIT="" V_CACHE="" V_CTX="" V_CACHED="" V_NEW="" V_INPUT="" V_OUTPUT=""

if [ "$use_color" -eq 1 ]; then
  RST=$'\033[0m'
  C_DIM=$'\033[38;5;242m'     # separators, dim text
  C_GRAY=$'\033[38;5;245m'    # secondary text
  C_RED=$'\033[38;5;197m'     # warnings

  V_MODEL=$'\033[38;5;219m'   # model name
  V_VER=$'\033[38;5;252m'     # version
  V_DIR=$'\033[38;5;45m'      # directory path
  V_GIT=$'\033[38;5;120m'     # git branch
  V_CACHE=$'\033[38;5;220m'   # cache expiry, rate limit brackets
  V_CTX=$'\033[38;5;39m'      # context token counts
  V_CACHED=$'\033[38;5;156m'  # cache read tokens (📦)
  V_NEW=$'\033[38;5;209m'     # cache write tokens (✨)
  V_INPUT=$'\033[38;5;117m'   # input totals, next-turn warning (⚠️)
  V_OUTPUT=$'\033[38;5;222m'  # output totals
fi

SEP=" ${C_DIM}│${RST} "

# ==========================================================================
# Utility functions
# ==========================================================================

# Return an ANSI true-color escape for a utilization percentage.
# Green (#22DD22) below 75%, then piecewise RGB interpolation to red over 75–100%.
utilization_color() {
  local pct=$1
  if [ "$pct" -lt 75 ]; then
    printf '\033[38;2;34;221;34m'
    return
  fi
  local t=$(( (pct - 75) * 100 / 25 ))
  [ "$t" -gt 100 ] && t=100
  local hue=$(( 120 - 120 * t / 100 ))
  local V=230 C=195 m=34
  local sector=$(( hue / 60 )) f=$(( hue - sector * 60 ))
  local r g b
  if [ "$sector" -le 0 ]; then
    r=$((C + m)); g=$((C * f / 60 + m)); b=$m
  elif [ "$sector" -le 1 ]; then
    r=$((C * (60 - f) / 60 + m)); g=$((C + m)); b=$m
  else
    r=$m; g=$((C + m)); b=$m
  fi
  printf '\033[38;2;%d;%d;%dm' "$r" "$g" "$b"
}

# Render a 10-character progress bar: [▓▓▓░░░░░░░], color-coded by utilization.
make_progress_bar() {
  local util=$1 width=${2:-10}
  local filled=$((util * width / 100))
  [ "$filled" -gt "$width" ] && filled=$width
  local empty=$((width - filled))
  local bar_color=$(utilization_color "$util")
  local bar="${C_DIM}[${bar_color}"
  for ((i = 0; i < filled; i++)); do bar+='▓'; done
  bar+="${C_DIM}"
  for ((i = 0; i < empty; i++)); do bar+='░'; done
  bar+="]${RST}"
  echo "$bar"
}

# Format a token count for display: 1234567 → "1.234M", 12345 → "12k", 123 → "123".
format_tokens() {
  local count=$1
  if [ "$count" -ge 1000000 ]; then
    printf '%d.%03dM' "$((count / 1000000))" "$((count % 1000000 / 1000))"
  elif [ "$count" -ge 1000 ]; then
    echo "$((count / 1000))k"
  else
    echo "$count"
  fi
}

# ==========================================================================
# Parse JSON input (single jq call extracts all fields as null-delimited
# key/value pairs; `printf -v` assigns them to shell vars without `eval`,
# so quotes/backslashes/newlines in values can't inject shell code)
# ==========================================================================

# Pre-declare so a malformed stdin JSON leaves them empty rather than unset.
current_dir="" model_name="" cc_version="" session_id="" transcript_path="" git_worktree=""
context_window_size=0 input_tokens=0 cache_creation=0 cache_read=0 output_tokens=0 total_cost_usd=0
used_percentage="" remaining_percentage="" five_hour_util="" five_hour_epoch="" seven_day_util="" seven_day_epoch=""

while IFS= read -r -d '' key && IFS= read -r -d '' value; do
  printf -v "$key" '%s' "$value"
done < <(jq -j '
  def kv($k; $v): $k, "\u0000", ($v | tostring), "\u0000";
  kv("current_dir";          .workspace.current_dir // .cwd // "unknown"),
  kv("model_name";           .model.display_name // "Claude"),
  kv("cc_version";           .version // ""),
  kv("session_id";           .session_id // ""),
  kv("transcript_path";      .transcript_path // ""),
  kv("git_worktree";         .workspace.git_worktree // ""),
  kv("context_window_size";  .context_window.context_window_size // 0),
  kv("used_percentage";      .context_window.used_percentage // ""),
  kv("remaining_percentage"; .context_window.remaining_percentage // ""),
  kv("input_tokens";         .context_window.current_usage.input_tokens // 0),
  kv("cache_creation";       .context_window.current_usage.cache_creation_input_tokens // 0),
  kv("cache_read";           .context_window.current_usage.cache_read_input_tokens // 0),
  kv("output_tokens";        .context_window.current_usage.output_tokens // 0),
  kv("total_cost_usd";       .cost.total_cost_usd // 0),
  kv("five_hour_util";       .rate_limits.five_hour.used_percentage // ""),
  kv("five_hour_epoch";      .rate_limits.five_hour.resets_at // ""),
  kv("seven_day_util";       .rate_limits.seven_day.used_percentage // ""),
  kv("seven_day_epoch";      .rate_limits.seven_day.resets_at // "")
' <<< "$input" 2>/dev/null)

current_dir=${current_dir/#$HOME/\~}

# Current usage (per-turn token breakdown from the last API call)
current_context_tokens=$((input_tokens + cache_creation + cache_read))
cached_tokens=$cache_read
cache_written=$cache_creation
next_turn_new=$output_tokens
context_percentage=""

if [ "$current_context_tokens" -gt 0 ]; then
  if [ -n "$used_percentage" ]; then
    context_percentage=$(printf "%.0f" "$used_percentage" 2>/dev/null)
  elif [ "$context_window_size" -gt 0 ]; then
    context_percentage=$((current_context_tokens * 100 / context_window_size))
  fi
fi

[ -n "$five_hour_util" ] && five_hour_util=$(printf "%.0f" "$five_hour_util" 2>/dev/null)
[ -n "$seven_day_util" ] && seven_day_util=$(printf "%.0f" "$seven_day_util" 2>/dev/null)

five_hour_reset=""
if [ -n "$five_hour_epoch" ]; then
  now_epoch=$(date +%s)
  diff=$((five_hour_epoch - now_epoch))
  if [ "$diff" -gt 0 ]; then
    hours=$((diff / 3600)); mins=$(((diff % 3600) / 60))
    [ "$hours" -gt 0 ] && five_hour_reset="${hours}h ${mins}m" || five_hour_reset="${mins}m"
  fi
fi

seven_day_reset=""
if [ -n "$seven_day_epoch" ]; then
  now_epoch=${now_epoch:-$(date +%s)}
  diff=$((seven_day_epoch - now_epoch))
  if [ "$diff" -gt 0 ]; then
    days=$((diff / 86400)); hours=$(((diff % 86400) / 3600))
    [ "$days" -gt 0 ] && seven_day_reset="${days}d ${hours}h" || seven_day_reset="${hours}h"
  fi
fi

# ==========================================================================
# Git branch (cached) & worktree detection (from JSON)
# ==========================================================================

git_branch=""

if [ -n "$session_id" ]; then
  GIT_CACHE="/tmp/statusline-git-${session_id}"
  GIT_CACHE_TTL=5

  git_cache_stale() {
    [ ! -f "$GIT_CACHE" ] || [ $(($(date +%s) - $(file_mtime "$GIT_CACHE"))) -gt $GIT_CACHE_TTL ]
  }

  if git_cache_stale; then
    if git rev-parse --git-dir >/dev/null 2>&1; then
      git_branch=$(git branch --show-current 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
    fi
    echo "$git_branch" > "$GIT_CACHE"
  else
    git_branch=$(cat "$GIT_CACHE" 2>/dev/null)
  fi
else
  if git rev-parse --git-dir >/dev/null 2>&1; then
    git_branch=$(git branch --show-current 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
  fi
fi

# ==========================================================================
# Cache expiry (from main transcript only — not subagents)
# ==========================================================================
# Reads the last assistant message to determine the cache TTL in effect.
# Subagents use their own independent cache, so only the main transcript
# is relevant for the user's next prompt.

cache_expires=""
if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  # Claude Code appends the latest assistant turn to the transcript as the
  # statusline hook fires. If the transcript was written within the last
  # second, the write may still be flushing — sleep briefly so we read the
  # current turn's usage numbers, not the previous turn's. When the transcript
  # is already stable (idle refreshInterval tick, permission toggle, etc.)
  # skip the sleep to avoid blocking 1Hz timer ticks.
  now_epoch=${now_epoch:-$(date +%s)}
  tx_mtime=$(file_mtime "$transcript_path")
  [ $((now_epoch - tx_mtime)) -le 1 ] && sleep 1
  if [ "$IS_MACOS" -eq 1 ]; then
    last_assistant=$(tail -r "$transcript_path" | grep -m1 '"type":"assistant"')
  else
    last_assistant=$(tac "$transcript_path" | grep -m1 '"type":"assistant"')
  fi
  last_ts=$(echo "$last_assistant" | jq -r '.timestamp // empty' 2>/dev/null)
  if [ -n "$last_ts" ]; then
    last_epoch=$(parse_ts_to_epoch "$last_ts")
    now_epoch=${now_epoch:-$(date +%s)}
    if [ -n "$last_epoch" ]; then
      cache_5m=$(echo "$last_assistant" | jq -r '.message.usage.cache_creation.ephemeral_5m_input_tokens // 0' 2>/dev/null)
      cache_1h=$(echo "$last_assistant" | jq -r '.message.usage.cache_creation.ephemeral_1h_input_tokens // 0' 2>/dev/null)
      if [ "${cache_5m:-0}" -gt 0 ]; then
        cache_ttl=300
      elif [ "${cache_1h:-0}" -gt 0 ]; then
        cache_ttl=3600
      else
        cache_ttl=""
      fi
      if [ -n "$cache_ttl" ]; then
        expiry_epoch=$((last_epoch + cache_ttl))
        [ "$expiry_epoch" -gt "$now_epoch" ] && cache_expires=$(format_epoch "$expiry_epoch" "$TIME_FMT")
      fi
    fi
  fi
fi


# ==========================================================================
# Build output buffer
# ==========================================================================

OUT=""

# Debug line (only when DEBUG=1): shows session ID for cross-referencing
[ "$DEBUG" -eq 1 ] && [ -n "$session_id" ] && \
  OUT+="${C_GRAY}[id]${RST} ${C_GRAY}${session_id}${RST}"$'\n'

# --- Single line: ⏳ | 🤖 Model | 🧠 Context | 📦·✨ | 📁 Dir | 🌿 Branch [wt] ---

if [ -n "$cache_expires" ]; then
  OUT+="⏳ ${V_CACHE}${cache_expires}${RST}"
else
  OUT+="⏳ ${C_DIM}--${RST}"
fi
OUT+="${SEP}🤖 ${V_MODEL}${model_name}${RST}"

OUT+="${SEP}🧠 "
if [ "$current_context_tokens" -gt 0 ]; then
  [ -n "$context_percentage" ] && OUT+="$(make_progress_bar "$context_percentage" 10) "
  OUT+="${V_CTX}$(format_tokens "$current_context_tokens")${RST}${C_DIM}/${RST}${C_GRAY}$(format_tokens "$context_window_size")${RST}"
  if [ -n "$remaining_percentage" ]; then
    remaining_int=$(printf "%.0f" "$remaining_percentage" 2>/dev/null)
    [ "${remaining_int:-100}" -lt 30 ] && OUT+=" ${C_RED}⚠ ${remaining_int}%${RST}"
  fi
else
  OUT+="$(make_progress_bar 0 10) ${C_DIM}--/${RST}${C_GRAY}$(format_tokens "$context_window_size")${RST}"
fi

OUT+="${SEP}📦 ${V_CACHED}$(format_tokens "$cached_tokens")${RST}"
OUT+=" ${C_DIM}·${RST} ✨ ${V_NEW}$(format_tokens "$cache_written")${RST}"

OUT+="${SEP}📁 ${V_DIR}${current_dir}${RST}"
if [ -n "$git_branch" ]; then
  if [ -n "$git_worktree" ]; then
    OUT+="${SEP}🌿 ${V_GIT}${git_branch} ${C_DIM}[wt]${RST}"
  else
    OUT+="${SEP}🌿 ${V_GIT}${git_branch}${RST}"
  fi
fi

OUT+=$'\n'

# ==========================================================================
# Flush (single write prevents tearing when Claude Code redraws)
# ==========================================================================

printf '%s' "$OUT"
exit 0
