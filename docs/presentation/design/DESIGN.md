# DESIGN.md — presentation design principles

**Core idea:** slides are a visual aid, not a script. If someone can read the whole slide faster
than you can talk, the slide has failed.

## Rules

- **One point per slide.** Before adding anything, ask: "what's the one thing I want them to
  remember?" Can't say it in one sentence? Split the slide.
- **Text is a caption, not a paragraph.** Headlines state the *takeaway*, not a topic label. Body
  text is short phrases, never full sentences the audience has to read.
- **White space is a feature.** Empty space is what makes the important thing stand out. Don't
  fill a slide just because there's room.
- **Visual hierarchy guides the eye.** Size, color, and position tell the audience what to look at
  first, second, third, without them thinking about it.
- **Story over slide-by-slide facts.** Each slide is the next beat in a story, not an isolated
  fact card. Ask: does this connect to the slide before it?
- **Not everything gets highlighted.** If everything is bold or bright, nothing is. Pick one or
  two things that matter; let the rest fade back.
- **Visually striking, but purposeful.** Design serves the message. A striking layout is good; a
  distracting one is bad.
- **No em-dashes ("—") in slide copy** (Bela, 2026-07-08). Replace with comma, colon, "·" or "→",
  whichever fits. Hyphens inside words (index-based, false-done) stay untouched.
- **Cards and boxes size to their content** (Bela, 2026-07-08). Never stretch cards to equal
  height with dead space at the bottom, and never push a stats/output box to the card's bottom
  edge with a flex spacer: it sits directly beneath the content it belongs to. Leftover space
  collects at the bottom of the slide, not inside boxes.

## Specific to this deck (agent project)

- **The log table is the presentation** (lecturer, Day 1). Numbers from `runs/log.md` and
  `summary.md` go on slides as they are: task, run, verifier, failure class. Never round a
  success rate into a vaguer claim.
- **Show the trace, not the diagram.** A failure is explained with the real screenshot from
  `screens/step_NN.jpg` and the real history line, not with a box-and-arrow sketch.
- **Name the model on the title or design slide.** `qwen3-vl:4b-instruct` (Q4_K_M, Ollama,
  local). This is a stated requirement.
- **Code only as a line, never as a block.** One JSON action (`{"action_type":"click","index":3}`)
  is a slide element; a 20-line function is not.

## Check before finishing the deck

1. Could I present this **without reading the slides out loud**?
2. Does each slide have a clear **"so what"**?
3. Is there **at least one slide I could delete** without losing the story?
4. Are all six required contents covered (use case, agent design, implementation, results,
   findings, failed attempt) and is the model named?

## Design system: TUM

The deck uses the official **TUM corporate design**, ported from the "TUM Design System"
claude.ai/design project into `deck/assets/tum-theme.css` (which imports the tokens in
`deck/assets/tokens/`). Don't invent new colors, fonts, or spacing; use the system so every
slide matches.

- **Colors:** TUM Blue `#0065bd` carries the brand; deep blue `#003359` for dark slides. Black &
  white first, color used sparingly (green/orange are rare accents only). Suggested use here:
  orange `#e37222` for FAIL / the failure class under discussion, green `#a2ad00` for PASS.
- **Type:** Helvetica stack, left-aligned/ragged-right (never justified). Title 44px, body 25px.
- **Chrome:** logo top-right + hairline footer are injected automatically on every slide.

### Slide recipe (copy this into `deck/index.html`)

```html
<section data-background-color="#ffffff">
  <p class="eyebrow">SECTION LABEL</p>
  <h2 class="title">Takeaway headline (not a topic)</h2>
  <hr class="rule" />
  <ul class="bullets"><li>Point<small>optional caption</small></li></ul>
  <aside class="notes">Speaker notes (may be German).</aside>
</section>
```

Building blocks: `eyebrow`, `title` (+`title--xl`), `rule` (+`rule--wide`), `lead`, `sub`,
`bullets`, `cols`/`col`, `keyfig`, `chart`/`bar`, `section-num`. Tones: add class `tum-dark`
(blue) or `tum-deep` (deep blue) to the `<section>` **and** set `data-background-color` to match;
add `center` to vertically center.
