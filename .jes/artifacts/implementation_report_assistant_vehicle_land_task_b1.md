# Implementation Report — Assistant vehicle LAND Task (`B1-assistant-vehicle-land-task`, T7)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_vehicle_land_task_b1.md`](implementation_contract_assistant_vehicle_land_task_b1.md)
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_land_task_b0.md) · T6 `B1-assistant-vehicle-hold-task` — ★ **ACCEPT CLOSED @ `v0.6.14`** (commit `5feeab4`, tag `v0.6.14` present); HOLD INV ★ CLOSED (seams reused — no new INV per this IC's own Parents)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.15` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.15` is reserved for Engineer ACCEPT per IC §3/§4.

---

## 1. Files changed

**New:**
- `tests/test_assistant_vehicle_land_task_b1.py` — T1–T8

**Modified:**
- `src/jarvis/config.py` — added `VEHICLE_LAND_PHRASES: frozenset[str]` (8 already-accent-free entries: `land`, `aterrizar`, `aterriza`, `aterrizaje`, `baja`, `bajar`, `descend`, `descender`), right after `VEHICLE_HOLD_PHRASES`
- `src/jarvis/intelligence/assistant_task.py` — added `CAPABILITY_FLIGHT_LAND`, `TASK_KIND_REQUEST_LAND`, `try_request_land_task`; module docstring extended to mention T7
- `src/jarvis/core/orchestrator.py` — `_handle_global_commands` gained a new branch (after the HOLD branch, before `return None`): build an `Intent`, call `try_request_land_task`, and on a match, fulfill via a new `_handle_vehicle_land` method — `_handle_vehicle_hold` itself was **not** touched (thin duplication per DC's own "Not" list, see §2)
- `src/jarvis/capabilities/data/default_registry.json` — added, keeping every existing row byte-identical: capability `flight.land` (`v0.6.15`, `availability=not_implemented`, `provider_id=provider.flight_land`), provider `provider.flight_land` (`kind=vehicle`, offers `["flight.land"]`, deliberately **separate** from `provider.flight_hold` per DC §0 row 5), skill `skill.request_land` (`v0.6.15`, `required_capability_ids=["flight.land"]`, `availability=stub`)
- `pyproject.toml` — `version = "0.6.14"` → `version = "0.6.15"`
- Eleven files' own stale version-checkpoint assertions bumped `0.6.14` → `0.6.15` (IC §2: "bump stale `0.6.14` checkpoints that this Buy owns"): `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_software_safety_bridge_b1.py`, `tests/test_assistant_task_registry_coherence_b1.py`, `tests/test_assistant_vehicle_hold_task_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_capability_skills_seed_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py`
- **39 Fase C isolation files** — the same T2/T5/T6-era cascade, scripted-and-verified again (see §2): the shared skill-id assertion extended from three ids to all four (adding `skill.request_land`)
- `src/jarvis/intelligence/README.md` — new "Vehicle LAND Task (T7)" section (placed above the T6 section, newest-first per existing convention); Buys/Package/Parent lines updated to `0.6.15`; the T5 "Skills catalog" pointer paragraph extended to mention T7's fourth skill row; the T6 section's stale "no LAND/GO_TO (separate future Buys)" line corrected to note LAND shipped here
- `docs/PLATFORM_CAPABILITY_VISION.md` — §10 gained a T7 sentence extending the "First vehicle verb" paragraph (same disarmed-gate chain, LAND verb); §12 Placement line: T6 corrected to ★ ACCEPT CLOSED @ `v0.6.14`, new T7 clause added; §13 gained a new T7 paragraph, and the T6 paragraph's stale "LAND/GO_TO... separate later Buys" corrected to note LAND shipped here
- `docs/system_map/CONNECTIONS.md` — **extended the existing T6 note** (corrected its status to ★ ACCEPT CLOSED @ `v0.6.14`) and **added a new paragraph directly below it** for T7; **extended C-010's own row** again (Symbols/Authority/Mutation/Evidence fields, naming the new LAND branch and the four-way precedence). **No new `C-xxx`**, per IC §0 row 12
- `docs/USER_GUIDE_EXPLAIN.md` — one internal-architecture note appended after T6's own (§7), following the same established "Nota interna" pattern; no user-facing instruction changed
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T7 cola row updated from "★ AUTHORIZED → Claude" to "IMPLEMENTED · package `0.6.15`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link

**Not touched (verified — see §4):** `src/jarvis/capabilities/safety.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/registry.py`, `src/jarvis/capabilities/schemas.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/flight_software/autonomy/*.py` (the existing C4 surface — used, never edited), `core/orchestrator.py`'s own `_handle_vehicle_hold` method (thin sibling duplication was used specifically so this method needed zero edits — verified by diffing its body before/after, byte-identical), `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.vehicle_profiles`, `default_safety_gate()`'s function body, `RejectAllSafetyGate`, `ArmedAllowlistSafetyGate`'s class body/allow-list/`arm()` method.

---

## 2. Design choices carried over from HOLD, and the cascade re-adaptation (IC §0 row 11)

**Thin duplication over shared helper (DC §0 row 9 / IC's own "Not" list).** `_handle_vehicle_land` is a near-identical sibling of `_handle_vehicle_hold` (same gate construction, same message shape, verb-swapped) rather than a shared multi-verb helper — the DC explicitly excludes "collapsing HOLD+LAND into a generic verb framework" this Buy, and the safest way to guarantee zero HOLD regression was to leave `_handle_vehicle_hold` completely untouched rather than refactor it into a shared path. Confirmed via `git diff` that `_handle_vehicle_hold`'s own body has zero changes.

**Internal HOLD guard (IC §0 row 10).** `try_request_land_task` refuses explain-shaped, Continuity-defer-shaped, *and* HOLD-shaped input internally — not just relying on the orchestrator's own call order — mirroring the same internal-guard discipline every earlier kind in this module already uses (T1's explain guard, T6's explain+Continuity guard). Verified by test T3: a HOLD phrase fed directly to `try_request_land_task` is refused, while the same phrase fed to `try_request_hold_task` still classifies — proving the guard is LAND-side only and doesn't accidentally weaken HOLD.

**Registry: separate providers, not merged (DC §0 row 5).** `provider.flight_land` is its own row, distinct from `provider.flight_hold`, each offering exactly one capability — verified live and by test T5's explicit id-inequality assertion.

**Cascade re-adaptation.** T6's own cascade fix (39 Fase C isolation files, extended in that Buy from two skill ids to three) needed one more round for T7: verified the exact shared block (comment + `assert {skill.id ...} == {three ids}`) still matched in exactly 39 files via a Python counting script (same discipline as T5/T6), then scripted the replacement to a four-id set. **I initially missed this step** — jumped from wiring the orchestrator straight to writing the new test file and bumping the version, and only caught the gap when a broader regression run (beyond just the new T7 suite) surfaced 8 failures across `test_fase_c_safety_real_policy_b1.py`, `test_fase_c_autonomy_surface_b1.py`, and `test_fase_c_first_fc_rung_b1.py` — all instances of the exact-three-skill assertion T6 had left behind, now legitimately stale. Ran the cascade script immediately after noticing, then re-ran the full suite to confirm only the pre-existing stale-version failures remained. No other boundary/count test needed manual re-fixing this time: the `core/orchestrator.py`-only allow-list exceptions T6 established (in `test_fase_c_autonomy_surface_b1.py`, `test_fase_c_safety_sim_policy_b1.py`, `test_fase_c_craft_fs_bind_b1.py`, `test_fase_c_first_fc_rung_b1.py`) exclude the file by identity, not by verb, so they needed no further change for LAND; the T2/T5-era subset-membership fixes (`<=` rather than `==`) from T6's own turn are similarly verb-agnostic and stayed correct unmodified.

---

## 3. Manual verification

**Classify, live** (via `TerminalIntentAdapter.parse` + `try_request_land_task`):

```text
'land'        -> Task(required_capability_ids=['flight.land'])  metadata: {'task_kind': 'request_land'}
'aterrizar'   -> Task(...)                                       metadata: {'task_kind': 'request_land'}
'Baja'        -> Task(...)                                       metadata: {'task_kind': 'request_land'}
'descender'   -> Task(...)                                       metadata: {'task_kind': 'request_land'}
'hold'        -> None  (LAND's own guard refuses HOLD phrases)
'mantener'    -> None
'estado'      -> None  (Continuity, unaffected)
'explain land' -> None  (explain wins)
'aterriza el dron sobre la mesa' -> None  (not an exact phrase match)
```

**HOLD regression, unaffected:**

```text
try_request_hold_task(Intent('hold')) -> Task(required_capability_ids=['flight.hold'])  metadata: {'task_kind': 'request_hold'}
```

**Full orchestrator path, no LLM present:**

```text
handle_user_text('land', exploding)       -> action='vehicle_land'
  message: 'LAND solicitado, pero no se ejecuta ningún vuelo real desde este chat
             todavía. Safety: reject (motivo: disarmed). Ejecución: not_attempted.'
handle_user_text('aterrizar', exploding)  -> same shape
handle_user_text('baja', exploding)       -> same shape
handle_user_text('hold', exploding)       -> action='vehicle_hold' (unchanged from T6)
handle_user_text('mantener', exploding)   -> action='vehicle_hold' (unchanged)
handle_user_text('estado', exploding)     -> action='project_status'
handle_user_text('explain land', exploding) -> action='global_command'
```

Precedence (explain → Continuity defer → HOLD → LAND → fallthrough) verified through the full orchestrator, HOLD included — re-checked a second time after the docs/cascade fixes in §2, identical results both times.

**`default_safety_gate()`/`ArmedAllowlistSafetyGate` untouched:**

```text
type(default_safety_gate()).__name__ == 'RejectAllSafetyGate'   -> True
ArmedAllowlistSafetyGate().armed == False   (fresh instance, as constructed on every _handle_vehicle_land call)
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

`tests/test_assistant_vehicle_land_task_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | LAND phrase → `Task(required_capability_ids=["flight.land"])`, `task_kind=request_land` | PASS |
| T2 | Non-land craft line → `None` | PASS |
| T3 | Explain / Continuity / HOLD phrase → LAND try is `None`; the same HOLD phrase still classifies via `try_request_hold_task` (proves the guard is LAND-side only) | PASS |
| T4 | `handle_user_text` LAND phrase → message has Safety reject (`disarmed`); never `executed`/`landed`; exploding LLM ok; HOLD/`estado`/explain precedence intact through the full path | PASS |
| T5 | Seed: `flight.land` `not_implemented` + its own `provider.flight_land` (`vehicle`, distinct from `provider.flight_hold`) + skill stub; HOLD + software rows still present | PASS |
| T6 | AST: `assistant_task` no FS/vehicle_profiles/`jarvis.core` | PASS |
| T7 | `default_safety_gate()` still `RejectAllSafetyGate`; fulfill uses a fresh, unarmed `ArmedAllowlistSafetyGate` | PASS |
| T8 | `pyproject.toml` reads `0.6.15` | PASS |

```text
$ python3 -m pytest tests/test_assistant_vehicle_land_task_b1.py -v
8 passed
```

HOLD regression (T6's own suite, must stay green per IC):

```text
$ python3 -m pytest tests/test_assistant_vehicle_hold_task_b1.py -q
8 passed
```

Regression — T7 + T0–T6 + Safety + C4 + fence suites together (after §2's cascade re-fix):

```text
$ python3 -m pytest tests/test_assistant_vehicle_land_task_b1.py \
    tests/test_assistant_vehicle_hold_task_b1.py \
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
    tests/test_fase_c_autonomy_surface_b1.py \
    tests/test_fase_c_craft_fs_bind_b1.py \
    tests/test_fase_c_first_fc_rung_b1.py -q
142 passed, 5 failed
```

The 5 failures are pre-existing, out-of-scope stale `0.5.x` version-checkpoints — not `0.6.14`, not touched by this IC's "bump stale `0.6.14` checkpoints that this Buy owns" instruction.

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3824 passed, 9 skipped
```

All 52 failures are the identical pre-existing stale-version set as before this Buy (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`); 3824 passed is +8 over the T6 baseline (3816), exactly the new T7 test file's count. None of the 39 cascade files, `assistant_task.py`, `orchestrator.py`, or the registry seed appear among the failures.

---

## 5. Non-edits verification

```text
$ git diff --stat -- src/jarvis/capabilities/safety.py src/jarvis/core/project_continuity.py \
    src/jarvis/capabilities/registry.py src/jarvis/capabilities/schemas.py \
    src/jarvis/capabilities/intent.py
(empty)
```

Zero diff on all five. `src/jarvis/flight_software/autonomy/*.py` is used (`propose_command`/`submit_command`/`AutonomyVerb`) but not edited — confirmed the same way. `_handle_vehicle_hold`'s own body diffed byte-identical before/after this Buy's edits (verified by re-reading the method after the orchestrator edit and comparing against the version quoted in the T6 report).

---

## 6. Git-state note: T6 landed mid-session (same pattern as every prior Buy this cycle)

At authorization time, `docs/IMPLEMENTATION_TASKS.md` already showed T6 as `✅ ★ ACCEPT CLOSED · tip v0.6.14` and T7 as `★ AUTHORIZED → Claude` — the Engineer/Cursor side had landed and tagged T6 (`v0.6.14`, commit `5feeab4`) before this turn began. I built this Buy's docs updates on top of that already-updated state rather than re-deriving or overwriting it. `git log`/`git tag` stayed stable throughout this Buy's own implementation — no mid-turn HEAD movement observed this time.

---

## 7. IC acceptance checklist self-check

- [x] Classify + membership + orchestrator fulfill via `submit_command(LAND)` (verified live, §3; tested T1/T4/T5)
- [x] Disarmed `ArmedAllowlist` · honest UX · no FS import in intelligence · HOLD path unchanged (verified live, §3; tested T3/T4/T6/T7; HOLD's own suite re-run green)
- [x] Registry honesty (`flight.land` never `available`, separate provider) · cascade adapted (§2, caught and fixed mid-turn) · tests T1–T8 · docs · package `0.6.15`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.15`** — pending, not claimed here

**No ACCEPT claim.**
