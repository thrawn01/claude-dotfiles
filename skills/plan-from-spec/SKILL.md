---
name: plan-from-spec
description: Create a detailed implementation plan from an existing PRD or tech spec. The spec is treated as authoritative — requirements are not re-questioned, only implemented.
---

You are tasked with creating detailed implementation plans from an existing PRD
or tech spec. Your job is to figure out **how** to build what is already
specified — not to re-evaluate **what** to build. Treat the provided
spec/PRD as the source of truth for all product and functional decisions.

**CRITICAL: DO NOT use `EnterPlanMode` or `ExitPlanMode` tools at any point. This command manages its own workflow, including mandatory sub-agent review steps that those tools would bypass.**

## Step 1: Gather Spec from User

When this command is invoked:

1. **Check if parameters were provided**:
   - Parameters appear as text after the command (e.g., `/plan-from-spec docs/features/auth/tech-spec.md`)
   - If a spec path was provided, read it immediately and skip the prompt below
   - Begin the research process immediately after reading

2. **If no parameters provided**, respond with:
```
I'll create an implementation plan from your spec. Please provide:
1. Path(s) to the PRD and/or tech spec documents
2. Any additional context about constraints or codebase areas to focus on

I'll treat the spec as authoritative and plan the implementation without re-questioning its decisions.
```
Then wait for the user's input.

## CRITICAL REMINDER

Your role is to **PLAN ONLY**. You will NOT implement this plan.

The spec/PRD is authoritative. Do not:
- Ask whether the user is sure about a requirement the spec already answers
- Suggest alternatives to decisions the spec has already made
- Re-litigate product or functional choices

After writing the plan to a file, you MUST:
1. Review the plan with a general sub-agent (mandatory, see step 5)
2. Run the plan-review skill
3. Run the spec-coverage validation sub-agent (mandatory, see step 5)
4. Incorporate feedback and ask user for final approval
5. NEVER offer to implement the plan yourself
6. NEVER ask "Ready to proceed with implementation?"
7. NEVER create a "Next Steps" section about implementation

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

Immediately after receiving the spec path(s), create tasks to track the planning process.

Use TaskCreate to create tasks for:
- Read all spec/PRD documents provided
- Spawn parallel research tasks (codebase-locator, codebase-analyzer, codebase-pattern-finder)
- Read all files discovered by research
- Present findings and ask clarifying questions (technical gaps only)
- Write implementation plan to file
- Review plan with sub-agent
- Run plan-review skill
- Run spec-coverage validation sub-agent

Use TaskUpdate to mark each task as in_progress when working on it and completed when done.

#### 1b. Read All Spec Documents (FIRST PRIORITY)

Read every provided spec and PRD file immediately and FULLY using the Read tool WITHOUT limit/offset parameters. Also read any `docs/CONTEXT.md` files relevant to the feature area — these are the project's domain glossaries; use them throughout planning to ensure consistent terminology in component names, data model terms, and API naming. Do this before spawning any research tasks. Build a complete picture of:
- All stated requirements and acceptance criteria
- Decisions already made (treat these as final)
- Technical constraints or approaches the spec prescribes
- Open questions or explicit TBDs noted in the spec itself (these are legitimate to ask about)

#### 1c. Spawn Parallel Research Tasks

Research focuses on **how to implement** what the spec describes — not on discovering requirements.

**Model Selection:**
- Use `model: "haiku"` for quick, straightforward tasks (file finding, simple searches)
- Use `model: "sonnet"` for analysis requiring deep understanding
- Omit model parameter to inherit from parent

**Parallel Execution:**
When spawning multiple independent research tasks, call ALL of them in a SINGLE message with multiple Task tool calls.

**Agent Selection:**
- **codebase-locator** (haiku) - Finding the files the spec refers to. Provide a detailed list of components, handlers, models, configs, and tests to locate. Ask for categorized file paths with brief descriptions.
- **codebase-analyzer** (sonnet) - Understanding how existing code is structured so the new work fits naturally. Specify what to analyze (architecture, data flow, error handling, testing patterns). Ask for specific file:line references and traced flows.
- **codebase-pattern-finder** (haiku) - Finding existing patterns the implementation should follow. Describe what patterns to find (CRUD endpoints, pagination, validation, etc.). Ask for concrete code examples with file:line references.

Write specific, detailed prompts for each agent tailored to what the spec requires.

#### 1d. Wait and Read All Discovered Files

1. After ALL research tasks complete, review their findings
2. Read all relevant files identified by the research agents (fully, no limit/offset), prioritizing those directly related to the implementation
3. Build complete understanding of the codebase before proceeding

#### 1e. Present Informed Understanding

After research and reading, present your findings including:
- How the spec requirements map to the current codebase (with file:line references)
- Relevant patterns or constraints discovered
- Potential implementation complexities or edge cases
- **Only ask questions that the spec genuinely leaves unanswered** (see Phase 2a)

### 2. Technical Gap Resolution

#### Phase 2a: Technical Questions Only

The spec is authoritative on product and functional decisions. Only ask questions about:
- **Technical ambiguities**: The spec says *what* but leaves *how* genuinely unclear
- **Codebase conflicts**: The spec assumes something exists or works a certain way, but you found the codebase differs
- **Missing implementation details**: Things the spec intentionally deferred (library choice, retry strategy, specific API contract shapes)
- **Explicit TBDs**: Open questions the spec itself flagged as unresolved

Do NOT ask about:
- Whether a requirement is the right choice
- Whether the user considered alternative approaches to stated decisions
- Acceptance criteria or user workflows already defined in the spec
- Performance or security requirements already stated in the spec

#### Phase 2b: Reconciling Spec Intent with Codebase Reality

Sometimes the codebase doesn't match what the spec assumes. When this happens:

1. **Document the conflict**: What the spec expects vs. what you found (with file:line)
2. **Propose reconciliation**: How you plan to bridge the gap in the implementation plan
3. **Present to user**: "The spec assumes X, but I found Y at `file.go:42`. I plan to handle this by Z — does that match your intent?"
4. **Wait for confirmation** before proceeding if the conflict is significant
5. **Re-research if redirected**: If they point you elsewhere, spawn new research tasks

This is reconciliation, not verification — you are not questioning whether the spec is right, you are resolving how to implement it given reality.

#### Phase 2c: Deep Dive Research (If Needed)

If initial research leaves implementation gaps, spawn additional parallel tasks using the same agent types from step 1c. Remember to spawn all independent research tasks in ONE message with multiple Task calls.

### Research Phase Completion Criteria

Stop research and move to planning when ALL of the following are met:

**Technical Understanding:**
- [ ] Current system architecture is mapped with specific file:line references
- [ ] All integration points called out by the spec are identified in the codebase
- [ ] Existing patterns for similar features are documented
- [ ] Database schema and access patterns are understood
- [ ] Error handling and validation patterns are clear
- [ ] Testing patterns and project structure are documented
- [ ] The commands that gate merge are known and have been run against the current codebase; any failures are assigned to a phase

**Spec Readiness:**
- [ ] Every requirement in the spec maps to at least one identified codebase area or new component
- [ ] All spec-flagged TBDs and open questions are resolved
- [ ] Conflicts between spec and codebase are reconciled and confirmed with user
- [ ] No major implementation unknowns remain that would block planning

**Quality Gate:**
Ask yourself:
- "Could another AI agent implement this successfully with the current information?"
- "Are there any 'figure it out during implementation' items that should be resolved now?"
- "Does every spec requirement have a clear implementation home in my mental model?"

Only proceed to planning when you can answer "yes" to all three.

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
   - Which spec requirements this phase satisfies (reference spec section/requirement IDs if present)
   - Clear acceptance criteria (simple bullet points)

2. **Code Architecture**
   - Function signatures for public APIs
   - Key types/structs/classes with field definitions
   - Interface definitions
   - Data flow documentation

3. **Testing Requirements**
   - Follow the `surface-testing` skill — read it and apply its principles when writing testing sections
   - Tests must exercise the system through its public interface only (HTTP endpoints, CLI entry points, exported functions)
   - Code architecture must be designed for surface testability (the skill defines patterns for this)
   - Key scenarios to cover
   - Include database interaction validation where applicable
   - Note: Implementation should follow TDD approach

4. **Validation Commands**
   - Specific commands to validate milestone completion (e.g., `make test`, `make build`, `go test ./...`, `npm test`, `pytest`)
   - To find validation commands: Check `Makefile`, `package.json` scripts, `justfile`, or similar project automation files
   - Look for existing CI/CD configurations for standard project commands
   - The final phase's validation commands must include the full CI check set and must be expected to pass

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
    Field1 Type1 `json:"field1"`          // Required: [purpose]
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
- Reference to existing test patterns to follow (e.g., "Follow setup pattern from `auth_test.go:15-23`")

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
func TestExistingFunction(t *testing.T)  // May need: [specific aspect]
func TestRelatedFunction(t *testing.T)   // May need: [specific aspect]
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

## Source Documents
- [Link or path to PRD]
- [Link or path to tech spec]

## Overview

[Brief description of what we're implementing and why, grounded in the spec]

## Current State Analysis

[What exists now, what's missing, key constraints discovered in the codebase]

## Desired End State

[Specification of the desired end state after this plan is complete, and how to verify it — should directly reflect the spec's success criteria]

### Key Discoveries:
- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]
- [Spec conflict reconciled and how]

## What We're NOT Doing

[Explicitly list out-of-scope items. Reference the spec where it explicitly excludes things.
Out-of-scope items must not block merge of the final PR.]

## Implementation Approach

[High-level strategy and reasoning for how the spec requirements will be implemented]

## Phase 1: [Descriptive Name]

### Overview
[What this phase accomplishes and which spec requirements it satisfies]

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

### 5. Review Process (MANDATORY — THREE STEPS)

#### Step 5a: General Plan Review

Spawn a review agent using the Task tool (subagent_type: "general-purpose", model: "sonnet"). Ask it to review the plan at `plans/[filename].md` for completeness, clarity, and missing information. It should evaluate whether another AI agent could implement the plan without asking questions, whether all requirements are addressed, and whether there are ambiguities or missing edge cases.

Additionally, the agent must:

1. Read the `surface-testing` skill and validate that:
   - The plan's testing requirements only test through public interfaces (never internal/private functions)
   - The plan's code architecture is designed for surface testability (e.g., thin `main()` wrapping a testable `Run()`, servers with `Start()`/`Shutdown()`, observability APIs for async behavior)
   - Any behavior that cannot be tested via the public interface is either removed from the plan or exposed through an observability surface

2. Read the project's CLAUDE.md and verify any code examples, function signatures, or testing patterns in the plan are consistent with its guidelines

Present review findings to the user and ask if they want changes addressed. Iterate until satisfactory.

#### Step 5b: Plan-Review Skill

Execute the plan-review skill to validate the plan follows plan guidelines:
```
Use the Skill tool to execute: /plan-review
```

Address any issues identified before proceeding.

#### Step 5c: Spec-Coverage Validation (MANDATORY)

Spawn a spec-coverage validation agent using the Task tool (subagent_type: "general-purpose", model: "sonnet") with the following instructions:

```
Read the source spec/PRD at [spec path] and the implementation plan at plans/[filename].md.

Produce a traceability report with four sections:

1. UNCOVERED REQUIREMENTS: List every requirement, acceptance criterion, or stated behavior
   in the spec that has no corresponding phase or task in the plan. Be specific — quote
   the spec text and note which phase you expected to cover it.

2. UNTRACED PLAN ITEMS: List every phase or significant task in the plan that cannot be
   traced back to a requirement in the spec. These are potential scope creep items.

3. CONFLICTS: List any place where the plan's approach contradicts a decision or constraint
   stated in the spec.

4. CORRECTNESS TRACEABILITY: If the spec has a Correctness section (invariant preservation
   arguments, illegal state analysis, behavioral constraints), check:
   - Every invariant preservation argument in the spec maps to at least one test in the plan
     that attempts to violate the invariant through the surface and verifies the system
     rejects the operation.
   - Every behavioral constraint maps to at least one test that verifies enforcement.
   - Every component boundary with explicit preconditions/postconditions maps to at least
     one test that exercises the boundary contract.
   List any correctness arguments or constraints that have no corresponding test in the plan.
   If the spec has no Correctness section, report "N/A — spec has no correctness constraints."

Be thorough. A missed requirement here means it won't get built.
```

Present the traceability report to the user. Address any uncovered requirements or conflicts before delivering the final plan.

### 6. Final Deliverable

**MANDATORY**: The plan must be written to `plans/<descriptive-name>-implementation-plan.md`

A comprehensive design document that:
- Provides complete context for a NEW AI agent in a SEPARATE session (not you)
- Is fully traceable to the source spec — every phase maps to spec requirements
- Includes all discovered patterns and references
- Clearly defines what to build without implementation details
- Specifies validation criteria for each phase
- Notes that TDD approach should be used for implementation

**This plan will be implemented by a DIFFERENT agent using `/plan-implement` command.**

### 7. Completion

After completing steps 1-6, confirm the plan file path and remind the user to run `/plan-implement` when ready.

## Boundaries

After completing the plan:
- DO NOT ask "Ready to proceed with implementation?"
- DO NOT offer to start implementing the plan yourself
- DO NOT create a "Next Steps" section about implementation
- DO NOT suggest beginning Phase 1 or ask about timeline
- DO NOT question decisions already made in the spec
- DO write the plan to a file
- DO run all three mandatory reviews (general, plan-review, spec-coverage)
- DO ask if they want clarifications or changes to the plan
- DO remind them to use `/plan-implement` when ready to implement

## Success Criteria

The plan serves as an architectural blueprint providing:
- Full traceability to the source spec — every requirement has a phase
- Clear interface contracts
- Component interaction patterns
- Specific references to existing codebase patterns
- Sufficient guidance for implementation without constraining approach
- Complete context for successful implementation in a new session
