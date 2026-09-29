# Implementation Report — Continuity explain topics expand (`B1-continuity-explain-topics-expand`)

**Project:** Jarvis
**Date:** 2026-09-29
**Implementer:** Claude Code
**Contract:** [`implementation_contract_continuity_explain_topics_expand_b1.md`](implementation_contract_continuity_explain_topics_expand_b1.md)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.7` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.7` is reserved for Engineer ACCEPT per IC §0 row 8 / §5.

**Note on scope isolation:** A7 (`B1-chat-explain-intercept`) is ★ ACCEPT CLOSED but its own commit had not yet landed when this Buy started — its changes were already present, uncommitted, in the working tree (confirmed via `implementation_review_chat_explain_intercept_b1.md`, verdict **★ ACCEPT CLOSED**). `git diff` against the last commit therefore mixes A7's and A8's changes. §1 below lists only what **this Buy** actually touched.

---

## 1. Files changed (this Buy only)

**New:**
- `tests/test_continuity_explain_topics_expand_b1.py` — T1–T5 (+2 supporting checks)

**Modified:**
- `src/jarvis/core/project_continuity.py` — `_explain_topics_for_continuity` gained `op_current_present: bool`; one new `if op_current_present: topics.append(_EXPLAIN_TOPIC_CURRENT)` line; the call site computes it from `current_parameters["motor_op_current_a"] is not None`
- `pyproject.toml` — `version = "0.6.6"` → `version = "0.6.7"`
- `tests/test_chat_explain_intercept_b1.py` — its own version-checkpoint test bumped `0.6.6` → `0.6.7` per IC §4's explicit instruction ("Also bump/fix any stale `0.6.6` version checkpoint in the A7 test file")
- `src/jarvis/intelligence/README.md` — new "Topics expand (A8)" section; "Continuity cite seam" and "Chat intercept" section headers updated to note ACCEPT-closed status / all-five-topics-active; Tip parent and Tests sections updated
- `docs/USER_GUIDE_EXPLAIN.md` — §7 title updated, new paragraph with a live-verified `current`/`corriente-y-circuitos` example
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD line, A8 cola row, and the COLA header's package/status note updated
- `docs/system_map/08_continuity/CONTINUITY_MAP.md` — `explain_topics` description extended with A8's `current` tagging rule
- `docs/system_map/CONNECTIONS.md` — **C-115 extended** (registry row + full Detail entry, including a new "A8 addendum" to the existing "Non-edges" paragraph) — no new `C-xxx`, per the IC's own preference for extending over minting

**Not touched by this Buy:** `src/jarvis/intelligence/continuity_cite.py` (the IC's own §3 table allowed a docstring-only change here "unless the map is missing `current`" — it already had the row from R3, so this Buy left the file untouched entirely), `explain.py`/`explain_aliases.py`/`explain_maps.py`/`ontology_retrieve.py`, `orchestrator.py`/`config.py` (A7's own files), `ENTRY_MAP.md`/`RUNTIME_MAP.md`/`DIAGRAMS.md`/`JARVIS_SYSTEM_MAP.md`/`jarvis-system-map.canvas.tsx` (not listed in this IC's own §0 row 9 docs table — A7's own docs sync, not re-touched here), `ontology/` (confirmed zero diff below), `library/`.

---

## 2. Signal wiring (IC §0 rows 2–3, §1)

Confirmed the exact field shape before writing any code: `_motor_op_electrical_from_params` (`orchestrator.py:144`) already reads `params.get("motor_op_current_a")` from `project_state.current_parameters` — the same dict the IC's own signal spec names. `_explain_topics_for_continuity` gained one new kwarg and one new unconditional check, appended after every existing rule so topic order stays stable:

```python
def _explain_topics_for_continuity(
    *,
    motor_catalog_gap: str | None,
    underspec_live: bool,
    energy_model_note: str | None,
    autonomy_target_min: float | None,
    watts_recovery_active: bool,
    op_current_present: bool,
) -> list[str]:
    ...
    if op_current_present:
        topics.append(_EXPLAIN_TOPIC_CURRENT)
    return topics
```

Call site (unchanged position — last statement before `build_project_continuity`'s return, exactly where R3 left it):

```python
explain_topics = _explain_topics_for_continuity(
    motor_catalog_gap=motor_catalog_gap,
    underspec_live=_underspec_live,
    energy_model_note=energy_model_note,
    autonomy_target_min=req.get("autonomy_target_min"),
    watts_recovery_active=_watts_recovery_next_step(project_state) is not None,
    op_current_present=(
        (getattr(project_state, "current_parameters", None) or {}).get(
            "motor_op_current_a"
        )
        is not None
    ),
)
```

**Live verification before writing tests:**

```text
motor_op_current_a=12.5  -> explain_topics = ['current']
motor_op_current_a absent -> explain_topics = []
motor_op_current_a=None (key present, null)  -> 'current' not tagged
energy_model_note set alone -> ['c_rate', 'operating_point'], no 'current'
motor_catalog_gap set alone -> ['motor'], no 'current'
```

The last two confirm the IC's own "Forbidden" rule (§1): `current` is never tagged from watts-recovery or a generic energy/catalog gap alone.

---

## 3. Ranking regression (IC §0 row 6)

Reused the exact R3 golden fixture (`motor_catalog_gap` set) and re-asserted its `next_useful_step`/`next_useful_why` byte-for-byte — both matched exactly, and `explain_topics == ["motor"]` (unaffected by the new kwarg's default absence of the `current` signal in that fixture). Full pre-existing `tests/test_project_continuity.py` (18 tests) and `tests/test_continuity_explain_cite_r3_b1.py` (9 tests, R3) both re-run: all pass unchanged.

---

## 4. Tests

`tests/test_continuity_explain_topics_expand_b1.py` — 7 tests, all green:

| ID | Assert | Result |
|---|---|---|
| T1 | `op_current_present` fixture (`motor_op_current_a=12.5`) → `"current"` in `explain_topics`; `cites_for_topics` resolves it to solid `corriente-y-circuitos` | PASS |
| T2 | Absent field, and explicit `None` value → `"current"` never tagged; neutral fixture → `explain_topics == []` | PASS |
| T2b | Generic `energy_model_note` fixture and `motor_catalog_gap` fixture, neither exercising `motor_op_current_a` → `current` never tagged in either (IC's own "Forbidden" rule) | PASS |
| T3 | R3 golden fixture — `next_useful_step`/`next_useful_why` byte-identical; `explain_topics == ["motor"]` | PASS |
| T4 | `project_continuity.py` never imports `jarvis.intelligence`; `continuity_cite.py` never imports `jarvis.core` (AST, both fences) | PASS |
| T5 | `cites_for_topics(["current"])` returns one cite, id `corriente-y-circuitos`, non-empty `definicion` | PASS |
| — | `pyproject.toml` reads `version = "0.6.7"` | PASS |

```text
$ python -m pytest tests/test_continuity_explain_topics_expand_b1.py -v
...
7 passed in 0.11s
```

---

## 5. Full suite

```text
$ python -m pytest -q
54 failed, 3760 passed, 9 skipped in 7.58s
```

Before this Buy (parent package `0.6.6`), the suite had 54 failures (53 pre-existing + A6's own `test_pyproject_version_is_0_6_5`, freshly stale from A7's bump). This Buy: fixed A7's own stale `test_pyproject_version_is_0_6_6` forward to `0.6.7` per IC §4's explicit instruction (−1 failure), and R3's own `test_pyproject_version_is_0_6_5` is already counted in that 54. Net effect on the failure count: zero (one fixed forward, none newly broken) — **54 failed, unchanged**, +7 passed (the new test file). Confirmed zero unexpected failures via `grep FAILED | grep -v <version-checkpoint pattern>` returning empty, both before and after the docs-only pass.

---

## 6. Docs sync (IC §0 row 9) — every path touched

| Doc | Change |
|---|---|
| `docs/USER_GUIDE_EXPLAIN.md` §7 | Title updated ("R3, extendido por A8"); new paragraph with a live-verified `current`/`corriente-y-circuitos` Conceptos example |
| `src/jarvis/intelligence/README.md` | New "Topics expand (A8)" section; "Continuity cite seam"/"Chat intercept" headers corrected (ACCEPT-closed status, all-five-topics-active); Tip parent + Tests sections updated |
| `docs/system_map/08_continuity/CONTINUITY_MAP.md` | `explain_topics` description extended with the A8 tagging rule and its "forbidden" scope |
| `docs/system_map/CONNECTIONS.md` | **C-115 extended** — registry row + Detail entry's Mechanism/Payload/Status/Evidence fields updated, plus a new "A8 addendum" to the Non-edges paragraph naming the forbidden-tagging guarantee |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD line, A8 cola row, COLA header package/status note — all updated to "delivered, awaiting review" |

All are pointer-level or small-section edits, no rewrite epics — same discipline as every prior report in this series.

---

## 7. Acceptance criteria (IC §5) — self-check

- [x] `current` tagged only on `motor_op_current_a` present (T1/T2/T2b)
- [x] Ranking / step-why regression held (T3, byte-identical golden strings)
- [x] Fences AST held (T4)
- [x] Tests T1–T5 · report · docs · package `0.6.7`
- [ ] Cursor review PASS · Engineer ACCEPT · tag `v0.6.7` — **pending**, not claimed by Claude

---

## 8. Explicitly out (IC §2) — honored

- No new Continuity ranking branches or `next_useful_why` codes — `situation`/`next_step`/`next_why` logic has zero diff; only the post-ranking topic-tag helper changed.
- No new ontology notes / vault edits — confirmed zero diff on `ontology/` below.
- No new `CONTINUITY_TOPIC_MAP` keys — `continuity_cite.py` itself has zero diff from this Buy.
- No `explain_maps`/`--rung` expansion, no bare-id chat steal, no A7 behavior change (beyond the one explicitly-requested version-checkpoint test fix).

**No ACCEPT claimed.** This report is for Cursor review; tag creation is Engineer's decision after ★ ACCEPT.

---

## 9. Non-edits / git-state verification

```text
$ git diff --stat -- ontology/
 ontology/.obsidian/workspace.json | 47 ++++++++++++++++++++++-----------------
 1 file changed, 27 insertions(+), 20 deletions(-)
```

Zero diff on every actual vault note (the `.obsidian/workspace.json` diff is the same pre-existing, unrelated local Obsidian UI state noted in every prior report in this series).

```text
$ git diff --stat -- src/jarvis/intelligence/continuity_cite.py
(no output beyond what A7 already changed there — this Buy added zero lines to this file)
```

```text
$ git tag -l | sort -V | tail -1
v0.6.5

$ grep -m1 '^version' pyproject.toml
version = "0.6.7"
```

Tag remains **`v0.6.5`** (A7's own tag has not yet been cut, per the "git tag when commit lands" note on this IC's own parent line) — package bumped to `0.6.7` in `pyproject.toml` only, no tag created by this Buy. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision on ★ ACCEPT + tag `v0.6.7`.
