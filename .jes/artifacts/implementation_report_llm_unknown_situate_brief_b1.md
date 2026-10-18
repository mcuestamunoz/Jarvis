# Implementation Report — Unknown → brief situate (`B1-llm-unknown-situate-brief`, CI-1e)

**Project:** Jarvis
**Date:** 2026-10-18
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_llm_unknown_situate_brief_b1.md)
**Parent:** [CI-1d IC](implementation_contract_llm_unknown_situate_b1.md) · [CI-1d review](implementation_review_llm_unknown_situate_b1.md) (egress REJECT) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) · tip `v0.8.6` · tree `0.8.7` untagged
**Status:** **Implemented — awaiting Cursor review / Engineer ★.** No ACCEPT claimed.
**Package:** stays **`0.8.7`** (no bump).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | New `_handle_situate()` (next to `_handle_project_status`): returns `{"status": "ok", "action": "situate", "message": …}` built from `build_startup_context()` only. CI-1d early claim and the CI-1c backstop now call it instead of `_handle_project_status()`. Claim condition unchanged (unknown + active project + not `is_explain_ask` → 0 LLM). |
| `src/jarvis/adapters/cli/main.py` | `render_response`: `action == "situate"` → message only (no `Acción ejecutada`), checked before the `ok` branch. |
| `tests/test_llm_unknown_situate_brief_b1.py` | **new** — T1–T6 |
| `tests/test_llm_unknown_situate_b1.py` · `tests/test_llm_interpret_unknown_guard_b1.py` | `project_status` expectations → `situate` (+ lead assertion); docstrings note CI-1e |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | New **Unknown-line situate** row (must-speak-brief, speak-as-printed); CI-1d trigger retracted from the `project_status` row; tip line updated |
| cola CI · PRIORIDAD · `engineering_state.json` | CI-1e → Implemented / awaiting review |

**Message shape** (each line omitted when its field is absent; closed-project example):

```text
No capté una orden clara.
Proyecto: transporte de carga.
Física orientativa en PASS, pero el sistema aún tiene gaps de componentes.
Siguiente paso: Define el componente pendiente: esc.
Estado del proyecto: no listo para ensamblar.
```

**Untouched:** `_handle_project_status` / `estado` (full wall), Continuity builders/ranking, ActionPolicy, prompts, `DEFAULT_OLLAMA_MODEL`, voice adapters (speak path already speak-as-printed for non-`project_status` actions), `pyproject.toml`.

## 2. Decisions

1. **`next_useful_why` left out** (lock 5d allows it "if already available without new subsystem"). The field can be a raw warning code whose humanizer (`_humanize_next_useful_why`) lives in `adapters/cli/main.py`; its docstring states core stays free of adapter display maps. Importing it into core would invert the layering; the why can also be several sentences, which defeats "brief".
2. **Project line = `objective`, falling back to `project_slug`** — one short line, never the header block.
3. **Readiness copy** matches the voice brief (T51): `Estado del proyecto: listo / no listo para ensamblar.` from `readiness.overall == "ASSEMBLY_READY"`.
4. **No `startup_context` on the result** (lock 4 optional) — print and speech use `message` only, so nothing downstream can fall back to the wall. `attach_project_coherence` ignores `situate` (not in its action set), so no footer is appended (T3 renders after `attach_project_coherence`).
5. Bug 54 side effect of `_handle_project_status` (persisting `pending_define_missing` from `proactive_question`) intentionally **not** reproduced: the situate reply asks no question.

## 3. Tests

| ID | What it proves |
|---|---|
| T1 | `hablar` / `gracias` / `hola` + `_RefuseLLM` → `situate`, first line is the lead, contains the project's `situation` and `next_useful_step`, readiness one-liner, ≤ 6 lines, none of `ENGINEERING READINESS` / `TOP GAPS` / `Conceptos` / `Componentes` / `Evidencia` / `PROJECT STATUS`; no `startup_context` |
| T2 | 0 interpret / 0 analyze (counting stub would return `create_project`), no wizard copy, IDLE |
| T3 | `render_response` (after `attach_project_coherence`) == message; no `Acción ejecutada` |
| T4 | `estado` → `project_status`, wall markers present (`ENGINEERING READINESS`, `TOP GAPS`, `Situación:`), no situate lead |
| T5 | `explicame el margen` → analyze, no plan; `nuevo` → create wizard; `poco margen` → FN-022 |
| T6 | `qué es el margen` (unknown, explain-shaped) → analyze, no situate lead |

Executed: the three CI-1c/1d/1e files → 33 passed. **Full suite: 4144 passed, 10 skipped** (1:18).

## 4. Remaining risks

- **Live smoke not run** (IC §0): `hablar`/`gracias` → brief situate, no wall, no new `llm_logs` row; `estado` → full wall; `explicame el margen` → analyze.
- The broad-claim trade from CI-1d stays: real but unclassified requests on an active project (`añadir un motor`, `cuanto pesa`, a typed component spec) now get this brief situate instead of an LLM turn — shorter than CI-1d's wall, same routing. CI-3 territory.
- `situation` / `next_useful_step` strings are Continuity's own; if one is long, the brief is long — no truncation (would be inventing).
- G-03 still open.
