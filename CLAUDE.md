## Commiting Code
- You MUST NOT include Co-Authored notification in commit message
- You MUST NOT include Claude attribution in commit or description messages

## Pull Requests
- You MUST format the description as follows
```
### Purpose
A paragraph describing what this change intends to acheive

### Implementation
- An explaination of each major code change made
```

## Testing Patterns

- Test MUST always be in the test package `package XXX_test` and not `package XXX`
- Test names should be in camelCase and start with a capital letter (e.g., `ListAllEnrollments`)
- Table-driven tests are preferred for parameter validation
- Use integers to indicate multiples. For example, `listPageOne` becomes `listPage1` or simply `page1`.
- Avoid logging what the test is doing, instead prefer comments. For example, avoid `t.Log("Enrolling customers...")`
- Avoid the DRY (Don't Repeat Yourself) principle in tests, be explicit when testing repetitive behaviors.
- Use `for _, test := range []struct {` style test when testing error cases.
- Do NOT use `if (condition) { t.Error() }` for assertions. Use `github.com/stretchr/testify/require` and `github.com/stretchr/testify/assert`
- Do NOT use `require.Contains(t, err.Error(), test.wantErr)` use
  `require.ErrorContains(t, err, test.wantErr)` instead.
- Avoid placing explanations in require or assert statements. Do not include descriptive messages as the final parameter. For example:
    - Do NOT use: `require.NotNil(t, page1, "page1 result should not be nil")`
    - Do NOT use: `require.NoError(t, err, "Failed to enroll for %s", customerID)`
    - Do NOT use: `require.NotEmpty(t, endCursor, "EndCursor should not be empty")`
    - Instead use: `require.NotNil(t, page1)`, `require.NoError(t, err)`, `require.NotEmpty(t, endCursor)`
- Use `require` for critical assertions that should halt the test on failure, use `assert` for non-critical assertions that allow the test to continue. Import both packages when needed:
    - Use `require` for: error checking (`require.NoError`), nil checks that prevent further operations, setup/teardown operations
    - Use `assert` for: value comparisons (`assert.Equal`), boolean checks (`assert.True`/`assert.False`), length checks (`assert.Len`), existence checks where test can continue
    - Example:
    ```go
    // Critical operations - test cannot continue if these fail
    require.NoError(t, err)
    require.NotNil(t, result)

    // Non-critical assertions - test can continue to verify other aspects
    assert.Equal(t, expectedValue, result.Value)
    assert.True(t, result.IsValid)
    assert.Len(t, result.Items, 3)
    ```

## Code Guidelines

- Use `const` for variables that don't change and are used more than once
- Prefer one or two word variable names
- Avoid using local variables if the variable is only used once. Inline values directly into function calls instead.
    ```go
    // BAD: Creating variables that are used only once
    request := pkg.EnrollRequest{Thing: pkg.Thing1, Key: "value"}
    err := core.Enroll(ctx, request)

    // GOOD: Inline the struct directly
    err := core.Enroll(ctx, pkg.EnrollRequest{
        Thing:  pkg.Thing1,
        Key:    "value",
    })
    ```
- Prefer one or two word variables. `createdProductIDs` should be `created` or `createdIDs` if `created` is unclear in the current context
- Don't use abbreviations for variable names, use full words instead. For example `listP1` should be `listPage1`
- Use single letters for variable names only if the context is clear, and the scope is very small. For example, within a for loop where `i` is the index.
- Use `const` for variables that do not change. For example, `numEnrollments := 20` should be `const numEnrollments = 20`
- Do not comment in code that you are following guidelines
- Use `lo.ToPtr()` from the `github.com/samber/lo` package to create pointers to local variables

## Struct Field Formatting - Visual Tapering
When formatting struct literals, arrange fields to create a visual tapering effect:
- Order fields by the length of their complete line (field name + value)
- Place longer lines toward the top, shorter lines toward the bottom
- This creates a pleasing diagonal slope from long to short
- The goal is visual harmony and improved readability, not strict alphabetical or logical ordering

Example:
```go
req := pkg.CreateRequest{
    ThingType:      "THIS_THING_IS_WAY_TOO_DARN_LONG",  // longest line
    Quantity:       decimal.NewFromInt(100),            // medium length
    DriversID:      "DL-2134234122132",                 // medium length
    ThingID:        pkg.ThingTwenty,                    // medium length
    ThingName:      "thing-20",                         // shorter
    PackageID:      "pack",                             // shorter
    Msg:            "hi",                               // shortest
}

### Problem Solving
- Prefer fixing implementation over changing tests - When tests fail after code
  changes, the default assumption should be that the implementation broke
  expected behavior, not that the tests are wrong
- Tests encode business requirements - Test expectations often represent the
  correct business behavior that should be preserved. Changing tests to match
  broken implementation can mask real functional regressions
- Investigate test failures as potential bugs first - Before concluding "the
  tests need to be updated," thoroughly investigate whether the implementation
  correctly preserves the original business semantics
