# Implementation Report — Explain maps expand (`B1-explain-maps-expand`)

**Project:** Jarvis
**Date:** 2026-09-28
**Implementer:** Claude Code
**Contract:** [`implementation_contract_explain_maps_expand_b1.md`](implementation_contract_explain_maps_expand_b1.md)
**Status:** Code delivered and Cursor-reviewed (**PASS**); IC §8 living-docs gap flagged by that review (**HOLD**, `implementation_review_explain_maps_expand_b1.md`) closed by the **§7b/§8 remediation** below (2026-09-28). Delivered for re-review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.4` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.4` is reserved for Engineer ACCEPT per IC §0 row 10 / §5.

---

## 1. Files changed

**New:**
- `src/jarvis/intelligence/explain_maps.py` — `FS_EXPLAIN_MAP`, `HD_EXPLAIN_MAP`, `ids_for_rung`
- `tests/test_explain_maps_expand_b1.py` — T1–T6 (+3 supporting checks)

**Modified:**
- `src/jarvis/intelligence/explain_aliases.py` — `EXPLAIN_ALIASES` expanded from 4 to 29 entries
- `src/jarvis/intelligence/ontology_retrieve.py` — added `list_solid_ids()` (same read-only `_iter_notes` scan the existing lookups already use)
- `src/jarvis/intelligence/explain.py` — added `run_explain_list_cli()`, `run_explain_rung_cli()`; positional-query path (`resolve_explain_query`/`format_explain_cite`/`run_explain_cli`) unchanged
- `src/jarvis/adapters/cli/main.py` — `explain` subparser extended with a mutually-exclusive `--list`/`--rung KEY`/positional `query` group
- `src/jarvis/intelligence/README.md` — new "Explain maps (A5)" section; updated Buys/Package header, Tests section, and the `list_solid_ids` honesty note
- `pyproject.toml` — `version = "0.6.3"` → `version = "0.6.4"`
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line + A5 row updated to "delivered, awaiting Cursor review + Engineer ACCEPT"
- `docs/ARCHITECTURE.md` §1 — `intelligence/` knowledge-tree row: A5 delivered @ package `0.6.4`
- `docs/PLATFORM_CAPABILITY_VISION.md` §12 — placement line updated: A5 delivered, pending ACCEPT before tag
- `docs/ONTOLOGY_CROSSWALKS.md` header — one-line epoch note: `explain_maps.py` code-ifies the seeded crosswalk rows (IC §0 row 6, optional pointer)

**Not touched:** `ontology/` (read-only; confirmed zero diff on any vault note below), `library/`, `jarvis.core`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm`, `jarvis.knowledge.retriever`, `JarvisOrchestrator`/chat path.

---

## 2. Alias expansion verification (IC §1)

Before writing `explain_aliases.py`, I ran a full vault scan for every `estado: solid` note's frontmatter `id` (script output preserved below) and cross-checked every proposed alias target against it:

```text
vectores | corriente-y-circuitos | magnetismo | dinamica | momento-y-rotacion
control-clasico | c-rate-de-bateria | forma-medicion-banco-empuje
punto-de-operacion-vs-capacidad-intrinseca | actuadores | motor-dc | motores
control-robotico | navegacion-y-planificacion | acelerometro | giroscopio
imu | sensores-de-movimiento
```

All 18 solid ids. Every target in the IC's own §1 seed table matched one of these exactly — **no spelling adjustment was needed**. `EXPLAIN_ALIASES` now has **29 entries** (4 original A3 seeds + 25 new), within the IC's ≤40 cap, covering every remaining solid spine id with at least one short alias. `tests/test_explain_maps_expand_b1.py::test_t6_...` re-verifies this same invariant programmatically at test time (every `EXPLAIN_ALIASES` value must be a current solid id), so a future vault change that demotes a note would fail CI rather than silently ship a stale alias.

---

## 3. FS/HD maps (IC §2)

`FS_EXPLAIN_MAP`/`HD_EXPLAIN_MAP` use the IC's own normative seed values verbatim. Cross-checked against `docs/ONTOLOGY_CROSSWALKS.md` before writing the module:

```text
$ grep -n "C3\|C7\|C10\|C39\|C42\|HD-001\|HD-005" docs/ONTOLOGY_CROSSWALKS.md
C3  -> [[Sensores de movimiento]] · [[IMU]]
C7  -> [[IMU]] · [[Giroscopio]] · [[Acelerómetro]] · [[Control robótico]] · [[Vectores]]
C10 -> [[Actuadores]] · [[Motores]] · [[Motor DC]]
C39 -> [[Navegación y planificación]] · [[Control robótico]]
C42 -> [[IMU]] · [[Sensores de movimiento]]
HD-001 -> [[C-rate de batería]] · [[Corriente y circuitos]] · [[Punto de operación vs capacidad intrínseca]]
HD-005 -> [[Forma de medición en banco de empuje]] · [[Punto de operación vs capacidad intrínseca]] · [[Motor DC]]
```

Exact match to the shipped dicts (each `[[Nombre]]` wikilink resolved to its corresponding `id`). `ids_for_rung(key)` normalizes via `.strip().upper()` so `C7`/`c7` and `HD-001`/`hd-001` resolve identically; returns a `list()` copy (never the live dict object) so callers can't mutate the static table; `None` on a miss. `explain_maps.py` never imports `jarvis.flight_software` — both maps are hand-written static dicts, not a rung registry read from anywhere.

---

## 4. CLI (IC §3)

Extended the `explain` subparser with a mutually-exclusive group: positional `query` (now `nargs="?"`), `--list`, `--rung KEY`. Verified argparse's actual behavior before wiring (a standalone scratch check) — the three are mutually exclusive, `explain` alone parses with all three `None`/`False` (handled by an explicit `explain_parser.error(...)` in `main()`, not a silent fallthrough), and `explain c-rate --list` correctly exits non-zero as a usage error.

```text
$ jarvis explain --list
Solid ontology ids:
  acelerometro
  actuadores
  c-rate-de-bateria
  ... (18 total)

Known aliases:
  accel -> acelerometro
  ... (29 total)

$ jarvis explain --rung HD-005
HD-005 ->
  forma-medicion-banco-empuje  (Forma de medición en banco de empuje)
  punto-de-operacion-vs-capacidad-intrinseca  (Punto de operación vs capacidad intrínseca)
  motor-dc  (Motor DC)
```

`--rung` prints ids + `nombre` only, never the `[DEFINICION]`/`[INTUICION]` bodies (IC §0 row 6 — "does not dump... by default"). The positional query path (`jarvis explain c-rate-de-bateria`) is byte-for-byte unchanged from A3 — `resolve_explain_query`/`format_explain_cite`/`run_explain_cli` were not modified.

---

## 5. Tests

`tests/test_explain_maps_expand_b1.py` — 9 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | Alias `imu`/`gyro` resolve via `resolve_explain_query` to solid cites (`imu`, `giroscopio`) | PASS |
| T2 | `ids_for_rung("C7")` contains `imu` and `giroscopio`; case-normalized (`"c7"` gives the same result) | PASS |
| T3 | `ids_for_rung("HD-001")` contains `c-rate-de-bateria`; case-normalized | PASS |
| T4 | Unknown rung/HD key → `None`; `run_explain_rung_cli` on an unknown key → exit 1 | PASS |
| T5 | `--list` output mentions `c-rate-de-bateria` and the `c-rate -> c-rate-de-bateria` alias line; printed id list matches the real solid-id scan exactly | PASS |
| T6 | `explain_maps.py`/`explain_aliases.py` have no `jarvis.core`/LLM-named imports and no write API; every id referenced by the new maps/aliases is a real, current solid vault id | PASS |
| — | A3 query path unchanged (`resolve_explain_query("c-rate")` still resolves to `c-rate-de-bateria`) | PASS |
| — | Subprocess smoke: `--list`, `--rung C7`, and the `c-rate --list` mutual-exclusion error | PASS |
| — | `pyproject.toml` reads `version = "0.6.4"` | PASS |

```text
$ python -m pytest tests/test_explain_maps_expand_b1.py -v
...
9 passed in 0.77s
```

Prior suites re-run: `tests/test_intelligence_scaffold_b1.py` (A1, T1–T5), `tests/test_ontology_retrieve_r2_b1.py` (A2, T1–T7), `tests/test_assistant_terminal_canal_b1.py` (A3, T1–T6) — **all IC-mandated assertions still green.** Three of my own *additional* (non-IC-required) version-checkpoint tests from the prior three Buys now fail (`test_pyproject_version_is_0_6_1`/`_0_6_2`/`_0_6_3`) — expected, same documented class of drift as every prior report in this series (a version string frozen at that Buy's own landing time, not an IC-mandated T1–TN assertion).

---

## 6. Full suite

```text
$ python -m pytest -q
52 failed, 3739 passed, 9 skipped in 16.91s
```

Before this Buy (parent tip `v0.6.3`), the suite had 51 pre-existing version-pinned checkpoint failures (documented across all three prior reports in this series). This Buy adds exactly one more of the same kind (A3's own `test_pyproject_version_is_0_6_3`, now stale at this Buy's `0.6.4` bump). Net: 9 new tests added (all pass), 1 additional stale checkpoint (expected), zero new behavioral failures, zero tests weakened or deleted.

---

## 7. Docs pointers (IC §0 row 6)

- `src/jarvis/intelligence/README.md` — new "Explain maps (A5)" section covering the static FS/HD dicts, `--list`/`--rung`, namespace honesty, and the alias expansion; Buys/Package header, Tip parent, and Tests sections all updated.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line and A5 cola row now read "delivered, package `0.6.4`, awaiting Cursor review + Engineer ★ ACCEPT."
- `docs/ARCHITECTURE.md` §1 — `intelligence/` row updated: A5 delivered @ package `0.6.4`, naming `--list`/`--rung`.
- `docs/PLATFORM_CAPABILITY_VISION.md` §12 — placement paragraph updated: A5 delivered on disk, pending ACCEPT before tag.
- `docs/ONTOLOGY_CROSSWALKS.md` header (optional per IC) — one-line note: `explain_maps.py` code-ifies the seeded crosswalk rows, explicitly "a finite subset mirroring this doc, not a replacement for it."

All are pointer-level edits, no rewrite epics.

### 7b. Remediation — IC §8 living docs sync (2026-09-28, ★ REMEDIATION, Cursor review HOLD → N1 blocking)

Cursor's independent review (`.jes/artifacts/implementation_review_explain_maps_expand_b1.md`) correctly found the first delivery covered only the thin pointer docs above and **missed IC §8's normative table** (new user guide, cheatsheet pointer, `C-114`, `ENTRY_MAP.md`, canvas/diagram mirrors). This subsection lists every path touched to close that gap — **no code changed in this remediation pass** (confirmed: `git diff --stat -- src/ tests/` after the remediation shows zero new lines beyond what §1 already reported for the original delivery; the full Assistant test suite re-run identically, same 3 pre-existing stale version-checkpoint failures, zero new ones).

**New:**
- `docs/USER_GUIDE_EXPLAIN.md` — new short user guide: direct query, `--list`, `--rung`, the `never_invents` honesty line, a cheatsheet, and known limits. Every command/output shown was run for real against the live CLI before being pasted in (not hand-typed from memory).

**Modified:**
- `docs/USER_GUIDE_CRAFT_MONTAGE.md` — one-line pointer added right after the cheatsheet's mission section: "Para conceptos… `jarvis explain <id/alias>` es un comando de terminal **separado** de este chat… Ver `docs/USER_GUIDE_EXPLAIN.md`."
- `docs/system_map/CONNECTIONS.md` — added **`C-114`** to the Canonical registry table and a full Detail entry (`Detail — 00 Entry`, right after C-003) with the normative Field/Value shape used by every other entry in the file, plus an explicit **"Non-edges (verified, not violated)"** paragraph naming exactly what the IC asked for: `explain` never reaches `jarvis.core`/`submit_command`/`JarvisOrchestrator` (so never `step()` or any Continuity write) and never touches `library/` catalog JSON. Registry counts bumped consistently (66→67 total `C-xxx`, 65→66 "unique edges" section header, 64→65 🟢 connected) — also added a chronology entry describing the four-Buy arc (A1–A5).
- `docs/system_map/00_entry/ENTRY_MAP.md` — `explain` documented beside `board` in "Key modules" (own table row, explicit "does not route through `handle_user_text`/`handle`"), the Inbound/Outbound line extended with C-114, and one line each added to "Local state touched" and "Tests".
- `docs/system_map/jarvis-system-map.canvas.tsx` — `C-114` added to the live `CONNECTIONS` data array (not just prose — it now participates in the interactive DAG/filter/count logic), a new `intelligence` node label, a new dated header-comment log line, and a new "Shipped" `Callout` block matching the file's own per-milestone pattern. **Also found and flagged, not silently fixed:** the file's header-comment running tallies (`Counts: 66 unique C-xxx… 63 connected…`) had already drifted one behind `CONNECTIONS.md` before this remediation — `C-113` itself was never added to the `CONNECTIONS[]` data array, only mentioned in prose. Corrected the connected count to mirror `CONNECTIONS.md`'s own authoritative top-line tally (65, not a naive 64) and left an inline comment documenting the gap rather than silently re-deriving C-113's own missing data-array entry (that backfill is outside this Buy's scope — flagging it here per the "docs reveal a naming mismatch" clause in the remediation instructions).
- `docs/system_map/DIAGRAMS.md` — canonical-count line updated (67 unique, through C-114), the "Counts (do not conflate)" table updated (67/65), and a new dated bullet describing the four-Buy Assistant arc, matching the file's existing per-milestone bullet style.
- `docs/system_map/JARVIS_SYSTEM_MAP.md` — new dated paragraph for the Assistant canal (mirroring the "Fase C tagged tip" paragraph style immediately above it) and the `CONNECTIONS.md` registry pointer line count bumped (66→67, `…C-113`→`…C-114`).

All of the above were verified against the actual live vault/CLI before writing (18 solid ids, 29 aliases, the exact `--rung HD-005` output block) rather than re-typed from the IC's own prose — see §5/§6 below and the original delivery's §3–§4 for the underlying verification work.

---

## 8. Acceptance criteria — self-check

**IC §5 (original delivery):**

- [x] Alias table expanded + solid-verified (18/18 targets confirmed against a fresh vault scan)
- [x] FS/HD maps seeded exactly as in IC §2, cross-checked against `ONTOLOGY_CROSSWALKS.md`
- [x] `--list` and `--rung` work (manual run + subprocess test)
- [x] A3 query path unchanged (`resolve_explain_query`/`format_explain_cite`/`run_explain_cli` untouched; explicit regression test)
- [x] Tests T1–T6 green
- [x] Report + docs + `pyproject` `0.6.4`
- [x] Tag `v0.6.4` **not created** — reserved for Engineer ACCEPT

**IC §8 (living docs sync — this remediation):**

- [x] `docs/USER_GUIDE_EXPLAIN.md` — new, real-commands-only guide
- [x] `docs/USER_GUIDE_CRAFT_MONTAGE.md` — cheatsheet pointer added
- [x] `docs/ARCHITECTURE.md` — row/narrative (done in the original delivery, §7 above)
- [x] `docs/PLATFORM_CAPABILITY_VISION.md` — placement line current (original delivery)
- [x] `docs/IMPLEMENTATION_TASKS.md` — A5 state (original delivery)
- [x] `src/jarvis/intelligence/README.md` — aliases/maps/CLI/namespace honesty (original delivery)
- [x] `docs/ONTOLOGY_CROSSWALKS.md` — header note (original delivery)
- [x] `docs/system_map/CONNECTIONS.md` — `C-114` added, explicit non-edges documented
- [x] `docs/system_map/00_entry/ENTRY_MAP.md` — `explain` documented beside `board`
- [x] `docs/system_map/jarvis-system-map.canvas.tsx` — node/edge/Callout added
- [x] `docs/system_map/DIAGRAMS.md` — count + bullet synced
- [x] `docs/system_map/JARVIS_SYSTEM_MAP.md` — count + paragraph synced
- [x] Report (this file) amended to list every doc path touched (this §7b/§8)

---

## 9. Stop conditions honored (IC §6)

- No A4 voice/`world/` work — untouched.
- No RAG/embeddings — `ids_for_rung`/alias lookup are `dict.get`/exact-match only.
- No Continuity auto-cite wiring — `explain_maps.py`/`explain.py` still never import `jarvis.core` or construct `JarvisOrchestrator` (AST-enforced, T6).
- **No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 10. Non-edits / git-state verification

```text
$ git status --short
 M .jes/state/engineering_state.json
 M docs/ARCHITECTURE.md
 M docs/IMPLEMENTATION_TASKS.md
 M docs/ONTOLOGY_CROSSWALKS.md
 M docs/PLATFORM_CAPABILITY_VISION.md
 M ontology/.obsidian/workspace.json
 M pyproject.toml
 M src/jarvis/adapters/cli/main.py
 M src/jarvis/intelligence/README.md
 M src/jarvis/intelligence/explain.py
 M src/jarvis/intelligence/explain_aliases.py
 M src/jarvis/intelligence/ontology_retrieve.py
?? src/jarvis/intelligence/explain_maps.py
?? tests/test_explain_maps_expand_b1.py
```

`.jes/state/engineering_state.json` and `ontology/.obsidian/workspace.json` were **already modified in the working tree before this Buy started** — same pre-existing local state noted in every prior report in this series, unrelated to this IC, not written by this implementation.

```text
$ git diff --stat -- ontology/ | grep -v obsidian
(empty — zero diff on every vault note; only ontology/.obsidian/workspace.json, pre-existing Obsidian UI state, shows in the raw diff)
```

```text
$ git diff --stat -- docs/ pyproject.toml src/jarvis/intelligence/ src/jarvis/adapters/cli/main.py
 docs/ARCHITECTURE.md                         |  2 +-
 docs/IMPLEMENTATION_TASKS.md                 |  4 +-
 docs/ONTOLOGY_CROSSWALKS.md                  |  2 +-
 docs/PLATFORM_CAPABILITY_VISION.md           |  2 +-
 pyproject.toml                               |  2 +-
 src/jarvis/adapters/cli/main.py              | 32 +++++++++++--
 src/jarvis/intelligence/README.md            | 69 +++++++++++++++++++++++-----
 src/jarvis/intelligence/explain.py           | 52 +++++++++++++++++++--
 src/jarvis/intelligence/explain_aliases.py   | 53 ++++++++++++++++++---
 src/jarvis/intelligence/ontology_retrieve.py | 13 ++++++
```

`library/`, `jarvis.core`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm` — zero diff, confirmed untouched.

```text
$ git tag -l | sort -V | tail -1
v0.6.3

$ grep -m1 '^version' pyproject.toml
version = "0.6.4"
```

Tag remains **`v0.6.3`** — package bumped to `0.6.4` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.4`.

### 10b. Remediation git-state (2026-09-28, §7b/§8 pass)

```text
$ git status --short
 M .jes/artifacts/implementation_contract_explain_maps_expand_b1.md   (Cursor's own IC amend, not Claude)
 M .jes/state/engineering_state.json                                  (pre-existing, unrelated)
 M docs/ARCHITECTURE.md
 M docs/IMPLEMENTATION_TASKS.md
 M docs/ONTOLOGY_CROSSWALKS.md
 M docs/PLATFORM_CAPABILITY_VISION.md
 M docs/USER_GUIDE_CRAFT_MONTAGE.md
 M docs/system_map/00_entry/ENTRY_MAP.md
 M docs/system_map/CONNECTIONS.md
 M docs/system_map/DIAGRAMS.md
 M docs/system_map/JARVIS_SYSTEM_MAP.md
 M docs/system_map/jarvis-system-map.canvas.tsx
 M ontology/.obsidian/workspace.json                                  (pre-existing, unrelated)
 M pyproject.toml                                                     (unchanged since original delivery — still 0.6.4)
 M src/jarvis/adapters/cli/main.py                                    (unchanged since original delivery)
 M src/jarvis/intelligence/README.md                                  (unchanged since original delivery)
 M src/jarvis/intelligence/explain.py                                 (unchanged since original delivery)
 M src/jarvis/intelligence/explain_aliases.py                         (unchanged since original delivery)
 M src/jarvis/intelligence/ontology_retrieve.py                       (unchanged since original delivery)
?? .jes/artifacts/implementation_report_explain_maps_expand_b1.md     (this file — Claude, original delivery)
?? .jes/artifacts/implementation_review_explain_maps_expand_b1.md     (Cursor's own review, not Claude)
?? docs/USER_GUIDE_EXPLAIN.md                                         (this remediation — Claude)
?? src/jarvis/intelligence/explain_maps.py                            (unchanged since original delivery)
?? tests/test_explain_maps_expand_b1.py                               (unchanged since original delivery)

$ git diff --stat -- src/ tests/
(byte-identical to the §1/§10 diff already reported above — zero new lines added by this remediation)
```

`.jes/artifacts/implementation_contract_explain_maps_expand_b1.md` (Cursor's own §8-amendment + HOLD status note) and `.jes/artifacts/implementation_review_explain_maps_expand_b1.md` (Cursor's own review, new file) were **not written by Claude** — both are Cursor's review-process artifacts, present in the working tree before this remediation turn began.

Confirms the remediation instruction's own condition — "No code behavior change required unless docs reveal a naming mismatch" — was honored: no naming mismatch was found, so `src/`/`tests/` stayed exactly as the original delivery left them. Tag still `v0.6.3`, `pyproject.toml` still `0.6.4`. **No ACCEPT claimed by Claude.**
