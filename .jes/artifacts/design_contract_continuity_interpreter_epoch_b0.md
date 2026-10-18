# Design Contract — Continuity Interpreter epoch (`DC-continuity-interpreter-epoch`)

**Project:** Jarvis  
**Date:** 2026-10-15  
**Author:** JES / Cursor  
**Status:** **DC ready** — Engineer ★ locked Intent (“si” 2026-10-15)  
**Type:** Epoch / block lock — new LLM product role + chat∥voice Continuity  
**Cola:** **CI-0** (Continuity Interpreter)  
**Parents:**
- [INV anchors + §5b/§5c](investigation_report_llm_semantic_interpreter_anchors_b0.md)  
- [Engineer lock — Gemma 4 local](engineer_lock_llm_gemma4_local_model_b0.md)  
- [T44-DC spoken continuity](design_contract_assistant_chat_spoken_continuity_b0.md) · [T52-DC FULL spoken](design_contract_assistant_voice_full_spoken_b0.md)  
- [T53-DC two-mode product](design_contract_assistant_voice_two_mode_product_b0.md)  
- [`AUTHORITY.md`](../../docs/system_map/AUTHORITY.md) · [`LLM_MAP.md`](../../docs/system_map/10_llm/LLM_MAP.md) · [`JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md)  
- Tip idle **`v0.8.6`** (T59 ★) — this DC does **not** bump package

**Not** an Implementation Contract. **Not** permission to edit `src/` until a pasted IC. **Not** Conversation Engine. **Not** T40/`world/`. **Not** immediate deletion of ActionPolicy.

---

## Intent (Engineer ★)

> TODO a partir de ahora va en **voz**, en paralelo **chat y voz**.  
> El LLM tiene una función **completamente nueva** — no es FASE_LLM “último recurso”.  
> Intérprete: **unir piezas**, mapear **lenguaje Jarvis ↔ humano**, **dar Continuity**.  
> Ontology aporta teoría determinista.  
> Revisar retiro del LLM actual → **cuarentena**, no delete día 1.

Product sentence:

```text
Continuity DECIDE. Ontology EXPLICA. Skills HACEN.
El Continuity Interpreter TRADUCE y COMPONE lenguaje
(humano ↔ Jarvis) en chat y voz en paralelo —
sin elegir next_useful_step ni inventar física.
```

---

## Epoch name

**Continuity Interpreter** (CI) — replaces “FASE_LLM as product story” for new Buys.  
Old modules may remain as **quarantined residual** until measured unused.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Primary LLM role** = Continuity Interpreter (bilingual bridge + piece composer). Not OpenClaw-as-brain. Not Conversation Engine. |
| 2 | **Layer 1 SoT** = Continuity / readiness / project dicts and render path. Screen engineering truth **unchanged** as authority. Interpreter never writes Continuity ranking or invents gaps. |
| 3 | **Layer 2 language** = may use LLM to **compose** human Spanish from Layer 1 fields (+ optional ontology cites). Amends T44 lock 2 / T52 “no LLM” **for language compose only**. Deterministic extract (T45–T52) remains valid fallback and regression baseline. |
| 4 | **Chat ∥ voice parallel** = Continuity-shaped egress is spoken **and** printed in both product modes (`--chat` and `--voice-only`) once CI Buys ship. “TODO” = Continuity walls + interpreter turns; craft wizard body speak policy = per later IC (not silent forever, not T40). |
| 5 | **Ingress** = human Spanish → existing contracts only: Skills / status-Continuity phrases / explain / (later) iterate variables via adapter. Prefer claim-before-LLM. |
| 6 | **Egress** = compose situation · next_useful_step · why · readiness headline · optional first gap title · optional ontology cite — from **already computed** fields. Join pieces; do not decide which gap wins. |
| 7 | **Ontology** = EXPLAINS (retrieve exact / R3 topics / future R4 cite into compose). Never Continuity decision input. Never SKU invention. |
| 8 | **ActionPolicy** stays the structural fence for any residual action JSON. No 5th verb without a separate ★ DC. |
| 9 | **Quarantine old LLM product modes** — `analyze` as standalone product story → fold into CI egress. `interpret` (4-verb last resort) → **quarantined**: keep code path; measure `runtime/llm_logs/`; delete only in a dedicated Buy after evidence of near-zero useful calls + ingress coverage. |
| 10 | **Runtime model** = Gemma 4 E4B (stretch 12B) per [engineer_lock](engineer_lock_llm_gemma4_local_model_b0.md); smoke before default-config IC. |
| 11 | **Naming** — product docs say **Continuity Interpreter**. Do not overload `core/semantic_interpreter` (wizard slots, 0-LLM) or silently rename `SemanticIntentAdapter` without an IC. |
| 12 | **Out of this epoch DC** — T40 craft/`world/` · OpenClaw gateway · embeddings/RAG · widening ActionPolicy · deleting ActionPolicy · silicon/HD |

---

## Amendment to prior voice locks

| Prior | Amendment under this DC |
|---|---|
| T44 lock 2: “No LLM in Layer 2” | **Superseded for CI Buys:** LLM may compose Layer 2 **language** from Layer 1 fields. Layer 1 remains sole engineering truth. |
| T52: FULL narrated Layer 2 0-LLM | Deterministic FULL remains shipped baseline. CI may **add** optional richer compose behind IC; must not break Layer 1 or invent facts. |
| T53: `--chat` print-only brain vs `--voice-only` | Modes remain two CLI surfaces; CI requires **spoken Continuity** on the path Engineer uses daily — exact CLI flags / default speak = per first CI IC. |

Historical T45–T59 ★ ACCEPT stays valid for what shipped; new behavior needs new ICs.

---

## Cola (CI) — ordered

| # | Buy | Type | Package | Qué | Gate |
|---|---|---|---|---|---|
| **CI-0** | **This DC** | DC | docs | Epoch locks | Engineer ★ Intent (done) |
| **CI-1** | `B1-llm-gemma4-default-model` | IC | tip+1 | Default/runtime Gemma 4 E4B (or 12B after smoke); env documented | Smoke ES + JSON/compose |
| **CI-2** | `DC/B1-continuity-interpreter-egress` | DC→IC | tip+ | Layer 2 compose from Continuity fields; chat∥voice speak; Layer 1 untouched | IC paste |
| **CI-3** | `DC/B1-continuity-interpreter-ingress` | DC→IC | tip+ | Human → Skills/status/explain claim-before residual | IC paste |
| **CI-4** | `B1-llm-analyze-fold` / quarantine note | IC | tip+ | Retire `analyze` as product mode into CI egress | After CI-2 |
| **CI-5** | `B1-llm-interpret-retire` | IC | later | Delete/quarantine-hard `interpret` after log evidence | Measure first |
| **CI-R4** | R4 ontology cite into compose | IC | later | Quote-only cites | After CI-2 |
| — | **T40** | — | — | Parked | Own DC |

Each step independently ★-able. **No `src/` until CI-1 (or later) IC is pasted.**

---

## Forbidden claims

- Continuity Interpreter chooses `next_useful_step`  
- Ontology replaces catalog or Continuity  
- LLM invents mass/W/thrust/SKU  
- OpenClaw is the Jarvis brain  
- “Delete interpret today” without CI-5 evidence  
- Conversation Engine / unbounded free chat as product

---

## Opens (Engineer)

1. First IC to paste: **CI-1** (Gemma default) vs **CI-2** DC detail first? → **resolved:** CI-1 first (in flight through CI-1e).  
2. Should bare `--chat` **always** speak Continuity after CI-2, or opt-in flag retained? → **★ locked 2026-10-18 — Option B (opt-in):** `--chat` stays silent by default; a speak flag/mode (exact CLI in CI-2 DC/IC) enables Continuity TTS without requiring `--voice-only` mic. `--voice-only` keeps mic + speak-all. Not A (always speak) nor C (Continuity-only speak on bare chat).

---

## SoT pointers

- INV: [investigation_report_llm_semantic_interpreter_anchors_b0.md](investigation_report_llm_semantic_interpreter_anchors_b0.md)  
- Cola note: [engineer_note_continuity_interpreter_cola.md](engineer_note_continuity_interpreter_cola.md)  
- PRIORIDAD: [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md)  
- Spoken map: still update on any chat/Continuity/`render_*` Buy ([`CLAUDE.md`](../../CLAUDE.md))
