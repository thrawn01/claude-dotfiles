package standup_test

import (
	"os"
	"strings"
	"testing"

	"standup"
)

func openFixture(t *testing.T, path string) *os.File {
	t.Helper()
	f, err := os.Open(path)
	if err != nil {
		t.Fatalf("open fixture %s: %v", path, err)
	}
	t.Cleanup(func() { f.Close() })
	return f
}

func TestParseSession_DOM1608(t *testing.T) {
	d, err := standup.ParseSession(openFixture(t, "testdata/sessions/dom1608.jsonl"))
	if err != nil {
		t.Fatalf("ParseSession: %v", err)
	}

	if d.DomID != "DOM-1608" {
		t.Errorf("domId = %q, want DOM-1608", d.DomID)
	}
	if d.Branch == "" {
		t.Errorf("branch is empty, want set")
	}

	// ciEvents contains {golangci-lint, 3}
	var found bool
	for _, e := range d.CIEvents {
		if e.Pipeline == "golangci-lint" {
			found = true
			if e.FailCount != 3 {
				t.Errorf("golangci-lint failCount = %d, want 3", e.FailCount)
			}
		}
	}
	if !found {
		t.Errorf("ciEvents missing golangci-lint; got %+v", d.CIEvents)
	}

	// actions contains "git push" and "gh pr merge"
	if !containsStr(d.Actions, "git push") {
		t.Errorf("actions missing 'git push'; got %v", d.Actions)
	}
	if !containsStr(d.Actions, "gh pr merge") {
		t.Errorf("actions missing 'gh pr merge'; got %v", d.Actions)
	}

	if len(d.HumanTurns) == 0 {
		t.Errorf("humanTurns is empty, want non-empty")
	}

	// No raw tool output may appear in any digest field.
	blob := digestBlob(t, d)
	for _, leak := range []string{"Everything up-to-date", "Merged pull request"} {
		if strings.Contains(blob, leak) {
			t.Errorf("raw tool output %q leaked into digest: %s", leak, blob)
		}
	}
}

func TestParseSession_DOM1700_PassingBuildWithFAILEDWord(t *testing.T) {
	d, err := standup.ParseSession(openFixture(t, "testdata/sessions/dom1700.jsonl"))
	if err != nil {
		t.Fatalf("ParseSession: %v", err)
	}
	if len(d.CIEvents) != 0 {
		t.Errorf("ciEvents = %+v, want zero (passing build whose log mentions FAILED)", d.CIEvents)
	}
	// Regression (dogfooding): CLI/system-injected user messages — a
	// <local-command-stdout> wrapper and a "Claude configuration file ... is
	// corrupted" notice — must not count as genuine human turns.
	if len(d.HumanTurns) != 1 || d.HumanTurns[0] != "add the total balance metric" {
		t.Errorf("humanTurns = %#v, want exactly [\"add the total balance metric\"] (injected noise must be filtered)", d.HumanTurns)
	}
}

func TestDeriveDomID(t *testing.T) {
	cases := map[string]string{
		"derrickwippler/dom-1608-golangci-lint": "DOM-1608",
		"derrickwippler/DOM-42-thing":           "DOM-42",
		"feature/no-ticket":                     "",
		"":                                      "",
	}
	for in, want := range cases {
		if got := standup.DeriveDomID(in); got != want {
			t.Errorf("DeriveDomID(%q) = %q, want %q", in, got, want)
		}
	}
}

func containsStr(s []string, want string) bool {
	for _, v := range s {
		if v == want {
			return true
		}
	}
	return false
}
