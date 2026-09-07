# Investigation Contract — Spatial board product limits

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_spatial_board_product_limits.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ B3 · IC READY  
**Review:** [investigation_review_spatial_board_product_limits.md](investigation_review_spatial_board_product_limits.md)  
**Report:** [investigation_report_spatial_board_product_limits.md](investigation_report_spatial_board_product_limits.md)  
**★:** [engineer_ratification_spatial_board_product_limits.md](engineer_ratification_spatial_board_product_limits.md)  
**IC:** [implementation_contract_spatial_board_honest_absence_b3.md](implementation_contract_spatial_board_honest_absence_b3.md)  
**Parents (do not re-derive):**
- Design (locked): [design_spatial_board_ui.md](design_spatial_board_ui.md) — U0, B1–B3, U1 visor, Q1–Q11
- Viewport motor CLOSED: [implementation_review_spatial_board_viewport.md](implementation_review_spatial_board_viewport.md)
- Projector + `jarvis board` shipped @ **`v0.3.8`** / `checkpoint-spatial-board-projector` (`f3deae0`)

**Type:** Product-surface investigation. Map **what the board can and cannot do as an engineering tool**, and how far it can be improved **as product** (authority, honesty, workflow, persistence, freshness) — **not** visual polish.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** tag **`v0.3.8`** · commit `f3deae0`  
**Live tree:** visor + Python projector + CLI launcher. Preserve them.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not reopen Structure PASS, MEASURE/CAD/FEA, Conversation Engine, or new architectural subsystems. Do not rewrite PRODUCT_SCOPE** (you may *recommend* a ★ for later).

---

## 0. Role split (do not invert)

```text
Engineer  → asked: current limits + how far to improve this UI as product (not “bonito”)
Cursor    → this contract; later IC only after ★ on Buy
Claude    → investigation_report_spatial_board_product_limits.md
Cursor    → investigation review
Engineer ★ → Buy lock
Claude    → implements from IC only
```

---

## 1. Why this investigation exists

The **craft of the viewport is done** (Q1–Q11): pan, zoom-to-cursor, drag, resize, minimap, fit, layout overlay. Cards now come from `state.json`. `jarvis board` launches the visor.

That is **not yet a product evaluation**. An engineer can move cards. The open question is:

> What does the board **fail to do** as a way to **understand and continue a Jarvis project** — and which of those failures are the next real purchase vs decoration?

Engineer mandate (2026-09-05): evaluate **limits** and **how far we can optimize/improve at product level**, explicitly **not** visibility / “make it pretty.”

Cosmetic **out** (do not recommend as Buy): themes, typography, shadows, animation, card skins, 2D glyphs-as-aesthetics, dark-mode polish, spacing tweaks, “looks more like Figma.”

---

## 2. Governing question

> Given the visor as shipped at `v0.3.8`, what are its **product limits** (authority, honesty, freshness, persistence, payload, workflow vs CLI), and what is the **smallest Buy** that makes the board a better engineering instrument without turning it into a second source of truth or a mutation surface?

Answer all of §3. Cite `file:line` on the live tree.

---

## 3. Questions the report must answer

### Know — as-is product surface

1. **What can an engineer do today** with `jarvis board` that they cannot do in CLI / `views/*.md`? What can they **still only** do in CLI?
2. **Authority map** — who owns: engineering fields, layout `{x,y,w,h}`, project selection, card payload, Continuity / ERF / BOM? Confirm the design thesis (`state.json` truth; projector read-only; CLI/writers mutate) still holds in code.
3. **Projector honesty** — `project_spatial_nodes`: what it includes (properties, SKU, parts, lanes) and **refuses** (BOM buckets, missing architecture keys, completeness, `source=calculated` vs declared, empty-name specs). Is that refusal a product virtue or a product hole?
4. **Freshness** — after CLI `definir` / catalog bind / iterate, when do board cards update? Spawn-on-GET, no watch, localStorage overlay: what stale states can the Engineer see?
5. **Persistence** — layout lives in `localStorage` keyed by project id. What is lost on another browser, another machine, or `workspace/` copy? Contrast with `views/*.md` (derived, in the project tree).
6. **Grain** — 1 ComponentSpec = 1 card (U0). On a real 4/4 project this yields ~11–14 cards including ordinal plates. Is that the right **engineering grain**, or does it bury the craft (roots) under assembly children? Do **not** propose CAD.

### Claim — where the board can lie or over-promise

7. Phrase / implication matrix (required):

| Implication a user could take from the board | True today? | Over-claim? | Desired (proposal only) |

Cover at least: “this is the project,” “these are all components,” “empty card = slot to fill,” “layout is part of the project,” “numbers are declared geometry,” “I can edit the design here,” “PASS / next step is on the board.”

8. **PRODUCT_SCOPE** — v1 is still CLI + MCP. U1: visor is extra until ★. Does any shipped copy (`README`, toolbar, empty states) imply the board replaces CLI?

### Limit — how far product can go (ceiling, not wishlist)

9. What is the **ceiling** of this UI **without** becoming a Conversation Engine, a writer, or CAD? Name hard walls (must remain visor) vs **elastic** walls (layout-on-disk, missing slots, freshness, inspect).
10. Which deferred design items are **product** vs **cosmetic**?

| Item (design §4/§6) | Product? | Cosmetic? | Still deferred? Why |
|---|---|---|---|
| Ghost architecture slots (U6) | | | |
| 2D glyphs (U7) | | | |
| Labeled 4/4 lanes | | | |
| Continuity / ERF chrome on the board | | | |
| Catalog pick from the card | | | |
| Edges between cards | | | |
| `views/spatial_layout.json` | | | |

11. **Workflow** — can the board participate in “reopen weeks later without losing the thread” (PRODUCT_SCOPE Continuity) **without** duplicating Continuity as cards? If yes, what **one** artifact would it show? If no, say the board is **inspect-only** and Continuity stays CLI.

### Buy

12. Exactly **one primary Buy** from §7 E. Smallest capability jump that changes what an engineer **knows or trusts**, not how it looks.
13. Explicit non-goals for the next IC.

---

## 4. Locked stances (do not contradict)

1. **CLI / writers remain the engineering mutation surface.** Board writes, if any, are presentation (`{x,y,w,h}` only) unless Engineer ★ later. Do not recommend property/SKU/PASS editors on the card.
2. **1 ComponentSpec = 1 card** stays unless you prove a **blocking** product lie (e.g. plates drowning roots). If you recommend grouping, it must be presentation grouping, not a new domain ontology.
3. **No Conversation Engine / Decision Engine.** No FastAPI/JWT product. No RAG. No multiplayer.
4. **No CAD / FEA / MEASURE / glyphs-as-proof.** Declared scalars already on `ComponentSpec.properties` may be displayed; do not invent geometry.
5. **Do not reopen Structure PASS / `_derive_overall` / HD-*.** The board must not become a new verdict authority.
6. **Do not duplicate domain logic in React.** Payload projection stays Python (`spatial_board.py` or `render_views` sibling).
7. Viewport Q1–Q11 are **closed**. Do not re-litigate zoom math unless a **product** limit depends on it (unlikely).
8. Cosmetic work is **not** a Buy.

---

## 5. Surfaces to trace (file:line required)

| Surface | Find |
|---|---|
| Projector | `src/jarvis/workspace/spatial_board.py` — what is emitted / omitted; lane recipe vs `BLOCK_TO_COMPONENTS` |
| Tests | `tests/test_spatial_board_projector.py` — locked refusals (no invented slots, empty name, SKU) |
| Launcher | `src/jarvis/adapters/cli/board.py` — `jarvis board`; already-running port; no orchestrator |
| Visor fetch | `ui/spatial-board/vite-plugin-jarvis-projects.ts` — `/api/projects`, `/api/projects/:id/nodes`, Python spawn |
| Overlay | `ui/spatial-board/src/useBoardNodes.ts` — `localStorage` key; merge vs projector defaults |
| Card payload | `ui/spatial-board/src/SpatialCard.tsx`, `types.ts` — identity + fields only |
| Derived views precedent | `src/jarvis/workspace/render_views.py` + `WorkspaceManager.render_views` — markdown analog |
| Spec | `ComponentSpec` / `PropertyValue` / `CatalogRef` / `parent_key` |
| Scope | `PRODUCT_SCOPE.md` in-scope v1 (CLI+MCP); Continuity table |
| Design locks | `design_spatial_board_ui.md` §1 authority, §4 deferred, §6 U1/U6/U7 |
| Entry map | `docs/system_map/00_entry/ENTRY_MAP.md` — board is **not** yet a documented adapter; say whether it should be (doc-only, not a new C-xxx unless you prove a connection) |

Do **not** mutate Engineer `workspace/` projects. Reconstruct in `tmp_path` or **read** existing `workspace/*/state.json` as evidence (read-only).

---

## 6. Field reconstruction (required)

### Fixture A — projector vs BOM vs architecture (tmp_path)

```text
Aerial project, system_blocks = propulsion/energy/structure/control
components: motors (catalog SKU + properties), battery, frame + frame_arm child
omit esc (architecture expects it; components dict has no esc)
flight_controller with name="" and empty properties
```

Record: node ids, kinds, whether `esc` appears, how empty FC is shown, whether completeness/BOM missing appears anywhere. Contrast `build_component_bom` missing list vs board.

### Fixture B — freshness / overlay (reasoned, code-backed; live visor optional)

```text
1) Project nodes from state.json
2) Overlay moves motors {x,y} in localStorage
3) CLI-equivalent: change motors.name / add a property on the same id
```

What does the next GET `/nodes` show for payload vs rect? When is the Engineer looking at a **moved** card with **stale** SKU if they never reload?

### Fixture C — persistence ceiling

State in prose + code: layout key schema; what a second browser / clone of `workspace/` does **not** restore. Compare to `views/sistema.md` after `render_views`.

---

## 7. Required report shape

### A. Executive answer (≤20 lines)

Current product limits in one paragraph + primary Buy.

### B. As-is map (Know)

| Capability | Board today | CLI / views today | Gap class: none / honesty / freshness / persist / workflow |

### C. Authority (Claim)

```text
engineering fields  ← ?
layout x,y,w,h      ← ?
card list           ← ?
Continuity/ERF/BOM  ← ?
```

### D. Honesty matrix

§3.7 table, filled, with `file:line`.

### E. Ceiling

Hard walls vs elastic walls (§3.9–3.11). Deferred-item table (§3.10).

### F. Buy (exactly one primary)

| Option | Meaning |
|---|---|
| **B0** | No IC — board stays visor-as-shipped; debt/agenda only |
| **B1** | Layout in the project tree (`views/spatial_layout.json` or equivalent) — presentation persist, no engineering write |
| **B2** | Freshness: reload/watch/`mtime` so CLI mutations appear without a full page ritual; still read-only |
| **B3** | Honest absence: architecture-expected keys missing from `components` appear as **slots** (kind already exists) — display-only, not acquisition |
| **B4** | Payload honesty: distinguish declared vs calculated/`source`; completeness or “sin propiedades” without becoming ERF |
| **B5** | Grain: presentation grouping (e.g. parts tucked under frame) **without** new ontology — only if Fixture A proves drowning |
| **B6** | One inspect/focus affordance (select a card → that card is the reading surface) — **product attention**, not chrome; no writers |
| **B7** | Doc-only: ENTRY_MAP + README honesty; PRODUCT_SCOPE unchanged |

If two feel tied, pick the one that removes a **lie** (D) over one that adds a **feature**. Justify. Secondary options may be listed as later, not this IC.

### G. Explicit non-goals

Cosmetic UI · RAG · catalog pick from card · Continuity/ERF as a second dashboard · Conversation Engine · CAD/glyphs-as-proof · property editors · version bump · Structure/HD-* reopen.

### H. IC skeleton (if Buy ≠ B0)

≤25 lines: files, behavior, tests, forbidden — **not** an IC.

---

## 8. Constraints

- No `src/` or `ui/` edits as the deliverable (you may propose files in H).
- No new C-xxx unless you show a real connection the map is missing; default is **doc note**, not registry inflation.
- No recommending FastAPI as the freshness mechanism if the Vite plugin + projector already can poll/mtime.
- Full honesty: if the board is a **good visor and should stay small**, B0/B7 is a valid primary.

---

## 9. Done criteria

- Report at the path above with A–H  
- Every factual claim cites `file:line` or a named test on live tree / `v0.3.8`  
- Primary Buy chosen; cosmetic work rejected with reason  
- No `src/` / `ui/` edits  

---

## 10. After review

Cursor writes investigation review. Engineer ★ on Buy (or edits). Only then an Implementation Contract.
