# PR description intent — what the open-pr skill now asks for

Summary of the 2026-09-09 changes to `~/.claude/skills/open-pr/` (SKILL.md +
pr-template.md), ported from armada's `pr-create` skill (ARM-2731 outcome-first
rewrite, ARM-2656 verbatim-quoting fold). The headings below quote the exact
verbiage the skill uses, because the wording is the change — the template
structure barely moved.

## Purpose: outcome first, in the surface's voice

The old table cell said "1-3 sentences on why this change exists." The new one
defines whose experience the section describes:

> The outcome, written for the system's users. The product is the system's
> **surface** — the interfaces, APIs, config, and behavior the change touches —
> so open with the burden lifted or capability gained, then the before → after
> from the user's or operator's perspective, with the mechanism in **one
> clause**, not a section.

Two enforcement lines carry the intent:

- The rewrite trigger: *"If a reader can't tell from this section who
  experiences the change, rewrite it."*
- The calibration example (target voice, quoted in the skill): *"Health
  monitoring of merchant endpoints lifts the burden of keeping the catalog up
  to date off staff. The change adds an interval check that runs once a day
  against the registered endpoints in the catalog."* — outcome sentence first,
  mechanism sentence second, no section for the mechanism.

## Implementation: judge-only consequences, not diff narration

The cell now scopes itself to *"Only the calls a reviewer must judge, as 2–4
bullets of plain consequences: what a caller or operator now experiences
differently … never function-level narration of the diff."* Rejected
alternatives appear *"only when a reviewer would plausibly ask 'why not X'."*

The ARM-2656 rule rides here: when the diff changes a string a caller or model
reads (error message, tool/schema description, API doc field), *"quote the
before and after **verbatim** here; a reviewer judging that change without
opening the file is the point."*

## The description register (new block)

The visible body — everything above any collapsed block — is **~200–300 words**
and *"must stand alone: a reviewer understands intent and change without
opening the ticket or the diff."* Diligence material (test counts, QA
checklists, failure-mode analyses) goes into a collapsed
`<details><summary>Review evidence</summary>` block, with the guard that
*"nothing inside a collapsed block may be required reading: if a fact changes
what a reviewer would approve, it stays visible."*

Three named rules keep the register:

- **Selection, not compression.** Past ~300 words visible, *"move whole facts
  into the collapsed block or delete them — don't tighten sentences."* More
  than a couple of function/package names visible means detail leaked upward.
- **State each fact once.** Mechanism in one section; verification numbers
  live only in the collapsed block.
- **Human, not generic.** Cut wrapper phrases ("this PR aims to", "ensures",
  "enhances", "streamlines") unless the next words name the concrete behavior;
  *"If a sentence could fit any PR in the repo, replace it with the fact this
  diff proves."* Note tradeoffs honestly.

## Title: name the outcome, not the artifact

*"One clause of at most ~72 characters naming the outcome — the constraint,
user need, or problem resolved, not just the artifact touched."* The skill's
own contrast pair: `add helix editor` (artifact, rejected) vs `add helix
editor for devs without local GUI access` (outcome, accepted). No AI-generic
adjectives (`robust`, `seamless`, `comprehensive`).

## Template change

pr-template.md keeps Purpose/Implementation (anchorage's hermes bot references
"the Purpose section" by name) and gains one optional block above the
`Fixes {{TICKET}}` line:

```
<details><summary>Review evidence</summary>

{{EVIDENCE}}

</details>
```

with a comment instructing to omit it entirely when there is no diligence
material to fold.

## Deliberately not ported from armada

The failure-mode walk, wiki-coverage gate, and Codex/un-draft sequencing —
repo-specific process machinery, not description prose.
