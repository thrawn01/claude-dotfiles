---
name: spec-review
description: Review an existing tech spec for gaps, inconsistencies, unresolved soft flags, and ambiguities that would force implementation decisions during the build, then produce an updated version. Use when the user asks to "review the tech spec", "check the spec", or "update the spec"; or when a plan-from-prompt session has surfaced technical questions that need to be resolved back in the spec. Do NOT use to start a new tech spec from scratch (use spec-create) or to make minor wording edits that don't need a structured review.
allowed-tools: Read, Edit, Bash, Agent, AskUserQuestion
---

# Review a Technical Spec

## Goal

Make the spec implementable: an engineer can build the feature from this spec without getting stuck on ambiguous contracts, contradictory requirements, or missing decisions. The review is done when a goal-validation agent confirms this — not when it runs out of findings to file. The skill does not pursue completeness, exhaustiveness, or editorial polish.

## How it works

The orchestrator runs a review cycle (find issues → validate → skeptic → fix → apply), then a **goal validation agent** reads the updated spec cold and answers: "Is this spec implementable?" If yes, the review is done. If no, the validator names specific blockers and those become the sole inputs for the next cycle (max 5 iterations).

## Environment

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the spec** | Read from `docs/features/{feature}/tech-spec.md` | Ask the user to paste the spec |
| **Writing the updated spec** | Write to the same path on disk | Produce as markdown artifact; remind user to replace the file at its original path |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface decisions clearly; user takes them to Claude Code |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat.

## Inputs

The skill expects a tech spec file. If `$ARGUMENTS` is provided, treat it as a path to the spec file. Otherwise, search for `tech-spec.md` in `docs/features/` directories under the current working directory.

Before starting, locate and read these files:
- The tech spec file (required)
- The PRD — look for `prd.md` in the same directory or parent directories (required for soft-flag analysis; proceed without if not found)
- User stories — look for `user-stories.md` or `stories.md` in the same directory as the spec. Optional — skip if not found. When present, use as an additional cross-reference: stories describe the user-facing workflows the spec must support, so a spec gap that leaves a story unimplementable is a higher-priority finding.
- `CONTEXT.md` — look in the `docs/` directory at the service root (i.e., walk up from the feature directory to find `docs/CONTEXT.md`). This is the domain glossary that defines canonical terminology. Optional — skip if not found.
- Spec handoff file — look for `docs/features/{feature}/spec-handoff.md`. If present (from a prior `/prd-review` run), treat each entry as a pre-seeded finding alongside drift findings and soft-flag triage results. Include the entries in the PRE-SEEDED FINDINGS block passed to the review agent. In Claude Code, delete the handoff file once every item is resolved.

If the tech spec file cannot be found, ask the user for the path.

Derive the `{feature}` slug from the spec file path — the directory name under `docs/features/`. For example, `docs/features/enrollment/tech-spec.md` yields `{feature}` = `enrollment`. This slug is used in the handoff file path and template at the end of the review.

Additionally, list files in the `adr/` directory at the service docs root (e.g., `docs/adr/`). Do NOT read the ADR files upfront. Instead, pass the list of ADR filenames and paths to the sub-agents so they can read specific ADRs on demand if a finding needs architectural context to validate.

## Orchestrator Pre-work

Before entering the iteration loop, the orchestrator performs two tasks that require broad access. Their outputs are passed to the sub-agents as pre-seeded context.

### Coverage pass

Read the spec end-to-end and build a coverage map — note which sections or paragraphs cover which topics (components, data, API, migrations, failure modes, testing surfaces, etc.), using section headings or line references. Also list every file in `docs/adr/` and read each title. Read the full ADR for any title that names a topic the spec touches. The spec must be consistent with these decisions, and ADR-settled topics are not gaps just because the spec refers out to them instead of restating them.

This is the step that prevents false-positive findings. Include the coverage map in the review agent prompt so it generates findings against the map and ADR set, not against an abstract checklist.

### Code drift scan

Scan the code that implements (or partially implements) the spec. Where the spec and the code disagree, those disagreements become pre-seeded drift findings. For each, note: the spec passage, the code location, what differs, and an **authoritativeness classification** — either **code-is-authoritative** (the code has been shipped/tested and the spec simply wasn't updated) or **unclear** (genuine ambiguity about whether the spec or the code is correct). This classification determines Phase 5 routing: code-is-authoritative drift gets auto-applied, unclear drift gets surfaced to the user.

If the review was triggered by a `plan-from-prompt` session that surfaced technical questions, those questions are also pre-seeded findings — include them alongside drift findings.

### Soft-flag triage

For each `[NEEDS PRD CLARIFICATION: ...]` marker in the spec, check whether the question has since been answered elsewhere in the spec or in the linked PRD. Classify each as **stale** (answer exists) or **unresolved** (genuinely unanswered). Include the classification and evidence in the pre-seeded context for the review agent.

## Iteration Loop

Run Phases 1–5 followed by Phase 6 (Goal Validation) as a loop. Each iteration reviews the current state of the tech spec file (which may have been updated by previous iterations).

**Stop conditions** — exit the loop when ANY of these are true:
- Phase 6 (Goal Validation) returns **PASS** — the spec is implementable
- 5 iterations have completed (hard cap)

**Do NOT exit** just because an iteration produced zero findings or zero applied fixes — always run Phase 6 to confirm the spec is implementable. The goal validation is the authoritative exit signal.

Track across iterations:
- `total_auto_applied`: running count of all auto-applied fixes (spec was edited)
- `total_user_resolved`: running count of findings the user resolved with a spec edit (user chose an option that changed the spec)
- `total_user_dismissed`: running count of findings the user dismissed without a spec change ("no change needed", "defer", "skip")
- `total_validation_fp`: running count of false positives caught by the validation agent (Phase 2)
- `total_skeptic_rejections`: running count of findings the skeptic downgraded (Phase 3)

At the start of iteration 2+, re-read the tech spec file to pick up changes from prior iterations and rebuild the coverage map from the updated spec before spawning the Phase 1 agent. Tell the user which iteration is starting (e.g., "Starting iteration 2 — re-reviewing after 4 fixes applied.").

Maintain a **deferred list** of findings the user explicitly dismissed or deferred ("no change needed", "defer", "skip"). Include the deferred list in the Phase 1 prompt for iteration 2+ alongside PRIOR FIXES APPLIED, so the review agent does not re-file them. A deferred finding should only re-surface if the spec text around it changed in a way that makes the original dismissal no longer apply.

**Iteration 2+ input scoping:** In iteration 2+, the Phase 1 review agent receives ONLY the blockers identified by the Phase 6 goal validation agent from the previous iteration. It does not perform an open-ended review. Its job is to produce findings and fixes for those specific blockers only.

## Phase 1: Review Agent

Spawn a sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) with the following responsibilities:

**Prompt structure:**

```
You are reviewing a tech spec for gaps, inconsistencies, and ambiguities that would force implementation decisions during the build. Read all provided content fully before producing findings.

TECH SPEC CONTENTS:
<paste the full text of the tech spec file — do NOT paste just the path>

PRD CONTENTS:
<paste the full text of the PRD, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map — section headings, what each covers, which ADRs were read>

PRE-SEEDED FINDINGS (from orchestrator):
<paste any drift findings from code scan, pre-seeded questions from plan-from-prompt, and soft-flag triage results>

ITERATION: <N of max 5>
<if iteration 2+, include:>
PRIOR FIXES APPLIED: <brief list of fixes from previous iterations so you don't re-file them>
DEFERRED FINDINGS (user dismissed — do NOT re-file unless surrounding spec text changed): <list of deferred finding titles and categories>
BLOCKERS FROM GOAL VALIDATION (iteration 2+ only — these are your ONLY inputs, do not perform an open-ended review): <paste the specific blockers the goal validation agent identified>

For each finding, use this format:

### Finding <N>: <short title>
**Category**: <one of the categories below>
**Priority**: <P0, P1, or P2>
**Section**: <spec section heading where the issue lives, or "N/A" for gaps>
**Authoritativeness**: <only for Drift from code: "code-is-authoritative" or "unclear">
**Evidence**: <see evidence rules below>
**Issue**: <precise description>
**Suggested fix**: <concrete suggested change>

PRIORITY DEFINITIONS:
- **P0** — blocks planning or build (drift from code, implementation-blocking ambiguity, unresolved soft flag the planner must know).
- **P1** — forces a build-time decision the engineer shouldn't be making alone.
- **P2** — polish, clarity, small inconsistency.

Do NOT file findings below P2 severity. Skip them entirely.

THE IMPLEMENTABILITY TEST — every finding MUST pass this gate:
Could an engineer reading ONLY this spec (plus PRD and ADRs) get stuck, build the wrong thing, or make an irreversible mistake because of this issue? If the answer is "no, a competent engineer would figure it out from context," do NOT file the finding. Specs are not exhaustive implementation guides — they define contracts, boundaries, and decisions. Implementation details that an engineer will naturally resolve during the build are not findings.

FINDING CATEGORIES (use exactly these labels):

1. **Gap** — A topic that the PRD or user stories explicitly require BUT is entirely absent from the spec. Not "covered briefly," not "addressed under a different heading." If the spec says anything substantive about the topic — even one sentence — it is not a gap. Content that is present but too thin belongs under Ambiguous implementation decision. Check the coverage map before filing a gap. A topic the PRD does not mention is NOT a gap — do not invent requirements the product hasn't asked for.
2. **Inconsistency** — Technical contradictions within the document.
3. **Drift from code** — The spec no longer matches what has been implemented. Pre-seeded drift findings from the orchestrator should be included verbatim unless you find they are incorrect. For each drift finding, include an **Authoritativeness** field: **code-is-authoritative** (the code is shipped/tested and the spec wasn't updated) or **unclear** (genuine ambiguity about which is correct). Use the orchestrator's pre-seeded classification as a starting point but override it if your review of the evidence warrants.
4. **ADR conflict** — The spec contradicts, ignores, or silently re-decides something already settled in an ADR. Read the relevant ADR before filing.
5. **Stale soft flag** — A `[NEEDS PRD CLARIFICATION: ...]` marker whose question has already been answered elsewhere. Quote the marker and the passage that answers it.
6. **Unresolved soft flag** — A `[NEEDS PRD CLARIFICATION: ...]` marker whose question is genuinely unanswered. Quote the marker and confirm the spec and PRD do not answer it.
7. **Ambiguous implementation decision** — Requirements where two specific, named interpretations exist that produce incompatible behavior or data contracts. You MUST name both interpretations and explain why they are incompatible. "Could be clearer" or "doesn't specify the exact algorithm" is NOT an ambiguity — it's an implementation detail the engineer resolves.
8. **Missing testing surface** — No testable entry point; external dependency without a substitute; async behavior with no observable assertion path; time coupling without an injected clock; in-memory store without a parity-testing model. Only file this if the PRD or user stories require the behavior to be tested AND the spec provides no way to observe it. Do not invent testing requirements the PRD doesn't establish.
9. **Missing failure mode** — Error handling, rollback, or degradation behavior is not specified for a path that the PRD or user stories explicitly require to be handled gracefully. Do not flag failure modes for paths the spec intentionally leaves to infrastructure defaults or standard error propagation.
10. **Implementation leakage** — Content in the spec that belongs in code: function bodies, full SQL statements, rendered config, pinned versions, internal-only log text, test bodies, directory trees. Signatures, type definitions, schema, and externally-visible text stay.

EVIDENCE RULES — every finding MUST include evidence:
- For Gaps: name the topic, state which section headings you searched, confirm it was not addressed.
- For Inconsistencies, Ambiguities, Drift, Implementation leakage: quote the problematic passage(s).
- For Stale soft flags: quote the marker verbatim AND quote the passage that answers it.
- For Unresolved soft flags: quote the marker verbatim, state you checked spec and PRD for an answer.
- If you cannot produce evidence, do not file the finding.

IMPORTANT RULES:
- Generate findings against the coverage map. Do not flag gaps for topics the map shows are covered.
- ADR-settled topics are not gaps just because the spec refers out to them.
- Do not flag a soft flag as unresolved without first confirming the spec and PRD have not already answered it. Use the orchestrator's soft-flag triage as a starting point.
- Use the CONTEXT.md domain glossary (if provided) to verify terminology is used correctly.
- If this is iteration 2+, do NOT re-file findings that match fixes already applied.

ANTI-SCOPE-EXPANSION RULES:
- Do NOT suggest the spec should cover topics it never claimed to cover. A spec defines its own scope. If it doesn't mention caching, that is not a "gap" unless the PRD or user stories require caching.
- Do NOT flag missing detail when the spec's level of abstraction is intentionally high for that section. A one-sentence description of a non-critical component is sufficient if the contracts are clear.
- Do NOT suggest adding sections, subsections, or content areas that go beyond what the PRD requires. The spec should be as short as possible while remaining unambiguous on contracts and decisions.
- Do NOT flag "what if" scenarios unless the PRD or user stories explicitly require handling them. Hypothetical edge cases that aren't in the requirements are not findings.
- Do NOT re-file findings that address the same conceptual area as a finding already resolved, dismissed, or deferred in a prior iteration or prior review run. If the spec text hasn't changed, the finding is stale.
```

The prompt template above uses `<paste the full text of ...>` placeholders. The orchestrator MUST read each file (spec, PRD, user stories, CONTEXT.md) and paste its full contents into the prompt — not just the file path. Sub-agents cannot read files the orchestrator has not provided. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 2: Validation Agent

Take the findings from Phase 1 and spawn a second sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) to validate each one.

**Prompt structure:**

```
You are a second-opinion reviewer. Your job is to verify whether each finding below is correct by cross-referencing the tech spec, PRD, ADRs, and domain glossary.

TECH SPEC CONTENTS:
<paste the full text of the tech spec file>

PRD CONTENTS:
<paste the full text of the PRD, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For EACH finding, read the cited section and evidence, then classify as:

- **Confirmed**: The finding is factually correct. The evidence holds up. One sentence explaining why.
- **False positive**: The finding is wrong. Explain specifically why — e.g., "The spec covers this under section X", "The ADR already settles this", "The quoted passage is taken out of context."
- **Needs clarification**: The finding identifies a real ambiguity, but the spec and PRD are both ambiguous or silent on the topic. The user needs to make a design decision. One sentence framing the question.

RULES FOR REJECTION:
- If the finding claims something is "missing" but the coverage map shows it is addressed under a different heading, reject it.
- If the finding claims a "contradiction" but the two passages use different words for the same concept, reject it.
- If the finding claims drift from code, verify the code location exists and actually differs before confirming.
- If the finding flags an ADR conflict, read the ADR and verify the conflict is real.
- If the finding flags a soft flag as unresolved, check the spec and PRD for an answer before confirming.
- If the finding flags a terminology issue, check the CONTEXT.md glossary (if provided) before confirming.

FINDINGS TO ASSESS:
<paste all findings from Phase 1>
```

Read the tech spec, PRD, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 3: Skeptic Agent

Take only the **Confirmed** findings from Phase 2 and spawn a third sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) whose job is to argue against each one.

If Phase 2 produced zero confirmed findings, skip this phase entirely.

**Prompt structure:**

```
You are a skeptic reviewer. Your job is to argue AGAINST each confirmed finding below. You are the defense attorney for the tech spec — try to prove that each finding is wrong, unnecessary, or overstated.

TECH SPEC CONTENTS:
<paste the full text of the tech spec file>

PRD CONTENTS:
<paste the full text of the PRD, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For EACH confirmed finding, read the actual spec text yourself (do not trust the quoted excerpts — verify them). Then classify as:

- **Upheld**: You tried to argue against it but could not. The finding is genuinely correct. One sentence on why your best counterargument fails.
- **Downgraded to false positive**: The finding is wrong despite two prior agents agreeing. Explain specifically what they both missed.
- **Downgraded to clarification**: The finding was marked confirmed but the spec is actually ambiguous on this point AND the ambiguity concerns an API, architecture, or contract decision the user must make. Frame the ambiguity.
- **Dismissed as implementation detail**: The finding touches internal behavior (data structure housekeeping, algorithm internals, protocol mechanics, optimization choices) that an engineer will resolve during implementation and verify through tests. It does not affect the spec's API, architecture, or contracts. One sentence naming what it is and why the engineer will handle it.

SKEPTIC RULES:
- VERIFY every quote. If the finding misquotes the spec or PRD (even slightly), downgrade it.
- Check whether the "missing" content is covered by a different section than the one cited.
- Check whether a section uses broader language that encompasses the specific behavior the finding says is missing.
- If the suggested fix would add redundant information already implied by existing content, downgrade it.
- If the finding's priority seems inflated (labeled P0 but an engineer would likely get it right anyway from context), downgrade to clarification or false positive.
- If the finding concerns internal implementation mechanics (map pruning, cache eviction timing, internal state cleanup, algorithm steps) rather than API/architecture decisions, dismiss it as an implementation detail.
- For drift findings, verify the code location and confirm the divergence is real, not a naming difference.
- Be aggressive but honest — if the finding is genuinely correct, uphold it. Do not downgrade valid findings just to reduce the count.

SCOPE-EXPANSION SKEPTICISM — apply these additional checks aggressively:
- **Implementability test**: Would an engineer actually get stuck here, or would they figure it out? If the answer is "they'd figure it out," dismiss as implementation detail.
- **Requirement tracing**: Does the PRD or user stories actually require the behavior the finding says is missing? If not, dismiss as scope expansion.
- **Spec-is-not-a-tutorial test**: Is the finding asking the spec to explain HOW to implement something rather than WHAT the contract is? Dismiss as implementation detail.
- **Diminishing returns test**: Is this finding making the spec longer without making it less ambiguous on any contract or decision? Dismiss as false positive.

CONFIRMED FINDINGS TO CHALLENGE:
<paste only confirmed findings from Phase 2, including the validation agent's confirmation reasoning>
```

Read the tech spec, PRD, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 4: Fix Proposal Agent

After the skeptic pass completes (or after Phase 2 if skeptic was skipped), collect all surviving findings:

- **Upheld** findings from Phase 3 (or **Confirmed** findings from Phase 2 if Phase 3 was skipped)
- **Needs clarification** findings from Phase 2
- **Downgraded to clarification** findings from Phase 3

Discard all **False positive**, **Downgraded to false positive**, and **Dismissed as implementation detail** findings — they do not reach the fix proposal agent. Do not mention them to the user unless asked.

If no surviving findings remain, skip this phase and Phase 5 — no fixes were applied this iteration, so proceed directly to the loop-exit check (the loop will exit since zero fixes were applied).

Spawn a sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) to propose concrete fixes for every surviving finding and pick the best option for each.

**Prompt structure:**

```
You are a fix proposal agent. For each finding below, propose 2–3 concrete fix options for the tech spec, then pick the best one. Your job is to turn each finding into an actionable spec edit with a clear recommendation.

TECH SPEC CONTENTS:
<paste the full text of the tech spec file>

PRD CONTENTS:
<paste the full text of the PRD, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map — section headings, what each covers, which ADRs were read>

For each finding, produce a fix proposal using this format:

### Fix for Finding <N>: <short title>
**Category**: <category from the finding>
**Routing**: <"auto-apply" or "surface-to-user" — see routing rules below>

**Option 1** (recommended) — <one-line summary>
Spec edit: <quote the current spec text to replace, then show the replacement text. Be precise enough that an Edit tool call could apply this.>
Rationale: <why this is the best option>

**Option 2** — <one-line summary>
Spec edit: <same format>
Rationale: <trade-off vs Option 1>

<Option 3 if there are three genuinely different approaches; omit if two covers it>

**Recommendation**: Option <N> because <one sentence>.

ROUTING RULES — classify each finding:

**auto-apply** (clear-cut corrections, no design decision):
- Stale soft flags — remove the marker, reconcile text with the decided answer
- Implementation leakage — remove the content that belongs in code
- Drift from code where Authoritativeness = "code-is-authoritative" — update spec to match reality

**surface-to-user** (requires a design decision):
- Gaps
- Inconsistencies
- ADR conflicts
- Unresolved soft flags
- Ambiguous implementation decisions
- Missing testing surfaces
- Missing failure modes
- Drift from code where Authoritativeness = "unclear"
- Needs clarification (from validation)
- Downgraded to clarification (from skeptic)

FIX PROPOSAL RULES:
- Each option must be a concrete spec edit, not a vague suggestion. Show the old text and new text so it can be applied directly.
- For auto-apply findings, still propose 2+ options and pick the best one — the orchestrator applies the recommended option without user input, but having alternatives documented helps if the edit needs adjustment.
- For surface-to-user findings, the options will be presented to the user for a decision. Make each option distinct with meaningfully different consequences. Do not pad with a "do nothing" option unless deferral is a genuinely reasonable choice.
- Err toward shorter edits. Resolving a finding does not require adding a section — sometimes one sentence or removing a sentence is enough.
- Write for an engineer who was not in the review. No deictic references.
- If two findings are tightly coupled (resolving one affects the other), note the dependency and propose a combined fix.

SURVIVING FINDINGS:
<paste all surviving findings with their full details, category, priority, authoritativeness (for drift), and the agent verdicts (upheld/confirmed/needs-clarification/downgraded-to-clarification)>
```

The prompt template above uses `<paste the full text of ...>` placeholders. The orchestrator MUST read each file (spec, PRD, user stories, CONTEXT.md) and paste its full contents into the prompt — not just the file path. The SURVIVING FINDINGS block must also be pasted as full text (the finding details, verdicts, and categories from Phases 1–3), not a reference to a prior agent's output. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 5: Apply Fixes and Surface Decisions

Using the fix proposal agent's output from Phase 4, the orchestrator applies or surfaces each proposed fix.

**Stale-text guard:** Before applying any edit, verify the "old text" from the fix proposal still matches the current spec file. In iteration 2+ or after applying prior fixes in the same iteration, the spec may have changed since the fix proposal agent read it. If the old text no longer matches, re-read the affected section and adapt the edit to the current text, preserving the intent of the recommended fix. If the edit cannot be adapted, skip it and note it in the summary.

### Auto-apply findings

For each finding the fix proposal agent routed as **auto-apply**, apply the agent's recommended option directly to the tech spec file using the Edit tool. Use the spec edit (old text / new text) from the recommended option.

If the fix proposal agent flagged two auto-apply findings as tightly coupled with a combined fix, apply the combined edit as a single Edit call rather than two sequential edits that may conflict. If sequential auto-apply edits target overlapping spec text, re-read the affected section after each edit to verify the next edit's old-text still matches before applying.

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

**Clarification findings** (verdict: Needs clarification or Downgraded to clarification) — the spec and PRD are both ambiguous, so this is a product decision, not a spec-edit choice. Before presenting options, include a "Why this matters" explanation so the user understands the technical or product consequence that motivates the question — what scenario, constraint, or downstream decision makes this ambiguity problematic. Present using AskUserQuestion with the ambiguity framed as a question and concrete options derived from the fix proposal agent's output. After the user answers, apply the corresponding spec edit from the fix proposal agent's options (or craft a new edit if the user's answer doesn't match any proposed option).

Cluster a finding with the next one only when the fix proposal agent flagged them as tightly coupled. Resolve each before moving on. Apply the user's chosen option to the spec via the Edit tool immediately after they answer.

Keep a running log of all decisions made during the review (both auto-applied and user-resolved). Show it on request, and whenever you finish a finding category before moving to the next.

If the user pushes back with "that's already in the spec," stop and re-read the section they point to before continuing.

### Proceed to Goal Validation

After processing all findings for this iteration, proceed to Phase 6 (Goal Validation) to determine whether the spec is now implementable.

## Phase 6: Goal Validation

After Phase 5 completes (or after Phase 1 produces zero findings), spawn a sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) that reads the spec with fresh eyes and evaluates implementability.

This agent is separate from the review agent — it has no knowledge of what findings were filed or fixed. Its only job is to answer: "Can an engineer build this?"

**Prompt structure:**

```
You are a goal validation agent. Your job is to determine whether this tech spec is IMPLEMENTABLE — meaning an engineer can build the feature from this spec without getting stuck on ambiguous contracts, contradictory requirements, or missing decisions.

You are NOT a reviewer. Do NOT look for things to improve, polish, or expand. You are answering one question: if an engineer sat down to build this tomorrow with only this spec (plus the PRD and ADRs), would they get stuck anywhere?

TECH SPEC CONTENTS:
<paste the full text of the tech spec file>

PRD CONTENTS:
<paste the full text of the PRD, or "not found">

USER STORIES:
<paste the full text of user-stories.md or stories.md, or "not found">

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">

ADR FILES (read on demand if needed):
<list each ADR filename and path, or "none found">

Evaluate the spec against these criteria:

1. **Contracts are unambiguous** — For every API, interface, data model, or component boundary the spec defines, could two engineers independently build compatible implementations? If yes for all, this criterion passes.

2. **No contradictions** — Does the spec contradict itself anywhere? (Not "could be clearer" — actually says two incompatible things.) If no contradictions, this criterion passes.

3. **Decisions are made** — Are there any places where the spec explicitly defers a decision that an engineer would need answered before they can write code? (Unresolved soft flags, TBDs, or "to be determined" language.) If no unresolved blockers, this criterion passes.

4. **PRD coverage** — Does the spec address every requirement in the PRD that needs a technical decision? (Not every PRD bullet needs spec coverage — only those that require architectural or contract decisions.) If yes, this criterion passes.

IMPORTANT RULES:
- A spec does NOT need to be exhaustive to pass. It needs to be unambiguous on contracts and decisions.
- Missing implementation details are NOT blockers. Engineers resolve those during the build.
- Brevity is fine. A one-sentence description of a component is sufficient if the contracts are clear.
- "Could be more detailed" is NOT a blocker. Only "an engineer would get stuck here" is a blocker.
- If the spec is good enough to build from, it PASSES. Do not hold it to an academic standard.

Respond in this format:

**VERDICT**: PASS or FAIL

**Criteria results**:
1. Contracts: PASS/FAIL — <one sentence>
2. Contradictions: PASS/FAIL — <one sentence>
3. Decisions: PASS/FAIL — <one sentence>
4. PRD coverage: PASS/FAIL — <one sentence>

<if FAIL, include:>
**Blockers** (ONLY list items that would cause an engineer to get stuck):
- <Blocker 1: specific description of what's ambiguous/contradictory/missing and WHERE in the spec>
- <Blocker 2: ...>

Maximum 5 blockers. If you find yourself listing more than 5, you are being too strict — re-evaluate whether each is truly a blocker vs. a preference.
```

### Decide whether to loop

Based on the goal validation agent's verdict:

- **PASS** → Exit the loop. The spec is implementable. Proceed to "Writing the updated document."
- **FAIL** → If iteration count < 5, continue to the next iteration. Pass the blocker list to Phase 1 as its ONLY inputs (the review agent addresses these specific blockers, not an open-ended review). If iteration count = 5, exit the loop and report the remaining blockers to the user as unresolved items.

## Writing the updated document

Fixes are applied incrementally during Phase 5 via Edit. After the loop exits, do a final read of the spec to verify all changes landed correctly. If any resolved finding was not yet incorporated, apply it now.

Preserve unchanged sections and their ordering — a review should not reshuffle the document. Remove resolved soft flags; replace each with the actual decision reached. Do not add sections for findings the user dismissed or deferred.

Err toward shorter. Resolving a finding does not require adding a section — sometimes one sentence is enough. A review should sharpen the spec, not inflate it.

Write for an engineer who was not in the review discussion. No deictic references. "We considered X but chose Y because Z" is fine and useful; bare references to the review conversation are not.

## Output

After the loop exits, print a final summary across all iterations:

```
## Spec Review Complete

**Result**: <PASS — spec is implementable | INCOMPLETE — blockers remain after 5 iterations>
**Iterations**: N
**Auto-applied fixes**: N (across all iterations)
- <one-line summary of each auto-applied fix, grouped by iteration>

**User-resolved findings**: N
- <one-line summary of each, grouped by iteration>

**User dismissals**: N (findings the user deferred or skipped without a spec change)
**Validation false positives**: N (rejected by the validation agent)
**Skeptic rejections**: N (downgraded by the skeptic agent)

<if INCOMPLETE, include:>
**Remaining blockers**:
- <blocker from final goal validation that was not resolved>

File updated: <path>
```

## At the end of the review

1. Confirm the updated file was written with its path.
2. If the review resolved or corrected any domain terms, write them to the appropriate `docs/CONTEXT.md` in a single pass alongside the spec update. If the file does not exist, create it in the `docs/` directory closest to the code whose domain it describes.
3. If any unresolved soft flags remain (including those on the deferred list), or if resolved findings have implications that make the PRD inconsistent or out of date, offer to hand the relevant items off to `/prd-review`. See **Handoff to `/prd-review`** below.
4. Review the running decision log. For each decision — apply this checklist. Only offer an ADR if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the spec. Decisions made during a spec review — resolving soft flags, settling ambiguous component ownership, choosing between implementation approaches — are strong ADR candidates when they pass the checklist. Decisions resolved through the `deliberate` skill automatically satisfy "Hard to reverse" and "Result of a real trade-off" — only check "Surprising without context." These should already have been offered as ADR candidates immediately after deliberation resolved; do not re-offer them here.
5. For each decision that passes the checklist, offer to capture it as an ADR: "This looks ADR-worthy — want me to record it?" Invoke `adr-write` for the ones the user approves.
6. Note that the reviewed spec is ready as the primary input to `plan-from-context` or `plan-from-prompt` when the user is ready to plan implementation.
7. Do not commit. The user handles commits.

## Handoff to `/prd-review`

Two kinds of items flow back to the PRD:

- **Unresolved soft flags** — product questions the spec cannot answer on its own.
- **Spec decisions with PRD impact** — decisions made during the review whose consequence is that the PRD is now inconsistent or out of date. Examples: drift reconciled to match code that implemented a different user flow; an ambiguous implementation decision settled in a way that narrows product scope; a departure from an existing ADR that makes the PRD's assumptions obsolete.

Either kind keeps the resolution on the right document — the PRD gets updated, then the spec reflects the final answer on a return pass.

When the user agrees to the handoff:

- **In Claude Code:** write a handoff file to `docs/features/{feature}/prd-handoff.md` with the format below. Tell the user to run `/prd-review` next, then return here to reconcile the spec with the resolved PRD.
- **In Claude chat:** emit the handoff as a markdown block for the user to paste into a new `/prd-review` session. Same format.

Handoff file format:

```markdown
# PRD Handoff from spec-review

Source: docs/features/{feature}/tech-spec.md
Feature: {feature}

## Unresolved flags needing product resolution

- **Flag:** [NEEDS PRD CLARIFICATION: <exact marker text>]
  **Spec context:** <which section/heading the flag appeared in, and the 1–2 sentences of surrounding text>
  **What the spec needs:** <one line restating what decision the engineer is waiting on>

- **Flag:** ...

## Spec decisions with PRD impact

- **Spec change:** <what was decided or changed in the spec during the review>
  **PRD section affected:** <which PRD section is now inconsistent or out of date>
  **What the PRD should do:** <one line — update X, remove Y, add Z>

- **Spec change:** ...
```

Omit either section if it has no entries.

`/prd-review` reads the file (or the pasted block), treats each entry in either section as a pre-seeded finding, and — in Claude Code — deletes the handoff file once every item is resolved, so the state is self-cleaning.
