# Implementat A Plan

You are tasked with implementing a plan provided by the user

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

Tip: You can also invoke this command with a ticket file directly: `/implement plan.md`
```

Once the plan has been implemented, run the **codebase-review-critical**
and **codebase-guidelines-validator** agents in parallel and fix any issues found.
