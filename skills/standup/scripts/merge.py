#!/usr/bin/env python3
"""Thin CLI wrapper around standuplib.merge.

Reads collector JSON from --sessions/--github/--linear/--notes file paths and the
window from --since/--now, then prints buckets.json to stdout (CONTRACT.md section 5).

Usage:
  merge.py --sessions s.json --github g.json --linear l.json --notes n.json \
           --since 2026-06-02T00:00:00Z --now 2026-06-03T00:00:00Z
"""

import argparse
import json
import sys

import standuplib


def _load(path, default):
    if not path:
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    p = argparse.ArgumentParser(description="Merge collector outputs into buckets.json")
    p.add_argument("--sessions")
    p.add_argument("--github")
    p.add_argument("--linear")
    p.add_argument("--notes")
    p.add_argument("--since", required=True)
    p.add_argument("--now", required=True)
    args = p.parse_args(argv)

    sessions = _load(args.sessions, [])
    github = _load(args.github, {})
    linear = _load(args.linear, {})
    notes = _load(args.notes, {"notes": []})
    window = {"since": args.since, "now": args.now}

    buckets = standuplib.merge(sessions, github, linear, notes, window)
    json.dump(buckets, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
