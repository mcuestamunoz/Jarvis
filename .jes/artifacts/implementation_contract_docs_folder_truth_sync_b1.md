# Implementation Contract — Docs folder truth sync to code @ v0.4.2 (`B1-docs-folder-truth-sync`)

**Project:** Jarvis  
**Date:** 2026-09-18  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check of PRIORIDAD + USER_GUIDE + system_map headers

**Status:** **ACCEPT CLOSED** (Engineer 2026-09-20 with U1 closeout)  
**Parents:**
- Package / tag **`v0.4.2`** / `checkpoint-fase-m-mission-craft` — [M7 closeout](engineer_note_fase_m_closeout_m7.md)
- Fase M CLOSED · Fase C PRIORIDAD await ★ — [fase gate note](engineer_note_fase_m_mission_craft_to_control_gate.md)
- Living queue: [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) § PRIORIDAD ACTUAL
- Prior docs Buy pattern: [user-guide craft montage IC](implementation_contract_user_guide_craft_montage_b1.md) (inventory-first discipline)

**Type:** **Documentation Buy** (primary deliverable = markdown under `docs/` + audit artifacts under `.jes/artifacts/`).  
**Mandatory Phase 0 = full-folder audit** against **real code / library / tests / package version**.  
**Phase 1 = update living docs** + **label obsolete** (never silent delete of historical truth without Engineer ★).  
**Not** new product features. **Not** `src/` / `ui/` / `tests/` / `library/` / `.jes/state` product changes. **Not** inventing Fase C Buys. **Not** claiming ASSEMBLY READY / flight-validated autonomy / firmware. **Not** rewriting the entire historical body of `IMPLEMENTATION_TASKS.md` or `BUGS.md` into a new narrative.

**Outputs (all required):**
1. `.jes/artifacts/inventory_docs_folder_truth_sync_b0.md` — Phase 0 file-by-file audit  
2. Edits under `docs/` per Phase 1 rules (this IC)  
3. `.jes/artifacts/implementation_report_docs_folder_truth_sync_b1.md` — what changed, what marked obsolete, what deferred, evidence method  
4. Optional but recommended: `.jes/artifacts/docs_obsolete_register_b1.md` — compact register of files/sections stamped obsolete (can be a section inside the report if short)

**Checkpoint:** package **`0.4.2`** · suite green at ★ (doc Buy — **no** required suite growth; run a smoke subset only if a doc claim cites a specific test path that looks wrong)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-docs-folder-truth-sync`** — audit **every** file under `docs/`, then sync living docs to **code truth @ v0.4.2** |
| 2 | Scope root | **`docs/` only** (37 files today — recount at ★). Out of scope unless Engineer expands: root `VISION.md`, `PRODUCT_SCOPE.md`, `CLAUDE.md`, `README.md` (README already bumped in M7 — do **not** reopen unless a `docs/` cross-link is broken) |
| 3 | Authority order | **Code / tests / `library/` / `pyproject.toml` version >** closed ICs/reviews/smoke > living PRIORIDAD > old prose in docs. If prose conflicts with code, **fix the doc or stamp obsolete** — never “fix” by changing product code in this Buy |
| 4 | Truth epoch | Document state as of **`v0.4.2` / M7 CLOSED / Fase C await Engineer ★**. Suite count: use **live `pytest` count at ★** (M7 closeout cited **3165** · UI **105** — verify, do not invent) |
| 5 | Phase 0 gate | **STOP before bulk edits** until the inventory artifact exists with **one row per file** under `docs/` |
| 6 | Obsolete policy | If a section/file is outdated: **say so explicitly** (banner / status line / register). Prefer `**Status: OBSOLETE / historical**` + pointer to SoT over deletion. **Delete only** duplicate stubs that are pure redirects already superseded **and** listed in the report — never delete long historical registers (`BUGS.md` archive body, closed IC narratives inside IMPLEMENTATION_TASKS) |
| 7 | Living vs archive | **Living** docs must match code. **Archive / closed-phase** prose may stay if clearly dated and not presented as PRIORIDAD AHORA |
| 8 | IMPLEMENTATION_TASKS discipline | Update **§ PRIORIDAD ACTUAL** + any **living** “Next / queue” blurbs that still say Fit VERIFIED / software closeout lean / M7 GATE / `0.4.1` tip. **Do not** rewrite thousands of historical closed-section lines unless they **actively mislead** (e.g. a section titled as current that is not). When touching history, add a one-line “historical — closed @ date” rather than full rewrite |
| 9 | System map | Update **headers / product checkpoint / PRIORIDAD / catalog family lists / acquisition help-choose families** to include cameras + vtx and Fase M closed. New **C-xxx only if** a real new connection exists (Fase M did **not** require new C-xxx — do not invent). Canvas (`.canvas.tsx`) counts as in-scope under `docs/system_map/` |
| 10 | USER_GUIDE | Re-read against orchestrator / `catalog_rebind_assist` / Continuity ladder; fix any phrase that code no longer accepts; ensure VTX / cámara / power_w / mount paths match smoke 2026-09-18 |
| 11 | Vision docs | `ENGINEERING_READINESS_VISION.md` / `PLATFORM_CAPABILITY_VISION.md` = **to-be + shipped markers**. Sync **shipped / PRIORIDAD** banners to v0.4.2; do **not** invent new readiness families or firmware claims |
| 12 | Honesty | Never document firmware / MAVLink / ELRS bind / PID as **implemented in Jarvis**. Fase C = await ★ only |
| 13 | Version | **No** bump (already `0.4.2`) |
| 14 | Language | Prefer Spanish for user-facing guide fixes; system_map / ARCHITECTURE may stay bilingual as today. Status banners in English or Spanish OK if consistent per file |

**Product sentence:**

```text
Todo docs/ debe decir la verdad del código en v0.4.2 (Fase M cerrada,
Fase C await ★). Lo obsoleto se etiqueta; lo vivo se actualiza;
nada se inventa ni se borra en silencio.
```

---

## 1. Inventory of `docs/` (Phase 0 must cover **all**)

Recount at ★. Baseline 2026-09-18:

### 1.1 Root of `docs/`

| File | Likely class (verify) | Known stale risk @ M7 |
|---|---|---|
| `IMPLEMENTATION_TASKS.md` | Living queue + huge archive | PRIORIDAD header OK post-M7; deep body may still say old suite/PRIORIDAD in mid-sections |
| `USER_GUIDE_CRAFT_MONTAGE.md` | Living user guide | Mostly synced; verify every phrase vs code; power_w / vtx / bare `ayúdame` |
| `ARCHITECTURE.md` | Living as-is narrative | Headers still **`v0.4.1` / software closeout lean / suite 2968** — **must update** |
| `ENGINEERING_READINESS_VISION.md` | Vision + shipped markers | Status still Fit VERIFIED / closeout lean / `0.4.1` — **must update** |
| `PROJECT_CONTINUITY.md` | Product contract Continuity | Dated Aug; may miss mission Continuity ladder (mount/endurance/power/vtx) — sync or stamp “partial / see Continuity map” |
| `PHYSICAL_COMPONENT_CATALOG_V1.md` | Design closed + impl status | Must mention `library/cameras` + `library/vtx` exist; kill any “no cameras library” implication |
| `PHYSICAL_PROPULSION_ENGINE_PHASE2.md` | Phase design / historical | Stamp epoch; point HD-004 wall; don’t present as next Buy |
| `PLATFORM_CAPABILITY_VISION.md` | Directional to-be | Keep directional; fix any “current capability” overclaim |
| `HARDWARE_DEBT.md` | Living debt register | Sync HD-* vs PRIORIDAD (never AHORA); cite v0.4.2 |
| `BUGS.md` | Historical register | **Archive** — do not rewrite; add top banner “historical register; not PRIORIDAD” if missing |
| `CLI_TESTS.md` | Possibly stale test doc | Audit vs `tests/` + current CLI; stamp obsolete if superseded by pytest suite |
| `CODE_AUDIT_CORE.md` | Point-in-time audit | Stamp date/obsolete unless claims still true |
| `FASE_LLM.md` | Historical LLM phase | Stamp obsolete/historical; do not revive Conversation Engine |
| `JARVIS_SYSTEM_MAP.md` | Stub redirect? | Ensure points to `system_map/`; no divergent PRIORIDAD |

### 1.2 `docs/system_map/`

| File | Likely class | Known stale risk |
|---|---|---|
| `README.md` | Living index | Checkpoint / PRIORIDAD |
| `JARVIS_SYSTEM_MAP.md` | Living master | Still **v0.4.1 · suite 2968 · software closeout lean** — **must update** |
| `CONNECTIONS.md` | Living C-xxx registry | Craft montage trail stops mid-Fase M; add **post-hoc product notes** for cameras/vtx/power/mass **without inventing C-xxx** unless code added a new connection ID |
| `AUTHORITY.md` | Living | Verify writers/authority for mission mass/power/vtx |
| `FLOWS.md` / `DIAGRAMS.md` | Living reference | Update epoch banners; fix diagrams that claim wrong next step |
| `MISMATCHES.md` | Living debt of map vs code | Re-check open mismatches; close or restate against v0.4.2 |
| `HANDOFF_CONTEXT_DESIGN.md` | Design / possibly partial | Stamp status honestly |
| `jarvis-system-map.canvas.tsx` | Living canvas | Queue callouts still **v0.4.1 / Fit / closeout** — **must update** |
| `00_entry/ENTRY_MAP.md` … `10_llm/LLM_MAP.md` | Per-subsystem | **Acquisition** must list cameras+vtx catalog assists; **Continuity** must list mission ladder; **Engineering/State** mass/power mirrors; Runtime IDLE rebind named families |

### 1.3 `docs/fixes/` · `docs/refactors/`

| Path | Class | Rule |
|---|---|---|
| `fixes/human_layer.md` | Historical fix note | Stamp **historical** |
| `refactors/*.md` | Historical refactor notes | Stamp **historical**; do not imply pending work |

---

## 2. Code truth anchors (Phase 0 **must** verify against these)

Claude must open and cite evidence (path + symbol), not chat memory.

### 2.1 Package / phase

| Claim | Evidence |
|---|---|
| Version **0.4.2** | `pyproject.toml` `[project].version` |
| Fase M CLOSED / M7 | `.jes/artifacts/engineer_note_fase_m_closeout_m7.md` |
| PRIORIDAD = Fase C await ★ | `docs/IMPLEMENTATION_TASKS.md` § PRIORIDAD ACTUAL (after this Buy, must remain consistent) |

### 2.2 Catalog families (library on disk)

| Family dir | Spec / loader | Doc implication |
|---|---|---|
| `library/cameras/` | `CameraSpec` / camera catalog assist | Seed Phoenix 2; help-choose `ayúdame a elegir cámara` |
| `library/vtx/` | `VtxSpec` / vtx catalog assist | Seed Zeus 800; RF mW ≠ `power_w`; mass yes |
| `library/fc/`, `sensors/`, motors, props, battery, esc, frames, kit_hardware | existing | Already documented — verify no contradiction |

### 2.3 IDLE named catalog rebind (complete list)

From `catalog_rebind_assist.CatalogRebindKey` / `_FAMILY_NOUN_PATTERNS`:

`frame` · `motors` · `propellers` · `battery` · `esc` · `flight_controller` · `sensors` · `cameras` · `vtx`

Docs that list catalog help-choose **without** cameras/vtx are stale.  
Bare `ayúdame a elegir` = FN-005 triage (motor→prop→battery), **not** “any component”.

### 2.4 Mission Continuity ladder (software)

Identity → mass (`mission_payload_mass_kg`) → mount → autonomy target → `power_w` (`mission_accessory_power_w`) → VTX identity → soft margin.

Evidence modules (verify names at ★): `reasoning_layer` / `project_continuity` / `component_writers` (`_MISSION_MASS_KEYS` includes `vtx`; `_MISSION_POWER_KEYS` = cameras/radio only) / mount + power declare assists / `vtx_catalog_assist` / `camera_catalog_assist`.

### 2.5 Honesty locks (must remain in docs)

- Simplified energy model disclaimer (Wh/W×60)
- Autonomy gap ≠ “restrictions” confusion (guide already fixed — keep)
- Structure/Control PASS* caveats
- Propulsion fallback ≠ manufacturer exact combo
- No firmware / GCS / ELRS commissioning in SoT
- HD-* never PRIORIDAD AHORA without lab

---

## 3. Phase 0 — Audit method (mandatory)

### 3.1 Procedure

1. `find docs -type f | sort` → full file list.  
2. For **each** file: read status/header + skim for version, PRIORIDAD, suite, “next”, catalog claims, “not implemented”, “no library/X”.  
3. Cross-check living claims against §2 anchors (rg + open symbols).  
4. Classify each file:

| Class | Meaning |
|---|---|
| **LIVING** | Must match code; edit in Phase 1 |
| **VISION** | To-be OK if labeled; sync shipped/PRIORIDAD banners only |
| **HISTORICAL** | Keep; add/verify obsolete/historical banner; no false “current” |
| **OBSOLETE-ACTIVE** | Presents as current but is wrong — **must** fix or stamp + demote |
| **DUPLICATE/STUB** | Redirect only — ensure single SoT link |

5. Build a **stale-claim table** (claim → file:line → evidence → action: update / stamp / defer).

### 3.2 Inventory artifact shape

`.jes/artifacts/inventory_docs_folder_truth_sync_b0.md` must include:

1. File table (path · class · last meaningful epoch · action).  
2. Stale-claim table (minimum the **Known stale** items in §1 — confirm or clear each).  
3. Missing-doc gaps (optional): e.g. “no map section for vtx assist” → propose Continuity/Acquisition paragraph (still docs-only).  
4. Explicit **out of scope** leftovers for Engineer.

**STOP** for Engineer/Cursor skim of inventory if ★ required a hold — default: Claude proceeds to Phase 1 after inventory is written in the same Buy (unless Engineer said inventory-only).

---

## 4. Phase 1 — Edit rules

### 4.1 Priority order (do in this order)

1. **Banners / PRIORIDAD / version / suite** on:  
   `IMPLEMENTATION_TASKS.md` (PRIORIDAD only + misleading “current” mid-headers) · `ARCHITECTURE.md` · `ENGINEERING_READINESS_VISION.md` · `system_map/JARVIS_SYSTEM_MAP.md` · `system_map/README.md` · `system_map/CONNECTIONS.md` (top trail) · `system_map/jarvis-system-map.canvas.tsx` · `PHYSICAL_COMPONENT_CATALOG_V1.md` status/next  
2. **Acquisition / Continuity / Entry maps** — cameras + vtx + mission ladder + named rebind list  
3. **USER_GUIDE_CRAFT_MONTAGE.md** — phrase truth pass  
4. **PROJECT_CONTINUITY.md** — add “mission Continuity extensions @ 0.4.2” section **or** clear pointer to Continuity map / closeout (don’t fork SoT)  
5. **Historical stamps** — BUGS, FASE_LLM, CODE_AUDIT_CORE, CLI_TESTS, fixes/, refactors/, PHYSICAL_PROPULSION_ENGINE_PHASE2 as needed  
6. **MISMATCHES.md** — reconcile open items against code  

### 4.2 Required content patches (acceptance themes)

After Phase 1, a reader of living docs must correctly learn:

| Theme | Must say |
|---|---|
| Version | **`v0.4.2`** current product checkpoint |
| Phase | **Fase M CLOSED**; **Fase C await Engineer ★** (no open control Buy) |
| Catalog | cameras + vtx seeded; listed help-choose families complete |
| Mission | mass / mount / endurance / power_w / vtx ladder exists; power keys ≠ vtx RF |
| Queue | Not “Fit VERIFIED” / not “software closeout lean Continuity intent” as AHORA |
| Physical | plate-box / Path N / HD-* parked |
| Obsolete | Anything still describing pre-cameras world as current is stamped or fixed |

### 4.3 Obsolete labeling template

At top of historical/obsolete files (adapt tone to file):

```markdown
> **Status:** HISTORICAL / OBSOLETE as living guidance (epoch: <date or tag>).
> **SoT now:** `docs/IMPLEMENTATION_TASKS.md` § PRIORIDAD · tag `v0.4.2` ·
> [M7 closeout](../../.jes/artifacts/engineer_note_fase_m_closeout_m7.md).
> Do not treat this file as the current execution queue.
```

### 4.4 Forbidden edits

- Inventing firmware/GCS/ELRS product behavior in Jarvis  
- New architectural subsystems or Conversation Engine revival  
- Silent deletion of BUGS / closed IMPLEMENTATION_TASKS history  
- Changing `src/` / `ui/` / `tests/` / `library/` “to match docs”  
- Version bump  
- Claiming suite numbers without running or citing M7 closeout figure + “verify at ★”  
- Marking HD-* as PRIORIDAD  

---

## 5. Tests / verification (doc Buy)

| ID | Check |
|---|---|
| T1 | Inventory lists **every** file under `docs/` (count match `find`) |
| T2 | No living header still claims tip **`0.4.1`** as current **without** historical framing |
| T3 | Living PRIORIDAD ≠ Fit VERIFIED / software closeout lean / M7 GATE AHORA |
| T4 | Acquisition or Continuity map names **cameras** and **vtx** catalog paths |
| T5 | `CatalogRebindKey` families ⊆ documented named help-choose list (or explicit “not IDLE-named” for kit/radio) |
| T6 | USER_GUIDE examples for cámara/vtx still match `resolve_idle_catalog_rebind` + offer copy |
| T7 | At least one explicit **OBSOLETE/HISTORICAL** stamp added where Phase 0 found active-obsolete prose |
| T8 | Report lists every file touched + every file stamped + deferred list |
| T9 | `rg` sanity: `docs/` should not still say `PRIORIDAD = Fit VERIFIED` or `software closeout lean Continuity intent` as present tense AHORA (allow quotes inside historical archive sections if clearly dated) |

No new pytest required unless Claude discovers a doc that cites a **nonexistent** module path — then either fix the doc path or note as code debt (do not invent the module).

---

## 6. Report shape

`.jes/artifacts/implementation_report_docs_folder_truth_sync_b1.md`:

1. Method (commands, key files opened).  
2. Phase 0 summary counts: living updated / stamped historical / deferred.  
3. Table of edits (path · change summary).  
4. Obsolete register (or link).  
5. Residual risks (docs still thin on X).  
6. Explicit: **no** `src/` changes; package still **0.4.2**.

---

## 7. Out of scope

| Out | Why |
|---|---|
| Root `VISION.md` / `PRODUCT_SCOPE.md` / `CLAUDE.md` | Outside `docs/`; separate Buy if needed |
| Opening Fase C product IC | Engineer ★ separate |
| Full rewrite of `IMPLEMENTATION_TASKS.md` history | Archive; touch only misleading “current” |
| Full rewrite of `BUGS.md` | Historical register |
| UI copy / Tramp / SmartAudio | Not in this truth epoch as features |
| Translating entire system_map to Spanish | Not requested |
| Tag / bump | Already `0.4.2` |

---

## 8. Acceptance

**PASS when:**
- Inventory + report exist and are honest  
- Living docs (§4.1 priority set) reflect **v0.4.2 / Fase M CLOSED / Fase C await ★**  
- Obsolete material is **labeled**, not silently wrong  
- T1–T9 hold  
- Cursor review PASS (or PASS WITH NOTES)

**ACCEPT (Engineer) when:** spot-check PRIORIDAD + ARCHITECTURE header + system_map master + USER_GUIDE cámara/vtx still feel true to CLI.

---

## 9. Handoff

```text
Engineer → ★ this IC (docs Buy; can run before any Fase C product Buy)
Claude   → Phase 0 inventory → Phase 1 edits → report
Cursor   → independent review vs this IC
Engineer → spot-check / ACCEPT
```

**Estimate:** large read (13k+ lines under `docs/`) · prefer systematic rg + headers first · do not boil the ocean on archive bodies.

---

## 10. Suggested PRIORIDAD blurb (Cursor may paste on ★)

```text
COLA docs: B1-docs-folder-truth-sync READY — audit docs/ vs code @ v0.4.2;
label obsolete; no src/; no bump. Fase C product still await ★.
```
