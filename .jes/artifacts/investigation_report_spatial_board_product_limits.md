# Investigation Report — Spatial Board Product Limits

**Project:** Jarvis
**Date:** 2026-09-05
**Investigator:** Claude Code
**Contract:** [investigation_contract_spatial_board_product_limits.md](investigation_contract_spatial_board_product_limits.md)
**Checkpoint:** `v0.3.8` / `checkpoint-spatial-board-projector` (`f3deae0`)
**Status:** OPEN — for Cursor review → Engineer ★ on Buy

**Not an Implementation Contract. No `src/`/`ui/` edits made.** Every claim below cites `file:line` on the live tree or a concrete Python reconstruction run this session (shown inline); nothing is reused from the viewport-motor investigation's own conclusions without re-verifying against the current code.

---

## A. Executive answer

The viewport craft (Q1–Q11) is real and closed — pan/zoom/drag/resize/minimap work, and the projector (`spatial_board.py`) is a clean, honest, read-only DTO layer with zero write endpoints anywhere in the stack (confirmed: only two `fetch()` calls in the whole UI, both `GET`; no `POST`/`PUT`/`PATCH` anywhere). As a product, though, the board has one damaging **silent omission**: architecture-expected components that are simply absent from `components` (e.g. ESC on a 4-block aerial project) render **no card and no signal at all** — the engineer sees a board that looks complete when `build_component_bom` would show `✗ esc: no definido`. Every other limit found (freshness requires a manual project-switch or reload; layout lives in browser `localStorage`, not the project tree; declared vs. `calculated` `PropertyValue.source` is displayed identically) is a real gap but not an active lie — the board never claims to be live or authoritative, and README/the empty-project copy are already honest about CLI owning mutation.

**Primary Buy: B3 — honest absence (ghost slots for architecture-expected, undeclared components), display-only.** This is the smallest capability jump that removes an actual epistemic lie ("this board shows all the components"), not a feature addition. It is also nearly free: the frontend's `kind` field already has a third value (`"slot"`) with its own CSS (dashed border, muted minimap dot) built and unused since the viewport-motor fixture phase — this Buy is Python-only.

---

## B. As-is map (Know)

| Capability | Board today | CLI / views today | Gap class |
|---|---|---|---|
| See every declared component + its properties, at a glance, spatially arranged by architecture block | Yes — `project_spatial_nodes` (`spatial_board.py:30-97`) emits one card per `ComponentSpec`, lane-grouped via the same `BLOCK_TO_COMPONENTS` registry BOM/architecture-progress use (`spatial_board.py:16,105-124`) | `views/sistema.md` lists components as a flat bullet list (`render_views.py:41-43`); CLI `estado`/BOM prints them as text | none — board is a genuine, non-duplicated improvement here |
| See parent/child structure part nesting (e.g. Armattan's arm/4-plate/cage/standoff) | Yes, visually — children stack directly under their parent in the same lane column (`spatial_board.py:60-79`, proven by `test_parts_are_kind_part_stacked_under_parent_lane`) | Only as indented `└` BOM sub-lines (`project_closure.py::_frame_part_sublines`) — text, no spatial grouping | none |
| See that an architecture-expected component (ESC, propellers, sensors) is **missing** | **No** — confirmed live (Fixture A below): with `esc` absent from `components`, zero card, zero hint, zero difference from "ESC doesn't apply to this project" | Yes — `build_component_bom`'s `"missing"` list + `✗ esc: no definido` BOM line | **honesty** |
| See *why* a card is empty (blank name, zero properties) | Card renders, but as an undifferentiated blank box — no completeness label, no "why" (Fixture A: `flight_controller` name="" → `declaredName: ""` → UI shows "sin nombre declarado" (`SpatialCard.tsx:40`) but nothing distinguishes "stub, needs definition" from "legitimately minimal") | BOM buckets it under `"incomplete"` with `missing_fields` / a completeness tail (`project_closure.py`) | honesty |
| Distinguish a user-declared number from one the DSE/system calculated on its behalf | **No** — `_format_property` (`spatial_board.py:138-148`) reads only `.value`/`.unit`, never `.source`/`.confidence`; a `PropertyValue(source="calculated")` (real production case: `component_sync.py:43-49`, DSE-elevated `motor_count`/`thrust_n` after a params-only apply) renders identically to a hand-typed one | `PropertyValue.source` exists in the schema (`action_schema.py:123-127`) but no CLI/BOM copy surfaces it either today — this is not a board-specific hole, it's a schema field nobody displays yet | honesty (shared debt, not board-unique) |
| Get current data after a CLI mutation without reloading | **No** — `useBoardNodes`'s fetch effect depends only on `[projectId]` (`useBoardNodes.ts:40-66`); no poll, no `mtime` watch, no visible "stale" indicator; the toolbar has exactly two buttons, "Encajar" and "100%" — no reload control (`InfiniteCanvas.tsx:116-137`) | `views/*.md` regenerate at 2 of the ~12 `save_state` call sites in `orchestrator.py`/`param_definition_session.py` (grepped: `orchestrator.py:4421`, `param_definition_session.py:1015`) — **fresher on more paths, but not universally guaranteed fresh either** | freshness (real, but not unique to the board) |
| Keep a layout across machines / a second browser / a `workspace/` copy | **No** — layout key `jarvis.spatial-board.layout.v1.<projectId>` lives in browser `localStorage` (`useBoardNodes.ts:8-9,23-29`, `constants.ts:24`), entirely outside `workspace/<project>/`; a fresh clone or second browser reverts silently to the deterministic lane recipe (not a crash — a quiet reset) | `views/sistema.md` etc. are files inside the project tree — travel with `git`/copy/another machine by construction | persist |
| Reopen a project and know "where was I" without losing the thread | Board shows current cards only — no next-step, no situation/evidence | `continuity.situation`/`evidence`/`next_useful_step` (PRODUCT_SCOPE.md's Continuity table) is CLI-only | workflow (by design — see §H11) |
| Move/mutate an engineering value from the UI | **No** — confirmed: zero POST/PUT/PATCH fetch anywhere in `ui/spatial-board`; `SpatialCard.tsx` renders fields as `<dl>/<dt>/<dd>` (`SpatialCard.tsx:42-49`), no inputs | Yes, via CLI/`definir`/catalog bind | none — this is correct, locked-stance-respecting behavior, not a gap |

---

## C. Authority (Claim)

```text
engineering fields  ← CLI / writers only (component_writers.py, catalog_bind.py) —
                       confirmed: project_spatial_nodes (spatial_board.py:30) takes a
                       ProjectState and only reads it; no function in spatial_board.py
                       or anywhere in ui/spatial-board/ constructs/returns a ProjectState
                       or calls a writer. Zero write HTTP routes exist
                       (vite-plugin-jarvis-projects.ts:126-163 registers exactly two
                       GET routes, /api/projects and /api/projects/:id/nodes).

layout x,y,w,h      ← browser localStorage, keyed jarvis.spatial-board.layout.v1.<id>
                       (useBoardNodes.ts:8-9,23-29). NOT state.json, NOT workspace/.
                       Design's own §1 authority diagram (design_spatial_board_ui.md:33-41)
                       named `spatial_layout.json` as the intended persistence target;
                       the shipped viewport-motor IC used localStorage as an explicit
                       "v0" placeholder (implementation_review_spatial_board_viewport.md:15,21
                       — "Pass — localStorage" / "Acceptable for localStorage v0").
                       spatial_layout.json was never built. This is real, named debt,
                       not a discovery.

card list           ← Python projector only, freshly computed every request
                       (vite-plugin-jarvis-projects.ts:97-118 spawns a fresh
                       `python -m jarvis.workspace.spatial_board <state.json>` process
                       per GET — the SERVER side is always fresh at request time).
                       The staleness gap (§B) is entirely front-end: the browser
                       just doesn't ask again until projectId changes or the page reloads.

Continuity/ERF/BOM  ← CLI only. Confirmed absent from the board by direct code search:
                       no import of build_component_bom, engineering_readiness, or
                       project_continuity anywhere under ui/spatial-board/ or in
                       spatial_board.py (its own docstring states the rule:
                       "no muta ingeniería, no clasifica BOM, no inventa slots
                       ausentes" — spatial_board.py:5).
```

**Verdict: the design thesis holds in code, with one named exception (layout persistence backend, above) that was already known/accepted as interim, not a surprise this investigation uncovered.**

---

## D. Honesty matrix

| Implication a user could take from the board | True today? | Over-claim? | Desired (proposal only) |
|---|---|---|---|
| "This is the project" | No — it's a read-only view of one artifact (`state.json`'s `components`), not the project (no objective, no history, no continuity) | No over-claim — nothing in the UI says this; empty-project copy says "Este proyecto no tiene componentes declarados" (`InfiniteCanvas.tsx:144`), and the brand header shows the project's own title/slug (`ProjectSwitcher.tsx:31-33`), correctly scoping it as *a view of* the project | Same — this framing needs no change |
| "These are all the components" | **No** — architecture-expected-but-undeclared keys (ESC, propellers, sensors in Fixture A) are silently absent, no different from "not applicable" | **Yes — this is the one real over-claim** (by omission, not by an explicit sentence) | B3: an absent, architecture-expected key renders a dashed "slot" card, honestly distinguishing "not yet declared" from "doesn't apply to this architecture" |
| "Empty card = slot to fill" | No — an empty-name/empty-property card (Fixture A's `flight_controller`) is a **real, declared** `ComponentSpec` that merely has nothing set yet; it looks identical to what a *slot* (§ above) would look like if one existed, which is itself confusing in the other direction | Mild over-claim (ambiguity, not falsehood) — a reader can't tell "user started defining this and stopped" from "genuinely nothing here" | B4 (secondary): distinguish "declared, currently empty" from "not declared at all" (the new slot kind) visually — these are two different facts today with one visual treatment |
| "Layout is part of the project" | No — proven in Fixture C: layout lives in the browser, not `workspace/<project>/` | Nothing in the UI claims persistence beyond "this browser, this project id" — no over-claim in copy, but no disclaimer either | B1: move layout into `views/spatial_layout.json` or equivalent so it *becomes* true |
| "Numbers are declared geometry" | Not always — `PropertyValue.source` can be `"calculated"` (real case: DSE-elevated `motor_count`, `component_sync.py:43-49`) and renders identically to `"declared"` | Yes, a real (if narrow) over-claim, shared with CLI/BOM which also don't surface `source` anywhere yet — not board-unique | B4: only if/when a broader source-honesty pass happens; low priority alone since the board isn't worse than CLI here |
| "I can edit the design here" | No — confirmed zero write paths (see §C); drag/resize only ever mutate `{x,y,width,height}` | No over-claim — no input fields exist on the card (`SpatialCard.tsx:42-49` is a plain `<dl>`), and the toolbar hint text only describes viewport gestures (`InfiniteCanvas.tsx:132-136`) | No change needed |
| "PASS / next step is on the board" | No — confirmed absent by code search (§C); Fixture A shows `frame`'s BOM completeness footnote ("compatibilidad de clase nivel A pendiente") has no board equivalent at all | No over-claim — nothing on the board suggests a verdict exists | No change needed; explicitly forbidden to add (locked stance §4.5) |

---

## E. Ceiling

**Hard walls (must remain visor, never cross regardless of Buy):**
- No write HTTP route, ever — confirmed zero exist; any Buy that adds one turns the board into a mutation surface, forbidden by locked stance #1.
- No PASS/ERF/`_derive_overall` computation or display — the board must never become a second verdict authority (locked stance #5); Fixture A already shows this line is respected today.
- No BOM bucket classification (`"declarative"`/`"incomplete"` labels) reproduced on the board — that's Continuity/BOM's job; a slot (B3) is not a BOM bucket, it's a narrower, purely structural fact ("this key is in `BLOCK_TO_COMPONENTS[block]` and not in `components`") computed the same way `_lane_index` already computes lane placement, with no dependency on `build_component_bom` at all.
- No CAD/geometry/glyph-as-proof — only `ComponentSpec.properties` values already present may ever be displayed (locked stance #4).

**Elastic walls (can move without becoming any of the above):**
- Layout persistence backend (localStorage → file) — pure infra swap, doesn't touch authority.
- Freshness (poll/`mtime`/manual reload) — pure infra, the projector is already stateless and cheap to re-invoke.
- Honest absence (this report's B3) — pure display, reuses an existing registry, no new domain concept (a "slot" is not a `ComponentSpec`, so it doesn't create a fifth node type or contradict "1 ComponentSpec = 1 card," §H11 note).
- Payload honesty (`source`/`confidence` display) — pure display of an existing schema field.
- One inspect/focus affordance (B6) — pure UI state (which card is "focused"), no new data.

### Deferred-item table (§3.10)

| Item (design §4/§6) | Product? | Cosmetic? | Still deferred? Why |
|---|---|---|---|
| Ghost architecture slots (U6) | **Yes** | No | **No longer deferred — this report promotes it to primary Buy (B3).** The frontend groundwork (`kind: "slot"` type, `.sb-card--slot`/`.sb-minimap__dot--slot` CSS, and a literal `esc` slot example in `fixtures.ts:31-39`) already exists unused since the viewport-motor phase — confirmed via `grep`, zero frontend changes needed. |
| 2D glyphs (U7) | No | **Yes** | Deferred — explicitly named cosmetic by the Engineer's own framing in this contract's §0 ("2D glyphs-as-aesthetics" listed under cosmetic-out). No product argument surfaced in this investigation either. |
| Labeled 4/4 lanes | Mild yes | Mild yes | Deferred, but cheap follow-on to B3 — once slot columns exist, a text header over each lane ("Propulsion", "Structure", ...) would help orient a reader faster. Not chosen as primary because it doesn't remove a lie, only reduces a "which column is this" guess that a returning engineer resolves in a few seconds anyway. |
| Continuity/ERF chrome on the board | N/A | N/A | **Forbidden**, not merely deferred (locked stance #5) — would make the board a second verdict/next-step authority. See §H11: if any single Continuity fact ever belongs on the board, it should be an inspect-surface reference, never a duplicated dashboard. |
| Catalog pick from the card | N/A | N/A | **Forbidden**, not merely deferred (locked stance #1, design §7 non-goal) — a card-side action is a mutation surface. |
| Edges between cards | Mixed | Mixed | Deferred — design's own U5 lock keeps it out of scope; this investigation adds a claim-risk reason too: an edge between "motors" and "esc" would visually imply a checked/compatible connection that Jarvis has never verified (`electrical_compatibility` runs in CLI, not surfaced here) — drawing a line risks a new over-claim, not just cosmetics. |
| `views/spatial_layout.json` | **Yes** | No | Deferred to a **secondary** IC (this report's Buy B1) — real, named durability gap (§B/§C), but per the tie-break rule in §7 of the contract ("pick the one that removes a lie over one that adds a feature"), B3 outranks it for *this* IC. Recommended as the very next Buy after B3. |

---

## F. Buy

### Primary: **B3 — Honest absence (architecture-expected, undeclared keys render as display-only slot cards)**

| Option | Meaning |
|---|---|
| B0 | No IC — rejected: leaves a proven, live over-claim (§D) unaddressed for free |
| **B1** | Layout in the project tree | Real gap, but doesn't remove a lie — named as the clear next Buy, not this one |
| B2 | Freshness (reload/watch/mtime) | Real gap, but the board never claims liveness — friction, not dishonesty |
| **B3** | **Honest absence** | **Chosen** — the only candidate that removes an active over-claim, is architecturally free on the frontend, and reuses the exact registry (`BLOCK_TO_COMPONENTS`) the projector already imports |
| B4 | Payload honesty (declared vs. calculated) | Real but narrower/rarer in practice (DSE-elevated properties are the only live `source="calculated"` producer found); also a schema-wide gap CLI shares, so fixing it board-only is a partial, possibly confusing win |
| B5 | Grain (presentation grouping) | **Not proven** — Fixture A/reasoning shows children stack cleanly under their parent column (no overlap, no hiding); a 7-card frame subtree is a scroll cost, not a "can't find the root" failure. Locked stance #2 requires a *proven blocking* lie before regrouping; none found. Rejected for this IC. |
| B6 | Inspect/focus affordance | A real, cheap improvement, but it's an attention feature, not a knowledge/trust fix — doesn't outrank B3 on the tie-break rule |
| B7 | Doc-only | Insufficient alone — the underlying board behavior (§D's real over-claim) would stay unfixed; doc notes are still recommended as small additions to B3 (see §H) |

**Why B3 over the others, explicitly against the tie-break rule ("if two feel tied, pick the one that removes a lie"):** B1/B2/B6 are all real, legitimate product improvements, but none of them is currently making the board say something false. B3 is the one place this investigation found the board actively implying something untrue by omission — that what's on screen is the complete component set for the declared architecture. It is also the cheapest possible Buy: the exact registry needed (`BLOCK_TO_COMPONENTS`) is already imported by `spatial_board.py:16`; the frontend rendering path (`kind`-driven CSS class) requires zero new code, confirmed by `grep` showing `kind` is never branched on in interaction logic (`useNodeGestures.ts`, drag/resize) — only used for a CSS class string in `SpatialCard.tsx:23` and `Minimap.tsx:46`.

**Recommended next (not this IC):** B1 (layout in the project tree) — the design's own §1 authority diagram already named this as the target; the viewport-motor IC's localStorage choice was explicitly interim.

---

## G. Explicit non-goals (for the eventual IC)

Cosmetic UI (2D glyphs, lane labels, themes) · RAG · catalog pick from card · Continuity/ERF as a second dashboard · Conversation Engine · CAD/glyphs-as-proof · property editors · edges between cards · payload honesty (`source`/`confidence` display, B4 — separate future IC) · layout persistence backend change (B1 — separate future IC) · freshness/polling (B2 — separate future IC) · grain/grouping (B5 — not evidenced) · version bump · Structure/HD-* reopen · new C-xxx registry entries (a doc-only ENTRY_MAP note is enough — see §H).

---

## H. IC skeleton (Buy = B3 — not an Implementation Contract, ≤25 lines)

- **Files:** `src/jarvis/workspace/spatial_board.py` — `project_spatial_nodes` gains a slot-emission pass: for each block in `state.design_properties.system_blocks`, for each key in `BLOCK_TO_COMPONENTS[block]` not already present as a root in `components` (dedupe across blocks — a key like `motors` appearing in 3 blocks is checked/emitted once, at its first-occurring block, mirroring `_lane_index`'s own existing first-match rule), emit `{id: key, kind: "slot", title: key, declaredName: "", fields: [{"label": "estado", "value": "no declarado"}], ...same x/y/w/h placement path as a real root}`. No dependency on `build_component_bom` — computed directly from `BLOCK_TO_COMPONENTS`, already imported.
- **Behavior change:** a project with a declared architecture block whose expected component isn't in `components` now shows a dashed-border card for it (frontend needs **zero** changes — `kind: "slot"` CSS already exists, confirmed unused since `fixtures.ts:31-39`). Projects with no declared blocks, or with every expected key present, are byte-identical to today.
- **Doc-only, same PR:** one row in `docs/system_map/00_entry/ENTRY_MAP.md`'s adapters table for `adapters/cli/board.py`/`workspace/spatial_board.py` (no new C-xxx — this is a doc note, not a discovered connection); optionally a one-line honest caveat in README's "Pizarra" blurb ("slots muestran huecos de arquitectura, no completeness/BOM").
- **Tests:** slot appears for a declared block's missing expected key; slot absent for an *undeclared* block (supersedes, deliberately and explicitly, today's `test_does_not_invent_missing_architecture_slots` — this IC's whole point is to invent them, honestly, for declared-but-unfilled architecture only); a key present as a real component never also gets a slot; slot never appears for a key with no owning block at all (orphan handling unchanged); slot node carries no `catalog_ref`/no properties beyond the fixed `estado` field; regression — BOM/`_frame_completeness`/`_structure_evidence`/ERF verdict byte-identical (the slot pass reads `state`, never writes it, and lives entirely inside `spatial_board.py`, which no engineering-verdict code imports).
- **Forbidden:** any write endpoint; any BOM-bucket label (`"incomplete"`/`"declarative"`) copied onto the slot; any PASS/completeness computation; any new node type beyond the frontend's already-existing `"slot"` kind; any change to `BLOCK_TO_COMPONENTS` itself; any change to `build_component_bom`; version bump.
