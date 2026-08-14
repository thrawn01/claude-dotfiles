---
name: lazy
description: "Write the fewest words that carry the facts — terse, plain, human, not
  lawyerly. Auto-apply whenever the user asks to draft a message, write something up,
  write a Slack/email/standup/PR description, or 'write up X for the team'. Also
  invocable directly as /lazy. Do NOT apply to ADRs, blueprints, tech specs, or other
  documents where structure and completeness are the point."
argument-hint: "[what to write, or paste of a draft to tighten]"
---

# Lazy Writing

Write like a tired engineer who respects the reader's time: say the thing in as few
words as it takes, then stop.

## Base rules

Follow the **Simplified Technical English** output style
(`~/.claude/output-styles/simplified-technical-english.md`). It is usually already in
your system prompt. It carries the sentence, voice, and word rules this skill assumes.

If it is not in your system prompt, apply these six rules instead:

- Keep sentences to 20 words. One idea per sentence.
- Use active voice and simple tenses. Avoid the `-ing` form.
- Use the same word for the same thing. Never swap in a synonym for variety.
- Cut hedges and intensifiers: very, really, basically, actually, simply, just.
- Put the conclusion first, the evidence after.
- To shorten, cut whole ideas. Never cut articles, verbs, or relative pronouns.

## What this skill adds

**Audience.** You draft a message for someone else to send or post — Slack, email, a
standup, a PR description. Not an answer to the user.

**Register.** Looser than the base rules allow. Contractions, plain verbs, the
occasional human aside. "The image went bye bye" beats "the image was garbage-collected
from the registry."

**No AI-tell openers.** No "Heads up", "One thing on your radar", "A couple things to
flag", "On that note". State the fact. Do not announce that a fact is coming.

**No lawyer mode.** One line per real point. Name the caveat that matters and move on.
Do not enumerate every edge case.

**No `**Label:**` scaffolding** on every line. Prose, not a form.

**Receipts stay verbatim.** Commands, IDs, error strings, and links never get shortened.
Terseness applies to the prose around them.

## Anti-examples → fixes

- "It's worth noting that staging and prod are currently unaffected; however, they will
  eventually be subject to the same condition." → "Staging and prod are fine now but on
  the same clock."
- "I went ahead and triggered the pipeline in order to rebuild a fresh image." → "I
  triggered the pipeline to rebuild the image."
- "Heads up — there are a couple of follow-up items worth tracking." → list them, or cut
  the sentence.

## When not to apply

Skip ADRs, blueprints, tech specs, and PRDs. Those want structure and completeness. They
have their own skills.

## Process

1. Draft, or read the user's draft.
2. Pass over it once. Delete the ideas that carry nothing, kill the openers, flatten the
   labels.
3. Output only the message, ready to paste. No preamble about what you changed.
