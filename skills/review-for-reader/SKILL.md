---
name: review-for-reader
description: Review a PR/diff from the perspective of the next maintainer who never saw the change — catching comments, docstrings, and docs that only make sense to someone holding the diff ("diff-anchored writing"), stale comments referencing removed code, journal/history comments, what-not-why comments, and README/doc drift. Then rewrite the flagged prose to current-state phrasing in place. Use when the user says "review for the next reader", "review my comments", "check for diff-anchored comments", "review the PR as a maintainer", "does this make sense without the diff", or "review-for-reader". This is the prose/reader counterpart to review-behavior-change (which reviews the contract) and is NOT a bug finder (use code-review / the built-in /review) or a guideline linter (use review-guidelines).
allowed-tools: Read, Grep, Glob, Edit, Bash, Agent, AskUserQuestion
---

# Review For Reader

Review a change the way the **next maintainer** experiences it: someone who opens the file months from now, never saw the diff, never read the PR thread, and has no access to the code this change replaced. Comments and docs must make sense to *that* reader. This skill finds the prose that fails that test and rewrites it.

It reviews **prose, not logic** — comments, docstrings, README/docs, examples, and (lightly) the PR description. It does not hunt for bugs (`code-review` / built-in `/review`), check guideline compliance (`review-guidelines`), or review the behavioral contract (`review-behavior-change`). It is the *reader-experience* lens those skills lack.

## The core test: the Stranger Test

> For every comment, docstring, and doc line the change touches: **would it make sense to someone who never saw the previous version and isn't looking at the diff?** If it only makes sense to someone holding the diff — if it references code, state, or behavior not present in the final file — it is **diff-anchored** and must be rewritten or removed.

This is mechanized by a **fresh-context reviewer**: a sub-agent given **only the final file contents — never the diff, never this conversation.** A reviewer blind to the change reads each comment exactly as the future maintainer will. That blindness is the engine of the skill; do not leak the diff into it.

Motivating example (a real Claude-authored test comment):

> `// The old direct storage write left the in-memory accounting stale (unLeased 0, nextLifecycleRun ~37y), so this fails on main.`

"The old direct storage write", "fails on main" — invisible to the future reader; the comment is noise to them. The durable *why* (a direct partition write leaves in-memory accounting stale) survives; the temporal framing is stripped:

> `// A direct partition write would leave in-memory accounting stale (unLeased 0, nextLifecycleRun ~37y); routing through the partition's loop keeps it consistent — asserted below.`

## What counts as diff-anchored (the named anti-patterns)

- **Diff-anchored comments** — reference a prior state the reader can't see. Tells: *old, previously, used to, formerly, originally, now (in the "changed to" sense), changed from, replaced, this fixes, this used to, before this change, on main, the original, no longer, instead of the previous.*
- **Stale comments** — describe code the change renamed or removed; the comment now points at nothing in the file.
- **Journal comments** — embed history in the source: dates, author names, ticket/PR numbers, "added in v2", change logs. Version control owns history (Ousterhout: *"comments belong to the code, not the commit log"*).
- **What-not-why comments** — narrate what the code mechanically does instead of why it exists (Google: comments *"should not be explaining what some code is doing"*). Diff-authored comments often restate the change as "what".
- **Doc / README drift** — prose, examples, or flags referencing renamed symbols, removed options, or old behavior the change invalidated.
- **Dangling cross-references** — a comment points at documentation that won't outlive the code. A reference is only as durable as its *target*: a pointer into an **ephemeral** location — a per-feature or working directory the repo discards once the work lands (e.g. `docs/features/<x>/`, a feature's review-report HTML, a scratch plan/blueprint), the PR/issue thread, or a ticket/decision id whose only definition lives in such a place — points nowhere the day that location is deleted. Tell: a parenthetical id (`(BP-3)`, `(RS-008)`) or `§section` whose meaning a reader can only recover by opening a document *outside* the permanent docs. Contrast with the SPARE list: a pointer into durable documentation (an ADR, a stable decision/design doc kept under `docs/`) is fine — that target is maintained, not disposable. The fix is the same as for any diff-anchored comment: keep the durable reason inline (it usually already is) and drop the dangling pointer, or demote a durable-doc id to a trailing "see also".
- **PR-description inversion** — the durable *why/purpose* is missing from the PR body while it's full of diff narration (or vice versa: durable reasoning trapped only in the PR thread, where future readers won't find it — Google: *"Explanations written only in the code review tool are not helpful to future code readers."*).

**The "Tells" are a locator, never a finding.** Grepping the change for tell-words is a fine way to *point the blind reviewer at suspects* — but a keyword match is not itself a finding, and the same word is often innocent: *"used to delete the source ID"* (the verb *use*) is FINE; *"this used to write directly"* (temporal) is not; *"now"* meaning *at this point in execution* is FINE, *"now we route through the loop"* is not. Only the blind read of the final file decides. Never report a finding straight from a grep hit, and never inflate the count with regex false positives — the tell list feeds Phase 1's attention, not its verdict.

## What to SPARE (do not flag)

Referencing change is **correct** in version-scoped artifacts. Never flag:
- `CHANGELOG.md`, release notes, migration/upgrade guides, deprecation notices.
- The PR description / commit message body themselves (they *are* the diff's narration).
- ADR "Context" / "Consequences" / "Alternatives considered" sections — discussing the prior approach is their job.
- Comments that name an alternative for a *current* reason ("we don't use a mutex here because single-writer is the invariant") — that's durable why, not diff narration, even though it mentions what's *not* done.
- In-code pointers into **permanent** documentation — an ADR number, a stable design/decision-log doc kept under `docs/`, a spec section — when the comment's durable reason is already stated inline and the id is just a "see also". (A pointer into a *disposable* location is the opposite case, not spared — see "Dangling cross-references" above.)

The line: does the prose inform a reader who never saw the change, or does it only make sense to someone reviewing the diff? Spare the former.

## Inputs & scope

Default target: **the current branch's changes vs the base** (`main`/`master`). Resolve:
- A PR number / URL in `$ARGUMENTS` → `gh pr diff <n>` for the patch and `gh pr diff <n> --name-only` for files; check out / fetch as needed to read final file contents.
- Otherwise the current branch: base is `main` (fall back to `master`). Changed files: `git diff --name-only <base>...HEAD`. Patch (orchestrator-only, for locating changed regions): `git diff <base>...HEAD`. If the branch has no commits vs base, review the working tree (`git diff --name-only` incl. staged) instead.

If on `main`/`master` with no diff and no PR given, ask the user what to review.

## Phase 0: Gather

1. Resolve the target and get the **changed-file list** and the **patch** (orchestrator use only).
2. For each changed file, read its **final, post-change content** (the whole file). This — not the patch — is what the fresh-context reviewer sees.
3. Partition files into **source** (code with comments/docstrings) and **docs** (`*.md`, README, docs/). Drop pure data/lock files and the spare-list artifacts above from prose review.
   - While here, learn which documentation locations the repo treats as **ephemeral** vs **permanent** — check the project's ADRs / docs conventions (e.g. a `docs/features/` working tree that the repo's own ADRs slate for eventual removal, vs a durable `docs/design/` decision log). The skeptic gate uses this to sort each in-code doc pointer into durable (keep) or dangling (strip). When the convention isn't documented, ask the user rather than guessing which way a location cuts.
4. From the patch, note for each source file the **changed/added line ranges**. These define **in scope**: a finding is in scope only if the comment/doc it concerns was *introduced or touched* by this change. The reviewer still judges every comment from a blind read of the final file.
5. **In-scope vs. pre-existing.** The Stranger Test reviewer reads whole files by necessity — a comment can only be judged with its surrounding code — so it *will* surface valid findings on prose this change never touched (a years-old journal comment, a pre-existing stale comment). Do **not** silently drop these and do **not** attribute them to this change. Confirm a finding's provenance against the changed-line ranges (or `git blame`), then sort it into one of two buckets: **in-scope** (introduced/touched here) or **pre-existing (out of scope)**. Only in-scope findings are auto-fixed (Phase 4); pre-existing ones are reported in their own section (Phase 5) for the user to fix separately or via a whole-file run.
6. State scope to the user in a few lines: target (branch/PR), files in prose scope, what was spared, and whether this is a diff-scoped run (default) or a whole-file run (everything in the touched files is in scope).

## Phase 1: Stranger Test (fresh-context sub-agents)

Spawn a small number of sub-agents in parallel (Agent tool, **foreground**, `model: "sonnet"`, default general-purpose agent), partitioned by file or directory. **Give each agent only final file contents and the in-scope comment locations — never the diff, never this conversation.**

Sub-agent prompt structure:

```
You are the next maintainer of this code. You have NEVER seen any previous version
of these files and you are NOT looking at any diff. Read each file as it exists now.

For every comment, docstring, and (for docs) prose line listed below, judge:
- Does it make sense using ONLY what is present in this file? Or does it reference
  something — code, a variable, a state, a behavior, a prior approach, a branch like
  "main", a fix — that you cannot see anywhere in this file?
- Classify: DIFF-ANCHORED (needs unseen prior state) | STALE (describes code not in
  this file) | JOURNAL (history/date/author/ticket) | WHAT-NOT-WHY (narrates what the
  code does, adds nothing) | FINE.
- For anything not FINE: quote it with file:line, say exactly what unseen thing it
  assumes, and propose a CURRENT-STATE rewrite that preserves the durable "why" while
  removing the temporal/diff framing — or DELETE if there is no durable content.
- If a comment points at an external document or carries a bare id/`§section`
  (`(BP-3)`, `RS-008`, "see the blueprint"), name the referenced target explicitly
  and note whether the comment still reads sensibly WITHOUT the lookup. Do not decide
  keep-vs-strip — that depends on whether the target is a permanent or disposable doc,
  which the orchestrator resolves. Just surface the pointer and its target.

Files (final contents):
<full content of each file>
In-scope comment locations (new or changed-adjacent): <file:line list>
Be strict on the Stranger Test but do NOT flag version-scoped files (changelogs,
release notes) or comments that name an alternative for a current reason.
```

Read the cited lines in the real files yourself before trusting any flag. Collect findings.

## Phase 2: Doc-drift & PR-description pass

One sub-agent (Agent tool, **foreground**, `model: "sonnet"`), this one *may* see the changed-symbol list (renames/removals extracted from the patch):

- **Doc/README drift:** does any doc, example, or flag reference a symbol/option/behavior the change renamed, removed, or altered? Cite and propose the current-state fix.
- **PR-description durability** (if a PR/branch description exists, `gh pr view --json body` or the commit body): is the durable *purpose/why* present and stated in current-state terms, or is the body only diff narration? Is any durable reasoning stranded only in the PR thread that belongs in a code comment or doc? Report; do not rewrite the PR body here (that's `open-pr`).

## Phase 3: Skeptic gate (stay high-signal)

Spawn one sub-agent (Agent tool, **foreground**, `model: "sonnet"`) as defense attorney, or do it directly. Apply the **maintainer bar**: only keep a finding at high confidence it genuinely confuses a future reader. For each finding, argue:
- Is this actually diff-anchored, or durable why-it-exists prose that merely mentions an alternative? (Keep only if a stranger is genuinely lost.)
- Is it in a spared, version-scoped artifact? → drop.
- Would a linter/formatter already handle it? → drop (out of scope).
- Is the proposed rewrite faithful — does it preserve every durable fact (the *why*, the magic numbers, the invariant) and only strip the temporal framing?

Drop everything that doesn't clear the bar. Silence on a borderline comment is correct.

## Phase 4: Auto-fix

For each surviving finding with a confident, faithful rewrite, apply it in place with Edit:
- **Rewrite** diff-anchored / journal / what-not-why comments to current-state phrasing that passes the Stranger Test, preserving the durable why and any concrete values.
- **Delete** comments that are pure diff narration with no durable content ("// changed to fix the bug", "// was Foo, now Bar").
- **Update** drifted docs/examples to match current symbols/behavior.

Leave for the user (do not guess) any finding where the durable *why* is unclear from the final code alone — rewriting it would risk inventing a rationale. Collect these as questions.

Never touch logic. Never edit spared artifacts. After edits, re-read each touched region to confirm the rewrite reads cleanly standalone.

## Phase 5: Decisions & report

If any findings were left for the user (ambiguous why, or a PR-description gap that needs their input), surface them with `AskUserQuestion` — quote the comment, say what's unseen, offer the candidate rewrite vs. delete vs. keep.

Then give a concise chat summary (no HTML report needed unless the user asks):

```
## Review For Reader — <branch/PR>

Files reviewed (prose):   N
Diff-anchored fixed:      N
Stale comments fixed:     N
Journal/what-not-why:     N
Doc drift fixed:          N
Left for your call:       N   (listed above)
Pre-existing (skipped):   N   (out of scope — listed below)
PR description:           <ok | missing durable why | reasoning stranded in thread>
```

List each applied fix as `file:line` with before → after, so the user can eyeball the rewrites. Then, in a separate **Pre-existing (out of scope)** section, list any valid findings the blind read surfaced on prose this change did not touch — `file:line`, the issue, and a candidate rewrite — clearly marked as not introduced by this change, with a one-line offer to clean them up via a whole-file run. Mention spared files only if asked.

## Rules

- **The reviewer must be blind.** The Stranger Test only works if the fresh-context sub-agent never sees the diff or this conversation. The orchestrator uses the diff to locate in-scope comments; the *judgment* is always a blind read of the final file. Because the blind read spans whole files, it will surface valid findings on untouched prose — sort those into the pre-existing bucket; never auto-fix them in a diff-scoped run and never attribute them to this change.
- **Tells locate, the blind read decides.** A tell-word grep only points attention at suspects. Never raise a finding from a keyword match alone, and discard regex false positives (the verb *"used to"*, *"now"* meaning *at this point*) before they reach the report.
- **Preserve the why, strip the when.** A diff-anchored comment usually contains a durable reason wrapped in temporal framing. Rewrite to keep the reason and drop "old/previously/now/on main". Delete only when there is no durable content. Never discard a real rationale.
- **Spare version-scoped artifacts.** Changelogs, release notes, migration guides, PR/commit bodies, and ADR context sections are *supposed* to reference change. Flagging them is a false positive.
- **A pointer is only as durable as its target.** Spare in-code references into permanent docs (ADRs, stable design/decision docs under `docs/`) when the durable reason is already inline. Flag references into ephemeral/disposable locations (per-feature working dirs like `docs/features/`, review-report HTML, scratch plans, the PR thread) — they dangle the moment that location is removed, leaving the reader chasing a pointer to nothing. When unsure which a location is, consult the repo's conventions/ADRs (Phase 0) before deciding.
- **High-signal only.** Apply the maintainer bar — flag at high confidence, stay silent when unsure. This skill earns trust by not nagging about durable comments that merely mention alternatives.
- **Prose only, never logic.** Edits change comments, docstrings, and docs — never code behavior. If a comment is wrong because the *code* is wrong, report it; don't fix the code (that's `code-review` / `review-validate`).
- **Don't rewrite the PR body.** Report description gaps; hand the rewrite to `open-pr`.
