---
name: goal-from-spec
description: Emit a /goal command pointed at a feature directory containing a blueprint.md (or the legacy prd.md + tech-spec.md). Use whenever the user wants to implement, build, ship, or run a feature whose design lives in a docs/features/<name>/ directory (or similar). Do NOT use for design discussions or one-shot edits.
---

# Goal from Spec

Emit a `/goal` command pointed at a feature directory. The user pastes it to launch — Claude Code's slash commands are parsed from user input, not from model output.

## What to do

1. Identify the feature directory path. Ask once if ambiguous; otherwise read it from the conversation.
2. Check which design docs are present, and pick the matching template:
   - **Prefer `blueprint.md`** — the current single-document design artifact (product *what* + technical *how* in one file). Use the **Blueprint template**.
   - **Fall back to the legacy `prd.md` + `tech-spec.md`** (+ optional `user-stories.md`) for older feature directories that predate the Blueprint. Use the **Legacy template**.
3. Emit the command using the matching template below, in a fenced code block, with no commentary after.

## Blueprint template

```
/goal Implement the feature specified in <feature-dir>/. Follow <feature-dir>/blueprint.md as the source of truth for both WHAT correct means and HOW to build it, matching the existing codebase's patterns, conventions, and terminology so the new code fits naturally rather than inventing divergent structure. The feature is complete only when every acceptance criterion in the Blueprint is satisfied AND demonstrably verified: all new and existing tests pass, the build is green, and lint is clean. Treat the Blueprint as the source of truth for correctness — if the implementation and the Blueprint disagree, the implementation is wrong. For each acceptance criterion, there must be a passing test that exercises it through the system's surface — its public interface (HTTP endpoints, CLI entry points, exported functions), never internal functions; use the surface-testing skill to guide the testing strategy. For every invariant or illegal-state constraint stated in the Blueprint, there must also be a surface test that attempts to violate it and verifies the system rejects the operation. Derive every test from the Blueprint, never from your own implementation; for each, confirm it fails against the unimplemented behavior before writing the code that makes it pass. Do not mark complete until that coverage exists and passes. If the implementation is large or complex — many files, many independent components, or many acceptance criteria that can be tackled in parallel — use a workflow to plan the orchestration and run subagents in parallel; each subagent prompt that writes tests must carry the same surface-testing instruction.
```

## Legacy template

Use only when there is no `blueprint.md` and the directory still carries the older `prd.md` / `tech-spec.md` split.

```
/goal Implement the feature specified in <feature-dir>/. Follow <feature-dir>/tech-spec.md as the implementation guide for HOW to build it, matching the existing codebase's patterns, conventions, and terminology so the new code fits naturally rather than inventing divergent structure. The feature is complete only when every acceptance criterion in <feature-dir>/prd.md is satisfied AND demonstrably verified: all new and existing tests pass, the build is green, and lint is clean. Treat the PRD as the source of truth for correctness — if the implementation and the PRD disagree, the implementation is wrong. For each PRD acceptance criterion, there must be a passing test that exercises it through the system's surface — its public interface (HTTP endpoints, CLI entry points, exported functions), never internal functions; use the surface-testing skill to guide the testing strategy. For every invariant or illegal-state constraint stated in the PRD or tech-spec, there must also be a surface test that attempts to violate it and verifies the system rejects the operation. Derive every test from the PRD/tech-spec, never from your own implementation; for each, confirm it fails against the unimplemented behavior before writing the code that makes it pass. Do not mark complete until that coverage exists and passes. If the implementation is large or complex — many files, many independent components, or many acceptance criteria that can be tackled in parallel — use a workflow to plan the orchestration and run subagents in parallel; each subagent prompt that writes tests must carry the same surface-testing instruction.
```

- The Blueprint already folds in user stories — there is no separate `user-stories.md` in the Blueprint flow. For the **Legacy template** only: if `user-stories.md` is present, append `Each user story in <feature-dir>/user-stories.md must also be satisfied with a passing test.`, and if `tech-spec.md` is absent, drop the second sentence ("Follow … HOW to build it.").
- The word "workflow" in the template is load-bearing — it triggers Claude Code's Dynamic Workflows. Don't remove or rephrase it.
- "surface" and "surface-testing skill" are also load-bearing — they trigger the surface-testing skill and keep tests on the public interface. Keep them in the template, and keep the clause requiring subagent prompts to repeat the instruction so parallel workers inherit it rather than relying on ambient CLAUDE.md.
