# Implementation Review — Cited kit layout pack B1 (`B1-layout-pack-cited`)

**Date:** 2026-09-13  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_geometry_layout_pack_cited_b1.md) · [report](implementation_report_geometry_layout_pack_cited_b1.md)

**Verdict:** **PASS WITH NOTES**

---

## Checklist

| Gate | Result |
|---|---|
| Pack id `hglrc_my5_flush_stack_b1` from §0.1 only | **Pass** — registry rows = FC/ESC/battery/sensors → `frame_plate`; motors/props/arm excluded (tested) |
| Formula-at-propose-time z; bag floats = fixture only | **Pass** — `flush_centered_z_mm`; T1 live-recompute ≠ frozen 5.0 |
| Authority / supuesto disclosure in copy | **Pass** — header + per-row reason; no CAD / VERIFICADO claim |
| Suggest-only IDLE; confirm = retype existing writers | **Pass** — bridge never writes; pose+mount phrases round-trip real parsers (T1) |
| `requires_plate_box` honest skip | **Pass** — T3; `[]` = missing plate only |
| Origins box-only; disk writer gate unweakened | **Pass** — T4 |
| No invent XY / body 225×200 / arm radial | **Pass** |
| No workspace mutation / version still `0.4.1` | **Pass** |
| T1–T5 + report | **Pass** — suite **2830** passed, 1 skipped (Cursor re-ran) |
| Path F N1 (sibling) closed in same cycle | **Pass** — live 10min + 5min Path F show `✓ done`, not false “no placa” |

---

## Independent checks (Cursor)

1. `pytest tests/test_geometry_layout_pack_cited_b1.py tests/test_geometry_craft_montage_path_f_b1.py` → **34 passed**.  
2. Full suite → **2830 passed, 1 skipped**.  
3. `pyproject.toml` version **`0.4.1`**; `git status -- workspace/` empty.  
4. Live read-only `propose_layout_pack` / `format_layout_pack` (and Path F) on both projects:  
   - **10-min** and **5min:** all four subjects **`done`** (pose+mount already declared after Engineer mount smoke) — honest “nada pendiente”, **not** “falta la caja”.  
5. Triggers: `layout pack` and `aplicar layout hglrc_my5_flush_stack_b1` → pack id.  
6. Mount phrases use Spanish nouns (`la controladora montada…`, `el sensor montado…`) — **parse SET** via real mount assist (avoids the separate key-tip bug in mount-standard ambiguous tips).

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Smoke hygiene | Both live smoke projects are **fully done** for this pack. §3 “retype one phrase → Board” needs a **clean project**, or clear one pose/mount first (`quita la pose…` / clear `mounted_on`), or rely on the fixture path already covered by tests. Listing-only smoke (`layout pack` → ✓ rows + supuesto header) still works on 10min/5min. |
| **N2** | Confirmed OK | Explicit `kind="done"` + `✓` vocabulary is clearer than omitting rows; Cursor **accepts** it for this family (closes Path F N1 the same way). |
| **N3** | Follow-up (not a fail) | Bare `layout pack` → sole pack today. Second pack needs a real list/select path (report already flags). |
| **N4** | Optional honesty | Registry stores `kit_frame_sku: hglrc_my5_5in` but propose does **not** gate on live frame SKU — any project with a boxed `frame_plate` can run the pack (copy still names MY5 smoke authority). Acceptable for first kit + Path F arithmetic; gate later if a second kit pack lands. |
| **N5** | Orthogonal open | Mount-standard ambiguous tips still suggest raw keys `flight_controller` / `sensors` that the mount parser rejects ([FN](field_note_mount_ambiguous_tip_parse_mismatch_b0.md)). Layout-pack phrases do **not** share that bug. |

---

## Verdict

**PASS WITH NOTES** — matches IC; honesty lock held; N1 Path F closed; suite green.

**Engineer smoke §3:** prefer trigger `layout pack` on 10min (expect all ✓ / nada pendiente) **or** clear one subject then retype a listed pose/mount phrase. No auto-apply on reload.

**Cola after ACCEPT:** silhouette Product B (prereq-gated) · plate caliper · mount tip/parse align · second-pack listing when needed.
