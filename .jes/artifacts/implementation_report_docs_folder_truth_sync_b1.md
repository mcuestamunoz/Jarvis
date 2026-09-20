# Implementation Report — Docs folder truth sync to code @ v0.4.2 (`B1-docs-folder-truth-sync`)

**IC:** [implementation_contract_docs_folder_truth_sync_b1.md](implementation_contract_docs_folder_truth_sync_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-18
**Inventory:** [inventory_docs_folder_truth_sync_b0.md](inventory_docs_folder_truth_sync_b0.md)
**Baseline:** package `0.4.2` (unchanged, no version bump) · suite **3166 passed, 1 skipped** · no UI changes (this is a docs-only Buy)

---

## Prerequisite fix (src/, outside this IC's own scope, done with explicit user sign-off before Phase 0)

Before starting the audit, `pytest` showed 9 failures — 6 were trivial `0.4.1`→`0.4.2` version-pin drift in my own test files from the immediately-preceding Fase M Buys (package was bumped externally during the M7 closeout, between my last check and this session), harmless. The other 2 (`test_assisted_acquisition.py::test_fn009_idle_thrust_help_*` ×2, `test_cli_polish.py::test_t8_terrestrial_definir_motores_still_opens_transmission_wizard`) were real, deterministic behavior regressions already shipped in the `v0.4.2` tag (commit `9878e6c`): an external fix (addressing the real VTX/cameras "first-time acquisition never opened the catalog" smoke finding) widened `orchestrator.py`'s IDLE catalog-rebind `_open_catalog` condition to fire on first-time acquisition for **all nine** catalog families, not just the two that actually lacked a first-acquisition path (`vtx`, `cameras`) — silently stealing turns from `motors`' thrust-aware FN-009 bridge and the terrestrial transmission wizard.

Since this directly contradicted the docs Buy's own "suite green at ★" checkpoint, and since a docs Buy asserting a queue/architecture status that includes a known-red suite would itself be dishonest, I flagged it to the user before proceeding (`AskUserQuestion`) rather than silently fixing or silently ignoring it. User chose "fix it first, then do the docs Buy." Fix: narrowed the first-time-acquisition branch back to `("vtx", "cameras")` only, restoring the other seven families' more specific bridges. Verified: both regressed test files pass again, the original VTX smoke-fix test still passes, and the full suite is green (**3166 passed, 1 skipped**, up from 3165 pre-fix by the one net new smoke-regression test). No IC/report of its own — recorded here since it's the reason "suite green" holds for this Buy's own checkpoint, and because the docs edits below (ARCHITECTURE.md, ACQUISITION_MAP.md) reference it directly as living debt/history.

---

## Phase 0 — Inventory

37 files under `docs/` (`find docs -type f | wc -l` = 37, matches the IC's own baseline exactly). Full file-by-file table + stale-claim table + missing-doc gaps + out-of-scope leftovers: [inventory_docs_folder_truth_sync_b0.md](inventory_docs_folder_truth_sync_b0.md).

**Summary:** 6 files needed no change (already accurate/well-framed: `HARDWARE_DEBT.md`, `PLATFORM_CAPABILITY_VISION.md`, root `JARVIS_SYSTEM_MAP.md` stub, `MISMATCHES.md`, `HANDOFF_CONTEXT_DESIGN.md`, `FLOWS.md`); `IMPLEMENTATION_TASKS.md`'s own PRIORIDAD header was **already** correctly synced (`v0.4.2`, Fase M CLOSED, Fase C await ★) — only a 1-count suite bump needed. Everything else fell into: version/PRIORIDAD banner fixes (7 files), missing cameras/vtx/mission-ladder content (4 files), a new pointer section (1 file), and historical/obsolete stamps (7 files).

## Phase 1 — Table of edits

| Path | Change |
|---|---|
| `docs/IMPLEMENTATION_TASKS.md` | Suite count `3165`→`3166` (top banner only; ~2900-line closed-section history untouched — none of it is misleading, every closed entry already carries its own date + suite count) |
| `docs/ARCHITECTURE.md` | Fixed the one non-dated "still v0.4.1 / PRIORIDAD: software closeout" mid-paragraph; appended two new dated changelog bullets (Fase M arc) in the existing chronological style — did not rewrite any prior entry |
| `docs/ENGINEERING_READINESS_VISION.md` | Updated top Status/Date lines (`v0.4.2`, Fase M CLOSED, PRIORIDAD → Fase C await ★); fixed one "As of 2026-09-10 ... PRIORIDAD = Fit VERIFIED" line adjacent to a live-queue pointer bullet (high misread risk); left the deeper §8-scoped "PRIORIDAD = Fit VERIFIED" line alone — that section explicitly disclaims itself as historical ("not in §8 phase history above") |
| `docs/PROJECT_CONTINUITY.md` | Added a "Mission Continuity extensions" pointer paragraph (waterfall summary + link to `CONTINUITY_MAP.md`, no duplicated SoT) |
| `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` | Appended a note after §13's table naming `library/cameras/`/`library/vtx/` as later catalog families following the same design pattern — table itself (dated 2026-09-07) left as historical record |
| `docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md` | Added an "Epoch check (2026-09-18)" line confirming HD-004 wall status unaffected by Fase M (orthogonal subsystem) — already well-framed, light touch only |
| `docs/BUGS.md` | Added HISTORICAL status banner (1710-line body untouched) |
| `docs/CLI_TESTS.md` | Added HISTORICAL/OBSOLETE banner (superseded by the pytest suite) |
| `docs/CODE_AUDIT_CORE.md` | Added HISTORICAL banner (point-in-time audit, already self-dated) |
| `docs/FASE_LLM.md` | Added HISTORICAL banner, explicit "principle still enforced, but this file is not the authority reference; never revives Conversation Engine" framing |
| `docs/fixes/human_layer.md` | Added HISTORICAL banner |
| `docs/refactors/domain_registry_refactor.md` | Added HISTORICAL banner |
| `docs/refactors/iterate_interactive_session_refactor.md` | Added HISTORICAL banner |
| `docs/system_map/README.md` | Updated date line (`v0.4.2` / suite 3166) |
| `docs/system_map/JARVIS_SYSTEM_MAP.md` | Updated "Product checkpoint" paragraph (`v0.4.2`, Fase M ladder, PRIORIDAD → Fase C await ★, "no new C-xxx" explained) |
| `docs/system_map/CONNECTIONS.md` | Appended a new dated trail entry (Fase M arc: all 6 Buy names, no new C-xxx — explicit reasoning) after the existing 2026-09-15 entry; nothing rewritten |
| `docs/system_map/jarvis-system-map.canvas.tsx` | Fixed the "Product queue" callout (was `v0.4.1`/idle-framed); appended a new "Shipped — Fase M" callout next to the existing dated `v0.4.1` one (left that one as-is, its own title already carries a date) |
| `docs/system_map/DIAGRAMS.md` | Extended the craft-montage epoch paragraph with a dated Fase M continuation + corrected the trailing "PRIORIDAD: idle" → "Fase C await ★" |
| `docs/system_map/00_entry/ENTRY_MAP.md` | Extended the epoch phrase to include `v0.4.2` / Fase M |
| `docs/system_map/AUTHORITY.md` | Added two new authority rows: mission mass mirror (`set_mission_component_mass`, widened to `vtx`) and mission power mirror (`set_mission_component_power`, **structurally excludes** `vtx`) |
| `docs/system_map/03_acquisition/ACQUISITION_MAP.md` | Added `esc_catalog_assist.py`/`camera_catalog_assist.py`/`vtx_catalog_assist.py` module rows; extended the `catalog_bind.py` row with the 4 missing bind functions (`esc`/`camera`/`vtx` were never listed, plus a note on the shared manual-mass-preserve discipline); extended the IDLE-rebind bullet with all 9 families **and** the first-time-acquisition scoping (documents the prerequisite fix above as acquisition-subsystem history); extended the SYSTEM_DEFINITION gate bullet with `video_link`/`vtx`; extended the Tests line |
| `docs/system_map/06_calculation/CALCULATION_MAP.md` | Added a note on `mission_accessory_power_w`'s additive term in both autonomy paths; extended the Tests line |
| `docs/system_map/08_continuity/CONTINUITY_MAP.md` | Added `mission_mass_declare_assist.py`/`mission_power_declare_assist.py` module rows; added a full "Mission Continuity ladder" bullet (the complete waterfall, first-match-wins order); noted the `classify_component` "declared"→"defined" reclassification for cameras/vtx with measurable fields (an accurate consequence, not a bug); extended the Tests line |

**Files audited, found already accurate, left untouched:** `docs/HARDWARE_DEBT.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/JARVIS_SYSTEM_MAP.md` (root stub), `docs/USER_GUIDE_CRAFT_MONTAGE.md` (verified against current `catalog_rebind_assist.py`/`reasoning_layer.py` — already accurate from this same session's earlier Buys), `docs/system_map/MISMATCHES.md` (all 6 `M-xxx` entries already CLOSED/RESOLVED), `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` (§5 already CLOSED, consistent with `MISMATCHES.md`'s own note), `docs/system_map/FLOWS.md`, and the `01_runtime`/`02_intent`/`04_engineering`/`05_iteration`/`07_simulation`/`09_state`/`10_llm` subsystem maps.

## Obsolete register

Every file stamped HISTORICAL/OBSOLETE above kept its full body — only a top status banner was added, per lock #6 (prefer status line over deletion). No file or section was deleted. No duplicate-stub redirect existed that needed pruning (the one stub found, root `JARVIS_SYSTEM_MAP.md`, already correctly points to `system_map/README.md`).

## T1–T9 verification (IC §5)

- **T1** — inventory lists all 37 files, count matches `find docs -type f | wc -l` = 37. ✅
- **T2** — no living header claims `0.4.1` as current without historical framing (every remaining `0.4.1` mention is inside a dated, self-scoped historical entry — verified via `rg`). ✅
- **T3** — no living PRIORIDAD reads "Fit VERIFIED" / "software closeout lean" / "M7 GATE" as AHORA; the one adjacent-to-live-queue instance was fixed. ✅
- **T4** — `ACQUISITION_MAP.md` and `CONTINUITY_MAP.md` both name `cameras`/`vtx` catalog paths explicitly. ✅
- **T5** — `CatalogRebindKey`'s 9 families (`frame`, `motors`, `propellers`, `battery`, `esc`, `flight_controller`, `sensors`, `cameras`, `vtx`) are all documented in `USER_GUIDE_CRAFT_MONTAGE.md` §4 and `ACQUISITION_MAP.md`. ✅
- **T6** — `USER_GUIDE_CRAFT_MONTAGE.md`'s cámara/vtx examples verified against current `resolve_idle_catalog_rebind`/orchestrator offer copy this session (no drift found — it was already current from the same-session cameras/power/vtx Buys). ✅
- **T7** — 7 files gained an explicit OBSOLETE/HISTORICAL stamp. ✅
- **T8** — this report lists every file touched (table above) and every file audited-and-left-alone (list above); no deferred-to-Engineer item beyond what `inventory_...b0.md` §4 already names (H1–H5 appendix reconciliation — explicitly not this Buy's). ✅
- **T9** — `rg` sanity: no `docs/` file states `PRIORIDAD = Fit VERIFIED` or `software closeout lean Continuity intent` in present tense outside a clearly-dated historical section. ✅

## Residual risks

- `docs/system_map/01_runtime/RUNTIME_MAP.md`'s ~25-checkpoint dispatch-chain description does not individually enumerate every named catalog family at each checkpoint (it never did, even pre-Fase-M) — left as-is per the IC's own "don't invent new enumeration this Buy didn't ask for" discipline; the family list now lives correctly in `ACQUISITION_MAP.md` instead.
- `docs/BUGS.md`'s 1710-line body and `docs/IMPLEMENTATION_TASKS.md`'s ~2900-line closed-section history were deliberately NOT rewritten — both are already dated/CLOSED-labeled per-entry, so a full rewrite would have violated lock #6/#8's "don't boil the ocean" instruction rather than fixed anything.
- The `HANDOFF_CONTEXT_DESIGN.md` / `MISMATCHES.md` H1–H5 "open questions" appendix staleness (flagged by `MISMATCHES.md` itself, predates and is unrelated to Fase M) remains explicitly deferred to Engineer/Cursor, per that file's own note and this IC's §2 scope.

## Explicit confirmations

- **No `src/`/`ui/`/`tests/`/`library/`/`.jes/state` product changes** in this docs Buy itself. (The one `src/` edit — narrowing `orchestrator.py`'s `_open_catalog` condition — was a pre-existing regression fix, explicitly approved by the user before Phase 0 started, and is recorded separately above, not folded into "the docs Buy's own work.")
- **Package still `0.4.2`** — no version bump.
- **No new C-xxx** — `CONNECTIONS.md`'s Fase M trail entry explicitly states why (existing writer/bind/rebind patterns, no new connection class).
- **No firmware/MAVLink/ELRS-bind/PID claimed as implemented** anywhere touched.
- **No Fase C Buy invented** — every touched file's PRIORIDAD language says "await Engineer ★," matching `IMPLEMENTATION_TASKS.md`'s own live value.
