---
name: implement-plan-all
description: Implement all phases of a technical plan sequentially using subagents
---

# Implement All Phases of a Plan

You are tasked with orchestrating the complete implementation of a multi-phase technical plan by coordinating subagents to implement each phase sequentially.

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - Parameters appear as text after the command (e.g., `/implement-plan-all plans/my-plan.md`)
   - If a file path was provided, skip the default message
   - Immediately read the plan file FULLY
   - Begin the orchestration process

2. **If no parameters provided**, respond with:
```
I'll help you implement all phases of a plan sequentially. Please provide the name of the file which
contains the implementation plan details and I'll coordinate the phased implementation.

Tip: You can also invoke this command with a plan file directly: `/implement-plan-all plans/my-plan.md`
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

## Launching Phase Implementer

Use the Task tool with subagent_type "phase-implementer":

```
Implement Phase [N]: [PHASE_NAME] from the plan at [PLAN_PATH].

Read the plan at [PLAN_PATH] and implement ONLY Phase [N].
```

That's it! The phase-implementer subagent knows what to do. No need to repeat guidelines or instructions.

## Verification After Each Phase

The phase-implementer subagent handles all verification (tests, builds, etc.), so you should:

1. **Review the subagent's completion report**: Check that it says tests passed
2. **Verify key files exist**: Quick check that expected files were created

If the subagent reports issues or failures:
- Review what it tried
- Check if it's a plan mismatch vs implementation bug
- Attempt to resolve if straightforward
- Ask user for guidance if stuck

The subagent should have already run tests and verified the phase works. Your job is mainly to confirm and commit.

## Git Commits

After successfully verifying each phase, create a descriptive commit:

```bash
git add .
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

Use the TodoWrite tool to track overall progress:
- Create todos for each phase
- Mark phases as in_progress when launching subagent
- Mark phases as completed after successful verification and commit
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

## Success Criteria

All phases are complete when:
- All phase subagents have finished successfully
- All tests pass for all phases
- All phases are committed to git
- The complete implementation compiles/builds successfully
- You report: "All [N] phases implemented successfully"

Remember: Your job is orchestration, not implementation. Let the subagents do the detailed work while you ensure proper sequencing, verification, and commits.
