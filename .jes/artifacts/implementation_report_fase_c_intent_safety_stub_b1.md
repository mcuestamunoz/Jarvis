# Implementation Report — Fase C Intent ingress + Safety gate stub (`B1-fase-c-intent-safety-stub`)

**IC:** [`implementation_contract_fase_c_intent_safety_stub_b1.md`](implementation_contract_fase_c_intent_safety_stub_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** **ACCEPT CLOSED** (Engineer 2026-09-20) — Cursor review PASS; package stays `0.5.0` (no tag).

---

## 1. Package path

Added to the existing `src/jarvis/capabilities/` tree (IC §3 guidance — no new top-level package):

```text
src/jarvis/capabilities/
├── __init__.py          # extended: exports intent + safety public types
├── schemas.py            # C1, unchanged
├── registry.py            # C1, unchanged
├── intent.py              # NEW — IntentSource, Intent, Task, 4 channel adapters
├── safety.py               # NEW — AuthoritySignal, SafetyRequest/Decision, SafetyGate, RejectAllSafetyGate, default_safety_gate, run_intent_through_safety
└── data/default_registry.json   # C1, unchanged
```

No `flight_software/`, `safety/` (top-level), or `intent/` package was created. `orchestrator.py`, Board, and `library/` are untouched — confirmed by `grep -rln "jarvis.capabilities" src/jarvis/core/ src/jarvis/adapters/` returning nothing.

---

## 2. Types implemented vs IC §1

| Type | IC §1 ref | Match |
|---|---|---|
| `IntentSource` (`terminal`/`voice`/`radio`/`api`/`ui`) | §1.1 | ✅ `ui` included as the IC's stated optional member |
| `Intent` (`id`, `source`, `raw_text`, `created_at`, `metadata`) | §1.2 | ✅ `model_config = ConfigDict(extra="forbid")`; `metadata: dict[str, str]` bounded to string values |
| `Task` (`id`, `intent_id`, `required_capability_ids`) | §1.3 | ✅ shipped, no execution fields, no production code path constructs an instance outside tests |
| `AuthoritySignal` (`id`, `source`, `kind`, `payload`) | §1.4 | ✅ `source: Literal["radio","api","operator"]`, `kind: Literal["override","kill","mode","unknown"]` — data only, no decode |
| `SafetyDecision` (`outcome`, `reason`, `gate_id`) | §1.5 | ✅ `outcome: Literal["allow","reject","defer"]`; `@model_validator(mode="after")` enforces `reason` is non-empty whenever `outcome == "reject"` |
| `SafetyRequest` (`intent_id`, `action_id`) | §1.6 | ✅ both optional, no actuator command blob field exists |

---

## 3. APIs implemented vs IC §2

### 3.1 Channel adapters (§2.1)

- `TerminalIntentAdapter.parse(raw_text: str) -> Intent` — constructs `Intent(source=TERMINAL, raw_text=...)`. The **only** adapter that returns successfully in C2.
- `VoiceIntentAdapter.parse(...)`, `RadioIntentAdapter.parse(...)`, `ApiIntentAdapter.parse(...)` — each raises `NotImplementedError` whose message contains the literal substring `"not_implemented"`, per the IC's lock. None can produce a "success flight intent."

### 3.2 Safety (§2.2)

- `SafetyGate` — `typing.Protocol` (matching the existing interface convention in this codebase, e.g. `jarvis.llm.llm_client.LLMClient`), with `evaluate(request: SafetyRequest) -> SafetyDecision`.
- `RejectAllSafetyGate` — the only concrete gate shipped under `src/`. `evaluate(...)` always returns `SafetyDecision(outcome="reject", reason="not_implemented", gate_id="reject_all")`.
- `default_safety_gate()` — the **only** shipped gate factory; always returns `RejectAllSafetyGate()`.
- **`AllowAllSafetyGate` does not exist anywhere under `src/`** — confirmed by `test_t4_allow_all_gate_does_not_exist_under_src`, which checks both `jarvis.capabilities.safety` and the public `jarvis.capabilities` package.

### 3.3 Pipeline helper (§2.3)

- `run_intent_through_safety(intent, gate) -> SafetyDecision` — builds a `SafetyRequest(intent_id=intent.id)` and returns `gate.evaluate(request)`. No actuator call, no Skill `execute`, no registry "run" anything; with the default gate this always resolves to `reject`. This same function satisfies IC §0 decision 7 (the "pipeline stub" requirement) — no separate `propose_resolution`/`ResolutionProposal` was added since the IC lists that as optional and §2's normative API list only names the three helpers above.

---

## 4. Tests run + counts

New module: `tests/test_fase_c_intent_safety_stub_b1.py` — **11 tests**, all passing, covering IC §4 T1–T9 plus two extra cases (reason-required-on-reject validation, and a structural Protocol-conformance check):

```text
test_t1_terminal_adapter_builds_intent PASSED
test_t2_voice_radio_api_adapters_refuse PASSED
test_t3_default_gate_always_rejects_not_implemented PASSED
test_t4_allow_all_gate_does_not_exist_under_src PASSED
test_t5_run_intent_through_safety_rejects_with_default_gate PASSED
test_t6_authority_signal_is_data_only PASSED
test_t7_no_execute_dispatch_command_esc_in_new_modules PASSED
test_t8_capability_registry_default_still_empty PASSED
test_t9_pyproject_version_stays_0_5_0 PASSED
test_safety_decision_requires_reason_on_reject PASSED
test_safety_gate_is_structurally_satisfied_by_reject_all PASSED
```

**T10 (full craft suite green):** `pytest -q` at repo root — **3192 passed, 1 skipped** (baseline before this Buy was 3181 passed, 1 skipped; delta is exactly the 11 new tests, no other file's pass/fail count moved).

**T11 (report confirms H-locks):** see §5 below.

No pre-existing test needed modification for this Buy — the version stays `0.5.0` so none of the checkpoint-version pins (already re-pinned in the C1 Buy) needed touching again.

---

## 5. Honesty / forbidden confirmation (IC §5)

| Rule | Status | Evidence |
|---|---|---|
| Default gate must not `allow` | ✅ | `default_safety_gate()` → `RejectAllSafetyGate`, `evaluate()` hardcodes `outcome="reject"`. `SafetyDecision`'s own validator makes an empty-reason `reject` impossible to construct at all |
| Voice/radio "working" parse forbidden | ✅ | All three non-terminal adapters unconditionally raise `NotImplementedError("...not_implemented...")` — no code path inside them can return an `Intent` |
| CLI `handle_user_text` must not hook into Safety | ✅ | Zero references to `jarvis.capabilities` in `src/jarvis/core/` or `src/jarvis/adapters/` (grep-verified) |
| No new "available" flight capabilities | ✅ | This Buy adds no `CapabilityRecord`/`ProviderRecord` instances to any product path; `CapabilityRegistry.load_default()` is untouched and still empty (T8) |
| No ELRS/CRSF drivers | ✅ | `AuthoritySignal` is a plain data record (`id`/`source`/`kind`/`payload: str \| None`) — no decode logic, no radio I/O |
| No FC rung / mixer | ✅ | Not present anywhere in `intent.py`/`safety.py` |
| No `execute`/`dispatch`/`command_esc` method or field | ✅ | `test_t7_no_execute_dispatch_command_esc_in_new_modules` audits every public class attribute in both new modules |
| No craft coupling (orchestrator/Board/`library/`) | ✅ | Neither file touched; only `src/jarvis/capabilities/*` and docs/report files changed |
| Version stays `0.5.0` | ✅ | `pyproject.toml` unchanged from C1's `0.5.0` (T9) |

---

## 6. Files changed

**New:**
- `src/jarvis/capabilities/intent.py`
- `src/jarvis/capabilities/safety.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `.jes/artifacts/implementation_report_fase_c_intent_safety_stub_b1.md` (this file)

**Modified:**
- `src/jarvis/capabilities/__init__.py` — exports the new `intent`/`safety` public types alongside the existing C1 exports
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C2 queue row updated to "landed, awaiting ★ ACCEPT"; suite count 3181 → 3192
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 split into C1 (ACCEPT CLOSED) and C2 (landed) blocks with report links
- `docs/ARCHITECTURE.md` — §1b extended with the C2 `intent.py`/`safety.py` paragraph

**Not touched (confirmed):** `pyproject.toml`, `README.md`, `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `.jes/state/engineering_state.json`.

---

## 7. Residual — what C3 should pick up

- First FC rung (per C0 attack order) — out of scope here per IC §6/§0 decision 12.
- A real (non-`RejectAll`) Safety policy remains unauthorized until its own IC explicitly opens that door — C2 intentionally ships no path to `allow`.
- `AuthoritySignal` stays undecoded data; ELRS/CRSF decode is C5 per the IC.
- Git tag: this Buy does not bump the version, so no new tag is expected from it — `v0.5.0` (from C1) remains the current tag pending Engineer ACCEPT of this C2 Buy.

---

## 8. Acceptance self-check against IC §7

- T1–T11: ✅ (T10/T11 are process gates, both satisfied — see §4 above)
- Default Safety always rejects: ✅
- Terminal Intent only produces a real `Intent`: ✅
- No `flight_software/` tree: ✅ (`find src -iname "flight_software"` → empty)
- Version stays `0.5.0`: ✅
