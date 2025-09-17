# Review Comments

You are tasked with reading a file provided and addressing any `// REVIEW` comments in the file

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - If a file path was provided as a parameter, skip the default message
   - Immediately read any provided files FULLY
   - Begin the review

2. **If no parameters provided**, respond with:
```
I'll help you review a file, please provide the name of the file which
contains `// REVIEW` comments and I'll read the file and begin implementation

Tip: You can also invoke this command with a ticket file directly: `/review-comments code.go`
```
