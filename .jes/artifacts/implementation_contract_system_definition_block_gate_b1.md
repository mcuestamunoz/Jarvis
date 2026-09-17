# Implementation Contract — Gate SYSTEM_DEFINITION B-path until ComponentRule exists (`B1-system-definition-block-gate`)

**Project:** Jarvis  
**Date:** 2026-09-15  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** IMPLEMENTED · review **PASS WITH NOTES** — awaiting Engineer smoke ACCEPT  
**Parents:**
- Investigation REVIEWED **PASS WITH NOTES** — [contract](investigation_contract_mission_functional_payload_holes_b0.md) · [report](investigation_report_mission_functional_payload_holes_b0.md) · [review](investigation_review_mission_functional_payload_holes_b0.md) — lean **B1-min (a)**
- Live bug: SYSTEM_DEFINITION mode **B** accepts aliases (`camara` → `perception` → stubs `cameras`/`lidar`) with **no** `ComponentRule` in `aerial_registry` → permanent `completeness: low` BOM rows
- Registry today (7 keys only): `motors`, `propellers`, `esc`, `battery`, `frame`, `flight_controller`, `sensors`
- Dead blocks today (all component keys missing a rule): `perception`, `communication`, `payload`, `manipulation`, `actuation` (`wheels`), `transmission` (`gearbox`)
- Feature locks: no invent camera/mass/mm · no Conversation Engine · no firmware · no new `library/cameras` this Buy

**Type:** Fail-closed **honesty gate** on SYSTEM_DEFINITION custom-block acceptance so Jarvis cannot create component stubs it cannot later resolve.  
**Not** adding `ComponentRule`s for cameras/lidar/radio/…  
**Not** catalog families / mirrored mass for payload  
**Not** wizard “vigilancia” nudge (follow-on ★)  
**Not** Continuity “Aumentar carga útil” rewrite  
**Not** version bump · **Not** `workspace/` mutation unless ★ Path D (default: tests-only)

**Output:** `.jes/artifacts/implementation_report_system_definition_block_gate_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2929** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-system-definition-block-gate`** — close the shipped SYSTEM_DEFINITION B dead-end |
| 2 | Branch | Investigation **B1-min (a)** only — **gate**, do not add rules/catalog |
| 3 | Rule of offerability | A catalog `block` may be **accepted** into `custom_blocks` / expanded to component stubs **iff every** key in `BLOCK_TO_COMPONENTS[block]` has a matching `ComponentRule.suggested_key` in the live aerial registry (default: `aerial_registry`). If the block has an empty component list, treat as non-expanding custom (existing free-text path) — do not invent keys |
| 4 | Where to enforce | Single shared helper (name OK, e.g. `block_components_are_resolvable(block, registry=…)`) used from **both** places that add aliased blocks today: `_handle_choice` (implicit B via alias) and `_handle_custom_blocks` (step 1). Prefer helper living next to `BLOCK_TO_COMPONENTS` / catalog module so the gate is not duplicated |
| 5 | On refuse | Stay in SYSTEM_DEFINITION interactive session; **do not** append the block; **do not** create stubs. Spanish message must say the capability is **not available yet** / cannot declare that subsystem until Jarvis can resolve its components — and invite another block or `listo`. Do **not** silently ignore |
| 6 | Step-1 prompt copy | Update the “Ejemplos: 'visión artificial', 'comunicación', 'payload'” line so examples are **only** blocks that currently pass the gate (for aerial default: propulsion/energy/structure/control synonyms — e.g. frame/batería/control — **not** cámara/comunicación/payload). Exact strings in report |
| 7 | Option B still offered | User may still pick **B**; only **ungrounded aliases** are refused. Base architecture **A** unchanged |
| 8 | Existing tests | `test_answer_b_then_vision_then_listo` (expects `cameras`/`lidar` stubs) **must change** to assert refuse + **no** `cameras`/`lidar` keys — that test currently encodes the bug |
| 9 | Forbidden | Add camera/lidar/radio/payload_bay/arm/wheels/gearbox `ComponentRule` · invent library seeds · invent mass/mm · Continuity next-step rewrite · wizard mission nudge · version bump · Conversation Engine |
| 10 | Live apply | Default **tests-only**. No need to mutate `dron-de-vigilancia-doméstico` (it never took B) |

**Product sentence:**

```text
Si aún no puedo resolver “cámara”/“radio”/… como componentes reales,
no te dejo añadir ese bloque a la arquitectura — así el BOM no queda
roto con huecos imposibles de completar.
```

---

## 1. You (Claude)

1. Add resolvability helper + wire refuse paths (locks #3–#5).  
2. Fix step-1 example copy (lock #6).  
3. Update / invert the vision→cameras test; add T1–T6 below.  
4. Report: exact refuse strings; list of blocks currently gated vs passable for aerial registry.  
5. No `aerial.py` new rules. No version bump. No workspace write (unless ★ overrides).

**STOP if** forced to add ComponentRules or catalog rows to “make B work” for cameras — that is a different ★.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Helper: `perception` / `communication` / `payload` / `manipulation` / `actuation` / `transmission` → **not** resolvable with live `aerial_registry` |
| T2 | Helper: `propulsion` / `energy` / `structure` / `control` → **resolvable** |
| T3 | Mode B → `visión artificial` / `camara` → refuse message; after `listo`, project has **no** `cameras`/`lidar` stubs |
| T4 | Mode B → `comunicación` or `payload` → refuse; no `radio_module` / `payload_bay` |
| T5 | Mode B → resolvable alias (e.g. structure/`frame` if not already in base — or re-add energy synonym) still works; no regression on **A** creating default stubs |
| T6 | Full pytest green; package `0.4.1`; prior `test_answer_b_then_vision_then_listo` rewritten to T3 semantics |

---

## 3. Smoke (Engineer)

1. `n` → create throwaway drone project → SYSTEM_DEFINITION appears.  
2. **B** → type `cámara` or `visión artificial` → Jarvis **refuses** with honest “not available yet”; no `cameras` in `estado`/BOM.  
3. **A** (or B + only resolvable blocks) still reaches propulsion acquisition as today.  
4. Confirm examples in B prompt no longer advertise cámara/comunicación/payload as if they worked.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| B1-min (b) minimal ComponentRules for cameras/… | Needs Engineer definition of identity-only rule |
| Wizard nudge for “vigilancia” → try B | After this gate ships |
| `library/cameras` / link / mass mirrored params | Bags required |
| Continuity suppress `increase_payload` vs mission | Park until holes exist |
| Purge already-stuck `cameras` rows in any live project | None known from vigilancia smoke; if found, separate ★ |

---

## 5. Done when

- [ ] ★  
- [ ] Gate + copy + T1–T6 + report  
- [ ] Cursor review PASS  
- [ ] Engineer smoke ACCEPT  

---

## 6. Handoff

```text
Engineer → ★ B1-system-definition-block-gate (this IC)
Claude   → implement gate + tests + report (no new ComponentRules)
Cursor   → review
Engineer → smoke §3
```
