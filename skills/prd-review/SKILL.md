---
name: prd-review
description: Review an existing PRD for gaps, inconsistencies, and unresolved open questions, then produce an updated version. Use when the user asks to "review the PRD", "check the PRD", or "update the PRD"; or when a tech-spec session has surfaced product questions that need to be resolved back in the PRD. Do NOT use to start a new PRD from scratch (use prd-create) or to make minor wording edits that don't need a structured review.
allowed-tools: Read, Edit, Bash, Agent, AskUserQuestion
---

# Review a Product Requirements Document

Review an existing PRD using four sub-agent passes per iteration: a review agent finds issues, a validation agent confirms or rejects each finding, a skeptic agent challenges confirmed findings to eliminate false positives, and a fix proposal agent produces concrete PRD edits with recommendations. The orchestrator applies surviving fixes and loops until no new confirmed findings emerge (max 3 iterations).

## Environment

This skill runs in both Claude Code and Claude chat. Behavior differs in two places:

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the PRD** | Read directly from `docs/features/{feature}/prd.md` | Ask the user to paste the current PRD into the conversation |
| **Writing the updated PRD** | Write to the same path on disk | Produce as a markdown artifact; remind the user to replace the file at its original path |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface ADR-worthy decisions clearly; tell the user to take them into Claude Code and run `adr-write` for each |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat. Everything else — the findings list, suggested resolutions, and running log — is identical in both environments.

## Inputs

The skill expects a PRD file. If `$ARGUMENTS` is provided, treat it as a path to the PRD file. Otherwise, search for `prd.md` in `docs/features/` directories under the current working directory.

Before starting, locate and read these files:
- The PRD file (required)
- The tech spec — look for `tech-spec.md` in the same directory (optional — used for reverse drift analysis)
- User stories — look for `user-stories.md` or `stories.md` in the same directory as the PRD. Optional — skip if not found. When present, use as an additional cross-reference: stories describe user-facing workflows the PRD must fully support, so a PRD gap that leaves a story without clear requirements is a higher-priority finding.
- `CONTEXT.md` — look in the `docs/` directory at the service root (i.e., walk up from the feature directory to find `docs/CONTEXT.md`). This is the domain glossary that defines canonical terminology. Optional — skip if not found.
- Handoff file — look for `docs/features/{feature}/prd-handoff.md`. If present, treat each entry as a pre-seeded finding (see Handoff triage below).

If the PRD file cannot be found, ask the user for the path.

Derive the `{feature}` slug from the PRD file path — the directory name under `docs/features/`. For example, `docs/features/enrollment/prd.md` yields `{feature}` = `enrollment`. This slug is used in the handoff file path and template at the end of the review.

Additionally, list files in the `adr/` directory at the service docs root (e.g., `docs/adr/`). Do NOT read the ADR files upfront. Instead, pass the list of ADR filenames and paths to the sub-agents so they can read specific ADRs on demand if a finding needs scope or architectural context to validate.

## Orchestrator Pre-work

Before entering the iteration loop, the orchestrator performs three tasks that require broad access. Their outputs are passed to the sub-agents as pre-seeded context.

### Coverage pass

Read the PRD end-to-end and build a coverage map — note which sections or paragraphs cover which product topics (problem statement, audience, goals, non-goals, requirements, user stories, constraints, open questions, success criteria, etc.), using section headings or line references. Also list every file in `docs/adr/` and read each title. For any title that sounds like it could cap product scope — users, tenancy, regions, languages, roles, pricing, deployment targets — read the full ADR. Skip titles that are clearly purely technical (storage engines, serialization formats, library choices). The PRD must be consistent with scope-capping ADRs, and ADR-settled scope is not a gap just because the PRD refers out to it instead of restating it.

This is the step that prevents false-positive findings. Include the coverage map in the review agent prompt so it generates findings against the map and ADR set, not against an abstract checklist.

### Reverse drift scan

If a tech spec exists for the feature (`tech-spec.md` in the same directory), scan it for divergences from the PRD. Where the tech spec's understanding of requirements differs from the PRD, those disagreements become pre-seeded drift findings. For each, note: the PRD passage, the spec passage, what differs, and a **drift direction** — either **spec-leads** (the spec resolved an ambiguity or made a decision the PRD never captured) or **unclear** (genuine disagreement about the intended product behavior). This classification determines Phase 5 routing: spec-leads drift gets surfaced with a recommendation to adopt the spec's decision into the PRD; unclear drift is a product decision the user must make.

If no tech spec exists, skip this step.

### Handoff triage

If a `prd-handoff.md` file exists (from a prior `/spec-review` run), read it and classify each entry:

- **Unresolved flags needing product resolution** — check whether the PRD already answers the question. Classify as **stale** (answer exists) or **unresolved** (genuinely unanswered).
- **Spec decisions with PRD impact** — check whether the PRD already reflects the spec's decision. Classify as **stale** (PRD is consistent) or **needs update** (PRD contradicts or omits the decision).

Stale entries (answer already exists in the PRD) are resolved here — report them to the user in a brief summary but do not pass them to the review agent as findings. Only unresolved and needs-update entries become pre-seeded findings for the review agent.

## Iteration Loop

Run the phases below as a loop. Each iteration reviews the current state of the PRD file (which may have been updated by previous iterations).

**Stop conditions** — exit the loop when ANY of these are true:
- An iteration produces zero applied fixes (auto-applied or user-resolved edits that changed the PRD)
- 3 iterations have completed

Track across iterations:
- `total_auto_applied`: running count of all auto-applied fixes (PRD was edited)
- `total_user_resolved`: running count of findings the user resolved with a PRD edit (user chose an option that changed the PRD)
- `total_user_dismissed`: running count of findings the user dismissed without a PRD change ("no change needed", "defer", "skip")
- `total_validation_fp`: running count of false positives caught by the validation agent (Phase 2)
- `total_skeptic_rejections`: running count of findings the skeptic downgraded (Phase 3)

At the start of iteration 2+, re-read the PRD file to pick up changes from prior iterations and rebuild the coverage map from the updated PRD before spawning the Phase 1 agent. Tell the user which iteration is starting (e.g., "Starting iteration 2 — re-reviewing after 4 fixes applied.").

Maintain a **deferred list** of findings the user explicitly dismissed or deferred ("no change needed", "defer", "skip"). Include the deferred list in the Phase 1 prompt for iteration 2+ alongside PRIOR FIXES APPLIED, so the review agent does not re-file them. A deferred finding should only re-surface if the PRD text around it changed in a way that makes the original dismissal no longer apply.

## Phase 1: Review Agent

Spawn a sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) with the following responsibilities:

**Prompt structure:**

```
You are reviewing a PRD for gaps, inconsistencies, and ambiguities that would force product decisions during the tech spec or build. Read the PRD as an engineer about to write the tech spec — for each section, ask: do I have enough information to make technical decisions, or will I have to go back to the product? Read all provided content fully before producing findings.

PRD CONTENTS:
<paste the full text of the PRD file — do NOT paste just the path>

TECH SPEC CONTENTS:
<paste the full text of the tech spec, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for scope/architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map — section headings, what each covers, which ADRs were read>

PRE-SEEDED FINDINGS (from orchestrator):
<paste any reverse drift findings from tech spec scan, pre-seeded handoff items, and handoff triage results>

ITERATION: <N of max 3>
<if iteration 2+, include:>
PRIOR FIXES APPLIED: <brief list of fixes from previous iterations so you don't re-file them>
DEFERRED FINDINGS (user dismissed — do NOT re-file unless surrounding PRD text changed): <list of deferred finding titles and categories>

For each finding, use this format:

### Finding <N>: <short title>
**Category**: <one of the categories below>
**Priority**: <P0, P1, or P2>
**Section**: <PRD section heading where the issue lives, or "N/A" for gaps>
**Drift direction**: <only for Reverse drift: "spec-leads" or "unclear">
**Evidence**: <see evidence rules below>
**Issue**: <precise description>
**Suggested fix**: <concrete suggested change>

PRIORITY DEFINITIONS:
- **P0** — blocks tech spec writing (missing core requirement, fundamental scope ambiguity, unresolved handoff item the spec is waiting on).
- **P1** — forces a product decision the engineer shouldn't make alone during implementation.
- **P2** — polish, clarity, small inconsistency.

Do NOT file findings below P2 severity. Skip them entirely.

FINDING CATEGORIES (use exactly these labels):

1. **Gap** — A product topic entirely absent from the document. Not "covered briefly," not "addressed under a different heading." If the PRD says anything substantive about the topic — even one sentence — it is not a gap. Content that is present but too thin belongs under Scope ambiguity. Check the coverage map before filing a gap.
2. **Inconsistency** — Contradictions within the document — scope says X but a user story implies not-X, a constraint rules out something the requirements ask for.
3. **Reverse drift** — The tech spec's understanding of a requirement differs from the PRD. Pre-seeded drift findings from the orchestrator should be included verbatim unless you find they are incorrect. For each, include a **Drift direction** field: **spec-leads** (the spec resolved an ambiguity or made a decision the PRD never captured) or **unclear** (genuine disagreement about the intended product behavior).
4. **ADR conflict** — The PRD requests something a scope-capping ADR has ruled out, or silently contradicts an ADR-settled product decision. Read the relevant ADR before filing.
5. **Unresolved handoff item** — A handoff entry from `/spec-review` whose question is genuinely unanswered. Quote the entry and confirm the PRD does not answer it. (Stale handoff items — where the PRD already answers the question — are resolved during orchestrator pre-work and do not appear as findings.)
6. **Scope ambiguity** — Requirements that could be interpreted multiple ways by an engineer — anything that would force a judgment call during tech spec or implementation that should have been a product decision.
7. **Implicit assumption** — Something that requires context from outside the document to understand. If it requires memory of the original discussion, it needs to be written down.
8. **Unresolved open question** — Questions listed in the Open Questions section without answers, or questions implicit in the text that were never surfaced. Filter out anything whose answer lives in an interface signature, a config key, an exit code, or a middleware shape — those are tech-spec questions and belong there. PRD open questions concern users, scope, scenarios, and outcomes.

EVIDENCE RULES — every finding MUST include evidence:
- For Gaps: name the topic, state which section headings you searched, confirm it was not addressed.
- For Inconsistencies, Scope ambiguity, Implicit assumptions: quote the problematic passage(s).
- For Reverse drift: quote the PRD passage AND the tech spec passage that diverges.
- For ADR conflicts: quote the PRD passage and name the ADR that constrains it.
- For Unresolved handoff items: quote the entry verbatim, state you checked the PRD for an answer.
- For Unresolved open questions: quote the question or identify the implicit question and the section it arises in.
- If you cannot produce evidence, do not file the finding.

IMPORTANT RULES:
- Do NOT expand scope. A review sharpens what the PRD already covers — it does not add new features, new user segments, new integrations, or new requirements the author did not include. If a topic is absent from the PRD, it is intentionally out of scope unless its absence creates an internal contradiction or blocks the tech spec. When in doubt, flag it as a question for the user rather than filing a gap.
- Generate findings against the coverage map. Do not flag gaps for topics the map shows are covered.
- ADR-settled scope is not a gap just because the PRD refers out to it.
- Do not raise "missing success metrics" as a gap unless the PRD makes an outcome claim that requires measurement to verify.
- Use the CONTEXT.md domain glossary (if provided) to verify terminology is used correctly.
- If this is iteration 2+, do NOT re-file findings that match fixes already applied.
```

The prompt template above uses `<paste the full text of ...>` placeholders. The orchestrator MUST read each file (PRD, tech spec, user stories, CONTEXT.md) and paste its full contents into the prompt — not just the file path. Sub-agents cannot read files the orchestrator has not provided. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 2: Validation Agent

Take the findings from Phase 1 and spawn a second sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) to validate each one.

**Prompt structure:**

```
You are a second-opinion reviewer. Your job is to verify whether each finding below is correct by cross-referencing the PRD, tech spec, ADRs, and domain glossary.

PRD CONTENTS:
<paste the full text of the PRD file>

TECH SPEC CONTENTS:
<paste the full text of the tech spec, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for scope/architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For EACH finding, read the cited section and evidence, then classify as:

- **Confirmed**: The finding is factually correct. The evidence holds up. One sentence explaining why.
- **False positive**: The finding is wrong. Explain specifically why — e.g., "The PRD covers this under section X", "The ADR already settles this", "The quoted passage is taken out of context."
- **Needs clarification**: The finding identifies a real ambiguity, but the PRD and any available context are both ambiguous or silent on the topic. The user needs to make a product decision. One sentence framing the question.

RULES FOR REJECTION:
- If the finding claims something is "missing" but the coverage map shows it is addressed under a different heading, reject it.
- If the finding claims a "contradiction" but the two passages use different words for the same concept, reject it.
- If the finding claims reverse drift, verify the tech spec passage exists and actually diverges before confirming.
- If the finding flags an ADR conflict, read the ADR and verify the conflict is real.
- If the finding flags a handoff item as unresolved, check the PRD for an answer before confirming.
- If the finding flags a terminology issue, check the CONTEXT.md glossary (if provided) before confirming.
- If the finding raises "missing success metrics" but the PRD makes no outcome claim that needs measurement, reject it.

FINDINGS TO ASSESS:
<paste all findings from Phase 1>
```

Read the PRD, tech spec, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 3: Skeptic Agent

Take only the **Confirmed** findings from Phase 2 and spawn a third sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) whose job is to argue against each one.

If Phase 2 produced zero confirmed findings, skip this phase entirely.

**Prompt structure:**

```
You are a skeptic reviewer. Your job is to argue AGAINST each confirmed finding below. You are the defense attorney for the PRD — try to prove that each finding is wrong, unnecessary, or overstated.

PRD CONTENTS:
<paste the full text of the PRD file>

TECH SPEC CONTENTS:
<paste the full text of the tech spec, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for scope/architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For EACH confirmed finding, read the actual PRD text yourself (do not trust the quoted excerpts — verify them). Then classify as:

- **Upheld**: You tried to argue against it but could not. The finding is genuinely correct. One sentence on why your best counterargument fails.
- **Downgraded to false positive**: The finding is wrong despite two prior agents agreeing. Explain specifically what they both missed.
- **Downgraded to clarification**: The finding was marked confirmed but the PRD is actually ambiguous on this point AND the ambiguity concerns a product decision the user must make (scope, user behavior, success criteria). Frame the ambiguity.
- **Dismissed as tech-spec concern**: The finding is about an implementation or technical design detail that belongs in the tech spec, not the PRD. It does not affect product scope, user behavior, or requirements. One sentence naming what it is and why it belongs downstream.

SKEPTIC RULES:
- VERIFY every quote. If the finding misquotes the PRD (even slightly), downgrade it.
- Check whether the "missing" content is covered by a different section than the one cited.
- Check whether a section uses broader language that encompasses the specific behavior the finding says is missing.
- If the suggested fix would add redundant information already implied by existing content, downgrade it.
- If the finding's priority seems inflated (labeled P0 but an engineer would likely figure it out from context anyway), downgrade to clarification or false positive.
- If the finding concerns technical implementation details (data model shape, API design, protocol mechanics, algorithm choices) rather than product decisions, dismiss it as a tech-spec concern.
- For drift findings, verify the tech spec passage and confirm the divergence is real, not a wording difference.
- Be aggressive but honest — if the finding is genuinely correct, uphold it. Do not downgrade valid findings just to reduce the count.

CONFIRMED FINDINGS TO CHALLENGE:
<paste only confirmed findings from Phase 2, including the validation agent's confirmation reasoning>
```

Read the PRD, tech spec, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 4: Fix Proposal Agent

After the skeptic pass completes (or after Phase 2 if skeptic was skipped), collect all surviving findings:

- **Upheld** findings from Phase 3 (or **Confirmed** findings from Phase 2 if Phase 3 was skipped)
- **Needs clarification** findings from Phase 2
- **Downgraded to clarification** findings from Phase 3

Discard all **False positive**, **Downgraded to false positive**, and **Dismissed as tech-spec concern** findings — they do not reach the fix proposal agent. Do not mention them to the user unless asked.

If no surviving findings remain, skip this phase and Phase 5 — no fixes were applied this iteration, so proceed directly to the loop-exit check (the loop will exit since zero fixes were applied).

Spawn a sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) to propose concrete fixes for every surviving finding and pick the best option for each.

**Prompt structure:**

```
You are a fix proposal agent. For each finding below, propose 2–3 concrete fix options for the PRD, then pick the best one. Your job is to turn each finding into an actionable PRD edit with a clear recommendation.

PRD CONTENTS:
<paste the full text of the PRD file>

TECH SPEC CONTENTS:
<paste the full text of the tech spec, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for scope/architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map — section headings, what each covers, which ADRs were read>

For each finding, produce a fix proposal using this format:

### Fix for Finding <N>: <short title>
**Category**: <category from the finding>
**Routing**: <"auto-apply" or "surface-to-user" — see routing rules below>

**Option 1** (recommended) — <one-line summary>
PRD edit: <quote the current PRD text to replace, then show the replacement text. Be precise enough that an Edit tool call could apply this.>
Rationale: <why this is the best option>

**Option 2** — <one-line summary>
PRD edit: <same format>
Rationale: <trade-off vs Option 1>

<Option 3 if there are three genuinely different approaches; omit if two covers it>

**Recommendation**: Option <N> because <one sentence>.

ROUTING RULES — classify each finding:

**auto-apply** (clear-cut corrections, no product decision, no scope expansion):
- Reverse drift where Drift direction = "spec-leads" AND the spec's decision is unambiguously correct (e.g., the spec resolved a detail the PRD left vague and the resolution is the only reasonable one)
- NEVER auto-apply a fix that adds new requirements, features, user segments, or integrations not already in the PRD

**surface-to-user** (requires a product decision):
- Gaps
- Inconsistencies
- ADR conflicts
- Unresolved handoff items
- Scope ambiguity
- Implicit assumptions
- Unresolved open questions
- Reverse drift where Drift direction = "unclear" or where "spec-leads" but the spec's decision narrows product scope
- Needs clarification (from validation)
- Downgraded to clarification (from skeptic)

FIX PROPOSAL RULES:
- Do NOT propose fixes that expand the PRD's scope — no new features, user segments, integrations, or requirements the author did not include. Fixes should clarify, correct, or resolve ambiguity within existing scope. If a fix would expand scope, route it as surface-to-user and frame it as a question ("Should the PRD also cover X?"), not a recommended edit.
- Each option must be a concrete PRD edit, not a vague suggestion. Show the old text and new text so it can be applied directly.
- For auto-apply findings, still propose 2+ options and pick the best one — the orchestrator applies the recommended option without user input, but having alternatives documented helps if the edit needs adjustment.
- For surface-to-user findings, the options will be presented to the user for a decision. Make each option distinct with meaningfully different consequences. Do not pad with a "do nothing" option unless deferral is a genuinely reasonable choice.
- Err toward shorter edits. Resolving a finding does not require adding a section — sometimes one sentence or removing a sentence is enough.
- Write for an engineer who was not in the review. No deictic references.
- If two findings are tightly coupled (resolving one affects the other), note the dependency and propose a combined fix.

SURVIVING FINDINGS:
<paste all surviving findings with their full details, category, priority, drift direction (for reverse drift), and the agent verdicts (upheld/confirmed/needs-clarification/downgraded-to-clarification)>
```

The prompt template above uses `<paste the full text of ...>` placeholders. The orchestrator MUST read each file (PRD, tech spec, user stories, CONTEXT.md) and paste its full contents into the prompt — not just the file path. The SURVIVING FINDINGS block must also be pasted as full text (the finding details, verdicts, and categories from Phases 1–3), not a reference to a prior agent's output. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 5: Apply Fixes and Surface Decisions

Using the fix proposal agent's output from Phase 4, the orchestrator applies or surfaces each proposed fix.

**Stale-text guard:** Before applying any edit, verify the "old text" from the fix proposal still matches the current PRD file. In iteration 2+ or after applying prior fixes in the same iteration, the PRD may have changed since the fix proposal agent read it. If the old text no longer matches, re-read the affected section and adapt the edit to the current text, preserving the intent of the recommended fix. If the edit cannot be adapted, skip it and note it in the summary.

### Auto-apply findings

For each finding the fix proposal agent routed as **auto-apply**, apply the agent's recommended option directly to the PRD file using the Edit tool. Use the PRD edit (old text / new text) from the recommended option.

If the fix proposal agent flagged two auto-apply findings as tightly coupled with a combined fix, apply the combined edit as a single Edit call rather than two sequential edits that may conflict. If sequential auto-apply edits target overlapping PRD text, re-read the affected section after each edit to verify the next edit's old-text still matches before applying.

After applying, tell the user what was auto-applied in a brief summary list, including which option was applied for each finding.

### Surface trade-off findings

For each finding the fix proposal agent routed as **surface-to-user**, check the finding's verdict to determine presentation style:

**Design-decision findings** (verdict: Upheld or Confirmed) — these have a clear issue and need the user to pick an approach. Before presenting, score the finding against the high-impact trigger criteria in the `deliberate` skill. If the finding is P0 or P1 and 2+ signals fire, run the deliberation protocol — the synthesis replaces the standard options block below. Otherwise, present the fix proposal agent's options:

```
**Finding N: <title>** (<category>)
<one-line issue summary>

**Why this matters:** <1-2 sentences explaining the technical or product consequence of leaving this unresolved — what breaks, what becomes ambiguous for implementers, or what decision gets forced downstream. For technical findings, explain the specific scenario or constraint that makes this a problem.>

**Option 1** (recommended) — <summary>
**Option 2** — <summary>
**Option 3** — <summary (if present)>

The fix agent recommends Option 1 because <reason>. Pick one or propose another.
```

**Clarification findings** (verdict: Needs clarification or Downgraded to clarification) — the PRD and available context are both ambiguous, so this is a product decision without a clear right answer. Before presenting options, include a "Why this matters" explanation so the user understands the technical or product consequence that motivates the question — what scenario, constraint, or downstream decision makes this ambiguity problematic. Present using AskUserQuestion with the ambiguity framed as a question and concrete options derived from the fix proposal agent's output. After the user answers, apply the corresponding PRD edit from the fix proposal agent's options (or craft a new edit if the user's answer doesn't match any proposed option).

Cluster a finding with the next one only when the fix proposal agent flagged them as tightly coupled. Resolve each before moving on. Apply the user's chosen option to the PRD via the Edit tool immediately after they answer.

Keep a running log of all decisions made during the review (both auto-applied and user-resolved). Show it on request, and whenever you finish a finding category before moving to the next.

If the user pushes back with "that's already in the PRD," stop and re-read the section they point to before continuing.

### Decide whether to loop

After processing all findings for this iteration:

- If any confirmed fixes were applied to the PRD file this iteration (auto-applied edits or user-resolved edits that changed the PRD) AND iteration count < 3, continue to the next iteration (go back to Phase 1).
- User dismissals — where the user chose "no change" or "defer" — do not count as applied fixes and do not trigger another iteration.
- Otherwise, exit the loop.

## Writing the updated document

Fixes are applied incrementally during Phase 5 via Edit. After the loop exits, do a final read of the PRD to verify all changes landed correctly. If any resolved finding was not yet incorporated, apply it now.

Preserve unchanged sections and their ordering — a review should not reshuffle the document. Do not add sections for findings the user dismissed or deferred.

Err toward shorter. Resolving a finding does not require adding a section — sometimes one sentence is enough. A review should sharpen the PRD, not inflate it.

Write for an engineer who was not in the review discussion. No deictic references. "We considered X but chose Y because Z" is fine and useful; bare references to the review conversation are not.

## Output

After the loop exits, print a final summary across all iterations:

```
## PRD Review Complete

**Iterations**: N
**Auto-applied fixes**: N (across all iterations)
- <one-line summary of each auto-applied fix, grouped by iteration>

**User-resolved findings**: N
- <one-line summary of each, grouped by iteration>

**User dismissals**: N (findings the user deferred or skipped without a PRD change)
**Validation false positives**: N (rejected by the validation agent)
**Skeptic rejections**: N (downgraded by the skeptic agent)

File updated: <path>
```

## At the end of the review

1. Confirm the updated file was written with its path.
2. If the review resolved or corrected any domain terms, write them to the appropriate `docs/CONTEXT.md` in a single pass alongside the PRD update. If the file does not exist, create it in the `docs/` directory closest to the code whose domain it describes.
3. In Claude Code, if a `prd-handoff.md` file existed and every handoff item has been resolved (either answered in the PRD or explicitly deferred by the user), delete `prd-handoff.md` so the workflow state is self-cleaning. In Claude chat, tell the user the handoff items are resolved and the flags can now be cleared on the return pass through `/spec-review`.
4. If any findings have implications that make the tech spec inconsistent or out of date, offer to hand the relevant items off to `/spec-review`. See **Handoff to `/spec-review`** below.
5. Review the running decision log. For each decision — product or technical — apply this checklist. Only offer an ADR if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the PRD. Decisions resolved through the `deliberate` skill automatically satisfy "Hard to reverse" and "Result of a real trade-off" — only check "Surprising without context." These should already have been offered as ADR candidates immediately after deliberation resolved; do not re-offer them here.
6. For each decision that passes the checklist, offer to capture it as an ADR: "This looks ADR-worthy — want me to record it?" Invoke `adr-write` for the ones the user approves.
7. Note that the reviewed PRD is ready as input to `spec-create` or `/spec-review` when the user is ready.
8. Do not commit. The user handles commits.

## Handoff to `/spec-review`

Two kinds of items flow forward to the tech spec:

- **PRD decisions with spec impact** — decisions made during the review whose consequence is that the tech spec is now inconsistent or out of date. Examples: a scope change that invalidates a spec section; a requirement rewritten in a way that changes the spec's assumptions; a new constraint added that the spec doesn't account for.
- **New requirements** — gaps filled during the review that the spec does not yet cover.

When the user agrees to the handoff:

- **In Claude Code:** write a handoff file to `docs/features/{feature}/spec-handoff.md` with the format below. Tell the user to run `/spec-review` next to reconcile the spec with the updated PRD.
- **In Claude chat:** emit the handoff as a markdown block for the user to paste into a new `/spec-review` session. Same format.

Handoff file format:

```markdown
# Spec Handoff from prd-review

Source: docs/features/{feature}/prd.md
Feature: {feature}

## PRD decisions with spec impact

- **PRD change:** <what was decided or changed in the PRD during the review>
  **Spec section affected:** <which spec section is now inconsistent or out of date>
  **What the spec should do:** <one line — update X, remove Y, add Z>

- **PRD change:** ...

## New requirements needing spec coverage

- **Requirement:** <the new or expanded requirement from the PRD>
  **PRD section:** <where it appears in the PRD>
  **What the spec needs:** <one line — add section for X, extend Y to cover Z>

- **Requirement:** ...
```

Omit either section if it has no entries.

`/spec-review` reads the file (or the pasted block), treats each entry as a pre-seeded finding, and — in Claude Code — deletes the handoff file once every item is resolved, so the state is self-cleaning.
