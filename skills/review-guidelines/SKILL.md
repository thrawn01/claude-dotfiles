---
name: review-guidelines
description: Review code changes for compliance with CLAUDE.md guidelines. Use when the user says 'review guidelines', 'check guidelines', or 'validate against guidelines'.
---
# Review Code Guidelines

You are tasked with reviewing code changes for compliance with the CLAUDE.md guidelines.

## When Invoked

1. **Check if parameters were provided**:
   - If a branch name or file path was provided, use that to scope the review
   - If no parameters provided, review all changes on the current branch vs main

2. **Gather the changes**:
   - Run `git diff master...HEAD` to get all changes on the current branch
   - If no diff exists (on main), run `git diff HEAD` for unstaged/staged changes
   - If a specific file was provided, scope the diff to that file

3. **Read the full CLAUDE.md** to get the current guidelines

4. **Review each changed file** against the guidelines found in CLAUDE.md

## Output Format

For each violation found, report:

```
### [Category]: [Brief description]
**File**: `path/to/file.go:line`
**Guideline**: The specific rule being violated
**Current code**:
\```
// the offending code
\```
**Suggested fix**:
\```
// the corrected code
\```
```

## Summary

End with a summary:
- Total violations found
- Violations by category
- Overall compliance assessment (compliant / minor issues / needs attention)

## Important Notes

- Focus on **changed lines** - do not flag pre-existing violations in unchanged code
- If no violations found, confirm the code is compliant
- Do NOT automatically fix violations - report them for the user to review
- Be specific with line numbers and file paths
