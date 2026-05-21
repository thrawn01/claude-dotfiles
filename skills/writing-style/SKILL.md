---
name: writing-style
description: Write or edit prose in the practitioner essay style — experience-backed, opinionated, structured but conversational. Use for blog posts, tech specs, engineering communications, and any long-form writing the user asks for. Activated when the user asks to "write a post", "draft a blog", "write up X", "edit this for style", or invokes /writing-style directly.
---

# Practitioner Essay Style

All prose produced under this skill follows the practitioner essay style. This style draws authority from production experience, not theory. It is opinionated but fair-minded, conversational but structured, and always grounded in real-world consequences.

This skill applies to blog posts, tech specs, engineering communications, internal documentation, and any other long-form writing the user requests. Adapt the structure and formality to the medium — a blog post gets full narrative treatment, a tech spec gets the tone and argumentation pattern without the storytelling.

## Voice

Write as an experienced practitioner speaking to peers. Authority comes from having built and operated systems, not from citations or credentials. Ground claims in production experience — what happened, what broke, what worked. First-person accounts of real outcomes are the primary evidence.

The practitioner voice implies:
- You've been burned by the thing you're warning about
- You've shipped the thing you're recommending
- You have conviction earned from experience, not ideology

### Technical specificity over polish
This voice sounds like someone who builds systems, not someone who writes about building systems. Prefer concrete technical details (name the database, the failure mode, the scale) over polished generalizations. "The reservation timed out and the message was delivered twice" is better than "things can go wrong in unexpected ways." When a sentence could appear in any senior engineer's blog post, it's too generic — make it specific to the actual system and experience.

## Argumentation Pattern

Structure arguments using the practitioner cycle. This is a repeatable unit — use it once for short pieces, nest it for longer ones where each section gets its own cycle.

### 1. Positional claim
Open with a clear stance. Plant a flag the reader can agree or disagree with. This is a declaration, not a question and not a gentle introduction. But strong is not the same as edgy — the claim should be measured and defensible, not provocative for shock value. The goal is conviction, not controversy.

- Strong: "Only test the public surface."
- Strong: "PostgreSQL carries the design baggage of a bygone era."
- Too edgy: "The testing industry has a coverage fetish."
- Weak: "In this post we'll explore some ideas about testing."
- Weak: "There are many opinions on database design."

### 2. War story
Ground the claim in something that happened — a production incident, a team decision, a system you built or operated. This is where authority lives. The story should be specific enough to be credible (name the system, the scale, the failure mode) but brief enough to serve the argument. The war story is evidence, not the point.

### 3. Extracted principle
Pull back from the specific story and state the general rule. The word "extracted" matters — the principle was earned from the anecdote, not assumed beforehand. This is the inductive move from particular to general.

### 4. Actionable guidance
Close with concrete recommendations. Tell the reader what to do, not just what to think. This is the payoff — practical, specific, implementable.

### Nesting
In longer pieces, each section runs its own mini-cycle. A blog post with four sections might have four positional claims, four war stories, four principles, and four sets of guidance. The overall piece also follows the cycle at the macro level — the opening plants the big flag, the body provides the evidence, the conclusion extracts the overarching principle.

## Tone

Write with confident informality — conversational but structured, opinionated but fair-minded.

### What the tone is
- **Conversational**: contractions, colloquialisms, first-person accounts. Reads like talking to a peer, not lecturing a classroom.
- **Authoritative**: speaks with confidence. Doesn't hedge or equivocate. Takes positions and defends them.
- **Earnest**: genuinely cares about the topic. Not detached, not ironic. Comfortable showing frustration or enthusiasm.
- **Direct**: every sentence does work. No filler, no padding, no throat-clearing.
- **Humorous when natural**: humor is dry and offhand — a parenthetical aside, a deadpan observation, an analogy grounded in something concrete ("smoke some brisket to celebrate — I live in Texas, it's a thing"). Never quippy, never performative, never a punchline crafted for effect. If the humor calls attention to itself, it's too much.

### What the tone is not
- Not chatty or meandering. Forward momentum always.
- Not formal or academic. Never "one might observe that..." or "it should be noted that..."
- Not preachy or moralizing. State the case and move on.
- Not detached or dispassionate. Care is visible.

### Anti-patterns to avoid
- Never open with "Hey folks!" or "Welcome to..." or "In this post we'll explore..."
- Never use academic hedging: "it could be argued that," "there is evidence to suggest"
- Never moralize: "developers should really think about..." "it's important to remember..."
- Never use filler transitions: "Moving on...", "With that said...", "Let's dive in..."
- Never use "we" to mean the general reader when the writer means "I." Use "I" for personal experience, "we" only when referring to an actual team.
- Never let a secondary concern become the framing lens. If the post is about testing strategy, frame it through the product and the customer — not through CI status or coverage badges. If the post is about developer workflow, then tooling framing is appropriate. Match the frame to the actual subject.

## Rhetorical Devices

Two devices are core to this style. Use them naturally, not mechanically.

### Dialogic objection handling
Anticipate what a skeptical reader would say and address it mid-paragraph. Argue with an imagined interlocutor. This creates a sense of conversation and shows the writer has considered the counterargument.

The construction matters: phrase objections as things the reader "might be thinking" or introduce them with "But wait..." — as if the thought just occurred in real-time. Never use the "I hear you say" or "you might say" construction, which sounds like a TED talk addressing an audience. The objection should feel like a natural interruption in the writer's own train of thought.

- "But wait, doesn't your example include user-provided data in the path? Yes, it does, and as with most things in life, there are exceptions."
- "You might be thinking this only applies to large teams. It doesn't."
- Wrong register: "I hear you saying, 'but that's slow.'" (too performative, too audience-aware)

### Aphoristic crystallization
Compress a principle into a memorable one-liner that works as a standalone quote. These should feel earned — they land because the argument built up to them, not because they were clever in isolation.

- "Once you release it, it lives forever."
- "Good architecture makes change easy."
- "There is no Vudu. The effect does have a cause."

Use sparingly. One or two per piece is enough. Blockquotes are a natural home for these.

## Structure

### Headers as signposts
Use headers to create a scannable structure. Readers should be able to get the argument from headers alone. Prefer short, declarative headers over question-form or clever headers.

- Strong: "Avoid user provided data in the path"
- Strong: "Test the Product, not the code"
- Weak: "What should we think about next?"
- Weak: "Down the rabbit hole"

### Blockquotes
Use blockquotes for two purposes: citing external sources and setting off the writer's own aphorisms or key claims. Both uses are common in this style.

### Lists for contrast
When comparing two approaches or philosophies, use parallel bullet lists. This is a signature structural device — two lists side by side that make the contrast visceral.

### Length and pacing
Sections should be long enough to complete a thought but short enough to maintain momentum. If a section needs more than a few paragraphs, break it into subsections. If a post grows beyond its natural scope, break it into separate posts — acknowledge this directly: "this post has already gone longer than I imagined, so I'm breaking it up."

## Adapting to Medium

### Blog posts
Full practitioner essay treatment. Narrative war stories, strong positions, aphorisms, humor. This is the native format for this style.

### Tech specs
Same tone and argumentation pattern, but compressed. Positional claims become design decisions. War stories become brief justifications referencing past experience. Extracted principles become design constraints. Actionable guidance becomes the specification itself.

### Engineering communications
Emails, Slack posts, RFC comments. Same voice — direct, opinionated, grounded in experience. Shorter. Skip the narrative scaffolding but keep the confident informality and the willingness to take a position.

### Internal documentation
Handbooks, onboarding guides, runbooks. Same voice. Emphasize the "why" — documentation explains why things are the way they are, not just how they work. Production anecdotes are especially valuable here, as they give new team members the context that code alone cannot.
