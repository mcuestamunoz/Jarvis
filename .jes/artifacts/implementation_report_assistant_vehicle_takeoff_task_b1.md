# Implementation Report — Assistant vehicle TAKEOFF Task (`B1-assistant-vehicle-takeoff-task`, T9)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_vehicle_takeoff_task_b1.md`](implementation_contract_assistant_vehicle_takeoff_task_b1.md)
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_takeoff_task_b0.md) · T8 `B1-assistant-vehicle-go-to-task` — ★ **ACCEPT CLOSED @ `v0.6.16`** (commit `5c4be12`, tag `v0.6.16` present); Engineer cola lock T9 TAKEOFF → T10 RETURN_HOME; HOLD INV ★ (seams reused — no new INV per this IC's own Parents)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.17` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.17` is reserved for Engineer ACCEPT per IC §3/§4.

---

## 1. Files changed

**New:**
- `tests/test_assistant_vehicle_takeoff_task_b1.py` — T1–T8

**Modified:**
- `src/jarvis/config.py` — added `VEHICLE_TAKEOFF_PHRASES: frozenset[str]` (9 already-accent-free entries: `takeoff`, `take off`, `despegar`, `despega`, `despegue`, `levanta`, `levantar`, `sube`, `ascender`), right after `VEHICLE_GO_TO_PHRASES`
- `src/jarvis/intelligence/assistant_task.py` — added `CAPABILITY_FLIGHT_TAKEOFF`, `TASK_KIND_REQUEST_TAKEOFF`, `try_request_takeoff_task`; module docstring extended to mention T9, including the DC §0 row 7 note about `ArmedAllowlistSafetyGate`'s unwidened allow-list
- `src/jarvis/core/orchestrator.py` — `_handle_global_commands` gained a new branch (after the GO_TO branch, before `return None`): build an `Intent`, call `try_request_takeoff_task`, and on a match, fulfill via a new `_handle_vehicle_takeoff` method — `_handle_vehicle_hold`, `_handle_vehicle_land`, and `_handle_vehicle_go_to` were **not** touched (thin sibling per IC's explicit instruction, see §2)
- `src/jarvis/capabilities/data/default_registry.json` — added, keeping every existing row byte-identical: capability `flight.takeoff` (`v0.6.17`, `availability=not_implemented`, `provider_id=provider.flight_takeoff`), provider `provider.flight_takeoff` (`kind=vehicle`, offers `["flight.takeoff"]`, its own **separate** provider from the three earlier vehicle providers), skill `skill.request_takeoff` (`v0.6.17`, `required_capability_ids=["flight.takeoff"]`, `availability=stub`)
- `pyproject.toml` — `version = "0.6.16"` → `version = "0.6.17"`
- Thirteen files' own stale version-checkpoint assertions bumped `0.6.16` → `0.6.17` (IC §2: "bump stale `0.6.16` checkpoints this Buy owns"): `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_software_safety_bridge_b1.py`, `tests/test_assistant_task_registry_coherence_b1.py`, `tests/test_assistant_vehicle_go_to_task_b1.py`, `tests/test_assistant_vehicle_hold_task_b1.py`, `tests/test_assistant_vehicle_land_task_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_capability_skills_seed_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py`
- **39 Fase C isolation files** — the same T2/T5/T6/T7/T8-era cascade, scripted-and-verified again (see §2): the shared skill-id assertion extended from five ids to all six (adding `skill.request_takeoff`) — run proactively, immediately after wiring the orchestrator, same discipline established in T8's own turn
- `src/jarvis/intelligence/README.md` — new "Vehicle TAKEOFF Task (T9)" section (placed above the T8 section, newest-first per existing convention); Buys/Package/Parent lines updated to `0.6.17`; the T5 "Skills catalog" pointer paragraph extended to mention T9's sixth skill row; the T8 section's stale "no TAKEOFF/FOLLOW/RETURN_HOME/PATROL" line corrected to note TAKEOFF shipped here
- `docs/PLATFORM_CAPABILITY_VISION.md` — §10's "First vehicle verb" paragraph extended to cover TAKEOFF; §12 Placement line: T8 corrected to ★ ACCEPT CLOSED @ `v0.6.16`, new T9 clause added; §13 gained a new T9 paragraph, and the T8 paragraph's stale "arm()/TAKEOFF/FOLLOW/RETURN_HOME/PATROL remain out" corrected to note TAKEOFF shipped here
- `docs/system_map/CONNECTIONS.md` — **extended the existing T8 note** (corrected its status to ★ ACCEPT CLOSED @ `v0.6.16`) and **added a new paragraph directly below it** for T9; **extended C-010's own row** a fourth time (Symbols/Authority/Mutation/Evidence fields, naming the new TAKEOFF branch and the six-way precedence). **No new `C-xxx`**, per IC §0 row 12
- `docs/USER_GUIDE_EXPLAIN.md` — one internal-architecture note appended after T8's own (§7), following the same established "Nota interna" pattern; no user-facing instruction changed
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T9 cola row updated from "★ AUTHORIZED → Claude" to "IMPLEMENTED · package `0.6.17`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link; the already-Engineer-locked T10 queue row (RETURN_HOME) was left untouched

**Not touched (verified — see §4):** `src/jarvis/capabilities/safety.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/registry.py`, `src/jarvis/capabilities/schemas.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/flight_software/autonomy/*.py` (the existing C4 surface — used, never edited), `core/orchestrator.py`'s own `_handle_vehicle_hold`, `_handle_vehicle_land`, and `_handle_vehicle_go_to` methods (verified via `git diff` showing zero removed/modified lines anywhere in the file — pure additions only), `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.vehicle_profiles`, `default_safety_gate()`'s function body, `RejectAllSafetyGate`, `ArmedAllowlistSafetyGate`'s class body/allow-list/`arm()` method (still `{HOLD, LAND, GO_TO}`, unwidened per DC §0 row 7 — TAKEOFF deliberately not added).

---

## 2. Design choices carried over from HOLD/LAND/GO_TO

**Fourth thin sibling (IC's own instruction, verbatim: "Do NOT edit `_handle_vehicle_hold` / `_handle_vehicle_land` / `_handle_vehicle_go_to` bodies").** `_handle_vehicle_takeoff` is a near-identical sibling of the three earlier fulfill methods — same gate construction, same message shape, verb-swapped, `params={}`. Verified via `git diff -- src/jarvis/core/orchestrator.py | grep "^-" | grep -v "^---"` returning empty: every line in the diff is an addition, zero lines removed or modified anywhere in the file, confirming all three earlier methods are byte-for-byte untouched.

**Internal HOLD+LAND+GO_TO guard (IC §0 row 10).** `try_request_takeoff_task` refuses explain-shaped, Continuity-defer-shaped, HOLD-shaped, LAND-shaped, *and* GO_TO-shaped input internally — five ahead-of-it guards deep, same discipline every earlier kind uses. Verified by test T3: HOLD, LAND, and GO_TO phrases fed directly to `try_request_takeoff_task` are all refused, while the same phrases fed to their own classifiers still match — proving TAKEOFF's guard doesn't leak into any earlier kind's own behavior.

**Empty params, no altitude parsing (DC §0 row 9 / IC §0 row 9).** `_handle_vehicle_takeoff` always calls `propose_command(AutonomyVerb.TAKEOFF, intent_id=intent.id, params={})`. Verified live and by test T7 (`command.params == {}`).

**`ArmedAllowlistSafetyGate`'s own allow-list stays unwidened (DC §0 row 7 — explicit note in the DC itself).** The gate's `_ALLOWED_VERBS` is still `frozenset({"HOLD", "LAND", "GO_TO"})` — TAKEOFF is not on it. This is irrelevant on the product chat path (the gate is always constructed disarmed, so the outcome is always `"disarmed"` regardless of allow-list membership), but is worth testing explicitly since the DC calls it out as a fact worth knowing: if a later Buy ever armed the gate, `TAKEOFF` would resolve to `verb_not_allowed` rather than `allow`, until a separate, explicit allow-list-widening Buy. Verified by test T7's own assertion on `ArmedAllowlistSafetyGate._ALLOWED_VERBS`.

**Cascade re-adaptation run proactively (continuing the T8-established discipline).** Following the same pattern successfully used in T8 (after T7's own near-miss), I ran the verify-then-script cascade update (39 files, five-id set → six-id set) immediately after wiring the orchestrator, before writing the new test file. The subsequent regression bundle showed only the pre-existing, out-of-scope stale-`0.5.x` failures on the first run.

---

## 3. Manual verification

**Classify, live** (via `TerminalIntentAdapter.parse` + `try_request_takeoff_task`):

```text
'takeoff'    -> Task(required_capability_ids=['flight.takeoff'])  metadata: {'task_kind': 'request_takeoff'}
'take off'   -> Task(...)
'Despegar'   -> Task(...)
'despega'    -> Task(...)
'levanta'    -> Task(...)
'sube'       -> Task(...)
'ascender'   -> Task(...)
'hold'       -> None  (TAKEOFF's own guard refuses HOLD phrases)
'land'       -> None  (TAKEOFF's own guard refuses LAND phrases)
'go to'      -> None  (TAKEOFF's own guard refuses GO_TO phrases)
'estado'     -> None  (Continuity, unaffected)
'explain takeoff' -> None  (explain wins)
'sube el volumen' -> None  (not an exact phrase match)
```

**HOLD + LAND + GO_TO regression, unaffected:**

```text
try_request_hold_task(Intent('hold'))   -> Task(required_capability_ids=['flight.hold'])
try_request_land_task(Intent('land'))   -> Task(required_capability_ids=['flight.land'])
try_request_go_to_task(Intent('go to')) -> Task(required_capability_ids=['flight.go_to'])
```

**Full orchestrator path, no LLM present:**

```text
handle_user_text('takeoff', exploding)    -> action='vehicle_takeoff'
  message: 'TAKEOFF solicitado, pero no se ejecuta ningún despegue real desde este
             chat todavía. Safety: reject (motivo: disarmed). Ejecución: not_attempted.'
handle_user_text('go to', exploding)      -> action='vehicle_go_to' (unchanged from T8)
handle_user_text('land', exploding)       -> action='vehicle_land' (unchanged from T7)
handle_user_text('hold', exploding)       -> action='vehicle_hold' (unchanged from T6)
handle_user_text('estado', exploding)     -> action='project_status'
handle_user_text('explain takeoff', exploding) -> action='global_command'
```

Precedence (explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → fallthrough) verified through the full orchestrator, all three earlier verbs included — re-checked a second time after the docs/cascade work, identical results both times.

**`default_safety_gate()`/`ArmedAllowlistSafetyGate` untouched:**

```text
type(default_safety_gate()).__name__ == 'RejectAllSafetyGate'   -> True
ArmedAllowlistSafetyGate().armed == False   (fresh instance, as constructed on every _handle_vehicle_takeoff call)
ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset({'HOLD', 'LAND', 'GO_TO'})   -> unwidened, TAKEOFF absent
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

`tests/test_assistant_vehicle_takeoff_task_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | TAKEOFF phrase → `Task(required_capability_ids=["flight.takeoff"])`, `task_kind=request_takeoff` | PASS |
| T2 | Non-takeoff craft line → `None` | PASS |
| T3 | Explain / Continuity / HOLD / LAND / GO_TO → TAKEOFF try `None`; all four prior classifiers still match their own phrases | PASS |
| T4 | `handle_user_text` TAKEOFF → Safety reject (`disarmed`); never `executed`/`airborne`; exploding LLM ok; HOLD/LAND/GO_TO/`estado`/explain precedence intact through the full path | PASS |
| T5 | Seed honesty (`flight.takeoff` `not_implemented`, separate provider, skill stub) + all prior rows present, all four vehicle providers distinct | PASS |
| T6 | AST fence on `assistant_task` | PASS |
| T7 | `default_safety_gate()` RejectAll; fulfill uses disarmed `ArmedAllowlistSafetyGate`; empty `params`; TAKEOFF confirmed absent from the gate's own allow-list | PASS |
| T8 | `pyproject.toml` reads `0.6.17` | PASS |

```text
$ python3 -m pytest tests/test_assistant_vehicle_takeoff_task_b1.py -v
8 passed
```

HOLD + LAND + GO_TO regression (must stay green per IC):

```text
$ python3 -m pytest tests/test_assistant_vehicle_hold_task_b1.py tests/test_assistant_vehicle_land_task_b1.py tests/test_assistant_vehicle_go_to_task_b1.py -q
24 passed
```

Regression — T9 + T0–T8 + Safety + C4 + fence suites together (cascade already fixed proactively, §2):

```text
$ python3 -m pytest tests/test_assistant_vehicle_takeoff_task_b1.py \
    tests/test_assistant_vehicle_go_to_task_b1.py \
    tests/test_assistant_vehicle_land_task_b1.py \
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
158 passed, 5 failed
```

The 5 failures are pre-existing, out-of-scope stale `0.5.x` version-checkpoints — not `0.6.16`, not touched by this IC's "bump stale `0.6.16` checkpoints this Buy owns" instruction.

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3840 passed, 9 skipped
```

All 52 failures are the identical pre-existing stale-version set as before this Buy (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`); 3840 passed is +8 over the T8 baseline (3832), exactly the new T9 test file's count. None of the 39 cascade files, `assistant_task.py`, `orchestrator.py`, or the registry seed appear among the failures.

---

## 5. Non-edits verification

```text
$ git diff --stat -- src/jarvis/capabilities/safety.py src/jarvis/core/project_continuity.py \
    src/jarvis/capabilities/registry.py src/jarvis/capabilities/schemas.py \
    src/jarvis/capabilities/intent.py
(empty)

$ git diff -- src/jarvis/core/orchestrator.py | grep "^-" | grep -v "^---"
(empty)
```

Zero diff on the first five files. The second check confirms `orchestrator.py`'s diff is pure addition — no line was removed or modified anywhere in the file, so `_handle_vehicle_hold`, `_handle_vehicle_land`, and `_handle_vehicle_go_to` are all provably byte-for-byte unchanged. `src/jarvis/flight_software/autonomy/*.py` is used (`propose_command`/`submit_command`/`AutonomyVerb`) but not edited — confirmed the same way.

---

## 6. Git-state note: T8 landed mid-session (same pattern as every prior Buy this cycle)

At authorization time, `docs/IMPLEMENTATION_TASKS.md` already showed T8 as `✅ ★ ACCEPT CLOSED · tip v0.6.16` and T9 as `★ AUTHORIZED → Claude`, with T10 (RETURN_HOME) already Engineer-locked in the queue below it — the Engineer/Cursor side had landed and tagged T8 (`v0.6.16`, commit `5c4be12`) before this turn began. I built this Buy's docs updates on top of that already-updated state, leaving the T10 queue row untouched. `git log`/`git tag` stayed stable throughout this Buy's own implementation — no mid-turn HEAD movement observed this time.

---

## 7. IC acceptance checklist self-check

- [x] Classify + membership + fulfill `submit_command(TAKEOFF)` (verified live, §3; tested T1/T4/T5/T7)
- [x] Disarmed `ArmedAllowlist` · honest UX · prior verbs unchanged (verified live, §3/§5; tested T3/T4/T6/T7; all three prior suites re-run green)
- [x] Registry · cascade (run proactively, §2) · T1–T8 · docs · `0.6.17`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.17`** — pending, not claimed here

**No ACCEPT claim.**
