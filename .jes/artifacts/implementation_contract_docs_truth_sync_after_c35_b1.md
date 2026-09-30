# Implementation Contract — Docs truth-sync integral after C35 / Taller (`B1-docs-truth-sync-after-c35`)

**Project:** Jarvis  
**Date:** 2026-09-25  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check of system_map tip + native README + USER_GUIDE §8.4

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — docs work landed @ `73d289c`; Cursor review PASS WITH NOTES. **No tag `v0.5.36`** (superseded: next tip was C36 @ **`v0.5.37`**). Spot-check residual retired as historical. Optional later **D3** = truth-sync maps to current `v0.6.x` tip (separate Buy).
**Parents:**
- [Taller CSS cuboid faces](implementation_contract_geometry_taller_css_cuboid_faces_b1.md) — six faces meet on a thin plate · tag **`v0.5.34`**  
- [Taller CSS cylinder faces](implementation_contract_geometry_taller_css_cylinder_faces_b1.md) — caps + 16 slats on Ø×H · tag **`v0.5.35`** on ACCEPT (this docs Buy waits)  
- [C35](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) — denser `step` tests @ **`v0.5.33`**  
- [D1 docs folder truth-sync](implementation_contract_docs_folder_truth_sync_b1.md) — last integral docs Buy, epoch **`v0.4.2` / v0.4.3 / Fase C C1–C5 @ `v0.5.3`**  
- Cursor audit 2026-09-25 (Engineer: living Buy quartet is current; system_map + native README froze at 2026-09-20)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front** (this Buy is **docs only**)

**Type:** **Documentation Buy** — make **base maps and READMEs** tell the same tagged truth as `ARCHITECTURE.md` §1c / `PLATFORM` §13 / PRIORIDAD. Not a product feature. Not a new `C-xxx`. Not silicon. Not standoff points.  
**Package:** bump to **`0.5.36`**; tag **`v0.5.36`** only after Engineer ACCEPT.  
**Not** `src/` / `ui/` / `library/` product edits · not new connections · not claiming standoff ×8 · not claiming MY5 caliper catalog · not rewriting `VISION.md` / Continuity maps / `BUGS.md` · not DShot wire · not C30 desk DFU.

**Outputs (required):**
1. Phase 0 inventory: `.jes/artifacts/inventory_docs_truth_sync_after_c35_b0.md` — **one row per file** in scope (§1)  
2. Phase 1 edits per §0 / §3  
3. Report: `.jes/artifacts/implementation_report_docs_truth_sync_after_c35_b1.md`  
4. `pyproject.toml` → **`0.5.36`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-docs-truth-sync-after-c35`** — docs match tagged product after cylinder ACCEPT |
| 2 | One front | Docs only. Do **not** open standoff points, MY5 catalog seed, F460, silicon, cuboid/cylinder recut |
| 3 | What this Buy demonstrates | D1 left maps at C5/`v0.5.3`. Thirty platform rungs later, PRIORIDAD is honest and CONNECTIONS is not. **Human:** “si abres el mapa, ves el mismo tip que en Architecture.” |
| 4 | Authority | **Tagged code + closed ICs > living PRIORIDAD > old map prose.** If prose conflicts with code, **fix the doc or stamp obsolete**. Never “fix” by changing `src/` / `ui/` / `library/` |
| 5 | Truth epoch | **`v0.5.35`** (cylinder CSS ACCEPT) on top of **`v0.5.34`** (cuboid) / **`v0.5.33`** (C35). Craft tip remains **`v0.4.3`**. Suite / UI / `ctest` counts = **live at ★**, do not copy 3236 / 3166 |
| 6 | No new `C-xxx` | Fase C C6–C35 and Taller CSS (cuboid + cylinder) added **zero** craft connections. Isolation holds. **Do not invent C-114** for `probe_rx` / `step` / cuboid / cylinder faces |
| 7 | C++ honesty | Maps must **not** say production FC is a **future** IC or that there is **no C++/CMake tree**. C++ exists under `native/flight_control/` since C13; host + MCU image exist; **not** flying, **not** gyro live, **not** DShot pin. The C3 quote in Python module docstrings (“future IC”) is **historical lock on those Python files** — do **not** edit `plant.py` to “fix” the map |
| 8 | Phase 0 gate | **STOP before bulk edits** until the inventory artifact has one row per in-scope file |
| 9 | Obsolete policy | Stamp `**Status: OBSOLETE / historical**` + pointer to SoT. Do **not** delete `BUGS.md` body, closed TASKS archives, or C3 historical paragraphs in ARCHITECTURE §1c |
| 10 | Version | **`0.5.35` → `0.5.36`**. Do **not** implement until cylinder CSS is ACCEPT-tagged `v0.5.35` |
| 11 | Forbidden | “we fly” · new C-xxx · standoffs ×8 as shipped · MY5 161×42×2 as catalog SoT · rewriting VISION · touching `src/`/`ui/`/`library/` |

**Product sentence:**

```text
El mapa, Connections, la guía y el README nativo dicen el mismo tip
que Architecture: v0.5.35, C++ existe y está aislado, Taller es visor.
```

**Defaults locked by Cursor:**
- Phase 0 inventory then Phase 1  
- Must-fix list in §3 is normative (not optional polish)  
- Spanish in USER_GUIDE; maps may stay bilingual  

---

## 1. Scope (normative)

### 1.1 Must audit + update (living / stale tip)

| File | What is wrong today (2026-09-25) | Required fix |
|---|---|---|
| `docs/system_map/README.md` | Header: Fase C tip **`v0.5.3`**, suite **3236** | Tip **`v0.5.35`** (after cylinder tag) · live suite/UI · C++ tree exists, isolated, no new C-xxx |
| `docs/system_map/JARVIS_SYSTEM_MAP.md` | § Fase C = C1–C5 only; “C++ (future IC)”; tagged tip `v0.5.3` | Rewrite **that section** (not the craft chain): Python scaffold **plus** `native/flight_control/` C13–C35; still **zero** import into orchestrator/Board/`library/`; tip `v0.5.35`; pointer to ARCHITECTURE §1c / PLATFORM §13 |
| `docs/system_map/CONNECTIONS.md` | Last Fase C note is C1–C5 @ `v0.5.3` | **One new changelog paragraph** after the C1–C5 note: C6–C35 + Taller CSS (cuboid + cylinder), **no new C-xxx**, isolation holds, tip `v0.5.35`. Canonical registry **unchanged** (still C-001…C-113) |
| `docs/system_map/jarvis-system-map.canvas.tsx` | Callouts: C1–C5 @ v0.5.3, “no C++/CMake tree”, “future IC” | Same facts as the map section. **Do not** add fake nodes for SPI/`step` |
| `docs/system_map/DIAGRAMS.md` | Fase C line if still C5-only | One epoch line matching the map (no new mermaid edges) |
| `native/flight_control/README.md` | Tree stops ~C28–C30; C30 “not yet tagged”; missing spi / ScriptedSpi / probe_rx / dshot / C35 tests | Layout lists those files; C30 **is** tagged `v0.5.28`; honesty: encode ≠ pin, probe ≠ gyro, many ticks ≠ flying |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` §8.4 | Taller workshop text OK; no cuboid/cylinder honesty | **One short paragraph:** a declared box is **one** six-face prism; a declared cylinder is **one** body (2 caps + 16 slats); a thin plate / short hub is still one solid, not extra parts; **not CAD / not fit**. Only after cylinder ACCEPT. Do **not** add MY5 mm or standoff ×8 |
| `docs/system_map/00_entry/ENTRY_MAP.md` | Visor projector line @ v0.4.2 | One clause: Taller CSS cuboid + cylinder faces (visor) @ `v0.5.35`; still C-094 / C-113 class; no new C-xxx |

### 1.2 Must **not** rewrite (stamp or leave)

| File | Rule |
|---|---|
| `VISION.md` | Product contract v0.1 — **leave** (not a changelog) |
| `docs/PROJECT_CONTINUITY.md` | Craft Continuity SoT — **leave** except a broken cross-link |
| `docs/ENGINEERING_READINESS_VISION.md` | Readiness families — **leave** |
| `docs/BUGS.md` / `docs/FASE_LLM.md` / `docs/CODE_AUDIT_CORE.md` | Archive — banner if missing; no body rewrite |
| `docs/IMPLEMENTATION_TASKS.md` historical closed sections | **Do not** rewrite thousands of lines. PRIORIDAD after this Buy: standoff cola · silicon parked |
| `ARCHITECTURE.md` §1c C3 quote | Historical C3 lock — **leave**. Do not “correct” C3 prose to erase “future IC” |
| `src/jarvis/flight_software/**` docstrings | **Out of this Buy** |
| Standoff ×8 / MY5 catalog / plate-box seed | **Unaccepted / uncommitted** — must **not** appear as shipped SoT |

### 1.3 Living quartet (already current each Buy)

`README.md` · `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD · `docs/ARCHITECTURE.md` §1a/§1c · `docs/PLATFORM_CAPABILITY_VISION.md` §13 — retarget **Next** to this Buy’s closeout then cola standoff. Do **not** duplicate C35/Taller essays.

---

## 2. Non-goals

New `C-xxx`, canvas graph of SPI/`step`, product code, Taller recut, standoff points, MY5 catalog, silicon, rewriting Continuity maps, deleting archives, claiming flying / gyro live / DShot pin.

---

## 3. Integration rules

| Existing | This Buy |
|---|---|
| D1 @ v0.4.2 | **Superseded as living epoch**; D1 file stays CLOSED historical |
| C-113 / C-094 | **Unchanged** |
| Isolation grep | Still zero `flight_software` imports from `core/` / Board / `library/` — **document**, do not recode |
| Taller CSS | **Already ACCEPT** when this starts — USER_GUIDE may name it |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Inventory artifact exists, one row per §1.1 + remaining `docs/*.md` (stamp-only rows OK) |
| T2 | `JARVIS_SYSTEM_MAP.md` + `system_map/README.md` named tip is **`v0.5.35`** (or `v0.5.36` after bump — must not remain `v0.5.3` as current tip) |
| T3 | Those two files plus canvas do **not** claim “no C++/CMake tree” or “C++ (future IC)” as **current** (historical C3 quote in ARCHITECTURE §1c allowed) |
| T4 | `CONNECTIONS.md` canonical table still ends at **C-113**; new paragraph names C6–C35 + Taller, no new ID |
| T5 | `native/flight_control/README.md` mentions `spi.hpp` / `ScriptedSpi` / `probe_rx` / `dshot` / C35 `test_loop` density; C30 tagged `v0.5.28` |
| T6 | USER_GUIDE §8.4 has the one-prism / one-cylinder-body honesty line; **no** 161×42×2 / standoff ×8 as shipped |
| T7 | No `src/` / `ui/` / `library/` diffs in this Buy |
| T8 | `pyproject` **`0.5.36`** |
| T9 | Full pytest + host `ctest` green (no required new product tests) |
| T10 | Report lists every §1.1 file touched + every stamp-only file |

---

## 5. Honesty / forbidden

```text
docs tip ≠ flying ≠ gyro live ≠ DShot pin ≠ new C-xxx ≠ standoff ×8 shipped
```

**Exists:** maps and READMEs that name the same tagged tip as Architecture.  
**Impossible:** a new craft connection; firmware on the desk; catalog MY5 as SoT from this Buy.

---

## 6. Docs (this Buy *is* the docs)

PRIORIDAD after ACCEPT: cola standoff points. PLATFORM / ARCHITECTURE “Next” retarget. Root README tip `v0.5.36`.

---

## 7. Acceptance

**PASS when:** T1–T10 · no new C-xxx · C++ named as existing-and-isolated · USER_GUIDE cuboid+cylinder line · native tree current.  
**FAIL if:** product code edited · C-114 invented · maps still tip `v0.5.3` · “future IC” as current · MY5/standoff×8 claimed shipped · VISION rewrite.

---

## 8. Handoff

```text
Engineer → ACCEPT Taller cuboid + tag v0.5.34  (done)
Engineer → ACCEPT cylinder CSS + tag v0.5.35  (STOP until then)
Engineer → ★ this IC
Claude   → Phase 0 inventory, then Phase 1 edits + 0.5.36
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.36
Cola     → standoff points (still no ACCEPT)
```

**STOP** if `v0.5.35` does not exist.

---

## 9. PRIORIDAD blurb (paste on ★)

```text
Docs: B1-docs-truth-sync-after-c35 READY —
maps/Connections/native README/USER_GUIDE match v0.5.35; no new C-xxx.
```

---

## 10. Engineer ★ checklist

1. Buy = **docs only** after cylinder tag OK?  
2. No new `C-xxx` · C++ exists and stays isolated OK?  
3. USER_GUIDE one prism + one cylinder body · no MY5/standoff×8 as shipped OK?  
4. Version **`0.5.36`** after `v0.5.35` OK?  
