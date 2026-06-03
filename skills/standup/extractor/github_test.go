package standup_test

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	standup "standup"
)

// runGithubCLI invokes the `github` subcommand through the Run surface.
func runGithubCLI(t *testing.T, args ...string) standup.GithubResult {
	t.Helper()
	var stdout bytes.Buffer
	if err := standup.Run(append([]string{"github"}, args...), nil, &stdout); err != nil {
		t.Fatalf("Run github: %v", err)
	}
	var got standup.GithubResult
	if err := json.Unmarshal(stdout.Bytes(), &got); err != nil {
		t.Fatalf("decode output: %v\n%s", err, stdout.String())
	}
	return got
}

func TestGithub_FixtureContract(t *testing.T) {
	got := runGithubCLI(t,
		"--since", "2026-06-02T00:00:00Z", "--now", "2026-06-03T00:00:00Z",
		"--no-local", "--me", "derrick-wippler-anchor",
		"--prs", "testdata/github/prs.raw.json",
		"--commits", "testdata/github/commits.raw.json",
	)

	var want standup.GithubResult
	b, err := os.ReadFile("testdata/github/github.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(b, &want); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(got, want) {
		gb, _ := json.MarshalIndent(got, "", "  ")
		t.Errorf("github output != github.json\ngot:\n%s", gb)
	}
}

func TestGithub_FiltersOutOfWindowAndTeammateCommits(t *testing.T) {
	got := runGithubCLI(t,
		"--since", "2026-06-02T00:00:00Z", "--now", "2026-06-03T00:00:00Z",
		"--no-local", "--me", "derrick-wippler-anchor",
		"--prs", "testdata/github/prs.raw.json",
		"--commits", "testdata/github/commits.raw.json",
	)
	for _, c := range got.Commits {
		if strings.Contains(c.Subject, "DROP-ME") {
			t.Errorf("out-of-window / teammate commit leaked: %q", c.Subject)
		}
	}
}

// TestGithub_LocalWorktreeScan exercises the PR-less-branch gap closure against a
// REAL temp git repo (the git surface is exercised for real, not faked).
func TestGithub_LocalWorktreeScan(t *testing.T) {
	if _, err := exec.LookPath("git"); err != nil {
		t.Skip("git not available")
	}
	wt := t.TempDir()
	repo := filepath.Join(wt, "dom-2000")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	git := func(env []string, a ...string) {
		t.Helper()
		cmd := exec.Command("git", append([]string{"-C", repo}, a...)...)
		cmd.Env = append(os.Environ(), env...)
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("git %v: %v\n%s", a, err, out)
		}
	}
	git(nil, "init", "-q", "-b", "derrickwippler/dom-2000-local-only")
	git(nil, "config", "user.email", "dev@example.com")
	git(nil, "config", "user.name", "Dev")
	// git log --since/--until filters by COMMITTER date, so pin both via env.
	git([]string{"GIT_AUTHOR_DATE=2026-05-01T00:00:00", "GIT_COMMITTER_DATE=2026-05-01T00:00:00"},
		"commit", "-q", "--allow-empty", "-m", "ancient local work")
	git([]string{"GIT_AUTHOR_DATE=2026-06-02T12:00:00", "GIT_COMMITTER_DATE=2026-06-02T12:00:00"},
		"commit", "-q", "--allow-empty", "-m", "in-window local work no PR yet")
	// A teammate's commit, authored in-window, landed on the first-parent line by a
	// rebase onto master. It must be excluded by the --author filter.
	git([]string{
		"GIT_AUTHOR_DATE=2026-06-02T13:00:00", "GIT_COMMITTER_DATE=2026-06-02T13:00:00",
		"GIT_AUTHOR_NAME=Teammate", "GIT_AUTHOR_EMAIL=mate@example.com",
	}, "commit", "-q", "--allow-empty", "-m", "teammate work from rebased master")

	empty := filepath.Join(wt, "empty.json")
	if err := os.WriteFile(empty, []byte("[]"), 0o644); err != nil {
		t.Fatal(err)
	}

	got := runGithubCLI(t,
		"--since", "2026-06-02T00:00:00Z", "--now", "2026-06-03T00:00:00Z",
		"--me", "derrick-wippler-anchor",
		"--prs", empty, "--commits", empty, "--worktrees", wt,
	)

	var foundInWindow, foundAncient, foundTeammate bool
	for _, c := range got.Commits {
		switch c.Subject {
		case "in-window local work no PR yet":
			foundInWindow = true
			if c.DomID == nil || *c.DomID != "DOM-2000" {
				t.Errorf("local commit domId = %v, want DOM-2000", c.DomID)
			}
		case "ancient local work":
			foundAncient = true
		case "teammate work from rebased master":
			foundTeammate = true
		}
	}
	if !foundInWindow {
		t.Errorf("in-window PR-less local commit did not surface; commits=%+v", got.Commits)
	}
	if foundAncient {
		t.Errorf("out-of-window local commit should have been dropped")
	}
	if foundTeammate {
		t.Errorf("teammate commit (rebased from master) should have been dropped by --author")
	}
}

func TestGithub_PreconditionSinceAfterNow(t *testing.T) {
	var stdout bytes.Buffer
	err := standup.Run([]string{"github", "--since", "2026-06-03T00:00:00Z",
		"--now", "2026-06-02T00:00:00Z", "--no-local", "--prs", "testdata/github/prs.raw.json"},
		nil, &stdout)
	if err == nil {
		t.Fatal("expected error when --since > --now")
	}
}

func TestGithub_MissingSinceErrors(t *testing.T) {
	var stdout bytes.Buffer
	err := standup.Run([]string{"github", "--now", "2026-06-03T00:00:00Z", "--no-local"}, nil, &stdout)
	if err == nil {
		t.Fatal("expected error when --since missing")
	}
}
