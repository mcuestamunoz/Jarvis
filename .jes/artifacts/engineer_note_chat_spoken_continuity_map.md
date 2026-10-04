# Engineer note — Chat spoken-continuity map (living SoT)

**Date:** 2026-10-04  
**Status:** **OPEN living map** — Layer 2 **shipped** by [T45](implementation_report_assistant_chat_spoken_continuity_b1.md) @ `0.7.4` ([T44-inv](investigation_report_assistant_chat_spoken_continuity_b0.md) · [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [T45 IC](implementation_contract_assistant_chat_spoken_continuity_b1.md))  
**Authority:** Engineer — this is the single inventory future chat/Continuity egress Buys update in the same Buy  
**Tip:** `0.7.4` — Layer 2 live on the two Continuity walls (project load + `action == "project_status"`); every other surface unchanged since T43

**Purpose:** Every `--chat` print surface and every `build_startup_context`/`build_project_continuity` field, classified for the two-layer spoken-continuity model:

> **Layer 1 — TRUTH:** full `--chat` / Continuity on screen. Unchanged, always complete.  
> **Layer 2 — SPOKEN CONTINUITY:** a deterministic extract of what matters for continuity. Brief by default on Continuity **walls**. Full only on request. **No LLM** in this layer.

**Classification legend:**
- **must-speak-brief** — spoken every time under `--chat --voice-speak`, kept short (already short, or a single extracted fact).
- **speak-on-request** — spoken only when the user asks for full (`dame detalles` / `completo` / the locked FULL set).
- **screen-only** — never spoken by default, even on request (operator diagnostics / visual-only content).

**Shipped extractor (T45):** `src/jarvis/adapters/voice/spoken_continuity.py` — `brief_spoken_continuity(ctx)` (the brief extract), `is_full_continuity_request(raw_text)` (locked FULL-phrase match), `spoken_text_for_wall(raw_text, printed_wall, ctx)` (the combinator `run_chat` calls on both wall sites). Three of the ten locked FULL phrases (`completo`, `estado completo`, `cuentame todo`) were also newly added to `CONTINUITY_DEFER_PHRASES` (`jarvis/config.py:108-110`) so they resolve to `action == "project_status"` at all — the other seven were already members.

Phase cola: [`engineer_note_voice_phase_c_cola.md`](engineer_note_voice_phase_c_cola.md).

---

## ⚠ Standing norm (in `CLAUDE.md`)

Whenever a Buy adds or changes a `--chat` print surface, a `build_startup_context`/`build_project_continuity` field, or any `render_*` function that produces chat egress, update this map **in the same Buy**. Clause: [`CLAUDE.md`](../../CLAUDE.md) § Chat / spoken-continuity egress map.

---

## Table 1 — Chat egress surfaces (`run_chat`, `src/jarvis/adapters/cli/main.py`)

| Surface | Symbol | Trigger | Length | Speaks (`0.7.4`)? | Class |
|---|---|---|---|---|---|
| Startup banner | `main.py:966-968` | every `run_chat()` | 3 lines | No | **screen-only** |
| Welcome / project picker | `_print_welcome`, `main.py:810-827` / `971` | every `run_chat()` | banner + N rows | No | **screen-only** |
| EOF/Ctrl-C exit | `main.py:979-980` | `EOFError`/`KeyboardInterrupt` | 1 sentence | Yes | **must-speak-brief** |
| `exit`/`quit` | `main.py:986` | typed exit | 1 sentence | Yes | **must-speak-brief** |
| `help` | `main.py:989` | typed help | 1 sentence | Yes | **must-speak-brief** |
| Startup-selection error | `main.py:998` | bad project pick | 1 sentence | Yes | **must-speak-brief** |
| **Startup Continuity wall** | `main.py:1003-1005`, speak via `spoken_text_for_wall` (`spoken_continuity.py`) | load/select existing project | print: long (Table 2, all sections) · speak: brief (5 fields) or full on a locked FULL phrase | Yes — print always full; speak **brief by default**, full only on a FULL phrase this turn | print: **screen-truth** · speak: **brief-extract default / speak-on-request for the rest** (see Table 2) |
| Define-wizard proactive opener | `main.py:1015` | auto-define fires after load | short/medium | Yes | **must-speak-brief** (speak-as-printed — not a wall) |
| No-project / `load_project` confirmation | `main.py:1017` | fresh/no-project path | short (4 lines) | Yes | **must-speak-brief** |
| Turn exception handler | `main.py:1026` | uncaught exception | 1 sentence | Yes | **must-speak-brief** |
| Main-turn error | `main.py:1030` | `status == "error"` | short–medium | Yes | **must-speak-brief** |
| Main-turn success (Skill-shaped) | `main.py:1032` → `render_response` plain `ok` branch (`main.py:590-598`) | e.g. `armar`/`hold`/`land` | short (1-2 sentences) | Yes | **must-speak-brief** (speak-as-printed, unchanged by T45) |
| Main-turn success (coherence-footer-shaped) | `main.py:1032` → `render_response` coherence block (`main.py:674-694`) | calculate/iterate/simulate/etc. once Continuity exists | short–medium | Yes | **must-speak-brief** (speak-as-printed, unchanged by T45 — already = Table 2's brief fields, not routed through the T45 extractor since `action != "project_status"`) |
| Main-turn success (reasoning-shaped, no coherence) | `main.py:1032` → `render_response` reasoning block (`main.py:696-734`) | rare — e.g. `create_project` before Continuity exists | long, multi-part | Yes | **speak-on-request** (unchanged by T45 — future IC: speak only top `PRIORIDAD CRÍTICA` label by default) |
| Main-turn success (`estado`/`project_status`) | `main.py:1029-1035`, speak via `spoken_text_for_wall` when `result["action"] == "project_status"` | typed `estado`/`CONTINUITY_DEFER_PHRASES` (`jarvis/config.py:51-110`, now includes `completo`/`estado completo`/`cuentame todo`) | print: long (Table 2) · speak: brief or full (same rule as the startup wall) | Yes | print: **screen-truth** · speak: **brief-extract default / speak-on-request for the rest** (same as startup wall) |
| TTS honesty failure | `main.py:943-944` | `speak_tts=True` + `TtsError` | 1 sentence | n/a (failure notice, not re-spoken) | **must-speak-brief** (it's already the only thing spoken for that failed attempt) |
| JSON fallback | `render_response`, `main.py:743` | any unhandled result shape | raw dict dump | No path pairs this with `speak` today | **screen-only** |

---

## Table 2 — Continuity / startup-context fields

### `build_project_continuity` return (`src/jarvis/core/project_continuity.py:676-682`)

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
| `readiness.overall` | inside readiness block, `main.py:230` (`PROJECT STATUS:` line) | **must-speak-brief** — extracted alone by `brief_spoken_continuity` (`spoken_continuity.py`), without the subsystem table |
| `readiness.subsystems` (9-row table + footnotes) | `main.py:216-227` | **speak-on-request** |
| `readiness.prioritized_gaps[0].title` | inside TOP GAPS, `main.py:242` | **must-speak-brief** — extracted alone by `brief_spoken_continuity`, title only |
| `readiness.prioritized_gaps[1:]` (full detail: blocks/depends_on/next) | `main.py:236-249` | **speak-on-request** |
| `prop_energy_block_closure` | `main.py:500-537` | **speak-on-request** |
| `margin_claim_weak` | bool gate only, `main.py:233-234` | **screen-only** |

---

## Brief spoken shape (default, shipped T45 @ `0.7.4`) — ordered

Implemented in `brief_spoken_continuity` (`src/jarvis/adapters/voice/spoken_continuity.py`):

1. `continuity["situation"]`
2. `continuity["next_useful_step"]`
3. humanized `continuity["next_useful_why"]` (via `main.py::_humanize_next_useful_why`, same mapping the wall itself uses — omitted if `next_useful_step` or `next_useful_why` is absent)
4. `"PROJECT STATUS: ASSEMBLY READY"` / `"PROJECT STATUS: NOT ASSEMBLY READY"` derived from `readiness["overall"]` (not the subsystem table)
5. `readiness["prioritized_gaps"][0]["title"]` if the list is non-empty (title only)

Each piece is omitted when its source field is absent; joined with newlines. Everything else in Table 2 stays **speak-on-request**; nothing is ever removed from the screen — Layer 1 (truth, on screen) is untouched by any of this, proven by `tests/test_assistant_chat_spoken_continuity_b1.py::test_t2_chat_wall_prints_full_but_speaks_brief`.

**FULL override:** `is_full_continuity_request`/`spoken_text_for_wall` (same module) speak the exact printed wall instead, for one turn only, when the typed line matches the locked FULL set — see the header above.

---

## Maintenance

This map is updated **in the same Buy** that changes the surfaces/fields it tracks (see the norm above). Do not mark a row's classification changed from prose alone — cite the new/changed symbol the way every row above does.

**Known future additions (not yet in code, no placeholder row):** T40 (craft/`world` voice) will introduce new egress surfaces when it lands — those get their own rows then, classified the same way, per the norm.
