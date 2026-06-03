package standup

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	iofs "io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Run is the CLI surface. main() delegates here; tests call it directly.
func Run(args []string, stdin io.Reader, stdout io.Writer) error {
	if len(args) == 0 {
		return fmt.Errorf("expected a subcommand (\"sessions\" or \"github\")")
	}
	switch args[0] {
	case "sessions":
		return runSessions(args[1:], stdout)
	case "github":
		return runGithub(args[1:], stdout)
	default:
		return fmt.Errorf("unknown subcommand %q", args[0])
	}
}

func defaultRoot() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ".claude/projects"
	}
	return filepath.Join(home, ".claude", "projects")
}

func runSessions(args []string, stdout io.Writer) error {
	fs := flag.NewFlagSet("sessions", flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	since := fs.String("since", "", "window start (RFC3339, required)")
	now := fs.String("now", "", "window end (RFC3339, required)")
	root := fs.String("root", defaultRoot(), "directory to scan for *.jsonl session logs")
	owner := fs.String("owner", "derrickwippler", "owner substring for attribution")
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

	digests := []SessionDigest{}

	walkErr := filepath.WalkDir(*root, func(path string, dirent iofs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if dirent.IsDir() {
			return nil
		}
		if !strings.HasSuffix(path, ".jsonl") {
			return nil
		}
		f, err := os.Open(path)
		if err != nil {
			return err
		}
		defer f.Close()
		d, err := ParseSession(f)
		if err != nil {
			return fmt.Errorf("parse %s: %w", path, err)
		}
		if includeDigest(d, *owner, sinceT, nowT) {
			digests = append(digests, d)
		}
		return nil
	})
	if walkErr != nil {
		return walkErr
	}

	enc := json.NewEncoder(stdout)
	enc.SetEscapeHTML(false)
	return enc.Encode(digests)
}

// includeDigest applies attribution AND window filters per CONTRACT §1.
func includeDigest(d SessionDigest, owner string, since, now time.Time) bool {
	// Attribution: cwd OR branch contains the owner substring.
	if !strings.Contains(d.Cwd, owner) && !strings.Contains(d.Branch, owner) {
		return false
	}
	// Window: [firstTs,lastTs] overlaps [since,now].
	if d.FirstTs == "" || d.LastTs == "" {
		return false
	}
	first, err := time.Parse(time.RFC3339, d.FirstTs)
	if err != nil {
		return false
	}
	last, err := time.Parse(time.RFC3339, d.LastTs)
	if err != nil {
		return false
	}
	// overlap iff first <= now AND last >= since
	if first.After(now) || last.Before(since) {
		return false
	}
	return true
}
