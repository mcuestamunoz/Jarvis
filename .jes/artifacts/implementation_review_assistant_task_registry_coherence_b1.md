# Implementation Review — Assistant Task ↔ registry coherence (`B1-assistant-task-registry-coherence`)

**Date:** 2026-09-30  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_assistant_task_registry_coherence_b1.md) · [report](implementation_report_assistant_task_registry_coherence_b1.md) · T2 DC §0.7  
**Verdict:** **★ ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review **PASS**. Package/tag **`0.6.11` / `v0.6.11`**.

---

## Summary

T3 adds membership-only soft gate `_capabilities_known_in_default_registry` on both Task emitters: build Task → check `load_default().get_capability` → then metadata + return, or `None` with no `task_kind`. Package `0.6.11`; no premature tag. Parent tip `v0.6.10` held.

Independent checks:

- Read both `try_*` call sites against IC §0.4 / §1 ordering.
- Ran T3 suite: **7/7 PASS**; T3+T0+T1+T2: **31/31 PASS**.
- Confirmed zero diff this Buy on `orchestrator.py`, `default_registry.json`, `registry.py` (aside from caller-side import into `assistant_task`).

---

## IC checklist

| Lock | Verdict |
|---|---|
| §0.2 Shared helper on both try_* | **PASS** |
| §0.3 Membership via `load_default().get_capability` | **PASS** |
| §0.4 Order: Task → check → metadata; refuse = None, no task_kind | **PASS** |
| §0.5 Soft ≠ dispatch (no availability / providers) | **PASS** (extra test) |
| §0.6 Import edge authorized; reverse fence held | **PASS** (T5) |
| §0.7 Happy path with T2 seed | **PASS** (T1–T2) |
| §0.8 Orchestrator untouched | **PASS** |
| §0.9–0.10 Package `0.6.11` · docs · no new C-xxx | **PASS** |
| Tests T1–T6 | **PASS** |

---

## Notes (non-blocking)

**N1 — T2 `test_t6b` supersession.** Removing the “assistant_task must not import registry” half is correct: T2 DC §0.7 deferred that edge to this IC. Reverse fence kept. Not a weakening.

**N2 — `handle_explain_intent` still fulfills if `try_*` refuses.** Pre-T0 pattern ignores try return and always fulfills explain-shaped lines. Soft gate blocks **Task emission**, not cite fulfill via that helper. Defer path (orchestrator checks try return) does refuse fallthrough. Matches “soft on Task”; optional later tighten if wanted.

---

## Next

```text
DONE — T3 ★ ACCEPT CLOSED @ v0.6.11
Next: T4 B1-assistant-software-safety-bridge IC READY FOR ★
```

**ACCEPT by Engineer.**
