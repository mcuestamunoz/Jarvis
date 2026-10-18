# Implementation Contract — Gemma 4 E4B default model (`B1-llm-gemma4-default-model`)

**Project:** Jarvis  
**Date:** 2026-10-15  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.7`**

**Status:** Cursor review **PASS WITH NOTES** — awaiting Engineer ★ ACCEPT + tag **`v0.8.7`** (live smoke N1). [review](implementation_review_llm_gemma4_default_model_b1.md)  
**Parents:** [CI-0 DC ★](design_contract_continuity_interpreter_epoch_b0.md) · [Gemma lock](engineer_lock_llm_gemma4_local_model_b0.md) · [cola CI](engineer_note_continuity_interpreter_cola.md) · tip **`v0.8.6`**  
**Type:** Change default Ollama model tag to Unsloth Gemma 4 E4B QAT `UD-Q4_K_XL`; document operator env; bump package. **No** Continuity Interpreter compose yet (CI-2).  
**Opens:** **`0.8.7` / `v0.8.7`**. **Cola:** **CI-1**

**Not:** CI-2 egress compose · CI-3 ingress · deleting `interpret`/`analyze` · ActionPolicy change · OpenAI-compatible client · OpenClaw · T40 · Conversation Engine · new C-xxx.

---

## Why this Buy

CI epoch needs a local model that fits M4 16 GB and speaks Spanish / JSON. Operator smoke (2026-10-15) on the machine:

- Tag installed: `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` (~5.2 GB)  
- Spanish one-shot reply OK  
- `format: json` → `{"action":"calculate","parameters":{}}` OK  

Repo default is still `qwen2.5:14b` (tight on 16 GB, deleted locally). CI-1 makes the locked Gemma tag the product default.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-llm-gemma4-default-model`**. Package/tag **`0.8.7` / `v0.8.7`** |
| 2 | Default `OLLAMA_MODEL` / `JARVIS_OLLAMA_MODEL` fallback → **`hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL`** exactly (same string as `ollama list`) |
| 3 | Env override **`JARVIS_OLLAMA_MODEL`** still wins (unchanged semantics) |
| 4 | Docs that cite `qwen2.5:14b` as **default** → Gemma tag (README / `src/jarvis/README.md` operator bits only — no VISION rewrite) |
| 5 | Tests that hardcode `qwen2.5:14b` as constructor arg for `OllamaClient` → use the new default constant or an explicit test string; **no tip/package version pins** |
| 6 | PRIORIDAD · CI cola · `engineering_state` · Gemma engineer_lock note “default still qwen” → updated to shipped |
| 7 | **Out** — CI-2 compose · prompt rewrite · ActionPolicy · changing temperature/timeout defaults · adding MLX/OpenAI client |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | Default `OLLAMA_MODEL` → Gemma Unsloth tag |
| `tests/test_main_cli.py` (and any other hardcoded `qwen2.5:14b` defaults) | Align with new default or keep explicit fixtures without claiming old product default |
| `README.md` · `src/jarvis/README.md` | Default model line |
| `pyproject.toml` | `0.8.6` → **`0.8.7`** |
| `.jes/artifacts/engineer_note_continuity_interpreter_cola.md` | CI-1 → Implemented / awaiting review |
| `.jes/artifacts/engineer_lock_llm_gemma4_local_model_b0.md` | Note default shipped (or “superseded by CI-1”) |
| `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD · `.jes/state/engineering_state.json` | CI-1 state |

Do **not** touch orchestrator, ActionPolicy, Continuity, voice Layer 2 compose, prompt_builder schema.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `OLLAMA_MODEL` default (no env) equals the locked Gemma tag string |
| T2 | With `JARVIS_OLLAMA_MODEL=other-tag`, config/client uses override (existing pattern if present; add if missing) |
| T3 | No tip-pin / no suite requirement that Ollama is running; unit-level only |
| T4 | `pyproject` **0.8.7**; PRIORIDAD/cola/state coherent; grep product docs no longer claim `qwen2.5:14b` as **default** |

Live Engineer smoke (ACCEPT, not pytest):

```bash
# ollama list shows the Gemma tag
export JARVIS_OLLAMA_MODEL=hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL   # optional after default ships
python -m jarvis.adapters.cli.main --chat
# banner Modelo: <gemma tag>
# one Continuity/status turn + one phrase that may hit interpret/analyze — no hang
```

---

## 3. Acceptance

- [ ] Default without env → Gemma Unsloth tag  
- [ ] Override env still works  
- [ ] Docs + cola + PRIORIDAD + `0.8.7`  
- [ ] Cursor review · Engineer ★ · tag **`v0.8.7`**

---

## 4. Paste for Claude

```text
Implementation — B1-llm-gemma4-default-model (CI-1)
Parent: CI-0 DC Continuity Interpreter epoch ★.
Package → 0.8.7 / tag v0.8.7.

IC: .jes/artifacts/implementation_contract_llm_gemma4_default_model_b1.md
Locks: engineer_lock_llm_gemma4_local_model_b0.md
Cola: engineer_note_continuity_interpreter_cola.md

GOAL: Product default Ollama model =
hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL
(JARVIS_OLLAMA_MODEL override unchanged). Docs + tests +
PRIORIDAD/cola/state. Operator smoke already passed ES + JSON.

DO:
- config.py default tag
- Fix hardcoded qwen2.5:14b default claims in tests/docs
- pyproject 0.8.7 · cola CI-1 · PRIORIDAD · state
- Tests T1–T4 (no live Ollama required in pytest)
- Implementation report
- No ACCEPT claim

NO: CI-2 compose · CI-3 ingress · delete interpret/analyze ·
ActionPolicy · prompt schema · OpenAI/MLX client · T40
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires changing ActionPolicy, Continuity compose, or retiring `interpret`.
