# Implementation Report — Docs truth-sync integral after C35 / Taller (`B1-docs-truth-sync-after-c35`)

**IC:** [`implementation_contract_docs_truth_sync_after_c35_b1.md`](implementation_contract_docs_truth_sync_after_c35_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-25
**Status:** Landed — awaiting Cursor independent review + Engineer ★ ACCEPT. **No `v0.5.36` tag yet** (confirmed via `git tag -l | sort -V | tail -5` at close of this Buy: `v0.5.31`, `v0.5.32`, `v0.5.33`, `v0.5.34`, `v0.5.35` — `v0.5.36` does not exist). Note: `v0.5.35` (cylinder's own tag) exists locally but has not been pushed to origin, per the Engineer's own note at handoff.

---

## 0. Read this first — honesty summary

This Buy is **docs only**. D1 (the last integral docs Buy) left the base
maps and native README frozen at the Fase C C1-C5 snapshot (tag
`v0.5.3`, 2026-09-20) while thirty-plus platform rungs (C6-C35) plus two
Taller CSS visor-face fixes landed since. This Buy makes `docs/system_map/`,
`native/flight_control/README.md`, and `docs/USER_GUIDE_CRAFT_MONTAGE.md`
§8.4 tell the same tagged truth `ARCHITECTURE.md` §1c / `PLATFORM_CAPABILITY_VISION.md`
§13 / the PRIORIDAD banner already do. **No product code was touched.**

```text
docs tip != flying != gyro live != DShot pin != new C-xxx != standoff x8 shipped
```

**Exists:** maps and READMEs that now name the same tagged tip (`v0.5.35`)
as `ARCHITECTURE.md`. **Impossible:** a new craft connection; firmware on
the desk; the MY5/standoff catalog claimed as shipped. Nothing in this
Buy is any of those.

---

## 1. Phase 0 gate (IC §0 decision 8) — cleared before any edit

`.jes/artifacts/inventory_docs_truth_sync_after_c35_b0.md` was written
**first**, one row per file: 8/8 IC §1.1 "must audit + update" files,
9/9 IC §1.2 "must not rewrite" files (all verified via grep/read —
none needed a fresh stamp since `BUGS.md`/`FASE_LLM.md`/`CODE_AUDIT_CORE.md`
already carried `HISTORICAL` banners from a prior Buy), the 4-file
living quartet, and all 22 remaining `docs/*.md`/`.tsx` files in the
repo (grep-verified zero stale Fase C references in every one). Only
after that gate was recorded did Phase 1 editing begin.

---

## 2. Phase 1 edits vs IC §1.1 (required fixes)

| File | Fix applied |
|---|---|
| `docs/system_map/README.md` | Header clause rewritten: tip `v0.5.35`, live suite `3691`/UI vitest `142`/`ctest` `76/76`, names C6-C35 + Taller CSS by category, C++ tree named as existing and isolated |
| `docs/system_map/JARVIS_SYSTEM_MAP.md` | Both the "Fase C packages" section (§"structurally isolated") and the tagged-tip summary line rewritten: Python scaffold **plus** `native/flight_control/` (since C13, host+MCU-cross-compile, equally isolated); the "future IC" docstring quote is now explicitly framed as a *dated, pre-C13* lock on the Python files, not a current fact; tip `v0.5.35`; pointer to `ARCHITECTURE.md` §1c / `PLATFORM_CAPABILITY_VISION.md` §13 |
| `docs/system_map/CONNECTIONS.md` | **One new** changelog paragraph added after the existing C1-C5 entry, naming C6-C35 + Taller CSS (cuboid + cylinder) by category, isolation re-confirmed, tip `v0.5.35`. The canonical registry table itself — still ending at C-113 — was **not** touched |
| `docs/system_map/jarvis-system-map.canvas.tsx` | Header changelog comment: one new line (no new mermaid edges). "Product queue" Callout (the current-status headline, not a dated entry): rewritten to name the `v0.5.35` tip and every Buy category. The dated historical "Shipped — Fase C C1-C5 @ v0.5.3" Callout: its one false-as-current phrase ("no C++/CMake tree") reframed as "accurate as of this date" with a forward pointer. One **new** dated "Shipped — Fase C C6-C35 + Taller CSS @ v0.5.35" Callout added after it. No fake SPI/`step` graph nodes added anywhere |
| `docs/system_map/DIAGRAMS.md` | One epoch line appended to the existing chronology paragraph (no new mermaid edges): C6-C35 + Taller CSS, isolated, tip `v0.5.35`, PRIORIDAD retargeted to cola standoff points |
| `native/flight_control/README.md` | Layout list extended to name `dshot.hpp`/`dshot.cpp`, `spi.hpp`/`spi.cpp`, `spi_probe.hpp`/`spi_probe.cpp`, and `test_dshot.cpp`/`test_spi.cpp`/`test_spi_probe.cpp` (previously stopped at C28's `uart.hpp`/`test_uart.cpp`); both C30 "not yet tagged" mentions corrected to "★ ACCEPT CLOSED @ tag `v0.5.28`" (verified `git tag -l v0.5.28` exists, commit `e99965d`); five new honesty paragraphs added for C31 (DShot encode), C32/C33 (SPI port + scripted slave), C34 (`probe_rx`), and C35 (denser `step` density tests), matching this README's own established per-Buy paragraph style and citing the correct tags (`v0.5.29`/`v0.5.30`/`v0.5.31`/`v0.5.32`/`v0.5.33`, each verified via `git log -1 --format=%s <tag>`) |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` §8.4 | One short Spanish paragraph added (after the Situar bullet list, before the `---`/§9 divider): a declared box is one six-face prism, a declared cylinder is one body (2 caps + 16 slats), a thin plate/short hub is still one solid — not extra parts, not CAD, not a fit verdict. No `161×42×2` mm and no standoff `×8` anywhere in the new text (grep-verified, §6 below) |
| `docs/system_map/00_entry/ENTRY_MAP.md` | One clause appended to the visor-projector table row: Taller CSS cuboid + cylinder faces @ `v0.5.35`, still C-094/C-113 class, no new C-xxx |

---

## 3. IC §1.2 (must not rewrite) — confirmed untouched

`VISION.md`, `docs/PROJECT_CONTINUITY.md`, `docs/ENGINEERING_READINESS_VISION.md`,
`docs/BUGS.md`, `docs/FASE_LLM.md`, `docs/CODE_AUDIT_CORE.md`, the
historical/closed sections of `docs/IMPLEMENTATION_TASKS.md`, `ARCHITECTURE.md`
§1c's own historical C3 quote, and `src/jarvis/flight_software/**`
docstrings — all confirmed via the Phase 0 inventory and re-verified
with `git diff --stat` at close (§6): zero edits to any of them. No
standoff ×8 / MY5 catalog / plate-box seed is claimed as shipped
anywhere touched by this Buy.

---

## 4. IC §1.3 (living quartet) — retargeted, no new essay

| File | What changed |
|---|---|
| `README.md` | Header banner + both "Next" pointers retargeted to this Buy's LANDED status; new "What v0.5.36 includes" section added (a docs-Buy summary, not a product essay) |
| `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD | Banner retargeted; one new table row added for this Buy |
| `docs/ARCHITECTURE.md` §1a/§1c | Banner (§2) retargeted; the cylinder paragraph's own "Siguiente" pointer retargeted. **No new essay paragraph** — this Buy is docs-only, not a product Buy, per IC §1.3's own "do not duplicate C35/Taller essays" rule |
| `docs/PLATFORM_CAPABILITY_VISION.md` §13 | "Next" pointer retargeted only. **No new §13 block** — this Buy does not touch `src/jarvis/flight_software/` |

---

## 5. Verified — real test runs (T7/T9)

```text
$ git status --short -- src/jarvis ui/spatial-board library
# only pre-existing, external, unrelated diffs (src/jarvis/actions,
# src/jarvis/core, src/jarvis/schemas, src/jarvis/workspace,
# src/jarvis/knowledge, library/frames — the parallel craft-geometry
# track's own work, present before this Buy started, not touched by it)
# — zero NEW diffs from this Buy anywhere under src/, ui/, or library/

$ python -m pytest -q
3691 passed, 2 skipped in 8.01s

$ cd build/flight_control && ctest
100% tests passed out of 76

$ cd ui/spatial-board && npm test
Test Files  15 passed (15)
     Tests  142 passed (142)

$ npm run typecheck
> tsc --noEmit
(clean)
```

All four counts are **exactly unchanged** from the pre-Buy baseline —
expected and correct, since this Buy adds zero product tests (T7's own
"no required new product tests").

---

## 6. Honesty-lock grep (T2/T3/T4/T5/T6, run at close of this Buy)

```text
$ grep -n 'tagged tip `v0.5.3`\|Fase C tagged tip `v0.5.3`' docs/system_map/README.md docs/system_map/JARVIS_SYSTEM_MAP.md
# no match — v0.5.3 no longer named as the CURRENT tip in either file
# (T2)

$ grep -n "no C++/CMake tree\|C++ (future IC)" docs/system_map/README.md \
    docs/system_map/JARVIS_SYSTEM_MAP.md docs/system_map/jarvis-system-map.canvas.tsx
# 2 hits, both explicitly framed as historical/dated ("describes the
# pre-C13 state... not a current architectural fact" / "accurate as of
# this date") — neither claims the absence as CURRENT (T3)

$ grep -n "C-113" docs/system_map/CONNECTIONS.md | tail -3
# highest ID referenced is still C-113 — no C-114 anywhere (T4)

$ grep -c "spi\.hpp\|ScriptedSpi\|probe_rx\|dshot" native/flight_control/README.md
14
# spi.hpp / ScriptedSpi / probe_rx / dshot all named (T5)

$ grep -n "161.42.2\|161×42×2\|standoff.*×8\|standoff.*x8" docs/USER_GUIDE_CRAFT_MONTAGE.md
# no match — no MY5 mm, no standoff ×8 anywhere in the guide (T6)
```

---

## 7. Files changed

**New:**
- `.jes/artifacts/inventory_docs_truth_sync_after_c35_b0.md` (Phase 0 gate)
- `.jes/artifacts/implementation_report_docs_truth_sync_after_c35_b1.md` (this file)

**Modified (docs only):**
- `docs/system_map/README.md`
- `docs/system_map/JARVIS_SYSTEM_MAP.md`
- `docs/system_map/CONNECTIONS.md`
- `docs/system_map/jarvis-system-map.canvas.tsx`
- `docs/system_map/DIAGRAMS.md`
- `native/flight_control/README.md`
- `docs/USER_GUIDE_CRAFT_MONTAGE.md`
- `docs/system_map/00_entry/ENTRY_MAP.md`
- `README.md`, `docs/IMPLEMENTATION_TASKS.md`, `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md` (living quartet retarget)
- `pyproject.toml` (`0.5.35` → `0.5.36`)
- 41 pre-existing Python test files re-pinned from `0.5.35` to `0.5.36` (literal `'version = "X.Y.Z"' in text` pattern and the `match.group(1) == "X.Y.Z"` regex pattern)

**Zero edits** to any file under `src/jarvis/` (production code), `ui/`
(besides none — this Buy touches zero `ui/` files), or `library/` — the
one file this report modified inside `native/flight_control/` is its own
`README.md`, a docs file, never `include/`/`src/`/`tests/`.

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

Every file this Buy touched carries "landed, awaiting Cursor review +
Engineer ★ ACCEPT, no `v0.5.36` tag yet" phrasing where a version/status
claim appears — none says `v0.5.36` is tagged or ACCEPT CLOSED. Confirmed
via `git tag -l | sort -V | tail -5` at close of this Buy: `v0.5.31`,
`v0.5.32`, `v0.5.33`, `v0.5.34`, `v0.5.35` — `v0.5.36` does not exist
yet. This report and the docs it touches also note that `v0.5.35` itself
is a **local** tag not yet pushed to origin, per the Engineer's own
handoff note on the cylinder Buy — this Buy did not push anything
either.

---

## 9. Residual / next steps

- Standoff perimeter points is the one remaining cola item named across
  every retargeted "Next" pointer in this Buy — not opened here.
- This report lists every IC §1.1 file touched (8, §2 above) and every
  IC §1.2 stamp-only file verified untouched (9, §3 above), per IC T10.
- A future integral docs Buy (a "D3") would be the next point to
  re-audit the base maps, should another multi-Buy platform stretch
  land before the next truth-sync — this Buy does not schedule one, it
  only closes the gap D1 left open.

---

## 10. Acceptance self-check vs IC §7

- T1 (inventory, one row per file): ✅ `.jes/artifacts/inventory_docs_truth_sync_after_c35_b0.md`, 8+9+4+22 rows.
- T2 (`JARVIS_SYSTEM_MAP.md` + `system_map/README.md` tip `v0.5.35`, not `v0.5.3` as current): ✅ grep-verified, §6.
- T3 (no "no C++/CMake tree"/"future IC" as current in those two + canvas): ✅ both hits reframed as historical, §6.
- T4 (`CONNECTIONS.md` canonical table still ends C-113, new paragraph names C6-C35+Taller, no new ID): ✅ §6.
- T5 (`native/flight_control/README.md` names `spi.hpp`/`ScriptedSpi`/`probe_rx`/`dshot`/C35 density; C30 tagged `v0.5.28`): ✅ §6, §2.
- T6 (USER_GUIDE one-prism/one-cylinder-body line; no `161×42×2`/standoff ×8): ✅ §6.
- T7 (no `src/`/`ui/`/`library/` diffs): ✅ §5.
- T8 (`pyproject` `0.5.36`): ✅ `pyproject.toml` + all 41 checkpoint tests re-pinned.
- T9 (full pytest + host `ctest` green): ✅ `3691 passed, 2 skipped`; `76/76`.
- T10 (report lists every §1.1 file touched + every stamp-only file): ✅ §2 (8 files) + Phase 0 inventory's own §2/§4 (9 + 22 stamp-only files).

**PASS** against every criterion in IC §7. **FAIL conditions** (product
code edited, C-114 invented, maps still tip `v0.5.3`, "future IC" as
current, MY5/standoff×8 claimed shipped, VISION rewrite) — none present,
verified above.
