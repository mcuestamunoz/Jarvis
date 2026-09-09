# Investigation Report — Mapping rung 2 first cut: wheelbase on the bound frame spec

**Date:** 2026-09-09  
**Investigator:** Cursor  
**Contract:** [investigation_contract_geometry_wheelbase_on_spec_b1.md](investigation_contract_geometry_wheelbase_on_spec_b1.md)  
**Checkpoint:** package `0.3.8` · suite **2462** · `ca7a290`

---

## Executive lean

**B1 — lock the existing bind/refresh path with a stale-frame regression test, then smoke `actualiza el frame` on the live demo.**

There is **no missing binder**. `bind_frame_from_catalog` already projects seed `wheelbase_mm`. The live Rooster card is **stale ProjectState** (bound before that projection landed; catalog-refresh smoke only walked the ESC). The Board already prints every `properties` key. Auto-refresh and catalog overlay are dishonest. Four-motor instancing is a **later ★**, not this cut.

---

## 1. Binder already projects

`library/frames/_datos.json` `armattan_rooster_5in.wheelbase_mm` = **230** (Armattan motor-to-motor).

`catalog_bind.bind_frame_from_catalog` (lines 318–321) copies it as `PropertyValue(..., unit="mm", source="declared")` when the seed is not `None`.

Covered: `tests/test_frame_parts_graph_v1.py::test_bind_frame_from_catalog_projects_wheelbase_and_configuration` asserts 230 and `configuration=quad_x`.

`refresh_component_from_catalog` dispatches `family=="frame"` to that same binder with `base=spec`. Catalog-refresh tests **never** assert a stale frame grows `wheelbase_mm` (N3 in that review only dry-ran the demo).

---

## 2. Live census (file, not memory)

`workspace/autonomía-de-10min-9ada1a1b0cca/state.json` `components.frame`:

| Key | Live |
|---|---|
| `catalog_ref` | `frame` / `armattan_rooster_5in` |
| `properties` | `mass_kg` 0.125 · `size_class_inch` 5 · `material` fibra de carbono |
| `wheelbase_mm` | **absent** |
| `configuration` | **absent** |
| `declared_box_pose` | `null` |
| children | `frame_arm` / four plates / cage / standoff present via `parent_key` |

Matches the mapping-path lock. Not a missing seed row.

---

## 3. Refresh dry-run (in-memory, not saved in this report)

`refresh_component_from_catalog` on a copy of that spec must merge seed projection over `base.properties`. Expected new keys: `wheelbase_mm` 230, `configuration` `quad_x`. `mass_kg` / `material` stay. Writer only replaces `components["frame"]` — plate/arm siblings are out of scope by construction (catalog-refresh report §).

Parse already maps `"actualiza la frame"` → `"frame"` (`test_t4_parse_set`).

---

## 4. Projector does not backfill

`spatial_board._fields` walks `spec.properties` only. No `library.get_frame`. A stale frame card **must not** show 230 until ProjectState has the property. Confirmed by construction; this Buy should keep a test that stale state stays silent.

Wheelbase is **not** an envelope for `_geometry_from_spec` (no L×W×H). After this cut the frame still has **no** CSS 3D solid. Honest: text on the card, not a quadrotor silhouette.

---

## 5. Code hole vs state hole

| Layer | Hole? |
|---|---|
| Seed | No — 230 cited |
| `bind_frame_from_catalog` | No — projects |
| Fresh catalog pick | No — new binds get 230 |
| `refresh_component_from_catalog` | Path exists; **untested** for this growth |
| Live demo | **Yes** — never refreshed after binder growth |
| `_fields` | No |
| Board load auto-refresh | Must remain **absent** (refresh IC lock 6) |

---

## 6. Leans scored

| Lean | Verdict |
|---|---|
| **B0** walk-only | Honest but the refresh growth stays untested (catalog-refresh N3 was awareness only) |
| **B1** test lock + live smoke | **Buy** — no new writer; no second SoT |
| **B1+** projector reads `library.frames` | Reject — ProjectState is SoT |
| **B2** Scene3D 230 mm glyph | Later ★ after the number exists; not this cut |
| **4 motors** | Mapping path: separate ★ after spec has wheelbase |

**B0 remains available** if Engineer wants only the demo walk. Not recommended: the exact failure mode (stale bound frame) has no named pytest today.

---

## Risks

- Refresh also projects `configuration` (`quad_x`) — honest binder growth, same class as catalog-refresh N3. Smoke copy must not say “only wheelbase” if both appear.  
- Live `motor_count` on the demo is **3** in `current_parameters` vs Structure `4` — do **not** “fix” by instancing motors in this Buy.  
- Do not treat card 230 mm as a 3D span.

---

## Out of this Buy

N-motor copies · Scene3D line · plate L×W · motor 31.7 · auto-refresh · fit/`cabe` · version bump · Here3
