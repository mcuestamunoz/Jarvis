# Design — Jarvis spatial board UI

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Status:** DESIGN NARROWED — board-first. RAG and satellite product **out**. Await confirmation of craft bar (Q1–Q11).  
**Type:** Product-surface design. **Not** an Implementation Contract. **No `src/`.**

**Parents:**
- Engineer vision: 1 card = 1 component; then 2026-09-05: *solo pizarra* (mover, resize); RAG y el resto se omiten; **trabajar la pizarra muy bien, es clave**
- Informe origen (motor): [interactive-board-review](/Users/marccuestamunoz/.cursor/projects/Users-marccuestamunoz-repos-multiagent-problem-solving/canvases/interactive-board-review.canvas.tsx)
- Canvas de este diseño: [jarvis-spatial-board-design](/Users/marccuestamunoz/.cursor/projects/Users-marccuestamunoz-Desktop-Ingenieria-Projects-Jarvis/canvases/jarvis-spatial-board-design.canvas.tsx)

**Baseline:** Structure block CLOSED @ 2229 · thickness arms B2 CLOSED @ suite **2286** · PRODUCT_SCOPE v1 = CLI + MCP

---

## 0. Thesis (narrowed)

The product slice is an **interactive infinite board** with component cards.

- **In:** pan, zoom-to-cursor, minimap, **drag**, **resize** (four corners), cards that show component data + declared geometry scalars.
- **Out:** RAG, generación IA, fases, templates sprint/roadmap, Continuity/ERF chrome, catalog-assist, multiplayer, edges, Conversation Engine, CAD.

SolveSphere is a **viewport donor**, not a product donor. Copy Capa A (transform / drag / resize / minimap). Do not copy Capa C. Do not copy the 743-line god board.

The craft is the board itself. Payload (what a card says) is secondary until the motor is trustworthy at every zoom.

---

## 1. Authority

```text
state.json                 ← engineering truth (unchanged)
projector                  ← cards appear; does not own x/y/w/h after first layout
InfiniteCanvas             ← the product: pan/zoom/drag/resize/minimap
spatial_layout.json        ← presentation only: id → {x,y,width,height}
```

Moving or resizing a card **must not** write mass, SKU, PASS, or properties. Layout persist is the only board write.

CLI / writers remain the engineering mutation surface.

---

## 2. Interaction contract (the thing to get right)

Initial layout: deterministic recipe (4/4 lanes) so a new project is not a blank world. After that, the Engineer **owns placement**: drag and resize persist.

| Gesture | Behavior |
|---|---|
| Wheel on world | Zoom to cursor (world point under pointer invariant) |
| Drag empty world | Pan |
| Drag card body / grip | Move card; preview every mousemove; commit `x,y` on mouseup |
| Drag corner handles | Resize; min size; zoom-aware; commit `width,height` |
| Click minimap | Pan viewport there |
| Fit control | `fitToScreen` **wired** (exists unused in origin) |

SolveSphere bugs we **do not** import: RAG card `useDrag(zoom=1.0)`; Ctrl+R vs browser refresh; CSS handles as global soup; zero UI tests.

---

## 3. Quality bar (Q1–Q11) — this *is* the work

The board is “done well” only if these hold. This is the Implementation Contract seed, not decoration.

| # | Bar | Why |
|---|---|---|
| **Q1** | Zoom-to-cursor: world point under pointer does not jump | Figma-class viewport; origin’s best idea |
| **Q2** | Drag follows cursor at **any** zoom | Origin bug: RAG path used zoom 1.0 |
| **Q3** | Resize NW/NE/SW/SE zoom-aware; min width/height | Engineer asked “hacer más grande” |
| **Q4** | Pan only from empty world; cards and handles do not start pan | Origin already ignores clicks on cards/buttons — keep and test |
| **Q5** | Minimap shows viewport rect; click navigates | Origin has this |
| **Q6** | Fit-to-screen is a real control | Origin implemented, unused |
| **Q7** | Layout `{x,y,w,h}` persists; reload restores | Otherwise move/resize is a toy |
| **Q8** | Unit tests: `screen→world`, drag delta / zoom, resize delta / zoom, zoom invariant | Origin has **zero** frontend tests of this module |
| **Q9** | No RAG, no templates, no phase sidebar, no Ctrl+R hijack, no “collaborate realtime” copy | Engineer omit |
| **Q10** | Handle / minimap CSS scoped to the board | Origin is global `index.css` |
| **Q11** | Drag/resize: local preview → commit → rollback if persist fails | Origin `useBoardState` pattern; keep, without React Query coupling |

Until Q1–Q8 are green, do not add glyph-2D, slots, edges, or catalog pick from the card.

---

## 4. Cards (payload, not the craft)

Still **1 ComponentSpec = 1 card**. Body: identity + all properties + geometry scalars if present.

v0 may even boot with **fixture nodes** to prove Q1–Q8 before the Python projector exists. Binding `state.json` is the next slice after the motor is trustworthy.

Deferred (not this board-first slice): ghost ESC slots (was U6), 2D glyphs (was U7), Continuity/ERF chrome, lanes as labeled regions (nice, not blocking).

---

## 5. Build order (after Buy)

1. **Tests of transform math** (new; not present in SolveSphere).
2. **InfiniteCanvas** with fixture cards: pan / zoom / drag / resize / minimap / fit / layout persist.
3. Projector `ProjectState → SpatialNode[]` + real cards.
4. Only then: extras.

Do **not** start with a Python projector IC while the viewport is untested. Engineer named the board as the key.

---

## 6. Buy (updated)

| # | Decision | Status |
|---|---|---|
| **U0** | Card = component | **LOCKED** |
| **B1** | Slice = board only (RAG and satellite product out) | **LOCKED** this message |
| **B2** | Drag + resize in the first slice | **LOCKED** this message |
| **B3** | Persist layout (`x,y,w,h` only) | **LOCKED** — required by B2 |
| **U1** | Ship as local visor (CLI stays engineering surface) | Lean **yes visor**; PRODUCT_SCOPE still needs ★ to call it “product v1” |
| **U4** | Extract Capa A vs copy | Lean: copy-or-extract **motor only**, then make it correct (Q8) |
| **U5** | Edges | **Out** of this slice |
| **U6 / U7** | Ghost slots / 2D glyph | **Deferred** until Q1–Q8 |

---

## 7. Explicit non-goals (this slice)

RAG · generate-at-100% · phase sidebar · sprint templates · Continuity/ERF as cards · catalog pick from card · task CRUD / completed checkbox · FastAPI / JWT / Supabase · multiplayer · pinch-zoom · multi-select · edges · CAD/FEA/MEASURE · Conversation Engine · Ctrl+R shortcut · inventing geometry

---

## 8. Next

Confirm Q1–Q11 as the bar. Then Investigation Contract for the **viewport motor** (math + gestures + persist layout), with tests, using fixture cards. Projector is slice 2.
