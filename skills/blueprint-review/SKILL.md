---
name: blueprint-review
description: Review an existing Blueprint (the single product + technical design document) for gaps, inconsistencies, unresolved questions, correctness holes, and ambiguities that would force decisions during the build, then produce an updated version. Use when the user asks to "review the blueprint", "check the blueprint", or "update the blueprint". Reviews both halves and the user-stories section in one pass. Do NOT use to start a new Blueprint from scratch (use blueprint-create) or to make minor wording edits that don't need a structured review.
allowed-tools: Read, Edit, Bash, Agent, AskUserQuestion
---

# Review a Blueprint

## Goal

Make the Blueprint **buildable**: an engineer (or an LLM planner) can take it and build the right feature without getting stuck on ambiguous contracts, contradictory requirements, missing decisions, or unverifiable acceptance criteria — and without the technical half drifting from the product intent. The review is done when a goal-validation agent confirms this, not when it runs out of findings to file. The skill does not pursue completeness, exhaustiveness, or editorial polish.

Because the product definition and technical design live in one document, this review replaces the older separate PRD + tech-spec + stories review pipeline. The cross-document handoff files (`prd-handoff.md` / `spec-handoff.md`) are gone — product↔technical disagreement is now an internal inconsistency the review resolves directly, not a finding handed to another skill.

## How it works

The orchestrator runs a review cycle per iteration — find issues → validate → skeptic → propose fixes → apply — then a **goal validation agent** reads the updated Blueprint cold and answers: "Can an engineer build the right thing from this?" If yes, the review is done. If no, the validator names specific blockers, and those become the sole inputs for the next cycle (max 5 iterations). Phase 6 PASS is the authoritative exit signal — not zero findings.

## Environment

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the Blueprint** | Read from `docs/features/{feature}/blueprint.md` | Ask the user to paste the Blueprint |
| **Writing the updated Blueprint** | Write to the same path on disk | Produce as a markdown artifact; remind the user to replace the file at its original path |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface ADR-worthy decisions clearly; tell the user to run `adr-write` for each in Claude Code |
| **API contract at end** | Author/update the `openapi.yaml` (or equivalent contract source) to match the Blueprint's surface and run the contract lint (`duh lint` / `task duh-gen`) | Provide the updated spec fragment; tell the user to run the lint in Claude Code |
| **Question options** | `AskUserQuestion` tool | Numbered options block in text |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat. Everything else is identical in both environments.

## Inputs

The skill expects a Blueprint file. If `$ARGUMENTS` is provided, treat it as a path to the file. Otherwise, search for `blueprint.md` in `docs/features/` directories under the current working directory.

Before starting, locate and read these:
- The Blueprint file (required).
- `CONTEXT.md` — walk up from the feature directory to find `docs/CONTEXT.md` at the service root. The domain glossary. Optional — skip if not found.
- The implementing code, if any exists — used for the code drift scan (below).

If the Blueprint cannot be found, ask the user for the path.

Derive the `{feature}` slug from the file path — the directory name under `docs/features/`.

Additionally, list files in the `adr/` directory at the service docs root (e.g., `docs/adr/`). Do NOT read the ADR files upfront. Pass the list of filenames and paths to the sub-agents so they can read specific ADRs on demand when a finding needs scope or architectural context.

## Orchestrator Pre-work

Before the iteration loop, the orchestrator performs three tasks that require broad access. Their outputs are passed to the sub-agents as pre-seeded context.

### Coverage pass

Read the Blueprint end-to-end and build a coverage map — note which sections or paragraphs cover which topics across both halves (problem, users, scope, non-goals, correctness constraints, acceptance criteria, success metrics, user stories; functional/API, architecture, data design, security, PII, scale, testing surfaces, failure modes), using section headings or line references. Also note whether the Blueprint has a **Correctness Constraints** section and a **User Stories** section — several finding categories are gated on these.

Then list every file in `docs/adr/` and read each title. Read the full ADR for any title that could cap product scope (users, tenancy, regions, languages, roles, pricing, deployment) OR that names a technical topic the Blueprint touches (storage, API patterns, auth, error handling, deployment). The Blueprint must be consistent with these; an ADR-settled topic is not a gap just because the Blueprint refers out to it instead of restating it.

This is the step that prevents false-positive gap findings. Include the coverage map in the review agent prompt so it generates findings against the map and ADR set, not against an abstract checklist.

### Code drift scan

Scan the code that implements (or partially implements) the technical half. Where the Blueprint and the code disagree, those disagreements become pre-seeded drift findings. For each, note: the Blueprint passage, the code location, what differs, and an **authoritativeness classification** — **code-is-authoritative** (the code is shipped/tested and the Blueprint simply wasn't updated) or **unclear** (genuine ambiguity about which is correct). This classification determines Phase 4 routing: code-is-authoritative drift gets auto-applied; unclear drift gets surfaced to the user.

If a `plan-from-prompt` / `plan-from-context` session triggered this review by surfacing technical questions, those questions are also pre-seeded findings — include them alongside drift findings.

If no implementing code exists yet, skip this scan.

### Soft-flag triage

For each `[NEEDS CLARIFICATION: ...]` marker in the Blueprint, check whether the question has since been answered elsewhere in the document. Classify each as **stale** (answer exists) or **unresolved** (genuinely unanswered). Include the classification and evidence in the pre-seeded context for the review agent.

## Iteration Loop

Run Phases 1–5 followed by Phase 6 (Goal Validation) as a loop. Each iteration reviews the current state of the Blueprint (which may have been updated by previous iterations).

**Stop conditions** — exit when ANY is true:
- Phase 6 (Goal Validation) returns **PASS** — the Blueprint is buildable.
- 5 iterations have completed (hard cap).

**Do NOT exit** just because an iteration produced zero findings or zero applied fixes — always run Phase 6 to confirm buildability. Goal validation is the authoritative exit signal.

Track across iterations:
- `total_auto_applied`: running count of all auto-applied fixes (Blueprint was edited)
- `total_user_resolved`: running count of findings the user resolved with a Blueprint edit
- `total_user_dismissed`: running count of findings the user dismissed without a change ("no change needed", "defer", "skip")
- `total_validation_fp`: running count of false positives caught by the validation agent (Phase 2)
- `total_skeptic_rejections`: running count of findings the skeptic downgraded (Phase 3)

At the start of iteration 2+, re-read the Blueprint to pick up changes from prior iterations and rebuild the coverage map before spawning the Phase 1 agent. Tell the user which iteration is starting (e.g., "Starting iteration 2 — re-reviewing after 4 fixes applied.").

Maintain a **deferred list** of findings the user explicitly dismissed or deferred. Include it in the Phase 1 prompt for iteration 2+ alongside PRIOR FIXES APPLIED, so the review agent does not re-file them. A deferred finding should re-surface only if the Blueprint text around it changed in a way that makes the original dismissal no longer apply.

**Iteration 2+ input scoping:** In iteration 2+, the Phase 1 review agent receives ONLY the blockers identified by the Phase 6 goal validation agent from the previous iteration. It does not perform an open-ended review — its job is to produce findings and fixes for those specific blockers only.

## Phase 1: Review Agent

Spawn a sub-agent (Agent tool, **foreground**, `model: "sonnet"`) with the following prompt.

```
You are reviewing a Blueprint — a single design document holding both a feature's product definition (problem, users, scope, correctness constraints, acceptance criteria, optional user stories) and its technical design (interfaces, architecture, data design, security, PII, scale, testing). Find gaps, inconsistencies, and ambiguities that would force product or implementation decisions during the build, plus places where the technical half does not satisfy the product intent. Read all provided content fully before producing findings.

BLUEPRINT CONTENTS:
<paste the full text of the blueprint.md file — do NOT paste just the path>

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">

ADR FILES (read on demand if needed for scope/architectural context):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator — includes whether a Correctness Constraints section and a User Stories section exist):
<paste the coverage map>

PRE-SEEDED FINDINGS (from orchestrator):
<paste code-drift findings, plan-from-prompt questions, and soft-flag triage results>

ITERATION: <N of max 5>
<if iteration 2+, include:>
PRIOR FIXES APPLIED: <brief list so you don't re-file them>
DEFERRED FINDINGS (user dismissed — do NOT re-file unless surrounding text changed): <titles and categories>
BLOCKERS FROM GOAL VALIDATION (iteration 2+ only — these are your ONLY inputs, do not perform an open-ended review): <paste the blockers>

For each finding, use this format:

### Finding <N>: <short title>
**Category**: <one of the categories below>
**Half**: <Product | Technical | Stories | Cross-half>
**Priority**: <P0, P1, or P2>
**Section**: <Blueprint section heading where the issue lives, or "N/A" for gaps>
**Authoritativeness**: <only for Drift from code: "code-is-authoritative" or "unclear">
**Evidence**: <see evidence rules below>
**Issue**: <precise description>
**Suggested fix**: <concrete suggested change>

PRIORITY DEFINITIONS:
- **P0** — blocks the build (missing core requirement, fundamental scope ambiguity, drift from code, contract ambiguity, an unresolved decision the planner is waiting on).
- **P1** — forces a product or build decision the engineer shouldn't make alone during implementation.
- **P2** — polish, clarity, small inconsistency.

Do NOT file findings below P2. Skip them entirely.

THE BUILDABILITY TEST — every finding MUST pass this gate:
Could an engineer reading ONLY this Blueprint (plus the ADRs) get stuck, build the wrong thing, or make an irreversible mistake because of this issue? If "no, a competent engineer would figure it out from context," do NOT file it. A Blueprint defines intent, contracts, boundaries, and decisions — not exhaustive implementation detail. Details an engineer naturally resolves during the build are not findings.

FINDING CATEGORIES (use exactly these labels). Some are gated — only file them when the noted section exists.

Product half:
1. **Gap (product)** — A product topic the document needs but entirely omits. Not "covered briefly," not "under a different heading." One substantive sentence means it is not a gap; thin coverage belongs under Scope ambiguity. Check the coverage map first. A topic the Blueprint deliberately leaves out of scope is not a gap unless its absence creates a contradiction or blocks the build.
2. **Inconsistency** — Contradictions within the document — scope says X but a story implies not-X; a constraint rules out something the requirements ask for.
3. **ADR conflict** — The Blueprint requests something a scope-capping ADR ruled out, or silently contradicts an ADR-settled decision (product or technical). Read the relevant ADR before filing.
4. **Scope ambiguity** — Requirements an engineer could interpret multiple ways — anything that forces a judgment call during the build that should have been a product decision.
5. **Implicit assumption** — Something that requires context from outside the document to understand. If it requires memory of the original discussion, it must be written down.
6. **Unresolved open question** — Questions in the Open Questions section without answers, or implicit unanswered questions. Product open questions concern users, scope, scenarios, and outcomes. (Technical unknowns belong under Ambiguous implementation decision or as soft flags.)
7. **Correctness gap** — A requirement present and internally consistent but too imprecise for an engineer to write a test without making a product decision: acceptance criteria stated as intentions ("handles errors gracefully"); a domain that clearly has state invariants but none specified; absent behavioral constraints where failure modes are non-obvious; unaddressed concurrency/reversibility/partial-failure for operations where it matters. THRESHOLD: only flag where the domain clearly has a deterministic answer the Blueprint is hiding — not where it is appropriately deferring detail. "Users can filter results" is fine abstraction; "the system processes orders correctly" is a correctness gap. Distinguish missing information (someone knows the answer) from undefined behavior (a product decision not yet made).

Technical half:
8. **Gap (technical)** — A topic the product half explicitly requires but the technical half entirely omits. Same "one sentence means not a gap" rule. A topic the product half does not ask for is NOT a gap — do not invent requirements.
9. **Drift from code** — The technical half no longer matches what has been implemented. Include the pre-seeded drift findings verbatim unless you find them incorrect. Set Authoritativeness: code-is-authoritative or unclear. Use the orchestrator's classification as a starting point; override if the evidence warrants.
10. **Ambiguous implementation decision** — Two specific, named interpretations exist that produce incompatible behavior or data contracts. You MUST name both and explain why they are incompatible. "Could be clearer" or "doesn't specify the exact algorithm" is NOT this — that's an implementation detail.
11. **Missing testing surface** — No testable entry point; an external dependency with no substitute; async behavior with no observable assertion path; time coupling without an injected clock; an in-memory store without a parity-testing model. Only file if the product half requires the behavior to be tested AND the technical half provides no way to observe it.
12. **Missing failure mode** — Error handling, rollback, or degradation behavior unspecified for a path the product half explicitly requires to be handled gracefully. Do not flag paths intentionally left to infrastructure defaults or standard error propagation.
13. **Implementation leakage** — Content that belongs in code: function bodies, full SQL statements, rendered config, pinned versions, internal-only log text, test bodies, directory trees. Signatures are conditional: a **consumer/test-facing** signature stays (a library's exported API, an HTTP/RPC/wire contract — defined completely), but a **frozen signature for an internal surface** (a method or interface that is not a consumer or test boundary) is leakage where only its contract belongs — responsibility, conceptual inputs/outputs, invariants, error categories. Type definitions, schema, and externally-visible text stay. (Exception: a ticket whose explicit deliverable is to draw an internal seam may shape that seam more concretely.)

Correctness translation (only when a Correctness Constraints section exists):
14. **Missing invariant preservation** — The product half defines a state invariant but the technical half does not show how the operations touching its data preserve it (atomicity, validation order, schema constraints). Do not invent invariants the product half didn't state.
15. **Representable illegal state** — The data model permits a state a product invariant forbids, and a structural enforcement (schema constraint, type, foreign key) is clearly feasible but unused and unexplained.
16. **Infeasible behavioral constraint** — The technical half's chosen architecture cannot enforce a product behavioral constraint, or doesn't show how it satisfies it. Quote both.

Domain boundaries:
25. **Domain boundary leak** — A problem domain contains logic that belongs to a domain it calls: branching on which implementation backs an interface, inspecting implementation-specific error types, or relying on an implementation-specific property for a correctness guarantee without that property being a contract of the interface. The canonical case is a caller that changes behavior depending on the storage backend, but applies at every boundary (service → component, component → dependency). Quote the leaking passage. If the leak is in invariant enforcement (an invariant holds only because of a specific implementation's property), also cite the invariant.

Stories (only when a User Stories section exists):
17. **Incorrect story** — A story contradicts the rest of the Blueprint, describes an impossible workflow, or has a factual error.
18. **Missing story** — An important user workflow the product half describes has no corresponding story.
19. **Missing acceptance criterion** — A story exists but lacks a testable acceptance criterion for behavior the Blueprint specifies. (Criterion absent — not present-but-vague; that is category 21.)
20. **Story scope issue** — A story is too broad (epic), too narrow (task), or mixes distinct flows.
21. **Unverifiable criterion** — An acceptance criterion is an intention, not an observable condition; the "Then" clause cannot be mechanically verified ("Then the user feels confident", "Then the order is processed"). Rewrite to specify observable behavior.
22. **Invariant violation (stories)** — A story's workflow/criteria permit a state that violates a product state invariant, OR two individually-correct stories whose combined effect violates an invariant. Check both the individual and the combinatorial case.
23. **Missing correctness story** — The product half has a state invariant or behavioral constraint but no story describes what happens when it is tested (e.g., no "transfer rejected when insufficient balance" for "balance is never negative"). Do not require a story for purely structural invariants with no user-visible behavior.

Cross-half:
24. **Product/technical inconsistency** — The technical half's understanding of a requirement differs from the product half's statement of it — the design implements something the product intent did not ask for, or omits something it did. Quote both passages. (This replaces the old prd↔spec reverse-drift handoff; resolve it here.)

EVIDENCE RULES — every finding MUST include evidence:
- Gaps: name the topic, state which section headings you searched, confirm it was not addressed.
- Inconsistencies, Scope ambiguity, Implicit assumptions, Ambiguous implementation decisions, Implementation leakage, Story issues: quote the problematic passage(s).
- Drift from code: quote the Blueprint passage AND name the code location.
- ADR conflicts: quote the Blueprint passage and name the ADR that constrains it.
- Unresolved open questions: quote the question or identify the implicit one and its section.
- Correctness gaps: quote the imprecise requirement, explain the forced product decision, state whether it is missing information or undefined behavior.
- Stale/unresolved soft flags: quote the marker verbatim; for stale, also quote the passage that answers it.
- Missing invariant preservation: name the invariant, name the operation(s) touching its data, confirm no preservation argument exists.
- Representable illegal state: name the invariant, quote the data-model definition that permits the violating state, name the feasible structural enforcement.
- Infeasible behavioral constraint: quote the constraint, quote the conflicting architectural choice, explain why it cannot be satisfied.
- Domain boundary leak: quote the passage where one domain branches on or relies on another domain's implementation; if the leak is in invariant enforcement, also name the invariant and the implementation-specific property it depends on.
- Invariant violation (stories): name the invariant; for combinatorial, name the two stories and the combined state.
- Missing correctness story: name the constraint, confirm no story addresses its enforcement.
- Product/technical inconsistency: quote both the product passage and the technical passage that diverge.
- If you cannot produce evidence, do not file the finding.

ANTI-SCOPE-EXPANSION RULES:
- A review SHARPENS what the Blueprint already covers — it does not add new features, user segments, integrations, or requirements the author did not include. If a topic is absent, it is intentionally out of scope unless its absence creates a contradiction or blocks the build.
- Generate findings against the coverage map. Do not flag gaps for topics the map shows are covered.
- ADR-settled scope/topics are not gaps just because the Blueprint refers out to them.
- Do not flag missing detail when the level of abstraction is intentionally high for that section; a one-sentence description of a non-critical component is fine if the contracts are clear.
- Do not flag "missing success metrics" unless the Blueprint makes an outcome claim that requires measurement to verify.
- Do not flag "what if" scenarios the product half does not require handling.
- Use the CONTEXT.md glossary (if provided) to verify terminology.
- If iteration 2+, do NOT re-file findings matching fixes already applied.
```

The prompt uses `<paste the full text of ...>` placeholders. The orchestrator MUST read the Blueprint and CONTEXT.md and paste their full contents — not just paths. Sub-agents cannot read files the orchestrator has not provided. Do NOT include ADR contents — only the file list, so the agent reads them on demand.

## Phase 2: Validation Agent

Take the Phase 1 findings and spawn a second sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to validate each.

```
You are a second-opinion reviewer. Verify whether each finding below is correct by cross-referencing the Blueprint, the ADRs, and the domain glossary.

BLUEPRINT CONTENTS:
<paste the full text of the blueprint.md file>

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">

ADR FILES (read on demand if needed):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For EACH finding, read the cited section and evidence, then classify as:
- **Confirmed**: factually correct, evidence holds up. One sentence why.
- **False positive**: wrong. Explain specifically — "covered under section X", "the ADR already settles this", "quoted out of context".
- **Needs clarification**: a real ambiguity, but the Blueprint and available context are both silent or ambiguous, so the user must make a product/design decision. One sentence framing the question.

RULES FOR REJECTION:
- If it claims something is "missing" but the coverage map shows it under a different heading, reject.
- If it claims a "contradiction" but the two passages use different words for the same concept, reject.
- If it claims drift from code, verify the code location exists and actually differs before confirming.
- If it claims a product/technical inconsistency, verify both passages exist and actually diverge.
- If it flags an ADR conflict, read the ADR and verify the conflict is real.
- If it flags a soft flag as unresolved, check the Blueprint for an answer first.
- If it flags a terminology issue, check the CONTEXT.md glossary first.
- If it raises "missing success metrics" but the Blueprint makes no outcome claim needing measurement, reject.

RULES FOR CORRECTNESS / STORY CATEGORIES:
- Invariant violation (stories): verify the invariant is actually stated. Read the criteria literally — do they actively describe a violating state, or are they merely silent? Silence is not permission; confirm only if the criteria actively permit a violation.
- Missing correctness story: verify the constraint is actually in the Correctness Constraints section. Check whether ANY story addresses its enforcement, not just the cited one. "Broader language encompasses it" is NOT enough — the enforcement behavior must be an explicit acceptance criterion.
- Unverifiable criterion: verify it is truly unverifiable, not merely imprecise. "Within 30 seconds" is verifiable; "feels confident" is not.

FINDINGS TO ASSESS:
<paste all findings from Phase 1>
```

Read the Blueprint and CONTEXT.md yourself and include their full contents in the prompt. Do NOT include ADR contents.

## Phase 3: Skeptic Agent

Take only the **Confirmed** findings from Phase 2 and spawn a third sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to argue against each. If Phase 2 produced zero confirmed findings, skip this phase.

```
You are a skeptic reviewer — the defense attorney for the Blueprint. Try to prove each confirmed finding is wrong, unnecessary, or overstated.

BLUEPRINT CONTENTS:
<paste the full text of the blueprint.md file>

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">

ADR FILES (read on demand if needed):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For EACH confirmed finding, read the actual Blueprint text yourself (do NOT trust the quoted excerpts — verify them). Then classify as:
- **Upheld**: you tried to argue against it and could not. One sentence on why your best counterargument fails.
- **Downgraded to false positive**: wrong despite two prior agents agreeing. Explain what they both missed.
- **Downgraded to clarification**: marked confirmed but the Blueprint is actually ambiguous on this point AND the ambiguity is a product/design decision the user must make. Frame the ambiguity.
- **Dismissed as implementation detail**: touches internal behavior (data-structure housekeeping, algorithm internals, protocol mechanics, optimization choices) an engineer resolves during the build and verifies through tests. Does not affect intent, contracts, or architecture. One sentence why the engineer will handle it.

SKEPTIC RULES:
- VERIFY every quote. If the finding misquotes the Blueprint (even slightly), downgrade.
- Check whether the "missing" content is covered by a different section than cited.
- Check whether a section uses broader language that encompasses the specific behavior the finding says is missing.
- If the suggested fix adds redundant information already implied by existing content, downgrade.
- If the priority seems inflated (P0 but an engineer would figure it out from context), downgrade.
- For drift and product/technical-inconsistency findings, verify the second location and confirm the divergence is real, not a wording difference.

SCOPE-EXPANSION SKEPTICISM — apply aggressively:
- **Buildability test**: would an engineer actually get stuck, or figure it out? If they'd figure it out, dismiss as implementation detail.
- **Requirement tracing**: does the product half actually require the behavior the finding says is missing? If not, dismiss as scope expansion.
- **Not-a-tutorial test**: is the finding asking the document to explain HOW to implement rather than WHAT the contract is? Dismiss as implementation detail.
- **Diminishing-returns test**: does the finding make the Blueprint longer without making it less ambiguous on any contract or decision? Dismiss as false positive.

SKEPTIC RULES FOR CORRECTNESS / STORY CATEGORIES:
- Invariant violation (stories): if the criteria are silent on the invariant (neither permitting nor preventing), downgrade — silence is a gap (Missing correctness story), not an active violation.
- Missing correctness story: find an existing story whose criteria explicitly address the constraint's enforcement. "Broader language" is NOT sufficient. If none is explicit, uphold.
- Unverifiable criterion: if you can name a specific concrete assertion a test could make from the criterion, downgrade; otherwise uphold.

Be aggressive but honest — if a finding is genuinely correct, uphold it. Do not downgrade valid findings just to reduce the count.

CONFIRMED FINDINGS TO CHALLENGE:
<paste only confirmed findings from Phase 2, including the validation agent's reasoning>
```

Read the Blueprint and CONTEXT.md yourself and include their full contents. Do NOT include ADR contents.

## Phase 4: Fix Proposal Agent

After the skeptic pass (or after Phase 2 if skeptic was skipped), collect all surviving findings:
- **Upheld** from Phase 3 (or **Confirmed** from Phase 2 if Phase 3 skipped)
- **Needs clarification** from Phase 2
- **Downgraded to clarification** from Phase 3

Discard all **False positive**, **Downgraded to false positive**, and **Dismissed as implementation detail** findings. Do not mention them to the user unless asked.

If no surviving findings remain, skip this phase and Phase 5 — proceed directly to Phase 6 (the loop only exits on a Phase 6 PASS).

Spawn a sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to propose concrete fixes and pick the best option for each.

```
You are a fix proposal agent. For each finding, propose 2–3 concrete fix options for the Blueprint, then pick the best one. Turn each finding into an actionable edit with a clear recommendation.

BLUEPRINT CONTENTS:
<paste the full text of the blueprint.md file>

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">

ADR FILES (read on demand if needed):
<list each ADR filename and path, or "none found">

COVERAGE MAP (from orchestrator):
<paste the coverage map>

For each finding:

### Fix for Finding <N>: <short title>
**Category**: <category from the finding>
**Routing**: <"auto-apply" or "surface-to-user" — see rules below>

**Option 1** (recommended) — <one-line summary>
Blueprint edit: <quote the current text to replace, then the replacement text. Precise enough for an Edit tool call.>
Rationale: <why this is best>

**Option 2** — <one-line summary>
Blueprint edit: <same format>
Rationale: <trade-off vs Option 1>

<Option 3 only if there are three genuinely different approaches>

**Recommendation**: Option <N> because <one sentence>.

ROUTING RULES:

**auto-apply** (clear-cut corrections, no product or design decision, no scope expansion):
- Stale soft flags — remove the marker, reconcile text with the decided answer
- Implementation leakage — remove the content that belongs in code
- Drift from code where Authoritativeness = "code-is-authoritative" — update the Blueprint to match reality
- Product/technical inconsistency where the technical half resolved a detail the product half left vague AND the resolution is the only reasonable one
- Clear-cut story corrections — a Missing acceptance criterion the Blueprint already specifies unambiguously, an Incorrect story factually contradicted by the rest of the Blueprint, or an Unverifiable criterion rewritten to the observable behavior the Blueprint already names. (Story gaps, scope issues, invariant violations, and any correctness story requiring a judgment call stay surface-to-user.)
- NEVER auto-apply anything that adds new requirements, features, user segments, or integrations, or that narrows product scope

**surface-to-user** (requires a product or design decision):
- Gaps (product or technical), Inconsistencies, ADR conflicts, Scope ambiguity, Implicit assumptions, Unresolved open questions, Correctness gaps
- Ambiguous implementation decisions, Missing testing surfaces, Missing failure modes
- Missing invariant preservation, Representable illegal state, Infeasible behavioral constraint, Domain boundary leak
- Story categories requiring a judgment call — Missing story, Story scope issue, Invariant violation (stories), Missing correctness story, and any Missing acceptance criterion / Incorrect story / Unverifiable criterion whose correct resolution is not unambiguous from the rest of the Blueprint
- Drift from code where Authoritativeness = "unclear"
- Product/technical inconsistency where it is genuinely unclear which side is right, or where the technical half narrows product scope
- Needs clarification / Downgraded to clarification

FIX PROPOSAL RULES:
- Do NOT propose fixes that expand scope. If a fix would add a feature/segment/integration, route it surface-to-user and frame it as a question ("Should the Blueprint also cover X?"), not a recommended edit.
- Each option is a concrete edit with old text and new text, applyable directly.
- For auto-apply findings, still give 2+ options and pick one — alternatives help if the edit needs adjusting.
- For surface-to-user findings, make each option distinct with meaningfully different consequences. No padding "do nothing" option unless deferral is genuinely reasonable.
- Err toward shorter edits — sometimes one sentence (or removing one) is enough; resolving a finding rarely requires a new section.
- Write for an engineer who was not in the review. No deictic references.
- If two findings are tightly coupled, note the dependency and propose a combined fix.

SURVIVING FINDINGS:
<paste all surviving findings in full — details, category, priority, authoritativeness (for drift), and verdicts (upheld/confirmed/needs-clarification/downgraded-to-clarification)>
```

The orchestrator MUST paste the full Blueprint, CONTEXT.md, and the full SURVIVING FINDINGS block (not a reference to a prior agent's output). Do NOT include ADR contents.

## Phase 5: Apply Fixes and Surface Decisions

Using Phase 4's output, apply or surface each fix.

**Stale-text guard:** before applying any edit, verify the "old text" still matches the current Blueprint. After prior fixes in the same iteration or in iteration 2+, the file may have changed since the fix agent read it. If the old text no longer matches, re-read the affected section and adapt the edit to the current text, preserving the recommended fix's intent. If it cannot be adapted, skip it and note that in the summary.

### Auto-apply findings

For each finding routed **auto-apply**, apply the recommended option directly with the Edit tool. If two auto-apply findings were flagged tightly coupled with a combined fix, apply it as a single Edit. If sequential auto-apply edits target overlapping text, re-read the affected section after each edit to verify the next edit's old text still matches. After applying, tell the user what was auto-applied in a brief summary, naming the option applied for each.

### Surface trade-off findings

For each finding routed **surface-to-user**, check the verdict:

**Design-decision findings** (verdict: Upheld or Confirmed) — clear issue, user picks an approach. Before presenting, score the finding against the high-impact trigger criteria in the `deliberate` skill. If it is P0 or P1 and 2+ signals fire, run the deliberation protocol — the synthesis replaces the options block. Otherwise present the fix agent's options with `AskUserQuestion`. Frame as "Finding N: <title> (<category>)" with a "Why this matters" explanation in the question text. Place the recommended option first with "(Recommended)" appended. Use the `description` field for trade-offs. Always include your reasoning in the question text.

In Claude chat (no `AskUserQuestion`), fall back to a text options block:

```
**Finding N: <title>** (<category>)
<one-line issue summary>

**Why this matters:** <1-2 sentences on the product or technical consequence of leaving this unresolved — what breaks, what becomes ambiguous for implementers, or what decision gets forced downstream.>

**Option 1** (recommended) — <summary>
**Option 2** — <summary>
**Option 3** — <summary (if present)>

The fix agent recommends Option 1 because <reason>. Pick one or propose another.
```

**Clarification findings** (verdict: Needs clarification or Downgraded to clarification) — the Blueprint and available context are both ambiguous, so this is a decision without a clear right answer. Include a "Why this matters" explanation, then present with `AskUserQuestion` (ambiguity framed as a question, concrete options from the fix agent). After the user answers, apply the corresponding edit (or craft a new one if the answer doesn't match any proposed option).

Cluster a finding with the next only when the fix agent flagged them tightly coupled. Resolve each before moving on. Apply the user's choice immediately after they answer.

Keep a running decision log of everything applied or resolved (auto-applied and user-resolved). Show it on request, and whenever you finish a finding category. If the user pushes back with "that's already in the Blueprint," stop and re-read the section they point to before continuing.

### Proceed to Goal Validation

After processing all findings for this iteration, proceed to Phase 6.

## Phase 6: Goal Validation

After Phase 5 (or after Phase 1 produces zero findings), spawn a sub-agent (Agent tool, **foreground**, `model: "sonnet"`) that reads the Blueprint cold and evaluates buildability. This agent is separate from the review agent — it has no knowledge of what was filed or fixed. Its only job: "Can an engineer build the right thing from this?"

```
You are a goal validation agent. Determine whether this Blueprint is BUILDABLE — an engineer can build the right feature from it without getting stuck on ambiguous contracts, contradictory requirements, missing decisions, unverifiable acceptance criteria, or a technical design that does not match the product intent.

You are NOT a reviewer. Do NOT look for things to improve, polish, or expand. Answer one question: if an engineer (or an LLM planner) sat down to build this tomorrow with only this Blueprint plus the ADRs, would they get stuck anywhere, or build the wrong thing?

BLUEPRINT CONTENTS:
<paste the full text of the blueprint.md file>

CONTEXT FILE (domain glossary):
<paste the full text of CONTEXT.md, or "not found">

ADR FILES (read on demand if needed):
<list each ADR filename and path, or "none found">

Evaluate against these criteria:

1. **Product intent is clear** — Is it unambiguous what the feature must do and for whom? Are the acceptance criteria mechanically verifiable (a test could assert each without human judgment)? If yes, this passes.

2. **Contracts are unambiguous** — For every API, interface, data model, or component boundary, could two engineers independently build compatible implementations? If yes, this passes.

3. **No contradictions** — Does the Blueprint contradict itself anywhere, including between the product half and the technical half? (Not "could be clearer" — actually says two incompatible things.) If none, this passes.

4. **Decisions are made** — Any place the Blueprint defers a decision an engineer needs before writing code (unresolved soft flags, TBDs, "to be determined")? If no unresolved blockers, this passes.

5. **Technical half covers the product half** — Does the technical design address every product requirement that needs a technical decision? (Not every bullet needs coverage — only those requiring an architectural or contract decision.) If yes, this passes.

6. **Correctness preservation** — If there is a Correctness Constraints section: does the technical half show how each state invariant is preserved by the operations that touch it? Does the data model make illegal states unrepresentable where feasible? Does the architecture satisfy each behavioral constraint? Does any invariant's enforcement rely on an implementation-specific property of a dependency without that property being a contract of the interface (domain-boundary leak)? If there is no Correctness Constraints section, this auto-passes. This does NOT require formal proofs — only that a reader can SEE why the design preserves each invariant without figuring it out themselves.

7. **Stories coverage** — If there is a User Stories section: does each story have mechanically-verifiable acceptance criteria, and do the stories cover the workflows and correctness constraints the product half describes? If there is no User Stories section, this auto-passes.

IMPORTANT RULES:
- A Blueprint does NOT need to be exhaustive to pass. It needs to be unambiguous on intent, contracts, and decisions.
- Missing implementation details are NOT blockers — engineers resolve those during the build.
- Brevity is fine. A one-sentence component description is sufficient if the contracts are clear.
- "Could be more detailed" is NOT a blocker. Only "an engineer would get stuck here" or "an engineer would build the wrong thing" is.
- If it is good enough to build from, it PASSES. Do not hold it to an academic standard.

Respond in this format:

**VERDICT**: PASS or FAIL

**Criteria results**:
1. Product intent: PASS/FAIL — <one sentence>
2. Contracts: PASS/FAIL — <one sentence>
3. Contradictions: PASS/FAIL — <one sentence>
4. Decisions: PASS/FAIL — <one sentence>
5. Technical coverage: PASS/FAIL — <one sentence>
6. Correctness: PASS/FAIL/N/A — <one sentence>
7. Stories: PASS/FAIL/N/A — <one sentence>

<if FAIL, include:>
**Blockers** (ONLY items that would cause an engineer to get stuck or build the wrong thing):
- <Blocker 1: specific description of what's ambiguous/contradictory/missing and WHERE>
- <Blocker 2: ...>

Maximum 5 blockers. If you find yourself listing more than 5, you are being too strict — re-evaluate whether each is truly a blocker vs. a preference.
```

### Decide whether to loop

- **PASS** → exit the loop; proceed to "Writing the updated document."
- **FAIL** → if iteration count < 5, continue to the next iteration; pass the blocker list to Phase 1 as its ONLY inputs. If iteration count = 5, exit and report the remaining blockers to the user as unresolved.

## Writing the updated document

Fixes are applied incrementally during Phase 5 via Edit. After the loop exits, do a final read to verify all changes landed. If any resolved finding was not yet incorporated, apply it now.

Preserve unchanged sections and their ordering — a review does not reshuffle the document. Remove resolved soft flags, replacing each with the actual decision. Do not add sections for findings the user dismissed or deferred.

Err toward shorter. Resolving a finding rarely requires a new section. A review sharpens the Blueprint, it does not inflate it. Write for an engineer who was not in the review. No deictic references; "We considered X but chose Y because Z" is fine, a bare reference to "the approach we rejected in review" is not.

## Output

After the loop exits, print a final summary:

```
## Blueprint Review Complete

**Result**: <PASS — buildable | INCOMPLETE — blockers remain after 5 iterations>
**Iterations**: N
**Auto-applied fixes**: N (across all iterations)
- <one-line summary of each, grouped by iteration>

**User-resolved findings**: N
- <one-line summary of each, grouped by iteration>

**User dismissals**: N (findings the user deferred or skipped without a change)
**Validation false positives**: N (rejected by the validation agent)
**Skeptic rejections**: N (downgraded by the skeptic agent)

<if INCOMPLETE, include:>
**Remaining blockers**:
- <blocker from final goal validation that was not resolved>

File updated: <path>
```

## At the end of the review

1. Confirm the updated file was written with its path.
2. If the review resolved or corrected any domain terms, write them to the appropriate `docs/CONTEXT.md` in a single pass alongside the Blueprint update. Because the Blueprint is one document, the glossary is written once. If the file does not exist, create it in the `docs/` directory closest to the code whose domain it describes, using the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md); in a monorepo, route per-service.
3. Review the running decision log. For each decision, apply this checklist — offer an ADR only if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the Blueprint. Decisions made during review — resolving soft flags, settling an ambiguous boundary, choosing between approaches, fixing a product/technical inconsistency — are strong candidates when they pass. Decisions resolved through `deliberate` automatically satisfy "Hard to reverse" and "Result of a real trade-off" — only check "Surprising without context"; these should already have been offered immediately after deliberation resolved, so do not re-offer them here.
4. For each decision that passes, offer to capture it as an ADR: "This looks ADR-worthy — want me to record it?" Invoke `adr-write` for the ones the user approves.
5. **Review the API/contract surface.** If the Blueprint defines or changes a service's consumer-facing contract — DUH-RPC / HTTP / RPC endpoints, request/response schemas, or error codes, i.e. anything in its Functional/contract section — that contract *is* the surface the Blueprint fixes, so bringing the service's contract source into line is part of closing the review, not a downstream build step. Review whether the service's `openapi.yaml` — the active contract version the Blueprint targets (`api/v<N>/openapi.yaml`), or the project's equivalent contract source — needs new or changed paths, schemas, and error responses to match the Blueprint's endpoint table, shared schemas, and error codes — and whether any field name or shape the Blueprint deferred "to openapi authoring" must now be pinned. Then offer to author/update the spec to match and run the contract lint (for DUH-RPC services `duh lint`, usually wrapped by a `task duh-gen` target; otherwise the project's lint target), reporting the lint result. This is contract authoring + validation only — not the generated proto/server/client stubs or handler implementation, which remain the build phase. Skip only when the Blueprint defines no such surface (a pure-internal or infra change with no external contract).
6. Note that the reviewed Blueprint is ready as the primary input to `plan-from-context` or `plan-from-prompt` when the user is ready to plan implementation.
7. Do not commit. The user handles commits.
