# Engineer note — Chat spoken-continuity map (living SoT)

**Date:** 2026-10-04
**Status:** **OPEN living map** — seeded by [T44-inv](investigation_report_assistant_chat_spoken_continuity_b0.md)
**Authority:** Engineer — this is the single inventory a future spoken-continuity DC/IC implements against
**Tip parent:** `0.7.3` (T43) · this note is docs-only, no `src/` change

**Purpose:** Every `--chat` print surface and every `build_startup_context`/`build_project_continuity` field, classified for the two-layer spoken-continuity model:

> **Layer 1 — TRUTH:** full `--chat` / Continuity on screen. Unchanged, always complete.
> **Layer 2 — SPOKEN CONTINUITY:** a deterministic extract of what matters for continuity. Brief by default. Full only on request. **No LLM** in this layer — a later Buy may add an LLM *semantic interpreter* on top, but never inside the extraction itself.

**Classification legend:**
- **must-speak-brief** — spoken every time under `--chat --voice-speak`, kept short (already short, or a single extracted fact).
- **speak-on-request** — spoken only when the user asks for "completo"/full (trigger shape: see Q6 of the INV report — not yet implemented).
- **screen-only** — never spoken by default, even on request (operator diagnostics / visual-only content).

---

## ⚠ Standing norm (proposed — not yet in `CLAUDE.md`)

> ### Chat / spoken-continuity egress map
>
> Whenever a Buy adds or changes a `--chat` print surface, a `build_startup_context`/`build_project_continuity` field, or any `render_*` function that produces chat egress, update this map **in the same Buy** — add the new surface/field row and classify it (`must-speak-brief` / `speak-on-request` / `screen-only`). Do not leave this map stale; the spoken-continuity layer treats it as its single source of truth for what exists to classify.

Landing: Engineer ★ on [T44-inv](investigation_report_assistant_chat_spoken_continuity_b0.md) → land the clause above in `CLAUDE.md` (new short section) → add a pointer line here from [`engineer_note_voice_phase_c_cola.md`](engineer_note_voice_phase_c_cola.md), mirroring its existing pointer to `USER_GUIDE_VOICE.md`.

---

## Table 1 — Chat egress surfaces (`run_chat`, `src/jarvis/adapters/cli/main.py`)

| Surface | Symbol | Trigger | Length | Speaks today (`0.7.3`)? | Class |
|---|---|---|---|---|---|
| Startup banner | `main.py:966-968` | every `run_chat()` | 3 lines | No | **screen-only** |
| Welcome / project picker | `_print_welcome`, `main.py:810-827` / `971` | every `run_chat()` | banner + N rows | No | **screen-only** |
| EOF/Ctrl-C exit | `main.py:979-980` | `EOFError`/`KeyboardInterrupt` | 1 sentence | Yes | **must-speak-brief** |
| `exit`/`quit` | `main.py:986` | typed exit | 1 sentence | Yes | **must-speak-brief** |
| `help` | `main.py:989` | typed help | 1 sentence | Yes | **must-speak-brief** |
| Startup-selection error | `main.py:998` | bad project pick | 1 sentence | Yes | **must-speak-brief** |
| **Startup Continuity wall** | `main.py:1003-1005` | load/select existing project | long (Table 2, all sections) | Yes — full wall today | **brief-extract default / speak-on-request for the rest** (see Table 2) |
| Define-wizard proactive opener | `main.py:1015` | auto-define fires after load | short/medium | Yes | **must-speak-brief** |
| No-project / `load_project` confirmation | `main.py:1017` | fresh/no-project path | short (4 lines) | Yes | **must-speak-brief** |
| Turn exception handler | `main.py:1026` | uncaught exception | 1 sentence | Yes | **must-speak-brief** |
| Main-turn error | `main.py:1030` | `status == "error"` | short–medium | Yes | **must-speak-brief** |
| Main-turn success (Skill-shaped) | `main.py:1032` → `render_response` plain `ok` branch (`main.py:590-598`) | e.g. `armar`/`hold`/`land` | short (1-2 sentences) | Yes | **must-speak-brief** (speak-as-printed) |
| Main-turn success (coherence-footer-shaped) | `main.py:1032` → `render_response` coherence block (`main.py:674-694`) | calculate/iterate/simulate/etc. once Continuity exists | short–medium | Yes | **must-speak-brief** (already = Table 2's brief fields) |
| Main-turn success (reasoning-shaped, no coherence) | `main.py:1032` → `render_response` reasoning block (`main.py:696-734`) | rare — e.g. `create_project` before Continuity exists | long, multi-part | Yes | **speak-on-request** (future IC: speak only top `PRIORIDAD CRÍTICA` label by default) |
| Main-turn success (`estado`/`project_status`) | `main.py:1032` → `render_response` project_status branch (`main.py:560-574`) → same wall as startup | typed `estado`/`CONTINUITY_DEFER_PHRASES` (`jarvis/config.py:51-61`) | long (Table 2) | Yes — full wall today | **brief-extract default / speak-on-request for the rest** (same as startup wall) |
| TTS honesty failure | `main.py:943-944` | `speak_tts=True` + `TtsError` | 1 sentence | n/a (failure notice, not re-spoken) | **must-speak-brief** (it's already the only thing spoken for that failed attempt) |
| JSON fallback | `render_response`, `main.py:743` | any unhandled result shape | raw dict dump | No path pairs this with `speak` today | **screen-only** |

---

## Table 2 — Continuity / startup-context fields

### `build_project_continuity` return (`src/jarvis/core/project_continuity.py:389-395`)

| Field | Printed in | Class |
|---|---|---|
| `situation` | wall `main.py:305`, coherence footer `main.py:685` | **must-speak-brief** |
| `evidence` (`list[str]`, capped 6) | wall only `main.py:306-310` | **speak-on-request** |
| `next_useful_step` | wall `main.py:311`, coherence footer `main.py:686-687` | **must-speak-brief** |
| `next_useful_why` | wall `main.py:313-314`, coherence footer `main.py:688-689` | **must-speak-brief** |
| `explain_topics` → Conceptos lines | wall `main.py:315-318`, coherence footer `main.py:690-693` | **speak-on-request** |

### `build_startup_context` return (`src/jarvis/core/orchestrator.py:7862-7938`)

| Field | Section | Class |
|---|---|---|
| `project_slug`, `objective` | `main.py:296-298` | **speak-on-request** (identity, not continuity-decision content; low priority but harmless if later promoted) |
| `continuity` | see above | see above |
| `phase` | `main.py:321-324` | **screen-only** (superseded by `continuity.situation` whenever present) |
| `status_type`/`status_reason`/`missing_params` | `main.py:326-350` | **screen-only** (prose already folded into `continuity.situation`) |
| `active_variables` | `main.py:352-355` | **screen-only** |
| `suggested_action` | `main.py:358-368` | **screen-only** (superseded by `continuity.next_useful_step` whenever present) |
| `architecture_progress`/`next_architecture_label`/`next_block_status` | `main.py:370-384` | **speak-on-request** |
| `physical_requirements_lines` | `main.py:386-391` | **speak-on-request** |
| `component_bom_lines` | `main.py:402-407` | **speak-on-request** |
| `propulsion_resolution` | `main.py:412-438` | **speak-on-request** |
| `motor_operating_point_electrical` | `main.py:446-456` | **speak-on-request** |
| `hover_energy` | `main.py:464-480` | **speak-on-request** |
| `battery_endurance.envelope` | `main.py:483-485` via `_render_estimative_endurance_lines` (`main.py:253-287`) | **speak-on-request** |
| `readiness.overall` | inside readiness block, `main.py:230` (`PROJECT STATUS:` line) | **must-speak-brief** — extracted alone, without the subsystem table (Q5 item 4) |
| `readiness.subsystems` (9-row table + footnotes) | `main.py:216-227` | **speak-on-request** |
| `readiness.prioritized_gaps[0].title` | inside TOP GAPS, `main.py:242` | **must-speak-brief** — extracted alone, title only (Q5 item 5) |
| `readiness.prioritized_gaps[1:]` (full detail: blocks/depends_on/next) | `main.py:236-249` | **speak-on-request** |
| `prop_energy_block_closure` | `main.py:500-537` | **speak-on-request** |
| `margin_claim_weak` | bool gate only, `main.py:233-234` | **screen-only** |

---

## Brief spoken shape (default, when it ships) — ordered

1. `continuity["situation"]`
2. `continuity["next_useful_step"]`
3. `continuity["next_useful_why"]` (omit if `None`)
4. One phrase derived from `readiness["overall"]` (not the subsystem table)
5. `readiness["prioritized_gaps"][0]["title"]` if the list is non-empty (title only)

Everything else in Table 2 stays **speak-on-request**; nothing is ever removed from the screen — Layer 1 (truth, on screen) is untouched by any of this.

---

## Maintenance

This map is updated **in the same Buy** that changes the surfaces/fields it tracks (see the norm above). Do not mark a row's classification changed from prose alone — cite the new/changed symbol the way every row above does.

**Known future additions (not yet in code, no placeholder row):** T40 (craft/`world` voice) will introduce new egress surfaces when it lands — those get their own rows then, classified the same way, per the norm.
