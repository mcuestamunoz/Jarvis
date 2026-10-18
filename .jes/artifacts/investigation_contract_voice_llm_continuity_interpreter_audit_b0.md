# Investigation Contract — Voice + LLM / Continuity Interpreter audit (`INV-voice-llm-ci-audit`)

**Project:** Jarvis  
**Date:** 2026-10-16  
**Author:** JES / Cursor — **INV only**  
**Investigator:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ★ on findings  

**Status:** **IC READY** — Engineer may paste to Claude.  
**Type:** **Investigation** (read-only) — exhaustive forensic audit of (A) voice phase tip state, (B) LLM + Continuity Interpreter epoch, (C) ranked gaps + **next real obvious step** vs the locked CI roadmap.  
**Cola id:** **CI-INV-0** (audit) · may ship as one report with three parts **or** three sibling reports (same Buy).  
**Package:** tip stays **`v0.8.6`** for this INV (docs/report only). Tree may contain untagged **`0.8.7`** (CI-1/CI-1b) — **document that drift**; do **not** bump or tag.  

**Not** an Implementation Contract. **Not** permission to edit `src/`. **No ACCEPT claim.** **No** Conversation Engine. **No** T40 unpark unless live evidence forces a recommendation (expect: stay Parked).

---

## Why this INV now

Two colas sit at an epoch boundary:

| Cola | Tip claim | Reality pressure |
|---|---|---|
| **Voice** (T34–T59) | Daily path ★ closed @ **`v0.8.6`** | Layer 2 still **0-LLM** extract; product modes Chat \| Voice-only |
| **CI** (Continuity Interpreter) | [CI-0 DC ★](design_contract_continuity_interpreter_epoch_b0.md) | Chat∥voice + LLM **compose** language; CI-1 ACCEPT **REJECTED** on smoke; CI-1b **Implemented awaiting review** |

Engineer Intent (locked): LLM is no longer FASE_LLM “last resort” as product story — it is the **Continuity Interpreter** (unir piezas, Jarvis↔humano, dar Continuity) on **chat ∥ voice**. Ontology EXPLAINS; Continuity DECIDES.

This INV must produce an evidence-based map of **what is shipped**, **what contradicts the new epoch**, **what gaps block the roadmap**, and the **single next obvious step** (not a wishlist).

---

## Parents (must read)

### Voice
- [cola voz](engineer_note_voice_phase_c_cola.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
- [T34-DC](design_contract_assistant_chat_voice_channels_b0.md) · [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [T52-DC](design_contract_assistant_voice_full_spoken_b0.md) · [T53-DC](design_contract_assistant_voice_two_mode_product_b0.md)  
- [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) · [FN-017](engineer_note_voice_spoken_polish_field_fn017.md)  
- [T48-inv](investigation_contract_assistant_voice_phase_t_review_b0.md) / [T48 review](investigation_review_assistant_voice_phase_t_review_b0.md) — prior forensic pattern  
- [T59 review ★](implementation_review_assistant_voice_blank_stt_take_b1.md)

### LLM / CI
- [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) · [cola CI](engineer_note_continuity_interpreter_cola.md)  
- [INV anchors](investigation_report_llm_semantic_interpreter_anchors_b0.md) · [Gemma lock](engineer_lock_llm_gemma4_local_model_b0.md)  
- [CI-1 IC/report/review](implementation_contract_llm_gemma4_default_model_b1.md) · [CI-1b IC/report](implementation_contract_llm_analyze_goal_smoke_hotfix_b1.md)  
- [`LLM_MAP.md`](../../docs/system_map/10_llm/LLM_MAP.md) · [`AUTHORITY.md`](../../docs/system_map/AUTHORITY.md) · [`FASE_LLM.md`](../../docs/FASE_LLM.md) (historical principle only)  
- [`JARVIS_KNOWLEDGE_VISION.md`](../../docs/JARVIS_KNOWLEDGE_VISION.md) §7 (R4 Later)

### Process / tip
- [`IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD · [`.jes/state/engineering_state.json`](../state/engineering_state.json) · [`CLAUDE.md`](../../CLAUDE.md) spoken-map norm

---

## 0. Scope lock

**In (read-only):**
- All voice artifacts T34–T59 + tip `src/jarvis/adapters/voice/`, CLI voice/chat entrypoints, spoken Continuity helpers, guide § voice  
- All LLM modules under `src/jarvis/llm/`, orchestrator LLM call sites (`interpret`/`analyze`/`_semantic_preseed`), `goal_planner.detect_goal` / analyze prepend, Skills claim-before-LLM path  
- CI epoch artifacts CI-0…CI-1b and cola CI rows CI-2…CI-5 / CI-R4 / T40  
- Package/tip drift (`pyproject` vs last ★ tag vs cola Estado)

**Out forever (this INV):**
- Any `src/` / product edit · ACCEPT claims · wake-word · OpenClaw-as-brain · embeddings/RAG · unparking T40 without evidence · implementing CI-2 · deleting `interpret` · silicon/HD · craft montage redesign

**Parallel note:** CI-1b may be mid Cursor review. Audit **tip tree as found**; if CI-1b lands mid-INV, cite both pre/post if visible — do not wait for Engineer ★ to start Block A.

---

## Block A — Voice phase forensic (exhaustive)

### A questions

| # | Question |
|---|---|
| **A1 — Cola truth T34–T59** | For every cola row: Estado vs report/review vs tip code vs Engineer ★ ACCEPT yes/no. Flag drift (esp. DC “ready” vs consumed, hybrid retired by T53). |
| **A2 — Product modes today** | Against tip `main.py` / voice adapters: exact CLI surfaces for **Chat** (`--chat`) and **Voice-only** (`--voice-only`). What remains of hybrid / `--voice` Skills-only / fixture paths? Brain source (`TERMINAL`/`VOICE`), speaks when, Continuity Layer 2 when. Cite file:line. |
| **A3 — Layer 1 / Layer 2 inventory** | Reconcile [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md) with tip: every Continuity / `--chat` / `render_*` egress class (`must-speak-brief` / `speak-on-request` / `screen-only`). Any stale/missing row since T59? |
| **A4 — DC lock matrix** | Walk numbered locks in T34-DC, T44-DC, T52-DC, T53-DC, T54–T56 DCs against tip. Flag: still true / amended by CI-0 / drifted / never wired. **Especially:** T44 lock “No LLM in Layer 2” vs CI-0 amendment (LLM may compose language). |
| **A5 — Operator journey gaps** | What still hurts daily Spanish voice: STT language, blank takes, cancel/settle/keys, silence cut, echo, craft wizards mid-voice, Continuity speak vs print honesty? Separate **product gap** vs **Parked (T40)**. |
| **A6 — Honesty fences** | Re-verify: no `"voice"` AuthoritySource; external STT/TTS fail-closed; ESC/tip-pin policy; blank-STT path; no silent success on speech errors. |
| **A7 — Voice vs full chat brain** | On `--voice-only`, does the brain see the **same** Continuity/craft/LLM fallthrough as `--chat`? Any Skills-only leftover? Cite. |
| **A8 — Open N-notes harvest** | From T53–T59 reviews (+ residual T48–T52 if still open): list N-notes remediated vs open. |

### A method
1. Read cola + each ★ review/report off disk.  
2. Read `adapters/cli/main.py` argparse + voice loop + speak path — cite lines.  
3. Grep: `voice-only`, `FULL_CONTINUITY`, `spoken_continuity`, `sanitize_for_speech`, `is_blank_stt`.  
4. Do **not** trust CI-0 prose for what voice code does — prove A4 conflict with citations.

### A deliverable
`.jes/artifacts/investigation_report_voice_llm_ci_audit_part_a_voice_b0.md`  
(or Part A inside a single combined report)

---

## Block B — LLM + Continuity Interpreter epoch (exhaustive)

### B questions

| # | Question |
|---|---|
| **B1 — As-is LLM call graph** | Map every live path to `interpret` / `analyze` / stub refusal: orchestrator sites, CLI, voice, MCP if any. Order relative to Skills / Continuity / Acquisition / FN-022. Cite C-100–C-104 + file:line. |
| **B2 — Two “semantic” modules** | Document `llm/semantic_intent_adapter.py` vs `core/semantic_interpreter.py` (callers, LLM yes/no, relation to CI product name). |
| **B3 — ActionPolicy fence** | Confirm closed 4-verb set still structural; forbidden usurpers still impossible. Any leak smell where analyze/plan prepend steers product (CI-1 smoke class). |
| **B4 — CI-0 lock vs tip** | For each CI-0 numbered lock: satisfied / partial / contradicted by tip. Table. |
| **B5 — CI-1 / CI-1b status honesty** | Exact tree state: `DEFAULT_OLLAMA_MODEL`, package `0.8.7`, tag absence, ACCEPT REJECTED reasons, CI-1b files/tests present, whether Cursor review exists yet. Smoke criteria still unmet? |
| **B6 — Analyze / goal coupling** | `_handle_analyze` + `detect_goal` + plan prepend + prompt_builder analyze messages (prefill, system). What CI-1b changed; residual risk for other short keywords; Gemma-specific failure modes. |
| **B7 — Interpret quarantine readiness** | How often would last-resort `interpret` still be needed? Propose **measurement plan** (llm_logs routing) for CI-5 — do not delete. |
| **B8 — Ontology seam** | What explain/R3 already does (0 LLM); what R4/CI-R4 would add; confirm vault never decides Continuity. |
| **B9 — Chat∥voice parallel gap** | CI-0 says Continuity egress spoken on both modes. What tip actually does today for `--chat` (silent?) vs `--voice-only` (Layer 2)? Gap list for CI-2. |
| **B10 — Naming / docs drift** | FASE_LLM historical docs vs CI product sentence; PRIORIDAD/cola/state coherence. |

### B method
1. Grep `llm_interface.`, `.interpret(`, `.analyze(`, `_semantic_preseed`, `detect_goal`, `En resumen`, `DEFAULT_OLLAMA_MODEL`.  
2. Read `prompt_builder.py`, `llm_client.py`, `action_policy.py`, analyze branch in orchestrator end-to-end.  
3. Diff CI-1b against IC locks if code present.  
4. Sample `runtime/llm_logs/` if present (optional) — note if empty/absent.

### B deliverable
`.jes/artifacts/investigation_report_voice_llm_ci_audit_part_b_llm_ci_b0.md`  
(or Part B in combined report)

---

## Block C — Synthesis: gaps + next obvious step

### C questions

| # | Question |
|---|---|
| **C1 — Unified gap register** | Merge A+B gaps into one table: id · surface (voice/LLM/CI) · severity (blocker / high / medium / park) · evidence · suggested Buy grain (INV/DC/IC) · blocked-by. |
| **C2 — Roadmap coherence** | Against CI cola order (CI-1b → ★ CI-1 → CI-2 egress → CI-3 ingress → CI-4/5 → CI-R4) and voice Parked T40: which rows are still correct? What should reorder? |
| **C3 — The one next obvious step** | **Exactly one** recommended next Engineer action after this INV + any in-flight CI-1b review. Must be the bottleneck that unlocks the CI epoch. Alternatives listed as #2/#3 only. Justify with C1. |
| **C4 — Stop conditions** | What must **not** be the next Buy (e.g. T40, OpenClaw, delete interpret, CI-2 before CI-1 ★). |
| **C5 — PRIORIDAD / cola / state draft** | Exact wording for after this INV: `CI-INV-0 Implemented, await Cursor review` (+ note CI-1b if still open). |

### C deliverable
`.jes/artifacts/investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md`  
**or** a short Part C + a one-page “Next step” box at the top of a combined report.

**Also required:** index file if split:

`.jes/artifacts/investigation_report_voice_llm_ci_audit_b0.md` — links to Parts A/B/C + executive “next step” in ≤15 lines.

---

## Combined report option

Claude may instead write **one** file:

`.jes/artifacts/investigation_report_voice_llm_ci_audit_b0.md`

with sections `## Part A` / `## Part B` / `## Part C` answering every question ID. Prefer split if the single file would exceed ~800 lines.

---

## Forensic method (global)

1. Cite **file:line** or artifact path — not prior-report prose alone.  
2. Run full suite **or** document skip with reason; run targeted greps for fences.  
3. Distinguish: **shipped ★** · **in tree untagged** · **DC only** · **Parked** · **contradicted**.  
4. No design invention: recommendations must map to existing CI-0 locks or explicit “needs new DC”.  
5. Update PRIORIDAD / cola CI / `engineering_state.json` per C5 only (docs).

---

## Acceptance (investigation)

- [ ] Every A1–A8, B1–B10, C1–C5 answered with citations  
- [ ] Gap register + **one** next obvious step  
- [ ] T40 recommendation (expect Parked)  
- [ ] CI-0 vs T44 “no LLM Layer 2” conflict explicitly tabulated  
- [ ] Zero `src/` product edits  
- [ ] Cursor review · Engineer ★ on findings  

---

## 4. Paste for Claude

```text
Investigation — INV-voice-llm-ci-audit (CI-INV-0)
Parent: CI-0 DC Continuity Interpreter ★ · voice daily ★ @ v0.8.6 ·
CI-1 ACCEPT REJECTED · CI-1b may be awaiting review.
Package: tip stays v0.8.6 (docs only). Do not tag. Do not edit src/.

IC: .jes/artifacts/investigation_contract_voice_llm_continuity_interpreter_audit_b0.md
Colas: engineer_note_voice_phase_c_cola.md · engineer_note_continuity_interpreter_cola.md
DC: design_contract_continuity_interpreter_epoch_b0.md

GOAL: Exhaustive forensic audit in THREE BLOCKS:
  A — Voice phase tip (T34–T59, modes, Layer 2, DC locks, gaps)
  B — LLM + CI epoch (call graph, CI-0 vs tip, CI-1/1b, analyze/goal,
      interpret quarantine, ontology, chat∥voice gap)
  C — Unified gaps + THE one next obvious step vs CI roadmap

DO:
- Read-only. Cite file:line / artifacts.
- Deliver Part A/B/C reports (split OK) + index with ≤15-line next-step box.
- Gap register (severity, Buy grain, blocked-by).
- PRIORIDAD/cola CI/state draft: CI-INV-0 Implemented await Cursor review.
- No ACCEPT claim. No src/ changes. No Conversation Engine.

NO: implement CI-2 · delete interpret · unpark T40 without evidence ·
OpenClaw · embeddings · package bump
```

---

## 5. Cursor note

Claude investigates only. Cursor reviews the report(s). Same-session self-PASS is not review of record. If mid-flight CI-1b review conflicts with audit timing, finish this INV against tree-as-found and note the race in B5.
