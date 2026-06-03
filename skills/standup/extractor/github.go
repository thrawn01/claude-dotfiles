package standup

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

// PR and Commit are the GitHub collector's contract output (CONTRACT.md §2).
type PR struct {
	Number int     `json:"number"`
	URL    string  `json:"url"`
	Title  string  `json:"title"`
	Branch string  `json:"branch"`
	State  string  `json:"state"`
	DomID  *string `json:"domId"`
}

// Commit is an in-window commit attributed to a ticket via its branch.
type Commit struct {
	Subject string  `json:"subject"`
	DomID   *string `json:"domId"`
}

// GithubResult is the full collector output.
type GithubResult struct {
	PRs     []PR     `json:"prs"`
	Commits []Commit `json:"commits"`
}

// raw shapes decoded from `gh --json` output or injected fixtures.
type rawPR struct {
	Number      int    `json:"number"`
	URL         string `json:"url"`
	Title       string `json:"title"`
	HeadRefName string `json:"headRefName"`
	State       string `json:"state"`
	Author      struct {
		Login string `json:"login"`
	} `json:"author"`
	UpdatedAt string `json:"updatedAt"`
}

// rawCommit is the flattened commit shape (from `gh pr view`, `git log`, or a
// fixture). A missing authoredDate/login is treated as in-window / mine.
type rawCommit struct {
	MessageHeadline string `json:"messageHeadline"`
	AuthoredDate    string `json:"authoredDate"`
	Login           string `json:"login"`
	Branch          string `json:"branch"`
}

func domIDPtr(branch string) *string {
	id := DeriveDomID(branch)
	if id == "" {
		return nil
	}
	return &id
}

func parseLoose(s string) (time.Time, bool) {
	for _, layout := range []string{time.RFC3339Nano, time.RFC3339} {
		if t, err := time.Parse(layout, s); err == nil {
			return t, true
		}
	}
	return time.Time{}, false
}

// inWindow reports whether an RFC3339 timestamp falls in [since,now]. Missing or
// unparseable timestamps are kept (matching the collector's permissive default).
func inWindow(s string, since, now time.Time) bool {
	if s == "" {
		return true
	}
	t, ok := parseLoose(s)
	if !ok {
		return true
	}
	return !t.Before(since) && !t.After(now)
}

func runGithub(args []string, stdout io.Writer) error {
	fs := flag.NewFlagSet("github", flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	since := fs.String("since", "", "window start (RFC3339, required)")
	now := fs.String("now", "", "window end (RFC3339, required)")
	repo := fs.String("repo", "anchorlabsinc/anchorage", "owner/repo")
	me := fs.String("me", "", "GitHub login for attribution (default: gh api user)")
	worktrees := fs.String("worktrees", defaultWorktrees(), "local worktree root to scan with git log")
	gitAuthor := fs.String("git-author", "", "git --author filter for local scan (default: each worktree's user.email)")
	noLocal := fs.Bool("no-local", false, "disable the local-worktree git scan")
	prsFixture := fs.String("prs", "", "fixture file of recorded `gh pr list` JSON")
	commitsFixture := fs.String("commits", "", "fixture file of recorded commit JSON (also skips gh pr view)")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if *since == "" {
		return fmt.Errorf("--since is required")
	}
	if *now == "" {
		return fmt.Errorf("--now is required")
	}
	sinceT, err := time.Parse(time.RFC3339, *since)
	if err != nil {
		return fmt.Errorf("--since must be RFC3339: %w", err)
	}
	nowT, err := time.Parse(time.RFC3339, *now)
	if err != nil {
		return fmt.Errorf("--now must be RFC3339: %w", err)
	}
	if sinceT.After(nowT) {
		return fmt.Errorf("--since (%s) must be <= --now (%s)", *since, *now)
	}

	// --- PR list (fixture, or live `gh pr list`; a gh failure is a hard abort) ---
	var rawPRs []rawPR
	if *prsFixture != "" {
		if err := readJSON(*prsFixture, &rawPRs); err != nil {
			return err
		}
	} else {
		if *me == "" {
			if out, err := exec.Command("gh", "api", "user", "--jq", ".login").Output(); err == nil {
				*me = strings.TrimSpace(string(out))
			}
		}
		out, err := exec.Command("gh", "pr", "list", "--repo", *repo, "--author", "@me",
			"--state", "all", "--json", "number,url,title,headRefName,state,author,updatedAt",
			"--limit", "200").Output()
		if err != nil {
			return fmt.Errorf("gh pr list: %w", err)
		}
		if err := json.Unmarshal(out, &rawPRs); err != nil {
			return fmt.Errorf("gh pr list: decode: %w", err)
		}
	}
	if *me == "" {
		*me = "__me__"
	}

	prs := []PR{}
	for _, r := range rawPRs {
		// Always include open PRs — the dev may be babysitting CI on a PR that
		// had no GitHub activity (updatedAt) in the standup window. Only apply
		// the window filter to closed/merged PRs to avoid surfacing ancient history.
		open := strings.EqualFold(r.State, "open")
		if attributedTo(r.Author.Login, *me) && (open || inWindow(r.UpdatedAt, sinceT, nowT)) {
			prs = append(prs, PR{
				Number: r.Number, URL: r.URL, Title: r.Title,
				Branch: r.HeadRefName, State: r.State, DomID: domIDPtr(r.HeadRefName),
			})
		}
	}

	// --- PR-anchored commits (fixture, or concurrent `gh pr view` per PR) ---
	var prCommits []rawCommit
	if *commitsFixture != "" {
		if err := readJSON(*commitsFixture, &prCommits); err != nil {
			return err
		}
	} else {
		prCommits = fetchPRCommits(prs, *repo)
	}

	// --- Local worktree commits (concurrent `git log` per checked-out branch) ---
	var localCommits []rawCommit
	if !*noLocal {
		localCommits = scanWorktrees(*worktrees, *since, *now, *gitAuthor)
	}

	// --- Filter + dedup into the contract commit list ---
	commits := []Commit{}
	seen := map[string]bool{}
	for _, rc := range append(prCommits, localCommits...) {
		if !inWindow(rc.AuthoredDate, sinceT, nowT) || !attributedTo(rc.Login, *me) {
			continue
		}
		dom := domIDPtr(rc.Branch)
		ds := ""
		if dom != nil {
			ds = *dom
		}
		key := rc.MessageHeadline + "\x00" + ds
		if seen[key] {
			continue
		}
		seen[key] = true
		commits = append(commits, Commit{Subject: rc.MessageHeadline, DomID: dom})
	}

	enc := json.NewEncoder(stdout)
	enc.SetEscapeHTML(false)
	return enc.Encode(GithubResult{PRs: prs, Commits: commits})
}

// attributedTo treats a missing login as the developer's own (fixtures omit it).
func attributedTo(login, me string) bool {
	if login == "" {
		return true
	}
	return login == me
}

func defaultWorktrees() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return "worktrees/derrickwippler"
	}
	return filepath.Join(home, "worktrees", "derrickwippler")
}

func readJSON(path string, v any) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(b, v)
}

// fetchPRCommits fetches each PR branch's commits concurrently. A per-PR gh failure
// is a warning (the PR itself still appears), not a hard abort.
func fetchPRCommits(prs []PR, repo string) []rawCommit {
	var (
		mu  sync.Mutex
		wg  sync.WaitGroup
		out []rawCommit
	)
	for _, pr := range prs {
		wg.Add(1)
		go func(pr PR) {
			defer wg.Done()
			b, err := exec.Command("gh", "pr", "view", strconv.Itoa(pr.Number),
				"--repo", repo, "--json", "commits").Output()
			if err != nil {
				fmt.Fprintf(os.Stderr, "warning: gh pr view %d: %v\n", pr.Number, err)
				return
			}
			var view struct {
				Commits []struct {
					MessageHeadline string `json:"messageHeadline"`
					AuthoredDate    string `json:"authoredDate"`
					Authors         []struct {
						Login string `json:"login"`
					} `json:"authors"`
				} `json:"commits"`
			}
			if json.Unmarshal(b, &view) != nil {
				return
			}
			local := make([]rawCommit, 0, len(view.Commits))
			for _, c := range view.Commits {
				login := ""
				if len(c.Authors) > 0 {
					login = c.Authors[0].Login
				}
				local = append(local, rawCommit{
					MessageHeadline: c.MessageHeadline, AuthoredDate: c.AuthoredDate,
					Login: login, Branch: pr.Branch,
				})
			}
			mu.Lock()
			out = append(out, local...)
			mu.Unlock()
		}(pr)
	}
	wg.Wait()
	return out
}

// scanWorktrees runs `git log` over each worktree's checked-out branch concurrently.
// Three guards keep other people's / other days' work out, because a branch REBASED
// onto a recent master puts master's commits onto the first-parent line:
//   - --author (the dev's git identity) drops teammate commits brought in by rebase;
//   - AUTHOR date (%aI) + the window drop commits authored on other days (a rebase
//     rewrites committer date to "now", so committer date can't be trusted);
//   - --first-parent / --no-merges keep side-branch and merge commits out.
//
// Soft throughout: missing dir / non-git / git errors are skipped silently.
func scanWorktrees(root, since, now, gitAuthor string) []rawCommit {
	entries, err := os.ReadDir(root)
	if err != nil {
		return nil
	}
	var (
		mu  sync.Mutex
		wg  sync.WaitGroup
		out []rawCommit
	)
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		dir := filepath.Join(root, e.Name())
		wg.Add(1)
		go func(dir string) {
			defer wg.Done()
			if _, err := exec.Command("git", "-C", dir, "rev-parse", "--is-inside-work-tree").Output(); err != nil {
				return
			}
			bout, err := exec.Command("git", "-C", dir, "rev-parse", "--abbrev-ref", "HEAD").Output()
			if err != nil {
				return
			}
			branch := strings.TrimSpace(string(bout))
			if branch == "" {
				return
			}
			// Author identity: explicit flag, else this worktree's configured email.
			author := gitAuthor
			if author == "" {
				if aout, err := exec.Command("git", "-C", dir, "config", "user.email").Output(); err == nil {
					author = strings.TrimSpace(string(aout))
				}
			}
			logArgs := []string{"-C", dir, "log", "HEAD", "--first-parent", "--no-merges",
				"--since", since, "--until", now, "--format=%aI\x1f%s"}
			if author != "" {
				logArgs = append(logArgs, "--author="+author)
			}
			lout, err := exec.Command("git", logArgs...).Output()
			if err != nil {
				return
			}
			local := []rawCommit{}
			for _, line := range strings.Split(strings.TrimRight(string(lout), "\n"), "\n") {
				if line == "" {
					continue
				}
				parts := strings.SplitN(line, "\x1f", 2)
				if len(parts) != 2 {
					continue
				}
				local = append(local, rawCommit{
					AuthoredDate: parts[0], MessageHeadline: parts[1], Branch: branch,
				})
			}
			mu.Lock()
			out = append(out, local...)
			mu.Unlock()
		}(dir)
	}
	wg.Wait()
	return out
}
