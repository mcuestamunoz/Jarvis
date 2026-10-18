# Engineer lock — Local LLM model for Jarvis (Gemma 4)

**Status:** Design locked (Engineer 2026-10-15) — **not** an Implementation Contract. **Default shipped by CI-1** (`B1-llm-gemma4-default-model`, `0.8.7`, awaiting ★): `OLLAMA_MODEL` default = `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL`  
**Cycle:** Research → Analysis → **Design** (this note). Plan/IC pending Engineer open Buy  
**Machine target:** Mac Apple Silicon M4 · **16 GB** unified memory  
**Authority:** Engineer

---

## Locked product direction

| Item | Lock |
|---|---|
| Role of LLM | Semantic interpreter only (`interpret` JSON + `analyze` narrate). ActionPolicy / Continuity unchanged. **Not** Conversation Engine. **Not** OpenClaw-as-brain. |
| Runtime lab | Prefer **LM Studio (MLX)** or Ollama for smoke; product client remains pluggable (`LLMClient` Protocol). |
| **Daily model** | **Gemma 4 E4B** — Q4 class (`Q4_K_M` Ollama stock **or** Unsloth **`UD-Q4_K_XL`** / QAT when available) |
| **Stretch daily** | **Gemma 4 12B** same quant class — if E4B JSON/ES quality is weak on smoke |
| Parked on 16 GB | Gemma 4 **26B-A4B**, Qwen3.6 **35B-A3B**, default tip `qwen2.5:14b` as long-term daily (tight) |
| Out of this lock | R4 ontology cite · OpenClaw gateway · changing ActionPolicy |

---

## Why E4B first

- Fits 16 GB with headroom (~6–9.5 GB Ollama tags; room for macOS + Jarvis + modest context).
- Fast enough for interactive `--chat` / voice turns.
- MoE giants (26B-A4B / 35B-A3B) load near-full weights → no comfortable daily margin on 16 GB.

**12B** stays the upgrade path if smoke shows E4B failing structured `interpret` JSON or Spanish instruction-following.

---

## Operator smoke (no Buy — env override only)

~~Do **not** change `src/jarvis/config.py` default until a ★ IC.~~ Superseded by CI-1: default is now the Path B E4B tag; env override below remains for trying other tags.

### Path A — Ollama stock (fastest)

```bash
ollama pull gemma4:e4b
# optional stretch:
# ollama pull gemma4:12b

export JARVIS_OLLAMA_MODEL=gemma4:e4b
# run Jarvis --chat as usual; confirm Modelo: line prints gemma4:e4b
```

### Path B — Unsloth `UD-Q4_K_XL` / QAT (preferred quality when stock Q4_K_M is weak)

```bash
# E4B QAT XL (Unsloth via Ollama HF bridge) — verify tag on HF if pull fails
ollama pull hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL

# 12B QAT XL
# ollama pull hf.co/unsloth/gemma-4-12B-it-qat-GGUF:UD-Q4_K_XL

export JARVIS_OLLAMA_MODEL=hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL
```

### Path C — LM Studio MLX (lab)

Download Gemma 4 E4B (or 12B) MLX 4-bit in LM Studio → Start Server → later Buy may add OpenAI-compatible client; today Jarvis speaks **Ollama** `/api/chat` only.

---

## Smoke criteria (Engineer)

1. Model loads without red Memory Pressure under normal apps.
2. `interpret`-shaped turn: Spanish free text → valid JSON action in closed set (or safe fallback, no hang).
3. `analyze`-shaped turn: readable Spanish narration; no invented physics as authority.
4. Latency acceptable for interactive use (order-of-magnitude: not multi-minute).

Pass E4B → keep as candidate default for IC. Fail JSON/ES → retry **12B** same quant. Still fail → revisit Qwen 7–8B (not reopen 26B/35B on 16 GB).

---

## Next Buy (when Engineer opens)

Suggested id: `INV` optional short → `B1-llm-gemma4-default-model` (or DC if runtime client changes).

Minimum IC scope if only default tag changes:

- Default `OLLAMA_MODEL` → locked Gemma 4 tag (E4B or 12B after smoke).
- Docs: README / OPERATOR one-liner; PRIORIDAD cola LLM row.
- Tests: no tip-pin; keep Protocol; stub LLM tests unchanged.
- **STOP** if Buy needs OpenAI-compatible client, OpenClaw, or ActionPolicy widen.

---

## Engineering State note

Current tip PRIORIDAD remains voice **T59 ★** idle. This lock does **not** auto-open a Buy. Engineer must pick LLM cola vs T40 Parked vs other.
