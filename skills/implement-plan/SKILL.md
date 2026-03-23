---
<<<<<<<< HEAD:commands/plan-implement.md
name: plan-implement
description: Implement all phases of a technical plan sequentially using subagents
========
name: implement-plan
description: Implement all phases of a technical plan sequentially using subagents. Use when user wants to execute/implement a plan file or asks to implement phases.
argument-hint: "[plan-file-path]"
allowed-tools: Read, Edit, Glob, Grep, Bash, Agent, TaskCreate, TaskUpdate, TaskList
>>>>>>>> 01e1cec (Converted some commands to skills):skills/implement-plan/SKILL.md
---

# Implement All Phases of a Plan

You are tasked with orchestrating the complete implementation of a multi-phase technical plan by coordinating subagents to implement each phase sequentially.

The plan file path is: `$ARGUMENTS`

## Initial Response

<<<<<<<< HEAD:commands/plan-implement.md
When this command is invoked:

1. **Check if parameters were provided**:
   - Parameters appear as text after the command (e.g., `/plan-implement plans/my-plan.md`)
   - If a file path was provided, skip the default message
   - Immediately read the plan file FULLY
   - Begin the orchestration process

2. **If no parameters provided**, respond with:
========
- If `$ARGUMENTS` is provided, immediately read the plan file FULLY and begin the orchestration process.
- If `$ARGUMENTS` is empty, respond with:
>>>>>>>> 01e1cec (Converted some commands to skills):skills/implement-plan/SKILL.md
```
I'll help you implement all phases of a plan sequentially. Please provide the name of the file which
contains the implementation plan details and I'll coordinate the phased implementation.

Tip: You can also invoke this command with a plan file directly: `/plan-implement plans/my-plan.md`
```

## Orchestration Approach

Your role is to orchestrate, not implement directly. For each phase:

1. **Launch a phase-implementer subagent** using the Task tool (subagent_type: "phase-implementer")
2. **Pass minimal instructions**: Just the plan path and phase number
3. **Wait for completion**: The subagent will implement, test, and report results
4. **Verify the subagent's report**: Check that tests passed and phase is complete
5. **Commit the changes** with a descriptive commit message
6. **Move to the next phase** (do NOT run multiple subagents simultaneously)

The phase-implementer subagent has built-in knowledge of:
- How to read and understand plans
- Code and testing guidelines from CLAUDE.md
- Verification steps to run
- When to stop and ask for guidance
- NOT to commit (you handle commits)
- NOT to include Co-Authored or emoji in any messages
- NOT to create temporary test programs (write functional tests instead)
- NOT to leave build artifacts in the repository

## Resuming Work

Before starting implementation, check if previous phases have already been completed:

1. **Check plan file for checkboxes**: Scan for `[x]` markers indicating completed phases
2. **Check git log**: Look for "Implement Phase N:" commit messages to identify completed work
3. **Skip completed phases**: Start from the first incomplete phase
4. **Only re-verify previous work** if something seems off (e.g., test failures referencing completed phase code)

If resuming, briefly note which phases were already completed before continuing.

## Launching Phase Implementer

Use the Task tool with subagent_type "phase-implementer":

For **Phase 1** (no prior context):
```
Implement Phase 1: [PHASE_NAME] from the plan at [PLAN_PATH].

Read the plan at [PLAN_PATH] and implement ONLY Phase 1.
```

For **Phase 2+** (include previous phase summary):
```
Implement Phase [N]: [PHASE_NAME] from the plan at [PLAN_PATH].

Read the plan at [PLAN_PATH] and implement ONLY Phase [N].

Previous phase summary: [Brief summary from the previous phase-implementer's completion report, including key files modified and any decisions made]
```

The previous phase summary gives the subagent awareness of what was just done, reducing redundant exploration. Keep it to 2-3 sentences.

The phase-implementer subagent knows what to do. No need to repeat guidelines or instructions.

## Verification After Each Phase

The phase-implementer subagent handles initial verification, but you should independently confirm:

1. **Review the subagent's completion report**: Check that it says tests passed
2. **Check scope of changes**: Run `git diff --stat` to see what changed and confirm it aligns with expectations
3. **Run validation commands independently**: Run the plan's validation commands yourself — don't just trust the subagent's report
4. **Verify files exist**: Confirm files mentioned in the subagent's report actually exist

If the subagent reports issues or failures:
- Review what it tried
- Check if it's a plan mismatch vs implementation bug
- Attempt to resolve if straightforward
- Ask user for guidance if stuck

The subagent should have already run tests and verified the phase works. Your independent verification is a safety net before committing.

After committing a phase, update the plan file's checkboxes to `[x]` for all completed items using Edit. This creates persistent state that survives session boundaries and enables resume capability.

## Git Commits

After successfully verifying each phase:

1. **Review changes**: Run `git status` to see all modified/created files
2. **Stage specific files**: Stage only the files listed in the subagent's "Files created/modified" report — do NOT use `git add .`
3. **Review staged diff**: Run `git diff --cached` to confirm what will be committed
4. **Never stage** files that look like secrets (`.env`, credentials), build artifacts, or editor config files
5. **Commit** with a descriptive message:

```bash
git commit -m "Implement Phase [N]: [Phase Name]

- [Key change 1]
- [Key change 2]
- [Key change 3]"
```

Extract the key changes from the phase-implementer's completion report.

**IMPORTANT**:
- Do NOT include "Co-Authored-By: Claude <noreply@anthropic.com>"
- Do NOT include "🤖 Generated with [Claude Code](...)"
- Include what changed, not just the phase name

## Sequential Execution

**CRITICAL**: Do NOT run multiple subagents simultaneously. The workflow MUST be:

1. Launch subagent for Phase 1
2. Wait for completion
3. Verify Phase 1
4. Commit Phase 1
5. Launch subagent for Phase 2
6. Wait for completion
7. Verify Phase 2
8. Commit Phase 2
9. Continue until all phases complete...

## Progress Tracking

Use TaskCreate, TaskUpdate, and TaskList to track overall progress:
- At the start, create one task per phase using TaskCreate (e.g., "Implement Phase 1: [Name]")
- Mark a task as `in_progress` using TaskUpdate when launching its subagent
- Mark a task as `completed` using TaskUpdate after successful verification and commit
- Use TaskList to review progress before starting the next phase
- This gives the user visibility into which phase is currently being implemented

## Handling Issues

If a subagent encounters issues:
- Review the subagent's output carefully
- Check if it's a plan mismatch vs implementation bug
- Attempt to resolve minor issues yourself
- For major blockers, stop and ask the user:
  ```
  Issue in Phase [N]:
  Problem: [description]
  Subagent output: [relevant details]

  Should I:
  1. Attempt to fix and retry Phase [N]
  2. Skip Phase [N] and continue
  3. Stop and wait for guidance
  ```

## References and Dependencies

The phase-implementer subagent already knows:
- External project references are for context only
- All necessary information is in the plan itself
- Not to read external projects unless explicitly required

## Final Linting

After all phases are committed, run linting as the final verification step:

1. **Detect linting approach** (in order of preference):
   - Check for Makefile targets: `make lint`, `make check`, or `make verify`
   - Detect from project files: `golangci-lint run` (Go), `npx eslint .` (JS/TS), `ruff check .` (Python), `cargo clippy` (Rust)
   - If no linter is detected, skip this step
2. **Fix any issues**: If linting fails, fix the issues directly (do not spawn a subagent)
3. **Commit lint fixes**: If changes were made, stage the specific fixed files and commit:
   ```bash
   git commit -m "Fix linting issues"
   ```

Only proceed to report success after linting passes.

## Success Criteria

All phases are complete when:
- All phase subagents have finished successfully
- All tests pass for all phases
- All phases are committed to git
- The complete implementation compiles/builds successfully
- Linting passes with no errors
- You report: "All [N] phases implemented successfully"

Remember: Your job is orchestration, not implementation. Let the subagents do the detailed work while you ensure proper sequencing, verification, and commits.
