---
name: writing-prose
description: "Write explanatory prose for a smart reader meeting the subject for the
  first time: newcomer explainers, concept sections, 'how it works' docs, the
  explanatory parts of a README. Use when the user asks to 'explain X', 'write the
  explainer', 'write the overview', 'fill in this section', or hands over a spec, notes,
  or a fact list and wants prose a newcomer can read. Do NOT use for reference
  documents, specs, ADRs, rule tables, or anything that must be complete rather than
  understood; and not for messages, PR descriptions, or standups (use lazy)."
argument-hint: "[what to explain, and where the source material is]"
---

# Explanatory prose

This skill produces prose that explains a thing. The reader is smart, has not seen the
thing before, and wants to understand how it works and why it is the way it is. They
are reading to understand, not to look something up. A reference document exists (or
will exist) for looking things up, and this prose does not try to replace it.

## The reader and the purpose

Every section answers one question the reader arrives with. Before drafting, write
that question down in one sentence, then list the three to five things the reader must
grasp to answer it, in the order they must grasp them. That list is the outline. It is
also the first thing the reviewer checks, so the writer and reviewer are checking the
same thing.

The reader understands the section if, having read it once, they could explain the
mechanism to someone else in their own words. Write toward that.

## The register

Each section opens by saying what the thing is and what it is for, in one or two plain
sentences, and only then goes into how it works. The mechanism is told in order, cause
before effect, so the reader can follow it once through without backtracking.

Sentences are as long as the thought needs and vary in length. A sentence can carry
two or three linked facts when they belong together, and the joints are ordinary words:
and, so, which, because, before. Paragraphs run four to six sentences and each one
covers one stage or one idea.

Vocabulary is the literal, everyday word for the thing. A technical term appears when
there is no plain word for it, and is glossed in passing the first time, the way "the
drain field, a set of perforated pipes laid in gravel trenches" does it. A figure of
speech standing where a fact should be ("the finding lands on the pin") means the fact
is missing; state it ("the finding is reported at the pinned function, not at the line
that changed"). Concrete figures and specific names go in where they tell the reader
something real.

The reader stays out of the sentences. The subject of each sentence is the thing being
explained, the part of it that is acting, or the person who operates it in general. The
writer addresses the reader directly only in a passage that is actually about
something the reader does or chooses, and never as a closing turn tacked onto an
explanation.

The tone is that of a knowledgeable colleague explaining calmly, with no rhetorical
questions, no jokes, and no diminutives. Consequences of getting it wrong are stated as
facts about the system, such as "an underproofed loaf comes out dense", because they
are part of understanding it.

## Working from source material

The source is usually a spec, a rule table, notes, or a list of facts. The prose
absorbs the source and re-presents it; it does not mirror it. A mirror happens when
the source's order becomes the outline and each source item becomes one sentence.
The register cannot survive that, because the register is an order (what it is, what
it is for, then cause before effect) and the source almost never arrives in that order.

1. **Read all the relevant source first, then write from understanding.** Do not draft
   with the source open beside the draft, line by line. Close it, write the section
   from the outline, and come back to the source afterwards to check.
2. **Order by dependency, not by source.** A fact goes where the reader first needs it,
   which is often mid-sentence in a clause, not in its own sentence.
3. **Leave out what does not advance the explanation.** The section is not an
   inventory of the source. A fact that does not help this reader answer this
   section's question stays in the reference document. Omission is expected here, and
   a section that packs in every source fact to be safe has failed.
4. **Supply the mechanism when the source gives only the fact.** A source often states
   a rule without saying why it exists or what happens without it. The register needs
   the why. Supply it from elsewhere in the source or from settled knowledge that the
   reviewer would accept without looking it up.
5. **Check back against the source after drafting.** Every claim traces to the source
   or to settled knowledge. Numbers, names, identifiers, and quoted rules are
   byte-exact copies from the source.

### Facts are not made up to fit the narrative

When the explanation wants a fact the source does not give and settled knowledge does
not supply, the gap stays visible. The writer either writes around it, or leaves a
marker in the draft in the form `[VERIFY: what is needed and why]` for the reviewer
and the user. A smooth paragraph with an invented fact is worse than a paragraph with
a marked gap, because the gap gets fixed and the invention gets published. This
applies to numbers, to causes, to history, and to "typical" behaviour: if the source
does not say a thing is typical, the prose does not either.

## Review before showing a draft

Writing is not delegated. A sub-agent handed a fact list writes a fact list. The
writer drafts; a sub-agent reviews; the draft reaches the user only after review.

Give the reviewer the draft, the outline (the question and the ordered list), the
source material, and this register description. The reviewer answers, in order:

1. What does the section explain, and does every paragraph advance it? Name any
   paragraph that does not.
2. Is it a mirror? If each sentence lines up with a source item in source order, send
   it back.
3. Does every claim trace to the source or to settled knowledge? List any that do not,
   and any number, name, or identifier that differs from the source.
4. Does it open with what the thing is and what it is for, before the mechanism?
5. Does any sentence put the reader where the system belongs ("you already run three
   checks" where the system runs them)?
6. Does any wording, example, or subject from the samples below appear in the draft?
   The samples set the register only; their content never carries over.

Fix what the reviewer finds, then show the user.

## Samples

These two paragraphs set the register. They are on unrelated subjects on purpose.
Match the way they are written; take nothing from what they say.

> A septic tank is a buried, watertight tank that takes everything from a house's
> drains and separates it before the liquid goes out into the soil. Wastewater enters
> at one end and sits still long enough for solids to sink to the bottom as sludge and
> for grease and soap to float to the top as scum. The clear layer in the middle is
> what leaves the tank, through a baffle that stops the scum from following, into
> perforated pipes laid in gravel trenches called the drain field, where it seeps into
> the soil and the soil's bacteria finish cleaning it. Bacteria inside the tank slowly
> digest the sludge, but never completely, so the layer thickens over years. A typical
> household tank needs pumping every three to five years.

> Proofing is the final rise a shaped loaf gets before baking. During that rest the
> yeast keeps feeding on sugars in the flour and releasing carbon dioxide, and the
> gluten network built during kneading traps the gas as small bubbles that expand the
> dough. This is the only chance the dough has to rise. Oven heat kills the yeast
> within the first few minutes of baking, so a loaf that goes in underproofed stays
> dense, because the gas it needed was never produced. A loaf left too long has the
> opposite problem: the bubbles outgrow the gluten's ability to hold them and the
> structure gives way in the oven. Bakers judge readiness by pressing the dough and
> watching how quickly the dent fills back in.
