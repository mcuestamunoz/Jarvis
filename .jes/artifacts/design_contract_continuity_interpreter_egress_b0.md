# Design Contract — Continuity Interpreter egress (`DC-continuity-interpreter-egress`)

**Project:** Jarvis  
**Date:** 2026-10-18  
**Author:** JES / Cursor  
**Status:** **DC READY** — Engineer may ★ Intent then open first IC  
**Type:** Design — Layer 2 language compose from Continuity (+ optional ontology cite)  
**Cola:** **CI-2**  
**Parents:**
- [CI-0 DC epoch](design_contract_continuity_interpreter_epoch_b0.md) ★ (locks 3, 4, 6, 7; Open #2 = **B**)  
- Tip **`v0.8.7`** (CI-1…CI-1e ★)  
- [CI-INV-0](investigation_report_voice_llm_ci_audit_b0.md) G-05/G-06 · spoken map  
- Smoke 2026-10-18: situate brief OK; `explicame el margen` still weak analyze; `explicame como funciona la potencia de radio` → acquisition (CI-3 ingress — not this DC’s Buy)

**Not** an Implementation Contract. **Not** permission to edit `src/` until a pasted CI-2 IC. **Not** CI-3 ingress redesign. **Not** Conversation Engine. **Not** T40.

---

## Intent

After Gemma + turn hygiene (CI-1…1e), the product gap is **egress language**:

> Continuity DECIDE (Layer 1). The Continuity Interpreter **composes** short human Spanish from already-computed Continuity fields (and later ontology cites) — chat ∥ voice — without choosing the next gap or inventing physics.

Engineer Open #2 ★: **Option B** — bare `--chat` stays **silent** by default; a **speak opt-in** enables Continuity/interpreter TTS without requiring `--voice-only` mic. `--voice-only` keeps mic + speak-all.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Layer 1 untouched** — `build_startup_context` / Continuity ranking / readiness / gaps remain sole engineering truth. Interpreter never writes ranking or invents gaps/SKU/numbers |
| 2 | **Compose only from computed fields** — situation, next_useful_step, next_useful_why (humanized), readiness headline, optional first gap title; optional ontology **quote** only when a later Buy (CI-R4) supplies a cite. No new Continuity computation in the LLM path |
| 3 | **Deterministic fallback** — `brief_spoken_continuity` / `full_spoken_continuity` / CI-1e `situate` remain valid when LLM compose is off, fails, or times out. Fail closed to extract, never to silence-with-lie |
| 4 | **Surfaces in scope (v1 egress)** — (a) Continuity walls (`project_status` / startup) speak path may use compose **or** keep extract (IC picks one grain); (b) CI-1e `situate` may optionally use compose later — **default: keep deterministic situate**; (c) **not** craft wizard bodies (later IC); (d) **not** folding `analyze` (CI-4) |
| 5 | **Chat ∥ voice (Open #2 = B)** — `--voice-only`: speak Continuity-shaped / interpreter turns as today (speak-as-printed or wall speak). `--chat`: **silent default**; new opt-in flag (exact name in IC, e.g. `--chat --speak` or env) enables TTS for those same Continuity-shaped / interpreter turns **without** opening the mic. Retired hybrid `--chat --voice-speak` must not return |
| 6 | **No ActionPolicy widen** — compose returns language, not create/iterate/calculate/simulate JSON |
| 7 | **Spoken-continuity map** — every new/changed egress surface updated in the same Buy |
| 8 | **Out** — CI-3 explain→ontology ingress · CI-4 analyze fold · CI-5 interpret retire · G-03 test Ollama · T40 · embeddings |

---

## Relation to CI-3 (ingress) — explicit fence

Smoke: `explicame como funciona la potencia de radio` opened acquisition (“Indica la potencia… W”) instead of ontology explain. That is **ingress misroute** → **CI-3**, not CI-2.

CI-2 may still **compose** language for turns that already resolved to Continuity/status/situate. It does **not** reclaim explain-shaped lines from define_params in this DC.

---

## Suggested IC grain (after Engineer ★ this DC)

| Order | Buy | Qué |
|---|---|---|
| **CI-2a** | `B1-continuity-interpreter-egress-speak-opt-in` | Wire Open #2 = B CLI/env; no compose yet — speak path parity for Continuity walls / situate when opt-in |
| **CI-2b** | `B1-continuity-interpreter-egress-compose` | LLM compose short Spanish from Continuity fields for wall speak (and/or situate); stub + live smoke; fallback to extract |

Engineer may collapse 2a+2b into one IC if preferred; default recommendation: **2a then 2b** (speak plumbing before Gemma compose).

---

## Acceptance (design)

- [ ] Engineer ★ Intent on this DC (incl. Open #2 = B restated)  
- [ ] First IC (2a or combined) pasted to Claude  
- [ ] Cola CI-2 → DC ready / IC ready  

---

## Paste for Engineer (★ Intent)

```text
Design — DC-continuity-interpreter-egress (CI-2)
Parent: CI-0 ★ · tip v0.8.7 · Open #2 = B locked
File: .jes/artifacts/design_contract_continuity_interpreter_egress_b0.md

GOAL: Lock egress compose + speak opt-in for Continuity Interpreter.
Layer 1 SoT unchanged. Ingress/explain mapping = CI-3 (out).
Recommend IC grain: CI-2a speak opt-in → CI-2b compose.

Reply "si" / ★ to lock DC and authorize first IC.
```
