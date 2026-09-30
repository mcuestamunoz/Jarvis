# Implementation Report — Assistant vehicle GO_TO Task (`B1-assistant-vehicle-go-to-task`, T8)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_assistant_vehicle_go_to_task_b1.md`](implementation_contract_assistant_vehicle_go_to_task_b1.md)
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_go_to_task_b0.md) · T7 `B1-assistant-vehicle-land-task` — ★ **ACCEPT CLOSED @ `v0.6.15`** (commit `8b50a86`, tag `v0.6.15` present); T6 HOLD ★ / HOLD INV ★ (seams reused — no new INV per this IC's own Parents)
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.16` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.16` is reserved for Engineer ACCEPT per IC §3/§4.

---

## 1. Files changed

**New:**
- `tests/test_assistant_vehicle_go_to_task_b1.py` — T1–T8

**Modified:**
- `src/jarvis/config.py` — added `VEHICLE_GO_TO_PHRASES: frozenset[str]` (9 already-accent-free entries: `go to`, `goto`, `go_to`, `ve a`, `ir a`, `dirigete`, `dirigete a`, `navega`, `navigate`), right after `VEHICLE_LAND_PHRASES`
- `src/jarvis/intelligence/assistant_task.py` — added `CAPABILITY_FLIGHT_GO_TO`, `TASK_KIND_REQUEST_GO_TO`, `try_request_go_to_task`; module docstring extended to mention T8
- `src/jarvis/core/orchestrator.py` — `_handle_global_commands` gained a new branch (after the LAND branch, before `return None`): build an `Intent`, call `try_request_go_to_task`, and on a match, fulfill via a new `_handle_vehicle_go_to` method — `_handle_vehicle_hold` and `_handle_vehicle_land` were **not** touched (thin sibling per IC's explicit instruction "Do NOT edit `_handle_vehicle_hold`/`_handle_vehicle_land` bodies", see §2)
- `src/jarvis/capabilities/data/default_registry.json` — added, keeping every existing row byte-identical: capability `flight.go_to` (`v0.6.16`, `availability=not_implemented`, `provider_id=provider.flight_go_to`), provider `provider.flight_go_to` (`kind=vehicle`, offers `["flight.go_to"]`, its own **separate** provider from `provider.flight_hold`/`provider.flight_land`), skill `skill.request_go_to` (`v0.6.16`, `required_capability_ids=["flight.go_to"]`, `availability=stub`)
- `pyproject.toml` — `version = "0.6.15"` → `version = "0.6.16"`
- Twelve files' own stale version-checkpoint assertions bumped `0.6.15` → `0.6.16` (IC §2: "bump stale `0.6.15` checkpoints this Buy owns"): `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_software_safety_bridge_b1.py`, `tests/test_assistant_task_registry_coherence_b1.py`, `tests/test_assistant_vehicle_hold_task_b1.py`, `tests/test_assistant_vehicle_land_task_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_capability_skills_seed_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py`
- **39 Fase C isolation files** — the same T2/T5/T6/T7-era cascade, scripted-and-verified again (see §2): the shared skill-id assertion extended from four ids to all five (adding `skill.request_go_to`) — **this time run proactively, immediately after wiring the orchestrator**, to avoid the gap that surfaced mid-turn during T7's own report
- `src/jarvis/intelligence/README.md` — new "Vehicle GO_TO Task (T8)" section (placed above the T7 section, newest-first per existing convention); Buys/Package/Parent lines updated to `0.6.16`; the T5 "Skills catalog" pointer paragraph extended to mention T8's fifth skill row; the T7 section's stale "no GO_TO (separate future Buy)" line corrected to note GO_TO shipped here
- `docs/PLATFORM_CAPABILITY_VISION.md` — §10's "First vehicle verb" paragraph extended to cover GO_TO (and its empty-`params` honesty); §12 Placement line: T7 corrected to ★ ACCEPT CLOSED @ `v0.6.15`, new T8 clause added; §13 gained a new T8 paragraph, and the T7 paragraph's stale "GO_TO remains a separate later Buy" corrected to note it shipped here
- `docs/system_map/CONNECTIONS.md` — **extended the existing T7 note** (corrected its status to ★ ACCEPT CLOSED @ `v0.6.15`) and **added a new paragraph directly below it** for T8; **extended C-010's own row** a third time (Symbols/Authority/Mutation/Evidence fields, naming the new GO_TO branch and the five-way precedence). **No new `C-xxx`**, per IC §0 row 12
- `docs/USER_GUIDE_EXPLAIN.md` — one internal-architecture note appended after T7's own (§7), following the same established "Nota interna" pattern; no user-facing instruction changed
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T8 cola row updated from "★ AUTHORIZED → Claude" to "IMPLEMENTED · package `0.6.16`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link; the already-Engineer-locked T9/T10 queue rows (TAKEOFF/RETURN_HOME) were left untouched

**Not touched (verified — see §4):** `src/jarvis/capabilities/safety.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/registry.py`, `src/jarvis/capabilities/schemas.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/flight_software/autonomy/*.py` (the existing C4 surface — used, never edited), `core/orchestrator.py`'s own `_handle_vehicle_hold` and `_handle_vehicle_land` methods (verified via `git diff` showing zero removed/modified lines anywhere in the file — pure additions only), `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.vehicle_profiles`, `default_safety_gate()`'s function body, `RejectAllSafetyGate`, `ArmedAllowlistSafetyGate`'s class body/allow-list/`arm()` method.

---

## 2. Design choices carried over from HOLD/LAND, and lessons applied from T7's near-miss

**Thin sibling, not a third refactor (IC's own instruction, verbatim: "Do NOT edit `_handle_vehicle_hold` / `_handle_vehicle_land` bodies").** `_handle_vehicle_go_to` is a near-identical sibling of the two earlier fulfill methods — same gate construction, same message shape, verb-swapped, `params={}` added. Verified via `git diff -- src/jarvis/core/orchestrator.py | grep "^-" | grep -v "^---"` returning empty: every line in the diff is an addition, zero lines removed or modified anywhere in the file, confirming both earlier methods are byte-for-byte untouched.

**Internal HOLD+LAND guard (IC §0 row 10).** `try_request_go_to_task` refuses explain-shaped, Continuity-defer-shaped, HOLD-shaped, *and* LAND-shaped input internally — mirroring the same discipline every earlier kind uses, now four ahead-of-it guards deep. Verified by test T3: HOLD and LAND phrases fed directly to `try_request_go_to_task` are refused, while the same phrases fed to their own classifiers still match — proving GO_TO's guard doesn't leak into HOLD/LAND's own behavior.

**Empty params, no coordinate parsing (DC §0 row 9 / IC §0 row 9).** `_handle_vehicle_go_to` always calls `propose_command(AutonomyVerb.GO_TO, intent_id=intent.id, params={})` — the empty dict is passed explicitly rather than relying on `AutonomyCommand`'s own default, matching the IC's exact wording. Verified live and by test T7 (`command.params == {}`).

**Cascade re-adaptation run proactively this time.** T7's own report documented a near-miss: the 39-file skill-count cascade adaptation was initially skipped and only caught by a broad regression run after the fact. For this Buy, I ran the equivalent verify-then-script cascade update (39 files, four-id set → five-id set, same counting-script discipline as every prior round) **immediately after wiring the orchestrator**, before writing the new test file or bumping the version — and the subsequent regression bundle (HOLD + LAND + Safety + C4 + fence suites together) showed only the pre-existing, out-of-scope stale-`0.5.x` failures on the first run, with no new cascade gap to chase down this time.

---

## 3. Manual verification

**Classify, live** (via `TerminalIntentAdapter.parse` + `try_request_go_to_task`):

```text
'go to'       -> Task(required_capability_ids=['flight.go_to'])  metadata: {'task_kind': 'request_go_to'}
'goto'        -> Task(...)
've a'        -> Task(...)
'ir a'        -> Task(...)
'Navega'      -> Task(...)
'navigate'    -> Task(...)
'dirigete a'  -> Task(...)
'hold'        -> None  (GO_TO's own guard refuses HOLD phrases)
'land'        -> None  (GO_TO's own guard refuses LAND phrases)
'estado'      -> None  (Continuity, unaffected)
'explain go to' -> None  (explain wins)
've a comprar pan' -> None  (not an exact phrase match)
```

**HOLD + LAND regression, unaffected:**

```text
try_request_hold_task(Intent('hold')) -> Task(required_capability_ids=['flight.hold'])
try_request_land_task(Intent('land')) -> Task(required_capability_ids=['flight.land'])
```

**Full orchestrator path, no LLM present:**

```text
handle_user_text('go to', exploding)      -> action='vehicle_go_to'
  message: 'GO_TO solicitado, pero no se ejecuta ninguna navegación real desde este
             chat todavía. Safety: reject (motivo: disarmed). Ejecución: not_attempted.'
handle_user_text('land', exploding)       -> action='vehicle_land' (unchanged from T7)
handle_user_text('hold', exploding)       -> action='vehicle_hold' (unchanged from T6)
handle_user_text('estado', exploding)     -> action='project_status'
handle_user_text('explain go to', exploding) -> action='global_command'
```

Precedence (explain → Continuity defer → HOLD → LAND → GO_TO → fallthrough) verified through the full orchestrator, HOLD and LAND both included — re-checked a second time after the docs/cascade work, identical results both times.

**`default_safety_gate()`/`ArmedAllowlistSafetyGate` untouched:**

```text
type(default_safety_gate()).__name__ == 'RejectAllSafetyGate'   -> True
ArmedAllowlistSafetyGate().armed == False   (fresh instance, as constructed on every _handle_vehicle_go_to call)
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

`tests/test_assistant_vehicle_go_to_task_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | GO_TO phrase → `Task(required_capability_ids=["flight.go_to"])`, `task_kind=request_go_to` | PASS |
| T2 | Non-go-to craft line → `None` | PASS |
| T3 | Explain / Continuity / HOLD / LAND phrase → GO_TO try is `None`; HOLD/LAND classifiers still match their own phrases | PASS |
| T4 | `handle_user_text` GO_TO phrase → Safety reject (`disarmed`); never `executed`/`navigated`/`arrived`; exploding LLM ok; HOLD/LAND/`estado`/explain precedence intact through the full path | PASS |
| T5 | Seed: `flight.go_to` `not_implemented` + its own separate vehicle provider + skill stub; HOLD/LAND/software rows still present; all three vehicle providers distinct | PASS |
| T6 | AST: `assistant_task` no FS/vehicle_profiles/`jarvis.core` | PASS |
| T7 | `default_safety_gate()` still `RejectAllSafetyGate`; fulfill uses a fresh, unarmed `ArmedAllowlistSafetyGate`; `propose_command`'s `params` is exactly `{}` | PASS |
| T8 | `pyproject.toml` reads `0.6.16` | PASS |

```text
$ python3 -m pytest tests/test_assistant_vehicle_go_to_task_b1.py -v
8 passed
```

HOLD + LAND regression (must stay green per IC):

```text
$ python3 -m pytest tests/test_assistant_vehicle_hold_task_b1.py tests/test_assistant_vehicle_land_task_b1.py -q
16 passed
```

Regression — T8 + T0–T7 + Safety + C4 + fence suites together (cascade already fixed proactively, §2):

```text
$ python3 -m pytest tests/test_assistant_vehicle_go_to_task_b1.py \
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
150 passed, 5 failed
```

The 5 failures are pre-existing, out-of-scope stale `0.5.x` version-checkpoints — not `0.6.15`, not touched by this IC's "bump stale `0.6.15` checkpoints this Buy owns" instruction.

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3832 passed, 9 skipped
```

All 52 failures are the identical pre-existing stale-version set as before this Buy (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`); 3832 passed is +8 over the T7 baseline (3824), exactly the new T8 test file's count. None of the 39 cascade files, `assistant_task.py`, `orchestrator.py`, or the registry seed appear among the failures.

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

Zero diff on the first five files. The second check confirms `orchestrator.py`'s diff is pure addition — no line was removed or modified anywhere in the file, so `_handle_vehicle_hold` and `_handle_vehicle_land` are provably byte-for-byte unchanged, satisfying the IC's explicit instruction directly (not just by inspection). `src/jarvis/flight_software/autonomy/*.py` is used (`propose_command`/`submit_command`/`AutonomyVerb`) but not edited — confirmed the same way.

---

## 6. Git-state note: T7 landed mid-session (same pattern as every prior Buy this cycle)

At authorization time, `docs/IMPLEMENTATION_TASKS.md` already showed T7 as `✅ ★ ACCEPT CLOSED · tip v0.6.15` and T8 as `★ AUTHORIZED → Claude`, with T9 (TAKEOFF) and T10 (RETURN_HOME) already Engineer-locked in the queue below it — the Engineer/Cursor side had landed and tagged T7 (`v0.6.15`, commit `8b50a86`) before this turn began. I built this Buy's docs updates on top of that already-updated state, leaving the T9/T10 queue rows untouched. `git log`/`git tag` stayed stable throughout this Buy's own implementation — no mid-turn HEAD movement observed this time.

---

## 7. IC acceptance checklist self-check

- [x] Classify + membership + orchestrator fulfill via `submit_command(GO_TO)` with empty params (verified live, §3; tested T1/T4/T5/T7)
- [x] Disarmed `ArmedAllowlist` · honest UX · no FS import in intelligence · HOLD/LAND unchanged (verified live, §3/§5; tested T3/T4/T6/T7; both prior suites re-run green)
- [x] Registry honesty (`flight.go_to` never `available`, separate provider) · cascade adapted proactively (§2) · tests T1–T8 · docs · package `0.6.16`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.16`** — pending, not claimed here

**No ACCEPT claim.**
