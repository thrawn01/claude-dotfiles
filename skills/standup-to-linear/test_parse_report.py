"""Surface tests for parse_report: markdown report -> {domId, body} payloads."""

import unittest

from parse_report import parse_report

REPORT = """# Standup [2026-06-03T15:34:52Z … 2026-06-04T16:16:51Z]

## DOM-1546 · ci cannot detect ent regen drift (Open)

  - Built out ent regen-drift detection; landed go:generate sidecars.
  - 6 commits
  - PR [#208034](https://github.com/anchorlabsinc/anchorage/pull/208034) open

## [DOM-1621](https://linear.app/anchorlabs/issue/DOM-1621/more) · More Go Build Improvements (In Review)

  - Got the DWARF-strip migration up for review.
  - 7 commits
  - PR [#207900](https://github.com/anchorlabsinc/anchorage/pull/207900) open

## [DOM-1622](https://linear.app/anchorlabs/issue/DOM-1622/golden) · Golden Path Definition (In Progress)

  - Dug into the Golden Path service lifecycle.

## Other PRs

  - PR [#206265](https://github.com/x/206265) open — refactor

## Meetings / Notes

  - 2026-06-04: standup sync
"""


class ParseReportTest(unittest.TestCase):
    def setUp(self):
        self.out = parse_report(REPORT, "report.md")
        self.by_id = {c["domId"]: c for c in self.out["comments"]}

    def test_window_and_date_parsed(self):
        self.assertEqual(self.out["window"]["since"], "2026-06-03T15:34:52Z")
        self.assertEqual(self.out["window"]["now"], "2026-06-04T16:16:51Z")
        self.assertEqual(self.out["date"], "2026-06-04")

    def test_only_ticket_sections_become_comments(self):
        # Other PRs / Meetings have no identifier -> skipped.
        self.assertEqual(set(self.by_id), {"DOM-1546", "DOM-1621", "DOM-1622"})

    def test_id_extracted_from_both_heading_forms(self):
        self.assertIn("DOM-1546", self.by_id)  # bare form
        self.assertIn("DOM-1621", self.by_id)  # linked form

    def test_status_parsed(self):
        self.assertEqual(self.by_id["DOM-1621"]["status"], "In Review")

    def test_title_stripped_of_id_and_status(self):
        self.assertEqual(self.by_id["DOM-1621"]["title"], "More Go Build Improvements")

    def test_body_has_dated_header_and_lead_summary(self):
        body = self.by_id["DOM-1546"]["body"]
        self.assertTrue(body.startswith("**Standup · 2026-06-04**"))
        self.assertIn("Built out ent regen-drift detection", body)

    def test_body_promotes_summary_and_keeps_rest_as_bullets(self):
        body = self.by_id["DOM-1546"]["body"]
        # Lead summary is NOT a bullet; the stats/PR lines are.
        self.assertNotIn("- Built out ent", body)
        self.assertIn("- 6 commits", body)
        self.assertIn("- PR [#208034]", body)

    def test_summary_only_section_has_no_bullets(self):
        body = self.by_id["DOM-1622"]["body"]
        self.assertIn("Dug into the Golden Path", body)
        self.assertNotIn("\n- ", body)  # no bullet list, just header + lead

    def test_deleting_a_section_drops_it(self):
        # The edit-as-review gate: a removed section never becomes a comment.
        edited = REPORT.replace(
            "## DOM-1546 · ci cannot detect ent regen drift (Open)\n\n"
            "  - Built out ent regen-drift detection; landed go:generate sidecars.\n"
            "  - 6 commits\n"
            "  - PR [#208034](https://github.com/anchorlabsinc/anchorage/pull/208034) open\n\n",
            "",
        )
        ids = {c["domId"] for c in parse_report(edited)["comments"]}
        self.assertNotIn("DOM-1546", ids)
        self.assertIn("DOM-1621", ids)

    def test_self_reference_to_own_ticket_is_stripped(self):
        text = ("# Standup [a … b]\n\n## DOM-1635 · Config (In Progress)\n\n"
                "  - Opened DOM-1635 to track the config topic; it pairs with DOM-1622.\n")
        body = parse_report(text)["comments"][0]["body"]
        # Own id replaced with "this ticket"; a cross-ref to another ticket survives.
        self.assertNotIn("DOM-1635", body)
        self.assertIn("Opened this ticket to track", body)
        self.assertIn("DOM-1622", body)

    def test_section_with_no_bullets_is_skipped(self):
        text = "# Standup [a … b]\n\n## DOM-9999 · empty (Open)\n\n## DOM-1 · real (Open)\n\n  - did a thing\n"
        ids = {c["domId"] for c in parse_report(text)["comments"]}
        self.assertEqual(ids, {"DOM-1"})


if __name__ == "__main__":
    unittest.main()
