# Implementation Review — Chat Skill-first software Skills (`B1-assistant-chat-skill-first-software`)

**Date:** 2026-10-01  
**Reviewer:** Cursor (forensic pass — Engineer: “Lanza review y pasa a accept si está todo correcto”)  
**Against:** [IC](implementation_contract_assistant_chat_skill_first_software_b1.md) · [report](implementation_report_assistant_chat_skill_first_software_b1.md) · [DC ★](design_contract_assistant_chat_skill_first_b0.md)  
**Tip reviewed:** `a3b23ea` on `cursor/skill-first-software-impl-8ac5` (parent tip T21 ★ `v0.6.30` @ `0cb9fe9`)  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES**. Package/tag **`0.6.31` / `v0.6.31`**. Closes Skill-first **phase A** (software).

**Process note:** Cursor implemented under Engineer “ejecutalo tú”. Same-session implementer green is not normally review of record; Engineer explicitly ordered review + ACCEPT this turn — this pass is the review of record under that authority.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Explain bypasses `run_skill` on chat seam | **Clear** — `handle_explain_intent` calls `run_skill("skill.explain_concept")`; T4 AST: no direct `fulfill_ontology_explain` in that function |
| Status silently falls back on hard Skill reject | **Clear** — orch gates on `skill_stub` / `safety_reject` / `unknown_skill` with honest message; `ok` / `no_project` → `_handle_project_status` |
| Second Continuity ranker in capabilities | **Clear** — provider is `build_startup_context`; display SoT stays `_handle_project_status` |
| Vehicle/ops/CHARGE rewired Skill-first | **Clear** — T3: `hold`/`charge` Task-direct; no `skill.request_*` calls |
| Tip pins / invented Skill availability | **Clear** — T5 + tip-pin guardrail; vehicle Skills stay `stub` |
| Package tip | **Clear** — `pyproject.toml` = `0.6.31` |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 explain UX from `run_skill(…explain…).message` on ok | **PASS** |
| §0.3 status gated by `run_skill(…project_status…)` + Continuity shape/side effects | **PASS** |
| §0.4 optional runtime polish only | **PASS** — `ontology_root` passthrough |
| §0.5 vehicle/arm/ops/CHARGE unchanged | **PASS** |
| §0.6 tests T1–T5 | **PASS** |
| §0.7 version `0.6.31` · docs · no new C-xxx | **PASS** |
| §0.8 Out: vehicle Skill-first · voice · inventing availability · tip pins | **PASS** |

---

## 2. Verification (this pass)

```text
pytest tests/test_assistant_chat_skill_first_software_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_assistant_ops_charge_task_b1.py \
  tests/test_assistant_vehicle_hold_task_b1.py \
  tests/test_assistant_explain_task_b1.py \
  tests/test_assistant_defer_continuity_b1.py -q
→ 42 passed
```

- `handle_explain_intent` → `run_skill("skill.explain_concept", query=…, ontology_root=…)`.
- Continuity defer → `run_skill("skill.project_status", project_status_provider=build_startup_context)` then `_handle_project_status` on non-hard-reject.
- Software Skills `available`; vehicle/ops Skills remain `stub`.

---

## 3. Notes

**N1 — Stale T21 module prose in `skills_runtime.py`.** Top docstring still says chat classify is unchanged / Skill-first is “the next block.” Behavior matches T22; prose is historical. **Not blocking** — optional cleanup in a later Buy (vehicle Skill-first can refresh it).

**N2 — Status Skill message vs orch UX.** Gate uses `run_skill` + provider; user-facing Continuity body still comes from `_handle_project_status` (same as IC lock 3). Skill `message=str(ctx)` is unused for chat UX. Correct layering; same pattern candidate for vehicle Skill-first (gate then orch fulfill). **Not blocking.**

**N3 — Process.** Engineer ★ ACCEPT applied → tag `v0.6.31`. Phase A CLOSED. Next: phase B vehicle Skill-first (HOLD-first slice) — must **not** route vehicle Skills through `SoftwareCapabilitySafetyGate` alone (`flight.*` is vehicle/`not_implemented`).

---

## 4. Next

```text
★ ACCEPT CLOSED @ v0.6.31 (Engineer 2026-10-01)
Skill-first phase A (software) CLOSED
Next: T23 B1-assistant-chat-skill-first-vehicle-hold @ 0.6.32
```
