You are tasked with creating detailed implementation plan based on the context
of the existing conversation. Your goal is to produce high-quality technical implementation
plan that will be executed by an AI agent in a new session.

### Implementation Plan Creation

#### Plan Structure Requirements

**A. Phased Delivery**
- Multiple phases representing testable milestones
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

[Explicitly list out-of-scope items to prevent scope creep]

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

**This plan will be implemented by a DIFFERENT agent using `/implement-plan` command.**

### 7. Plan Delivery (MANDATORY FINAL STEP)

After completing steps 1-6:

1. **Confirm plan is written** to `plans/<descriptive-name>-implementation-plan.md`
2. **Confirm review completed** with sub-agent (as per step 5)
3. **Present final summary** to user including: number of phases, that file:line references and validation commands are included, the file path created, and a reminder to run `/implement-plan` when ready
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
- DO remind them to use `/implement-plan` when ready to implement

## Success Criteria

The plan serves as an architectural blueprint providing:
- Clear interface contracts
- Component interaction patterns
- Specific references to existing codebase patterns
- Sufficient guidance for implementation without constraining approach
- Complete context for successful implementation in a new session
