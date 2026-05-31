---
name: stories-review
description: Review user stories for gaps, incorrect stories, missing acceptance criteria, and scope issues using a three-pass sub-agent approach (review + validation + skeptic) that loops until clean. Use when the user asks to "review the stories", "check the user stories", "audit the stories", or "validate the stories". Do NOT use to write stories from scratch or for minor wording edits.
allowed-tools: Read, Edit, Bash, Agent, AskUserQuestion
---

# Review User Stories

Review a user stories document against its PRD using three sub-agent passes per iteration: a review agent finds issues, a validation agent confirms or rejects each finding, and a skeptic agent challenges confirmed findings to eliminate false positives. The orchestrator applies surviving fixes and loops until no new confirmed findings emerge (max 3 iterations).

## Inputs

The skill expects a user stories file and a PRD in the same directory. If `$ARGUMENTS` is provided, treat it as a path to the user stories file. Otherwise, search for `user-stories.md` in `docs/features/` directories under the current working directory.

Before starting, locate and read these files:
- The user stories file (required)
- The PRD — look for `prd.md` in the same directory or parent directories (required)
- `CONTEXT.md` — look in the `docs/` directory at the service root (i.e., walk up from the feature directory to find `docs/CONTEXT.md`). This is the domain glossary that defines canonical terminology. Optional — skip if not found.

If the user stories file or PRD cannot be found, ask the user for the path. CONTEXT.md is supplementary — proceed without it if it doesn't exist.

Additionally, list files in the `adr/` directory at the service docs root (e.g., `docs/adr/`). Do NOT read the ADR files upfront. Instead, pass the list of ADR filenames and paths to the sub-agents so they can read specific ADRs on demand if a finding needs architectural context to validate.

## Iteration Loop

Run the phases below as a loop. Each iteration reviews the current state of the user stories file (which may have been updated by previous iterations).

**Stop conditions** — exit the loop when ANY of these are true:
- An iteration produces zero confirmed findings after the skeptic pass
- 3 iterations have completed

Track across iterations:
- `total_confirmed`: running count of all confirmed fixes applied
- `total_clarifications`: running count of all clarifications resolved with the user
- `total_false_positives`: running count of all false positives discarded (including skeptic downgrades)
- `total_skeptic_rejections`: running count of findings the skeptic downgraded

At the start of iteration 2+, re-read the user stories file to pick up changes from prior iterations. Tell the user which iteration is starting (e.g., "Starting iteration 2 — re-reviewing after 4 fixes applied.").

## Phase 1: Review Agent

Spawn a sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) with the following responsibilities:

**Prompt structure:**

```
You are reviewing a user stories document against its PRD. Read all provided files fully before producing findings.

USER STORIES FILE: <path>
PRD FILE: <path>
CONTEXT FILE (domain glossary): <path or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

ITERATION: <N of max 3>
<if iteration 2+, include:>
PRIOR FIXES APPLIED: <brief list of fixes from previous iterations so you don't re-file them>

For each finding, use this format:

### Finding <N>: <short title>
**Category**: <one of the categories below>
**Severity**: <Major or Medium>
**Story**: <story number and name, or "Missing" for gap findings>
**What the story says**: <quote the relevant text, or "N/A" for missing stories>
**What the PRD says**: <quote the relevant PRD text>
**Issue**: <precise description of the discrepancy, gap, or problem>
**Suggested fix**: <concrete suggested change>

SEVERITY DEFINITIONS:
- **Major**: An engineer would build the wrong thing, skip a required workflow, or violate a PRD constraint. Includes: incorrect behavior, missing stories for core workflows, contradictions with PRD requirements, invariant violations, missing correctness stories for critical invariants.
- **Medium**: An engineer could probably figure it out, but the story is incomplete or unclear enough to cause confusion or inconsistency. Includes: missing acceptance criteria for PRD-specified behavior, ambiguous wording where the PRD is clear, scope issues that mix distinct flows, unverifiable acceptance criteria.

Do NOT file findings below Medium severity. Minor wording preferences, style issues, and nitpicks should be omitted entirely.

FINDING CATEGORIES (use exactly these labels):

1. **Incorrect** — Story contradicts the PRD, describes an impossible workflow, or has a factual error.
2. **Missing story** — An important user workflow in the PRD has no corresponding story.
3. **Missing acceptance criterion** — A story exists but is missing a testable acceptance criterion for behavior the PRD specifies.
4. **Scope issue** — A story is too broad (epic) or too narrow (task), or mixes distinct flows.
5. **Ambiguous** — A story or criterion could be interpreted multiple ways; the PRD is clear but the story is not.
6. **Invariant violation** — A story's workflow or acceptance criteria would permit a state that violates a PRD state invariant, or two stories are individually correct but their combined effect violates an invariant. Only file when the PRD has an explicit Correctness Constraints section with state invariants.
7. **Missing correctness story** — The PRD has a state invariant or behavioral constraint in its Correctness Constraints section but no story describes what happens when the constraint is tested (e.g., no story for "transfer rejected when insufficient balance" when the PRD says "balance is never negative"). Only file when the PRD has an explicit Correctness Constraints section.
8. **Unverifiable criterion** — An acceptance criterion is stated as an intention rather than an observable condition. The "Then" clause cannot be mechanically verified by a test (e.g., "Then the user feels confident" or "Then the order is processed"). Rewrite to specify the observable system behavior. NOTE: If a story has criteria but they are theater (unverifiable), file under category 8, not category 3. Category 3 is for absent criteria only — the criterion literally does not exist. Category 8 is for present but unverifiable criteria.

CATEGORY DISAMBIGUATION — invariant-related findings:
- If no story addresses a correctness constraint at all → file category 7 (Missing correctness story).
- If a story exists but its acceptance criteria would permit a state that violates an invariant → file category 6 (Invariant violation).

IMPORTANT RULES:
- Every finding MUST cite specific PRD text. If you cannot quote a PRD passage that supports the finding, do not file it.
- Do NOT file findings about implementation details the PRD intentionally leaves to the tech spec.
- Do NOT file findings about missing personas/actors unless the PRD defines distinct access roles that the stories conflate.
- Do NOT flag the absence of error-handling stories for edge cases the PRD does not mention.
- Do NOT flag subjective style preferences (story granularity, wording choices) unless they create genuine ambiguity.
- Focus on what matters: can an engineer build the right thing from these stories alone, cross-referenced with the PRD?
- Use the CONTEXT.md domain glossary (if provided) to verify terminology is used correctly and consistently across stories. Flag findings where stories use terms that contradict or diverge from the glossary definitions.
- If a finding involves an architectural constraint (e.g., polling vs webhooks, read-only access, deployment model), read the relevant ADR file to verify whether the story aligns with the recorded decision before filing the finding.
- If this is iteration 2+, do NOT re-file findings that match fixes already applied. Focus on new issues or issues introduced by previous fixes.
- For Invariant violation findings: check whether two or more stories, when their workflows are combined, could produce a state that violates a PRD state invariant. Also check individual stories whose acceptance criteria permit an invariant-violating state.
- For Missing correctness story findings: only file when the PRD has an explicit Correctness Constraints section. Check each state invariant and behavioral constraint — does at least one story describe the system's behavior when the constraint is tested? Do not require a story for invariants that are purely structural (enforced by schema/types with no user-visible behavior).
- For Unverifiable criterion findings: apply the test "How would a test know this happened?" If the answer requires human judgment or subjective evaluation, file the finding. Do not flag criteria that are observable but imprecise (e.g., "within 30 seconds" is verifiable even if the threshold is debatable).
```

Read the user stories, PRD, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt so it has everything in context. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 2: Validation Agent

Take the findings from Phase 1 and spawn a second sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) to validate each one.

**Prompt structure:**

```
You are a second-opinion reviewer. Your job is to verify whether each finding below is correct by cross-referencing the user stories, PRD, and domain glossary.

USER STORIES FILE: <path>
PRD FILE: <path>
CONTEXT FILE (domain glossary): <path or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

For EACH finding, read the cited story and PRD section, then classify as:

- **Confirmed**: The finding is factually correct. The story text and PRD text genuinely conflict, or the gap genuinely exists. One sentence explaining why.
- **False positive**: The finding is wrong. Explain specifically why — e.g., "The story already covers this at line N", "The PRD does not actually specify this", "The file referenced does exist."
- **Needs clarification**: The finding identifies a real ambiguity, but the PRD is also ambiguous or silent on the topic. The user needs to make a product decision. One sentence framing the question.

RULES FOR REJECTION:
- If the finding claims something is "missing" but the behavior is logically implied by existing acceptance criteria, reject it.
- If the finding claims a "contradiction" but the two texts use different words for the same concept, reject it.
- If the finding is about a file not existing, verify by checking the filesystem before confirming.
- If the finding is about story ordering or bullet ordering implying execution order, reject it — unordered lists do not imply sequence.
- If the finding recommends changing actor/persona labels but the PRD uses the same labels, reject it.
- If the finding involves an architectural constraint, read the relevant ADR file before confirming or rejecting.
- If the finding flags a terminology issue, check the CONTEXT.md glossary (if provided) before confirming or rejecting.

RULES FOR NEW CATEGORIES:
- For Invariant violation (category 6): verify the PRD actually states the invariant cited. Read the story's acceptance criteria literally — does the criteria explicitly permit a violating state, or does the finding assume a violation that the criteria are silent on? Silence is not permission; only confirm if the criteria actively describe a state that violates the invariant.
- For Missing correctness story (category 7): verify the PRD's Correctness Constraints section actually contains the cited invariant or constraint. Check whether ANY story in the file addresses the constraint, not just the section the finding cites. If a workflow story's acceptance criteria already cover the constraint's rejection behavior, reject the finding. Do not reject just because "broader language encompasses" the constraint — the constraint's enforcement behavior must be explicitly present as an acceptance criterion.
- For Unverifiable criterion (category 8): verify the criterion is truly unverifiable, not merely imprecise. "Within 30 seconds" is verifiable. "Successfully" is verifiable if the success condition is defined elsewhere in the story. "Feels confident" is unverifiable. Do not confuse category 8 with category 3 — if the criterion exists but is theater, confirm as category 8.

FINDINGS TO ASSESS:
<paste all findings from Phase 1>
```

Read the user stories, PRD, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 3: Skeptic Agent

Take only the **Confirmed** findings from Phase 2 and spawn a third sub-agent (using the Agent tool, **foreground**, `model: "sonnet"`) whose job is to argue against each one.

If Phase 2 produced zero confirmed findings, skip this phase entirely.

**Prompt structure:**

```
You are a skeptic reviewer. Your job is to argue AGAINST each confirmed finding below. You are the defense attorney for the user stories — try to prove that each finding is wrong, unnecessary, or overstated.

USER STORIES FILE: <path>
PRD FILE: <path>
CONTEXT FILE (domain glossary): <path or "not found">
ADR FILES (read on demand if needed for architectural context):
<list each ADR filename and path, or "none found">

For EACH confirmed finding, read the actual story text and PRD text yourself (do not trust the quoted excerpts — verify them). Then classify as:

- **Upheld**: You tried to argue against it but could not. The finding is genuinely correct. One sentence on why your best counterargument fails.
- **Downgraded to false positive**: The finding is wrong despite two prior agents agreeing. Explain specifically what they both missed — e.g., "The quoted PRD text is from a non-normative example, not a requirement", "The acceptance criterion at line N already covers this implicitly", "The story uses different wording but describes the same behavior."
- **Downgraded to clarification**: The finding was marked confirmed but the PRD is actually ambiguous on this point. The prior agents assumed a PRD interpretation that isn't the only valid one. Frame the ambiguity.

SKEPTIC RULES:
- VERIFY every quote. If the finding misquotes the story or PRD (even slightly), downgrade it.
- Check whether the "missing" behavior is covered by a different story than the one cited.
- Check whether an acceptance criterion uses broader language that encompasses the specific behavior the finding says is missing.
- If the suggested fix would add redundant information already implied by existing criteria, downgrade it.
- If the finding's severity seems inflated (labeled Major but an engineer would likely get it right anyway from context), downgrade to clarification or false positive.
- Be aggressive but honest — if the finding is genuinely correct, uphold it. Do not downgrade valid findings just to reduce the count.

SKEPTIC RULES FOR NEW CATEGORIES:
- For Invariant violation (category 6): try to argue that the story's criteria, when read charitably, do not actually permit the violating state. If the criteria are silent on the invariant (neither permitting nor preventing violation), downgrade — silence is a gap (category 7), not an active violation (category 6).
- For Missing correctness story (category 7): try to find an existing story whose acceptance criteria explicitly address the constraint's enforcement behavior. "Broader language" is NOT sufficient — the constraint's rejection/enforcement must be an explicit criterion, not an implication. If you cannot find an explicit criterion, uphold the finding.
- For Unverifiable criterion (category 8): try to argue that the criterion IS verifiable — perhaps the observable condition is implied by context elsewhere in the story. If you can name a specific, concrete assertion a test could make based on the criterion, downgrade it. If not, uphold it.

CONFIRMED FINDINGS TO CHALLENGE:
<paste only confirmed findings from Phase 2, including the validation agent's confirmation reasoning>
```

Read the user stories, PRD, and CONTEXT.md (if found) yourself and include their full contents in the sub-agent prompt. Do NOT include ADR contents — only pass the file list so the agent can read them on demand.

## Phase 4: Apply Fixes

After the skeptic pass completes (or after Phase 2 if skeptic was skipped), work through the results:

### Auto-apply fixes

For each **Upheld** finding (or **Confirmed** if skeptic was skipped), apply the fix directly to the user stories file using the Edit tool. These are factual corrections — the PRD is clear and the story is wrong or incomplete.

Types of fixes to apply:
- Adding missing acceptance criteria (append to the relevant story's criteria list)
- Correcting factual errors in existing criteria
- Adding missing stories (append to the appropriate section, following the existing numbering scheme)
- Restructuring stories with scope issues

After applying fixes, tell the user what was changed in a brief summary list for this iteration.

### Surface ambiguous items

Collect **Needs clarification** findings from Phase 2 and **Downgraded to clarification** findings from Phase 3. Present them to the user using the AskUserQuestion tool. Group related questions if possible.

For each ambiguous item, frame it as a product decision with concrete options derived from the finding. Use this pattern:

- Frame the question around what the PRD and stories leave open
- Provide 2-3 concrete options (not "keep as is" vs "change it")
- Flag one as recommended if the PRD leans in a direction

After the user answers, apply their decisions to the user stories file.

### Discard false positives

For **False positive** findings (from Phase 2) and **Downgraded to false positive** findings (from Phase 3), do nothing. Do not mention them to the user unless asked.

### Decide whether to loop

After applying all fixes and clarifications for this iteration:

- If any confirmed fixes were applied AND iteration count < 3, continue to the next iteration (go back to Phase 1).
- Otherwise, exit the loop.

## Output

After the loop exits, print a final summary across all iterations:

```
## Stories Review Complete

**Iterations**: N
**Confirmed fixes applied**: N (across all iterations)
- <one-line summary of each fix, grouped by iteration>

**Clarifications resolved**: N (if any were surfaced)

**Skeptic rejections**: N (findings downgraded by the skeptic agent)
**False positives discarded**: N (total across validation + skeptic)

File updated: <path>
```

Do not commit. The user handles commits.
