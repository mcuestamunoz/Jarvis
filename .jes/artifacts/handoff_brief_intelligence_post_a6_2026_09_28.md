# Intent cycle brief — Assistant / `intelligence/` (post A0–A6)

**Date:** 2026-09-28  
**For:** new Cursor chat (new Intent / cycle)  
**Repo:** Jarvis · tip **`v0.6.5`** · branch `main` (local ahead of origin — **do not push** unless Engineer asks)  
**Scope of this cycle:** continue **`src/jarvis/intelligence/`** (Assistant column) — **not** craft energy/autonomy fixes, **not** silicon, **not** Continuity ranking redesign.

---

## 0. First actions (mandatory — methodology)

Before proposing any Buy, the agent **must**:

1. **Explore / visualize the JES workspace** — walk `.jes/` (artifacts, state, conventions) and how this repo runs engineering cycles.  
2. **Read methodology & role sources** (do not invent process):
   - `CLAUDE.md` — code-agent rules (deterministic SoT; no new subsystems without approval)
   - `.cursor/rules/jes-cursor-claude-roles.mdc` — Cursor = IC/cola/PRIORIDAD/review; Claude = implement after ★; Cursor does **not** implement `src/`/`ui/`/`tests/`/`library/` unless Engineer says “implementa tú”
   - `docs/IMPLEMENTATION_TASKS.md` — **PRIORIDAD AHORA** only (top section)
   - Recent handoff pattern: `.jes/artifacts/handoff_brief_post_c20_2026_09_22.md` (process spine)
3. **Read product tip for this cycle** (intelligence path):
   - `docs/USER_GUIDE_EXPLAIN.md`
   - `docs/JARVIS_KNOWLEDGE_VISION.md` §7
   - `docs/ONTOLOGY_CROSSWALKS.md`
   - `.jes/artifacts/design_contract_assistant_placement_b0.md`
   - A6 review: `.jes/artifacts/implementation_review_continuity_explain_cite_r3_b1.md`
   - Parked A7: `.jes/artifacts/implementation_contract_chat_explain_intercept_b1.md`

Only after that: summarize tip + propose **one** next front for Engineer ★.

---

## 1. Roles (unchanged)

| Agent | Does | Does not |
|---|---|---|
| **Cursor** | ICs, PRIORIDAD/cola, independent review after code | Implement Buy code unless Engineer explicitly asks |
| **Claude Code** | Implements ★ IC + report | Claim ACCEPT / cut tags |
| **Engineer** | ★ Buy / ACCEPT / next front / tags on ACCEPT | — |

Always explain **what is asked** and **what is done**.

---

## 2. Where tip is (intelligence)

| Item | State |
|---|---|
| Git tip tagged | **`v0.6.5`** |
| Package | `0.6.5` |
| Path closed | **A0–A6** — placement → scaffold → retrieve → `jarvis explain` CLI → maps/`--rung` → Continuity `explain_topics` → Conceptos |
| Field smoke | CLI `python -m jarvis.main explain …` **works** (OP note verified) |
| Continuity Conceptos | Works in `estado` (points at `jarvis explain <id>`) |
| **A7** `B1-chat-explain-intercept` | **Parked** — typing `jarvis explain` **inside** `--chat` hits LLM → Mac collapse; Engineer deferred |
| A4 voice/world | Parked |
| R4 LLM cite | Later (LLM = semantic interpreter only; command/tables first) |

**Locks still true:**
- Ontology EXPLAINS · Continuity decides craft · catalog declares SKUs  
- `intelligence` ids ≠ `core` param names — bridges are tables  
- RAG/LLM not SoT  
- Conceptos is garnish; does not change `next_useful_step`

---

## 3. Candidate next fronts (Engineer picks ONE)

Natural deepen-after-A6 (intelligence only):

1. **Reopen A7** — chat intercept `explain` / `jarvis explain` in `_handle_global_commands` **before LLM** (fixes Mac collapse). IC already written, parked.  
2. **Topic expand** — more Continuity → `explain_topics` when a real signal exists (e.g. `current` when distinguished).  
3. **Maps expand** — more FS/HD keys in `explain_maps.py` / aliases (demand-driven, not “map everything”).  
4. **R4 (later)** — LLM as interpreter only over tables/cites — **not** default next.

**Out of scope for this cycle:** fixing autonomy gap on `dron-de-vigilancia-doméstico`, silicon, Board, Continuity ranking changes.

Do **not** open two fronts in one IC.

---

## 4. Cycle rhythm

1. Methodology read (§0) → tip summary.  
2. Engineer names **one** front (or asks Cursor to recommend).  
3. Cursor drafts/refines IC → PRIORIDAD → Engineer ★.  
4. Claude implements + report (+ § living docs when IC requires).  
5. Cursor independent review → Engineer ACCEPT + tag.  
6. No push unless asked. Tags only on ACCEPT.

---

## 5. Suggested paste for the new chat

```text
New Jarvis JES Intent cycle — continue Assistant / intelligence/ only.

Tip: v0.6.5 (A0–A6 CLOSED). A7 chat-explain-intercept PARKED.
Craft autonomy / silicon are OUT OF SCOPE this cycle.

FIRST: explore/visualize .jes/ and read methodology before any Buy:
  CLAUDE.md
  .cursor/rules/jes-cursor-claude-roles.mdc
  docs/IMPLEMENTATION_TASKS.md (PRIORIDAD top only)
  .jes/artifacts/handoff_brief_post_c20_2026_09_22.md (process spine)
  .jes/artifacts/handoff_brief_intelligence_post_a6_2026_09_28.md (this cycle)
  docs/USER_GUIDE_EXPLAIN.md + design_contract_assistant_placement_b0.md

Roles: Cursor = IC / cola / review (no src/ unless Engineer says implementa tú).
Claude = implement after ★. Always explain what is asked and what is done.

Then summarize tip and propose ONE next intelligence front for Engineer ★
(candidates: reopen A7 · topic expand · maps expand · R4 later).
```
