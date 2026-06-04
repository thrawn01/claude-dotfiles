"""Surface tests for standuplib (CONTRACT.md sections 5, 7, 8; blueprint AC/constraints).

Tests exercise the exported library functions directly — that IS the surface for a
library per the surface-testing skill. No private helpers are touched. Fixtures live
under ../testdata, resolved via __file__. Standard library + unittest only.
"""

import json
import os
import re
import tempfile
import unittest

import standuplib
from standuplib import (
    MAX_TURNS,
    MAX_CHARS_PER_TURN,
    derive_dom_id,
    merge,
    format_range,
    format_report,
    report_path,
    deliver,
)

HERE = os.path.dirname(os.path.abspath(__file__))
TESTDATA = os.path.join(HERE, "..", "testdata")

WINDOW = {"since": "2026-06-02T00:00:00Z", "now": "2026-06-03T00:00:00Z"}


def load(*parts):
    with open(os.path.join(TESTDATA, *parts), encoding="utf-8") as f:
        return json.load(f)


def find_ticket(buckets, dom_id):
    for t in buckets["tickets"]:
        if t["domId"] == dom_id:
            return t
    return None


# Session digests constructed in-test from CONTRACT section 1 shapes.
def dom1608_session():
    # Has CI events + actions; matches the merged PR's domId.
    return {
        "branch": "derrickwippler/dom-1608-golangci-lint-shards-failing-in-ci",
        "domId": "DOM-1608",
        "firstTs": "2026-06-02T09:00:00Z",
        "lastTs": "2026-06-02T12:00:00Z",
        "msgCount": 40,
        "humanTurns": ["please fix the lint shards"],
        "ciEvents": [{"pipeline": "golangci-lint", "failCount": 3}],
        "actions": ["git push", "gh pr merge"],
    }


def dom1700_session():
    # Session-only: no PR, no commit; carries a human turn.
    return {
        "branch": "derrickwippler/dom-1700-investigate-something",
        "domId": "DOM-1700",
        "firstTs": "2026-06-02T15:00:00Z",
        "lastTs": "2026-06-02T16:00:00Z",
        "msgCount": 10,
        "humanTurns": ["help me investigate the offchain panic"],
        "ciEvents": [],
        "actions": [],
    }


class DeriveDomIdTest(unittest.TestCase):
    def test_derives_uppercase_dom_id(self):
        self.assertEqual(
            derive_dom_id("derrickwippler/dom-1608-golangci-lint"), "DOM-1608"
        )

    def test_case_insensitive(self):
        self.assertEqual(derive_dom_id("foo/DOM-42-bar"), "DOM-42")

    def test_none_when_no_dom_id(self):
        self.assertIsNone(derive_dom_id("derrickwippler/chore-bump-deps"))

    def test_none_for_empty(self):
        self.assertIsNone(derive_dom_id(None))
        self.assertIsNone(derive_dom_id(""))


class MergeTest(unittest.TestCase):
    def setUp(self):
        self.github = load("github", "github.json")
        self.linear = load("linear", "linear.json")
        self.notes = load("notes", "notes.json")
        self.sessions = [dom1608_session(), dom1700_session()]
        self.buckets = merge(
            self.sessions, self.github, self.linear, self.notes, WINDOW
        )

    def test_window_echoed_verbatim(self):
        self.assertEqual(self.buckets["window"], WINDOW)

    def test_one_ticket_per_qualifying_dom_id(self):
        ids = [t["domId"] for t in self.buckets["tickets"]]
        # No duplicates.
        self.assertEqual(len(ids), len(set(ids)))
        # Every qualifying domId present exactly once.
        for expected in ("DOM-1608", "DOM-1597", "DOM-1900", "DOM-1700"):
            self.assertEqual(ids.count(expected), 1, expected)

    def test_tickets_ordered_by_last_activity_desc(self):
        acts = [t["lastActivity"] for t in self.buckets["tickets"]]
        self.assertEqual(acts, sorted(acts, reverse=True))

    def test_dom1608_has_pr_and_ci_and_empty_human_turns(self):
        t = find_ticket(self.buckets, "DOM-1608")
        self.assertEqual(len(t["prs"]), 1)
        self.assertEqual(t["prs"][0]["number"], 206941)
        self.assertEqual(t["prs"][0]["state"], "MERGED")
        self.assertIn({"pipeline": "golangci-lint", "failCount": 3}, t["ciEvents"])
        # Has a PR, so humanTurns must be empty.
        self.assertEqual(t["humanTurns"], [])
        self.assertFalse(t["noPR"])

    def test_orphan_pr_in_other_prs_and_no_ticket(self):
        other_numbers = [pr["number"] for pr in self.buckets["otherPRs"]]
        self.assertIn(206800, other_numbers)
        for t in self.buckets["tickets"]:
            for pr in t["prs"]:
                self.assertNotEqual(pr["number"], 206800)

    def test_linear_only_ticket_is_own_bucket_no_pr(self):
        t = find_ticket(self.buckets, "DOM-1900")
        self.assertIsNotNone(t)
        self.assertTrue(t["noPR"])
        self.assertEqual(t["prs"], [])

    def test_session_only_ticket_carries_bounded_human_turns(self):
        t = find_ticket(self.buckets, "DOM-1700")
        self.assertIsNotNone(t)
        self.assertTrue(t["noPR"])
        self.assertEqual(t["prs"], [])
        self.assertTrue(len(t["humanTurns"]) >= 1)
        self.assertEqual(
            t["humanTurns"][0], "help me investigate the offchain panic"
        )

    def test_dom1597_commits_attached_and_no_human_turns(self):
        t = find_ticket(self.buckets, "DOM-1597")
        self.assertEqual(len(t["commits"]), 2)
        # Has a PR + commits, so no human turns.
        self.assertEqual(t["humanTurns"], [])

    def test_title_from_linear_when_present(self):
        t = find_ticket(self.buckets, "DOM-1597")
        self.assertEqual(t["title"], "custody migration")


class IllegalStateTest(unittest.TestCase):
    def test_every_bucket_keyed_by_nonempty_dom_id_and_orphan_absent(self):
        github = load("github", "github.json")
        linear = load("linear", "linear.json")
        notes = load("notes", "notes.json")
        buckets = merge(
            [dom1608_session(), dom1700_session()], github, linear, notes, WINDOW
        )
        for t in buckets["tickets"]:
            self.assertTrue(t["domId"])
            self.assertRegex(t["domId"], r"^DOM-\d+$")
        # The orphan chore PR (206800) appears in no ticket bucket.
        for t in buckets["tickets"]:
            self.assertNotIn(206800, [pr["number"] for pr in t["prs"]])


class BoundedHumanTurnsTest(unittest.TestCase):
    def test_human_turns_bounded_and_truncated(self):
        long_turn = "x" * (MAX_CHARS_PER_TURN + 500)
        session = {
            "branch": "derrickwippler/dom-2000-noisy",
            "domId": "DOM-2000",
            "firstTs": "2026-06-02T10:00:00Z",
            "lastTs": "2026-06-02T11:00:00Z",
            "msgCount": 100,
            "humanTurns": [long_turn] * (MAX_TURNS + 5),
            "ciEvents": [],
            "actions": [],
        }
        buckets = merge([session], {}, {}, {}, WINDOW)
        t = find_ticket(buckets, "DOM-2000")
        self.assertIsNotNone(t)
        self.assertLessEqual(len(t["humanTurns"]), MAX_TURNS)
        for turn in t["humanTurns"]:
            self.assertLessEqual(len(turn), MAX_CHARS_PER_TURN)
        # Truncation only shortens existing text: each kept turn is a prefix.
        for turn in t["humanTurns"]:
            self.assertTrue(long_turn.startswith(turn))


class FormatRangeTest(unittest.TestCase):
    def setUp(self):
        self.narrated = load("narrated", "narrated.json")
        self.out = format_range(self.narrated)

    def test_dom1608_bold_line(self):
        self.assertIn(
            "**[DOM-1608](https://linear.app/anchorage/issue/DOM-1608) · "
            "golangci-lint shards** (Done)",
            self.out,
        )

    def test_dom1608_ci_sub_bullet(self):
        self.assertIn("  - CI: golangci-lint failed 3× before passing", self.out)

    def test_commit_subjects_never_enumerated(self):
        # Commits inform the summary only; raw subjects must never be rendered.
        self.assertNotIn("  - commit:", self.out)

    def test_dom1597_commit_count_collapsed(self):
        # 2 commits, no CI → a single collapsed stats line, not per-commit bullets.
        self.assertIn("  - 2 commits", self.out)

    def test_dom1608_pr_sub_bullet(self):
        self.assertIn(
            "  - PR [#206941](https://github.com/anchorlabsinc/anchorage/"
            "pull/206941) merged",
            self.out,
        )

    def test_dom1597_group_present(self):
        self.assertIn(
            "**[DOM-1597](https://linear.app/anchorage/issue/DOM-1597) · "
            "custody migration** (In Review)",
            self.out,
        )

    def test_other_prs_group_header(self):
        self.assertIn("**Other PRs**", self.out)

    def test_meetings_notes_group_header(self):
        self.assertIn("**Meetings / Notes**", self.out)

    def test_no_punctuation_dashes_anywhere(self):
        # Em/en dashes are banned report-wide; status sits in parens, not after a dash.
        self.assertNotIn("—", self.out)
        self.assertNotIn("–", self.out)
        # No spaced-hyphen clause break (the markdown bullet marker is "  - " at line
        # start, which is not a clause break between two words).
        for line in self.out.splitlines():
            body = line.lstrip()
            if body.startswith("- "):
                body = body[2:]
            self.assertNotIn(" - ", body, "stray dash clause break: %r" % line)


class NoDashesTest(unittest.TestCase):
    def test_em_and_en_dash_become_semicolon(self):
        from standuplib import _no_dashes
        self.assertEqual(_no_dashes("got it green — mostly CI"), "got it green; mostly CI")
        self.assertEqual(_no_dashes("a–b"), "a; b")

    def test_spaced_hyphen_clause_break_rewritten(self):
        from standuplib import _no_dashes
        self.assertEqual(_no_dashes("shipped X - moved on"), "shipped X; moved on")

    def test_identifiers_and_urls_preserved(self):
        from standuplib import _no_dashes
        self.assertEqual(_no_dashes("fixed DOM-1546 verify-generate"),
                         "fixed DOM-1546 verify-generate")


class FormatReportTest(unittest.TestCase):
    def setUp(self):
        self.narrated = load("narrated", "narrated.json")
        self.out = format_report(self.narrated)

    def test_window_header_contains_both_since_and_now(self):
        # Invariant #2: header equals the window actually queried.
        self.assertIn(self.narrated["window"]["since"], self.out)
        self.assertIn(self.narrated["window"]["now"], self.out)
        # Both appear before any ticket section heading.
        header_region = self.out.split("##", 1)[0]
        self.assertIn(self.narrated["window"]["since"], header_region)
        self.assertIn(self.narrated["window"]["now"], header_region)

    def test_one_section_per_ticket(self):
        for dom_id in ("DOM-1608", "DOM-1597", "DOM-1900"):
            self.assertIn(dom_id, self.out)

    def test_other_prs_and_notes_sections(self):
        self.assertIn("Other PRs", self.out)
        self.assertIn("Meetings / Notes", self.out)

    def test_never_fabricates_dom_ids(self):
        # Behavioral Constraint 1: every DOM-id token in the output must be
        # present in the narrated input.
        input_blob = json.dumps(self.narrated)
        input_ids = set(re.findall(r"DOM-\d+", input_blob))
        output_ids = set(re.findall(r"DOM-\d+", self.out))
        self.assertTrue(output_ids)
        for oid in output_ids:
            self.assertIn(oid, input_ids)


class StatusLabelTest(unittest.TestCase):
    """Regression (dogfooding): a null Linear status must not be rendered as 'no PR'
    when the ticket actually has a PR."""

    def _narrated(self, ticket):
        return {
            "window": {"since": "2026-06-02T00:00:00Z", "now": "2026-06-03T00:00:00Z"},
            "tickets": [ticket],
            "otherPRs": [],
            "notes": [],
        }

    def test_pr_with_null_status_not_labeled_no_pr(self):
        ticket = {
            "domId": "DOM-1553", "title": "ci determinism", "status": None,
            "url": None, "noPR": False, "summary": "Pushed a commit.",
            "prs": [{"number": 206001, "url": "https://gh/206001", "state": "OPEN"}],
            "commits": [], "ciEvents": [], "humanTurns": [],
            "lastActivity": "2026-06-02T12:00:00Z",
        }
        for out in (format_report(self._narrated(ticket)),
                    format_range(self._narrated(ticket))):
            self.assertNotIn("no PR", out)
            self.assertIn("Open", out)

    def test_genuinely_pr_less_ticket_labeled_no_pr(self):
        ticket = {
            "domId": "DOM-1900", "title": "investigate", "status": None,
            "url": None, "noPR": True, "summary": "Looked into it.",
            "prs": [], "commits": [], "ciEvents": [], "humanTurns": [],
            "lastActivity": "2026-06-02T12:00:00Z",
        }
        self.assertIn("no PR", format_report(self._narrated(ticket)))


class ReportPathTest(unittest.TestCase):
    def test_path_shape(self):
        p = report_path("/tmp/Notes", "2026-06-03T00:00:00Z")
        self.assertEqual(p, "/tmp/Notes/2026-06/standup-2026-06-03.md")

    def test_tolerates_trailing_z(self):
        p = report_path("/n", "2026-06-03T12:34:56Z")
        self.assertTrue(p.endswith("2026-06/standup-2026-06-03.md"))


class DeliverTest(unittest.TestCase):
    def test_success_writes_report_clipboard_and_last_run(self):
        # Invariant #1 success path.
        with tempfile.TemporaryDirectory() as d:
            notes_dir = os.path.join(d, "Notes")
            last_run = os.path.join(d, ".last-run")
            captured = []

            def clip(text):
                captured.append(text)

            now = "2026-06-03T00:00:00Z"
            result = deliver(
                notes_dir, now, "REPORT BODY", "RANGE TEXT", clip, last_run
            )

            expected_path = os.path.join(
                notes_dir, "2026-06", "standup-2026-06-03.md"
            )
            self.assertEqual(result["report_path"], expected_path)
            self.assertTrue(os.path.exists(expected_path))
            with open(expected_path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "REPORT BODY")
            self.assertEqual(captured, ["RANGE TEXT"])
            self.assertTrue(result["clipboard_ok"])
            self.assertFalse(result["copy_fence"])
            with open(last_run, encoding="utf-8") as f:
                self.assertEqual(f.read(), now)

    def test_abort_before_step4_leaves_last_run_unchanged(self):
        # Invariant #1 abort path: force a failure before last_run is written.
        with tempfile.TemporaryDirectory() as d:
            notes_dir = os.path.join(d, "Notes")
            last_run = os.path.join(d, ".last-run")
            old_ts = "2020-01-01T00:00:00Z"
            with open(last_run, "w", encoding="utf-8") as f:
                f.write(old_ts)

            # Place a regular FILE where the YYYY-MM directory must be created,
            # so makedirs/open raises before step 4.
            os.makedirs(notes_dir)
            blocker = os.path.join(notes_dir, "2026-06")
            with open(blocker, "w", encoding="utf-8") as f:
                f.write("not a dir")

            with self.assertRaises(OSError):
                deliver(
                    notes_dir,
                    "2026-06-03T00:00:00Z",
                    "REPORT BODY",
                    "RANGE TEXT",
                    None,
                    last_run,
                )

            # last_run did NOT advance.
            with open(last_run, encoding="utf-8") as f:
                self.assertEqual(f.read(), old_ts)

    def test_clipboard_none_sets_copy_fence_and_still_writes_report(self):
        with tempfile.TemporaryDirectory() as d:
            notes_dir = os.path.join(d, "Notes")
            last_run = os.path.join(d, ".last-run")
            now = "2026-06-03T00:00:00Z"
            result = deliver(
                notes_dir, now, "REPORT BODY", "RANGE TEXT", None, last_run
            )
            self.assertTrue(result["copy_fence"])
            self.assertFalse(result["clipboard_ok"])
            self.assertTrue(os.path.exists(result["report_path"]))
            with open(last_run, encoding="utf-8") as f:
                self.assertEqual(f.read(), now)

    def test_idempotent_overwrites_same_dated_file(self):
        with tempfile.TemporaryDirectory() as d:
            notes_dir = os.path.join(d, "Notes")
            last_run = os.path.join(d, ".last-run")
            now = "2026-06-03T00:00:00Z"
            deliver(notes_dir, now, "FIRST", "R", None, last_run)
            result = deliver(notes_dir, now, "SECOND", "R", None, last_run)
            with open(result["report_path"], encoding="utf-8") as f:
                self.assertEqual(f.read(), "SECOND")


if __name__ == "__main__":
    unittest.main()
