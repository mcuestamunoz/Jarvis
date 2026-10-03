# Implementation Review — Connect plugs / real-data debt map (`B1-connect-plugs-real-data-map`)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T33 implementado…”)  
**Against:** [IC](implementation_contract_connect_plugs_real_data_map_b1.md) · [report](implementation_report_connect_plugs_real_data_map_b1.md) · [DC ★](design_contract_connect_plugs_real_data_map_b0.md) · [map](engineer_note_connect_plugs_real_data_map.md)  
**Tip reviewed:** `e39a4ce` on `cursor/connect-plugs-real-data-map-impl-8ac5` (parent authorize `6656ac1` / T31 ★ `v0.6.40`; parallel to T32 tip)  
**Verdict:** **PASS** — await Engineer ★ ACCEPT → tag **`v0.6.42`**. **No ACCEPT claim in this pass.**

**Process note:** Claude Code implemented under ★ AUTHORIZED IC. This is the independent Cursor review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Blind copy of seed status | **Clear** — `sd-go-to` / metadata plug marked **Implemented, not yet landed** after confirming `_resolve_go_to_destination` / `parse_go_to_destination` absent on this tip |
| Missing seed ids | **Clear** — T3 locks all §0b ids incl. `hd-001`…`hd-005` expanded |
| Wrong table columns | **Clear** — header `id \| type \| deferred \| seam_today \| connect_later \| status \| evidence` in A/B/C/D |
| Claimed closing debts | **Clear** — map OPEN living; SD-GO_TO note Status untouched |
| `src/` behavior change | **Clear** — T33 commit touches no `src/` |
| Taxonomy / purpose drift | **Clear** — A/B/C/D legend; “not a roadmap” intro |
| Extension honesty | **Clear** — `ui-intent-ingress` called out as forensic add (UI enum, no adapter) |
| Tip / package | **Clear** — `0.6.42`; tip-pin + ESC green |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 living SoT map OPEN | **PASS** |
| §0.3 forensic re-verify, not blind seed | **PASS** |
| §0.4–5 seed ids + exact columns; Gaps marked | **PASS** (+ `ui-intent-ingress`) |
| §0.6 PRIORIDAD / PLATFORM / CONNECTIONS / optional pointers | **PASS** |
| §0.7 `0.6.42` · no `src/` · fences | **PASS** |
| §0.8 tests T1–T4 | **PASS** |
| §0.9 Out list | **PASS** |

---

## 2. Verification (this pass)

```text
PYTHONPATH=/workspace python3 -m pytest \
  tests/test_connect_plugs_real_data_map_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 23 passed
```

Spot-checks: T32 symbols absent here; tick helper only HOLD/LAND/GO_TO; no `z_m=` in orch autonomy path; no `world/` package; `IntentSource.UI` with no `UiIntentAdapter`.

Report full-suite claim (3957 / +4) not re-run here.

---

## 3. Notes

**N1 — Process / tip stack.** T33 tip correctly documents T32 as sibling-not-landed. On Engineer ★ ACCEPT of both pending Buys, stack T32 tip under this map tip and update `sd-go-to` / `go-to-metadata-plug-for-world` rows to reflect T32 ★ CLOSED. **Not blocking review.**

---

## 4. Next

```text
Cursor: PASS @ e39a4ce (+ review commit)
Await: Engineer ★ ACCEPT T32 → v0.6.41 · T33 → v0.6.42 (stack tips)
```
