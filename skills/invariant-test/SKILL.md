---
name: invariant-test
description: Derive surface tests from a service's stated invariants (Accepted ADRs, load-bearing doc comments, tech specs), targeting the assertions a codebase's defensive mechanisms (mutexes, transactions, atomic backend ops) cannot satisfy — then write each test and mutation-validate it red-then-green so it provably fails when the invariant is violated. Use when the user says "test the invariants", "what test would have caught this", "find correctness-test gaps", "harden the tests against invariant violations", "invariant-test", or after a concurrency/correctness bug that passed `-race` and every existing test (e.g. a single-writer or ownership violation) and you want a test that would have caught it. Do NOT use to check coverage against PRD acceptance criteria (use review-tests), to validate a list of already-identified bugs (use review-validate), or to fix the implementation (this skill writes the proving test and reports live violations loud; hand fixes to review-validate).
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, Agent, AskUserQuestion
---

# Invariant Test

Turn a service's **stated invariants** into surface tests that **fail when the invariant is violated** — the tests that integrity-only suites and the race detector cannot produce.

The motivating case: querator's single-writer-per-partition invariant (ADR-0003, restated load-bearing at `internal/logical.go:97-100`) was violated by the DLQ-movement path, yet `-race` was green and every test passed. It survived because **no test could fail when single-writer broke** — every DLQ test asserted *integrity*, which the defensive per-backend mutexes provide for free. This skill manufactures the assertions those mutexes cannot satisfy (liveness, timeliness, ordering, ownership) and proves each one catches the violation before declaring it done.

**Three principles run through the whole pipeline:**

1. **`-race` green proves memory safety, not architectural correctness.** A data race and an invariant violation look identical at the diff — both are "two goroutines touch this resource" — but they have opposite fixes (add a lock vs. remove the second writer). A clean race run and a tidy mutex actively *hide* the architectural violation. This skill never treats a passing race/integrity test as evidence an invariant holds.

2. **A correctness test you have not watched go red is not yet a correctness test.** Every test this skill writes is **mutation-validated**: deliberately break the invariant, confirm the test turns red, restore, confirm it turns green. A test that stays green when the invariant is violated is rewritten until it doesn't — or the invariant is flagged as needing new observability. This is non-negotiable and is the load-bearing phase.

3. **Test the invariant's *purpose*, never its mechanism.** You cannot assert "only one goroutine wrote this partition" at the surface, and `-race` can't either. You assert the behavior the invariant *exists to guarantee* (the waiter is woken, the timer advances now, ordering holds) — observed through the public surface per the `surface-testing` skill.

This skill requires a filesystem, the source code, and the ability to run the test suite. It is Claude Code only. It writes the proving test; it does **not** fix the implementation.

## How this differs from neighboring skills

- **`review-tests`** measures coverage of *spec acceptance criteria* (PRD / tech spec / user stories) and fills gaps. `invariant-test` starts from *invariants* (ADRs + load-bearing doc comments), derives the consequences of violating them, and writes the one assertion a defensive mechanism can't satisfy. Where `review-tests` asks "is this criterion tested?", this asks "would any test fail if this invariant broke?" Running `review-tests` first and `invariant-test` second is a reasonable pairing.
- **`review-validate`** validates a list of *already-identified bugs*, proves each with a failing test, then **fixes** them. `invariant-test` discovers the *missing test class* from the design contract, and when a test is red-now it reports a **live invariant violation** loud but does not fix it — hand the fix to `review-validate`.
- **`review-behavior-change`** flags *undocumented* changes to public behavior in a diff. `invariant-test` works from the *documented* invariants toward tests, regardless of any diff.
- **`surface-testing`** is the philosophy every test here obeys. Read it; this skill assumes its rules (public interface only; expose observability when async behavior isn't visible at the surface).

## Inputs

`$ARGUMENTS` may be any of:

- **A feature directory** (e.g. `docs/features/<name>/`) — scope invariants to that feature's tech spec plus the ADRs and doc comments its implementation touches.
- **A specific invariant or issue** stated in the prompt or referenced (a Linear/GitHub issue like ENG-55, an ADR number, a quoted doc comment). Build the ledger from that one invariant and go deep.
- **Nothing** — scan the repository: every Accepted ADR plus load-bearing doc comments across the codebase. Confirm scope with the user before fanning out, since a whole-repo scan can be large.

Before starting, locate and read what exists:

- **`docs/adr/`** — list every ADR; read the **Accepted** ones (skip Proposed/Superseded/Rejected unless the user asks). ADRs are the primary invariant source.
- **`docs/CONTEXT.md`** (walk up from any feature dir) — domain glossary; use it to map invariant terms onto code, surface, and stats names.
- **Tech specs** in the target feature directory, if scoped to a feature.
- **`invariant-test.html`** — the report this skill wrote on prior runs, if present at the repo or feature `docs/` root. Parse its embedded JSON (`<script type="application/json" id="invariant-test-data">`) to recover the `runs` log and each invariant's status history. Use it to (a) avoid re-deriving invariants already covered by a `mutation-verified` test, (b) detect regressions where a previously-proven invariant test was deleted or now passes-under-mutation (stopped catching the violation), (c) carry forward open `needs-observability` items, and (d) **re-examine, never trust, any prior verdict whose `evidenceGrade` is not `mutation-verified`.** A reasoning-only "no surface consequence" verdict that calcifies will suppress re-investigation forever; only a test that was written and watched go red-then-green is carried forward without re-probing.

If no ADRs, doc-comment invariants, or tech specs can be found, tell the user: there is no *stated* correctness to test against. Offer to elicit the invariant directly ("what must always/never be true here?") or to record it as an ADR first (`adr-write`) — an unstated invariant cannot be checked and will simply be re-broken.

## Phase 0: Scope, Surface & Baseline

1. **Locate invariant sources.** Read the Accepted ADRs in scope. Then grep the codebase for **load-bearing doc comments** — the contract vocabulary that signals a stated invariant:
   `MUST`, `ONLY`, `single`, `exactly one`, `never`, `always`, `invariant`, `synchronization point`, `singleton`, `single-threaded`, `at most one`, `owns`, `must go through`.
   Also capture the **bypass/hedge vocabulary**, which marks where an invariant is *deviated from* (these are both invariant evidence and prime suspects for live violations):
   `directly`, `bypass`, `without going through`, `defensively`, `fast path`, `internal`, `should only`, `normally`.
2. **Identify the defensive mechanisms.** For each resource an invariant governs, find what already guards it: mutexes, RWMutex, atomics, DB transactions, individually-atomic backend ops, channels. **Record these per resource** — they decide which assertion buckets are masked in Phase 3. This is unique to this skill and you cannot skip it.
3. **Identify the surface.** Per `surface-testing`, list the public entry points (HTTP/gRPC handlers, CLI `Run()`, exported client methods, stats/observability endpoints). Every test enters here. Note the observability surface specifically (e.g. a `Stats()` / `QueueStats` API) — invariants whose consequences are otherwise invisible are tested through it.
4. **Run the test suite once** for a baseline, exactly as CI does (e.g. Go: `make ci` or `go test ./... -race -p=1`). Capture pass/fail. A green baseline is the backdrop against which a red-now invariant test stands out as a live violation.
5. **State scope to the user** in a few lines: which invariants are in scope, which resources/defensive mechanisms were found, which surface, and whether the baseline is green.

## Phase 1: Invariant Ledger

Build a numbered ledger. Do it yourself, or delegate to one extraction sub-agent if the ADR set is large. Each entry:

- **id** — `INV-1`, `INV-2`, … Carry forward ids from a prior `invariant-test.html` when the invariant is unchanged so history lines up.
- **statement** — the invariant in one sentence ("each storage partition has exactly one writer: its Logical's `requestLoop` goroutine").
- **source** — exact citation (ADR number + section, or `file:line` of the doc comment). Quote it.
- **resources** — the shared state/resource(s) it governs (the DLQ partition; `p.State`).
- **defensive mechanisms** — what currently guards each resource (from Phase 0 step 2), e.g. "`MemoryPartition.m.mu` on every method; Mongo ops individually atomic."
- **purpose** — *why the invariant exists / what it protects.* This is what you will actually test. ("The single writer is the only thing that, in one pass, keeps `p.State` consistent with storage **and** wakes blocked waiters **and** advances the lifecycle timer.")

Skip nothing that is stated. If a doc comment and an ADR state the same invariant, record one entry citing both.

## Phase 2: Consequence Derivation (parallel sub-agents)

Partition the ledger into balanced batches and spawn a small number of sub-agents in parallel (Agent tool, **foreground**, `model: "sonnet"`; default general-purpose agent for full tool access). For each invariant, derive **what a user would observe if it were violated**, bucketed:

- **integrity** — data wrong, lost, duplicated, corrupted.
- **liveness** — something that should happen never does / hangs (a blocked waiter never woken).
- **timeliness** — happens late / drifts (a timer not advanced; state stale until an unrelated wake).
- **ordering** — sequence/causality broken.
- **other** — uniqueness, idempotency, monotonicity, etc.

Sub-agent prompt structure:

```
You are deriving the observable consequences of violating a stated invariant.
For each invariant below: read the cited source and the code around the governed
resource yourself. Then answer, concretely and in terms of the PUBLIC SURFACE only:

For each consequence bucket (integrity / liveness / timeliness / ordering / other):
- Would violating this invariant produce an observable defect in this bucket? Describe it.
- Is that defect observable through the public surface (endpoint / exported call / stats)?
  If yes: name the exact surface call and the assertion that would detect it.
  If no: say so — this becomes a candidate "needs-observability" finding.

Invariant: <id> — <statement>
Source: <citation, quoted>
Governed resource(s): <...>
Defensive mechanisms on those resources: <...>
Purpose (what it protects): <...>
Public surface available: <entry points + stats API>

Output per invariant, per bucket: { bucket, defect, surfaceObservable: bool,
  surfaceCall, proposedAssertion }.
Do NOT propose a test yet. Just enumerate consequences and how each would be seen.
```

Collect all consequences. Read the relevant source yourself before trusting an agent's "not surface-observable" claim.

## Phase 3: Mask Filter (the load-bearing critic)

**This is the step every integrity-only suite skips, and the reason ENG-55 survived.** Spawn one sub-agent (Agent tool, **foreground**, `model: "sonnet"`) — or do it directly for a small ledger — to challenge each consequence against the defensive mechanisms recorded in Phase 1.

For every consequence, ask the discriminating question:

> **Would this assertion still PASS if the invariant were violated, because a defensive mechanism (mutex / transaction / atomic op) satisfies it anyway?**

- **Yes → DISCARD.** The assertion tests the lock, not the invariant. Integrity assertions almost always fall here when a mutex or atomic backend op guards the resource ("no corruption / no lost item" passes under the broken DLQ path because the mutex serializes writes). Record the discard with its reason in the report — it documents *why* the obvious test would have proven nothing.
- **No → KEEP.** The defensive mechanism cannot make this pass while the invariant is broken. These are the surviving assertions — usually **liveness** ("the blocked waiter is woken promptly") and **timeliness** ("the lifecycle timer advanced now, not on the next unrelated wake"). They are what the test must assert.

Sub-agent prompt structure:

```
For each (invariant, consequence) below, decide KEEP or DISCARD.
DISCARD iff a listed defensive mechanism would make the proposed assertion PASS
even while the invariant is violated (i.e. the assertion tests the mechanism, not
the invariant). Otherwise KEEP. For each, give a one-line reason and, for KEEPs,
sharpen the assertion and its bound (e.g. "require.Eventually within 1s", a tight
deadline a mutex cannot satisfy because the missing wake/timer is a liveness gap).
Be adversarial: prefer DISCARD when unsure whether the mechanism masks it, and say
what additional observable would be needed to make a KEEP possible.
```

After this phase each invariant has either: one or more **KEPT assertions**, or **no surviving surface-observable assertion** (every consequence is either not observable or masked).

## Phase 4: Skeptic & Gap Check

For the KEPT assertions, spawn one sub-agent (Agent tool, **foreground**, `model: "sonnet"`) as defense attorney for the existing suite. Skip if there are none.

```
For each proposed assertion, argue it is unnecessary:
- Does a surface test ALREADY exist that fails when this invariant breaks? Cite it
  (file:line) and quote the assertion. If so, this is ALREADY-PROVEN — record, don't rewrite.
- Would the proposed assertion actually catch the violation, or is its bound so loose
  the masked mechanism still satisfies it? If loose, say how to tighten it.
- Is the consequence real, or would normal operation produce it anyway (flaky/false alarm)?
Return ALREADY-PROVEN (cite test) | NEEDS-TEST (refined assertion) | NOT-A-REAL-CONSEQUENCE (reason).
```

Read the cited "already-proven" test yourself before trusting it — a test that asserts the consequence but with a bound the mutex satisfies is **not** proof and goes back to NEEDS-TEST. The output is the queue of assertions that need a new, mutation-validated test.

## Phase 5: Write & Mutation-Validate (the gate)

For each NEEDS-TEST assertion, spawn one prover sub-agent (Agent tool, **foreground**, `model: "sonnet"`; it **must** have Write + Bash to run the suite). It writes the surface test and proves it real by mutation. **A test is not done until it has gone red-on-violation and green-on-correct.**

Per assertion:

1. **Write the surface test** following `surface-testing` and the project's CLAUDE.md testing patterns — public surface only, drive the system to the condition through the real API, assert the kept consequence with the tight bound from Phase 3 (e.g. `require.Eventually` within a deadline a mutex cannot satisfy). Backend-agnostic where the invariant is (run across all backends if the project parameterizes them).
2. **Run it on current code:**
   - **RED now** → the invariant is **currently violated**: a *live bug*, exactly the ENG-55 situation on `main`. Leave the test red, mark it `live-violation`, and report it loud. Do **not** fix the implementation — that is `review-validate`'s job. The live failure *is* the red-then-green proof's red half; note that applying the fix should turn it green.
   - **GREEN now** → you must prove the test actually detects the violation, via **mutation**:
3. **Mutation-validate (only when green now).** Deliberately reintroduce the invariant violation in a controlled, reverted way, and confirm the test catches it:
   - Inject the known failure mode: e.g. reintroduce the direct-write bypass; remove/skip the wake (`notifyExpired` / waiter-assignment); stub out the timer advance; relax the single-writer routing. Choose the smallest mutation that embodies *this* invariant's violation.
   - Run the test → **expect RED.** If it stays **GREEN**, the test does **not** detect the violation (bound too loose, wrong observable, or the masked mechanism still satisfies it). Revert, rewrite the assertion (tighten the bound / target a different surface observable / expose new observability — see step 5), and repeat from step 1. Never accept a test that stays green under its own mutation.
   - **Revert the mutation** (leave the tree exactly as found) and run the test → **confirm GREEN.**
   - Record the mutation used and both outcomes. Mark the test `mutation-verified`.
4. **No surviving assertion / not surface-observable** → the invariant has no surface consequence a test can reach. Per `surface-testing`, the fix is to **expose observability** (a `Stats()` field, a metric, a debug endpoint that reveals the protected state). This is a code change to the implementation's *observability*, not its behavior — surface it to the user as a decision (Phase 6), do not silently invent it. Until exposed, mark `needs-observability`.
5. Keep mutations strictly local and reverted. The working tree must end identical to how it started except for the **added test files**. Never leave an injected mutation behind; never leave a `live-violation` fix applied.

Do the prover phase yourself instead of via sub-agent if the ledger is small — the red-then-green discipline matters more than the delegation.

## Phase 6: Decisions Gate

Surface only what genuinely needs the user (use `AskUserQuestion`):

- **`needs-observability` invariants** — "INV-N has no surface-observable consequence; to test it I'd add `<observable>` to the Stats API. Add it, or accept the invariant as untestable for now?"
- **`live-violation` tests left red** — report each as a proven live invariant violation; ask whether to hand it to `review-validate` to fix now, or just leave the failing test as the standing proof.
- **doc/code disagreements** — if the code's actual behavior contradicts a stated invariant in a way that isn't simply a bug (e.g. the ADR is stale), report it; do not adjudicate which source wins.

Everything with a `mutation-verified` test needs no decision — it is recorded and done.

## Phase 7: Report

Write `invariant-test.html` at the feature `docs/` root (feature-scoped) or repo `docs/` root (repo-scoped). The report **accumulates across runs**: keep the current state as the primary view plus a compact per-run history. On each run, append to the `runs` log and append each invariant's new status to its `history` — never discard prior runs. Get the timestamp via `date "+%Y-%m-%d %H:%M"` and inline it as text.

The report is **both** human-readable and machine-parseable:

- Embed `<script type="application/json" id="invariant-test-data">…</script>` with the structured data, authoritative; render the human table from it. Schema per invariant: `{ id, statement, source, resources, defensiveMechanisms, purpose, consequences:[{bucket, defect, surfaceObservable, verdict, reason}], test:{file, assertion, mutationUsed, redOnMutation, greenOnCorrect}, status, evidenceGrade, history:[...] }`.
- **status** ∈ `mutation-verified` (test written, proven red-on-violation/green-on-correct) · `live-violation` (test red now, invariant currently broken) · `already-proven` (existing test, re-confirmed) · `needs-observability` (no surface consequence; observability change proposed) · `discarded-all` (every consequence masked or unobservable — documented why) · `open-decision`.
- **evidenceGrade** ∈ `mutation-verified` · `live-red` · `reasoning-only` · `spec-asserted`. Only `mutation-verified` and `live-red` are trusted across runs without re-probing.
- Human sections must include: scope; the invariant ledger with sources; per invariant the **kept vs discarded** consequences (the discards documented — "integrity assertion discarded: mutex satisfies it even when single-writer is violated"); each test's mutation proof (mutation used → red, reverted → green); live violations called out at the top; and the run history.

Close with a short chat summary:

```
## Invariant Test Complete — {scope}

Invariants examined:     N
Tests written & proven:  N  (mutation-verified)
Live violations found:   N  (tests left red — invariant currently broken)
Needs observability:     N  (no surface consequence; change proposed)
Already proven:          N

<if live violations>   ⚠ N invariants are currently VIOLATED — failing tests left as proof. Hand to review-validate to fix.
<if needs-observability> ⚠ N invariants need a new observable to be testable — your decision (see report).
Report: <path>
```

## Rules

- **Never accept an integrity assertion as proof an invariant holds when a defensive mechanism guards the resource.** It passes on broken code. Discard it and say why, in the report.
- **Every written test is mutation-validated or it is not done.** Red-on-violation, green-on-correct, mutation reverted. A green-now test with no mutation proof is `reasoning-only`, not coverage. This is the whole point of the skill.
- **Test the purpose, not the mechanism, through the surface only.** No test calls an internal function to observe the invariant; if the invariant is invisible at the surface, expose observability (a decision for the user) rather than reaching inside.
- **Tight bounds are the weapon.** Liveness/timeliness assertions discriminate from masked mechanisms *because* of their bound — `require.Eventually` within a deadline the missing wake/timer cannot meet. A loose bound silently re-admits the masked mechanism; the skeptic and the mutation step exist to catch that.
- **Report live violations loud; do not fix them.** A red-now test is a discovered live invariant violation — surface it and route the fix to `review-validate`. This skill produces the test that *proves* correctness, not the change that *restores* it.
- **Leave the tree clean.** Added test files only. No injected mutation left behind; no live-violation fix applied. Re-run the baseline at the end to confirm the suite state is exactly the added tests' contribution.
- **The report is memory, not infallible memory.** Always parse a prior `invariant-test.html` on startup and append this run on completion. Trust a prior verdict across runs only when `evidenceGrade` is `mutation-verified` or `live-red`; re-examine every `reasoning-only` / `spec-asserted` verdict rather than letting a wrong "no surface consequence" calcify and suppress re-investigation.
