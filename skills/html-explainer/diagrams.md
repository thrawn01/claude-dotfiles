# Explainer diagram patterns

Copy-paste visual patterns for `html-explainer`, built **only** on the bundled
template's design tokens (`var(--accent)`, `var(--panel)`, …) so they match the
house style.

**Color convention:** blue (`--accent`) = the surface the caller touches; green
(`--accent-2`) = internal mechanism; muted = passive/internal detail. Keep this
consistent so "outside vs inside" reads at a glance.

## 1. CSS to add

Append this block to the **end** of the template's `<style>` (just before
`</style>`). Every value derives from an existing token.

```css
  /* ── Explainer diagrams ─────────────────────────────────────────────── */
  /* Flow: boxes joined by arrows. Add .vert for top-to-bottom. */
  .flow { display: flex; align-items: stretch; gap: 0; flex-wrap: wrap; margin: 1.5rem 0; }
  .flow.vert { flex-direction: column; align-items: flex-start; }
  .flow .node {
    border: 1px solid var(--border); border-radius: 8px; background: var(--panel);
    padding: .7rem 1rem; min-width: 120px; text-align: center;
  }
  .flow .node .t { font-weight: 600; font-size: .95rem; }
  .flow .node .d { color: var(--muted); font-size: .82rem; }
  .flow .node.surface { border-color: #58a6ff55; background: #58a6ff12; }  /* caller-facing */
  .flow .node.inside  { border-color: var(--border); background: var(--panel-2); }  /* internal */
  .flow .arrow { display: flex; align-items: center; justify-content: center; padding: 0 .7rem; color: var(--accent); font-size: 1.3rem; }
  .flow.vert .arrow { padding: .35rem 0 .35rem 2.2rem; }
  .flow .arrow .lbl { color: var(--muted); font-size: .72rem; margin-left: .35rem; }

  /* Boundary: the surface (highlighted) wrapping the internals (dimmed). */
  .boundary { border: 1px solid #58a6ff55; border-radius: 10px; background: #58a6ff0a; padding: 1rem; margin: 1.5rem 0; }
  .boundary > .cap { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); font-weight: 700; margin-bottom: .6rem; }
  .boundary .inner { border: 1px dashed var(--border); border-radius: 8px; background: var(--panel); padding: .9rem; }
  .boundary .inner > .cap { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: .5rem; }

  /* SVG diagram wrapper (state machines, sequences) */
  .diagram { width: 100%; margin: 1.5rem 0; }
  .diagram text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: var(--text); }
  .diagram .node-box { fill: var(--panel); stroke: var(--border); }
  .diagram .node-box.surface { fill: #58a6ff12; stroke: #58a6ff88; }
  .diagram .edge { stroke: var(--accent); stroke-width: 1.5; fill: none; }
  .diagram .edge-lbl { fill: var(--muted); font-size: 12px; }
  .diagram .muted { fill: var(--muted); }
```

If a project bundles its own token names, map these to the closest local tokens
rather than inventing new hex values.

## 2. Flow (pipeline / call path)

Horizontal boxes joined by arrows. Mark caller-facing boxes `.surface`, internal
ones `.inside`. Use a labeled arrow to name what passes between stages.

```html
<div class="flow">
  <div class="node surface"><div class="t">caller</div><div class="d">Begin(ctx)</div></div>
  <div class="arrow">→<span class="lbl">request</span></div>
  <div class="node inside"><div class="t">validate</div><div class="d">internal</div></div>
  <div class="arrow">→</div>
  <div class="node surface"><div class="t">caller</div><div class="d">*Result</div></div>
</div>
```

Add `class="flow vert"` for a top-to-bottom sequence (steps, layered stages).

## 3. Boundary (what the caller sees vs what's inside)

The first diagram in most explainers. Outer = the surface; inner (dashed, dimmed)
= the internals the caller never touches.

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

## 4. State machine (SVG)

For the internals section — the states an implementation moves through. Keep nodes
on a grid; route edges with straight or simple curved paths. Highlight any state
that is observable to the caller with `.surface`.

```html
<svg class="diagram" viewBox="0 0 640 200" role="img" aria-label="state machine">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" fill="var(--accent)"/>
    </marker>
  </defs>
  <!-- nodes -->
  <g>
    <rect class="node-box surface" x="20"  y="80" rx="8" width="120" height="44"/>
    <text x="80"  y="106" text-anchor="middle">Idle</text>
    <rect class="node-box" x="260" y="80" rx="8" width="120" height="44"/>
    <text x="320" y="106" text-anchor="middle">Assembling</text>
    <rect class="node-box surface" x="500" y="80" rx="8" width="120" height="44"/>
    <text x="560" y="106" text-anchor="middle">Done</text>
  </g>
  <!-- edges -->
  <path class="edge" d="M140 102 H260" marker-end="url(#arrow)"/>
  <text class="edge-lbl" x="200" y="94" text-anchor="middle">Begin()</text>
  <path class="edge" d="M380 102 H500" marker-end="url(#arrow)"/>
  <text class="edge-lbl" x="440" y="94" text-anchor="middle">flush</text>
</svg>
```

Notes: `marker-end="url(#arrow)"` puts the head on each edge; reuse the single
`<defs>` per SVG. For a self-loop, draw a small `c`-curve back to the same node.
Size the `viewBox` to your content and let `width:100%` scale it.

## 5. Sequence (caller ↔ thing)

Two (or three) lifelines with messages crossing between them — ideal for an
API/service round-trip. Caller lifeline on the left, in accent.

```html
<svg class="diagram" viewBox="0 0 560 220" role="img" aria-label="request sequence">
  <defs>
    <marker id="seqarrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" fill="var(--accent)"/>
    </marker>
  </defs>
  <!-- lifelines -->
  <text x="100" y="24" text-anchor="middle" fill="var(--accent)">caller</text>
  <text x="460" y="24" text-anchor="middle" class="muted">service</text>
  <line class="edge" x1="100" y1="36" x2="100" y2="200" stroke-dasharray="4 4" stroke="var(--border)"/>
  <line class="edge" x1="460" y1="36" x2="460" y2="200" stroke-dasharray="4 4" stroke="var(--border)"/>
  <!-- messages -->
  <path class="edge" d="M100 70 H460" marker-end="url(#seqarrow)"/>
  <text class="edge-lbl" x="280" y="62" text-anchor="middle">POST /v1/repo.fetch</text>
  <path class="edge" d="M460 130 H100" marker-end="url(#seqarrow)"/>
  <text class="edge-lbl" x="280" y="122" text-anchor="middle">200 — packfile stream</text>
  <path class="edge" d="M460 180 H100" marker-end="url(#seqarrow)"/>
  <text class="edge-lbl" x="280" y="172" text-anchor="middle">side-band 3 — PackError</text>
</svg>
```

## 6. Before / after

Reuse the template's `.grid2` + `.card`. Tint the cards to contrast old vs new.

```html
<div class="grid2">
  <div class="card"><h4>Before</h4>
    <pre><code>resp, err := c.Do(req)
// caller parses raw bytes, handles framing</code></pre></div>
  <div class="card"><h4>After</h4>
    <pre><code>pack, err := client.Fetch(ctx, ref)
// typed result; framing handled for you</code></pre></div>
</div>
```

## Choosing a diagram

| To show… | Use |
|---|---|
| Surface vs internals (the opener) | Boundary (§3) |
| A call path / pipeline of stages | Flow (§2) |
| Internal states & transitions | State machine (§4) |
| A request/response round-trip | Sequence (§5) |
| A change in the caller's experience | Before/after (§6) |
