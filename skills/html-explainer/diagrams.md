# Explainer diagram patterns

Copy-paste visual patterns for `html-explainer`. Flow, state, and sequence
diagrams render through Mermaid, which the bundled `template.html` already
loads and themes to match the house style — no extra setup needed beyond
pasting the `<div class="mermaid">` block. The boundary and tree patterns are
plain HTML/CSS and need no script.

**Color convention:** blue (`--accent`) = the surface the caller touches; green
(`--accent-2`) = internal mechanism; muted = passive/internal detail. Keep this
consistent so "outside vs inside" reads at a glance. In Mermaid diagrams, apply
it with `classDef`/`class` as shown below.

Mermaid needs network access to load from `cdn.jsdelivr.net` — the explainer is
no longer usable fully offline. If that matters for a given audience, say so in
the footer.

## 1. Boundary (what the caller sees vs what's inside)

The first diagram in most explainers. Outer = the surface; inner (dashed,
dimmed) = the internals the caller never touches. Plain CSS, no Mermaid.

Append once to the template's `<style>` block:

```css
  .boundary { border: 1px solid #58a6ff55; border-radius: 10px; background: #58a6ff0a; padding: 1rem; margin: 1.5rem 0; }
  .boundary > .cap { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); font-weight: 700; margin-bottom: .6rem; }
  .boundary .inner { border: 1px dashed var(--border); border-radius: 8px; background: var(--panel); padding: .9rem; }
  .boundary .inner > .cap { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: .5rem; }
```

```html
<div class="boundary">
  <div class="cap">What the caller sees</div>
  <p class="muted">One call in, one typed result out — errors are returned, never panicked.</p>
  <div class="inner">
    <div class="cap">Inside (not the caller's concern)</div>
    <p class="muted">Connection pool, retry/backoff, packfile assembly, side-band framing.</p>
  </div>
</div>
```

## 2. Flow (pipeline / call path)

A Mermaid flowchart. Mark caller-facing nodes with the `surface` class,
internal ones with `inside`. Label edges with what passes between stages.

```html
<div class="mermaid">
flowchart LR
  A["caller\nBegin(ctx)"]:::surface --> B["validate"]:::inside
  B -->|request| C["assemble"]:::inside
  C -->|result| D["caller\n*Result"]:::surface

  classDef surface fill:#58a6ff12,stroke:#58a6ff,color:var(--text);
  classDef inside fill:var(--panel-2),stroke:var(--border),color:var(--muted);
</div>
```

Use `flowchart TD` instead of `LR` for a top-to-bottom sequence (steps, layered
stages).

## 3. State machine

For the internals section — the states an implementation moves through.
Highlight any state the caller can observe with the `surface` class.

```html
<div class="mermaid">
stateDiagram-v2
  [*] --> Idle
  Idle --> Assembling: Begin()
  Assembling --> Done: flush
  Done --> [*]

  class Idle surface
  class Done surface
  classDef surface fill:#58a6ff12,stroke:#58a6ff,color:var(--text);
</div>
```

## 4. Sequence (caller ↔ thing)

A request/response round-trip. Put the caller's participant first so it reads
left to right as "them, then it."

```html
<div class="mermaid">
sequenceDiagram
  participant Caller
  participant Service
  Caller->>Service: POST /v1/repo.fetch
  Service-->>Caller: 200 — packfile stream
  Service-->>Caller: side-band 3 — PackError
</div>
```

## 5. Tree (file / component / call tree)

For showing ownership or hierarchy — which file owns what, which component
renders what, which function calls what. Plain monospace, no Mermaid; box-
drawing characters keep it scannable at a glance.

```html
<pre><code>src/
├── commands/       <span class="muted"># parses user actions</span>
├── sessions/       <span class="muted"># owns session state</span>
└── transport/      <span class="muted"># sends API requests</span></code></pre>
```

Same shape for a component tree or a call tree:

```html
<pre><code>&lt;SessionPage&gt;              <span class="muted">apps/example/src/routes/session.tsx</span>
  useSessionEvents()
  &lt;SessionToolbar&gt;
    &lt;RunSkillButton&gt;      <span class="muted">packages/ui</span></code></pre>
```

```html
<pre><code>submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession</code></pre>
```

Keep only the branches relevant to the point being made — prune anything the
reader doesn't need to answer the question this diagram exists to answer.

## Choosing a diagram

| To show… | Use |
|---|---|
| Surface vs internals (the opener) | Boundary (§1) |
| A call path / pipeline of stages | Flow (§2) |
| Internal states & transitions | State machine (§3) |
| A request/response round-trip | Sequence (§4) |
| Ownership / hierarchy (files, components, calls) | Tree (§5) |
