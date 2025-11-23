---
name: implement-plan
description: Implement technical plans with verification
---

# Implement A Plan

You are tasked with implementing an approved technical plan. These plans contain phases with specific changes and success criteria.

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - If a file path was provided as a parameter, skip the default message
   - Immediately read any provided files FULLY
   - Begin the implementation process

2. **If no parameters provided**, respond with:
```
I'll help you implement a plan, please provide the name of the file which
contains the implementation plan details and I'll read the file and begin implementation

Tip: You can also invoke this command with a ticket file directly: `/implement-plan-v2 plan.md`
```

## Getting Started

When given a plan path:
- Read the plan completely and check for any existing checkmarks (- [x] = completed, - [ ] = uncompleted)
- **Read files fully** - never use limit/offset parameters, you need complete context
- Check if phases have dependencies and ensure prerequisites are complete before starting
- Think deeply about how the pieces fit together
- Create a todo list to track your progress
- Start implementing if you understand what needs to be done

## Using Specialized Agents

Claude Code provides specialized agents that can significantly improve implementation efficiency. Use these proactively when appropriate:

### Explore Agent
Use when you need to understand unfamiliar parts of the codebase:
- Understanding the overall codebase structure before starting
- Finding where specific functionality is implemented
- Discovering how features are organized across multiple files
- Example: "Use the Explore agent to understand how authentication is currently implemented"

### codebase-locator Agent
Use when the plan mentions specific files, components, or features you need to find:
- Locating files or directories referenced in the plan
- Finding components that need to be modified
- Discovering related files that may need updates
- Example: "Use codebase-locator to find all files related to the user profile feature"

### code-review-critical Agent
Use when appropriate to review changes for critical issues:
- After implementing complex logic or algorithms
- When working with security-sensitive code (auth, permissions, data validation)
- Before marking phases complete if changes are substantial
- When you want to verify there are no bugs, performance issues, or security vulnerabilities
- This is optional and should be used based on your judgment of risk/complexity

### claude-enforcement Agent (Go projects only)
If working with Go code and a CLAUDE.md file exists in the repository:
- Use after implementing Go code to verify it follows project guidelines
- Checks for proper patterns, struct field ordering, naming conventions, etc.
- Only applicable to Go codebases with established CLAUDE.md standards

**Important**: These agents are tools to help you work efficiently. Use them when they add value, but don't feel obligated to use them for straightforward tasks where you already have the context you need.

## Implementation Philosophy

Plans are carefully designed, but reality can be messy. Your job is to:
- Follow the plan's intent while adapting to what you find
- Implement each phase fully before moving to the next
- Verify your work makes sense in the broader codebase context
- Update checkboxes in the plan as you complete sections

When things don't match the plan exactly, think about why and communicate clearly. The plan is your guide, but your judgment matters too.

If you encounter a mismatch:
- STOP and think deeply about why the plan can't be followed
- Present the issue clearly:
  ```
  Issue in Phase [N]:
  Expected: [what the plan says]
  Found: [actual situation]
  Why this matters: [explanation]

  How should I proceed?
  ```

## Verification Approach

After implementing a phase:
- Run the success criteria checks specified in the plan (commonly `make test`, but always defer to what the plan specifies)
- Fix any issues before proceeding. If automated checks fail repeatedly after multiple fix attempts, document the failures and ask the user for guidance
- Update your progress in both the plan and your todos
- Update checkboxes incrementally in the plan file as you complete individual items (not just at phase boundaries) using Edit
- **Pause for human verification**: After completing all automated verification for a phase, pause and inform the human that the phase is ready for manual testing. Use this format:
  ```
  Phase [N] Complete - Ready for Manual Verification

  Automated verification passed:
  - [List automated checks that passed]

  Let me know when manual testing is complete so I can proceed to Phase [N+1].
  ```

If the user explicitly requests multiple phases (e.g., "implement phases 1-3" or "complete all remaining phases"), skip the pause between phases and only pause at the end. Otherwise, assume you are implementing one phase at a time with manual verification after each.

Do not check off items in the manual testing steps until confirmed by the user.


## If You Get Stuck

When something isn't working as expected:
- First, make sure you've read and understood all the relevant code
- If you need to explore unfamiliar parts of the codebase, use the Explore agent rather than manual searches
- Consider if the codebase has evolved since the plan was written
- Present the mismatch clearly and ask for guidance

Use specialized agents (Explore, codebase-locator) when you need to understand or find code. Use the Task tool sparingly for other purposes - mainly for targeted debugging when agents aren't the right fit.

## Resuming Work

If the plan has existing checkmarks:
- Trust that completed work is done
- Pick up from the first unchecked item
- Verify previous work only if something seems off

Remember: You're implementing a solution, not just checking boxes. Keep the end goal in mind and maintain forward momentum.
