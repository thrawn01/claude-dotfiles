---
name: plan-review
description: Reviews a plan to ensure the plan follows plan guidelines
---


# Implementation Plan Review

Use this checklist when creating or reviewing implementation plans to ensure compliance with surface testing and coding guidelines.

## Surface Testing Compliance

### Public Interface Testing
- [ ] All tests interact through public API (exported functions only)
- [ ] Zero tests call internal (unexported) functions directly
- [ ] Each phase implements a **working** version of the public API
- [ ] Tests can be written and pass before internal implementation exists

### Test Structure
- [ ] Test names in camelCase starting with capital letter (e.g., `TestConvertMinimalMarkdown`)
- [ ] All tests use table-driven approach where appropriate
- [ ] Tests use `require` for critical assertions, `assert` for non-critical
- [ ] No descriptive messages in assertions (use comments instead)

### Observability for Internal Behavior
- [ ] If internal behavior needs verification, expose through observability
- [ ] Debug/Stats fields in result types (populated optionally)
- [ ] Metrics, counts, or status info returned from public API
- [ ] Never test internal functions to verify internal behavior

### Code Organization
- [ ] Public API (exported functions) defined first in plan
- [ ] Internal implementation details come later
- [ ] Clear separation between "what" (public) and "how" (internal)
- [ ] Each phase delivers working, testable functionality

## CLAUDE.md Guidelines Compliance (Go Projects)

The following checklist items apply to Go projects. For non-Go projects, verify equivalent patterns in the project's CLAUDE.md.

### Testing Patterns (Go)
- [ ] Tests in `package XXX_test` (external test package)
- [ ] Test names in camelCase starting with capital letter
- [ ] Table-driven tests preferred for parameter validation
- [ ] Use `for _, test := range []struct {` style for error cases
- [ ] Use testify/require and testify/assert (NOT `if err != nil`)
- [ ] Use `require.ErrorContains(t, err, test.wantErr)` for error checking
- [ ] No explanations in assertions (no descriptive messages)

### Test Best Practices
- [ ] Use `require` for critical checks that should halt test
- [ ] Use `assert` for non-critical checks that allow test continuation
- [ ] Avoid logging in tests (use comments instead)
- [ ] Avoid DRY in tests (be explicit, repeat when needed)
- [ ] Tests verify behavior through public interface

### Code Guidelines (Go)
- [ ] Use `const` for variables that don't change and are used more than once
- [ ] Prefer one or two word variable names
- [ ] Inline values directly if variable used only once
- [ ] Use full words (not abbreviations) for variable names
- [ ] Use `lo.ToPtr()` for creating pointers to local variables

### Struct Field Formatting (Go)
- [ ] Order fields by line length (visual tapering)
- [ ] Longest lines toward top, shorter toward bottom
- [ ] Creates pleasing diagonal slope for readability

## Plan Structure Requirements

### Phase Organization
- [ ] Each phase has clear overview
- [ ] Each phase delivers working, testable increment
- [ ] Phases build incrementally on previous work
- [ ] No phase requires testing internal functions

### Documentation Per Phase
- [ ] Function signatures with clear responsibilities
- [ ] Testing requirements (via public API only)
- [ ] Test objectives (what behavior to verify)
- [ ] Validation commands (make test, make ci)
- [ ] Context for implementation (file:line references)

### Validation Checklist
- [ ] Each phase ends with validation steps
- [ ] Validation uses make targets (test, ci, coverage)
- [ ] Manual verification steps included where needed
- [ ] Explicit check that no internal function tests exist

## Red Flags (Plan Violations)

Watch for these patterns that indicate surface testing violations:

### ❌ Testing Internal Functions
- Test names like `TestBuildIR`, `TestExtractParameter`, `TestRenderTable`
- Tests in same package as implementation (not `_test` package)
- Tests calling unexported functions directly

### ❌ Phase Structure Issues
- Public API defined but not implemented in Phase 1
- Tests that can't run until later phases complete
- "Skeleton" or "placeholder" implementations that don't work

### ❌ Missing Observability
- Plan says "verify internal behavior" but no observability provided
- Debug/Stats fields missing when internal metrics needed
- Tests that require internal function access to verify correctness

## Approval Criteria

A plan is ready for implementation when:

- [ ] ✅ All checklist items above marked complete
- [ ] ✅ Zero red flags present
- [ ] ✅ Each phase has working public API that can be tested
- [ ] ✅ All tests go through public interface
- [ ] ✅ Observability added for any internal behavior that needs verification
- [ ] ✅ Plan reviewed by sub-agent and feedback incorporated
- [ ] ✅ CLAUDE.md guidelines followed throughout

## Quick Reference: Good vs Bad Patterns (Go Examples)

### ✅ GOOD: Functional Testing Approach
```go
// Phase 1: Working Convert() that returns minimal output
func TestConvert_MinimalMarkdown(t *testing.T) {
    result, err := conv.Convert(openapi, opts)
    require.NoError(t, err)
    assert.Contains(t, string(result.Markdown), "# Title")
}

// Phase 2: Extend Convert() with new feature
func TestConvert_TableOfContents(t *testing.T) {
    result, err := conv.Convert(openapi, opts)
    require.NoError(t, err)
    assert.Contains(t, string(result.Markdown), "## Table of Contents")
}

// Verify internal behavior through observability
func TestConvert_Debug_ParameterExtraction(t *testing.T) {
    result, err := conv.Convert(openapi, conv.Options{Debug: true})
    require.NoError(t, err)
    assert.Equal(t, 5, result.Debug.ParameterCount)
}
```

### ❌ BAD: Testing Internal Functions
```go
// Phase 1: Define Convert() signature only (not implemented)
func Convert(openapi []byte, opts Options) (*Result, error)

// Phase 2: Test internal builder
func TestBuildIR(t *testing.T) {
    ir := builder.BuildIR(schemas)  // ❌ Testing internal function
    assert.NotNil(t, ir)
}

// Phase 3: Test internal generator
func TestRenderMarkdown(t *testing.T) {
    md := generator.Render(ir)  // ❌ Testing internal function
    assert.Contains(t, md, "# Title")
}
```

## When to Use This Checklist

- ✅ Before starting any implementation plan
- ✅ After drafting plan, before review
- ✅ During sub-agent review process
- ✅ Before marking plan as complete
- ✅ When reviewing existing code for compliance

## Resources

- **Surface Testing Skill**: See `surface-testing` skill for detailed examples
- **CLAUDE.md**: See `~/.claude/CLAUDE.md` for testing patterns and code guidelines
