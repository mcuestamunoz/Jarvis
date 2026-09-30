# Implementation Review — Assistant software Safety bridge (`B1-assistant-software-safety-bridge`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_assistant_software_safety_bridge_b1.md) · [report](implementation_report_assistant_software_safety_bridge_b1.md) · vision §10  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review **PASS**. Package/tag **`0.6.12` / `v0.6.12`**.

**Review format lock (Engineer):** every future review must explain (1) what landed, (2) where it leaves the system vs before, (3) how it adds to the path — so the Engineer can choose the next Buy consciously.

---

## 1. What this Buy claims to do

Close the vision gap **Intent → Task → capability → Safety → provider** for the two software Tasks already in product (`explain_concept`, `defer_to_continuity`), without enabling vehicle verbs or changing the FS/default RejectAll factory.

| Layer | Before T4 | After T4 |
|---|---|---|
| Classify | T0/T1 phrase/prefix match | unchanged |
| Registry membership | T3 `get_capability is not None` | unchanged (still first) |
| Safety | **none** on Assistant Task path | `SoftwareCapabilitySafetyGate` |
| Fulfill | cite / `_handle_project_status` | unchanged when allow |
| Flight Safety factory | `default_safety_gate()` → RejectAll | **unchanged** |

---

## 2. How the review was done (independent of Claude)

1. Re-read IC §0 locks and §1 shapes.  
2. Read `SoftwareCapabilitySafetyGate.evaluate` and `_parse_capability_action_id` in `safety.py`.  
3. Read both `try_explain_concept_task` / `try_defer_to_continuity_task` call order in `assistant_task.py`.  
4. Live Python: allow explain id; reject unknown; reject bad `action_id`; confirm `default_safety_gate()` type; snapshot `ArmedAllowlistSafetyGate._ALLOWED_VERBS == ['GO_TO','HOLD','LAND']`.  
5. `git diff --stat` on orchestrator / Continuity / registry / seed → empty.  
6. AST import walk on `safety.py` → no `jarvis.intelligence` import (docstring may mention the module name; imports do not).  
7. Pytest: T4 **8/8**; with T3+T0+T1 **31/31**.

---

## 3. IC checklist (detailed)

### §0.3–0.5 Gate + allow rule + reject reasons — **PASS**

`SoftwareCapabilitySafetyGate` exists with `gate_id = "software_capability"`.

Allow path (product seed): for each id → `get_capability` → must be `AVAILABLE` → `get_provider(provider_id)` → must be `ProviderKind.SOFTWARE`.

Reject reasons observed in code (all five from IC):

| reason | when |
|---|---|
| `unparseable_action_id` | missing/`None` action_id, wrong prefix, empty segments |
| `empty_capabilities` | well-formed `capability:` with no ids |
| `capability_unknown` | id not in `load_default()` |
| `capability_unavailable` | row exists but not `available` |
| `provider_not_software` | no provider or kind ≠ software |

Live: `capability:ontology.explain` → allow; `capability:nope` → `capability_unknown`; `hold:x` → `unparseable_action_id`.

### §0.6 Request encoding — **PASS**

No `SafetyRequest` schema change. Encoding is `capability:<id>` or comma-joined multi. Assistant helper builds `"capability:" + ",".join(capability_ids)`.

### §0.7 Wire order — **PASS**

Both emitters:

```text
build Task
  → T3 _capabilities_known_in_default_registry
  → T4 _software_safety_allows  (explicit SoftwareCapabilitySafetyGate, not default_safety_gate)
  → write task_kind (+ explain_query for explain)
  → return Task
```

T3 kept as separate pre-check (IC preference), so membership refuse stays distinguishable from Safety reject.

### §0.8 On reject — **PASS**

Either failed gate returns `None` **before** any `intent.metadata` write. No raise.

### §0.9 Factory / ArmedAllowlist locks — **PASS**

- `default_safety_gate()` still returns `RejectAllSafetyGate` (live + source).  
- ArmedAllowlist verbs still `GO_TO` / `HOLD` / `LAND` only.  
- Assistant constructs `SoftwareCapabilitySafetyGate()` explicitly; never routes through the default factory.

### §0.10 Fulfill — **PASS**

No changes required to cite fulfill or `_handle_project_status`. Orchestrator zero diff this Buy.

### §0.11 Import fences — **PASS**

- `assistant_task` may import `capabilities.safety` (authorized).  
- `safety.py` imports registry/schemas/intent only (AST).  
- Still no `jarvis.core` / `flight_software` / `vehicle_profiles` from `assistant_task`.

### §0.12 Version / docs — **PASS**

`pyproject` = `0.6.12`; no git tag. Docs: intelligence README T4 section, PLATFORM §10/§12–13, CONNECTIONS extend (no new C-xxx), PRIORIDAD.

### Tests T1–T7 — **PASS**

Suite file has **8** tests (T1–T7 + coverage of gate reasons / happy path). All green. Related T0/T1/T3 suites green together (31).

---

## 4. Notes (non-blocking)

**N1 — T3 test rescoped.**  
`test_gate_does_not_touch_availability_or_providers` now watches `_capabilities_known_in_default_registry` instead of full `try_*`. Correct: T4 adds legitimate `get_provider` / availability reads on the Safety step. Isolation intent of T3 (membership-only helper) preserved; not a weakening of no-dispatch.

**N2 — Docstring vs import.**  
`safety.py` docstring mentions `jarvis.intelligence.assistant_task` as the caller; AST imports do not pull intelligence. Fence is on imports, not prose.

**N3 — UX.**  
With T2 seed present, explain / `estado` still emit Tasks (Safety allow). No CLI surface change expected on ACCEPT.

---

## 5. Risks remaining (honest)

- `handle_explain_intent` can still fulfill cite if `try_*` refuses (pre-T0 pattern; same N2 as T3 review). Soft/Safety gates block **Task emission**, not necessarily that helper’s fulfill. Defer path (orchestrator checks try return) does fall through on refuse.  
- Next vehicle Task kind must **not** reuse this software gate as a shortcut to motors; HOLD/LAND stay on ArmedAllowlist + RejectAll default.

---

## 6. Next

```text
DONE — T4 ★ ACCEPT CLOSED @ v0.6.12
Intelligence tip: Intent→Task→registry→Safety(software)→fulfill
Next Buy: Engineer chooses (vehicle Task DC · Skills · R4 · park · other)
```

**ACCEPT by Engineer.**
