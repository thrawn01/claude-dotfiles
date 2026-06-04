#!/usr/bin/env python3
"""Parse an edited standup markdown report into per-ticket Linear comment payloads.

The standup report (`~/Notes/<YYYY-MM>/standup-<date>.md`, produced by the `standup`
skill) is the human-editable source of truth: the user edits wording or DELETES whole
`##` sections before this runs, and those edits ARE the review gate — which is why there
is no dry-run. This script does no network I/O and needs no credentials; it only turns
the (possibly edited) markdown back into structured `{domId, body}` payloads. The
`standup-to-linear` skill consumes that JSON and posts each via the Linear MCP.

Contract:
  python3 parse_report.py <report.md>   -> JSON on stdout

Output:
  {
    "report": "<path>",
    "date":   "YYYY-MM-DD",            # from the window header, for the comment title
    "window": {"since": "...", "now": "..."},
    "comments": [ {"domId", "status", "title", "body"} ]   # report order
  }

Parsing rules (deliberately lenient — the input may be hand-edited):
  - A ticket section is a `## ` heading containing a Linear identifier (e.g. DOM-1546),
    in either `## DOM-1546 · title (Status)` or `## [DOM-1546](url) · title (Status)` form.
  - `## ` headings with NO identifier (e.g. `## Other PRs`, `## Meetings / Notes`) are
    skipped — they have no ticket to comment on.
  - The body is the `  - ` bullets beneath the heading, up to the next `## ` (or EOF).
    The first bullet (the arc summary) is promoted to a lead paragraph; the rest stay
    as a bullet list. A section with no bullets is skipped (nothing to say).
"""

import json
import re
import sys

# A Linear issue identifier: 2+ uppercase letters/digits, a hyphen, then digits.
_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
# Trailing "(Status)" at the very end of a heading line.
_STATUS_RE = re.compile(r"\(([^()]*)\)\s*$")
# Window header: "# Standup [<since> … <now>]" (the separator is a unicode ellipsis).
_WINDOW_RE = re.compile(r"^#\s+Standup\s+\[(.+?)\s*…\s*(.+?)\]\s*$")


def _heading_title(heading, dom_id, status):
    """Best-effort human title from a heading line, for labelling only."""
    text = heading.lstrip("#").strip()
    if status:
        text = _STATUS_RE.sub("", text).strip()
    # Drop a leading "[ID](url) · " or "ID · " prefix.
    if "·" in text:
        text = text.split("·", 1)[1].strip()
    return text


def _strip_self_reference(text, dom_id):
    """The comment is posted ON `dom_id`, so naming its own identifier in the body is
    redundant. Replace a standalone self-reference with 'this ticket' and tidy up the
    grammar that produces (doubled 'ticket', collapsed spaces). Cross-references to
    OTHER tickets are left intact — only the comment's own id is rewritten."""
    if not text or not dom_id:
        return text
    out = re.sub(r"\b" + re.escape(dom_id) + r"\b", "this ticket", text)
    out = re.sub(r"\bthis ticket ticket\b", "this ticket", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out


def _build_body(date, bullets):
    """Comment markdown: a dated header, the summary as a lead line, rest as bullets."""
    header = "**Standup · {}**".format(date) if date else "**Standup**"
    if not bullets:
        return header
    lead, rest = bullets[0], bullets[1:]
    parts = [header, "", lead]
    if rest:
        parts.append("")
        parts.extend("- " + b for b in rest)
    return "\n".join(parts)


def parse_report(text, report_path=""):
    lines = text.splitlines()

    since = now = date = ""
    for line in lines:
        m = _WINDOW_RE.match(line)
        if m:
            since, now = m.group(1).strip(), m.group(2).strip()
            date = now[:10]  # YYYY-MM-DD
            break

    comments = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.startswith("## "):
            i += 1
            continue
        heading = line
        # Collect this section's body bullets until the next "## " heading.
        i += 1
        bullets = []
        while i < n and not lines[i].startswith("## "):
            stripped = lines[i].strip()
            if stripped.startswith("- "):
                bullets.append(stripped[2:].strip())
            i += 1

        m = _ID_RE.search(heading)
        if not m:
            continue  # e.g. "Other PRs", "Meetings / Notes" — no ticket to comment on
        if not bullets:
            continue  # nothing to say
        dom_id = m.group(1)
        sm = _STATUS_RE.search(heading)
        status = sm.group(1).strip() if sm else None
        comments.append({
            "domId": dom_id,
            "status": status,
            "title": _heading_title(heading, dom_id, status),
            "body": _strip_self_reference(_build_body(date, bullets), dom_id),
        })

    return {
        "report": report_path,
        "date": date,
        "window": {"since": since, "now": now},
        "comments": comments,
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: parse_report.py <report.md>\n")
        return 2
    path = argv[1]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    json.dump(parse_report(text, path), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
