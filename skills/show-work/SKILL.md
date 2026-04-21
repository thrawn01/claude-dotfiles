---
name: show-work
description: "Present investigation evidence as markdown directly in chat.
  Shows commands run and their full output as copyable markdown.
  Use when the user says 'show work', 'show me the evidence',
  or 'give me the receipts'."
argument-hint: "[topic or question to investigate]"
allowed-tools: [Bash, Read, Glob, Grep]
---

# Show Work

Present investigation findings as structured markdown **directly in the conversation** — never as a file.

## Output Format

For each piece of evidence, show the exact command run and its full unedited output using markdown code blocks. Structure the response as:

1. **Title** — a short heading describing what was investigated
2. **Evidence sections** — each section has:
   - A markdown heading describing what this check proves
   - The command run, shown as `$ command` inside a code block
   - The full output immediately below in the same code block
3. **Conclusion** — a short paragraph at the end tying the evidence together

## Rules

- Output everything as markdown directly in the chat response — do NOT write files
- Show command output fully when practical — truncation is acceptable provided it does not hide information important to the investigation
- Prefix each command with `$ ` so it reads like a terminal session
- Use fenced code blocks with appropriate language hints (```yaml, ```json, etc.) when the output is structured
- Group related commands under descriptive headings (e.g., "### No active pods" not "### Step 3")
- If `$ARGUMENTS` is provided, investigate that topic. Otherwise, compile evidence from commands already run in the current conversation.
- Re-run commands if needed to get fresh output — do not rely on stale results
- Include timestamps where relevant (e.g., job start/completion times)
- If a command fails or returns empty, include that too — absence of results is evidence
