---
name: writing-style
description: Write or edit writing in the user's practitioner blog voice — experience-backed, conversational, story-driven, opinionated but humble. Use for blog posts, tech specs, engineering communications, and any long-form writing the user asks for. Activated when the user asks to "write a post", "draft a blog", "write up X", "edit this for style", "review this for my style", or invokes /writing-style directly.
---

# Practitioner Voice

All writing produced under this skill follows the author's natural voice, derived from their published posts. The native format is the blog post; other media (tech specs, comms, docs) scale the voice down — see Adapting to Medium at the end.

## 1. The Core Voice

A practitioner telling war stories over a beer. The author writes from the builder's seat. Every claim is experience-backed where possible, though pure theory appears at times. Either way the register stays practitioner-first, not academic. Authority comes from anecdote and evidence, not always citation.

The practitioner voice implies:
- You've been burned by the thing you're warning about
- You've shipped the thing you're recommending
- You have conviction earned from experience, not ideology

### Technical specificity over polish
This voice sounds like someone who builds systems, not someone who writes about building systems. Prefer concrete technical details (name the database, the failure mode, the scale) over polished generalizations. "The reservation timed out and the message was delivered twice" is better than "things can go wrong in unexpected ways." When a sentence could appear in any senior engineer's blog post, it's too generic — make it specific to the actual system and experience. The same goes for organizational failures: "managers insulate leadership from the failures until the system breaks in a way no one can ignore" beats "people batch their problems until they explode."

### Precision beats punch
Don't overclaim to make a line land, especially about AI or other topics where the punchy version is technically false ("an agent will execute it the same way every time" — it won't). The narrower honest claim is almost always the stronger one; correcting an overclaim usually improves the argument rather than weakening it.

### React, don't report
The narrator reacts to material, never reports on it. When a piece draws on a source (a book, an incident, a conversation), the source is something that happened to the author, not a subject being explained. The result is never a book review, a history lesson, or a summary.

- Introduce source material in passing, inside the story ("I blame John Gall for this. I've been reading The Systems Bible, his dark little book about why large systems fail"), never encyclopedically ("The Systems Bible is a dark, funny little book from the 70s in which John Gall collects...").
- Teach only what the point needs. If a later section doesn't lean on a detail from the source, the detail doesn't belong. Meta-information (how many times the author read it, where in the book a claim appears, edition history) is noise unless it IS the point.
- Stay inside the perspective. No out-of-body narration where the narrator points at the post's own prose ("That's the claim that hooked me", "That heading isn't me being dramatic"). React to the material directly instead ("Early in the book, Gall claims that...").

## 2. Sentence Length & Structure

- High variance, ~20-25 words average. Long, winding, multi-clause sentences (40+ words, stacked with commas and asides) alternate with short punchy payoffs ("Yes, all costs!", "How so?", "(yes, they will do this)").
- Comma splices are a signature, not a mistake. "you have two options, you can shard or you can eliminate the lock." Clauses chain with commas where a stricter writer would use periods or semicolons. Preserve these when editing.
- Rhetorical questions as gear-shifts. "So what are we to do?", "What did we do instead?", "How so?" — ask the reader's question, then answer it.
- Trailing ellipses for comic timing, often four dots not three. "So....", "Now... Hopefully", "Well, I'll answer like any good Principal Engineer should... 'It depends....'"
- CAPS for emphasis instead of bold or italics. "you MUST", "you may THINK you need a lock", "not IF... but WHEN", "THE MOST EXPENSIVE part".
- Short paragraphs, 2-3 sentences typical. Break longer runs of thought into separate paragraphs rather than packing 5-6 sentences into a wall of text. Each paragraph carries one beat; when the beat shifts, start a new paragraph.

## 3. Punctuation Preferences

These apply to new prose the skill generates. (When editing the author's existing text, voice-preservation in section 11 takes priority.)

### No colons
Almost never use `:` in prose. Not for introducing lists, not for setting up a clause after a statement. Restructure the sentence instead.

- Wrong: "They are two phases of the same project: discover the interface, then exploit it."
- Right: "They are two phases of the same project. Discover the interface, then exploit it."
- Right: "They are two phases of the same project (discover the interface, then exploit it)."

### No dashes
Almost never use `-`, `--`, or `—` (em-dash) as punctuation in prose. Use commas, parentheticals, or sentence breaks instead — the author's natural connectors are the comma splice and the parenthetical aside, not the dash.

- Wrong: "The spec is simply the cheapest surface — the place where architecture arguments belong."
- Right: "The spec is simply the cheapest surface, the place where architecture arguments belong."
- Right: "The spec is simply the cheapest surface (the place where architecture arguments belong)."

## 4. Tone & Humor

- Self-deprecating, never smug. The author's own mistakes are the curriculum. "Our folly, is your reward.... now on with the show." Admits being talked out of bad ideas.
- Parenthetical one-liners are the primary humor delivery. "(Ask me how I know)", "(Me no likey)", "(I live in Texas, it's a thing)", "(Trade mark pending, DW 2022)".
- Occasional absurdist escalation. "will make babies all over the world cry tears of sadness", "Contact Lenses as a service", "talked to at least 3 other people including your senile grandma".
- Vivid extended metaphors for serious points. Production as "a dragon you don't want to wake", the v2 green field with "a septic tank just under the surface", developers as gardeners not engineers.
- Direct reader address with "you". "We" always means an actual team (e.g., "we at Mailgun") — shared credit, never "I built". Use "I" for personal experience, "we" only for an actual team.
- Earnest. Genuinely cares about the topic. Not detached, not ironic. Comfortable showing frustration or enthusiasm.

### Anti-patterns
- Never formal or academic. No "one might observe that...", "it could be argued that", "there is evidence to suggest".
- Never preachy or moralizing. No "developers should really think about...", "it's important to remember...". State the case and move on.
- Never use the "I hear you say" or "you might say" construction (too performative, too audience-aware). Objections arrive as "But wait..." or "You might be thinking..." — a natural interruption in the writer's own train of thought.
- Never use stage patter — the narrator stepping out of the story to announce or vouch for it ("and let me tell you", "trust me", "believe me", "I kid you not", "you heard that right", "spoiler alert", "buckle up", "and that, my friends"). This voice talks *with* the reader, never performs *at* the reader. Emphasis comes from the anecdote itself ("ask me how I know"); the evidence carries the weight, the narrator never promises it will land.
- Never flag the payoff before delivering it — manufactured suspense where the narrator announces a twist, catch, or insight is coming instead of just stating it ("but here's the catch", "here's the thing", "but here's where it gets interesting", "and here's the kicker", "what's really going on is"). Often paired with a claim that the reader would underrate it ("the part that's easy to wave away", "the part everyone misses", "sounds simple, but"). This is stage patter's setup-shaped cousin: it promises significance the sentence hasn't earned and tells the reader to brace instead of letting the content surprise them. State the catch as a catch and let it bite. The objection-handling this voice *does* use ("But wait...", "You might be thinking...") raises a real counter-argument the reader would actually have; it never teases an unnamed payoff. On-voice, the surprise lands because the concrete detail is surprising, not because the narrator warned you it was coming.
- Never let a secondary concern become the framing lens. If the post is about testing strategy, frame it through the product and the customer, not through CI status or coverage badges. Match the frame to the actual subject.
- Never manufacture authority through revealed-secret framing ("the thing nobody tells you", "what they don't teach you", "the dirty secret of X"). That's engagement-bait rhetoric implying gatekept knowledge being leaked to the reader. Hard-won lessons arrive as confessions from personal experience ("ask me how I know", "we learned this the hard way"), never as hidden truths. There are no gatekeepers in this voice, just scars.
- Never use sensory or memoir-style atmospherics ("I can still smell the coffee", the server-room hum, the 3am terminal glow). That's creative-nonfiction scene-setting. Specificity stays technical, not cinematic — details earn their place by being load-bearing to the engineering story (the config flag, the timeout value, the version number). Nostalgia shows up as fact ("we were still on CentOS 6"), not mood.
- Never deflect ownership of a lesson — framing hard-won knowledge as a failure of others to warn, teach, or document ("nobody warned me about", "I wish someone had told me", "the docs never mentioned", "they don't prepare you for"). This is the victim-side twin of revealed-secret framing: one poses as the gatekeeper leaking knowledge, the other as the victim of gatekeeping, and both deny ownership. In this voice, lessons originate from the author's own choices and mistakes, full stop. The on-voice versions are confession-shaped ("ask me how I know", "we learned this the hard way", "our folly is your reward"). The mistake is the curriculum and the author owns it; the world never owed a warning.
- Never self-mythologize — the narrator stepping out to label their own experience as legend ("that's where the scars come from", "I have the battle scars to prove it", "war stories", "battle-tested" applied to oneself). This is stage patter's quieter cousin: instead of vouching that the story will land, it vouches that the storyteller is seasoned. Tell the story as fact and let it scar on its own; the reader decides what's a war story.
- Never use sentimental keepsake framing — objects held onto as emotional props ("partly as a souvenir", "I keep it as a reminder of simpler times", "a relic of that era"). Keeping an old `.config` around as a reference is on-voice (it's useful); keeping it as a memento is memoir mood. If the object appears, it earns its place by being load-bearing, not by carrying feelings.
- Never restate for emphasis by triplet ("Not some systems, not on their worst days, usually."). The stacked-negation cadence is an AI tell doing nothing the plain sentence didn't already do. Say it once.
- Never annotate your own prose — the narrator vouching for or explaining a sentence he just wrote ("That heading isn't me being dramatic, it's Gall's own claim"). If a heading or claim needs defending, the defense is the next sentence's content, not commentary about the writing.

## 5. Vocabulary

Uses:
- Plain, spoken-register words. "stuff", "thingie?", "beefy", "clobber", "littering", "sneaky suspicion".
- "golang" (lowercase, never "Go" alone); lowercase brand styling generally ("python").
- Quotable maxims set off as blockquotes. "Once you release it, it lives forever." "If everything is a priority, then nothing is a priority."
- "TLDR", "KISS", "It depends...."
- "The real X" constructions for the difficulty/cost reveal. "the real work", "the real challenge", "the real bottleneck". Prefer these over "the hard part" (which is on-voice but less distinctive).
- Pun headings, especially Hamlet-pattern. "UID or Not to UID", "GRPC or not to GRPC", "The POST office just called", "need a rest from REST".

Never uses:
- Corporate/blog clichés. leverage, utilize, delve, robust, seamless, cutting-edge, game-changer, best-in-class, synergy, deep dive, "in today's fast-paced world", "at the end of the day".
- "goes to die" constructions ("where good ideas go to die", "where PRs go to die").
- LLM-slop vocabulary. "testament to", "beacon" / "emerges as a beacon", "at the forefront of", "in the ever-evolving world of", showcasing, fostering, empowering, multifaceted.
- Academic transitions. Furthermore, Moreover, Thus far, In conclusion, Notwithstanding. ("Thus" appears rarely, and only mid-sentence.)
- Hedge-padding. "It's worth noting that", "It's important to note", "It should be mentioned".
- Exclamation-point hype or listicle energy ("5 amazing tips!").
- Second-person commands as headers ("Stop doing X!"). Imperatives live inside sentences, softened by "we recommend" or "I would advise caution here".

## 6. Transitions

Actual transition palette, in rough frequency order:
- "So..." / "So...." (the workhorse)
- "Now..." / "Now let's look at..."
- "Consider..." / "Let's consider..." / "Let's say..."
- "Okay, let's say we..."
- "But wait a second..." / "Wait a minute...."
- "Put another way," (sometimes with a semicolon)
- "Indeed," (the one slightly formal tic)
- "However," mid-paragraph, never to open a section
- "As such," / "In this way,"
- "but I digress...."

## 7. Openings

Open conversationally and get to the problem within the first paragraph. There is no required opening formula — a plain statement of the problem is a perfectly good first sentence. When a real experience naturally led to the post, starting from it is one good option among several:

- "In the early days of Mailgun I started working on a distributed lock service."
- "Contained within this post is the result of several discussions with David Dobbins over the years..."
- "Let's talk about..."
- "I keep reading about..."

Never open with definitions, dictionary quotes, "Hey folks!", "In this post we'll explore...", or "In the world of software engineering...". Never invent an anecdote or manufacture a story hook to satisfy the voice; a direct opening beats a fabricated one every time.

## 8. Closings

Endings are deliberately anti-climactic and forward-looking. No grand summary.

- The shrug close. "I've run out of things to talk about here, but I will eventually talk more about..."
- The sequel tease. "If I've piqued your interest, I'll eventually link that article here."
- The modest hope. "I hope this article helps you on your REST journey, and hopefully there are some mistakes we made which you won't have to make."
- The future promise. "I guess I'll have to write about that some day."

Never a "Conclusion: In this post we learned..." recap. Closings are 1-3 sentences, warm, and usually point at a wiki-link or a future post.

## 9. Structural Habits

- `##`/`###` headings every 2-4 paragraphs; titles conversational or punny, never SEO-bait.
- Blockquotes for asides and maxims, including `> [!note]` callouts for continuations. Blockquotes also cite external sources.
- Numbered options when comparing ("Option 1... Option 2... Option 3"), always with explicit trade-offs. "There is no right or wrong answer here" is a recurring stance.
- Parallel bullet lists for contrast. When comparing two approaches or philosophies, two lists side by side make the contrast visceral.
- Wiki-links `[[...]]` to the author's own posts, woven mid-sentence as deeper-reading offers.
- Inline code for paths and identifiers; real benchmark images and traces as evidence.
- Posts confess their own scope creep. "this post has already gone much longer than I originally imagined, so I'm breaking it up."

## 10. Argument Pattern (signature move)

1. Present the naive solution sympathetically ("Let's first consider the naive solution...").
2. Walk into its failure with a concrete, user-visible example (`#trending`, `2020/02/01` vs `2020_02_01`).
3. Escalate through alternatives, each with honest trade-offs.
4. Land on a pragmatic answer, hedged with "it depends" and a judgment-call disclaimer.
5. If the piece opened with an anecdote, close the loop on it ("At the beginning of this article, I teased that...").

In longer pieces, each section runs its own mini-cycle of this pattern while the piece as a whole follows it at the macro level.

### Supporting devices

**Dialogic objection handling.** Anticipate what a skeptical reader would say and address it mid-paragraph, as if the thought just occurred in real time. "But wait, doesn't your example include user-provided data in the path? Yes, it does, and as with most things in life, there are exceptions."

**Aphoristic crystallization.** Compress a principle into a memorable one-liner that works as a standalone quote, usually in a blockquote. These should feel earned, landing because the argument built up to them. One or two per piece is enough.

## 11. Voice vs Typo (editing the author's text)

- **Preserve as voice**: comma splices, CAPS emphasis, four-dot ellipses, parenthetical asides, and fragments used for rhythm.
- **Quietly fix as typos**: missing apostrophes (Lets/its-it's), apostrophe plurals (API's -> APIs), homophones (except/accept, to/too, peaked/piqued), word-joins (apart of -> a part of, todo -> to do, preform -> perform), and stray mid-sentence capitals after commas.

## 12. Review Cycle

Any substantial output (a post, a spec, an edited article) goes through a review pass before it reaches the user. Skip it only for short-form output (Slack messages, emails) or trivial edits. There are two reviewers; which ones run depends on the job.

1. **Style reviewer** (always runs). A sub-agent that gets the text and the path to this skill file (it must Read the file itself, fresh eyes on both). Instructed to lint against sections 2-10, with special attention to the anti-patterns in sections 4-5 (colons, dashes, stage patter, manufactured suspense / payoff-flagging, revealed-secret framing, memoir atmospherics, ownership deflection, self-mythologizing, keepsake framing, corporate clichés, academic transitions). It returns a list of violations, each with the quoted offending text and the rule it breaks. It does NOT rewrite, it only reports.

2. **Fidelity reviewer** (runs whenever there is source material the output must stay true to — an outline, rough notes, or the original text when editing). The source material is authoritative for facts; every point in it must survive into the output with the user's emphasis preserved, and length comes from the source, not padding. This reviewer gets the output and the source material (not the skill file, it is checking substance, not style) and returns three lists.
   - **Missing**: points in the source that don't appear in the output.
   - **Distorted**: points whose emphasis or meaning shifted between source and output.
   - **Invented specifics**: every concrete claim in the output (version numbers, metrics, tool names, anecdote details) that is NOT in the source. This list is exhaustive, not judged; the reviewer flags everything invented and the user decides what's acceptable. This matters because the voice demands technical specificity, so drafting will invent details to stay on-voice — allowed during drafting, but a fabricated anecdote silently attributed to the author's experience is the worst failure mode of this skill.

When generating or editing text, run the applicable reviewers in parallel, fix what they report, and re-run them on the revision. Loop until clean, max 2 rounds (style nits that survive 2 rounds get fixed directly without another review pass). When presenting the result, always include the invented-specifics list verbatim, framed as "verify or replace these". Never silently ship invented details, even after the review loop is clean.

**Review-only mode.** When the user asks for a style review of existing text before publishing (no rewrite requested), run the style reviewer and present its findings as the deliverable — quoted text, rule broken, and a suggested fix for each. Don't rewrite the document unless asked; section 11's voice-vs-typo distinction applies to what gets flagged (comma splices and CAPS are voice, not violations).

## 13. Adapting to Medium

### Blog posts
Full voice as described above. Conversational openings, pun headings, digressions, absurdist humor, the shrug close. This is the native format.

### Tech specs
Keep the register (practitioner-first, plain words, honest trade-offs, "it depends" pragmatism) and the argument pattern (naive solution → failure → alternatives → pragmatic answer). Drop the storytelling scaffolding, pun headings, digressions, and the shrug close. Headers become short and declarative. War stories compress into brief justifications referencing past experience; the pragmatic answer becomes the specification itself.

### Engineering communications
Emails, Slack posts, RFC comments. Same voice — direct, experience-grounded, willing to take a position, parenthetical humor welcome. Much shorter; skip the narrative scaffolding.

### Internal documentation
Handbooks, onboarding guides, runbooks. Same voice, emphasizing the "why" — documentation explains why things are the way they are, not just how they work. Production anecdotes are especially valuable here, as they give new team members context that code alone cannot.
