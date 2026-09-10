# Engineer note — LLM pending deactivate / cleanup map

**Date:** 2026-09-10  
**Authority:** Engineer — “el LLM no sirve de nada, solo molesta”; local collapse + slow + useless reply; evaluate **desactivar**  
**Status:** PENDING REVIEW — not PRIORIDAD code · not an IC · map first, then ★ deactivate / strip  
**Parents:** Project identity (LLM = language interface, not engineering SoT) · IDLE `6 standoffs` LLM jump · Continuity spatial assembly

---

## Stance (Engineer)

As Jarvis is designed (deterministic writers, Continuity, catalog assists, Board bridges):

- Structured phrases that already parse **must not** fall to the LLM.  
- LLM replies are often useless, slow (local), and can stall the machine.  
- **Pending:** review **deactivating** the LLM path; if ★'d, clean call sites deliberately — do not leave dead “LLM will handle it” fallthroughs.

This is **not** “Conversation Engine.” It is removing or gating an interface that no longer earns its cost.

---

## Why now

Field: IDLE `6 standoffs` → LLM instead of G-N1 `upsert_frame_part`.  
Pattern: every missing IDLE bridge becomes an LLM trap. Closing bridges shrinks the need; remaining LLM use looks like noise.

---

## Map before cleanup (inventory when ★ deactivate)

Locate every use so a future strip/gate IC can be complete. Expected surfaces (confirm live before deleting):

| Area | Likely files / symbols | Role today |
|---|---|---|
| CLI turn loop | `adapters/cli/main.py` — LLM client construct / pass into orchestrator | Process entry |
| Orchestrator fallthrough | `core/orchestrator.py` — `handle_user_text` / IDLE branches that call `llm_interface` when no bridge matches | **Main trap** |
| Intent / narration | `llm_interface` (or equivalent), semantic helpers that still call generate | Soft intent / copy |
| CREATE / wizards | any path that requires LLM to advance DEFINE/CREATE | May block deactivate if still load-bearing |
| Tests | mocks/`_RefuseLLM` / suites that assert “LLM must not be called” | Regression fence |
| Config / deps | `pyproject.toml`, env keys, local model launch docs | Install/runtime weight |
| Docs | README / ARCHITECTURE claims “LLM interprets intent” | Honesty after deactivate |

**Method when ★:** grep `llm_interface`, `.generate(`, `LLM`, `ollama`, `openai`, refuse-LLM tests; produce a one-page inventory artifact; then IC: gate (hard refuse + honest copy) vs full remove.

---

## Explicit non-goals (until ★)

Do not deactivate in the Board drag Buy. Do not invent Conversation Engine. Do not weaken deterministic bridges to “make LLM useful.”

---

## Related cola

- [IDLE frame-part count](engineer_note_idle_frame_part_count_declare.md) — closes one LLM trap  
- Board drag → pose uses **no** LLM (writer bridge only) — correct pattern
