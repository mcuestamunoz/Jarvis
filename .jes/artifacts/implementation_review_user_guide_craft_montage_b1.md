# Implementation Review — User command guide to craft montage B1

**Date:** 2026-09-14  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_user_guide_craft_montage_b1.md) · [inventory](inventory_user_facing_commands_craft_montage_b0.md) · [report](implementation_report_user_guide_craft_montage_b1.md) · [guide](../../docs/USER_GUIDE_CRAFT_MONTAGE.md)

**Verdict:** **PASS WITH NOTES** — ready for Engineer cheatsheet walk on `10-min-autonomía`

---

## Checklist

| Gate | Result |
|---|---|
| Phase 0 inventory before guide (lock #5) | **Pass** — inventory artifact complete; report documents STOP gate honored |
| 14 IDLE bridges in dispatch order | **Pass** — matches `orchestrator.py` `_try_handle_*` Continuity block (mounted_on → idle_frame_part) |
| All 19 `*_assist.py` traced | **Pass** — every module name appears in inventory |
| Phrase truth (lock #6) | **Pass** — spot-check triggers resolve: `parece un dron`, `relaciones`, `apilar en placa`, `montajes estandar`, `declara el esc estimado 8 mm`, `cambiar esc`→`esc`, `cambiar controladora`→`None`, `actualiza el esc`→`esc`, `actualiza el fc`→`None`; §10 pose phrases parse SET with live z |
| Endpoint ≠ ASSEMBLY READY (lock #4/#7) | **Pass** — §1 + §9 + appendix; silhouette = checklist; estimated blocks documented |
| Scope / no product code | **Pass** — guide Buy deliverables are docs + `.jes` artifacts; no claim of src edits for this Buy |
| Length / TOC | **Pass** — 406 lines; TOC matches report; §10 worked example justified |
| Gaps documented | **Pass** — inventory §10 + guide §12.2 (FC rebind, refresh, envelope exclusions, bind_esc leak, disk attest, single pack) |
| Version | **Pass** — `0.4.1` untouched |

---

## Independent checks (Cursor)

1. Recounted **14** Continuity `_try_handle_*` and **19** assists — match inventory counts.  
2. Parser/trigger spot-checks (above) — including negative FC rebind/refresh.  
3. Live `10-min-autonomía` poses: ESC z=**5.0**, FC **4.9**, battery **15.5**, sensors **8.2** — match guide §10 (not the stale 5.75).  
4. **Mount ambiguity on 10-min:** `el esc montado en la placa` → `AMBIGUOUS_TARGET` (three plates). `… en frame_plate` / `… en top plate` → SET.  
5. Drafting error transparency in report (hand-computed z caught) — good process.

### Review-time doc fixes (Cursor, guide only)

Applied before smoke so the cheatsheet walk is not blocked:

| Fix | Why |
|---|---|
| §6 / §10 / cheatsheet mounts → `frame_plate` + multi-placa callout | Live 10-min rejects bare `la placa` |
| §7.3 + cheatsheet ESC pose `5.75` → `5.0` | Align with live state / corrected §10 |
| Appendix `### 11.1/11.2` → `### 12.1/12.2` | Numbering under §12 |

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Fixed in review | Multi-placa mount ambiguity was a **real** trap for the named smoke project; guide now warns and uses `frame_plate`. Inventory could add one gap row later (optional). |
| **N2** | Soft | Report said a PRIORIDAD status line was touched; cola still showed “IC ready” until this review — Cursor syncs PRIORIDAD below. Harmless. |
| **N3** | Process / future | No automated “guide ↔ inventory” drift check (report already flags). Future Continuity-regex Buys should touch the guide. |
| **N4** | Info | §10 numbers are snapshots of live 10-min — will drift if that project changes (accepted). |

---

## Smoke script (Engineer)

On **`10-min-autonomía`** (read-mostly; avoid re-applying poses already set):

1. Open [`docs/USER_GUIDE_CRAFT_MONTAGE.md`](../../docs/USER_GUIDE_CRAFT_MONTAGE.md) §11 cheatsheet.  
2. Fire non-mutating: `estado`, `montajes estándar`, `apilar en placa`, `relaciones`, `parece un dron`, `cabe el esc`.  
3. Confirm honesty: estimated plate/ESC → blocked / B\*; footer not ASSEMBLY READY.  
4. Optional: confirm `cambiar controladora` does nothing (gap).  
5. ACCEPT → Cursor closes Buy.

---

## Verdict

**PASS WITH NOTES** — Phase 0 depth and Phase 1 honesty meet the IC. Awaiting Engineer cheatsheet ACCEPT.
