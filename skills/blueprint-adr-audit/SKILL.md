---
name: blueprint-adr-audit
description: Audit a blueprint (or other plan/design/spec/diff) against the repository's Accepted ADRs to find where it VIOLATES or CONTRADICTS a binding decision — using parallel sub-agents that each own a slice of the ADR corpus, then a synthesized verdict. This is a companion to blueprint-review, meant to run during blueprint work once the design is drafted and before the build starts. Use when the user says "check the blueprint against our ADRs", "does this violate any ADRs", "audit the plan for ADR compliance", "make sure the blueprint doesn't contradict an ADR", or "/blueprint-adr-audit". It is READ-ONLY: it reports findings and does not edit the plan, the ADRs, or any code. Do NOT use it to WRITE a new ADR (that is adr-write), to REVIEW the blueprint for gaps/correctness (that is blueprint-review), to review code for bugs (/code-review), or to check a spec's documentation quality (review-openapi).
---

# Audit a blueprint against the repository's ADRs

Determine whether a proposed plan violates or contradicts any **Accepted** Architecture
Decision Record currently in force. The plan is usually a **blueprint** but can be any
design artifact — a tech spec, design doc, an ADR the plan itself records, an
implementation checklist, or an uncommitted diff. The ADR corpus is whatever binding
decisions live in the repo (`docs/adr/`, `services/*/docs/adr/`).

**Where this fits.** This runs during blueprint work, once the design is drafted — a
companion to `blueprint-review`. `blueprint-review` checks the design against *itself* (gaps,
unresolved questions, correctness holes); this checks the design against the *binding
decisions around it*. Run it after the blueprint is stable and before the build starts, so a
contradiction with an Accepted ADR surfaces as a design fix, not a mid-build surprise. It is
also fine to run standalone whenever a plan needs checking against the ADRs.

This is **read-only**. You audit and report. You never edit the plan, the ADRs, or any
code, and you never run builds or tests as part of the audit. Acting on the findings
(renaming a field, capturing an open question, recording a superseding ADR) is a separate,
explicit follow-up the user approves — not part of the audit.

The engine is **fan-out**: the plan is small and shared, the ADR corpus is large and
divisible, so N sub-agents each read the whole plan and audit a disjoint slice of the
ADRs, and you synthesize one verdict. This keeps each agent's context tight enough to read
every ADR in its slice *closely* rather than skimming 40 of them in one pass.

## 1. Resolve what is being audited (the plan)

Resolve in order; stop at the first hit:

1. **Supplied** — the user named or pasted a file/dir/PR/diff → use it.
2. **A feature directory** — if the work centers on `docs/features/<name>/` (a blueprint +
   contract), the plan is that directory's design artifacts.
3. **The current diff** — `git diff --stat main...HEAD`; the plan is the changed
   design/contract files.

Assemble the **full plan artifact list** — every file an agent must read to know what the
plan decides. Typically: the blueprint/design doc (primary), the authored contract
(`openapi.yaml`), any decision-log/technical-shape sections it changed, and **any ADR the
plan itself records** (see the exclusion rule in §3). If you cannot identify the plan, ask;
never guess.

## 2. Discover and scope the ADR corpus

Discover, do not assume:

```
find . -type d -name adr -not -path '*/node_modules/*'
```

Then decide **which ADR sets bind this plan**:

- **Root / cross-cutting ADRs** (e.g. `docs/adr/`) bind every service, including the one
  the plan touches. Include them unless the user scopes them out.
- **The owning service's ADRs** (`services/<svc>/docs/adr/`) bind that service. Include.
- **Another service's ADRs** bind this plan only through a shared contract (e.g. the plan
  produces into that service). Include *only* if there is such a dependency, and say so.

**Confirm the scope out loud** before dispatching, because it materially changes the audit
("I'm reading 'our ADRs' as root + <svc>, excluding <other-svc>'s internal ADRs — say the
word to narrow it"). Only ADRs whose **Status is Accepted** are enforceable; the agents
verify each one's status, but scope the corpus to the accepted-ADR directories up front.

List the corpus as **explicit file paths** — you will partition this list.

## 3. Partition the work

- **The plan is shared, never partitioned.** Every agent reads the entire plan artifact
  list, because any ADR can conflict with any plan decision — you cannot slice the plan.
- **Partition only the ADR corpus**, by a **content-agnostic, deterministic key**
  (filename sort order). Do **not** bucket ADRs by which ones you suspect are relevant —
  relevance-based bucketing reintroduces the reviewer's bias the fan-out exists to avoid.
  Each agent decides relevance for its own slice independently.
- **Explicit file lists per agent** — guarantees full coverage, zero overlap, zero gaps.
- **Preserve corpus boundaries** so each agent gets the right binding-scope framing (root
  binds-all vs service-local).
- **Exclude any ADR the plan itself records** from every audit slice — it is *plan input*,
  not a pre-existing constraint. Put it in the shared plan reading list instead, so its
  decision is tested against every slice (an agent auditing root ADR-X will test the
  plan-recorded ADR's decision against ADR-X for free).
- **Batch size ~5–8 ADRs per agent.** Compute agent count as `ceil(corpus / ~7)`; keep
  batches even.

## 4. Dispatch the auditor sub-agents

Launch all agents **concurrently** — send them in a single message with multiple `Agent`
tool calls (subagent_type `general-purpose`). Give each the identical template below, with
`{PLAN_FILES}`, `{ADR_BATCH}`, and `{SCOPE_NOTE}` filled in.

Do **not** add "things to pay special attention to" hints. Seeding your own suspicions
biases the sweep and manufactures false positives; a clean, uniform prompt is both a better
audit and a better test of the method. (Observed: the sharpest hint a reviewer is tempted
to seed is often the one an unbiased agent correctly rules *out*.)

### Auditor prompt template

```
ROLE & GOAL
You are an ADR-compliance auditor. Determine whether a proposed plan VIOLATES or
CONTRADICTS any Accepted Architecture Decision Record (ADR) in your assigned batch. This is
READ-ONLY: audit and report only. Do not edit any file; do not run builds or tests.

THE PLAN (read ALL of these in full first; audit design intent — there may be no code yet):
{PLAN_FILES}   # one path per line; mark the primary; mark any ADR recorded BY the plan as
               # "treat its decision as PART OF THE PLAN, not a constraint to audit against"

YOUR ADR BATCH (audit the plan against ONLY these; other agents cover the rest):
{ADR_BATCH}    # explicit file paths

BINDING SCOPE
{SCOPE_NOTE}   # e.g. "ROOT set, binds all services" or "the <svc> service set, binds <svc>"
  - Only ADRs whose Status is Accepted are enforceable. Read each ADR's status line. Treat
    Proposed/Draft/Superseded/Rejected as non-binding — but if the plan DEPENDS on a
    non-Accepted ADR in your batch, flag it.
  - Honor Supersedes/Superseded-by links.

METHOD
  1. Read the plan fully. Extract its concrete, load-bearing decisions (contract shape;
     storage/state behavior; auth; async/eventing + delivery/ordering; module/package
     boundaries; test approach; deferred work).
  2. For EACH ADR in your batch, derive its rule/invariant FROM THE ADR TEXT — never from
     what the plan says about it.
  3. Test each plan decision against each ADR in your batch. Classify.

CLASSIFICATION (most severe first)
  - VIOLATION       — plan does what an Accepted ADR forbids, or omits what it mandates. Blocking.
  - CONTRADICTION   — plan asserts a decision that directly conflicts with an Accepted ADR's
                      decision, without superseding it. Blocking.
  - SUPERSEDES(confirm) — plan intentionally overrides an ADR and says so explicitly. Not a
                      violation; surface it so a human confirms the supersession is intended/recorded.
  - TENSION         — gray area / partial compliance / unstated-interpretation-dependent.
                      Non-blocking; say precisely what would resolve it.
  - COMPLIANT       — plan respects a relevant, load-bearing ADR. List briefly; do NOT pad
                      with trivially-irrelevant ADRs.

EVIDENCE DISCIPLINE
  - Every finding cites the ADR (number + title) AND the plan location (file + line or
    section), and quotes the specific ADR clause that binds.
  - Do NOT manufacture violations from silence: the plan being silent on X is a violation
    only if an ADR mandates X.
  - When uncertain, use TENSION and state what would resolve it — do not inflate to VIOLATION.
  - Derive each ADR's rule independently; do not assume the plan's characterization is correct.

OUTPUT (return exactly this; your returned text IS the result, not a message to a human):
  BATCH: <the ADR ids you audited>
  VERDICT: PASS or FAIL   (FAIL if >=1 VIOLATION or CONTRADICTION in your batch)
  FINDINGS (most severe first):
    [CLASS] ADR-<n> <title> — RULE: <cited clause> | PLAN: <file + line/section> | RESOLUTION: <one line>
  COMPLIANT & RELEVANT: ADR-<n> <title> — <the decision the plan honors> (one line each)
  NOT APPLICABLE: <bare id list>
  NON-ACCEPTED DEPENDENCY: <any, or "none">
```

## 5. Synthesize

Merge the agent results into one report:

- **Overall verdict: FAIL if any agent reports a VIOLATION or CONTRADICTION; else PASS.**
- **Findings table**, most severe first, across all agents — class, ADR (with corpus),
  the tension in one line, and *when* it resolves (now / at implementation / in a named
  follow-up ticket).
- **Cluster related findings.** When several ADRs flag the *same* underspecified plan
  element (a common pattern: one deferred mechanism drawing tension from three different
  ADRs), say so — that convergence is the strongest signal in the audit and usually means
  that element needs its own decision, not three separate fixes.
- **Disambiguate ADR numbers across corpora** (root ADR-0007 ≠ service ADR-0007). Always
  prefix the corpus.
- Keep the COMPLIANT and NOT-APPLICABLE lists terse; the findings are the product.
- End by separating **act-on-now** items (usually contract/naming issues in files that
  exist) from **carry-forward** items (implementation-time invariants, follow-up-ticket
  decisions), and ask what the user wants to do — do not act unprompted.

## Notes and trade-offs

- **Uniform vs. targeted split.** The content-agnostic split is unbiased but can spend a
  whole agent on a batch nothing in the plan could touch (e.g. UI/frontend ADRs for a
  backend plan). That waste is the price of no bias; keep it unless the user asks to
  prioritize, in which case say you are trading neutrality for efficiency.
- **Pre-implementation is normal.** Audits often run on a design before any code exists —
  the agents audit *design intent*. Say so in the plan block so agents don't look for code.
- **One agent is fine for a small corpus** (≲10 ADRs). Fan out when the corpus is large
  enough that a single context would skim.

## Boundaries

- READ-ONLY. Never edit the plan, ADRs, or code inside this skill; never `git` mutate.
- Do not seed the agents with relevance hints or suspected violations.
- Do not treat a plan-recorded ADR as a constraint to audit against — it is plan input.
- Surface a doc-vs-ADR *behavior* disagreement as a finding; do not silently "fix" either
  side to make them agree.
