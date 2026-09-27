# Phase 0 Inventory — Docs truth-sync after C35 / Taller (`B1-docs-truth-sync-after-c35`)

**IC:** [`implementation_contract_docs_truth_sync_after_c35_b1.md`](implementation_contract_docs_truth_sync_after_c35_b1.md)
**Gate:** IC §0 decision 8 — STOP before bulk edits until this artifact has one row per in-scope file. Written before any Phase 1 edit in this Buy.
**Truth epoch this Buy targets:** `v0.5.35` (Taller cylinder ACCEPT, tip `c434e73`) on top of `v0.5.34` (Taller cuboid) / `v0.5.33` (C35). Craft tip stays `v0.4.3`.

---

## 1. Must audit + update (IC §1.1)

| # | File | Current state (verified by grep/read before this Buy) | Action this Buy |
|---|---|---|---|
| 1 | `docs/system_map/README.md` | Header line names Fase C **`v0.5.3`**, suite **3236**, UI **132** (dated 2026-09-20) | Rewrite header clause: tip **`v0.5.35`**, live suite/UI/ctest counts, C++ tree exists+isolated, no new C-xxx |
| 2 | `docs/system_map/JARVIS_SYSTEM_MAP.md` | §"Fase C packages" (line 59-61) says C1-C5 only, quotes "production flight_control runtime is C++ (future IC)" as current; summary block (line 84-86) tags tip `v0.5.3`, suite 3236 | Rewrite both: Python scaffold **plus** `native/flight_control/` C13-C35; zero import into orchestrator/Board/`library/` (unchanged, re-verified); tip `v0.5.35`; pointer to ARCHITECTURE §1c / PLATFORM §13 |
| 3 | `docs/system_map/CONNECTIONS.md` | Line 46: last Fase C changelog paragraph is "Fase C C1-C5 scaffold note (2026-09-20)" @ `v0.5.3`, suite 3236 | Add **one new** changelog paragraph after it: C6-C35 + Taller CSS (cuboid + cylinder), no new C-xxx, isolation holds, tip `v0.5.35`. Canonical registry table (still ends C-113) **untouched** |
| 4 | `docs/system_map/jarvis-system-map.canvas.tsx` | Header comment stops its Fase C note at `v0.5.3`/C1-C5 (line 29-37); "Product queue" Callout (line 464-478) titled "Fase C surface CLOSED @ v0.5.3", body says "production FC runtime is C++, future IC"; last "Shipped" Callout (line 579-593) titled "Fase C C1-C5 scaffold @ v0.5.3", body says `"(future IC)" — no C++/CMake tree` as a then-current fact | Add one header changelog line (no new mermaid edges); update the "Product queue" Callout to the current tip/facts; correct the one false-as-current phrase in the dated historical Callout (native C++ tree arrived later, C13+); add one new dated "Shipped" Callout for C6-C35 + Taller CSS @ `v0.5.35`. **Do not** add fake nodes for SPI/`step` |
| 5 | `docs/system_map/DIAGRAMS.md` | Chronology paragraph (line 49) ends at "PRIORIDAD: Fase C (control/enlace software) — await Engineer ★" — **zero** `v0.5.x` epoch line was ever added after Fase C actually opened | Append one epoch line matching the map (no new mermaid edges) |
| 6 | `native/flight_control/README.md` | Layout tree (line 271-310) lists headers through `uart.hpp`/`test_uart.cpp` (C28) only — missing `dshot.hpp`/`dshot.cpp`, `spi.hpp`/`spi.cpp`, `spi_probe.hpp`/`spi_probe.cpp`, `rc_hold.hpp` already listed, and `test_dshot.cpp`/`test_spi.cpp`/`test_spi_probe.cpp`/C35's density additions to `test_loop.cpp`. C30 paragraphs (line 139, 378) say "not yet tagged" — **stale**, `v0.5.28` exists (`git tag -l v0.5.28`, commit `e99965d`) | Extend layout list to name the missing files; fix both "not yet tagged" mentions to "★ ACCEPT CLOSED @ tag `v0.5.28`"; add honesty-summary paragraphs for C31 (DShot encode), C32/C33 (SPI port/scripted slave), C34 (`probe_rx`), C35 (denser `step` density) matching this README's own established per-Buy paragraph style |
| 7 | `docs/USER_GUIDE_CRAFT_MONTAGE.md` §8.4 | Taller workshop text (line 378-400) covers selection/inspector/Situar — no honesty line about the cuboid/cylinder visor construction | Add one short paragraph (Spanish, after line 400, before the `---`/§9 divider): a declared box is one six-face prism; a declared cylinder is one body (2 caps + 16 slats); a thin plate / short hub is still one solid, not extra parts; not CAD / not fit. No MY5 mm, no standoff ×8 |
| 8 | `docs/system_map/00_entry/ENTRY_MAP.md` | Line 14 table cell: "Visor projector" row's last epoch clause is "Fase M mission craft ladder ... @ v0.4.2 (suite 3166)" | Append one clause: Taller CSS cuboid + cylinder faces (visor) @ `v0.5.35`; still C-094/C-113 class; no new C-xxx |

---

## 2. Must **not** rewrite (IC §1.2) — verified, stamp-only

| File | Verified state | Action |
|---|---|---|
| `VISION.md` | Zero `v0.5.3`/C1-C5/"future IC" references (grep-verified) | **Leave** — not a changelog |
| `docs/PROJECT_CONTINUITY.md` | Zero stale references; no broken cross-link found (grep-verified) | **Leave** |
| `docs/ENGINEERING_READINESS_VISION.md` | Zero stale references | **Leave** |
| `docs/BUGS.md` | Already carries a `> **Status:** HISTORICAL` banner + SoT pointer at top | **Leave** — banner already present, no body rewrite |
| `docs/FASE_LLM.md` | Already carries a `> **Status:** HISTORICAL` banner + SoT pointer | **Leave** |
| `docs/CODE_AUDIT_CORE.md` | Already carries a `> **Status:** HISTORICAL` banner + SoT pointer | **Leave** |
| `docs/IMPLEMENTATION_TASKS.md` (historical closed sections) | Already-current living PRIORIDAD (updated every Buy this session); historical `### 🧊 FUERA DE FASE` sections untouched | **Leave body**; PRIORIDAD banner retargeted per §1.3 below |
| `docs/ARCHITECTURE.md` §1c C3 quote | Historical C3 lock ("future IC" as C3's own documented, dated claim) — confirmed present, not touched by any prior Buy | **Leave** — do not "correct" the historical C3 prose |
| `src/jarvis/flight_software/**` docstrings | Out of this Buy per IC §1.2 | **Leave** — zero edits |
| Standoff ×8 / MY5 catalog / plate-box seed | Not present as shipped SoT anywhere audited (`IMPLEMENTATION_TASKS.md`'s own MY5/standoff rows already read "COLA"/"no ACCEPT" honestly) | **Leave** — confirmed not misrepresented as shipped |

---

## 3. Living quartet (IC §1.3) — already current each Buy, retarget only

| File | Current "Next" pointer | Action |
|---|---|---|
| `README.md` | Points at Taller CSS cylinder faces LANDED @ `0.5.35` | Retarget "Next" to this docs Buy's own closeout, then cola standoff points. Add "What v0.5.36 includes" section |
| `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD | Points at Taller CSS cylinder faces LANDED @ `0.5.35` | Retarget PRIORIDAD banner + add a table row for this docs Buy |
| `docs/ARCHITECTURE.md` §1a/§1c | Points at Taller CSS cylinder faces LANDED | Retarget banner; no new essay paragraph (this Buy is docs-only, not a product Buy) |
| `docs/PLATFORM_CAPABILITY_VISION.md` §13 | Points at Taller CSS cylinder faces LANDED | Retarget "Next" pointer only — no new §13 block (this Buy doesn't touch `src/jarvis/flight_software/`) |

---

## 4. Remaining `docs/*.md` — stamp-only (IC T1: "remaining docs/*.md, stamp-only rows OK")

Grepped for `v0.5.3` (word-boundary) / `C1.C5` / `C1–C5` / `future IC` / `no C++/CMake` — **zero hits** in every file below. No stale Fase C claim found; no edit needed this Buy.

| File |
|---|
| `docs/JARVIS_SYSTEM_MAP.md` (root redirect stub, 16 lines, points at `system_map/README.md`) |
| `docs/HARDWARE_DEBT.md` |
| `docs/CLI_TESTS.md` |
| `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` |
| `docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md` |
| `docs/fixes/human_layer.md` |
| `docs/refactors/domain_registry_refactor.md` |
| `docs/refactors/iterate_interactive_session_refactor.md` |
| `docs/system_map/AUTHORITY.md` |
| `docs/system_map/FLOWS.md` |
| `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` |
| `docs/system_map/MISMATCHES.md` |
| `docs/system_map/01_runtime/RUNTIME_MAP.md` |
| `docs/system_map/02_intent/INTENT_MAP.md` |
| `docs/system_map/03_acquisition/ACQUISITION_MAP.md` |
| `docs/system_map/04_engineering/ENGINEERING_MAP.md` |
| `docs/system_map/05_iteration/ITERATION_MAP.md` |
| `docs/system_map/06_calculation/CALCULATION_MAP.md` |
| `docs/system_map/07_simulation/SIMULATION_MAP.md` |
| `docs/system_map/08_continuity/CONTINUITY_MAP.md` |
| `docs/system_map/09_state/STATE_MAP.md` |
| `docs/system_map/10_llm/LLM_MAP.md` |

---

## 5. Gate cleared

One row exists above for every file in IC §1.1 (8/8), every file in IC §1.2 (9/9, all verified — none needed a stamp since HISTORICAL banners were already present), the living quartet (4/4), and every remaining `docs/*.md`/`.tsx` file in the repo (22/22, all stamp-only, zero stale hits). **Phase 1 may proceed.**
