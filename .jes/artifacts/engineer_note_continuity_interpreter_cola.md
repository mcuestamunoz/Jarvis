# Engineer note — Continuity Interpreter cola (CI)

**Status:** **OPEN living cola** — tip **`v0.8.7`** ★ (CI-1…CI-1e CLOSED) · **CI-2 DC READY** (await Engineer ★ Intent) · **CI-INV-0 PASS WITH NOTES**  
**Authority:** Engineer ★ Intent 2026-10-15 · Open #2 = **B opt-in** (2026-10-18)  
**SoT DC:** [design_contract_continuity_interpreter_epoch_b0.md](design_contract_continuity_interpreter_epoch_b0.md)  
**CI-2 DC:** [design_contract_continuity_interpreter_egress_b0.md](design_contract_continuity_interpreter_egress_b0.md)  
**INV (anchors):** [investigation_report_llm_semantic_interpreter_anchors_b0.md](investigation_report_llm_semantic_interpreter_anchors_b0.md)  
**INV (audit):** [investigation_review_voice_llm_ci_audit_b0.md](investigation_review_voice_llm_ci_audit_b0.md)  
**Model lock:** [engineer_lock_llm_gemma4_local_model_b0.md](engineer_lock_llm_gemma4_local_model_b0.md)  
**Tip:** **`v0.8.7`**

---

## Product sentence

```text
Continuity DECIDE · Ontology EXPLICA · Skills HACEN
LLM = Continuity Interpreter (chat ∥ voice) — traduce y compone lenguaje
```

---

## Cola

| # | Buy | Estado | Qué | Gate |
|---|---|---|---|---|
| **CI-0** | `DC-continuity-interpreter-epoch` | ✅ **DC ready** ★ | Epoch locks | [DC](design_contract_continuity_interpreter_epoch_b0.md) |
| **CI-INV-0** | `INV-voice-llm-ci-audit` | **PASS WITH NOTES** ★ findings | Voice+LLM audit | [review](investigation_review_voice_llm_ci_audit_b0.md) |
| **CI-1** | `B1-llm-gemma4-default-model` | ✅ ★ **ACCEPT CLOSED** @ **`v0.8.7`** | Default Gemma E4B | [review](implementation_review_llm_gemma4_default_model_b1.md) |
| **CI-1b** | `B1-llm-analyze-goal-smoke-hotfix` | ✅ ★ **ACCEPT CLOSED** @ **`v0.8.7`** | Bare margen / explain-gate / prefill | [review](implementation_review_llm_analyze_goal_smoke_hotfix_b1.md) |
| **CI-1c** | `B1-llm-interpret-unknown-guard` | ✅ ★ **ACCEPT CLOSED** @ **`v0.8.7`** | No create wizard on unknown | [review](implementation_review_llm_interpret_unknown_guard_b1.md) |
| **CI-1d** | `B1-llm-unknown-situate` | ✅ ★ **ACCEPT CLOSED** (claim) @ **`v0.8.7`** · egress superseded by CI-1e | 0 LLM claim | [review](implementation_review_llm_unknown_situate_b1.md) |
| **CI-1e** | `B1-llm-unknown-situate-brief` | ✅ ★ **ACCEPT CLOSED** @ **`v0.8.7`** | Brief `situate` message | [review](implementation_review_llm_unknown_situate_brief_b1.md) |
| **CI-2** | `DC-continuity-interpreter-egress` | **DC READY** · await ★ Intent | Egress compose + speak opt-in (B) | [DC](design_contract_continuity_interpreter_egress_b0.md) |
| **CI-3** | Continuity Interpreter **ingress** | ☐ pending | Explain→ontology / claim-before; smoke radio-power misroute | after CI-2 |
| **CI-4** | Fold `analyze` into CI | ☐ later | Quarantine old analyze | after CI-2 |
| **CI-5** | Retire `interpret` | ☐ later | Measure first — **blocked** G-03/G-04 | measure → IC |
| **CI-R4** | Ontology cite in compose | ☐ later | R4 quote-only | after CI-2 |
| **T40** | craft/`world/` voice | Parked | Own DC | — |

---

## Process

```text
CI-0 ★ → CI-1…1e ★ @ v0.8.7 → CI-2 DC ★ → CI-2a/2b IC → CI-3 …
```

Claude implements ICs. Cursor writes/refines DC/IC + review. No `src/` without pasted IC.
