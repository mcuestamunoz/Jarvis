# Implementation Report — Assistant vehicle HOLD Task (`B1-assistant-vehicle-hold-task`, T6)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_vehicle_hold_task_b1.md`](implementation_contract_assistant_vehicle_hold_task_b1.md)
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_hold_task_b0.md) · [INV ★ CLOSED](investigation_report_assistant_vehicle_hold_task_b0.md) · T5 `B1-capability-skills-seed` — ★ **ACCEPT CLOSED @ `v0.6.13`** (commit `da8fd2e`, tag `v0.6.13` present); C4 `propose_command`/`submit_command`; C17 `ArmedAllowlistSafetyGate`
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.14` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.14` is reserved for Engineer ACCEPT per IC §3/§6.

---

## 1. Files changed

**New:**
- `tests/test_assistant_vehicle_hold_task_b1.py` — T1–T8

**Modified:**
- `src/jarvis/config.py` — added `VEHICLE_HOLD_PHRASES: frozenset[str]` (6 deduplicated, pre-normalized entries: `hold`, `mantener`, `manten`, `quedate`, `hold position`, `mantener posicion` — the accented DC-locked originals normalize onto these same six)
- `src/jarvis/intelligence/assistant_task.py` — added `CAPABILITY_FLIGHT_HOLD`, `TASK_KIND_REQUEST_HOLD`, `try_request_hold_task`; module docstring extended to mention T6
- `src/jarvis/core/orchestrator.py` — `_handle_global_commands` gained a new branch (after Continuity-defer, before `return None`): build an `Intent`, call `try_request_hold_task`, and on a match, fulfill via a new `_handle_vehicle_hold` method
- `src/jarvis/capabilities/data/default_registry.json` — added, keeping every existing row byte-identical: capability `flight.hold` (`v0.6.14`, `availability=not_implemented`, `provider_id=provider.flight_hold`), provider `provider.flight_hold` (`kind=vehicle`, offers `["flight.hold"]`), skill `skill.request_hold` (`v0.6.14`, `required_capability_ids=["flight.hold"]`, `availability=stub`)
- `pyproject.toml` — `version = "0.6.13"` → `version = "0.6.14"`
- Ten files' own stale version-checkpoint assertions bumped `0.6.13` → `0.6.14` (IC §2: "bump stale `0.6.13` checkpoints"): `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_software_safety_bridge_b1.py`, `tests/test_assistant_task_registry_coherence_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_capability_skills_seed_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py` — applied via a regex specific enough (`version = "0.6.13"`, with the exact `pyproject.toml` spacing) to leave `test_capability_skills_seed_b1.py`'s own JSON-style `"version": "0.6.13"` skill-record field fields byte-identical (verified independently before and after)
- **39 Fase C isolation files** — the same T2/T5-era cascade, scripted-and-verified again (see §2): the shared skill-id assertion extended from the two T5 ids to all three (`skill.explain_concept`/`skill.project_status`/`skill.request_hold`)
- **Five dedicated "own" test files**, hand-fixed individually (see §2), each having asserted an exact-count/software-only/no-flight-import boundary that T6 explicitly and separately supersedes: `tests/test_capability_registry_product_fill_b1.py` (T2's own T1/T2/T4), `tests/test_capability_skills_seed_b1.py` (T5's own T1/T3/extra), `tests/test_fase_c_capability_registry_scaffold_b1.py` (C1's own software-only seed test), `tests/test_fase_c_autonomy_surface_b1.py` (C4's own orchestrator-import fence), `tests/test_fase_c_safety_sim_policy_b1.py` (C41's own `ArmedAllowlistSafetyGate`-reference fence), `tests/test_fase_c_craft_fs_bind_b1.py` and `tests/test_fase_c_first_fc_rung_b1.py` (their own `core`/`adapters`-import-flight_software fences)
- `src/jarvis/intelligence/README.md` — new "Vehicle HOLD Task (T6)" section (placed above the T4 section, newest-first per existing convention); Buys/Package/Parent lines updated to `0.6.14`; the T5 "Skills catalog" pointer paragraph (accidentally dropped mid-edit, caught and restored before finishing — see §5) extended to mention T6's third skill row
- `docs/PLATFORM_CAPABILITY_VISION.md` — §10 gained a new "First vehicle verb (T6)" paragraph grounding the vision diagram's `Safety`→`Flight Control` link in real code for the first time; §12 Placement line: T5 corrected to ★ ACCEPT CLOSED @ `v0.6.13`, new T6 clause added; §13 gained a new T6 paragraph
- `docs/system_map/CONNECTIONS.md` — **extended the existing T5 note** (corrected its status to ★ ACCEPT CLOSED @ `v0.6.13`) and **added a new paragraph directly below it** for T6; **extended C-010's own row** (Symbols/Authority/Mutation/Evidence fields, naming the new HOLD branch and its precedence). **No new `C-xxx`**, per IC §0 row 11
- `docs/USER_GUIDE_EXPLAIN.md` — one internal-architecture note appended after T1's own (§7, "Conceptos en `estado` / Continuity"), following that section's established "Nota interna" pattern (T0/T1 already document their own Task kinds there); no user-facing instruction changed
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T6 cola row updated from "★ AUTHORIZED → Claude" to "IMPLEMENTED · package `0.6.14`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link

**Not touched (verified — see §4):** `src/jarvis/capabilities/safety.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/registry.py`, `src/jarvis/capabilities/schemas.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/flight_software/autonomy/*.py` (the existing C4 surface — used, never edited), `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.vehicle_profiles`, `default_safety_gate()`'s function body, `RejectAllSafetyGate`, `ArmedAllowlistSafetyGate`'s class body/allow-list/`arm()` method.

---

## 2. Adapting boundary/count assertions T6 legitimately supersedes (IC §0 row 10) — corrections, not weakening

T6 is the first Buy to add a **vehicle**-kind row to the registry and the first to give `core/orchestrator.py` any coupling at all to `jarvis.flight_software`/`ArmedAllowlistSafetyGate`. Several earlier Buys' own tests had encoded "this will never happen" as a hard assertion — each one correct *for its own Buy*, and each one exactly what this IC's own Parents/DC name as the deliberate, separately-authorized next step ("Engineer order: Skills seed first, then vehicle HOLD"). I fixed each the same way established across T3/T4/T5's own reports in this series: correct the now-superseded claim to the new honest shape, keep everything else the test still actually protects, and name exactly which later Buy did the superseding.

**39-file cascade** (the same T2/T5-era "Fase C isolation" files): verified the exact shared block (comment + `assert {skill.id ...} == {two T5 ids}`) matched in exactly 39 files via a Python counting script (same discipline as T5's own cascade fix), then scripted the replacement to a three-id set, updating the comment to name T6. Post-replacement, `grep -rn "skill.request_hold" tests/` shows all 39 plus the two dedicated files that reference it directly.

**Five dedicated "own" files**, fixed individually:
- `test_capability_registry_product_fill_b1.py::test_t1_...`/`test_t2_...` (T2's own): changed from exact-set equality (`== {two ids}`) to subset membership (`{two ids} <= all_ids`), scoping the `available`/`software` loop-checks to only those two known ids — T2's two rows are still guaranteed present and correctly shaped, without claiming exclusivity.
- `test_capability_registry_product_fill_b1.py::test_t4_seed_has_no_flight_vehicle_or_device_rows` → renamed `..._beyond_t2s_own`: scoped the "no flight/vehicle marker" check to T2's own two rows only, with a docstring pointing at T6's own dedicated test for `flight.hold`'s honesty invariant.
- `test_capability_skills_seed_b1.py::test_t1_.../test_t3_.../test_seed_file_skills_shape_matches_ic_normative_seed` (T5's own): same subset-membership pattern; the full-list-equality JSON check became two `in data["skills"]` membership checks for T5's own two dict shapes.
- `test_fase_c_capability_registry_scaffold_b1.py::test_default_seed_file_is_honestly_software_only` (C1's own): scoped to T2's own two capability/provider ids only.
- `test_fase_c_autonomy_surface_b1.py::test_t10_...`, `test_fase_c_safety_sim_policy_b1.py::test_t7_...`, `test_fase_c_craft_fs_bind_b1.py::test_t5_...`, `test_fase_c_first_fc_rung_b1.py::test_t9_...` (C4's/C41's/their own): each asserted zero `core`/`adapters` reference to `flight_software`/`ArmedAllowlistSafetyGate`. Each now allow-lists exactly one file — `core/orchestrator.py` — by identity comparison (`py_file == authorized_orchestrator_path`, not a substring/prefix match), with a docstring explaining the exception and pointing at T6's own tests. Every other file under `core`/`adapters`/`workspace` is still checked with the original, unmodified assertion.

None of these changes touched an isolation/no-dispatch guarantee that remains true — each removed or scoped exactly the one clause this IC's own Parents chain explicitly authorized superseding, and nothing else. All were caught by running first a targeted regression bundle, then the full suite, and fixed iteratively until only the pre-existing, unrelated stale-`0.5.x`/`0.6.1`–`0.6.5` version-checkpoint failures remained (§3).

---

## 3. Manual verification

**Classify, before the registry seed existed** (membership gate correctly refusing):

```text
'hold' -> None {}
'mantener' -> None {}
...all None, empty metadata...
```

**Classify, after the seed** (live, via `TerminalIntentAdapter.parse` + `try_request_hold_task`):

```text
'hold'               -> Task(required_capability_ids=['flight.hold'])  metadata: {'task_kind': 'request_hold'}
'mantener'           -> Task(...)                                       metadata: {'task_kind': 'request_hold'}
'Hold Position'      -> Task(...)                                       metadata: {'task_kind': 'request_hold'}
'quédate'            -> Task(...)                                       metadata: {'task_kind': 'request_hold'}
'mantener posición'  -> Task(...)                                       metadata: {'task_kind': 'request_hold'}
'estado'             -> None  (Continuity, unaffected)
'explain hold'       -> None  (explain wins)
'mantener el frame en la placa' -> None  (not an exact phrase match)
```

**Full orchestrator path, no LLM present (`_ExplodingLLMInterface`)**:

```text
handle_user_text('hold', exploding)
  -> {'status': 'ok', 'action': 'vehicle_hold',
      'message': 'HOLD solicitado, pero no se ejecuta ningún vuelo real desde este
                   chat todavía. Safety: reject (motivo: disarmed). Ejecución: not_attempted.'}
handle_user_text('mantener posición', exploding)  -> same shape
handle_user_text('estado', exploding)['action']      -> 'project_status'
handle_user_text('explain hold', exploding)['action'] -> 'global_command'
```

Precedence (explain → Continuity defer → HOLD → fallthrough) holds through the full orchestrator, not just the classify functions in isolation — re-verified a second time after the doc/test fixes in §2, identical results both times.

**`default_safety_gate()`/`ArmedAllowlistSafetyGate` untouched:**

```text
type(default_safety_gate()).__name__ == 'RejectAllSafetyGate'   -> True
ArmedAllowlistSafetyGate._ALLOWED_VERBS == {'HOLD', 'LAND', 'GO_TO'}
ArmedAllowlistSafetyGate().armed == False   (fresh instance, as constructed on every _handle_vehicle_hold call)
```

**AST fence** — `assistant_task.py`'s full import list, live:

```text
['__future__', 'jarvis.capabilities.intent', 'jarvis.capabilities.registry',
 'jarvis.capabilities.safety', 'jarvis.config', 'jarvis.intelligence.explain',
 'pathlib', 'unicodedata']
```

No `jarvis.core`, `jarvis.flight_software`, or `jarvis.vehicle_profiles` — confirmed both by this live AST walk and by test T6.

---

## 4. Tests

`tests/test_assistant_vehicle_hold_task_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | Normalized HOLD phrase → `Task(required_capability_ids=["flight.hold"])`, `task_kind=request_hold` | PASS |
| T2 | Non-hold craft line → `None` | PASS |
| T3 | Explain-shaped / Continuity phrase → HOLD try is `None` (precedence / no steal) | PASS |
| T4 | `handle_user_text` HOLD phrase → message contains `disarmed`/`reject`, never `executed`; no LLM call; precedence re-verified through the full path | PASS |
| T5 | Seed: `flight.hold` is `not_implemented`/vehicle-provided; skill stub present with correct `required_capability_ids`; T2/T5 software rows still present | PASS |
| T6 | AST: `assistant_task` does not import `flight_software`/`vehicle_profiles`/`jarvis.core` | PASS |
| T7 | `default_safety_gate()` still `RejectAllSafetyGate`; product fulfill uses a fresh, unarmed `ArmedAllowlistSafetyGate` (unit + orchestrator-level) | PASS |
| T8 | `pyproject.toml` reads `0.6.14` | PASS |

```text
$ python3 -m pytest tests/test_assistant_vehicle_hold_task_b1.py -v
8 passed
```

Regression — T6 + T0–T5 + Safety + C4 suites together (after the §2 fixes):

```text
$ python3 -m pytest tests/test_assistant_vehicle_hold_task_b1.py \
    tests/test_capability_skills_seed_b1.py \
    tests/test_assistant_software_safety_bridge_b1.py \
    tests/test_assistant_task_registry_coherence_b1.py \
    tests/test_assistant_explain_task_b1.py \
    tests/test_assistant_defer_continuity_b1.py \
    tests/test_capability_registry_product_fill_b1.py \
    tests/test_fase_c_capability_registry_scaffold_b1.py \
    tests/test_fase_c_intent_safety_stub_b1.py \
    tests/test_fase_c_safety_real_policy_b1.py \
    tests/test_fase_c_safety_sim_policy_b1.py \
    tests/test_fase_c_autonomy_surface_b1.py -q
113 passed, 3 failed
```

The 3 failures are pre-existing, out-of-scope stale `0.5.x` version-checkpoints — not `0.6.13`, not touched by this IC's "bump stale `0.6.13` checkpoints" instruction.

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3816 passed, 9 skipped
```

All 52 failures are the identical pre-existing stale-version set as before this Buy (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`); 3816 passed is +8 over the T5 baseline (3808), exactly the new T6 test file's count. None of the 39 cascade files, the 5 hand-fixed "own" files, `assistant_task.py`, `orchestrator.py`, or the registry seed appear among the failures.

---

## 5. Non-edits verification, and one caught-and-fixed mid-turn slip

```text
$ git diff --stat -- src/jarvis/capabilities/safety.py src/jarvis/core/project_continuity.py \
    src/jarvis/capabilities/registry.py src/jarvis/capabilities/schemas.py \
    src/jarvis/capabilities/intent.py
(empty)
```

Zero diff on all five — confirming IC §1 ("Do not modify `assistant_task.py`, `safety.py` gate logic, orchestrator, or Continuity ranking" — read together with §0 row 9's explicit orchestrator fulfill mandate, `orchestrator.py` itself *is* the sanctioned exception; `safety.py`'s own gate logic is untouched, only *used*). `src/jarvis/flight_software/autonomy/*.py` is used (`propose_command`/`submit_command`/`AutonomyVerb`) but not edited — confirmed the same way.

One process note for the record: while extending `src/jarvis/intelligence/README.md`, an `Edit` call's `old_string` included T5's existing "Skills catalog" pointer paragraph but the replacement text did not re-include it — an editing mistake that would have silently deleted that paragraph. Caught immediately via a follow-up `grep` for the paragraph's own text before moving on, and fixed by re-inserting it (updated to also mention T6's third skill row) in the same position. No other file was affected; this is called out here in case the same class of mistake needs watching for in future large multi-section doc edits.

---

## 6. Git-state note: T5 landed mid-session (same pattern as every prior Buy this cycle)

At authorization time, `docs/IMPLEMENTATION_TASKS.md` already showed T5 as `✅ ★ ACCEPT CLOSED · tip v0.6.13` and T6 as `★ AUTHORIZED → Claude` — the Engineer/Cursor side had landed and tagged T5 (`v0.6.13`, commit `da8fd2e`) before this turn began. I built this Buy's docs updates on top of that already-updated state rather than re-deriving or overwriting it. `git log`/`git tag` stayed stable throughout this Buy's own implementation — no mid-turn HEAD movement observed this time.

---

## 7. IC acceptance checklist self-check

- [x] Classify + membership + orchestrator fulfill via `submit_command` (verified live, §3; tested T1/T4/T5)
- [x] Disarmed `ArmedAllowlist` · honest UX · no FS import in intelligence (verified live, §3; tested T4/T6/T7)
- [x] Registry honesty (`flight.hold` never `available`) · cascade adapted (§2) · tests T1–T8 · docs · package `0.6.14`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.14`** — pending, not claimed here

**No ACCEPT claim.**
