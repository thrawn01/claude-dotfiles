---
name: review-openapi
description: "Review an OpenAPI spec as the product it is — documentation for an external API
  consumer — and fix what fails that reader. Catches internal-context leaks (framework names,
  repo doc paths, ticket/design-doc ids, 'per <framework>' justifications), spec-splained
  self-correction machinery (did-you-mean 404s, teaching-error rules), condition-specific
  vocabulary on shared schemas that renders under every status, union error vocabularies that
  advertise codes an endpoint cannot return, and missing or incoherent request/response examples.
  Use when the user says 'review the openapi', 'review-openapi', 'audit the API docs', 'review the
  spec', or after contract changes. This is the API-consumer counterpart to review-for-reader
  (which reviews code comments/docs for the next maintainer); it is NOT a schema/breaking-change
  checker (use review-behavior-change) and NOT a linter substitute (duh lint still runs)."
argument-hint: "[path/to/openapi.yaml]"
allowed-tools: [Read, Grep, Glob, Edit, Bash, Agent]
---

# Review OpenAPI

Review an OpenAPI spec the way its **actual reader** experiences it: an external API consumer —
human or LLM agent — who has this one document, no access to the repo, no knowledge of the
company's frameworks, tickets, or design history. The spec is a product for that reader. This
skill finds and fixes the prose and examples that fail them.

It reviews **the documentation quality of the contract** — descriptions, error vocabularies,
examples. It does not judge schema design or flag breaking changes (`review-behavior-change`),
and it does not replace the spec linter (`duh lint` in DUH-RPC repos) — it runs the linter as a
gate around its own edits.

## The core test: the Consumer Test

> For every description, example, and error vocabulary: **does it serve someone integrating
> against this API from the outside, with only this document?** If understanding a sentence
> requires knowing an internal framework, reading a repo doc, or having watched the design happen,
> it fails. If a rendered endpoint page shows information that endpoint cannot produce, it fails.

## 1. Resolve the spec

- Explicit argument → use it.
- Otherwise: specs touched by the current diff (`git diff --name-only <base>...HEAD | grep
  -i 'openapi.*\.ya?ml$'`), else `**/api/**/openapi.yaml` in the repo. Multiple hits with no
  argument → review each in turn.
- Locate the implementation's error emitters for Rule 4 (in this repo's Go services: the
  `NewServiceError` / `NewServiceErrorWithCode` call sites and the handlers that reach them).

## 2. The audit rules

Audit the whole spec against each rule. Fix findings in place.

### Rule 1 — Self-contained: no internal context leaks

The reader has never heard of your RPC framework, your monorepo, or your tickets. Remove or
rewrite, anywhere in the spec:

- **Internal framework/protocol names** used as explanation ("Standard DUH-RPC error body",
  "DUH paths are static").
- **Repo document references** ("see docs/duh-rpc-cheatsheet.md").
- **Ticket / design-doc / roadmap ids and internal shorthand** ("(D12)", "ENG-132", "slice 6",
  "the wire transport", invariant labels like "(I3)").
- **Deferred justifications** — "retryable per DUH" tells the reader nothing. State the actual,
  consumer-relevant reason: *"Safe to retry: every operation is read-only."*
- **Roadmap talk** — "lifecycle metadata arrives in slice 6" is internal planning. Describe what
  the API is today; omit what it isn't.

Rewrite test: every sentence must be justifiable to an external integrator using only concepts
the spec itself defines (its schemas, its endpoints, HTTP, and the domain — e.g. git plumbing for
a git API is fine; the house RPC framework is not).

### Rule 2 — Don't spec-splain the API's self-correction machinery

Convenience behaviors that exist to rescue callers who *have not read the spec* — did-you-mean
suggestions on unknown endpoints, teaching 400s that spell out the schema, endpoint listings in
error bodies — do **not** belong in the spec. The spec reader already has the endpoint list and
the schemas; documenting the recovery machinery is teaching them how the API works internally,
not how to use it. Keep the behaviors implemented and surface-tested; delete their documentation
from the spec, including cross-references they leave dangling (details fields, code lists,
"see the top-level description" pointers).

What stays: error facts a spec-reading consumer acts on — status codes, the code discriminator
values, what `details` carries, retry semantics.

### Rule 3 — Shared schemas stay generic; specifics live where they apply

A shared error schema (`Reply`-style: code/message/details) is referenced by **every** error
response on **every** endpoint. Any condition-specific enumeration in its property descriptions —
"the codes are REPO_NOT_FOUND, REF_NOT_FOUND, … (all HTTP 404)" — renders under a 500 on an
unrelated endpoint. The shared schema states only the general rule (what the field is, how to
branch on it, where the specific values are listed); the specific vocabularies live on the
response definitions they belong to.

### Rule 4 — Per-endpoint exhaustive error vocabularies, verified against the code

Shared response components document the **union** of what all endpoints can return — so a
`repos.get` renders `PATH_NOT_FOUND` it can never produce. Fix by splitting response components
by *actual* vocabulary and wiring each endpoint to the variant matching exactly what its
implementation emits:

1. **Derive the truth from the error emitters, never from the existing spec prose.** Walk each
   handler's reachable error paths (in Go: which `err*` constructors each endpoint's call graph
   reaches). Watch for structural facts: an endpoint without pagination cannot return a
   cursor-expired code; a name-anchored cursor cannot expire; a filter-not-deny endpoint has no
   404.
2. Define one response component per distinct vocabulary (`NotFoundRepo`, `NotFoundRev`,
   `NotFoundRevCursor`, `BadRequest`, `BadRequestWrongType`, …), same wire schema throughout.
3. Each component's description lists its codes **exhaustively and says so** ("the only code
   here", "the code is one of: …") with a one-clause meaning per code.
4. Rewire every endpoint's responses to its exact variants.

This is documentation-only: the wire schema and generated code must not change (see Verify).

### Rule 5 — Worked request/response example pairs in one consistent world

Every operation carries a request example and a 200 example, where **the request example is the
call that produces the response example**. All examples across the spec share **one example
world** (one fictional repo/tenant/dataset) so values cross-reference between endpoints: the id
one endpoint returns is the id another endpoint's example queries.

Coherence is load-bearing — the example world's facts must actually hold:

- Graph/relational claims are real: a merge-base example yields what the example history implies;
  ahead/behind counts match the listed items; a "more pages exist" flag is impossible after a
  terminal item (e.g. a root commit).
- Weave in teaching cases: an optional field **absent** where the API omits it (not null-filled),
  a realistic opaque cursor paired with `has_next_page: true`, input-format variety across
  requests (each accepted form — symbolic name, short name, raw id — appears at least once).
- Binary/streaming endpoints get a small literal example on their media type.
- Examples are illustrations, not contract: keep them typical-shaped, not exhaustive.

## 3. Verify (gate every edit batch)

1. **Spec lints**: the repo's spec linter (`duh lint <spec>` here) passes.
2. **Codegen-neutral**: regenerate/build the generated target (`bazel build …:generated` or the
   repo's `duh-gen` task). Doc-only changes must produce no schema/proto/fieldmap churn.
3. **Contract tests pass**: any tests that read the spec (vocabulary censuses, teaching-error
   surface tests) still pass — Rule 2 removes *documentation*, never behavior.

## 4. Report

Summarize per rule: findings fixed (with before → after for the representative ones), findings
left (with why). In a suite/pipeline context, emit findings in the host's ticket format instead.

## Boundaries

- Fix prose and examples **in the spec only** — never change schemas, field numbers, paths, or
  implementation behavior to make documentation "fit". A doc/code disagreement about *behavior*
  is a finding to surface (or a `review-behavior-change` handoff), not a silent doc edit.
- Do not invent error codes or example values the implementation cannot produce — Rule 4's
  derivation is from code, and Rule 5's world must be producible by the documented API.
- Internal design docs (blueprints, ADRs, explainers) are out of scope — they are *supposed* to
  carry internal context. Only the consumer-facing spec is held to the Consumer Test.
