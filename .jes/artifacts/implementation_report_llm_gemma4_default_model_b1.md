# Implementation Report — Gemma 4 E4B default model (`B1-llm-gemma4-default-model`, CI-1)

**Project:** Jarvis
**Date:** 2026-10-15
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_llm_gemma4_default_model_b1.md)
**Parent:** tip `v0.8.6` · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) · [Gemma lock](engineer_lock_llm_gemma4_local_model_b0.md)
**Status:** **Implemented — awaiting Cursor review / Engineer ★.** No ACCEPT claimed.
**Package:** `0.8.6` → **`0.8.7`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/config.py` | New `DEFAULT_OLLAMA_MODEL = "hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL"`; `OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)`. Override semantics unchanged. |
| `tests/test_main_cli.py` | Three `OllamaClient(model="qwen2.5:14b")` fixtures → `DEFAULT_OLLAMA_MODEL`. Assertions untouched. |
| `tests/test_llm_gemma4_default_model_b1.py` | **new** T1/T2/T4 |
| `README.md` · `src/jarvis/README.md` | Default model line → Gemma tag (+ `ollama pull` hint). |
| `pyproject.toml` | `0.8.7` |
| cola CI · Gemma lock · PRIORIDAD · `engineering_state.json` | CI-1 → Implemented / awaiting review; lock notes default shipped (operator "don't change default" line superseded). |

**Untouched:** orchestrator, ActionPolicy, Continuity, voice Layer 2, `prompt_builder`, temperature/timeout defaults, `OllamaClient` code. Spoken-continuity map: no new surface (the existing `Modelo:` banner only prints a different value) → not updated.

## 2. Tests

| ID | What it proves |
|---|---|
| T1 | `DEFAULT_OLLAMA_MODEL` equals the locked tag; with `JARVIS_OLLAMA_MODEL` unset, `config.OLLAMA_MODEL` and `OllamaClient().model` are the tag (subprocess — no in-process `config` reload) |
| T2 | `JARVIS_OLLAMA_MODEL=other-tag` → config and client use `other-tag`; explicit constructor `model=` still honoured |
| T3 | No live Ollama: all HTTP stubbed / no network; no tip/package version pin |
| T4 | `README.md` and `src/jarvis/README.md` contain the Gemma tag and no `qwen2.5:14b` |

Executed: targeted `tests/test_llm_gemma4_default_model_b1.py tests/test_main_cli.py` → 35 passed. Full suite: 4096 passed, 9 skipped (§4).

## 3. Remaining risks

- Live smoke (Engineer, at ACCEPT): `--chat` banner shows the Gemma tag; one status turn + one `interpret`/`analyze` turn with no hang. Not covered by pytest.
- Operators who never pulled the tag get the existing "No se pudo conectar / model not found" path from Ollama; they can `ollama pull` or set `JARVIS_OLLAMA_MODEL`.
- Historical artifacts (`calibration_summary.md`, INV) still mention `qwen2.5:14b` as history — intentionally not rewritten.
- `src/jarvis.egg-info/PKG-INFO` is generated and stale until reinstall.

## 4. Full suite

`python -m pytest -q -x` → **4096 passed, 9 skipped** (22:40). No failures.
