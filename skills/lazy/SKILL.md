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
words as it takes, then stop. The goal is laziness in the good sense — minimum words,
maximum signal — not lawyering every caveat "to be safe."

## When this applies

Auto-apply when the user asks to **draft a message**, **write something up**, **write
a Slack/email**, **write my standup**, **draft a PR description**, or **write up X for
the team**. Also when invoked as `/lazy`.

Do NOT apply to ADRs, blueprints, tech specs, PRDs, or docs where structure and
completeness matter — those have their own skills and want more, not less.

## Rules

- **Fewest words that still carry the fact.** If a sentence survives deletion without
  losing information, delete it.
- **No throat-clearing.** Drop "it appears that", "it's worth noting", "I wanted to
  flag", "just to be safe". Lead with the fact, don't announce that a fact is coming.
- **No AI-tell openers.** No "Heads up", "One thing on your radar", "A couple things to
  flag", "On that note". State it directly. (See feedback_avoid_ai_phrasings.md.)
- **No lawyer mode.** One line per real point. Don't enumerate every edge case and
  caveat — name the one that matters and move on.
- **No `**Label:**` scaffolding** on every line. Prose, not a form.
- **Plain verbs, contractions, the occasional human aside.** "the image went bye bye"
  beats "the image was subsequently garbage-collected from the registry."
- **Keep the receipts.** Commands, IDs, error strings, links stay verbatim — terseness
  applies to the prose around them, never to the evidence.
- **Active voice, present tense** where natural. Short sentences over compound ones.

## Anti-examples → fixes

- "It's worth noting that staging and prod are currently unaffected; however, they will
  eventually be subject to the same condition." → "Staging and prod are fine now but on
  the same clock."
- "I went ahead and triggered the pipeline in order to rebuild a fresh image." → "Got it
  running by triggering the pipeline to rebuild the image."
- "Heads up — there are a couple of follow-up items worth tracking." → just list them, or
  cut the sentence.

## Process

1. Draft (or read the user's draft).
2. Pass over it once: delete every word that isn't load-bearing, kill the openers, flatten
  the labels.
3. Output only the message — ready to paste. No preamble about what you changed unless asked.
