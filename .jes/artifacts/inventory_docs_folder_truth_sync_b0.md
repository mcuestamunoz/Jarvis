# Phase 0 Inventory — `docs/` truth sync vs code @ v0.4.2 (`B1-docs-folder-truth-sync`)

**Method:** `find docs -type f | sort` (35 files, 13,893 lines total) → per-file header read (first 10-25 lines) → `grep -rn` sweeps across the whole tree for known stale markers (`0.4.1`, `suite 2968`, `Fit VERIFIED`, `closeout lean`, `no library/cameras`) → cross-checked against code anchors already verified in-session (this implementer authored the cameras/power/vtx Buys this same session, so "code truth" for §2.2-§2.4 of the IC is first-hand, re-confirmed against `library/`, `catalog_rebind_assist.py`, `component_writers.py`, `reasoning_layer.py` just now) → targeted deeper reads of `IMPLEMENTATION_TASKS.md`, `MISMATCHES.md`, `AUTHORITY.md`, `CONNECTIONS.md`, and the subsystem maps for cameras/vtx mentions.

**Real-file count:** 37 (matches the IC's own "37 today — recount at ★" baseline exactly; an earlier manual tally in this pass misread the listing as 35 — corrected here, `find docs -type f | wc -l` = 37, verified twice).

---

## 1. File table

| # | Path | Class | Epoch found | Action |
|---|---|---|---|---|
| 1 | `docs/IMPLEMENTATION_TASKS.md` | LIVING (queue) + HISTORICAL (body) | PRIORIDAD header already `v0.4.2`/Fase C await ★ (current); body per-section dated & CLOSED-labeled correctly | Minor: suite count `3165`→`3166` (post-regression-fix) near top |
| 2 | `docs/USER_GUIDE_CRAFT_MONTAGE.md` | LIVING | Rewritten + extended this session (cameras/power/vtx) | Light verify pass only (§3) |
| 3 | `docs/ARCHITECTURE.md` | LIVING (narrative) | Header still `v0.4.1`/suite 2968 | **Fix** (§4.1) |
| 4 | `docs/ENGINEERING_READINESS_VISION.md` | VISION | Status/Date lines still `v0.4.1`/suite 2968/"PRIORIDAD = software closeout lean" | **Fix** (§4.1) |
| 5 | `docs/PROJECT_CONTINUITY.md` | LIVING (contract) | Dated Aug 2026; predates mount/endurance/power/vtx ladder | **Add pointer section** |
| 6 | `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` | DESIGN CLOSED + impl-status | §13 sync point predates cameras/vtx families | **Fix §13** |
| 7 | `docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md` | HISTORICAL/VISION hybrid (already self-labeled "P2-1 delivered, rest is vision") | Already honestly framed | Stamp epoch only |
| 8 | `docs/PLATFORM_CAPABILITY_VISION.md` | VISION (already labeled "Directional — not implementation authority") | Fine | No change needed |
| 9 | `docs/HARDWARE_DEBT.md` | LIVING debt register | Already self-consistent, HD-* explicitly never PRIORIDAD | No change needed |
| 10 | `docs/BUGS.md` | HISTORICAL (1710 lines) | No top OBSOLETE banner; has a "living CLI findings" pointer instead | **Add banner** |
| 11 | `docs/CLI_TESTS.md` | HISTORICAL/superseded (212 lines, manual checklist predating the pytest suite's current scale) | No banner | **Add banner** |
| 12 | `docs/CODE_AUDIT_CORE.md` | HISTORICAL (point-in-time, 3 Sep 2026) | Already dated, already says "no src edited" | **Add banner** (epoch pointer only) |
| 13 | `docs/FASE_LLM.md` | HISTORICAL (design note, no Conversation Engine) | No banner | **Add banner** |
| 14 | `docs/JARVIS_SYSTEM_MAP.md` (root) | STUB/redirect | Correct, points to `system_map/README.md` | No change needed |
| 15 | `docs/fixes/human_layer.md` | HISTORICAL fix note | No banner | **Add banner** |
| 16 | `docs/refactors/domain_registry_refactor.md` | HISTORICAL refactor note | No banner | **Add banner** |
| 17 | `docs/refactors/iterate_interactive_session_refactor.md` | HISTORICAL refactor note | No banner | **Add banner** |
| 18 | `docs/system_map/README.md` | LIVING index | Date line still `v0.4.1`/suite 2945 | **Fix** (§4.1) |
| 19 | `docs/system_map/JARVIS_SYSTEM_MAP.md` | LIVING master | Still `v0.4.1`/suite 2968/"closeout lean" as PRIORIDAD AHORA | **Fix** (§4.1) |
| 20 | `docs/system_map/CONNECTIONS.md` | LIVING C-xxx registry | Top trail stops at mission-payload-identity (2026-09-15); no cameras/vtx/power entries; no new C-xxx needed (lock #9) | **Add trail entries, no new C-xxx** |
| 21 | `docs/system_map/AUTHORITY.md` | LIVING | Zero mentions of `mission_payload_mass_kg`/`mission_accessory_power_w`/`set_mission_component_*` writers | **Add authority rows** |
| 22 | `docs/system_map/FLOWS.md` | LIVING reference | No cameras/vtx flow; not required (existing FLOW-xxx set doesn't claim exhaustive mission coverage) | No change (out of §4.1 priority set) |
| 23 | `docs/system_map/DIAGRAMS.md` | LIVING reference | Epoch banner still `v0.4.1`/suite 2945 | **Fix epoch banner** |
| 24 | `docs/system_map/MISMATCHES.md` | LIVING debt-of-map-vs-code | All 6 `M-xxx` entries already CLOSED/RESOLVED; one note flags an external H1-H5 reconciliation still pending (not this Buy's to fix, correctly flagged as Cursor/Engineer's) | No change needed |
| 25 | `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` | DESIGN, §5 already marked CLOSED | Consistent with MISMATCHES.md's own note | No change needed |
| 26 | `docs/system_map/jarvis-system-map.canvas.tsx` | LIVING canvas | 3 callouts still `v0.4.1`/old suite counts | **Fix** (§4.1) |
| 27 | `docs/system_map/00_entry/ENTRY_MAP.md` | LIVING (Level 2) | Epoch phrase still `v0.4.0`+`v0.4.1` | **Fix epoch phrase** |
| 28 | `docs/system_map/01_runtime/RUNTIME_MAP.md` | LIVING (Level 2) | No camera/vtx-specific claim to break; 25-checkpoint dispatch chain description — IDLE rebind dispatch order changed this session (regression fix) but chain-level description doesn't enumerate every family | No change needed |
| 29 | `docs/system_map/02_intent/INTENT_MAP.md` | LIVING (Level 2) | No stale marker found | No change needed |
| 30 | `docs/system_map/03_acquisition/ACQUISITION_MAP.md` | LIVING (Level 2) | Already mentions cameras/vtx | Verify completeness only |
| 31 | `docs/system_map/04_engineering/ENGINEERING_MAP.md` | LIVING (Level 2) | No stale marker found | No change needed |
| 32 | `docs/system_map/05_iteration/ITERATION_MAP.md` | LIVING (Level 2) | No stale marker found | No change needed |
| 33 | `docs/system_map/06_calculation/CALCULATION_MAP.md` | LIVING (Level 2) | Autonomy formula description predates `mission_accessory_power_w` additive term | **Add note** |
| 34 | `docs/system_map/07_simulation/SIMULATION_MAP.md` | LIVING (Level 2) | No stale marker found | No change needed |
| 35 | `docs/system_map/08_continuity/CONTINUITY_MAP.md` | LIVING (Level 2) | Zero mentions of mass/mount/autonomy/power/vtx ladder | **Add mission ladder section** |
| — | `docs/system_map/09_state/STATE_MAP.md` | LIVING (Level 2) | No stale marker found | No change needed |
| — | `docs/system_map/10_llm/LLM_MAP.md` | LIVING (Level 2) | No stale marker found; correctly has no Conversation Engine claim | No change needed |

(37 rows total: 35 numbered + `09_state/STATE_MAP.md` and `10_llm/LLM_MAP.md` on the two trailing `—`-marked rows — matches `find docs -type f | wc -l` = 37 exactly, T1.)

## 2. Stale-claim table (confirm/clear each `§1` "Known stale" item)

| Claim (file:approx line) | Evidence it's stale | Action |
|---|---|---|
| `ARCHITECTURE.md:105-107,1522-1523` — "checkpoint v0.4.0 + patch v0.4.1", "still v0.4.1", "Suite 2968" | `pyproject.toml` = `0.4.2`; live suite = 3166 | Update status line to note v0.4.2/Fase M CLOSED, keep the v0.4.0/v0.4.1 historical feature-lock dates as dated history (not rewritten) |
| `ENGINEERING_READINESS_VISION.md:3,5` — "PRIORIDAD = software closeout lean Continuity intent", "tag v0.4.1 ... suite 2968" | Fase M is CLOSED, PRIORIDAD is now Fase C await ★ per `IMPLEMENTATION_TASKS.md` | Update Status/Date lines |
| `ENGINEERING_READINESS_VISION.md:339` — "PRIORIDAD = Fit VERIFIED" | Inside a dated `v0.4.0`/patch-`v0.4.1` feature entry (2026-09-10 era) — already historically scoped by its own paragraph, but "PRIORIDAD" language is confusing this far down without a re-affirming top banner | Leave the sentence (historical, dated), rely on the corrected top Status line (item above) to prevent misreading |
| `system_map/JARVIS_SYSTEM_MAP.md:80` — "Product checkpoint v0.4.1", "PRIORIDAD AHORA: software closeout lean" | Same as above | Update |
| `system_map/README.md:4` — "@ v0.4.1 / suite 2945" | Stale | Update date line |
| `system_map/CONNECTIONS.md` top trail — stops at "mission-payload-identity closed (2026-09-15)" | Missing cameras/vtx/power entries | Append trail entries (no new C-xxx — lock #9: Fase M added no new connection, only new component families riding existing writer/bind patterns) |
| `system_map/jarvis-system-map.canvas.tsx:14,16,454,532` — `v0.4.1`, suite `2873`/`2945` | Stale | Update the 2 "current state" callouts (line ~454 queue callout, ~532 shipped callout); leave line 14/16 (dated history of v0.4.0→v0.4.1 transition) as-is |
| `00_entry/ENTRY_MAP.md` — "Continuity spatial assembly @ v0.4.0 + craft-montage/mission-payload/user-guide @ v0.4.1 (suite 2945)" | Stale epoch, no cameras/vtx word | Update epoch phrase |
| `PHYSICAL_COMPONENT_CATALOG_V1.md` §13 | Predates cameras/vtx library families | Add a line confirming `library/cameras/`+`library/vtx/` exist, same shape as `library/fc/`+`library/sensors/` |
| `IMPLEMENTATION_TASKS.md:11,40` — "Suite viva 3165" | Post-fix count is 3166 | Bump by 1 |
| No living doc found saying "no library/cameras" or "no library/vtx" as a current claim | Confirmed clear via `grep -rn` — zero matches | No action |
| `AUTHORITY.md` | No row for `set_mission_component_mass`/`set_mission_component_power` writers | Add authority rows |
| `08_continuity/CONTINUITY_MAP.md` | No mission ladder (mass→mount→autonomy→power→vtx→margin) at all | Add section |
| `06_calculation/CALCULATION_MAP.md` | Autonomy formula predates `mission_accessory_power_w` additive term | Add one-line note |

## 3. Missing-doc gaps (proposed, docs-only)

- `08_continuity/CONTINUITY_MAP.md` has no paragraph for the mission ladder (identity → mass → mount → autonomy target → power → VTX → soft margin) that `reasoning_layer._mission_aware_high_margin_suggestion` implements — proposed as a new subsection, not a new file.
- `AUTHORITY.md` has no row for the two mission-mirror writers (`set_mission_component_mass`, `set_mission_component_power`) alongside the existing battery/motor mirrored-param rows — proposed as two new table rows.

## 4. Explicit out-of-scope leftovers for Engineer

- `HANDOFF_CONTEXT_DESIGN.md` / `MISMATCHES.md`'s own flagged note (H1–H5 "open questions" appendix reading stale against its own Decision Log) — explicitly NOT this Buy's to touch (predates and is unrelated to the cameras/power/vtx epoch; `MISMATCHES.md` itself already correctly defers this to "whatever pass formally absorbs the FN-024 outcome").
- Root `VISION.md`/`PRODUCT_SCOPE.md`/`CLAUDE.md`/`README.md` — out of scope per IC §2/§7.
- Full historical rewrite of `BUGS.md`'s 1710-line body, or `IMPLEMENTATION_TASKS.md`'s ~2900-line closed-section history — neither is "actively misleading" (each closed entry already carries its own date + suite count + CLOSED label), so per lock #6/#8 only a top banner (BUGS.md) and a 2-line top-of-file count bump (IMPLEMENTATION_TASKS.md) are made, not a rewrite.
- `docs/system_map/FLOWS.md`, `01_runtime/RUNTIME_MAP.md`'s per-checkpoint enumeration — the IDLE-catalog-rebind family list changed this session (widened then correctly narrowed back — see this Buy's own prerequisite fix), but neither file enumerates every named family today, so nothing to un-say; left as-is rather than inventing new enumeration this Buy didn't ask for.

---

Proceeding to Phase 1 per the IC's own default ("Claude proceeds to Phase 1 after inventory is written in the same Buy").
