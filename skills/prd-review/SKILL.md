---
name: prd-review
description: Review an existing PRD for gaps, inconsistencies, and unresolved open questions, then produce an updated version. Use when the user asks to "review the PRD", "check the PRD", or "update the PRD"; or when a tech-spec session has surfaced product questions that need to be resolved back in the PRD. Do NOT use to start a new PRD from scratch (use prd-create) or to make minor wording edits that don't need a structured review.
---

# Review a Product Requirements Document

Read the existing PRD, surface findings as a structured list, work through them with the user, and write an updated version to the same path.

## Environment

This skill runs in both Claude Code and Claude chat. Behavior differs in two places:

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the PRD** | Read directly from `docs/features/{feature}/prd.md` | Ask the user to paste the current PRD into the conversation |
| **Writing the updated PRD** | Write to the same path on disk | Produce as a markdown artifact; remind the user to replace the file at its original path |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface ADR-worthy decisions clearly; tell the user to take them into Claude Code and run `adr-write` for each |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat. Everything else — the findings list, suggested resolutions, and running log — is identical in both environments.

## Review perspective

Read the PRD as an engineer who is about to write the tech spec. For each section, ask: do I have enough information to make technical decisions here, or will I have to go back to the product? Gaps and ambiguities that would force a tech-spec question are the highest-priority findings.

Also list every file in `docs/adr/` and read each title. For any title that sounds like it could cap product scope — users, tenancy, regions, languages, roles, pricing, deployment targets — read the full ADR. Skip titles that are clearly purely technical (storage engines, serialization formats, library choices). A PRD requesting something a scope-capping ADR has ruled out is a finding that needs either a PRD adjustment or a superseding ADR.

If the review was triggered by handoff from `/spec-review` — either a `docs/features/{feature}/prd-handoff.md` file or a handoff block pasted into the conversation — treat each entry in both sections ("Unresolved flags needing product resolution" and "Spec decisions with PRD impact") as a pre-seeded finding. Work through them alongside anything discovered fresh. Write the resolution into the PRD at the section where it belongs, not into a "Resolved Flags" appendix.

In Claude Code, once every handoff item is resolved (either answered in the PRD or explicitly deferred by the user), delete `prd-handoff.md` so the workflow state is self-cleaning. In Claude chat, tell the user the handoff items are resolved and the flags can now be cleared on the return pass through `/spec-review`.

## Finding categories

- **Gaps.** Domains absent or thin — no non-goals, problem stated in one sentence when it needs three, no audience statement when the product serves multiple distinct roles. Do not raise "missing success metrics" as a gap unless the PRD makes an outcome claim that requires measurement to verify — success metrics measure whether the PRD was right, not whether the work was done, and their absence is fine when no post-ship outcome is plausible.
- **Inconsistencies.** Contradictions within the document — scope says X but a user story implies not-X, a constraint rules out something the requirements ask for.
- **Unresolved open questions.** Questions listed in the Open Questions section without answers, or questions implicit in the text that were never surfaced. When proposing candidate open questions, filter out anything whose answer lives in an interface signature, a config key, an exit code, or a middleware shape — those are tech-spec questions and belong there. PRD open questions concern users, scope, scenarios, and outcomes.
- **Implicit assumptions.** Things that require context from outside the document to understand. If it requires memory of the original discussion, it needs to be written down.
- **Scope ambiguity.** Requirements that could be interpreted multiple ways by an engineer — anything that would force a judgment call during implementation that should have been a product decision.

## Surfacing findings

Generate the full findings list and present it to the user, then immediately start working through the first finding. Do not pause to ask whether to dismiss, reorder, or add items — the user can redirect at any point as items come up, but the default is forward motion. Showing the list gives shape; asking permission to proceed just adds friction.

For each finding, present the options as a numbered list with one option explicitly flagged as recommended, followed by your reasoning, and an invitation for the user to pick one or propose another. Use this format:

```
**Option 1** (recommended) — ...
**Option 2** — ...
**Option 3** — ...

I recommend Option 1 because <reason>. Pick one or propose another.
```

Numbered options let the user respond "go with 2" without re-typing. The inline `(recommended)` tag and the rationale line below make the pick explicit. Two options are fine when there are only two real choices; a single "recommended" option with no alternatives is fine when the decision is clear. What is never fine is a bare list without a pick — the user came to you for a recommendation.

Work through findings one at a time. Resolve each before moving to the next.

Keep a running log of decisions made during the review. Show it on request, and whenever you finish a finding category (gaps → inconsistencies, etc.) before moving to the next.

## Writing the updated document

Write the updated PRD to the same path — do not create a new file or change the feature slug unless the user asks.

Incorporate resolved findings. Preserve sections that did not change. Do not add sections for findings the user dismissed or deferred.

Write for a reader who was not in the review discussion. No deictic references, no references to ideas considered and dropped during the review conversation.

## At the end of the review

1. Confirm the updated file was written with its path.
2. Review the running decision log. Offer to capture architecture-level decisions as ADRs via `adr-write`.
3. Do not commit. The user handles commits.
