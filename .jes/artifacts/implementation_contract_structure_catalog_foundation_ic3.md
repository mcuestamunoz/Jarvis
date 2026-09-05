# Implementation Contract — Structure Catalog Foundation IC-3 (assist)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · IC-3 **CLOSED**  
**Review:** [implementation_review_structure_catalog_foundation_ic3.md](implementation_review_structure_catalog_foundation_ic3.md)  
**Report:** [implementation_report_structure_catalog_foundation_ic3.md](implementation_report_structure_catalog_foundation_ic3.md)  
**Suite:** **2197**  
**Type:** **Product UX** — show curated frame catalog + numbered pick + bind.  
**Not** new Structure physics. **Not** PASS-by-catalog. **Not** CAD/layout. **Not** ranking/DSE.

**Parents:**
- [engineer_ratification_structure_catalog_foundation_ic3.md](engineer_ratification_structure_catalog_foundation_ic3.md) — ★ product Buy
- [implementation_contract_structure_catalog_foundation_ic2.md](implementation_contract_structure_catalog_foundation_ic2.md) — **CLOSED** (suite **2188** + N1/N2 closed)
- IC-1 schema+seed **CLOSED**

**Baseline:** tag **`v0.3.6`** · IC-1+IC-2 landed · suite **≥2188**

**Buy:** Make IC-2 reachable in CLI so the user can **see and choose** real frames — mental mapping of the design space.

---

## 0. You

- Prefer mirroring **battery** assist shape (full curated list; no motor↔prop matching complexity).
- Reuse `bind_frame_from_catalog` + `set_frame_material(..., catalog_ref=, component_name=)` — **no** parallel binder.
- Reuse shared help-choose helpers from `motor_catalog_assist` (`is_help_choose_phrase`, `match_suggestion_by_input`) — do not duplicate phrase logic.
- Do **not** invent SKUs or expand seed beyond IC-1 rows (read-only).
- Do **not** wire `catalog_bound` into Structure PASS / `_derive_subsystem_verdict`.
- Do **not** change LEVEL A screening semantics.
- Do **not** add wheelbase / fit / strength claims in list copy.
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 1. Intent

```text
Frame pending (COMPONENT / architecture gap / fail-routing)
  → acquisition brief offers: free-text OR "ayúdame a elegir"
  → ayúdame a elegir
  → numbered list from library/frames (manufacturer, model, mass, class)
  → pick N
  → bind_frame_from_catalog(sku) → set_frame_material(..., catalog_ref=...)
  → estado/BOM can show [sku]; Structure A LEVEL A still applies
```

Free-text declare remains valid forever.

**Honesty in UX copy (locked idea, Spanish OK):** choosing a catalog frame means
*identity + declared mass/class from catalog* — **not** “estructura validada”,
**not** “la hélice cabe”, **not** ASSEMBLY_READY.

---

## 2. Locked behavior

### 2.1 Assist module — `frame_catalog_assist.py` (new)

Thin module (battery-class):

| Helper | Behavior |
|---|---|
| `build_frame_catalog_suggestions(project_state \| None)` | `ComponentLibrary.list_frames()` → list of dicts. **No ranking**, no filter inventiveness. Order = library list order (stable by name as `list_frames` already sorts). |
| `format_frame_catalog_suggestions(suggestions)` | Numbered Spanish list. Each line must expose enough for mental mapping: **manufacturer / model**, **mass**, **size class** (and SKU id). If empty library: honest empty message (should not happen with IC-1 seed). |
| Pick matching | Reuse `match_suggestion_by_input` (number or exact sku/name patterns already used by other families). |

Suggestion dict minimum keys: `name` (sku), `manufacturer`, `model`, `mass_g`, `size_class_inch` (and whatever format needs). Do **not** include wheelbase/geometry.

### 2.2 Session state

Add `frame_suggestions: list[dict] = []` on `InteractiveSessionState` (same tier as `motor_suggestions` / `propeller_suggestions` / `battery_suggestions`).

When offering frame list: set `frame_suggestions`, **clear** the other three suggestion lists (same cross-family rule as battery offer).

When offering another family’s list: clear `frame_suggestions` too (update motor/propeller/battery offer sites that already clear peer lists).

### 2.3 Orchestrator — offer / apply

Mirror `_offer_component_battery_catalog` / `_apply_component_battery_catalog_pick`:

1. **Offer** when user says help-choose and frame is the active component target (COMPONENT sub-mode / expected_keys[0]=="frame" / equivalent frame-pending path already used for free-text). Also allow IDLE / re-bind upgrade when frame exists but `catalog_ref is None` **if** that pattern is already how battery/propeller handle freeform→SKU — match the smallest existing family pattern; do not invent a third incompleteness theory.
2. **Apply** pick → `bind_frame_from_catalog(sku)` → `set_frame_material(mass_kg, material or None, size_class_inch, catalog_ref=..., component_name=sku)` → persist project → advance wizard / follow-up like other component binds.
3. Material absent on seed (TBS): pass `material=None` — writer must not invent; completeness stays honest (`medium` if material missing).

### 2.4 Acquisition brief

In `acquisition_brief.py`, extend the catalog CTA so **`frame`** also gets:

```text
• decir 'ayúdame a elegir' para ver candidatos numerados del catálogo
```

Update the comment that currently says frame has no bind path.

Optional one-line in frame brief: free-text still OK (mass/material/class).

### 2.5 Continuity / claim-copy

Do **not** rewrite Continuity “Diseño validado” or claim-copy class suffixes in this IC.  
Do **not** add Continuity pressure that requires catalog bind for structure.

If Continuity already mentions catalog help for motors only, **do not** expand Continuity scope unless a one-line frame next-step already exists and naturally should mention help-choose — prefer acquisition brief + COMPONENT path as the primary surface.

### 2.6 Explicitly unchanged

- `frame_class_compatibility_state` / GAP-FRAME-* builders  
- Seed JSON  
- IC-2 diverge / BOM resolve (consume them; don’t rework)  
- DSE / ranking / “best frame for thrust”  

---

## 3. Forbidden

- Fuzzy free-text → silent SKU match  
- Inventing frames not in `library/frames`  
- Claiming fit / strength / validated structure from a pick  
- Making structure incomplete solely because unbound  
- Expanding seed marketplace-style  
- CAD / layout / FEA  

---

## 4. Tests (mandatory)

1. `build_frame_catalog_suggestions` returns all IC-1 seed SKUs (≥2 classes).  
2. `format_frame_catalog_suggestions` includes mass + size class + identity (smoke assert on substrings).  
3. Offer path: help-choose with frame pending → `frame_suggestions` populated; peer suggestion lists cleared.  
4. Apply path: pick index → project frame has `catalog_ref.family=="frame"`, `structure_mass_override_kg` matches projected mass, `sku_resolved` True for that sku.  
5. TBS-style seed without material → bind/apply does not invent material.  
6. Free-text frame path still works (regression smoke).  
7. LEVEL A still fires on bound class vs oversized prop (reuse IC-2 idea; may be thinner).  

Full suite green. Prefer extending existing CLI/catalog assist tests rather than a giant new harness.

---

## 5. Files allowed

| Path | Change |
|---|---|
| `src/jarvis/core/frame_catalog_assist.py` | **NEW** — build/format suggestions |
| `src/jarvis/schemas/action_schema.py` | `frame_suggestions` on session |
| `src/jarvis/core/orchestrator.py` | offer/apply frame catalog; clear peers on other offers |
| `src/jarvis/core/acquisition_brief.py` | advertise help-choose for `frame` |
| `src/jarvis/core/battery_catalog_assist.py` / `propeller_catalog_assist.py` / motor offer sites | Only if needed to clear `frame_suggestions` when those families offer |
| `tests/…` | Mandatory tests |
| `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` | One status-table row: IC-3 assist landed (optional but preferred) |

**Not allowed:** `engineering_readiness.py` verdict changes, Continuity claim rewrites, `library/frames/_datos.json` expansion, CAD/layout modules.

---

## 6. Done when

1. §2.1–§2.4 complete.  
2. Mandatory tests + full suite green.  
3. Implementation report: product surface before/after; honesty copy; no physics change.  
4. Cursor review PASS / PASS WITH NOTES.  
5. **CLI walk recommended** (unlike IC-1/IC-2): Engineer or Cursor walks “frame pending → ayúdame a elegir → pick N → estado shows sku / LEVEL A still honest.”

---

## 7. Out

| Item | Status |
|---|---|
| Frame ranking / “best for my prop” | Out |
| Continuity redesign | Out |
| Layout / CAD / FEA | Out |

---

## 8. Engineer gate

**Do not implement until Engineer `procede` on this IC.**  
If no → edit this IC in place.
