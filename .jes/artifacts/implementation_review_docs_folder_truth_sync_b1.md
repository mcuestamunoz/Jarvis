# Implementation Review — Docs folder truth sync @ v0.4.2 (`B1-docs-folder-truth-sync`)

**Date:** 2026-09-18  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_docs_folder_truth_sync_b1.md) · [inventory](inventory_docs_folder_truth_sync_b0.md) · [report](implementation_report_docs_folder_truth_sync_b1.md)  
**Verdict:** **PASS WITH NOTES**

---

## Summary for Engineer

Claude audited all **37** `docs/` files, updated living banners/content to **`v0.4.2` / Fase M CLOSED / Fase C await ★**, stamped **7** historical files without deleting bodies, and filled real gaps (Acquisition cameras/vtx, Continuity mission ladder, Authority mass/power mirrors).  

Separately (user-approved, outside pure-docs scope): narrowed IDLE first-acquire catalog open back to **`("vtx", "cameras")`** after an over-broad fix had stolen FN-009 / terrestrial wizard turns. Targeted regressions green; report cites suite **3166**.

---

## Locks

| # | Lock | Result |
|---|---|---|
| 1–2 | Buy · `docs/` only as primary deliverable | **Pass** — inventory + report + docs edits present |
| 3 | Code > prose; don’t “fix” product via docs | **Pass** — content matches code anchors reviewed |
| 4 | Epoch `v0.4.2` / M7 / Fase C await ★ | **Pass** — PRIORIDAD, ARCHITECTURE, ERV, system_map master/canvas |
| 5 | Phase 0 inventory before bulk edits | **Pass** — `inventory_docs_folder_truth_sync_b0.md` (37 rows) |
| 6–7 | Label obsolete; don’t silent-delete archives | **Pass** — 7 HISTORICAL banners; BUGS/refactors bodies intact |
| 8 | IMPLEMENTATION_TASKS: living header only | **Pass** — suite 3166; closed history not boiled |
| 9 | System map: cameras/vtx · no invent C-xxx | **Pass** — CONNECTIONS trail + Acquisition/Continuity; no new C-xxx |
| 10 | USER_GUIDE phrase truth | **Pass** — verified leave-alone; already current from Fase M |
| 11–12 | Vision banners · no firmware claims | **Pass** |
| 13 | No version bump | **Pass** — still `0.4.2` |
| IC outputs | Inventory · report · obsolete register | **Pass** — register = report § Obsolete |

---

## Prerequisite `src/` fix (N1 — process)

| Item | Assessment |
|---|---|
| Problem | First-acquire `_open_catalog` widened to **all 9** families → stole FN-009 thrust help + terrestrial transmission wizard |
| Fix | `_rebind_key in ("vtx", "cameras")` only when absent/stub (`orchestrator.py`) |
| Honesty | Report separates this from docs Buy; comments cite regressions |
| Cursor check | Code matches report; `test_assisted_acquisition` FN-009 filter + `test_cli_polish` t8 + VTX absent-open: **pass** (targeted) |
| Note | IC said docs Buy must not change `src/` — **exception** with Engineer sign-off is acceptable; treat as **hotfix recorded in docs Buy report**, not as silent scope creep |

---

## What changed (detail)

### A. Living banners / PRIORIDAD / version (epoch sync)

| File | What Claude did |
|---|---|
| `IMPLEMENTATION_TASKS.md` | Suite **3165→3166** in PRIORIDAD; D1 still shows IN FLIGHT in working tree (review should flip CLOSED — N2) |
| `ARCHITECTURE.md` | Replaced “still v0.4.1 / closeout lean” living paragraph; appended **Fase M CLOSED @ v0.4.2** + changelog bullets |
| `ENGINEERING_READINESS_VISION.md` | Status/Date → v0.4.2 / suite 3166 / PRIORIDAD Fase C await ★; queue pointer line fixed; deeper dated “Fit VERIFIED” left historical |
| `system_map/README.md` | Date line → v0.4.2 / 3166 |
| `system_map/JARVIS_SYSTEM_MAP.md` | Product checkpoint paragraph → Fase M ladder + Fase C await ★ |
| `system_map/CONNECTIONS.md` | New dated trail entry for full Fase M arc; **no new C-xxx** |
| `system_map/DIAGRAMS.md` | Epoch + PRIORIDAD trailing fix |
| `system_map/00_entry/ENTRY_MAP.md` | Epoch includes v0.4.2 / Fase M |
| `jarvis-system-map.canvas.tsx` | Queue callout → Fase C await ★; new “Shipped — Fase M @ v0.4.2” callout; old v0.4.1 shipped callout kept dated |

### B. Substance gaps filled (code-truth content)

| File | What Claude added |
|---|---|
| `ACQUISITION_MAP.md` | `camera_catalog_assist` / `vtx_catalog_assist` / esc assist rows; full `bind_*` list incl. camera/vtx; **9 rebind families**; first-acquire scoped to vtx/cameras + regression history; `video_link`/`vtx` in SYSTEM_DEFINITION note |
| `CONTINUITY_MAP.md` | `mission_mass_declare_assist` / `mission_power_declare_assist`; full **mission Continuity waterfall**; cameras/vtx classify `"defined"` note; Fase M tests listed |
| `AUTHORITY.md` | Rows for `set_mission_component_mass` (incl. vtx) and `set_mission_component_power` (**vtx excluded** / RF≠W) |
| `CALCULATION_MAP.md` | `mission_accessory_power_w` additive autonomy note |
| `PHYSICAL_COMPONENT_CATALOG_V1.md` | §13 note: `library/cameras` + `library/vtx` exist |
| `PHYSICAL_PROPULSION_ENGINE_PHASE2.md` | Epoch check: HD-004 unaffected by Fase M |
| `PROJECT_CONTINUITY.md` | Pointer to mission Continuity extensions / CONTINUITY_MAP (no SoT fork) |

### C. HISTORICAL / OBSOLETE banners only (bodies untouched)

`BUGS.md` · `CLI_TESTS.md` · `CODE_AUDIT_CORE.md` · `FASE_LLM.md` · `fixes/human_layer.md` · `refactors/domain_registry_refactor.md` · `refactors/iterate_interactive_session_refactor.md`

### D. Audited, left alone (agree)

`HARDWARE_DEBT.md` · `PLATFORM_CAPABILITY_VISION.md` · root `JARVIS_SYSTEM_MAP.md` stub · `USER_GUIDE_CRAFT_MONTAGE.md` · `MISMATCHES.md` · `HANDOFF_CONTEXT_DESIGN.md` · `FLOWS.md` · subsystem maps without stale claims (`01_runtime`, `02_intent`, `04_engineering`, `05_iteration`, `07_simulation`, `09_state`, `10_llm`)

### E. Tests / package pins (ancillary)

Several Fase M tests: package pin **`0.4.1`→`0.4.2`** (report: drift after M7 bump). Honest maintenance for suite green.

---

## T1–T9 (Cursor re-check)

| ID | Result |
|---|---|
| T1 | **Pass** — 37 files; inventory complete |
| T2 | **Pass** — remaining `0.4.1` / suite 2968 are dated historical |
| T3 | **Pass** — living PRIORIDAD ≠ Fit VERIFIED / closeout lean / M7 GATE AHORA |
| T4–T5 | **Pass** — Acquisition + Continuity + USER_GUIDE name cameras/vtx / 9 families |
| T6 | **Pass** — USER_GUIDE leave-alone justified |
| T7 | **Pass** — 7 stamps |
| T8 | **Pass** — report table + leave-alone list |
| T9 | **Pass** — rg sanity; historical “Fit VERIFIED” only inside dated SHIPPED @ v0.4.0/0.4.1 block |

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Process / good | Prerequisite orchestrator narrow — correct; keep documented in Acquisition map (done). Optional later: tiny dedicated hotfix note if you want SoT outside this docs report. |
| **N2** | Soft | `IMPLEMENTATION_TASKS` / cola still say D1 **IN FLIGHT** — Cursor will mark **CLOSED** on this review accept path. |
| **N3** | Info | Report said “22 files edited”; git shows ~24 docs paths + orchestrator + test pins — counting difference only; substance OK. |
| **N4** | Soft | CONNECTIONS historical trail lines still say “Queue: idle / holds…” inside **dated** 2026-09-13→15 entries — acceptable under lock #7; living trail entry is correct. |
| **N5** | Named debt (pre-existing) | HANDOFF/MISMATCHES H1–H5 appendix reconciliation — correctly deferred. |

---

## Out of scope confirmed

Root VISION/PRODUCT_SCOPE/README · inventing Fase C · new C-xxx · firmware claims · boiling BUGS/IMPLEMENTATION_TASKS history · version bump.

---

## Next

```text
Engineer → spot-check PRIORIDAD + ARCHITECTURE header + USER_GUIDE cámara/vtx (optional smoke)
Cola     → D1 CLOSED · U1 board-3d-first-inspector READY next ★
```
