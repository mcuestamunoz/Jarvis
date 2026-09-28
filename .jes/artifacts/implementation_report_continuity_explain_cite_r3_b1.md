# Implementation Report — Continuity explain cite R3 (`B1-continuity-explain-cite-r3`)

**Project:** Jarvis
**Date:** 2026-09-28
**Implementer:** Claude Code
**Contract:** [`implementation_contract_continuity_explain_cite_r3_b1.md`](implementation_contract_continuity_explain_cite_r3_b1.md)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.5` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.5` is reserved for Engineer ACCEPT per IC §0 row 9 / §5.

---

## 1. Files changed

**New:**
- `src/jarvis/intelligence/continuity_cite.py` — `CONTINUITY_TOPIC_MAP`, `cites_for_topics`, `format_continuity_cite_lines`
- `tests/test_continuity_explain_cite_r3_b1.py` — T1–T6 (+3 supporting checks)

**Modified:**
- `src/jarvis/core/project_continuity.py` — added `_explain_topics_for_continuity(...)` (pure helper) and one new call site at the very end of `build_project_continuity`, adding `explain_topics` to the return dict
- `src/jarvis/adapters/cli/main.py` — added `_render_concept_lines(topics)`; wired into both `render_startup_context`'s Continuity block and `render_response`'s coherence footer
- `pyproject.toml` — `version = "0.6.4"` → `version = "0.6.5"`
- `src/jarvis/intelligence/README.md` — new "Continuity cite seam (A6/R3)" section; Buys/Package header, Tip parent, Tests sections updated
- `docs/USER_GUIDE_EXPLAIN.md` — new §7 "Conceptos en `estado`/Continuity" (real, verified CLI output); renumbered old §7→§8, added a Conceptos-specific bullet to Límites conocidos
- `docs/USER_GUIDE_CRAFT_MONTAGE.md` — one-line pointer added after the existing `jarvis explain` pointer
- `docs/ARCHITECTURE.md` §1, `docs/PLATFORM_CAPABILITY_VISION.md` §12, `docs/IMPLEMENTATION_TASKS.md` — A6/R3 state updated (delivered, awaiting review)
- `docs/JARVIS_KNOWLEDGE_VISION.md` §7 — branch (a) marked DONE, branch (b) R3 status updated to delivered
- `docs/system_map/CONNECTIONS.md` — `C-115` added (registry table + chronology entry + full Detail entry under `08 Continuity`, with an explicit "Non-edges" paragraph); also corrected a stale "pending Engineer ★ ACCEPT" note on the C-114 chronology entry (A5 has since landed)
- `docs/system_map/08_continuity/CONTINUITY_MAP.md` — `build_project_continuity`'s signature/description updated to include `explain_topics`
- `docs/system_map/00_entry/ENTRY_MAP.md` — new Key-modules row, Inbound/Outbound line extended, Local-state/Tests lines added
- `docs/system_map/DIAGRAMS.md`, `docs/system_map/JARVIS_SYSTEM_MAP.md`, `docs/system_map/jarvis-system-map.canvas.tsx` — `C-115` mirrored (counts, chronology paragraph, live data-array edge, node reuse, dated header log line, new "Shipped" Callout); also corrected the same stale A5 "awaiting ACCEPT" wording found in the canvas's own explain-canal Callout while touching that block

**Not touched:** `ontology/` (still read-only; confirmed zero diff on any vault note below), `library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm`, `ontology_retrieve.py`/`explain.py`/`explain_aliases.py`/`explain_maps.py` (A2–A5 modules, unchanged), `test_project_continuity.py` (unchanged, re-run as regression proof).

---

## 2. Topic tagging design (IC §2)

`_explain_topics_for_continuity(...)` is a small, pure function added to `project_continuity.py`, called as the **last statement before the return dict** in `build_project_continuity` — after `situation`, `evidence`, `next_step`, and `next_why` are all finalized:

```python
explain_topics = _explain_topics_for_continuity(
    motor_catalog_gap=motor_catalog_gap,
    underspec_live=_underspec_live,
    energy_model_note=energy_model_note,
    autonomy_target_min=req.get("autonomy_target_min"),
    watts_recovery_active=_watts_recovery_next_step(project_state) is not None,
)
```

Mapping from the IC §2 seed table to the actual signals used:

| IC §2 row | Signal(s) used | Topic(s) |
|---|---|---|
| "`motor_catalog_gap` set / catalog underspec / motor ranking branch" | `motor_catalog_gap is not None` (function param) or `_underspec_live` (already computed at the top of `build_project_continuity`, lines ~292–303) | `motor` |
| "Autonomy / energy / battery language in next_step or energy_model_note path" | `req.get("autonomy_target_min") is not None` or `energy_model_note` truthy | `c_rate`, `operating_point` |
| "Thrust / hover / OP / nameplate watts recovery path" | `_watts_recovery_next_step(project_state) is not None` | `operating_point` (if not already present), `thrust_stand` |
| "Electrical / current-related gap copy if already distinguished" | **Not tagged.** No existing Continuity signal in this codebase distinguishes a current-specific gap from the general catalog/energy gaps today — the IC's own wording gates this row on "if already distinguished," and it isn't. Documented in a code comment; a future Buy can add it once such a signal exists rather than guessing one now. | (none) |

**Design note on `_watts_recovery_next_step`:** this function is already called once inside the ranking `elif` chain (only reached if every higher-ranked branch misses — line ~563, `_wr := _watts_recovery_next_step(project_state)`). Calling it a second time, unconditionally, at the end for tagging purposes means it now always evaluates (previously lazy). It is a pure, read-only query (no I/O, no mutation — same class as the rest of `project_continuity.py`), so this is a computation-cost tradeoff only, never a correctness or ranking change; noted explicitly here per the "smallest safe scope" principle rather than silently accepted.

---

## 3. Regression proof (IC §0 row 2, §4 T2)

Before touching `project_continuity.py`, I ran two existing fixture shapes (reused from `tests/test_project_continuity.py`'s `test_continuity_catalog_gap_beats_optimization_suggestion` and `test_situation_thrust_feasibility_only_when_autonomy_unmet`) through the **pre-edit** code and captured the exact `next_useful_step`/`next_useful_why`/`situation` strings as golden values. After implementing, I re-ran the same fixtures and asserted byte-for-byte equality — both matched exactly. These golden assertions are now permanent regression tests in `tests/test_continuity_explain_cite_r3_b1.py` (`test_t2_...`/`test_t2b_...`).

The full pre-existing `tests/test_project_continuity.py` suite (18 tests, unmodified) was also re-run and passes unchanged — no test in that file needed updating, confirming `explain_topics` is purely additive to the return dict.

---

## 4. CLI render (IC §3)

Added `_render_concept_lines(topics)` to `adapters/cli/main.py` — resolves via `jarvis.intelligence.continuity_cite` (local import inside the function, matching the existing `board`/`explain` local-import pattern) and returns `[]` silently on no topics or no resolved cites. Wired into both places the IC named:

1. `render_startup_context`'s Continuity block (right after "Por qué", before the closing separator).
2. `render_response`'s coherence footer (right after "Por qué", before `return`).

Verified against the real code (not hand-typed) using the motor-catalog-gap fixture:

```text
Siguiente paso: Declara empuje real por motor (≥ 4.8 N) o elige una pieza fuera de catálogo; Jarvis no inventará un SKU.
   Por qué: Necesitas empuje ≥ 4.8 N/motor; no tengo motor en catálogo. Di 'qué motores tenemos' para ver el catálogo, o 'explora opciones' para que Jarvis pruebe configuraciones alternativas.
Conceptos (ontology):
  - motores  →  jarvis explain motores
  - motor-dc  →  jarvis explain motor-dc
```

No `[DEFINICION]`/`[INTUICION]` body anywhere in this output — only `id` + the exact `jarvis explain <id>` command, per IC §0 row 6.

---

## 5. Tests

`tests/test_continuity_explain_cite_r3_b1.py` — 9 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | Topic `c_rate` resolves to cite id `c-rate-de-bateria` with non-empty `definicion` | PASS |
| T2 | Motor-catalog-gap fixture tags `["motor"]`; `next_useful_step`/`next_useful_why` byte-identical to golden pre-Buy strings | PASS |
| T2b | Autonomy-target fixture tags `["c_rate", "operating_point"]`; `next_useful_step`/`next_useful_why`/`situation` byte-identical to golden pre-Buy strings | PASS |
| T2c | Fixture with no matching signal → `explain_topics == []` | PASS |
| T3 | `project_continuity.py` never imports `jarvis.intelligence` (AST) | PASS |
| T4 | `continuity_cite.py` never imports `jarvis.core`, never calls `submit_command`/mentions `JarvisOrchestrator` | PASS |
| T5 | `_render_concept_lines(["c_rate"])`, the thin formatter, and the full `render_startup_context` path all mention `c-rate-de-bateria` and `jarvis explain` | PASS |
| T6 | Unknown topic never crashes; resolves to no cite; mixed known/unknown topics still resolve the known one | PASS |
| — | `pyproject.toml` reads `version = "0.6.5"` | PASS |

```text
$ python -m pytest tests/test_continuity_explain_cite_r3_b1.py -v
...
9 passed in 0.21s
```

**T3 design note:** an initial draft of T3 additionally asserted `"ontology" not in source.lower()` as a raw text check. This would have false-failed against my own honesty-lock docstring (which *names* `ontology/` specifically to document that the module never reads it) — the exact same pitfall caught and fixed in the A1 Buy's own test suite. Removed the substring check; kept the AST import check, which is the real mechanism-level guarantee.

`tests/test_project_continuity.py` (18 tests, pre-existing, unmodified) re-run: **all pass, unchanged.**

---

## 6. Full suite

```text
$ python -m pytest -q
53 failed, 3747 passed, 9 skipped in 10.34s
```

Before this Buy (parent tip `v0.6.4`), the suite had 52 pre-existing version-pinned checkpoint failures (documented across every prior report in this series). This Buy adds exactly one more of the same kind (A5's own `test_pyproject_version_is_0_6_4`, now stale at this Buy's `0.6.5` bump). Net: 9 new tests added (all pass), 1 additional stale checkpoint (expected, same established convention), zero new behavioral failures, zero tests weakened or deleted. The full suite run was repeated after the docs-only pass (§8) and produced the identical 53/3747/9 split, confirming the docs edits caused zero code regressions.

---

## 7. Docs sync (IC §8) — every path touched

| Doc | Change |
|---|---|
| `docs/USER_GUIDE_EXPLAIN.md` | New §7 "Conceptos en `estado` / Continuity" — real, CLI-verified example; old §7 Límites renumbered to §8, one new bullet added there |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` | One-line pointer under the existing `jarvis explain` pointer |
| `docs/ARCHITECTURE.md` §1 | `intelligence/` knowledge-tree row: A6/R3 delivered @ package `0.6.5` |
| `docs/PLATFORM_CAPABILITY_VISION.md` §12 | Placement line: A6/R3 delivered, pending ACCEPT before tag |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD line + A6 cola row: delivered, awaiting review |
| `src/jarvis/intelligence/README.md` | New "Continuity cite seam (A6/R3)" section (fence explicitly stated); Buys/Package/Tip-parent/Tests sections updated |
| `docs/JARVIS_KNOWLEDGE_VISION.md` §7 | Branch (a) marked DONE (A0–A5 closed); branch (b) R3 status updated to delivered, R4 still "Later" |
| `docs/system_map/CONNECTIONS.md` | `C-115` added to the registry table, a full Detail entry under `08 Continuity` with an explicit "Non-edges" paragraph (Continuity ↛ vault decide), and a chronology entry; counts bumped consistently (67→68 total, 66→67 "unique edges", 65→66 connected) |
| `docs/system_map/08_continuity/CONTINUITY_MAP.md` | `build_project_continuity`'s signature/description line updated with `explain_topics` and the R3 fence explanation |
| `docs/system_map/00_entry/ENTRY_MAP.md` | New Key-modules row for the Conceptos seam, Inbound/Outbound line extended with C-115, Local-state and Tests lines added |
| `docs/system_map/jarvis-system-map.canvas.tsx` | `C-115` added to the live `CONNECTIONS` data array (participates in the interactive DAG), header count/log updated, new "Shipped" Callout |
| `docs/system_map/DIAGRAMS.md` | Canonical-count line, "Counts" table, and a new dated bullet, all updated |
| `docs/system_map/JARVIS_SYSTEM_MAP.md` | New dated paragraph + registry pointer count bumped |

All are pointer-level or small-section edits — no rewrite epics, matching every prior report's own discipline in this series.

---

## 8. Acceptance criteria (IC §5) — self-check

- [x] Topic map + `cites_for_topics`
- [x] Continuity emits `explain_topics` without vault I/O / without importing intelligence (AST-enforced, T3)
- [x] Ranking / `next_useful_step` regression held (byte-identical golden strings, T2/T2b)
- [x] CLI Conceptos block (both `render_startup_context` and coherence footer)
- [x] Tests T1–T6 green
- [x] §8 docs sync — every path listed above
- [x] `pyproject.toml` = `0.6.5`; tag `v0.6.5` **not created** — reserved for Engineer ACCEPT

---

## 9. Stop conditions honored (IC §6)

- Continuity does not read `ontology/` to pick the next craft step — it only emits a finite tag list, computed after the step is already chosen.
- No full note body (`[DEFINICION]`/`[INTUICION]`) dumped into `estado` anywhere — only `id` + `jarvis explain <id>`.
- No R4 LLM cite, no A4 voice — untouched.
- **No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 10. Non-edits / git-state verification

```text
$ git status --short
 M .jes/state/engineering_state.json
 M docs/ARCHITECTURE.md
 M docs/IMPLEMENTATION_TASKS.md
 M docs/JARVIS_KNOWLEDGE_VISION.md
 M docs/PLATFORM_CAPABILITY_VISION.md
 M docs/USER_GUIDE_CRAFT_MONTAGE.md
 M docs/USER_GUIDE_EXPLAIN.md
 M docs/system_map/00_entry/ENTRY_MAP.md
 M docs/system_map/08_continuity/CONTINUITY_MAP.md
 M docs/system_map/CONNECTIONS.md
 M docs/system_map/DIAGRAMS.md
 M docs/system_map/JARVIS_SYSTEM_MAP.md
 M docs/system_map/jarvis-system-map.canvas.tsx
 M ontology/.obsidian/workspace.json
 M pyproject.toml
 M src/jarvis/adapters/cli/main.py
 M src/jarvis/core/project_continuity.py
 M src/jarvis/intelligence/README.md
?? src/jarvis/intelligence/continuity_cite.py
?? tests/test_continuity_explain_cite_r3_b1.py
```

`.jes/state/engineering_state.json` and `ontology/.obsidian/workspace.json` were **already modified in the working tree before this Buy started** — same pre-existing local state noted in every prior report in this series, unrelated to this IC, not written by this implementation.

```text
$ git diff --stat -- ontology/
 ontology/.obsidian/workspace.json | 47 ++++++++++++++++++++++-----------------
 1 file changed, 27 insertions(+), 20 deletions(-)
```

Zero diff on every actual vault note — confirmed the "no vault read" lock held in practice, not just in the AST test.

```text
$ git diff --stat -- src/
 src/jarvis/adapters/cli/main.py                 | 31 ++++++++++++
 src/jarvis/core/project_continuity.py           | 64 +++++++++++++++++++++++++
 src/jarvis/intelligence/README.md               | 51 ++++++++++++++++++--
```

`library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`, `jarvis.llm`, `ontology_retrieve.py`/`explain.py`/`explain_aliases.py`/`explain_maps.py` — zero diff, confirmed untouched.

```text
$ git tag -l | sort -V | tail -1
v0.6.4

$ grep -m1 '^version' pyproject.toml
version = "0.6.5"
```

Tag remains **`v0.6.4`** — package bumped to `0.6.5` in `pyproject.toml` only, no tag created. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.5`.
