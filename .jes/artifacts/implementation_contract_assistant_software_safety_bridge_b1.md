# Implementation Contract — Assistant software Safety bridge (`B1-assistant-software-safety-bridge`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** — only after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer ACCEPT → tag **`v0.6.12`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS; package/tag **`0.6.12` / `v0.6.12`**.
**Parents:**
- T3 [`B1-assistant-task-registry-coherence`](implementation_contract_assistant_task_registry_coherence_b1.md) — ★ **ACCEPT CLOSED** @ **`v0.6.11`** — membership soft-check before Task emit
- T2 registry seed ★ CLOSED @ **`v0.6.10`** — `ontology.explain` / `engineering.continuity` as `available` software
- C2 / C17 Safety stack — `SafetyGate` / `SafetyRequest` / `default_safety_gate()` → **RejectAll** (unchanged this Buy); `ArmedAllowlistSafetyGate` stays autonomy-verb opt-in only
- Vision: [`PLATFORM_CAPABILITY_VISION.md`](../../docs/PLATFORM_CAPABILITY_VISION.md) §10–§12 — Intent → Task → capability → **Safety** → provider; Assistant never motors
- Tip / package parent: **`v0.6.11` / `0.6.11`**

**Type:** **First Assistant→Safety link for software Tasks** — after registry membership, a Task is emitted only if a dedicated **software** Safety gate allows it. Still not a dispatcher, not vehicle verbs, not `default_safety_gate` change.  
**Opens:** **`0.6.12` / `v0.6.12`** on Engineer ACCEPT.  
**Cola:** **T4**

**Not:** HOLD/LAND/GO_TO · arming ArmedAllowlist · changing `default_safety_gate()` · voice/world · R4 · Skills catalog · JES-in-product · Continuity ranking · UX copy changes when seed present.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-assistant-software-safety-bridge`** |
| 2 | Why | Vision chain needs Safety between capability and fulfill. Membership (T3) is not Safety. This Buy proves the link for **software-only** Tasks already in product |
| 3 | New gate | Add `SoftwareCapabilitySafetyGate` in `jarvis.capabilities.safety` (name fixed). Implements `SafetyGate`. **`gate_id = "software_capability"`** |
| 4 | Allow rule | `allow` iff every capability id encoded in the request (see §1) exists in `CapabilityRegistry.load_default()`, has `availability == available`, and its bound provider (via `capability.provider_id` → `get_provider`) has `kind == software`. Empty id list → `reject` |
| 5 | Reject reasons (finite) | Prefer stable strings: `capability_unknown` · `capability_unavailable` · `provider_not_software` · `unparseable_action_id` · `empty_capabilities` (IC may use a subset if one check collapses; document exact set in report) |
| 6 | Request encoding | Reuse `SafetyRequest` **without** schema fork: `action_id` shape **`capability:<id>`** for one id, or **`capability:<id1>,<id2>`** for multiple (comma-separated, no spaces). `intent_id` = Task’s `intent_id`. Do **not** add fields to `SafetyRequest` this Buy |
| 7 | Where wired | Inside `assistant_task` **after** T3 membership helper passes and **before** writing `task_kind` / returning Task — both `try_explain_concept_task` and `try_defer_to_continuity_task`. Prefer one private helper e.g. `_software_safety_allows(intent_id, capability_ids) -> bool` |
| 8 | On reject | Return `None` (no Task), **no** `task_kind` written — same refuse grain as T3 |
| 9 | Factory lock | **`default_safety_gate()` stays RejectAll.** Do **not** route Assistant through it. Do **not** modify `ArmedAllowlistSafetyGate` allow-list. Software gate is constructed explicitly where Assistant needs it |
| 10 | Fulfill | Unchanged when allow: cite / `_handle_project_status` paths stay as T0/T1. Gate does not fulfill |
| 11 | Import | `assistant_task` may import `jarvis.capabilities.safety` (gate + `SafetyRequest`). Still no `jarvis.core` / FS / vehicle_profiles. `safety.py` must not import `jarvis.intelligence` |
| 12 | Version / docs | Bump **`0.6.12`**; intelligence README T4 section · PLATFORM §10/§12–13 one-liner · CONNECTIONS extend T3 note (**no new C-xxx**) · PRIORIDAD T4 |

**Product sentence:**

```text
Task software solo se emite si SoftwareCapabilitySafetyGate allow —
mismo UX hoy; cadena Vision Intent→Task→capability→Safety visible
sin tocar vuelo ni default RejectAll.
```

---

## 1. Normative shapes

**action_id:**

```text
capability:ontology.explain
capability:engineering.continuity
capability:ontology.explain,engineering.continuity   # if ever multi
```

**Gate evaluate sketch:**

```python
class SoftwareCapabilitySafetyGate:
    gate_id = "software_capability"

    def evaluate(self, request: SafetyRequest) -> SafetyDecision:
        ids = _parse_capability_action_id(request.action_id)  # or reject unparseable
        ...
        return SafetyDecision(outcome="allow"|"reject", reason=..., gate_id=self.gate_id)
```

**Assistant wire (both try_*):**

```text
T3 membership pass
  → build Task
  → SoftwareCapabilitySafetyGate().evaluate(SafetyRequest(intent_id=..., action_id="capability:"+id))
  → if not allow: return None
  → write task_kind; return Task
```

(T3 membership may stay as a cheap pre-check **or** be folded into the gate’s `capability_unknown` path — prefer **keep T3 helper then Safety**, so refuse reasons stay distinguishable in tests.)

---

## 2. Files (expected)

| Area | Path | Change |
|---|---|---|
| Safety | `src/jarvis/capabilities/safety.py` (+ `__init__` exports) | `SoftwareCapabilitySafetyGate` + parse helper |
| Assistant | `src/jarvis/intelligence/assistant_task.py` | Wire gate after T3, before metadata |
| Tests | `tests/test_assistant_software_safety_bridge_b1.py` (**new**) | T1–T7 |
| Version | `pyproject.toml` | `0.6.12` |
| Docs | README · PLATFORM · CONNECTIONS · PRIORIDAD | §0.12 |

Do **not** change `default_registry.json` seed shape. Do **not** change orchestrator unless a test requires it (prefer gate entirely inside `assistant_task`).

---

## 3. Tests

| ID | Assert |
|---|---|
| T1 | With product seed: explain Intent → Task (allow); defer `estado` → Task (allow) |
| T2 | Gate alone: `action_id="capability:ontology.explain"` → `allow`, `gate_id=software_capability` |
| T3 | Gate alone: unknown id / stub-only fixture → `reject` (not allow) |
| T4 | Monkeypatch registry empty (or missing ids): both try_* → `None`, no `task_kind` |
| T5 | `default_safety_gate()` still returns `RejectAllSafetyGate`; ArmedAllowlist allow-list unchanged (HOLD/LAND/GO_TO only as today) |
| T6 | AST: `assistant_task` may import `capabilities.safety`; no core/FS/vehicle_profiles; `safety.py` does not import `intelligence` |
| T7 | `pyproject` reads `0.6.12` |

Bump stale `0.6.11` checkpoints forward.

---

## 4. Acceptance

- [ ] `SoftwareCapabilitySafetyGate` shipped; Assistant wires it for both Task kinds  
- [ ] Happy path UX unchanged with T2 seed · refuse on unknown/unavailable  
- [ ] `default_safety_gate` / ArmedAllowlist / FS paths untouched  
- [ ] Tests T1–T7 · report · docs · package `0.6.12`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.12`**

---

## 5. Paste for Claude (only after Engineer ★)

```text
★ AUTHORIZED implementation — B1-assistant-software-safety-bridge (T4)

IC: .jes/artifacts/implementation_contract_assistant_software_safety_bridge_b1.md
Parents: T3 ★ CLOSED @ v0.6.11; PLATFORM vision §10 Safety between capability and provider

Add SoftwareCapabilitySafetyGate (gate_id=software_capability) in
capabilities/safety.py. Allow iff every capability id in action_id
"capability:<id>[,<id>...]" is in load_default(), availability==available,
and bound provider kind==software. Reject with finite reasons otherwise.
Wire in assistant_task AFTER T3 membership check, BEFORE task_kind write,
on both try_explain_concept_task and try_defer_to_continuity_task.
Do NOT change default_safety_gate() (still RejectAll) or ArmedAllowlist.
No vehicle verbs, no orchestrator require, no registry seed change.
Tests T1–T7. Bump pyproject to 0.6.12. Docs + PRIORIDAD. Report.
No ACCEPT claim.
```

---

## 6. Engineer gate

★ **AUTHORIZED** — Claude implements now.  
Tag **`v0.6.12`** only after Cursor review + Engineer ACCEPT.
