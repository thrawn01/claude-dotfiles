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

2. **Code Architecture** (Golang)
   - Function signatures for public APIs
   - Key structs with field definitions and JSON tags
   - Interface definitions
   - Data flow documentation

3. **Testing Requirements**
   - High-level test objectives
   - Key scenarios to cover
   - Tests validate complete critical path through public APIs only
   - Include database interaction validation where applicable
   - Note: Implementation should follow TDD approach

4. **Validation Commands**
   - Specific commands to validate milestone completion (e.g., `go test ./...`, `make build`)
   - To find validation commands: Check `Makefile`, `package.json` scripts, `justfile`, or similar project automation files
   - Look for existing CI/CD configurations for standard project commands

5. **Context for Implementation**
   - Links/paths to relevant existing code files
   - Database schema if relevant
   - External dependencies or APIs used
   - References to discovered patterns

#### Documentation Guidelines

**What TO Include:**

1. **Function Signatures and Descriptions**
```go
// FunctionName performs [high-level purpose]
func (c *Struct) MethodName(ctx context.Context, arg1 ArgOne) error
```

**Function responsibilities:**
- Primary operation description
- Pattern reference: "Follow error handling from `auth.go:45-52`"
- Business logic: "Call existing `BusinessMethod()`"
- Validation: "Validate inputs using pattern from `validator.go:23`"

2. **Struct Definitions**
```go
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
// Existing tests that may require updates:
func TestExistingFunction(t *testing.T)  // May need: [specific aspect, e.g., "updated mock responses"]
func TestRelatedFunction(t *testing.T)   // May need: [specific aspect, e.g., "adjusted assertions"]
```

**Requirements for Refactoring:**
- All existing tests must pass after changes
- Minimize test changes (only update if public APIs or contracts change)
- Do NOT create new test signatures unless new functionality is being added

### 4. Document Creation
1. **Write the plan** to a file
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

**Function Responsiblities:**
- Bullet point list of what the function must do

**Testing Requirements:**
```[language]
// Function siguatures of Tests to update or create
```

**Test Objectives:**
- Bullet point list of test objectives

**Context for implementation:**
- Bullet point list of context valid for the implementation of this phase
```

### 5. Review Process
1. Pass the plan to a sub-agent for review
2. Sub-agent evaluates for:
   - **Completeness**: Are all requirements addressed?
   - **Clarity**: Will another agent understand what to build?
3. Sub-agent provides questions to improve the plan
4. Present questions to user
5. Wait for user responses
6. Iterate: Refine plan based on answers → Review again → Repeat until satisfactory

### 6. Final Deliverable
A comprehensive design document that:
- Provides complete context for a new AI agent session
- Includes all discovered patterns and references
- Clearly defines what to build without implementation details
- Specifies validation criteria for each phase
- Notes that TDD approach should be used for implementation

## Success Criteria
The plan serves as an architectural blueprint providing:
- Clear interface contracts
- Component interaction patterns
- Specific references to existing codebase patterns
- Sufficient guidance for implementation without constraining approach
- Complete context for successful implementation in a new session
