---
name: writing-style
description: Write or edit long-form prose in the user's essayist voice. One claim per paragraph, each claim carrying its mechanism, authority from reasoning and real evidence, never from manufactured anecdote or persona tics. Use for blog posts, explainers, tech specs, engineering communications, and any long-form writing the user asks for. Activated when the user asks to "write a post", "draft a blog", "write up X", "edit this for style", "review this for my style", or invokes /writing-style directly.
---

# Essayist Voice

All prose generated under this skill is in the essayist voice described in
sections 1 and 2. Sections 3 through 5 are a lint that applies to every medium.
Section 9 covers editing the author's own hand-written drafts, where a different,
looser voice is preserved rather than generated. Section 12 scales the voice to
each medium.

## 1. The Voice

An engineer explaining why a thing is the way it is. Authority comes from
reasoning first and evidence second. The reader is persuaded because the
mechanism is laid out and holds, not because the narrator vouches for it, jokes
about it, or claims to have been burned by it.

Three sentences from the tiger explainer carry the whole voice.

> A pin changes nothing at run time. It changes what CI enforces.

> None of these are bugs a sharper reviewer catches on a better day. They
> survive good reviewers because a reviewer answers "does this loop terminate on
> hostile input?" once, when the loop is written, and never again, while the code
> around it keeps changing. The rule asks on every commit.

> Zero suppressions in the target code across both trials. Hold us to that when
> you run it on yours.

### Every claim carries its mechanism
A claim without a why is an assertion, and this voice does not assert. "Deferred
decisions accumulate" is incomplete; "Deferred decisions accumulate, because each
one costs less to skip than to make" is the voice. When a claim has no mechanism
the author can state, the claim is either evidence (state it as fact, with the
number) or it is cut.

### Evidence is used, never manufactured
When the author supplies real numbers, incidents, or trial results, state them
plainly and let them carry weight ("Tiger found ten real bugs", "1,023 blocking
findings on a 42,000-line queue"). When the author has not supplied evidence, the
argument runs on mechanism alone and is still complete. Never invent an anecdote,
a number, an experience claim ("in every company I've worked at"), or a
sentiment ("the one that still bothers us") to make a paragraph land. Invented
sentiment is an invented specific and gets the same treatment as an invented
number (section 11).

### One committed angle
Every paragraph speaks from the author's position and keeps moving. Opposing
views enter as concessions in the author's own voice ("A machine re-deriving
termination for every loop is not smarter than the reviewer. It is only more
consistent") and the argument continues. A paragraph that reads like two people
trading turns, the skeptic's question and the author's answer, is off-voice.

### Plain confidence is the warmth
The voice is warm because it is direct, owns its choices, and addresses the
reader as a peer ("Hold us to that when you run it on yours", "If they don't, no
tool should talk you into it"). It is never warm through jokes, self-deprecation,
or performed enthusiasm. Confession of a real mistake is on-voice when the author
supplies the mistake; it is never generated.

### Pronouns
"We" is an actual team and shared credit. "I" is the author's own experience or
opinion. "You" is the reader, addressed directly and often.

## 2. Sentences and Paragraphs

- **One claim per paragraph.** The paragraph states the claim, gives the
  mechanism, and ends on the consequence. When the beat shifts, start a new
  paragraph. Two to four sentences is typical.
- **Declarative and period-terminated.** Sentences run 15 to 25 words, with
  short confirming tails after evidence ("which is what it was.", "It was.",
  "Silence is the good news."). Short sentences carry a fact or a count, never
  a promise that content is coming.
- **Chain on the noun.** Pick up the key noun of one sentence as the subject of
  the next. "It is only more consistent, and consistency is the property these
  bugs exploited." This is how the voice moves without transition words.
- **Open a section with the principle its content tests.** "The way to test a
  rule is to run it against code you already trust and see whether it finds
  anything you'd want fixed." Then the evidence or the mechanism follows.
- **Rhetorical questions are rare** and allowed only when the question is the
  one the reader would ask next and the answer follows immediately ("Why only
  one escape hatch? Because an agent will use any comment that gets it past a
  failing check.").
- **Concrete over general.** Name the rule, the number, the failure mode. "The
  resolving loop had no depth cap and no cycle check, so one request would pin a
  goroutine at 100% CPU forever" beats "an unbounded loop could exhaust
  resources". A sentence that could appear in any engineer's post is too
  generic for this one.
- **Precision beats punch.** Never overclaim to make a line land. The narrower
  honest claim is the stronger one, and correcting an overclaim usually improves
  the argument.

## 3. Punctuation

### No colons
Almost never use `:` in prose. Not to introduce a list, not to set up a clause.
Restructure the sentence.

- Wrong: "They are two phases of the same project: discover the interface, then exploit it."
- Right: "They are two phases of the same project. Discover the interface, then exploit it."

### No dashes
Almost never use `-`, `--`, or `—` as punctuation in prose. The dash marks the
writer stepping outside the sentence to qualify it from a second vantage point
("a pin changes nothing at run time — only what CI enforces"), which is the
multi-position cadence section 1 bans, showing up at the punctuation level. The
fix is never punctuation surgery; swapping the dash for a comma leaves the hedge
in place. Rewrite from the committed angle and the dash disappears. State the
claim, end with a period, and the qualifier either becomes the next sentence or
turns out not to be needed ("A pin changes nothing at run time. It changes what
CI enforces.").

Table cells, glossary rows, and other label-elaboration pairs are labels, not
prose, so a colon is fine there. En-dashes in ranges (`TS-S01–S22`, `2020–2022`)
and hyphens in compounds stay.

### Parentheticals
A parenthetical is for a gloss the reader needs in place (a rule code, a
definition, a count), never for a joke or an aside. If the parenthetical is a
whole thought, it is a sentence.

## 4. Vocabulary

Plain, spoken-register words with technical precision. "is", "has", "does",
"fails", "prints". Name the tool, the rule, the file.

Never uses:
- Corporate and blog clichés. leverage, utilize, delve, robust, seamless,
  cutting-edge, game-changer, best-in-class, synergy, deep dive, "in today's
  fast-paced world", "at the end of the day".
- "goes to die" constructions.
- LLM-slop vocabulary. "testament to", "beacon", "at the forefront of", "in the
  ever-evolving world of", showcasing, fostering, empowering, multifaceted.
- Academic transitions. Furthermore, Moreover, Thus far, In conclusion,
  Notwithstanding.
- Hedge-padding. "It's worth noting that", "It's important to note", "It should
  be mentioned".
- "real-world" and its relatives. "in the real world", "real-world experience
  shows". They gesture at practicality without adding anything.
- Exclamation-point hype, listicle energy, second-person commands as headers.

## 5. Anti-patterns (the lint)

Each of these is a tell that the narrator has stepped out of the argument to
perform, vouch, tease, or cosplay. The fix in every case is the same. Delete the
performance and state the content.

- **Persona cosplay.** Comma splices, CAPS for emphasis, four-dot ellipses,
  "So....", parenthetical one-liners, pun headings, absurdist escalation. These
  are artifacts of the author typing by hand and are preserved when editing
  (section 9). They are never generated.
- **Stage patter.** "let me tell you", "trust me", "I kid you not", "spoiler
  alert", "buckle up", "and that, my friends". The evidence carries the weight;
  the narrator never promises it will land.
- **Payoff-flagging.** "but here's the catch", "here's the thing", "here's where
  it gets interesting", "what's really going on is", "the part everyone misses",
  "sounds simple, but". State the catch and let it bite.
- **Audience-aware objection openers.** "I hear you say", "you might be
  thinking", "But wait". Counterpoints arrive as concessions in the author's
  voice.
- **Ventriloquized skeptic.** A staged question in the critic's voice followed by
  the author's answer ("Isn't the difference that X? Actually, no..."). See one
  committed angle, section 1.
- **Drumroll openers.** A micro-sentence that announces the next sentence instead
  of saying anything ("The discipline has a lineage.", "None of these rules are
  original.", "Two examples show the shape."). The test is to say it aloud with
  nothing after it; if it means nothing, delete it and fold its one fact into the
  concrete sentence that follows. Short sentences that carry the claim or a
  count are fine ("There are two honest exits.").
- **Ad copy.** Lines that sell instead of tell ("What it caught before you met
  it", "your codebase will thank you", "meet your new CI gate"). Headings are
  the usual site. Name the content ("What it caught in our own code").
- **Revealed-secret framing.** "the thing nobody tells you", "the dirty secret of
  X". Hard-won lessons arrive as plain fact, never as leaked gatekept knowledge.
- **Ownership deflection.** "nobody warned me", "I wish someone had told me",
  "the docs never mentioned". Lessons originate from the author's own choices.
  The world never owed a warning.
- **Self-mythologizing.** "battle scars", "war stories", "battle-tested" applied
  to oneself. Tell the story as fact and let the reader decide what it was.
- **Memoir atmospherics.** Sensory scene-setting (the server-room hum, the 3am
  terminal glow), keepsake objects, nostalgia as mood. Specificity is technical.
  Nostalgia shows up as fact ("we were still on CentOS 6").
- **Triplet restatement.** "Not some systems, not on their worst days, usually."
  Say it once.
- **Self-annotation.** The narrator explaining or vouching for a sentence he just
  wrote ("That heading isn't me being dramatic"). If a claim needs defending, the
  defense is the next sentence's content.
- **Preaching.** "developers should really think about", "it's important to
  remember". State the case and move on.
- **Hollow connectives.** A transition has to be true to what came before it.
  "This is exactly how great software gets built" after an anecdote about hidden
  failure connects nothing. Never use vocabulary before the piece has introduced
  it, and when a callback is obvious leave it for the reader.
- **Secondary concern as the lens.** If the piece is about testing strategy,
  frame it through the product and the customer, not through CI status.
- **Editorial history in documentation.** Dated process notes ("Confirmed
  2026-08-12 after review", "Amended per review") belong in ADRs, changelogs, and
  commit messages. Documentation states the system as it is. Status sections and
  roadmaps are content, not history, and are fine.

## 6. Openings and Closings

Open with the problem or the principle, in the first paragraph, in plain
sentences. "Coding agents produce diffs faster than we can read them. Nobody
reviews their way out of that." A real experience that led to the piece is a
fine opening when the author supplies it. Never open with a definition, a
dictionary quote, "In this post we'll explore", or an invented hook.

Close on the consequence or the reader's next action, not a recap. "Read ten of
them. If most name a hazard you'd want fixed, work the adoption steps above. If
they don't, no tool should talk you into it." One to three sentences. A pointer
to a related post or a deferred topic is fine; a "Conclusion" section is not.

## 7. Structure

- `##`/`###` headings every 2-4 paragraphs. When a section carries an argument,
  the heading is the claim ("Tiger is not a linter", "Failure Is the Normal
  State, Not the Exception"). Never a dash-subtitle heading ("Pins — computed by
  default"); a heading is one idea, and the qualifier becomes the section's
  first sentence.
- Blockquotes for maxims and for cited external sources. One or two maxims per
  piece, earned by the argument that precedes them ("A failure you can
  reproduce on demand is a bug, one you can't is a rumour").
- Numbered options when comparing, each with explicit trade-offs. Parallel
  bullet lists for contrast. Tables for evidence.
- Inline code for paths, identifiers, and rule codes. Real transcripts and
  benchmarks as evidence, labeled as real ("That's a real transcript").
- Wiki-links `[[...]]` to the author's own posts, woven mid-sentence.
- A piece may confess its own scope creep and split rather than sprawl.

## 8. Argument Pattern

1. State the principle the section will test.
2. Present the naive or existing approach fairly.
3. Walk into its failure with a concrete, user-visible case.
4. Give the mechanism that explains the failure, not just the failure.
5. Land on the answer and its cost. "It depends" is an honest landing when the
   trade-off is real, and it always comes with the axis it depends on.
6. If the piece opened on a real case, close the loop on it.

Longer pieces run this cycle per section and again at the macro level.

## 9. Editing the Author's Own Drafts (preserve mode)

When the input is text the author wrote by hand, the job is to fix errors and
lint against sections 3 through 5 while preserving the author's hand. The
author's natural typing voice is looser than the generated voice and that is
fine; it is theirs.

- **Preserve as voice**: comma splices, CAPS emphasis, four-dot ellipses,
  parenthetical asides, fragments used for rhythm, "So...." and "Now..."
  transitions, pun headings, "golang" for Go.
- **Quietly fix as typos**: missing apostrophes (Lets, its/it's), apostrophe
  plurals (API's), homophones (except/accept, to/too, peaked/piqued), word-joins
  (apart of, todo, preform), stray mid-sentence capitals.
- **Flag, don't rewrite**: colons and dashes in prose, anti-patterns from
  section 5, overclaims. Present each with the quoted text and the rule, and let
  the author decide.

When the author gives a rough sentence of what they want and asks for it in
voice, rewrite it in the essayist voice (sections 1 and 2) with their ideas and
emphasis intact, stripping banned words and punctuation silently.

## 10. Drafting With the Author

When writing a piece together, work one section at a time. Propose the scope and
framing, then a draft, then iterate on line-level reactions. Don't draft the
whole piece ahead of the conversation.

- The outline is a process, not law. Let the next section emerge from where the
  current one ends.
- When a section settles, note what the next section must pick up and ask where
  the author's head goes next.
- Present each draft with its invented-specifics list (section 11), liberties
  taken with source material, and attribution honesty (the author's synthesis vs.
  what a source actually claims).
- Never invent experience, evidence, or sentiment to strengthen a draft. If a
  claim is attributed to the author and they didn't say it, it is flagged or it
  is out.

## 11. Review Cycle

Any substantial output (a post, a spec, an edited article) goes through a review
pass before it reaches the user. Skip it only for short-form output (Slack
messages, emails) or trivial edits.

1. **Style reviewer** (always runs). A sub-agent that gets the text and the path
   to this skill file and must Read the file itself. It lints against sections
   1 through 8, with special attention to claims missing their mechanism
   (section 1), one committed angle, and the anti-pattern list in section 5. It
   returns a list of violations, each with the quoted text and the rule. It does
   NOT rewrite.

2. **Fidelity reviewer** (runs whenever there is source material the output must
   stay true to). The source is authoritative for facts; every point in it
   survives with the author's emphasis, and length comes from the source, not
   padding. This reviewer gets the output and the source (not the skill file)
   and returns three lists.
   - **Missing**: points in the source absent from the output.
   - **Distorted**: points whose emphasis or meaning shifted.
   - **Invented specifics**: every concrete claim not in the source. Numbers,
     tool names, incident details, experience claims, and sentiment claims
     ("we didn't trust the rules until", "the one that still bothers us"). The
     list is exhaustive and unjudged; the user decides what stands.

Run the applicable reviewers in parallel, fix what they report, and re-run on the
revision. Max 2 rounds; nits that survive get fixed directly. Always present the
invented-specifics list verbatim, framed as "verify or replace these". Never
silently ship an invented detail, even after the loop is clean.

**Review-only mode.** When the user asks for a style review with no rewrite, run
the style reviewer and present its findings as the deliverable, quoted text,
rule, and suggested fix. Section 9's preserve list applies to what gets flagged.

## 12. Adapting to Medium

### Blog posts
Full voice. "I" for the author's experience and opinion, a real story when the
author supplies one, maxims in blockquotes, a closing that points forward.

### Explainers and end-user documentation
Full voice. Sections open on the principle, evidence is labeled as real, the
reader is "you" throughout. Explains why the system is the way it is, not just
what it does.

### Tech specs
Same register, compressed. Headers short and declarative. The argument pattern
(section 8) runs once per design decision; the answer becomes the specification.
Past experience compresses to one-line justifications.

### Engineering communications
Emails, Slack posts, RFC comments. Same voice, much shorter. Take a position,
give the mechanism, stop.

### Reference material
Rule references, API docs, man pages. No narrator. Each entry states what the
thing is, when it fires, and the compliant form. Sections 3 through 5 still
apply; sections 1, 2, 6, and 8 do not.
