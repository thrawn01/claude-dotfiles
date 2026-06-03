#!/usr/bin/env python3
"""Thin CLI wrapper around standuplib for the narrate -> deliver step.

Used by the /standup skill in production. Reads the narrated buckets JSON
(--narrated), renders the markdown report and the Range clipboard text, writes the
report to ~/Notes/<YYYY-MM>/standup-<YYYY-MM-DD>.md, copies the Range text to the
clipboard via the first available tool (wl-copy -> xclip -> xsel), and only then
advances --last-run (CONTRACT.md section 8 / Invariant #1).

Usage:
  deliver.py --narrated narrated.json --notes-dir ~/Notes \
             --now 2026-06-03T00:00:00Z --last-run ~/Notes/.standup-last-run
"""

import argparse
import json
import shutil
import subprocess
import sys

import standuplib

# Clipboard tools in preference order: Wayland first, then X11 fallbacks.
_CLIPBOARD_TOOLS = [
    ["wl-copy"],
    ["xclip", "-selection", "clipboard"],
    ["xsel", "--clipboard", "--input"],
]


def _resolve_clipboard():
    """Return a callable(text) using the first available clipboard tool, or None."""
    for cmd in _CLIPBOARD_TOOLS:
        if shutil.which(cmd[0]):
            def copy(text, _cmd=cmd):
                # Suppress the tool's own stderr (e.g. xclip's "Can't open
                # display"); the failure is reported via the copy-fence instead.
                subprocess.run(
                    _cmd,
                    input=text.encode("utf-8"),
                    check=True,
                    stderr=subprocess.DEVNULL,
                )
            return copy
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description="Render and deliver the standup report")
    p.add_argument("--narrated", required=True)
    p.add_argument("--notes-dir", required=True)
    p.add_argument("--now", required=True)
    p.add_argument("--last-run", required=True)
    args = p.parse_args(argv)

    with open(args.narrated, encoding="utf-8") as f:
        narrated = json.load(f)

    report_md = standuplib.format_report(narrated)
    range_text = standuplib.format_range(narrated)
    clipboard_cmd = _resolve_clipboard()

    # Clipboard is an enrichment side effect (blueprint Behavioral Constraint 3):
    # a missing OR non-functional clipboard tool degrades to a copy fence, never a
    # crash, while the report write + last-run advance (Invariant #1) still proceed.
    # Wrap the resolved tool so a runtime failure (e.g. no display) is swallowed and
    # recorded, then expose that outcome via the printed fence below. We still pass
    # None to deliver when no tool exists so deliver sets copy_fence itself.
    clip_failed = {"value": False}
    if clipboard_cmd is not None:
        real_copy = clipboard_cmd

        def safe_copy(text):
            try:
                real_copy(text)
            except Exception:
                clip_failed["value"] = True

        clipboard_cmd = safe_copy

    result = standuplib.deliver(
        args.notes_dir,
        args.now,
        report_md,
        range_text,
        clipboard_cmd,
        args.last_run,
    )

    if clip_failed["value"]:
        # Tool was present but failed at runtime: treat as a fence, not a success.
        result["clipboard_ok"] = False
        result["copy_fence"] = True

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    # Always emit the Range fence so there is a single, consistent copy source in
    # chat regardless of whether a clipboard tool was present or worked. The header
    # only reflects whether the text was ALSO copied to the clipboard.
    if result.get("clipboard_ok"):
        header = "\nAlso copied to your clipboard. Range text:\n"
    else:
        header = "\nNo clipboard tool available; copy the Range text below:\n"
    sys.stdout.write(header)
    sys.stdout.write("```\n")
    sys.stdout.write(range_text)
    if not range_text.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.write("```\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
