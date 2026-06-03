package standup_test

import (
	"bytes"
	"encoding/json"
	"testing"

	"standup"
)

func digestBlob(t *testing.T, d standup.SessionDigest) string {
	t.Helper()
	b, err := json.Marshal(d)
	if err != nil {
		t.Fatalf("marshal digest: %v", err)
	}
	return string(b)
}

func runSessions(t *testing.T, args ...string) ([]standup.SessionDigest, error) {
	t.Helper()
	var out bytes.Buffer
	err := standup.Run(args, nil, &out)
	if err != nil {
		return nil, err
	}
	var digests []standup.SessionDigest
	if jerr := json.Unmarshal(out.Bytes(), &digests); jerr != nil {
		t.Fatalf("output is not a JSON array of digests: %v\noutput=%s", jerr, out.String())
	}
	return digests, nil
}

func TestRun_AttributionAndWindow(t *testing.T) {
	digests, err := runSessions(t,
		"sessions",
		"--root", "testdata/sessions",
		"--owner", "derrickwippler",
		"--since", "2026-06-02T00:00:00Z",
		"--now", "2026-06-03T00:00:00Z",
	)
	if err != nil {
		t.Fatalf("Run: %v", err)
	}

	doms := map[string]bool{}
	for _, d := range digests {
		doms[d.DomID] = true
	}

	if !doms["DOM-1608"] {
		t.Errorf("expected DOM-1608 in output; got doms=%v", doms)
	}
	if !doms["DOM-1700"] {
		t.Errorf("expected DOM-1700 in output; got doms=%v", doms)
	}
	// teammate session excluded (attribution) — branch teammate/dom-1500
	if doms["DOM-1500"] {
		t.Errorf("teammate session (DOM-1500) should be excluded by attribution; got doms=%v", doms)
	}
	// old.jsonl excluded by window — branch derrickwippler/dom-1234
	if doms["DOM-1234"] {
		t.Errorf("old session (DOM-1234) should be excluded by window; got doms=%v", doms)
	}
}

func TestRun_PreconditionSinceAfterNow(t *testing.T) {
	var out bytes.Buffer
	err := standup.Run([]string{
		"sessions",
		"--root", "testdata/sessions",
		"--since", "2026-06-03T00:00:00Z",
		"--now", "2026-06-02T00:00:00Z",
	}, nil, &out)
	if err == nil {
		t.Fatalf("expected error when since > now, got nil")
	}
}

func TestRun_PreconditionInvalidSince(t *testing.T) {
	var out bytes.Buffer
	err := standup.Run([]string{
		"sessions",
		"--root", "testdata/sessions",
		"--since", "not-a-timestamp",
		"--now", "2026-06-03T00:00:00Z",
	}, nil, &out)
	if err == nil {
		t.Fatalf("expected error for non-RFC3339 --since, got nil")
	}
}
