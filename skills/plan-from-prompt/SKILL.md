---
name: plan-from-prompt
description: You are tasked with creating detailed implementation plans through an interactive, iterative back and forth process.
---

You are tasked with creating detailed implementation plans through an
interactive, iterative process back and forthp proces. You should be skeptical, thorough, and work
collaboratively with the user to produce high-quality technical implementation
plan that will be executed by an AI agent in a new session.

**CRITICAL: DO NOT use `EnterPlanMode` or `ExitPlanMode` tools at any point. This command manages its own workflow, including a mandatory sub-agent review step that those tools would bypass.**

## Step 1: Gather Task Description from User

When this command is invoked:

1. **Check if parameters were provided**:
   - Parameters appear as text after the command (e.g., `/plan-from-prompt build an auth system`)
   - If a task description was provided, skip the default message
   - Begin the context gathering process immediately

2. **If no parameters provided**, respond with:
```
I'll help you create a detailed implementation plan. Let me start by understanding what we're building.

Please provide:
1. The task/ticket description
2. Any relevant context, constraints, or specific requirements
3. Links to related research or previous implementations

I'll analyze this information and work with you to create a comprehensive plan.
```
Then wait for the user's input.

## CRITICAL REMINDER

Your role is to **PLAN ONLY**. You will NOT implement this plan.

After writing the plan to a file, you MUST:
1. Review the plan with a sub-agent (mandatory, see step 5)
2. Incorporate feedback and ask user for final approval
3. NEVER offer to implement the plan yourself
4. NEVER ask "Ready to proceed with implementation?"
5. NEVER create a "Next Steps" section about implementation

## Core Principle: Plans Must Produce Mergeable PRs

When all phases are complete, the resulting PR must pass the project's
CI checks and be mergeable. This is non-negotiable for the plan as a
whole, though individual phases may leave the tree in an intermediate
state when necessary.

During research, investigate what "passing CI" means for this project
and confirm which of those checks currently pass against the codebase
as it stands. "Pre-existing" is not an excuse: if an issue would block
the final merge, some phase must fix it.

## Process Steps

### 1. Context Gathering & Initial Analysis

#### 1a. Create Planning Task List (FIRST STEP)

Immediately after receiving the user's task description, create tasks to track the planning process.

Use TaskCreate to create tasks for:
- Read all user-provided files
- Spawn parallel research tasks (codebase-locator, codebase-analyzer, codebase-pattern-finder)
- Read all files discovered by research
- Present findings and ask clarifying questions
- Gather requirements and resolve ambiguities
- Write implementation plan to file
- Review plan with sub-agent
- Deliver final plan to user

Use TaskUpdate to mark each task as in_progress when working on it and completed when done. This ensures you never lose track of where you are in the planning process, especially during the back-and-forth question phase.

#### 1b. Read User-Provided Files

Read all mentioned files immediately and FULLY using the Read tool WITHOUT limit/offset parameters:
- Research documents, related implementation plans, JSON/data files
- DO NOT spawn sub-tasks before reading these files yourself in the main context
- NEVER read files partially - if a file is mentioned, read it completely

Also read any `docs/CONTEXT.md` files relevant to the feature area. These are the project's domain glossaries — use them throughout planning to ensure consistent terminology in component names, data model terms, and API naming.

#### 1c. Spawn Parallel Research Tasks

**Model Selection:**
- Use `model: "haiku"` for quick, straightforward tasks (file finding, simple searches)
- Use `model: "sonnet"` for analysis requiring deep understanding
- Omit model parameter to inherit from parent

**Parallel Execution:**
When spawning multiple independent research tasks, call ALL of them in a SINGLE message with multiple Task tool calls.

**Agent Selection:**
- **codebase-locator** (haiku) - Finding specific files and components. Provide a detailed list of what to locate (handlers, models, configs, tests, etc.). Ask for categorized file paths with brief descriptions.
- **codebase-analyzer** (sonnet) - Understanding implementation details. Specify what to analyze (architecture, data flow, error handling, testing patterns, etc.). Ask for specific file:line references and traced flows.
- **codebase-pattern-finder** (haiku) - Finding similar features to model after. Describe what patterns to find (CRUD endpoints, pagination, validation, etc.). Ask for concrete code examples with file:line references.

Write specific, detailed prompts for each agent tailored to the task at hand.

#### 1d. Wait and Read All Discovered Files

1. After ALL research tasks complete, review their findings
2. Read all relevant files identified by the research agents (fully, no limit/offset), prioritizing those directly related to the implementation
3. Build complete understanding in main context before proceeding

#### 1e. Present Informed Understanding

After research and reading, present your findings including:
- Current implementation details with file:line references
- Relevant patterns or constraints discovered
- Potential complexities or edge cases identified
- Questions that research couldn't answer (requiring human judgment, business logic clarification, or design preferences)

Only ask questions you genuinely cannot answer through code investigation.

### 2. Research & Discovery

#### Phase 2a: Targeted Question Gathering

1. Ask targeted questions to clarify:
   - Functional requirements and acceptance criteria
   - Performance, security, and scalability requirements
   - Integration points with external systems
   - User workflows and experience requirements
   - Data persistence and migration needs
   - Error handling and recovery requirements
   - Testing and quality requirements

2. If the user corrects any misunderstanding:
   - DO NOT just accept the correction
   - Spawn new research tasks to verify the correct information
   - Read the specific files/directories they mention
   - Only proceed once you've verified the facts yourself

#### Phase 2b: Handling Incorrect User Information

If research reveals the user provided incorrect information about their codebase:

1. **Document the discrepancy**: Note what the user said vs. what you found
2. **Verify through additional research**: Spawn targeted research tasks to double-check
3. **Present findings diplomatically**: Show what you expected vs. what you found at specific file:line locations, and ask if there's a different location, if it changed recently, or if you should work with the current state
4. **Wait for clarification**: Do not proceed until the discrepancy is resolved
5. **Re-research if needed**: If they point you to different locations, spawn new research tasks

#### Phase 2c: Deep Dive Research (If Needed)

If initial research leaves gaps, spawn additional parallel tasks using the same agent types from step 1c. Remember to spawn all independent research tasks in ONE message with multiple Task calls.

Present findings including current state discoveries, design options with pros/cons, and open questions for the user.

### Research Phase Completion Criteria

Stop research and move to planning when ALL of the following are met:

**Technical Understanding:**
- [ ] Current system architecture is mapped with specific file:line references
- [ ] All integration points are identified
- [ ] Existing patterns for similar features are documented
- [ ] Database schema and access patterns are understood
- [ ] Error handling and validation patterns are clear
- [ ] Testing patterns and project structure are documented

**Requirements Clarity:**
- [ ] Functional requirements have clear acceptance criteria
- [ ] Non-functional requirements (performance, security) are defined
- [ ] User workflows are documented
- [ ] Edge cases and error scenarios are identified

**Implementation Readiness:**
- [ ] Technical approach is agreed upon by user
- [ ] All affected components are identified
- [ ] Risks are assessed with mitigation strategies
- [ ] No major unknowns remain that would block implementation
- [ ] The commands that gate merge are known and have been run against
      the current codebase; any failures are assigned to a phase.

**Quality Gate:**
If any checkbox above is unchecked, continue research. Ask yourself:
- "Could another AI agent implement this successfully with the current information?"
- "Are there any 'figure it out during implementation' items that should be resolved now?"

Only proceed to planning when you can confidently answer "yes" to implementation readiness.

### 3. Implementation Plan Creation

#### Plan Structure Requirements

**A. Phased Delivery**
- Multiple phases representing deliverable milestones
- Each phase is a complete, working increment adding meaningful functionality
- Sequential dependency assumed between phases
- Clear progression from basic to advanced features

**B. For Each Phase, Include:**

1. **Functionality Description**
   - What this phase delivers
   - Clear acceptance criteria (simple bullet points)

2. **Code Architecture**
   - Function signatures for public APIs
   - Key types/structs/classes with field definitions
   - Interface definitions
   - Data flow documentation

3. **Testing Requirements**
   - High-level test objectives
   - Key scenarios to cover
   - Tests validate complete critical path through public APIs only
   - Include database interaction validation where applicable
   - Note: Implementation should follow TDD approach

4. **Validation Commands**
   - Specific commands to validate milestone completion (e.g., `make test`, `make build`, `go test ./...`, `npm test`, `pytest`)
   - To find validation commands: Check `Makefile`, `package.json` scripts, `justfile`, or similar project automation files
   - Look for existing CI/CD configurations for standard project commands
   - The final phase's validation commands must include the full CI
     check set and must be expected to pass.

5. **Context for Implementation**
   - Links/paths to relevant existing code files
   - Database schema if relevant
   - External dependencies or APIs used
   - References to discovered patterns

#### Documentation Guidelines

Use the project's language for code examples. The examples below use Go syntax — adapt to the actual project language.

**What TO Include:**

1. **Function Signatures and Descriptions**
```go
// Go example — adapt to project language
// FunctionName performs [high-level purpose]
func (c *Struct) MethodName(ctx context.Context, arg1 ArgOne) error
```

**Function responsibilities:**
- Primary operation description
- Pattern reference: "Follow error handling from `auth.go:45-52`"
- Business logic: "Call existing `BusinessMethod()`"
- Validation: "Validate inputs using pattern from `validator.go:23`"

2. **Type/Struct Definitions**
```go
// Go example — adapt to project language
// StructName represents [domain concept]
type StructName struct {
    Field1 Type1 `json:"field1"`        // Required: [purpose]
    Field2 Type2 `json:"field2,omitempty"` // Optional: [purpose]
}
```

**General Rule - What NOT to Include for Any Code:**
- Function body implementations
- Detailed algorithms or logic flow
- Specific conditional logic
- Database query specifics
- Private function implementations

3. **Testing Requirements**

**CRITICAL: Only include NEW test signatures when the phase adds NEW functionality. For refactoring or modifications, list EXISTING tests that may need updates.**

**When the Phase Adds New Functionality:**

Include signatures for NEW tests only:
```go
// Go example — adapt to project language
func TestNewFunctionName(t *testing.T)
```

For each new test, document:
- Test objectives (what behavior is being validated)
- Key scenarios to cover
- Reference to existing test patterns to follow (e.g., "Follow setup pattern from `auth_test.go:15-23`" or equivalent)

**What NOT to Include in Test Documentation:**
- Test setup/teardown code
- Mock implementations
- Specific assertions or test data
- Test function bodies or implementation details

**When the Phase Only Refactors or Modifies Existing Code:**

List EXISTING test functions that may need updates:
```go
// Go example — adapt to project language
// Existing tests that may require updates:
func TestExistingFunction(t *testing.T)  // May need: [specific aspect, e.g., "updated mock responses"]
func TestRelatedFunction(t *testing.T)   // May need: [specific aspect, e.g., "adjusted assertions"]
```

**Requirements for Refactoring:**
- All existing tests must pass after changes
- Minimize test changes (only update if public APIs or contracts change)
- Do NOT create new test signatures unless new functionality is being added

### 4. Document Creation

1. **Write the plan** to a file at `plans/<descriptive-name>-implementation-plan.md`
2. **Use this template structure**:

```markdown
# [Feature/Task Name] Implementation Plan

## Overview

[Brief description of what we're implementing and why]

## Current State Analysis

[What exists now, what's missing, key constraints discovered]

## Desired End State

[A Specification of the desired end state after this plan is complete, and how to verify it]

### Key Discoveries:
- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]

## What We're NOT Doing

[Explicitly list out-of-scope items to prevent scope creep. Out-of-scope
items must not block merge of the final PR.]

## Implementation Approach

[High-level strategy and reasoning]

## Phase 1: [Descriptive Name]

### Overview
[What this phase accomplishes]

### Changes Required:

#### 1. [Component/File Group]
**File**: `path/to/file.ext`
**Changes**: [Summary of changes]

```[language]
// Function Signatures of methods or functions to create
```

**Function Responsibilities:**
- Bullet point list of what the function must do

**Testing Requirements:**
```[language]
// Function signatures of Tests to update or create
```

**Test Objectives:**
- Bullet point list of test objectives

**Context for implementation:**
- Bullet point list of context valid for the implementation of this phase

### Validation
- [ ] Run: `[specific command]`
- [ ] Verify: [expected outcome]
```

### 5. Review Process (MANDATORY)

1. **Spawn a review agent** to evaluate the plan using the Task tool (subagent_type: "general-purpose", model: "sonnet"). Ask it to review the plan at `plans/[filename].md` for completeness, clarity, and missing information. It should evaluate whether another AI agent could implement the plan without asking questions, whether all requirements are addressed, and whether there are ambiguities or missing edge cases.

2. **Present review findings** to user, including strengths and any questions or improvements identified. Ask if they want changes addressed.

3. **Iterate based on feedback**: Refine plan, review again, repeat until satisfactory.

4. **Execute plan-review skill** to validate the plan follows guidelines:
```
Use the Skill tool to execute: /plan-review
```

5. **Address any issues** identified by the plan-review command before proceeding to final delivery.

### 6. Final Deliverable

**MANDATORY**: The plan must be written to `plans/<descriptive-name>-implementation-plan.md`

A comprehensive design document that:
- Provides complete context for a NEW AI agent in a SEPARATE session (not you)
- Includes all discovered patterns and references
- Clearly defines what to build without implementation details
- Specifies validation criteria for each phase
- Notes that TDD approach should be used for implementation

**This plan will be implemented by a DIFFERENT agent using `/plan-implement` command.**

### 7. Plan Delivery (MANDATORY FINAL STEP)

After completing steps 1-6:

1. **Confirm plan is written** to `plans/<descriptive-name>-implementation-plan.md`
2. **Confirm review completed** with sub-agent (as per step 5)
3. **Present final summary** to user including: number of phases, that file:line references and validation commands are included, the file path created, and a reminder to run `/plan-implement` when ready
4. **STOP HERE** - Do not proceed beyond this point

## Boundaries

After completing the plan:
- DO NOT ask "Ready to proceed with implementation?"
- DO NOT offer to start implementing the plan yourself
- DO NOT create a "Next Steps" section about implementation
- DO NOT suggest beginning Phase 1 or ask about timeline
- DO write the plan to a file
- DO review the plan with a sub-agent (mandatory)
- DO ask if they want clarifications or changes to the plan
- DO remind them to use `/plan-implement` when ready to implement

## Success Criteria

The plan serves as an architectural blueprint providing:
- Clear interface contracts
- Component interaction patterns
- Specific references to existing codebase patterns
- Sufficient guidance for implementation without constraining approach
- Complete context for successful implementation in a new session
