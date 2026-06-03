"""Standup pipeline: merge + formatters + deliver.

Implements the locked data contract at skills/standup/CONTRACT.md sections 5, 7, 8.
Python 3.11, standard library only.

The surface of this module is its exported functions:
  derive_dom_id, merge, format_range, format_report, report_path, deliver
and the module-level tunables MAX_TURNS / MAX_CHARS_PER_TURN.
"""

import os
import re

# Named tunable constants bounding human-turn inclusion at merge time
# (blueprint Data Design: "a named tunable constant ... a max-turns count and a
# max-chars-per-turn limit"). Any value preserves the token-budget and
# never-fabricate properties since truncation only shortens existing text.
MAX_TURNS = 3
MAX_CHARS_PER_TURN = 280

_DOM_RE = re.compile(r"dom-(\d+)", re.IGNORECASE)


def derive_dom_id(branch):
    """Derive a DOM-id from a branch name, or None.

    "derrickwippler/dom-1608-..." -> "DOM-1608"; case-insensitive match of
    dom-<digits>. Returns None when branch is falsy or has no dom-id.
    """
    if not branch:
        return None
    m = _DOM_RE.search(branch)
    if not m:
        return None
    return "DOM-" + m.group(1)


def _max_ts(*values):
    """Return the lexicographically-greatest non-empty RFC3339 string, or None.

    RFC3339 in a consistent (Z) form sorts lexicographically by time, which is
    what the contract relies on for lastActivity.
    """
    candidates = [v for v in values if v]
    if not candidates:
        return None
    return max(candidates)


def _title_from_branch(branch, dom_id):
    """Derive a title from branch text after the dom-id (hyphens -> spaces)."""
    if branch:
        m = _DOM_RE.search(branch)
        if m:
            tail = branch[m.end():]
            tail = tail.lstrip("-/ ")
            tail = tail.replace("-", " ").strip()
            if tail:
                return tail
    return dom_id


def merge(sessions, github, linear, notes, window):
    """Union sessions + PRs + Linear issues on domId into ticket buckets.

    See CONTRACT.md section 5. Returns:
      {"window": window, "tickets": [Bucket], "otherPRs": [PR], "notes": [...]}.

    Buckets are only ever keyed by a non-empty domId (illegal state by
    construction). Orphan PRs route to otherPRs; orphan notes to notes.
    """
    sessions = sessions or []
    github = github or {}
    linear = linear or {}
    notes = notes or []

    prs = github.get("prs", []) or []
    commits = github.get("commits", []) or []
    issues = (linear.get("issues") if isinstance(linear, dict) else None) or []
    note_items = notes.get("notes", notes) if isinstance(notes, dict) else notes
    note_items = note_items or []

    buckets = {}
    other_prs = []

    def ensure(dom_id):
        # Illegal state by construction: never create a bucket without a domId.
        if not dom_id:
            raise ValueError("cannot create a ticket bucket without a domId")
        if dom_id not in buckets:
            buckets[dom_id] = {
                "domId": dom_id,
                "title": None,
                "status": None,
                "url": None,
                "prs": [],
                "commits": [],
                "ciEvents": [],
                "humanTurns": [],
                "noPR": True,
                "lastActivity": None,
                "_ts": [],
                "_branch": None,
                "_sessionTurns": [],
            }
        return buckets[dom_id]

    # PRs: those with a dom-id join a bucket; orphans -> otherPRs (never a ticket).
    for pr in prs:
        dom_id = pr.get("domId") or derive_dom_id(pr.get("branch"))
        if not dom_id:
            other_prs.append(pr)
            continue
        b = ensure(dom_id)
        b["prs"].append(pr)
        if b["_branch"] is None:
            b["_branch"] = pr.get("branch")

    # Commits with a dom-id attach their subject string to the bucket.
    for c in commits:
        dom_id = c.get("domId") or derive_dom_id(c.get("branch"))
        if not dom_id:
            continue
        b = ensure(dom_id)
        b["commits"].append(c.get("subject", ""))

    # Linear issues: provide title/status/url and discovery; an in-window issue
    # with no branch/PR becomes its own bucket with noPR=true, prs=[].
    for issue in issues:
        dom_id = issue.get("domId")
        if not dom_id:
            continue
        b = ensure(dom_id)
        b["status"] = issue.get("status")
        b["url"] = issue.get("url")
        if issue.get("title"):
            b["title"] = issue.get("title")
        b["_ts"].append(issue.get("updatedAt"))

    # Sessions: attach CI events and timestamps to matching-domId buckets; keep
    # human turns for later (attached only to no-PR/no-commit buckets).
    for s in sessions:
        dom_id = s.get("domId") or derive_dom_id(s.get("branch"))
        if not dom_id:
            continue
        b = ensure(dom_id)
        if b["_branch"] is None:
            b["_branch"] = s.get("branch")
        for ev in s.get("ciEvents", []) or []:
            b["ciEvents"].append(ev)
        b["_ts"].append(s.get("firstTs"))
        b["_ts"].append(s.get("lastTs"))
        for turn in s.get("humanTurns", []) or []:
            b["_sessionTurns"].append(turn)

    # Finalize each bucket.
    for b in buckets.values():
        has_pr = bool(b["prs"])
        has_commit = bool(b["commits"])
        b["noPR"] = not has_pr
        # humanTurns ONLY when no PR and no commit; bounded and truncated.
        if not has_pr and not has_commit:
            turns = b["_sessionTurns"][:MAX_TURNS]
            b["humanTurns"] = [t[:MAX_CHARS_PER_TURN] for t in turns]
        else:
            b["humanTurns"] = []
        # Title: Linear title if present, else from branch text, else domId.
        if not b["title"]:
            b["title"] = _title_from_branch(b["_branch"], b["domId"])
        b["lastActivity"] = _max_ts(*b["_ts"])
        del b["_ts"]
        del b["_branch"]
        del b["_sessionTurns"]

    tickets = list(buckets.values())
    # Order by lastActivity descending (most recent first); None sorts last.
    tickets.sort(key=lambda t: (t["lastActivity"] or ""), reverse=True)

    return {
        "window": window,
        "tickets": tickets,
        "otherPRs": other_prs,
        "notes": note_items,
    }


# --------------------------------------------------------------------------- #
# Formatters
# --------------------------------------------------------------------------- #

def _commit_subject(c):
    """A bucket commit may be a plain string or a {subject, domId} object."""
    if isinstance(c, dict):
        return c.get("subject", "")
    return c


def _ticket_sub_bullets(ticket):
    """Indented '  - ' sub-bullets for a ticket: summary, CI, commits, PRs."""
    lines = []
    summary = ticket.get("summary")
    if summary:
        lines.append("  - " + summary)
    for ev in ticket.get("ciEvents", []) or []:
        pipeline = ev.get("pipeline")
        fail = ev.get("failCount")
        lines.append(
            "  - CI: {} failed {}× before passing.".format(pipeline, fail)
        )
    for c in ticket.get("commits", []) or []:
        subject = _commit_subject(c)
        if subject:
            lines.append("  - commit: " + subject)
    for pr in ticket.get("prs", []) or []:
        state = (pr.get("state") or "").lower()
        lines.append(
            "  - PR [#{}]({}) {}".format(pr.get("number"), pr.get("url"), state)
        )
    return lines


def _status_label(ticket):
    """Heading label for a ticket. A null Linear status must NOT be read as 'no PR'
    (dogfooding bug): only a genuinely PR-less ticket is 'no PR'. When there is a PR
    but no Linear status, reflect the PR state instead of inventing one."""
    status = ticket.get("status")
    if status:
        return status
    if ticket.get("noPR"):
        return "no PR"
    states = [(pr.get("state") or "").upper() for pr in ticket.get("prs", []) or []]
    if "MERGED" in states:
        return "Merged"
    if "OPEN" in states:
        return "Open"
    return "—"


def _ticket_bold_line(ticket):
    dom_id = ticket.get("domId")
    url = ticket.get("url")
    title = ticket.get("title")
    status_text = _status_label(ticket)
    if url:
        head = "**[{}]({}) · {}**".format(dom_id, url, title)
    else:
        head = "**{} · {}**".format(dom_id, title)
    return "{} — {}".format(head, status_text)


def format_range(narrated):
    """Render the golden Range clipboard format (CONTRACT.md section 7)."""
    groups = []
    for ticket in narrated.get("tickets", []) or []:
        block = [_ticket_bold_line(ticket)] + _ticket_sub_bullets(ticket)
        groups.append("\n".join(block))

    other_prs = narrated.get("otherPRs", []) or []
    if other_prs:
        block = ["**Other PRs**"]
        os_summary = narrated.get("otherPRsSummary")
        if os_summary:
            block.append("  - " + os_summary)
        for pr in other_prs:
            state = (pr.get("state") or "").lower()
            block.append(
                "  - PR [#{}]({}) {} — {}".format(
                    pr.get("number"), pr.get("url"), state, pr.get("title")
                )
            )
        groups.append("\n".join(block))

    notes = narrated.get("notes", []) or []
    if notes:
        block = ["**Meetings / Notes**"]
        notes_summary = narrated.get("notesSummary")
        if notes_summary:
            block.append("  - " + notes_summary)
        for n in notes:
            block.append("  - {}: {}".format(n.get("date"), n.get("text")))
        groups.append("\n".join(block))

    return "\n\n".join(groups) + "\n"


def format_report(narrated):
    """Render the full markdown report (CONTRACT.md section 8).

    Begins with a window header carrying BOTH window.since and window.now
    verbatim (Invariant #2). Never introduces facts absent from the input.
    """
    window = narrated.get("window", {}) or {}
    since = window.get("since", "")
    now = window.get("now", "")

    lines = []
    lines.append("# Standup [{} … {}]".format(since, now))
    lines.append("")

    for ticket in narrated.get("tickets", []) or []:
        dom_id = ticket.get("domId")
        title = ticket.get("title")
        status = _status_label(ticket)
        url = ticket.get("url")
        if url:
            heading = "## [{}]({}) · {} — {}".format(
                dom_id, url, title, status
            )
        else:
            heading = "## {} · {} — {}".format(dom_id, title, status)
        lines.append(heading)
        lines.append("")
        # The narrated summary leads the sub-bullets (see _ticket_sub_bullets),
        # so it is not repeated as a separate paragraph here.
        for sub in _ticket_sub_bullets(ticket):
            lines.append(sub)
        lines.append("")

    other_prs = narrated.get("otherPRs", []) or []
    if other_prs:
        lines.append("## Other PRs")
        os_summary = narrated.get("otherPRsSummary")
        if os_summary:
            lines.append("")
            lines.append(os_summary)
        for pr in other_prs:
            state = (pr.get("state") or "").lower()
            lines.append(
                "  - PR [#{}]({}) {} — {}".format(
                    pr.get("number"), pr.get("url"), state, pr.get("title")
                )
            )
        lines.append("")

    notes = narrated.get("notes", []) or []
    if notes:
        lines.append("## Meetings / Notes")
        notes_summary = narrated.get("notesSummary")
        if notes_summary:
            lines.append("")
            lines.append(notes_summary)
        for n in notes:
            lines.append("  - {}: {}".format(n.get("date"), n.get("text")))
        lines.append("")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Delivery
# --------------------------------------------------------------------------- #

def report_path(notes_dir, now):
    """notes_dir/<YYYY-MM>/standup-<YYYY-MM-DD>.md. now is RFC3339 (tolerate Z)."""
    date_part = now[:10]  # YYYY-MM-DD
    year_month = now[:7]  # YYYY-MM
    return os.path.join(notes_dir, year_month, "standup-{}.md".format(date_part))


def deliver(notes_dir, now, report_md, range_text, clipboard_cmd, last_run_path):
    """Write report, copy range text, then advance last_run (CONTRACT.md section 8).

    Order (Invariant #1): (1) ensure month dir, (2) write report, (3) clipboard,
    (4) ONLY THEN write last_run. Any error before step 4 propagates and leaves
    last_run_path unchanged. Idempotent for a window (overwrites the dated file).
    """
    path = report_path(notes_dir, now)

    # (1) ensure the month directory exists.
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # (2) write the report to the dated file.
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # (3) clipboard: call injected cmd, or set the copy fence when absent.
    copy_fence = False
    clipboard_ok = False
    if clipboard_cmd is not None:
        clipboard_cmd(range_text)
        clipboard_ok = True
    else:
        copy_fence = True

    # (4) only now advance last_run.
    with open(last_run_path, "w", encoding="utf-8") as f:
        f.write(now)

    return {
        "report_path": path,
        "copy_fence": copy_fence,
        "clipboard_ok": clipboard_ok,
    }
