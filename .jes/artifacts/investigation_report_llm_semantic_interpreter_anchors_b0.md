# Investigation Report — LLM today + semantic-interpreter anchor options

**Buy id:** `INV-llm-semantic-interpreter-anchors` (informal B0 — Cursor Research/Analyze)  
**Date:** 2026-10-15  
**Author:** Cursor (Engineering Agent) — **no `src/`**  
**Status:** FINDINGS → Engineer ★ Design locked into [DC-continuity-interpreter-epoch](design_contract_continuity_interpreter_epoch_b0.md) (2026-10-15 “si”)  
**Parents:**
- [Engineer lock — Gemma 4 local model](engineer_lock_llm_gemma4_local_model_b0.md)
- [`docs/system_map/10_llm/LLM_MAP.md`](../../docs/system_map/10_llm/LLM_MAP.md)
- [`docs/system_map/AUTHORITY.md`](../../docs/system_map/AUTHORITY.md)
- [`docs/FASE_LLM.md`](../../docs/FASE_LLM.md) (HISTORICAL principle; live SoT = ActionPolicy)
- Knowledge vision R4 Later — [`JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md) §7 (b)
- Tip idle after **T59 ★** @ `v0.8.6`

**Type:** Investigation — map as-is LLM role + ranked **anchor points** for a semantic-interpreter evolution.  
**Not:** Implementation · Conversation Engine · widening ActionPolicy · OpenClaw-as-brain · changing default model in config (separate Buy after Gemma smoke).

---

## 1) Executive picture

Jarvis already has a **bounded LLM**, not a blank chat brain:

```text
Skills / Continuity / Acquisition / Goal plan / patterns
        ↓ (claim the turn first — 0 LLM)
Intent resolver (deterministic)
        ↓ (only if nothing claimed)
LLM interpret → ActionPolicy (4 verbs) → handle()
   or
LLM analyze  → string narration only (never routing)
```

The product gap is **not** “add an LLM.” It is: **where** natural language still leaks past deterministic layers, and **which existing seams** should become the semantic interpreter without inventing a second authority.

**Naming trap (already in system_map M-003):**

| Name | Path | Role today |
|---|---|---|
| `SemanticIntentAdapter` | `llm/semantic_intent_adapter.py` | Gate **LLM iterate JSON → wizard preseed** (confidence, aliases, grounding) |
| `semantic_interpreter` | `core/semantic_interpreter.py` | **Rule-based** slot fill inside iterate wizard (C-053) — **0 LLM** |

Any Design must say which one we grow — or introduce a third name under `intelligence/` with an explicit fence.

---

## 2) As-is: what the LLM does today

### 2.1 Two modes (live)

| Mode | Entry | Output | Authority |
|---|---|---|---|
| **`interpret`** | Last resort in `_handle_user_text_inner` after globals/modes/intent/local actions | JSON → `ActionRequest` in `{create_project, iterate, calculate, simulate}` | `ActionPolicy` + parser; invalid → safe fallback (`simulate` + `invalid_llm_output`) |
| **`analyze`** | Intent `analyze` / soft paths / explore miss / unknown→fake-iterate demotion | Spanish **string** | Must **not** choose gap/goal/next step (structurally: return type is str) |

Connections: **C-100…C-104** 🟢.

### 2.2 Pipeline order (authority before LLM)

From `ARCHITECTURE.md` / orchestrator (simplified):

1. `_handle_global_commands` — escape, nuevo, **explain**, Continuity defer, vehicle/ops **Skills** (Skill-first T22–T31)  
2. Active session modes (create / iterate / define_missing / system_definition)  
3. IDLE Acquisition Target gates  
4. `intent_resolver` patterns (GUIDANCE before ANALYZE, etc.)  
5. FN-022 / FN-025 engineering intent → goal plan (**0 LLM**)  
6. Local `resolve_action_request` / DSE explore / apply  
7. **`llm_interface.interpret`** — last resort  
8. Bug 52: unknown + LLM says iterate → demote to **`analyze`**

### 2.3 What is already “semantic interpreter–shaped”

| Piece | Status | Notes |
|---|---|---|
| Closed action set | ★ solid | 4 verbs only |
| `SemanticIntentAdapter` + `CONFIDENCE_THRESHOLD=0.75` | ★ calibrated 2026-08-05 | Lexical grounding cap; battery Wh G27 |
| `_semantic_preseed` | ★ | High confidence → wizard step 2 |
| Rule `semantic_interpreter` in wizard | ★ | Slots operation/variable/value — deterministic |
| `goal_context` into `analyze` | ★ | Quote-only |
| Ontology explain (A0–A7, R2/R3) | ★ | **0 LLM**; R4 cite = Later |
| Voice / spoken Continuity | ★ T59 | Explicit **no LLM** in Layer 2 |

### 2.4 Known residual edges (LLM still reached / leak smell)

Documented residuals (not all open bugs):

- Wrong-block-while-wizard LLM leak (acquisition UX residuals in IMPLEMENTATION_TASKS)  
- Phrases that miss pattern tables → fall through to `interpret`  
- `analyze` for causal / comparative questions (legitimate) vs accidental analyze from Bug 52  
- Default model still `qwen2.5:14b` until Gemma Buy — orthogonal to architecture  

**Map verdict:** LLM subsystem boundary holds; pain is **ingress claiming**, not ActionPolicy failure.

---

## 3) What “migrate to semantic interpreter” should mean (options)

Engineer Intent (this session): grow from a **specific-purpose LLM** toward a **semantic interpreter** that **joins Jarvis pieces** — without becoming SoT.

Proposed product sentence (for Design lock):

```text
El LLM interpreta lenguaje libre hacia contratos ya existentes
(Skills, Tasks, ActionRequest, Continuity cite). Nunca elige
el siguiente paso de ingeniería ni inventa física.
```

Three incompatible Design directions (pick one primary):

| Direction | Meaning | Risk |
|---|---|---|
| **A — Strengthen last-resort interpret** | Better model + prompts + adapter coverage for the 4 verbs | Small; stays FASE_LLM |
| **B — NL → existing Skills/Tasks** | Free text maps to Skill ids / Task kinds already in registry (explain, status, HOLD…) before ActionPolicy | Medium; must not bypass Safety |
| **C — NL → Continuity / Acquisition slots** | LLM proposes block/param/goal labels validated by Continuity/goal_planner | High authority smell — only if output is **proposal** validated by deterministic detectors |

**Recommendation for first Design:** **A + thin B**, never C as decision authority. R4 cite is a separate thin additive on `analyze`.

---

## 4) Anchor points (ranked)

An **anchor** = existing module/seam where a Buy can attach interpreter behavior with clear In/Out and tests.

### A1 — Last-resort `interpret` + Gemma (ops + quality)

| | |
|---|---|
| **Where** | `OllamaClient` / default model · `PromptBuilder` · logs in `runtime/llm_logs/` |
| **Why** | Model lock already started (Gemma 4 E4B); smoke validates JSON/ES |
| **Buy grain** | Default model tag + smoke criteria (see engineer_lock) |
| **Does not** | Change ActionPolicy · add verbs |
| **Priority** | **P0** — unblocks honest local use |

### A2 — `SemanticIntentAdapter` expansion (iterate vocabulary)

| | |
|---|---|
| **Where** | `llm/semantic_intent_adapter.py` · PARAMETER_REQUIREMENTS aliases |
| **Why** | Already the gate between LLM iterate and wizard; calibrated |
| **Buy grain** | More aliases / grounding rules / domain-scoped resolvers (pattern of G27) |
| **Does not** | Slot-fill inside wizard (that is `core/semantic_interpreter`) |
| **Priority** | **P1** — improves “quiero más X” without new architecture |

### A3 — Intent miss → structured interpret (not freestyle chat)

| | |
|---|---|
| **Where** | Orchestrator fallthrough before/around line that calls `interpret` |
| **Why** | Today unknown text hits LLM; joining pieces means classifying *what kind of miss* |
| **Buy grain** | Typed miss reasons → route to Continuity / explain / clarify template **0 LLM** when possible; else interpret |
| **Does not** | Conversation Engine |
| **Priority** | **P1** — reduces accidental LLM |

### A4 — Skill-first NL bridge (thin B)

| | |
|---|---|
| **Where** | `_handle_global_commands` / `assistant_task` / `run_skill` |
| **Why** | Twelve Skills already own explain/status/vehicle/ops; voice uses same brain |
| **Buy grain** | Finite phrase table **or** LLM→`skill_id` proposal validated against registry allow-list |
| **Does not** | LLM calling `submit_command` without Safety · inventing Skill ids |
| **Priority** | **P2** — “une piezas” without new subsystem |

### A5 — R4 ontology cite in `analyze` (vision §7 b)

| | |
|---|---|
| **Where** | `JarvisLLMInterface.analyze` + `intelligence/` retrieve (exact id only today) |
| **Why** | Narration can quote solid notes beside `goal_context`; vault never decides |
| **Buy grain** | Optional cite payload into analyze prompt; ActionPolicy unchanged |
| **Does not** | RAG/embeddings · Continuity reading vault to choose next step |
| **Priority** | **P2** — Later in PRIORIDAD; good after A1 stable |

### A6 — Unify naming / fence `semantic_*` (docs + optional thin module)

| | |
|---|---|
| **Where** | Docs + maybe `intelligence/semantic_ingress.py` facade |
| **Why** | Two “semantic” modules confuse Buys |
| **Buy grain** | Docs-first; facade only if A3/A4 need a single entry |
| **Does not** | Merge rule interpreter with LLM adapter |
| **Priority** | **P3** — hygiene when A3/A4 open |

### Parked (not anchors for v1 interpreter)

| Candidate | Why parked |
|---|---|
| OpenClaw / agent gateway | Competes with orchestrator authority |
| LLM → Acquisition target / goal pick | Forbidden by ActionPolicy + AUTHORITY |
| Embeddings / RAG retrieve | Explicitly out of intelligence/ R2 design |
| Growing `core/semantic_interpreter` with LLM calls | Would mix 0-LLM wizard with model — wrong layer |
| T40 craft/`world/` voice | Own DC; not LLM cola |

---

## 5) Recommended Design path (for Engineer pick)

```text
Phase 0  A1  Gemma default + smoke interpret/analyze   (ops)
Phase 1  A3  Miss taxonomy / claim-before-LLM          (less leak)
Phase 2  A2  Adapter aliases / grounding                (iterate quality)
Phase 3  A4  Optional Skill-id allow-list bridge        (join Skills)
Phase 4  A5  R4 cite                                    (knowledge)
```

**Join-the-pieces story:** Skills + Continuity + Action Router stay SoT; LLM is the **ingress translator** into those contracts when patterns miss.

**Stop conditions:** any Buy that needs a 5th ActionPolicy verb, LLM-chosen `next_useful_step`, or embeddings → STOP and reopen Design.

---

## 5b) Engineer Intent restatement (2026-10-15) — Continuity bilingual bridge

Engineer clarified the desired interpreter (not primarily “better ActionPolicy JSON”):

> Capacidad de **unir piezas**, **mapear el lenguaje de Jarvis ↔ lenguaje humano**, y **dar la Continuity**.

| Phrase | Jarvis meaning |
|---|---|
| **Unir piezas** | Compose already-computed facts (Continuity situation / next / why, readiness, Skill results, optional ontology cite) into one coherent human turn — **not** invent a second SoT |
| **Lenguaje Jarvis → humano** | Egress: engineering vocabulary (`next_useful_step`, gaps, ASSEMBLY READY, OP≠intrinsic, …) → Spanish a human can follow |
| **Humano → lenguaje Jarvis** | Ingress: free Spanish → existing contracts (status phrases, Skill ids, iterate variables, explain topics) |
| **Dar la Continuity** | The human always leaves knowing *dónde está el proyecto* and *qué toca* — Project Continuity / Coherence product contract |

**Relation to what already shipped**

- Layer 1 Continuity (screen) = engineering **truth** (`build_project_continuity`).  
- Layer 2 spoken (T45–T52) = **deterministic** extract/narrate — DC lock: *“Sin LLM… LLM later = semantic interpreter of entrada.”*  
- `analyze` today = partial egress narrator, not Continuity composer.  
- `interpret` today = last-resort **action** ingress (4 verbs) — necessary, but **not** the heart of this Intent.

**Reframed Design target (pending Engineer ★ lock)**

```text
Intérprete semántico = puente bilingüe Continuity ↔ humano
  · Ingress: humano → contratos Jarvis (Skills / status / iterate / explain)
  · Egress:  piezas Jarvis → Continuity hablada/escrita humana
  · Unir:    componer piezas ya calculadas; nunca decidir next_useful_step
```

Primary anchors for **this** Intent shift toward:

| Priority | Anchor | Role for bilingual Continuity |
|---|---|---|
| P0 | **A1** Gemma | Runtime that can narrate/interpret in ES |
| P1 | **Egress Continuity composer** (new thin seam — not rewrite Continuity) | Join situation+next+why[+readiness/cite] for chat/voice; Layer 1 untouched |
| P1 | **A3 / A4 ingress** | Human → Jarvis vocabulary / Skills before ActionPolicy |
| P2 | **A5 R4 cite** | Optional “why” vocabulary from ontology inside egress |
| Support | **A2** | Iterate variable mapping (human↔PARAMETER_REQUIREMENTS) |

**Fence (unchanged):** Continuity **decides**; LLM **translates and composes language**. If a Buy would let the model choose `next_useful_step`, STOP.

This restatement does **not** reopen T44-DC Layer 2 (still 0-LLM extract). A future DC must say explicitly whether egress LLM is **additive opt-in** (e.g. richer chat Continuity tell) or stays deterministic forever for voice brief.

---

## 5c) Engineer Design pressure (2026-10-15) — Voice∥Chat + new LLM role; retire old?

Engineer (this turn):

> TODO a partir de ahora va en **voz**, en paralelo **chat y voz**. TODO.  
> Esto ya no es la versión anterior del LLM — función **completamente nueva**.  
> Revisar si **eliminar** la función LLM actual.  
> Si es intérprete, la **ontology** aporta la teoría determinista.

### Product surface implication

| Old (shipped) | Proposed (Engineer pressure) |
|---|---|
| Chat text + optional voice; Layer 2 Continuity **0-LLM** extract; LLM = last-resort `interpret`/`analyze` | **Every** product turn: chat **and** voice in parallel; LLM = **Continuity bilingual interpreter** (new role) |
| T44-DC: “LLM later = semantic *ingress* only” | Egress Continuity language **also** in scope for LLM (amends voice locks — needs ★ DC) |
| T53 two-mode: `--chat` silent screen · `--voice-only` mic | Still two modes, but **both** speak Continuity / brain egress — not “voice is Skills-only orphan” |

This is a **new epoch**, not a Gemma tag swap. Requires its own **DC** before any delete/implement Buy.

### Can we delete today’s LLM (`interpret` / `analyze`)?

| Piece | Job today | Replaced by ontology? | If deleted without replacement |
|---|---|---|---|
| **`interpret`** → 4 verbs | Last-resort NL → `ActionRequest` when patterns/Skills miss | **No.** Ontology **explains** concepts; it does not emit `iterate`/`calculate` or choose gaps | Free-text mutate/calc/sim falls into “no se pudo interpretar” or forces endless pattern tables |
| **`analyze`** | Causal/comparative narration | **Partially.** Theory cites can come from ontology retrieve; *project-specific* “por qué este gap” still needs Continuity facts | Lose free-form Q&A; Continuity composer can cover *project* talk better than analyze ever did |
| **`SemanticIntentAdapter`** | Validate LLM iterate → wizard | N/A if interpret gone; still useful if any NL→variable path remains | — |
| **ActionPolicy** | Structural fence | Keep forever even if call sites shrink | — |

**Honest recommendation:** do **not** delete `interpret` on day one. **Demote / quarantine**:

1. New interpreter owns Continuity bilingual (ingress+egress) for chat∥voice.  
2. Ontology + Continuity + Skills claim turns first (already true).  
3. `analyze` → fold into Continuity egress composer (retire as separate product mode).  
4. `interpret` → **Parked residual** or allow-list-only until pattern/Skill coverage proves unused (measure `runtime/llm_logs/` routing); then delete in a dedicated Buy with suite proof of 0 call sites.

Deleting now = architectural leap without evidence that deterministic ingress covers 100% of craft Spanish.

### Ontology’s real role in the new picture

```text
ontology/     EXPLAINS theory (deterministic retrieve — already R2/R3)
Continuity    DECIDES next craft step (0 LLM)
library/      DECLARES SKU facts
LLM (new)     TRANSLATES + COMPOSES language Continuity↔humano (voice∥chat)
LLM (old)     Action JSON last resort — candidate to shrink/retire after proof
```

Ontology is fuel for **egress vocabulary** and explain Skills — **not** a substitute ActionPolicy.

### Epoch name (suggested)

**Continuity Interpreter epoch** — voice∥chat parallel; bilingual bridge; old FASE_LLM modes demoted.

---

## 6) Open questions for Engineer (updated)

1. ★ Lock epoch: **Continuity Interpreter** = primary LLM role; chat∥voice parallel for Continuity egress — yes/no?  
2. Amend T44/T52 “Layer 2 no LLM”: allow LLM **compose** of Continuity language while Layer 1 dict stays SoT — yes/no?  
3. Retire policy: **quarantine** `interpret` (measure→delete later) vs **delete now**?  
4. First artifact: **DC-continuity-interpreter-voice-chat** (no code) before Gemma default IC?  
5. Rename product surface to avoid `semantic_interpreter` clash?

---

## 7) Suggested next artifacts (when Engineer opens)

| If pick | Next artifact |
|---|---|
| Lock path A+thin B | `design_contract_llm_semantic_interpreter_b0.md` |
| Only model | `implementation_contract_llm_gemma4_default_model_b1.md` |
| Miss taxonomy | `investigation_contract` or DC for A3 |
| Update focus | PRIORIDAD row + short cola note `engineer_note_llm_interpreter_cola.md` |

---

## 8) Evidence index

- `src/jarvis/llm/{llm_client,action_policy,semantic_intent_adapter,ollama_client,prompt_builder,response_parser}.py`  
- `src/jarvis/core/semantic_interpreter.py` (wizard slots)  
- `src/jarvis/core/orchestrator.py` — fallthrough `interpret`; `_semantic_preseed`; `_handle_analyze`  
- `docs/system_map/10_llm/LLM_MAP.md`, `AUTHORITY.md`, CONNECTIONS C-100–C-104, C-053  
- Calibration: `.jes/artifacts/calibration_summary.md` (FASE_LLM 2026-08-05)

---

*End of investigation report — awaiting Engineer Design pick on §6.*
