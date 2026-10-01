# Implementation Review — Skills runtime software-only (`B1-capability-skills-runtime-software`)

**Date:** 2026-10-01  
**Reviewer:** Cursor (independent pass — Engineer pasted Claude T21 push summary)  
**Against:** [IC](implementation_contract_capability_skills_runtime_software_b1.md) · [report](implementation_report_capability_skills_runtime_software_b1.md) · [DC ★](design_contract_capability_skills_runtime_software_b0.md)  
**Tip reviewed:** `65a0c2f` on `cursor/skills-runtime-impl-8ac5` (parent tip T20 ★ `v0.6.29` @ `ca22362`)  
**Verdict:** **PASS WITH NOTES** — package ready for Engineer ★ ACCEPT → tag **`v0.6.30`**. **No ACCEPT claim from Cursor.** Closes today’s T18–T21 software block pending ★.

**Process note:** Claude Code implemented. Same-session implementer green is not review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Vehicle/ops Skills become runnable | **Clear** — stay `stub`; `run_skill` → `skill_stub` (T3) |
| Chat rewired Skill-first | **Clear** — `assistant_task` / orch classify untouched; T5 asserts no `run_skill` in assistant_task |
| New Continuity ranking in capabilities | **Clear** — no ranking; status via optional provider |
| `capabilities` → `core` import | **Clear** — none (AST) |
| Tip pins / ESC fence | **Clear** — T17 + ESC helpers green |
| Unisolated orch test picking real workspace | **Clear** — `tmp_path` (report + T2b) |

---

## 1. IC checklist

| Lock | Verdict |
|---|---|
| §0.2 two Skills → `available`; others stub | **PASS** |
| §0.3 `run_skill` + finite SkillRunResult outcomes | **PASS** |
| §0.4 explain → `fulfill_ontology_explain`; status → Continuity-shaped data / `no_project` | **PASS (N2)** |
| §0.5 T4-shaped software Safety before run | **PASS** |
| §0.6 Chat Task classify unchanged | **PASS** |
| §0.7 Vehicle/ops → `skill_stub` | **PASS** |
| §0.8 version `0.6.30` · docs · no new C-xxx | **PASS** |
| §0.9 Out: copper · CHARGE · tip pins · Skill-first rewrite | **PASS** |

---

## 2. Verification (this pass)

- T21 suite + T5 seed retarget + tip-pin guardrail + CHARGE regression: **22 passed**.
- AST: module-level imports stay in `capabilities`/`typing`/`pydantic`; sole `intelligence` import is **lazy** inside `run_skill` for `fulfill_ontology_explain`. Zero `jarvis.core` import lines.

---

## 3. Notes

**N1 — First `capabilities → intelligence` edge (accepted).** IC/DC name `fulfill_ontology_explain` and place the runner in `capabilities/skills_runtime.py`. Lazy import is the minimal honest way to reuse that path. Documented in report. **Not blocking.** Moving the runner later would be a separate architectural Buy.

**N2 — `project_status` via injectable provider.** Avoids `capabilities → core`. Without provider → `no_project`. With provider, message is currently `str(ctx)` (or whatever the callable returns) — not a second Continuity ranker, and not a byte-copy of `_handle_project_status` Spanish. Correct layering for this Buy; Skill-first can pass a provider that returns the same user-facing string as defer fulfill. **Not blocking.**

**N3 — Process.** Await Engineer ★ ACCEPT → tag `v0.6.30`. After ★: today’s T18–T21 block closed; next horizon **Skill-first chat** (then voz/world). SD-GO_TO remains OPEN debt.

---

## 4. Next

```text
Cursor review: PASS WITH NOTES @ 65a0c2f
Await Engineer ★ ACCEPT → tag v0.6.30
Then: Skill-first chat DC/IC (next block) — not auto-AUTHORIZED
```
