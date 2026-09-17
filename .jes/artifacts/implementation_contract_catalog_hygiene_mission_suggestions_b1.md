# Implementation Contract — Catalog hygiene + SuggestionEngine mission gate (`B1-catalog-hygiene-mission-suggestions`)

**Project:** Jarvis  
**Date:** 2026-09-17  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★  

**Parents:**
- Software closeout queue **#4** — [engineer_note_software_closeout_queue.md](engineer_note_software_closeout_queue.md)
- Continuity mission-intent **CLOSED** — review N1: `SuggestionEngine` still emits `increase_payload` on `simular` / action_map ([review](implementation_review_continuity_mission_intent_b1.md))
- Estimated-temporary ESC Skystars **CLOSED** — review N1: `bind_esc_from_catalog(..., base=)` leaks stale props when new SKU omits a key ([review](implementation_review_geometry_estimated_temporary_esc_skystars_b1.md))
- Library FC/sensors P0 **CLOSED** — review N1: binds exist; IDLE `cambiar controladora` / `cambiar gps` **not** wired ([report](implementation_report_library_fc_sensors_b1.md))
- User guide craft-montage — documented traps §3.2 / §12.2 / inventory §10
- Mission helpers already shipped — `mission_intent_active` / `mission_intent_text_signal` / waterfall in `reasoning_layer.py`

**Type:** Three **localized hygiene** fixes in one Buy: (A) ESC catalog rebind omit-key honesty, (B) IDLE FC/GPS rebind (+ optional refresh) using existing identity catalog offers/binds, (C) gate `increase_payload` under mission intent on the **SuggestionEngine → simulate / ReasoningLayer action_map** path that Continuity #1 left open.  
**Not** new catalog families / invented mm.  
**Not** axial prop geometry / HD-005.  
**Not** more identity rules (#5).  
**Not** Conversation Engine.  
**Not** version bump. **Not** `workspace/` mutation (tests-only).

**Output:** `.jes/artifacts/implementation_report_catalog_hygiene_mission_suggestions_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3006** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

### A — `bind_esc` omit-key leak

| # | Decision | Lock |
|---|---|---|
| A1 | Bug | `bind_esc_from_catalog(sku, base=old)` does `{**old.properties, **projected}` — keys the **new** catalog row omits (e.g. `height_mm`) survive labeled as if they belonged to the new SKU |
| A2 | Fix | On `base=` merge, for the ESC **catalog-projected key set** (at least: `current_a`, `mass_g`, `length_mm`, `width_mm`, `height_mm` — report exact frozenset), **drop** any base key in that set that the new `projected` dict does **not** include; then merge. Preserve non-catalog keys (`mounted_on`, `declared_box_pose`, attestations, user free-text identity fields not in the set) |
| A3 | Scope | **Required** for `bind_esc_from_catalog`. **Same omit hygiene** for `bind_flight_controller_from_catalog` / `bind_sensor_from_catalog` (identical merge pattern; prevents the same leak the moment IDLE rebind ships). Other binds (motor/prop/battery/frame) — apply the same pattern **iff** cheap and shared helper; else name as residual in report |
| A4 | Clear geometry | Existing clear-on-geometry-change / fit-attest clear paths must still run when envelope dims change or drop — do not weaken |

### B — IDLE FC / GPS rebind (+ refresh)

| # | Decision | Lock |
|---|---|---|
| B1 | Rebind | Extend `catalog_rebind_assist` so pure phrases like **`cambiar controladora`** / **`cambiar fc`** → `flight_controller`, and **`cambiar gps`** / **`cambiar sensores`** (or locked Spanish synonyms in report) → `sensors`. Update `CatalogRebindKey` + `_PURE_PHRASE_STRIP_RE` |
| B2 | Offer | Orchestrator IDLE rebind dispatch: handle the new keys by calling the **existing** `_offer_flight_controller_identity_catalog` / sensors offer + `_apply_control_identity_catalog_pick` / bind writers — **do not** invent a parallel picker |
| B3 | Refresh | Extend `catalog_refresh_assist` so `actualiza el fc` / `actualiza el gps` (locked patterns) resolve to those keys and hit `refresh_component_from_catalog` (already must support FC/sensors binds, or wire the thin missing branch — report) |
| B4 | Forbidden | New acquisition architecture · LLM · inventing FC/GPS SKUs |

### C — SuggestionEngine / action_map mission gate (Continuity N1)

| # | Decision | Lock |
|---|---|---|
| C1 | Problem | After `simular`, Spanish “Podrías aumentar la carga útil” still appears under mission intent; ReasoningLayer action_map can enrich `increase_payload` from injected suggestions without the #1 waterfall |
| C2 | Fix | Reuse `mission_intent_active` (+ existing waterfall helper). When mission active: **do not** surface `increase_payload` from SuggestionEngine outputs in (1) ReasoningLayer’s suggestion action_map loop and (2) the simulate/iterate user-visible suggestions list. Prefer replacing with the same mission-aware alternate as #1 when Continuity/reasoning is built; for the raw SuggestionEngine bullet list, either suppress `increase_payload` or rewrite via the shared helper — report exact UX |
| C3 | Neutral | Mission **not** active → byte-identical SuggestionEngine + action_map behavior to today |
| C4 | Where | Prefer filtering at ReasoningLayer + one orchestrator/simulate call site using shared helpers — **avoid** duplicating keyword lists. SuggestionEngine may stay physics-only if all consumers filter; or accept an optional context arg — report choice |
| C5 | Forbidden | Changing `HIGH_MARGIN_THRESHOLD` · flipping ASSEMBLY_READY · LLM rewrite of suggestions |

### Shared locks

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-catalog-hygiene-mission-suggestions`** — A + B + C in one ★ |
| 2 | Package | Stay **`0.4.1`** |
| 3 | Live | Default **tests-only** |
| 4 | Docs | Update USER_GUIDE trap lines that say FC rebind / bind-esc leak are open — mark fixed after ship (minimal guide patch OK this Buy) |

**Product sentence:**

```text
Cambiar ESC no deja medidas fantasma del SKU anterior;
cambiar controladora/GPS reabre el catálogo como el ESC;
y si la misión es vigilancia, simular tampoco te empuja a “más carga útil”.
```

---

## 1. You (Claude)

1. Implement A (ESC omit-key + FC/sensor bind siblings as locked).  
2. Implement B (rebind + refresh wiring).  
3. Implement C (mission gate on SuggestionEngine consumers).  
4. Tests T1–T12 + report. Guide trap one-liners if still claiming the bugs.  
5. No version bump. No workspace write.

**STOP if** forced to invent catalog rows, axial geometry, or a new Conversation Engine.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | `bind_esc_from_catalog(new_sku_without_H, base=old_with_H)` → result has **no** `height_mm` |
| T2 | Same bind preserves `mounted_on` / pose fields from base |
| T3 | FC bind omit-key: base had H, new FC row omits H → no leaked `height_mm` |
| T4 | `resolve_idle_catalog_rebind("cambiar controladora")` → `flight_controller` |
| T5 | `resolve_idle_catalog_rebind("cambiar gps")` → `sensors` |
| T6 | Orchestrator IDLE: those phrases offer identity catalog (message contains numbered FC/GPS options or locked assist format) |
| T7 | `actualiza el fc` / `actualiza el gps` resolve refresh keys (or documented refuse if refresh writer cannot — prefer success path) |
| T8 | Mission active + high margin: simulate suggestions list has **no** `increase_payload` / “aumentar la carga útil” |
| T9 | Mission active: ReasoningLayer with injected `increase_payload` suggestion does **not** enrich that label; waterfall/alternate instead (or suppress) |
| T10 | Neutral mission + high margin: `increase_payload` still present (regression) |
| T11 | Continuity #1 tests still green unmodified (or only intentional shared-helper edits) |
| T12 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. **ESC omit:** project with SpeedyBee ESC (has H) → `cambiar esc` → pick Skystars (no catalog H) → `estado`/component props must **not** show SpeedyBee height as if Skystars declared it (unless user re-applies `declara el esc estimado …`).  
2. **FC rebind:** `cambiar controladora` → see FC list → pick one → identity updates. Same optional for `cambiar gps`.  
3. **Mission suggestions:** on vigilancia (or throwaway with vigilancia objective + high margin) → `simular` → suggestions must **not** lead with “aumentar la carga útil”; Continuity/`estado` still mission-aware as #1.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| More identity rules (payload/arm/…) | Queue **#5** |
| Axial prop↔motor / HD-005 | Parked |
| plate-box / Path N | Parked |
| Full SuggestionEngine redesign | Only `increase_payload` mission gate |
| Motor/prop/battery/frame omit-key if not shared-helper’d | Residual OK if reported |

---

## 5. Done when

- [ ] ★  
- [ ] A + B + C + T1–T12 + report (+ guide trap patch)  
- [ ] Cursor review PASS  
- [ ] Engineer smoke ACCEPT (or waive)

---

## 6. Handoff

```text
Engineer → ★ B1-catalog-hygiene-mission-suggestions (this IC)
Claude   → implement A/B/C + tests + report
Cursor   → review
Engineer → smoke §3
```
