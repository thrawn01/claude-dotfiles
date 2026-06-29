---
name: html-explainer
description: >-
  Create a standalone HTML explainer that teaches a thing visually, from the
  outside in — leading with the perspective of the person who uses or calls it
  (a UI's end user, a library's caller, a service's API consumer, an
  implementation's invoker) before any internal detail. Use when asked to
  "explain X visually", "make an explainer for X", "write a visual explainer",
  "explain this from the user's perspective", "render an explanation of X as a
  page", or to walk through how something behaves/works for the people who depend
  on it. Self-contained (bundles its own dark "dimmed-terminal" template); if the
  project has an html-docs skill or docs/design.md, prefer those tokens. Do NOT
  use for plain reference docs with no teaching/perspective angle, or for PRDs/
  tech specs.
---

# HTML Explainer

An explainer is documentation that **teaches**, and it teaches from the **outside
in**. The reader meets the thing the way its users meet it — what they ask of it,
what they get back, how it behaves — *before* they meet how it is built. This
keeps the explanation product-focused: it describes outcomes for the caller, not
the internal machinery, even when the subject *is* the machinery.

This skill owns the **perspective discipline** (below) and a set of **visual
diagram patterns** (`diagrams.md`). It bundles its own styling so it works in any
project, but defers to a project's own house style when one exists.

## The one load-bearing rule

**The caller's perspective always comes first. Internals always come after.**

Everything else here is guidance you can adapt per subject. This rule is not. If
you catch yourself opening with a data structure, a class diagram, or "the system
is composed of…", stop — you have started inside. Back up to the boundary.

### Who "the user" is, by subject

The skill explains many kinds of things. Identify the caller first:

| Subject | "The user" is… | Lead with… |
|---|---|---|
| A UI | the person clicking | what they see, do, and get — screen by screen |
| A library / package | the developer writing code against its surface | the exported functions, the call, the return |
| A service / API | the consumer making requests | the endpoint, the request, the response, the errors |
| An implementation | whoever calls *into* this code | the contract it honors and the outcome it produces |
| A protocol / format | the party producing or consuming it | a real message and what each side does with it |

Even when the *requested topic* is internal (e.g. "explain the state machine
inside the packfile assembler"), open with what the caller hands in and what
comes back out — then descend into the internal states. The internals are framed
as *how the promised outcome is kept*, never as the starting point.

## Input

**The user describes the thing to explain.** You do not autonomously reverse-
engineer a subsystem to write this — the framing comes from their description.

- If they point you at code, a spec, or an `openapi.yaml`, read it **only** to make
  examples concrete and correct (real signatures, real request/response shapes).
- Ask clarifying questions **only when the user-first framing is genuinely unclear** —
  specifically: *who the caller is*, *what outcome they care about*, or *the
  audience's level*. One or two questions, then write. Do not run a full interview.

## Drafting, outside in

1. **Fix the perspective.** Name the caller (table above) and the single outcome
   they care about most. This becomes the `<p class="lead">`.
2. **Open with a picture.** The first visual should be a diagram of the boundary —
   what the caller sends in / gets back — not internal structure. See
   `diagrams.md` (`.boundary`, `.flow`).
3. **The user-first explanation.** Walk the caller's experience: the call/click,
   the result, the common variations, the errors they can hit. Make it concrete
   with annotated examples (`<pre>` request/response, real signatures). This
   section must stand on its own — a reader who stops here understands how to
   *use* the thing.
4. **Then internals, if relevant.** Only after the above, descend. Frame every
   internal detail as *how the promised outcome is kept*. Internal state walks,
   sequence diagrams, and data structures live here — never above. If the request
   was specifically about internals, this is where the depth goes, but it still
   follows the caller-facing section.
5. **Color-code the boundary.** Convention: **blue (`--accent`)** marks what the
   caller touches (the surface); **muted/green** marks what is internal. Carry
   this through diagrams and pills so "outside vs inside" is visible at a glance.

## Visuals

Lead with diagrams; prose supports them, not the reverse. The explanation is
carried by:

- **Diagrams** — SVG/CSS flow, state-machine, boundary, and sequence patterns.
  Copy them from **`diagrams.md`**, which defines them in terms of the bundled
  template's design tokens. Add that CSS block to the template's `<style>`.
- **Annotated examples** — real request/response bodies, function signatures,
  before/after blocks. Use the template's `<pre><code>` with `<span class="cmd">`
  and `<span class="muted">` for emphasis.

No JavaScript interactivity, no animation libraries — the house style is flat and
mostly static. A state machine is drawn, not animated.

## Producing the file

1. **Pick the styling source:**
   - If the project has an `html-docs` skill or a `docs/design.md`, follow it —
     copy *its* `template.html` and keep *its* tokens; this skill's diagram
     patterns still apply (map the colors to the local token names).
   - Otherwise use the bundled template:
     `cp ~/.claude/skills/html-explainer/template.html <target>.html`.
2. **Keep the `<style>` block verbatim** — it is the design system. No CSS
   framework, no web fonts. Then **append the diagram CSS** from `diagrams.md`
   (additive, built only on existing `var(--…)` tokens).
3. **Write the body** following the outside-in order above, using the template's
   component vocabulary (`.lead`, `.grid2`/`.card`, `.callout`, `.pill`,
   `.layers`, `<pre>`, `<table>`) plus the diagram snippets. Single centred
   column, no sidebar; navigation is the heading structure.
4. **Footer**: note what the explainer was generated from.
5. **Host for review** (the template is a single self-contained file — just serve
   its directory):
   ```bash
   cd <dir with the .html>
   peep -p 8090     # then open http://localhost:8090/<file>.html
   ```
   Run it in the background and confirm with
   `curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/<file>.html`
   (expect 200). If `peep` isn't installed, tell the user the file path so they
   can open it directly.

Default target: write beside the source it explains (e.g.
`docs/<thing>-explainer.html`), or a scratch/temp dir for a quick throwaway.
Confirm the path if it isn't obvious.

## Smell test (you have drifted inside if…)

- The first heading or first diagram is about architecture, not about what the
  caller gets.
- You describe a struct/table/class before describing the outcome it produces.
- The reader has to understand the implementation to understand how to *use* the
  thing.
- The word "internally" appears before the reader has seen a single call,
  request, or screen.

Any of these → back up to the boundary and lead with the caller.
