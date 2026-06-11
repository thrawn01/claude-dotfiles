---
name: review-tests
description: Review whether a feature's existing tests actually cover the acceptance criteria, scenarios, and correctness constraints documented in its Blueprint (blueprint.md) — then fill the gaps with surface tests, and finally sweep the implementation's code coverage to a soft 80% floor by surfacing still-uncovered code as candidate behaviors. Spawns gap-finding sub-agents plus a validator and a skeptic to eliminate false positives, then (when nothing is left for the user to decide) an implementer that writes the missing tests following the surface-testing skill. Use when the user says "review the tests", "check test coverage for this feature", "find test gaps", "review-tests", or wants to audit a feature's tests against its blueprint. Do NOT use to write tests from scratch for an unbuilt feature, or to validate a list of already-identified bugs (use review-validate for that).
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, Agent, AskUserQuestion
---

# Review Tests

Given a built feature, prove its existing tests cover the acceptance criteria, scenarios, and correctness constraints documented in its Blueprint (`blueprint.md`) — then fill the gaps with surface tests.

The pipeline is a single thorough pass: extract the testable expectations from the Blueprint, find coverage gaps with parallel sub-agents, validate and skeptically challenge those gaps to kill false positives, prove-or-refute any "this code is unreachable" claim by actually writing a test that reaches it, surface anything that needs a product decision — including disagreements between the Blueprint's own sections (its product half, technical half, and User Stories section), the ADRs, and the code's actual behavior — and, when nothing is left for the user to decide, have an implementer write the missing tests following the `surface-testing` skill. Then a final **Coverage Sweep** (Phase 6.5) measures the implementation's line coverage and lifts it toward a soft 80% floor: still-uncovered code becomes candidate behaviors that run through the very same validate→skeptic→probe→implement discipline, so the number is raised only by real surface tests — never by assertion-free padding — and any genuine shortfall (unreachable-through-surface code) is reported with evidence rather than gated on. It persists a machine-parseable HTML coverage report so the next run knows what was found before.

**Two principles run through the whole pipeline:**
1. **A claim that code is unreachable / untestable / dead is an empirical claim, not an argument.** It is the highest-scrutiny verdict in this skill. You never assign it by reasoning from the source; you assign it only after *attempting to write a test that reaches the code and failing*, with the specific unbypassable blocker named. Proving a gap exists already requires a failing test — proving the *absence* of a reachable behavior must be just as rigorous, or the pipeline will quietly bias toward false "untestable" verdicts.
2. **When sources disagree, report — do not adjudicate.** The Blueprint's sections (product half, technical half, User Stories), the ADRs, and the code's actual behavior will sometimes contradict each other. The skill surfaces every such disagreement to the user for evaluation; it never silently picks one source as authoritative and records a verdict on that basis.

This skill requires a filesystem, the source code, and the ability to run the test suite. It is Claude Code only.

## How this differs from neighboring skills

- **`blueprint-review`** reviews the Blueprint against itself — checking the document for gaps, inconsistencies, and unresolved questions. `review-tests` reviews *code* (the tests) against the Blueprint.
- **`review-validate`** validates a list of *already-identified bugs*, proves each with a failing test, then fixes. `review-tests` starts from the *Blueprint*, finds *untested* behavior, and writes tests to cover it. When `review-tests` discovers that the implementation doesn't actually satisfy a documented criterion, it flags that as a behavior gap — it does not fix the implementation. Handing the flagged behavior gaps to `review-validate` is a reasonable follow-up.
- **`surface-testing`** is the *philosophy* this skill enforces. The implementer phase follows it exactly. Read it; this skill assumes its rules.

## Inputs

If `$ARGUMENTS` is provided, treat it as a path to the feature directory (or to a doc inside it). Otherwise, search for feature directories under `docs/features/` in the current working directory. If more than one feature is found and none was specified, ask the user which feature to review.

Before starting, locate and read these files:
- **`blueprint.md`** — the single Blueprint in the feature directory. Required. It is the source of the acceptance criteria, scenarios, and correctness constraints to be covered. Read the whole document: its **product half** (problem, users, Correctness Constraints — state invariants and behavioral constraints, acceptance criteria, scope/non-goals), its **technical half** (interfaces, data model, failure modes, boundaries), and its optional **User Stories** section. If the feature directory still carries the older split documents (`prd.md`, `tech-spec.md`, `user-stories.md`) instead of a Blueprint, fall back to reading whichever of those exist — at least one is required.
- **`CONTEXT.md`** — the domain glossary at the service docs root (walk up from the feature directory to find `docs/CONTEXT.md`). Optional; use it to map Blueprint terminology onto code and test names. Skip if not found.
- **`review-tests.html`** — the report this skill wrote on prior runs, if present in the feature directory. Parse its embedded JSON (`<script type="application/json" id="review-tests-data">`) to recover the `runs` log and the current criteria list with each criterion's status history. Use it to (a) avoid re-flagging gaps the user already declined, (b) detect regressions where a previously-covered criterion lost its test, (c) carry forward open behavior gaps, (d) preserve the prior run history so this run appends to it rather than overwriting it, and (e) **re-examine, do not trust, any prior `untestable` / `behavior-gap` / `doc-disagreement` verdict whose `evidenceGrade` is not `test-verified`.** A reasoning-only "untestable" verdict that calcifies in the report will suppress re-investigation forever; the highest-stakes verdicts must decay toward re-scrutiny. Only verdicts backed by a test that was written and run are carried forward without re-probing.

Additionally, list files in the `adr/` directory at the service docs root. Do NOT read them upfront — pass the filenames/paths to sub-agents so they can read a specific ADR on demand when a finding needs architectural context (e.g., to confirm whether an untested path is intentionally out of scope).

Derive the `{feature}` slug from the feature directory name under `docs/features/`.

If no Blueprint (or fallback spec document) can be found, ask the user for the feature path. Do not attempt to review tests without a Blueprint to review them against — without documented criteria there is nothing to measure coverage of.

## Phase 0: Scope & Coverage Baseline

**Scope is implementation-package scoped.** Determine which packages/files implement this feature; their tests are the review scope.

1. **Locate the implementation.** Start from explicit file/package references in the Blueprint's technical half. Confirm and expand the set with a targeted search of the codebase (Grep/Glob, or a `codebase-locator` sub-agent for anything ambiguous). Produce a concrete list of implementation packages/directories and the test files in or adjacent to them.
2. **Identify the surface.** For the located code, identify the public entry points (HTTP/gRPC endpoints, CLI `Run()`, exported functions, internal library boundaries) per the `surface-testing` skill. The gap analysis is anchored to these — coverage means a test enters through the surface and asserts the behavior.
3. **Run the coverage tool once** over the implementation packages and capture the result. Detect the project type and use the idiomatic command:
   - Go: `go test ./<pkg>/... -coverprofile=/tmp/review-tests.cover -covermode=atomic` then `go tool cover -func=/tmp/review-tests.cover` (and per-line uncovered regions where useful).
   - Kotlin/JVM: the project's configured coverage (e.g. Kover/JaCoCo) if available.
   - Other: the standard coverage command for the toolchain.
   **Retain two things for the Coverage Sweep (Phase 6.5): the total coverage percentage for the scope, and the per-region uncovered list (file, line range, enclosing function).** Keep the raw profile on disk (e.g. `/tmp/review-tests.cover`) — Phase 6.5 re-reads it after the criteria tests are added.
   If no coverage tooling is configured or it fails to run, note that in the report and proceed with behavioral mapping alone — but in that case run the scope's existing test suite once anyway so its tests actually execute. A `covered` verdict may be graded `test-verified` only if the suite ran this run (the coverage run counts); if neither the coverage run nor a plain test run executed, grade `covered` as `reasoning-only` — reading a test is not the same as seeing it pass. With no coverage tooling, the Phase 6.5 sweep is skipped and the report records `coverageToolRan: false`.
4. **State the scope to the user** before spawning agents: which feature, which docs were found, which implementation packages are in scope, the baseline coverage percentage (if tooling ran), and whether coverage tooling ran. Keep it to a few lines.

**Coverage tooling is a corroborating signal and a discovery source — never a pass/fail gate.** A covered line is not the same as a covered *criterion* (a line can execute incidentally without any assertion proving the behavior), and a criterion can be legitimately covered by a test that lives in another package. Behavioral mapping decides coverage; the coverage profile points agents at suspicious untested code and guards against "I assumed a test exists." The **80% floor** introduced in Phase 6.5 is a *soft* target: still-uncovered code becomes candidate behaviors to investigate through the same surface-test discipline, and the report explains any shortfall rather than failing. The skill never brute-forces a number by writing assertion-free tests, and never tests internals to lift coverage.

## Phase 1: Criteria Extraction

Build a single normalized, numbered checklist of every testable expectation in the Blueprint. Do this yourself (orchestrator) by reading the Blueprint, or delegate to one extraction sub-agent if it is large. Each checklist item has:

- **id** — stable identifier prefixed by `kind`: `AC-` for functional, `INV-` for invariant, `CON-` for constraint, `BND-` for boundary (e.g. `AC-1`, `INV-2`). A fifth prefix, `COV-`, is reserved for coverage-derived candidates, but those are **not** extracted here — they are generated in Phase 6.5 from the uncovered-region list *after* the Blueprint criteria are implemented, so coverage measures what is still dark. Carry forward ids from a prior `review-tests.html` when the criterion is unchanged, so history lines up.
- **source** — which Blueprint section (or story) it came from (quote the relevant text).
- **text** — the expected behavior, stated as an observable condition.
- **surface** — the public entry point a test would use to exercise it (endpoint, CLI command, exported function), or `unknown` if not yet determinable.
- **kind** — one of:
  - `functional` — an acceptance criterion / scenario describing user-visible behavior.
  - `invariant` — a state invariant from the Blueprint's Correctness Constraints section (e.g. "balance is never negative").
  - `constraint` — a behavioral constraint (e.g. "messages are never silently dropped").
  - `boundary` — a component boundary precondition/postcondition.
  - `coverage` — a candidate behavior derived from an uncovered code region (assigned in Phase 6.5, not here).

Extract correctness-derived items (`invariant`, `constraint`, `boundary`) only when the Blueprint has an explicit Correctness Constraints section — these map onto the **Correctness-Derived Tests** section of the `surface-testing` skill (invariant-violation tests, behavioral-constraint tests, boundary-contract tests). The Blueprint's state invariants map to `invariant` items and its behavioral constraints to `constraint` items. Do not invent correctness constraints the Blueprint does not state.

## Phase 2: Gap-Finding (Parallel Sub-Agents)

Partition the checklist into balanced batches and spawn a few sub-agents in parallel (Agent tool, **foreground**, `model: "sonnet"`). Partition by surface area or by source document so each agent owns a coherent slice — aim for a small number of agents (≈2–4), not one per criterion. Give every agent the full list of implementation-package test files and the relevant coverage output so it can search broadly.

**Sub-agent capabilities.** Every sub-agent in this skill needs at least Read/Grep/Glob to search code and tests. The Phase 4.5 prover and the Phase 6 implementer additionally need **Write and the ability to run the project's test suite** (Bash) — they write tests and execute them. Use the default general-purpose agent (full tool access) unless your environment restricts it; if you pin a `subagent_type`, confirm it grants those tools, or the prove-it and implement phases will silently no-op.

**Sub-agent prompt structure:**

```
You are auditing whether a set of documented acceptance criteria are covered by a feature's existing tests. You determine coverage by reading the actual test code — never assume a test exists.

IMPLEMENTATION PACKAGES (review scope):
<list of packages/dirs and their test files>

SURFACE (public entry points for this feature):
<endpoints / CLI commands / exported functions identified in Phase 0>

COVERAGE TOOL OUTPUT (corroborating signal — not authoritative):
<func-level and notable uncovered regions for the implementation packages, or "coverage tooling unavailable">

CONTEXT (domain glossary): <path or "not found">
ADR FILES (read on demand if a criterion's coverage hinges on an architectural decision):
<list each ADR filename and path, or "none found">

CRITERIA TO ASSESS (your batch):
<the batch of checklist items: id, source, text, surface, kind>

For EACH criterion:
1. Search the test files for any test that exercises this behavior THROUGH THE SURFACE and asserts it.
2. Read that test's body — confirm it actually enters through the public entry point and makes a real assertion about this behavior. A test that calls internal functions directly, or that exercises the path without asserting the behavior, does NOT count as coverage (note it as a surface-testing violation).
3. Classify the criterion:
   - COVERED: a real surface test asserts this behavior. Cite the test as <file>:<TestName>.
   - PARTIAL: a test touches the behavior but misses a case the criterion requires (e.g. happy path covered, the rejection/error case is not), OR the test asserts the behavior but reaches in through internals rather than the surface. Describe precisely what is missing.
   - GAP: no test asserts this behavior. Confirm by searching the whole scope, not just the obvious file.
4. For PARTIAL and GAP, propose how to cover it through the surface: the entry point, the input, and the observable assertion. If the behavior cannot be observed through any public interface, say so and explain why (this becomes an observability/testability question).

Use this output format per criterion:

### <id>: <short title>
**Status**: COVERED | PARTIAL | GAP
**Criterion**: <text>  (source: <doc#section>)
**Surface**: <entry point>
**Existing tests**: <file:TestName, ...> or "none found"
**What's missing** (PARTIAL/GAP): <precise description>
**How to cover** (PARTIAL/GAP): <entry point + input + observable assertion>
**Observability concern** (if any): <why the behavior may not be observable through the surface>

RULES:
- Coverage means a SURFACE test with a real assertion. Be strict about the surface (see the surface-testing skill).
- Search exhaustively before declaring a GAP — the covering test may live in a sibling or parent package.
- Do not propose tests that reach into internals. If the only way to observe a behavior is through internals, that is an observability concern to flag, not a test to write.
- Do not invent criteria beyond the batch you were given.
```

Read the test files and coverage output yourself and include their relevant contents in each sub-agent prompt. Pass only the ADR file list (not contents).

Collect all findings. COVERED criteria are recorded for the report; PARTIAL and GAP findings flow to validation.

## Phase 3: Validator

Spawn one sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to sort every PARTIAL/GAP finding into the buckets that determine what happens next. This is the critic the user asked for.

**Sub-agent prompt structure:**

```
You are validating reported test-coverage gaps. For each finding, read the cited tests and source yourself — do not trust the excerpts. Classify each into exactly one bucket.

IMPLEMENTATION PACKAGES: <list>
SURFACE: <entry points>
CONTEXT (glossary): <path or "not found">
ADR FILES (read on demand): <list or "none found">

FINDINGS TO ASSESS:
<all PARTIAL/GAP findings from Phase 2, with their proposed coverage>

For EACH finding, classify as ONE of:

- ALREADY-COVERED (false positive): an existing test already asserts this behavior through the surface. Cite the exact test <file>:<TestName> and the assertion. The gap-finder missed it.

- GENUINE-GAP (test-only): the behavior IS implemented and IS observable through the surface, but no test asserts it. Covering it needs only a new test — no production code change. Confirm the entry point and the observable assertion exist today.

- NEEDS-TESTABILITY-CHANGE: the behavior is correct but is NOT observable through the public surface as the code stands. Covering it requires a SAFE, ADDITIVE production change that does not alter observable behavior — e.g. exposing a Stats()/observability API, making main() delegate to a testable Run(), or exporting a symbol a consumer would legitimately need. Describe the minimal change and the test it unlocks. (See the surface-testing skill's "Expose Observability APIs" and "Structuring Code for Testability" sections.)

- BEHAVIOR-GAP-SUSPECTED: the criterion is CLEAR and the implementation appears NOT to satisfy it. This is an empirical claim, not a question — do NOT surface it for a decision. It goes to the implementation queue, where a test asserting the criterion is written and run: if the test fails, the gap is PROVEN (left red, reported loud); if it passes, the suspicion was wrong and the criterion is simply now covered. Describe the asserting test (entry point + input + the assertion the criterion demands) so the implementer can write it.

- NEEDS-BEHAVIOR-DECISION: the criterion is ambiguous or contradicts the code and the right behavior is a genuine product call — you cannot write a deterministic assertion from the criterion alone (if you can, it is BEHAVIOR-GAP-SUSPECTED, not this). State the issue precisely and frame the decision.

- DOC-DISAGREEMENT: two or more sources disagree about the expected behavior — one Blueprint section vs another (product half vs technical half vs User Stories) vs an ADR vs the **code's actual observed behavior**. This is not a coverage gap; it is a contradiction the user must resolve. Quote each side verbatim with its source. Do NOT pick a winner and do NOT record a coverage verdict on one source's authority — the Blueprint is the statement of *intended* behavior to test against, never evidence of *what the code does*. (Example from a real run: the Blueprint's product half said string enums become proto string fields, an ADR said they become proto enums, and the code did a third thing — the correct action was to surface all three, not to grade coverage against the Blueprint.)

- UNTESTABLE-NEEDS-DESIGN: the behavior cannot be observed through any public interface and no safe additive observability change exposes it without a larger redesign. **This is the highest-scrutiny verdict and you may NOT assign it on reasoning alone.** A claim that code is unreachable is empirical. To propose this bucket you must (1) have ATTEMPTED to construct an input — spec, fixture, lock, request, config — that drives the code through the surface and failed, (2) name the exact blocker that stopped every attempt, and (3) confirm that blocker cannot be bypassed — explicitly check for disabling flags, config, or per-schema / per-rule ignore or extension mechanisms that could suppress the check you believe is blocking (these are the usual reason a "can't happen" path actually can). If you have not genuinely tried to reach it, classify it GENUINE-GAP instead and let Phase 4.5 try. "I can't see how to reach it" is not evidence; "I tried inputs A, B, C — each blocked by X — and X is not suppressible because Z" is. Every UNTESTABLE proposal is re-tested in Phase 4.5 before it can reach the user.

Output per finding:

### <id>: <short title>
**Bucket**: ALREADY-COVERED | GENUINE-GAP | NEEDS-TESTABILITY-CHANGE | BEHAVIOR-GAP-SUSPECTED | NEEDS-BEHAVIOR-DECISION | DOC-DISAGREEMENT | UNTESTABLE-NEEDS-DESIGN
**Reasoning**: <one or two sentences, citing the test/source you read>
**Covering test or change**: <for GENUINE-GAP / NEEDS-TESTABILITY-CHANGE / BEHAVIOR-GAP-SUSPECTED: the concrete asserting test and any minimal additive change>
**Reach attempt** (UNTESTABLE-NEEDS-DESIGN only): <the input(s) you actually tried, the blocker that stopped each, and why it can't be bypassed — required, or reclassify as GENUINE-GAP>
**Sources in conflict** (DOC-DISAGREEMENT only): <each source quoted verbatim with its location, including the code's observed behavior>
**Decision to surface** (NEEDS-BEHAVIOR-DECISION / DOC-DISAGREEMENT / UNTESTABLE-NEEDS-DESIGN): <the question for the user>

RULES:
- Default to skepticism on GAP claims: search for an existing covering test before confirming a gap.
- The line between NEEDS-TESTABILITY-CHANGE and NEEDS-BEHAVIOR-DECISION is whether the change alters observable behavior. Exposing a read-only Stats() is testability. Changing a status code, validation, or output is a behavior decision.
- If a finding asserts the implementation doesn't meet the criterion, do NOT assume it and do NOT turn it into a question — when the criterion is clear, classify it BEHAVIOR-GAP-SUSPECTED so the implementer proves it with a test (fail = proven gap, pass = covered). Reserve NEEDS-BEHAVIOR-DECISION for criteria that are genuinely ambiguous or contradict the code.
- Read the relevant ADR before deciding whether an untested path is intentionally out of scope.
- Never resolve a contradiction between Blueprint sections (or between the Blueprint and the code) yourself — that is a DOC-DISAGREEMENT for the user. The Blueprint claiming a behavior is "untestable" or "out of scope" is itself a claim to verify, not authority to record.
- Output one bucket per finding from this exact set: ALREADY-COVERED | GENUINE-GAP | NEEDS-TESTABILITY-CHANGE | BEHAVIOR-GAP-SUSPECTED | NEEDS-BEHAVIOR-DECISION | DOC-DISAGREEMENT | UNTESTABLE-NEEDS-DESIGN.
```

## Phase 4: Skeptic

Take only the **GENUINE-GAP** and **NEEDS-TESTABILITY-CHANGE** findings and spawn a third sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to argue against them — the defense attorney for the existing test suite. Skip this phase if there are none.

**Sub-agent prompt structure:**

```
You are a skeptic. Your job is to prove each confirmed gap below is wrong — that a test already covers it, or that the proposed test would be redundant or would reach into internals.

IMPLEMENTATION PACKAGES: <list>
SURFACE: <entry points>
ADR FILES (read on demand): <list or "none found">

For EACH finding, read the actual test files yourself (do not trust the quoted tests). Classify as:

- UPHELD: you tried to find covering test and could not. The gap is real. One sentence on why your best counterargument fails.
- DOWNGRADED-TO-COVERED: an existing test (possibly in another package, possibly under a non-obvious name) already asserts this through the surface. Cite <file>:<TestName> and the assertion both prior agents missed.
- DOWNGRADED-TO-DECISION: the "test-only" gap actually requires a behavior or design decision the prior agents glossed over (e.g. the proposed assertion presumes behavior the code doesn't have). Frame the decision. If your downgrade rests on the path being unreachable / unobservable through the surface, say so explicitly — that claim is empirical and will be sent to the Phase 4.5 Reachability Probe to prove-or-refute, not taken on your reasoning.

CONFIRMED GAPS TO CHALLENGE:
<the GENUINE-GAP and NEEDS-TESTABILITY-CHANGE findings, with the validator's reasoning>

RULES:
- Verify every cited test. If a prior agent miscited a test, that is a strong signal to re-examine.
- A test that exercises the path without asserting the behavior is NOT coverage — do not downgrade based on incidental execution.
- A proposed test that would only pass by reaching into internals should be downgraded to a decision (it needs an observability change, not a surface test).
- Be aggressive but honest. Uphold genuinely real gaps; do not downgrade just to reduce the count.
```

## Phase 4.5: Reachability Probe (prove-it-with-a-test)

Every finding heading for an unreachability-based verdict — **UNTESTABLE-NEEDS-DESIGN**, any **NEEDS-BEHAVIOR-DECISION** / **DOC-DISAGREEMENT** that rests on "this code/path can't be reached," or any skeptic **DOWNGRADED-TO-DECISION** that rests on unreachability/unobservability — gets one independent pass whose only job is to *reach it by writing a test*. Skip this phase only if there are no such findings.

Why this phase exists, and why it is separate from the skeptic: a **passing test that reaches code is definitive proof of reachability; failing to write one is only suggestive** — it can mean "truly unreachable" or just "nobody was creative enough yet." The validator and skeptic both reason from the source in-context and can share the same blind spot (in a real run, both wrongly concluded a path was unreachable; the truth only emerged when a fresh agent was tasked specifically with reaching it and discovered a per-schema ignore extension that opened the path). This phase spawns a fresh agent **motivated to break the unreachability claim**, the way an independent reproducer catches what the original author missed.

Spawn one sub-agent (Agent tool, **foreground**, `model: "sonnet"`). It does not argue — it writes a surface test and runs it. **It must not build or run a separate binary; the proof is a test executed by the project's normal test runner through the public surface.**

**Sub-agent prompt structure:**

```
You are a reachability prover. For each item below, a prior agent claimed the code is unreachable / untestable / out of scope through the public surface. Prove them WRONG by writing a real surface test that reaches it — or confirm them right ONLY after genuinely trying and failing.

IMPLEMENTATION PACKAGES: <list>
SURFACE (public entry points): <list>
TEST CONVENTIONS: <the project's test file(s), helpers, and CLAUDE.md testing rules — surface only>
SUPPRESSION MECHANISMS TO HUNT FOR: search the codebase for any flag, config option, or per-schema / per-rule ignore or extension hook that can disable a validation the "unreachable" claim depends on. These are the usual reason a "can't happen" path actually can happen — find them before concluding anything.

ITEMS TO PROBE (each with the claimed blocker):
<the UNTESTABLE / reachability-based findings and the blocker the prior agent named>

For EACH item:
1. Actually try to construct an input (spec, fixture, lock, request, config) that drives the suspect code through the public surface. Try several DISTINCT angles, including every suppression mechanism you found.
2. Write a surface test for it and RUN it (the project's normal test runner — do NOT build or invoke a separate binary).
   - A test reaches the code (passes, or fails as a genuine behavior gap) → REACHABLE; the unreachability claim is REFUTED. Return the working test.
   - You cannot reach it after genuine attempts → UNREACHABLE-CONFIRMED. Enumerate every input you tried, the exact blocker that stopped each, the suppression mechanisms you checked, and why none bypass it.

Output per item:
### <id>
**Verdict**: REACHABLE (refutes prior claim) | UNREACHABLE-CONFIRMED
**Evidence**: <the passing/failing test you wrote and ran — paste it — OR the enumerated failed attempts + the unbypassable blocker>

RULES:
- "Confirmed unreachable" requires that you WROTE AND RAN at least one real reaching attempt. Source-reading alone is NOT acceptable evidence.
- Prefer writing the test over arguing. The test is the proof.
- The test must enter through the public surface, never internals. If the ONLY way to reach the code is via internals, the UNTESTABLE verdict stands — note that internals-only access is the reason.
- **Clean up after yourself.** Reach attempts are scratch work, not deliverables. For REACHABLE, keep ONLY the single working test (paste it as evidence and leave it in place for Phase 6 to adopt); delete every other attempt. For UNREACHABLE-CONFIRMED, delete every attempt you wrote — the evidence is your enumerated list of inputs and blockers, not leftover code. Before returning, **run the scope's test suite once more and confirm it still compiles and passes as it did before you started** — a single leftover non-compiling test file breaks the entire package's tests for everyone downstream. Report the suite as clean in your output.
```

Feed the outcomes into Phase 5:
- **REACHABLE** → the item becomes a **GENUINE-GAP**; the reaching test the prover wrote goes into the implementation queue (if that test fails, it is a behavior gap). The prior "untestable/decision" verdict is discarded as refuted.
- **UNREACHABLE-CONFIRMED** → the verdict stands, now backed by execution evidence. Mark it `evidenceGrade: test-verified` in the report.

A reachability-based verdict that was **never probed** in this phase may not reach the user — send it back through Phase 4.5 first.

## Phase 5: Triage & Gating

Assemble the final disposition from the surviving classifications:

**Implementation queue (auto-implementable):**
- **UPHELD GENUINE-GAP** → write a surface test (no production change).
- **UPHELD NEEDS-TESTABILITY-CHANGE** → apply the minimal additive testability change, then write the surface test.
- **BEHAVIOR-GAP-SUSPECTED** → write the test that asserts the documented criterion and run it. This is NOT gated: a passing test means the criterion is covered (`test-added`); a failing test is a *proven* behavior gap — left red and reported loud, exactly like a behavior gap discovered while implementing a genuine gap (Phase 6 step 3). Proving it with a test is always better than asking the user about an unproven suspicion.

**Question queue (requires a user decision — gate):**
- **NEEDS-BEHAVIOR-DECISION** — the criterion is genuinely ambiguous or contradicts the code and the right behavior is a product call (a suspicion that the implementation simply doesn't meet a *clear* criterion is BEHAVIOR-GAP-SUSPECTED above — proven, not asked).
- **DOC-DISAGREEMENT** — two or more sources (Blueprint product half / technical half / User Stories / ADR / observed code behavior) contradict each other. Present every side; the user decides which is authoritative. Never resolve it yourself.
- **UNTESTABLE-NEEDS-DESIGN** — would need a redesign to observe. **Only admissible here if Phase 4.5 confirmed it UNREACHABLE with execution evidence.** An untestable verdict that was never probed is sent back to Phase 4.5, not to the user.
- **DOWNGRADED-TO-DECISION** from the skeptic.

Findings the Reachability Probe marked **REACHABLE** do NOT enter the question queue — they move to the implementation queue as genuine gaps (the prover's test is reused).

**Recorded only (no action):** ALREADY-COVERED and DOWNGRADED-TO-COVERED (cite the covering test in the report; do not mention to the user unless asked). COVERED criteria from Phase 2.

**Gating rule (auto-implement, gated):**
- If the question queue is **empty**, proceed directly to Phase 6 and implement the whole queue automatically.
- If the question queue is **non-empty**, surface those decisions with `AskUserQuestion` BEFORE implementing the items they concern. Frame each as a product decision with 2–3 concrete options derived from the finding (e.g. "Write a pending test documenting the expected behavior", "Adjust the criterion to match current behavior", "Out of scope — record and skip"). Flag a recommended option when the spec leans one way. For a **DOC-DISAGREEMENT**, present each conflicting source as its own option ("treat the Blueprint as authoritative", "treat the ADR as authoritative", "the code's current behavior is correct — update the Blueprint") and quote the conflicting text so the user can decide without re-reading the whole Blueprint; do not pre-pick a side.
  - The independent items in the implementation queue (genuine gaps, testability changes) are NOT blocked by open questions — they are implemented in Phase 6 regardless.
  - After the user answers, fold any "write the test" / "expose observability" decisions into the implementation queue. Decisions to change behavior are NOT executed by this skill — record them as flagged behavior gaps for follow-up (e.g. via `review-validate`).
  - **Map each answer to a report `status`** so the next run carries it correctly: "write the test / expose observability" → the resulting `test-added` / `testability-change` / `behavior-gap` once Phase 6 runs it; "adjust the criterion / current behavior is correct — update the Blueprint" → `behavior-gap` if still unmet, else `covered`; "out of scope — record and skip" → `declined`. A question raised but left unanswered this run stays `open-question`. A `doc-disagreement` the user resolved by naming an authoritative source is recorded against that source's expected behavior; if left unresolved it stays `doc-disagreement`.

Do not change production behavior on your own initiative at any point. Safe additive testability changes are the only production edits this skill makes without asking.

## Phase 6: Implementer (Gated Auto-Implement)

Spawn one sub-agent (Agent tool, **foreground**, `model: "sonnet"`) to implement the resolved queue, or do it directly. Implement strictly following the `surface-testing` skill and the project's CLAUDE.md testing patterns.

For each queue item:

1. **Apply any testability change first** (NEEDS-TESTABILITY-CHANGE items): make the minimal additive change — expose a `Stats()`/observability API, split `main()` into a testable `Run()`, export the needed symbol. Never alter observable behavior.
2. **Write the surface test** for the criterion: enter through the public entry point, substitute only external dependencies with real fakes, assert the observable behavior. For correctness-derived items, follow the matching pattern from the surface-testing skill (invariant-violation, behavioral-constraint, or boundary-contract test).
3. **Run the new test.**
   - **Passes** → the behavior was implemented but untested. Coverage added. Record as `test-added`.
   - **Fails** → the implementation does NOT satisfy the documented criterion. This is a discovered **behavior gap** (for a BEHAVIOR-GAP-SUSPECTED item this failing test is exactly the proof that was queued — it is the expected outcome, not a surprise). **Leave the test red.** Do NOT fix the implementation and do NOT change the test to pass. Record the failing test, its failure output, and the criterion it proves unmet. (This is the user-chosen behavior: failing gap tests stay red so the gap is loud.)
4. **Run the full test suite for the scope** after each addition (or as a batch at the end) to detect regressions:
   - If a **pre-existing** test now fails because of a testability change, the change was not actually behavior-preserving — revert it, and reclassify the item as NEEDS-BEHAVIOR-DECISION. Per CLAUDE.md, prefer fixing the change over altering the test.
   - Newly-written gap tests that are intentionally red (step 3) are expected and are not regressions.

For items the Reachability Probe (Phase 4.5) already proved REACHABLE, **reuse the test it wrote** rather than re-deriving one — fold it into the project's conventions and run it. Every test added or confirmed here is recorded with `evidenceGrade: test-verified`.

Follow CLAUDE.md exactly: tests in `package xxx_test`, table-driven where appropriate, `require`/`assert` from testify, no descriptive messages on assertions, surface-only access.

## Phase 6.5: Coverage Sweep (Soft 80% Floor)

The Blueprint pass measures coverage against *documented* behavior. This phase measures it against the *code that actually exists* — the bottom-up complement — and lifts the scope toward a **soft 80% line-coverage floor** by turning still-uncovered code into candidate behaviors that flow through the same discipline. Skip this phase entirely if coverage tooling did not run in Phase 0 (record `coverageToolRan: false` and note the sweep was skipped).

This phase runs **after** Phase 6 so coverage reflects the criteria tests just added — it sweeps what is *still* dark, not what the Blueprint pass was already about to cover.

1. **Re-measure.** Re-run the Phase 0 coverage command over the scope now that the new tests exist. Record the post-criteria percentage. If it is already ≥ 80%, record the floor as met and skip to the report — do not manufacture tests to pad a number that is already adequate.
2. **Emit `COV-` candidates.** For each still-uncovered region (file, line range, enclosing function), create a candidate criterion: `id` = `COV-<n>`, `kind` = `coverage`, `source` = `coverage:<file>:<lines>`, `text` = the behavior that region implements stated as an observable condition, `surface` = the nearest public entry point that could drive it (or `unknown`). Group trivially-related regions (e.g. all branches of one validation function) into one candidate so the list stays behavior-sized, not line-sized. **Do not** emit candidates for code the project conventionally excludes from coverage (generated files, `main()` wiring already delegated to a tested `Run()`, vendored code) — note the exclusion instead.
   **Key each `COV-` id stably by `<file>#<enclosing-function>` + a short behavior slug, NOT by raw line numbers** — line ranges shift every time the code changes, so a line-keyed id would fragment one region's history into a new criterion every run. When a prior `review-tests.html` already has a `COV-` item for the same function+behavior, reuse its id so `history` lines up (the `source` line range may update; the id must not). A region that became covered since the last run is carried forward with its existing id and a `covered`/`test-added` status, not dropped.
3. **Run the candidates through the existing tail, skipping Phase 2.** A `COV-` candidate is uncovered by definition, so it does not need the COVERED/PARTIAL/GAP gap-finders — send it straight to the **Phase 3 validator** for bucketing, then the **Phase 4 skeptic**, the **Phase 4.5 reachability probe**, Phase 5 triage, and the Phase 6 implementer. The buckets carry the same meanings; the common outcomes for coverage candidates are:
   - **GENUINE-GAP** → a surface test is written (Phase 6). Coverage rises.
   - **UNTESTABLE-NEEDS-DESIGN** → the region is real but unreachable/unobservable through the surface (defensive branches, `if err != nil` on calls that cannot fail in-surface, panic guards). This is the *expected, honest* outcome for a chunk of uncovered code — recorded with the Phase 4.5 reach attempt as evidence, **not** brute-forced into a test. It counts against the floor with a stated reason.
   - **BEHAVIOR-GAP-SUSPECTED / behavior-gap** → writing the reaching test exposes that the code is wrong; left red and reported loud, same as any other behavior gap.
   - **DOC-DISAGREEMENT / NEEDS-BEHAVIOR-DECISION** → the region's intended behavior is contested or ambiguous; gated to the user like any other question. Because this phase runs after the Blueprint pass already gated once, coverage-derived questions form a **second** `AskUserQuestion` round — batch all of them into one round here rather than asking per-candidate.
4. **Evaluate the floor — as a report line, never a gate.** After the sweep, record the final coverage percentage and classify the remainder below 100%: tests-added, untestable-through-surface (with evidence), conventionally-excluded, declined, or open-question. A scope that lands below 80% **is a valid, complete outcome** when the shortfall is accounted for — e.g. "76%; the missing 4 points are 3 defensive branches Phase 4.5 confirmed unreachable + 1 region awaiting a behavior decision." Never write an assertion-free test, and never reach into internals, to move the number.

The same prohibitions apply as everywhere else in this skill: surface-only tests, safe additive testability changes only, failing gap tests left red, sources-disagree-surface-don't-adjudicate. `COV-` criteria are recorded in the report with their own kind so the coverage view is distinct from the Blueprint criteria matrix.

## Phase 7: Report

Write a self-contained `review-tests.html` to the feature directory (`docs/features/{feature}/review-tests.html`) and print a short chat summary.

The report **accumulates across runs**: it keeps the current coverage state as the primary view AND a compact history of every run, so coverage progress is visible over time without re-storing the full matrix per run. On each run, append a new entry to the `runs` log and append the new status to each criterion's `history` — never discard prior runs. Get the run's datetime stamp by running `date "+%Y-%m-%d %H:%M"` in Bash and inlining it as text.

The report is **both** human-informative and machine-parseable. It must:
- Open directly in a browser with no external CSS/JS dependencies (inline styles only).
- Embed a `<script type="application/json" id="review-tests-data">…</script>` block containing the structured findings, so a future `review-tests` run (or any tool) can recover prior state by parsing that one element. Keep the JSON authoritative — the human table is rendered from the same data.

**Embedded JSON shape:**

```json
{
  "feature": "<slug>",
  "schemaVersion": 1,
  "runs": [
    {
      "n": 1,
      "stamp": "2026-05-30 14:42",
      "reviewedDocs": ["blueprint.md"],
      "implementationPackages": ["path/to/pkg"],
      "coverageToolRan": true,
      "coverage": {
        "floor": 80,
        "baselinePct": 0,
        "finalPct": 0,
        "floorMet": false,
        "remainder": "<one line accounting for the gap below 100%: e.g. 3 unreachable-through-surface branches + 1 awaiting decision>"
      },
      "summary": {
        "total": 0, "covered": 0, "partial": 0,
        "testsAdded": 0, "testabilityChanges": 0,
        "behaviorGaps": 0, "openQuestions": 0,
        "docDisagreements": 0, "untestable": 0,
        "coverageTestsAdded": 0, "coverageUntestable": 0
      },
      "delta": "<one line: e.g. 4 tests added, 1 behavior gap found, 2 prior gaps closed, coverage 71%→83%>"
    }
  ],
  "criteria": [
    {
      "id": "AC-1",
      "kind": "functional | invariant | constraint | boundary | coverage",
      "source": "blueprint.md#user-stories/story-3   (or coverage:<file>:<lines> for a COV- item)",
      "text": "<observable behavior>",
      "surface": "POST /orders",
      "status": "covered | partial | test-added | testability-change | behavior-gap | untestable | doc-disagreement | open-question | declined",
      "evidenceGrade": "test-verified | reasoning-only | spec-asserted",
      "coveringTests": ["path/test.go:TestX"],
      "testAdded": "path/test.go:TestY",
      "testRedReason": "<failure summary, for behavior-gap>",
      "reachAttempt": "<for untestable: the inputs tried + unbypassable blocker that Phase 4.5 confirmed>",
      "sourcesInConflict": "<for doc-disagreement: each source quoted with its location, incl. observed code behavior>",
      "note": "<short explanation, e.g. the testability change applied or the decision recorded>",
      "history": [
        { "run": 1, "status": "gap" },
        { "run": 2, "status": "test-added" }
      ]
    }
  ]
}
```

The top-level `status`, `coveringTests`, `testAdded`, and `note` on each criterion reflect the **latest** run; `history` records the per-run progression; `runs` is the append-only run log (newest run appended each invocation). Carry stable `id`s across runs so history lines up.

`evidenceGrade` records how a verdict was established and drives the next run's carry-forward decision (Inputs rule (e)):
- **`test-verified`** — backed by a test that actually executed this run: a `test-added` test this skill wrote and ran, a `covered` criterion whose existing test was executed by the coverage/suite run (NOT merely read — see Phase 0), or an `untestable`/`behavior-gap` confirmed by Phase 4.5's executed reach attempt. Trusted across runs.
- **`reasoning-only`** — concluded from reading source/tests without an executed test proving it. Any `untestable`/`behavior-gap`/`doc-disagreement` at this grade is **re-examined** next run, not trusted.
- **`spec-asserted`** — recorded because the Blueprint said so (e.g. the Blueprint calling something out of scope). Lowest trust; always re-verify against the code before relying on it. Never let a `spec-asserted` claim stand in for `test-verified`.

**Human-readable HTML must include:**
- A header with the feature, the latest run's number and datetime stamp, the docs reviewed, the implementation packages in scope, and whether coverage tooling ran.
- A summary line with the counts from the latest run's `summary`.
- A **Code coverage** panel (only when `coverageToolRan`): the baseline → final percentage, the 80% floor, whether it was met (green) or not (amber — **not** red; a shortfall with an accounted remainder is a valid outcome), and the one-line `remainder` accounting for everything still below 100% (tests-added vs untestable-through-surface vs excluded vs awaiting-decision). Make explicit that the floor is a soft target, not a pass/fail gate.
- A **coverage matrix** table reflecting the CURRENT state: one row per criterion — id · kind · criterion text · status (color-coded) · covering/added test · evidence grade · note. The `coverage`-kind (`COV-`) rows are the Phase 6.5 candidates; render them in their own sub-section (or visually grouped) so the bottom-up coverage findings read separately from the Blueprint criteria. Color suggestion: covered/test-added green, partial amber, behavior-gap/untestable/doc-disagreement red, open-question/declined grey. Show the `evidenceGrade` (e.g. a small `test-verified` / `reasoning-only` / `spec-asserted` tag) so the reader can see which verdicts are execution-backed. Where a criterion's status changed since the previous run, show the transition (e.g. a small "was: gap" marker) so progress is visible at a glance.
- A **Behavior gaps** section listing each red gap test, the criterion it proves unmet, and its failure output — these are the loudest items.
- A **Spec/code disagreements** section listing each `doc-disagreement`: the criterion, every conflicting source quoted with its location (including the code's observed behavior), and the decision the user needs to make. These are contradictions, not coverage gaps — keep them visually distinct.
- A **Flagged for decision** section for open-question / untestable / declined items. For each `untestable` item, show the Phase 4.5 reach attempt (inputs tried + unbypassable blocker) so the "can't be tested" claim carries its evidence.
- A **Run history** section, newest first: a compact table of every run — run # · datetime stamp · total / covered / tests-added / behavior-gap / doc-disagreement counts · coverage baseline→final % · the one-line delta. This is the iteration log.
- Stamp the datetime as static text taken from `date "+%Y-%m-%d %H:%M"`. Do NOT call `Date.now()` or `new Date()` in any embedded script — the stamp must be fixed at write time, not recomputed when the file is opened.

**Chat summary** — print after writing the file:

```
## Review Tests Complete — {feature}

Scope: <implementation packages>  |  Docs: <docs reviewed>  |  Coverage tool: <ran / unavailable>

Criteria: N total
- Covered (existing): N
- Tests added: N   (+ N safe testability changes applied)
- Behavior gaps (failing tests left red): N
- Spec/code disagreements (need your call): N
- Flagged for your decision: N
- Untestable / needs design (test-verified unreachable): N

Coverage sweep: <baseline>% → <final>%  (floor 80%: met / below — <one-line remainder>)
- Coverage tests added: N
- Uncovered & unreachable through surface (test-verified): N

Report: docs/features/{feature}/review-tests.html  (run #N, <datetime stamp>)

<if any behavior gaps>     ⚠ N failing tests were left red — the implementation does not meet these criteria. Listed in the report; consider review-validate to fix.
<if any disagreements>     ⚠ N spec/code disagreements found — sources contradict each other; listed in the report for your decision.
<if any flagged>           ⚠ N items need your decision (see report / the questions above).
<if below floor>           ℹ Coverage landed below 80%; the remainder is accounted for in the report (not a failure — soft floor).
```

Do not commit. The user handles commits.

## Rules

- **"Unreachable / untestable / dead" is the highest-scrutiny verdict — prove it with a test, never argue it (Phase 4.5).** It is an empirical claim, recorded only after a test that *tries* to reach the code through the public surface fails with the specific unbypassable blocker named. The proof artifact is a test run by the project's normal test runner — never a hand-built binary or manual CLI poke. A passing reach-test is definitive proof of reachability; failing to write one is only suggestive, so unconfirmed "untestable" claims go back to the probe, not to the user.
- **Prove suspected behavior gaps, don't ask about them.** When a clear criterion looks unmet, that is BEHAVIOR-GAP-SUSPECTED, not a question: write the asserting test (pass → covered, fail → a proven red gap). Reserve user questions for genuine ambiguity / source disagreement, where no deterministic assertion exists.
- **Reach attempts and proofs are scratch work — leave the tree clean.** Phase 4.5 and the implementer delete every test that isn't a kept deliverable and confirm the scope's suite still compiles and runs before returning. A leftover non-compiling test breaks the whole package; an intentionally-red proven-gap test is the one allowed exception and must be recorded as such.
- **When sources disagree, report — never adjudicate.** The Blueprint's sections (product half, technical half, User Stories), the ADRs, and the code's observed behavior will sometimes contradict each other. Surface every disagreement to the user as a `doc-disagreement` with all sides quoted; do not pick a winner and do not grade coverage on one source's authority. The Blueprint is the statement of *intended* behavior to test against — never evidence of *what the code does*.
- **Coverage is a surface assertion, not a covered line.** A criterion is covered only when a test enters through the public interface and asserts the behavior. Incidental line execution is not coverage. The coverage tool is a hint, never the verdict.
- **The 80% floor is a discovery source and a soft target, never a gate (Phase 6.5).** Uncovered code becomes candidate behaviors that run through the same validator/skeptic/probe/implementer discipline — it is not a number to brute-force. Never write an assertion-free test or reach into internals to lift the percentage. A scope that finishes below 80% with an accounted remainder (unreachable-through-surface branches, excluded code, items awaiting a decision) is a complete, valid outcome — the report explains the shortfall rather than failing on it. Coverage-derived (`COV-`) candidates run after the Blueprint criteria are implemented, so the sweep targets only what is still dark.
- **Never test internals to close a gap.** If a behavior can't be observed through the surface, that's an observability/design finding — expose a safe additive API (testability change) or flag it. Do not write a test that reaches into internals.
- **Safe additive testability changes are the only unprompted production edits.** Exposing `Stats()`, splitting `main()`→`Run()`, exporting a needed symbol. Anything that changes observable behavior requires a user decision.
- **Never fix the implementation to make a gap test pass.** A failing gap test proves the implementation doesn't meet a documented criterion. Leave it red, flag it, and stop there. Fixing it is a separate, user-approved step.
- **Prefer fixing the change over altering a test.** If a testability change breaks a pre-existing test, the change wasn't behavior-preserving — revert it; do not edit the existing test to compensate (per CLAUDE.md).
- **Skepticism kills false positives.** Every claimed gap is validated and then challenged by the skeptic before any test is written. A miscited test triggers re-examination.
- **Gate on questions, not on gaps.** Independent genuine gaps are implemented automatically. Only behavior/design decisions block, and only the items they concern.
- **The report is the memory — but it is not infallible memory.** Always parse a prior `review-tests.html` on startup and always append this run to it on completion (new `runs` entry + a `history` append on each criterion) rather than overwriting prior runs. Keep the embedded JSON authoritative — the human sections render from it. Trust a prior verdict across runs only when its `evidenceGrade` is `test-verified`; re-examine every `reasoning-only` or `spec-asserted` `untestable`/`behavior-gap`/`doc-disagreement` rather than letting a wrong verdict calcify and suppress re-investigation forever.
