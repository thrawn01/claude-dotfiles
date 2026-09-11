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

The unit of work is a section: one question the reader arrives with, answered in a
few hundred words. A document is a sequence of sections written in order. Everything
below, the writing, the critique, and the fixing, happens per section, and one pass at
the end looks at the seams between them.

## The reader and the purpose

Every section answers one question the reader arrives with. Before anything is
written, write that question down in one sentence, then list the facts the reader
must have to answer it. That fact list is what the writer receives. It is also what
the critic checks the draft against, so the writer and critic are checking the same
thing.

The reader understands the section if, having read it once, they could explain the
mechanism to someone else in their own words. Write toward that.

## The register

The register is the one Russ Cox uses in his posts on the Go blog and at
research.swtch.com: a knowledgeable colleague explaining a mechanism to working
developers, calmly, in the plainest words that are still exact. Name that register to
the writer and to the critic. It sets rhythm, vocabulary, and tone at once, and it
does so more reliably than any list of rules.

Each section opens by saying what the thing is and what it is for, in one or two plain
sentences, and only then goes into how it works. The mechanism is told in order, cause
before effect, so the reader can follow it once through without backtracking.

A sentence has one joint: one cause and one effect, tied by an ordinary word such as
and, so, because, which, before. A sentence with no joint is a statement, and a run
of statements is a list, not a paragraph. A sentence with two joints is split at the
weaker one, never at both. The halves are not the same length; a long sentence
followed by a short one reads as explanation, and three of the same length read as
bullets. "When the thermostat is set, the furnace runs until the room reaches it, so
the burner cycles less often, instead of running continuously" has three joints. "When
the thermostat is set, the furnace runs until the room reaches it. The burner cycles
less often as a result" keeps the strongest one.

A paragraph covers one stage or one idea, and every sentence after the first needs
the one before it. The second sentence uses a noun the first introduced, or begins
from its consequence, or contradicts it. The test is to shuffle the sentences: if
nothing is lost, the paragraph is a list of statements. "A furnace heats air. A
thermostat is a switch. The furnace is in the basement." shuffles freely, so it fails.

Vocabulary is the literal, everyday word for the thing, and the verbs are the ones a
developer uses about code: fails, returns, blocks, panics, merges, catches, runs. A
technical term appears when there is no plain word for it, and is glossed in passing
the first time, the way "the drain field, a set of perforated pipes laid in gravel
trenches" does it. A figure of speech standing where a fact should be ("the alert
lands on the pager") means the fact is missing; state it ("the alert is sent to whoever
is on call, not to the team channel"). Concrete figures and specific names go in where
they tell the reader something real.

The reader stays out of the sentences. The subject of each sentence is the thing being
explained, the part of it that is acting, or the person who operates it in general. The
writer addresses the reader directly only in a passage that is actually about
something the reader does or chooses, and never as a closing turn tacked onto an
explanation.

The tone is calm, with no rhetorical questions, no jokes, and no diminutives.
Consequences of getting it wrong are stated as facts about the system, such as "an
underproofed loaf comes out dense", because they are part of understanding it.

### Habits to leave behind

A model writing in a borrowed register still brings its own habits. The critic names
each one it finds; the writer removes it. The common ones:

- A throat-clearing opener that announces instead of saying: "It is worth being
  precise about why."
- A short dramatic setup for a contrast: "That works fine for a while."
- The "not X but Y" or "not X. It is Y." contrast pair.
- Emphatic filler: "full stop", "exactly", "even", "simply", "just".
- A rhetorical question standing in for a statement.
- An em-dash aside. There are none in this register; the aside is a sentence or is cut.
- A doubled adjective where one would do: "smaller, simpler".
- A vivid invented specific: "eighteen months later", "a few years", "take down a
  service". These are also invented facts, and the fact rule below applies.
- An imperative to the reader: "Do this for a few years and..."
- A scene standing in for a statement: "A day with tiger is a short loop", "Imagine a
  team that...", "Say you open the editor and...", "here is a function that...". The
  mechanism is stated, then the code is shown. Nobody is placed in a scene.
- An aphorism, a short general truth in memorable form, usually after a setup
  sentence: "Any one of them buys little. But restrictions compose." The pair hides a
  mechanism; write the mechanism.
- A figure of speech doing a verb's job: buys, lands, drifts, surfaces, burns, hides.
  Developers do not say these about code; use the verb for what happens.

## Working from source material

The writer is given facts, never prose. When the source is a spec, a rule table,
notes, or an earlier draft, the facts are extracted from it first, as a plain list
with no sentence structure worth keeping, and only the list reaches the writer. A
writer given prose translates it sentence by sentence and keeps its shape, however
the instruction is worded. A writer given facts writes.

### Where facts come from

A fact comes from a primary source: the code, a run of the tool, a test, the spec, or
something the author said. Each fact on the list names its source in a few words
("golangci.go, Verify"; "run of tiger golangci on a drifted config"; "author, in
chat"). An earlier draft of the same document is not a source. It may supply the
section's question and the order the reader needs things in, but a statement that
exists only in earlier prose is a claim, and it goes on the list as
`[VERIFY: what it says and where it might be checked]` until a source is found or it
is dropped. The critic checks the draft against the list, so a wrong fact on the list
passes every later step; this is the one place an error is not caught downstream.

A fact is a checkable statement with no evaluation in it. "No single restriction is
worth much on its own" is an opinion in the shape of a fact, and a writer given it
produces an aphorism. The fact under it is what each restriction removes from the
analysis and what the analysis can conclude once all of them hold. Keep the mechanism,
drop the evaluation, and when the mechanism is not known, mark it.

A fact is at the granularity the reader needs. A command or mechanism the section
leans on gets facts for what it does, what it reads, and what happens when it is not
satisfied, or the section does not lean on it. One line saying "tiger configures
golangci-lint" produces one sentence that carries more than it explains.

When the list was extracted from anything other than the author's own words, the
author reads it before the writer does. It is twenty lines, and an error found there
costs a minute; the same error in a finished section costs the section.

1. **Read the whole list, then close it and write from understanding.** Do not draft
   fact by fact. The order of the list is not the order of the section.
2. **Order by dependency, not by source.** A fact goes where the reader first needs it,
   which is often mid-sentence in a clause, not in its own sentence.
3. **Use every fact on the list and no others.** The list is what the author decided
   the reader needs. A fact that would help but is not on the list is a question for
   the author, marked in the draft, not a decision for the writer.
4. **Supply the mechanism when a fact gives only the what.** The register needs the
   why. Supply it from another fact on the list or from settled knowledge that the
   critic would accept without looking it up.

### Facts are not made up to fit the narrative

When the explanation wants a fact the list does not give and settled knowledge does
not supply, the gap stays visible. The writer either writes around it, or leaves a
marker in the draft in the form `[VERIFY: what is needed and why]` for the critic and
the user. A smooth paragraph with an invented fact is worse than a paragraph with a
marked gap, because the gap gets fixed and the invention gets published. This
applies to numbers, to causes, to history, and to "typical" behaviour: if the list
does not say a thing is typical, the prose does not either.

## The loop

Three roles, and one agent never holds two. An agent that critiques and then rewrites
anchors on its own list and produces the fact list back in sentences. An agent that
writes and then critiques does not see its own habits. The fact list is written
before the loop by the agent running it, from the sources named above, and the
author sees it first when its source was not the author.

1. **The writer** receives the section's question, the fact list, the register above
   with its samples, and the final text of the sections already written, labelled as
   already said and not to be repeated or redefined. It receives no prose for this
   section. It writes the section fresh.
2. **The critic** receives the draft, the fact list, and the register. It rewrites
   nothing. It answers, in order:
   1. What does the section explain, and does every paragraph advance it? Name any
      paragraph that does not.
   2. Does it open with what the thing is and what it is for, before the mechanism?
   3. Which claims are not on the fact list? Quote each. Which numbers, names,
      identifiers, or quoted lines differ from the list?
   4. Which sentences would the named exemplar not have written? Quote each and name
      the habit, using the list above and anything else it sees. Include any sentence
      a working developer would not say aloud to a colleague about the code, whether
      or not its habit is on the list. Be complete.
   5. Shuffle each paragraph's sentences. Name every paragraph where nothing is lost.
   6. Which sentences put the reader where the system belongs, or address the reader
      as a closing turn?
   7. Does any wording, example, or subject from the samples appear in the draft?
3. **The writer, again,** receives the draft and the critic's list. It changes only
   what the list names and leaves every other sentence word for word. It removes each
   unsourced claim rather than sourcing it.

Two rounds at most. What survives the second round is fixed by hand.

When every section is written, one **seams pass** reads the assembled document once,
start to finish, and reports only: a term used before the section that defines it, a
term defined twice, a fact stated in two sections, and a contradiction between
sections. Fix those by hand.

Writing is not delegated to a sub-agent that has been given prose, and a draft reaches
the user only after the loop.

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
