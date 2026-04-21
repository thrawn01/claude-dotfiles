---
name: pr-github-review
description: Review GitHub pull request comments and address reviewer feedback. Use when the user says 'review PR comments', 'address PR feedback', or provides a GitHub PR URL.
---
You are tasked with reviewing github pull request comments.

When this command is invoked:

1. **Check if parameters were provided**:
   - Parameters appear as text after the command (e.g., `https://github.com/<path-to-pr>`)
   - If a URL was provided, skip the default message and begin the review process immediately
   - If the parameters include a github name after the url, then only review
     comments from that user.

2. **If no parameters provided**, respond with:
```
I'll help you review pull request comments

Please provide the URL for review
```
Then wait for the user's input.
