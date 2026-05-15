---
name: spec-review
description: Review an existing tech spec for gaps, inconsistencies, unresolved soft flags, and ambiguities that would force implementation decisions during the build, then produce an updated version. Use when the user asks to "review the tech spec", "check the spec", or "update the spec"; or when a plan-from-prompt session has surfaced technical questions that need to be resolved back in the spec. Do NOT use to start a new tech spec from scratch (use spec-create) or to make minor wording edits that don't need a structured review.
---

# Review a Technical Spec

Read the existing tech spec, surface findings as a structured list, work through them with the user, and write an updated version to the same path.

## Environment

| | Claude Code | Claude chat |
|---|---|---|
| **Reading the spec** | Read from `docs/features/{feature}/tech-spec.md` | Ask the user to paste the spec |
| **Writing the updated spec** | Write to the same path on disk | Produce as markdown artifact; remind user to replace the file at its original path |
| **ADR offer at end** | Invoke `adr-write` for approved decisions | Surface decisions clearly; user takes them to Claude Code |

If Read, Write, and Edit tools are available in your toolset, you are in Claude Code; otherwise you are in Claude chat.

## Review perspective

Look for `CONTEXT.md` files in `docs/` directories relevant to the feature being reviewed (see the CONTEXT-FORMAT.md in the prd-create skill for location rules). Read any that exist once and hold them in memory for the session. Use them to catch terminology conflicts — if the spec uses a term differently than the glossary, or introduces a new domain term without defining it, that is a finding.

Read the spec as an engineer or planner who is about to break it into implementation phases. For each section, ask: do I have enough detail to produce concrete tasks, or will I have to make architectural decisions during the build? Ambiguities that force implementation-time design decisions are the highest-priority findings.

Also scan the code that implements (or partially implements) the spec. Where the spec and the code disagree, those disagreements are findings — often the highest-priority ones, since they mean the document no longer describes reality.

If the review was triggered by a `plan-from-prompt` session that surfaced technical questions, those questions are pre-seeded findings — include them in the list alongside anything discovered fresh.

`[NEEDS PRD CLARIFICATION: ...]` soft flags in the spec are *indicators to investigate*, not automatic findings. For each marker, check whether the question has since been answered elsewhere in the spec or in the linked PRD. The spec often drifts: a decision gets made and written into a section, but the original marker is never cleaned up. Classify each marker as either **stale** (answer exists — finding is "remove the marker and reconcile the text") or **unresolved** (answer is genuinely missing — finding is "resolve now or escalate to PRD"). Do not surface a soft flag as an open question without first confirming the spec has not already answered it.

### Coverage pass before findings

Before generating a single finding, read the spec end-to-end and build an internal coverage map — note which sections or paragraphs cover which topics (components, data, API, migrations, failure modes, testing surfaces, etc.), using section headings or line references. Also list every file in `docs/adr/` and read each title. Read the full ADR for any title that names a topic the spec touches — components, data, API patterns, auth, error handling, deployment, anything the spec has a section on. The spec must be consistent with these decisions, and ADR-settled topics are not gaps just because the spec refers out to them instead of restating them. Findings are generated against *this map and the ADR set*, not against an abstract checklist of "what a spec should have."

This is the step that prevents false-positive findings. If you skip it, you will flag things as missing that are actually addressed under a different heading, covered in prose, or already decided in an ADR — and the user will correct you one by one.

## Finding categories

- **Gaps.** A topic that is *entirely absent* from the document. Not "covered briefly," not "addressed under a different heading," not "mentioned in passing." If the spec says anything substantive about the topic — even one sentence in another section — it is not a gap. Content that is present but too thin belongs under **Ambiguous implementation decisions**, not here.
- **Inconsistencies.** Technical contradictions within the document — component A described as owning X in one section, component B in another; a constraint in one section that rules out an approach described elsewhere.
- **Drift from code.** Places where the spec no longer matches what has been implemented. Each one needs either a spec update to match reality or a decision to change the code back.
- **ADR conflict.** The spec contradicts, ignores, or silently re-decides something already settled in an ADR under `docs/adr/`. The finding is "align the spec with ADR-NNNN, or make the departure explicit and capture a superseding ADR."
- **Stale soft flags.** `[NEEDS PRD CLARIFICATION: ...]` markers whose underlying question has already been answered elsewhere in the spec or PRD. The finding is "remove the marker and reconcile the text with the decided answer."
- **Unresolved soft flags.** `[NEEDS PRD CLARIFICATION: ...]` markers whose question is genuinely unanswered. Each needs either a resolution now or escalation back to the PRD. Only classify a marker as unresolved after confirming the spec and PRD do not already answer it.
- **Ambiguous implementation decisions.** Requirements that could be built multiple ways with meaningfully different consequences — anything an engineer would reasonably stop and ask about mid-build. Content that is present in the spec but too thin to resolve the decision goes here.
- **Missing testing surfaces.** `spec-create` treats surface identification as a design output; a review should verify it is present. The `surface-testing` skill prescribes the specific decisions the spec must have locked in — flag any of these that are absent or underspecified:
  - **No testable entry point.** No `Run(args, opts)` function for a CLI, no `Start()`/`Shutdown()` lifecycle for a service, no named exported surface for a library.
  - **External dependency without a substitute.** A service, store, or API outside the deployment unit with no substitute tier chosen (in-process fake, testcontainers, or hand-written) and no library or image named.
  - **Async behavior with no observable assertion path.** A behavior that produces no downstream effect through the surface and no `Stats()`/status endpoint to assert against.
  - **Time coupling without an injected clock.** Retries, expiries, or scheduled work with no injectable clock in the component design.
  - **In-memory store without a parity-testing model.** An in-memory variant of the real store is mentioned or implied, but the spec doesn't pick between full-suite-against-both or a dedicated store-contract suite.
- **Missing failure modes.** Paths through the system where error handling, rollback, or degradation behavior is not specified.
- **Implementation leakage.** Content in the spec that belongs in code — function bodies, full SQL statement bodies, rendered config blobs, pinned versions, internal-only log text, test bodies, directory tree listings. Signatures, type definitions, schema, and externally-visible text (user-facing errors, API codes, alert-matched log lines) stay; bodies and realized content come out.

Prioritize findings as you present them:

- **P0** — blocks planning or build (drift from code, implementation-blocking ambiguity, unresolved soft flag the planner must know).
- **P1** — forces a build-time decision the engineer shouldn't be making alone.
- **P2** — polish, clarity, small inconsistency.

Priorities are a triage aid for a long list, not ceremony. Skip them on short reviews.

## Surfacing findings

Generate the full findings list and present it to the user, then immediately start working through the first finding. Do not pause to ask whether to dismiss, reorder, or add items — the user can redirect at any point as items come up, but the default is forward motion. Showing the list gives shape; asking permission to proceed just adds friction.

### Every finding must cite evidence

Before putting a finding on the list, attach its evidence:

- For **Gaps**: name the topic and confirm you re-scanned the spec for it. State where you looked (which section headings you read) and that it was not addressed. Do not flag a gap you have not actively searched for.
- For **Inconsistencies**, **Ambiguities**, **Drift**, **Implementation leakage**: quote the problematic passage (or passages, for contradictions), so the user can see exactly what you are pointing at.
- For **Stale soft flags**: quote the `[NEEDS PRD CLARIFICATION: ...]` line verbatim, *and* quote or cite the passage where the question has since been answered.
- For **Unresolved soft flags**: quote the `[NEEDS PRD CLARIFICATION: ...]` line verbatim, and state that you checked the spec and the PRD for an answer and did not find one.

If you cannot produce the evidence, drop the finding. A vague suspicion that something *might* be missing is not a finding — it is a prompt to go re-read the spec.

When presenting the list to the user, include the evidence with each finding. "Testing section is absent — I scanned Components, Data Model, API Design, and Error Handling and found no surface identification" is a real finding. "Testing might be underspecified" is not.

### Working the list

For each finding, present the options as a numbered list with one option explicitly flagged as recommended, followed by your reasoning, and an invitation for the user to pick one or propose another. Use this format:

```
**Option 1** (recommended) — ...
**Option 2** — ...
**Option 3** — ...

I recommend Option 1 because <reason>. Pick one or propose another.
```

Numbered options let the user respond "go with 2" without re-typing. The inline `(recommended)` tag and the rationale line below make the pick explicit. Two options are fine when there are only two real choices; a single "recommended" option with no alternatives is fine when the decision is clear. What is never fine is a bare list without a pick — the user came to you for a recommendation.

Work through findings in order, one at a time. Cluster a finding with the next one only when the two are so tightly coupled that resolving one alone would force re-opening the other. Resolve each before moving on.

Keep a running log of decisions made during the review. Show it on request, and whenever you finish a finding category before moving to the next.

If the user pushes back with "that's already in the spec," stop and re-read the section they point to before continuing. Treat a user correction as a signal that the coverage pass missed something — adjust the map before generating more findings.

## Writing the updated document

Write the updated spec to the same path — do not create a new file or change the feature slug unless the user asks.

Incorporate resolved findings. Preserve unchanged sections and their ordering — a review should not reshuffle the document. Remove resolved soft flags; replace each with the actual decision reached. Do not add sections for findings the user dismissed or deferred.

Err toward shorter. Resolving a finding does not require adding a section — sometimes one sentence is enough. A review should sharpen the spec, not inflate it.

Write for an engineer who was not in the review discussion. No deictic references. "We considered X but chose Y because Z" is fine and useful; bare references to the review conversation are not.

## At the end of the review

1. Confirm the updated file was written with its path.
2. If the review resolved or corrected any domain terms, write them to the appropriate `docs/CONTEXT.md` in a single pass alongside the spec update. If the file does not exist, create it in the `docs/` directory closest to the code whose domain it describes.
3. If any unresolved soft flags remain, or if resolved findings have implications that make the PRD inconsistent or out of date, offer to hand the relevant items off to `/prd-review`. See **Handoff to `/prd-review`** below.
4. Review the running decision log. For each decision — apply this checklist. Only offer an ADR if all three are true:
   - **Hard to reverse** — the cost of changing your mind later is meaningful
   - **Surprising without context** — a future reader will wonder "why did they do it this way?"
   - **Result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

   If any is missing, skip the ADR; the decision already lives in the spec. Decisions made during a spec review — resolving soft flags, settling ambiguous component ownership, choosing between implementation approaches — are strong ADR candidates when they pass the checklist.
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
