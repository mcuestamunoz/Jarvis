# Investigation Report — Chat spoken-continuity map (`INV-assistant-chat-spoken-continuity`, T44-inv)

**Project:** Jarvis
**Date:** 2026-10-04
**Investigator:** Claude Code (Engineer paste)
**Contract:** [`investigation_contract_assistant_chat_spoken_continuity_b0.md`](investigation_contract_assistant_chat_spoken_continuity_b0.md)
**Parents:** [T43 review](implementation_review_assistant_chat_voice_speak_b1.md) @ `0.7.3` (PASS WITH NOTES) · [T34-inv ★](investigation_review_assistant_voice_e2e_b0.md) · [voice channels DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ on findings → authorize DC/IC.
**Package:** tip stays **`0.7.3`** — docs/report only, **no `src/` change**.

**Scope discipline:** this report answers Q1–Q12 from the INV. It does **not** implement a spoken layer, does not touch `run_chat`/`_chat_speak_fn`/any `render_*` function, and proposes (never applies) a `CLAUDE.md` norm clause.

---

## Q1 — Chat egress inventory

Every `print`/`_say`/`speak` surface reachable from `run_chat` (`src/jarvis/adapters/cli/main.py:949-1032`), in source order:

| Surface | Symbol | Trigger | Typical length | Speaks today under `--chat --voice-speak`? |
|---|---|---|---|---|
| Startup banner (`Modelo:`/`Ollama:`/`Logs LLM:`) | `main.py:966-968` (plain `print`) | every `run_chat()` call | 3 one-line facts | **No** — never paired with `speak`/`_say` |
| Welcome / project picker | `_print_welcome` (`main.py:810-827`), called at `main.py:971` | every `run_chat()` call | banner + up to N project rows + picker hint | **No** — called directly, not through `_say`/`speak` |
| EOF / Ctrl-C exit | `main.py:979-980` (`print` + explicit `speak("Sesión cerrada.")`) | `EOFError`/`KeyboardInterrupt` | 1 short sentence | **Yes** |
| `exit`/`quit` command | `main.py:986` (`_say("Sesión cerrada.")`) | typed `exit`/`quit` | 1 short sentence | **Yes** |
| `help` command | `main.py:989` (`_say(...)`) | typed `help` | 1 sentence | **Yes** |
| Startup-selection error | `main.py:998` (`_say(startup_result.get("message") or ...)`) | invalid project pick | 1 short sentence | **Yes** |
| **Startup Continuity wall** | `main.py:1003-1005` (`render_startup_context(startup_ctx)` then `print` + `speak(startup_block)`) | selecting/loading an existing project at `--chat` startup | **long** — every section in Q2's table can appear at once | **Yes — the full wall, verbatim** (the exact failure mode the Engineer hit) |
| Define-wizard proactive opener | `main.py:1015` (`_say(render_response(proactive))`) | `should_auto_start_define_on_load` fires after a load | short/medium (`interactive` status: error + question) | **Yes** |
| No-project / `load_project` confirmation | `main.py:1017` (`_say(render_response(startup_result))`) | fresh project or no-project-picker path | short (`Proyecto cargado / Objetivo / Iteraciones / hint`) | **Yes** |
| Turn exception handler | `main.py:1026` (`_say(f"Error interno: {error}")`) | any uncaught exception from a turn | 1 short sentence | **Yes** |
| Main-turn error | `main.py:1030` (`_say(result.get("message") or ...)`) | `handle_user_text` returns `status == "error"` | short–medium (Safety reject reasons etc.) | **Yes** |
| Main-turn success | `main.py:1032` (`_say(render_response(result))`) | every other turn | **variable** — short for a Skill action, **long** for `estado`/`project_status` (same wall as startup), medium for calculate/iterate with a coherence footer | **Yes**, whatever `render_response` returns |
| TTS honesty failure | `main.py:943-944` inside `_chat_speak_fn`'s `speak(text)` closure | `speak_tts=True` and `speak_egress` raises `TtsError` | 1 sentence | n/a — this *is* the speak-failure print, never itself re-spoken |

Confirms the INV's forensic step 1 (re-verify `run_chat`/`_chat_speak_fn`): both match the implementation exactly as shipped in T43, unchanged since (`git log -1 -- src/jarvis/adapters/cli/main.py` shows no commit after T43's `8719e56`/review `bfcc964` on this tip).

---

## Q2 — Continuity field map

Three builders feed chat egress; this maps their **structured fields** to the **printed sections** that render them.

### `build_project_continuity` (`src/jarvis/core/project_continuity.py:288-395`)

Returns exactly five keys (`project_continuity.py:389-395`):

| Field | Printed as | Renderer |
|---|---|---|
| `situation` | "Situación: …" | `render_startup_context` (`main.py:305`) · coherence footer "Estado: …" (`main.py:685`) |
| `evidence` (`list[str]`) | "Evidencia:" bullets, capped at 6 | `render_startup_context` (`main.py:306-310`) — **not** shown in the short coherence footer |
| `next_useful_step` | "Siguiente paso: …" | both `render_startup_context` (`main.py:311`) and coherence footer (`main.py:686-687`) |
| `next_useful_why` | "   Por qué: …" | both (`main.py:313-314`, `main.py:688-689`) |
| `explain_topics` | "Conceptos (ontology) — …" block | both, via `_render_concept_lines` (`main.py:94-117`, called at `main.py:315-318` and `main.py:690-693`) |

### `build_startup_context` (`src/jarvis/core/orchestrator.py:7564-7938`)

Full return dict (`orchestrator.py:7862-7938`), each field mapped to its `render_startup_context` section:

| Field | Section in `render_startup_context` | Dict vs. prose |
|---|---|---|
| `project_slug`, `objective` | "Proyecto: …" / "Objetivo: …" (`main.py:296-298`) | plain strings |
| `continuity` | Situación/Evidencia/Siguiente paso/Conceptos block (`main.py:301-319`) | structured dict (above) |
| `phase` | "Fase: …" — only when `continuity.situation` absent (`main.py:321-324`) | enum-like string, mapped via `_PHASE_LABELS` |
| `status_type`, `status_reason`, `missing_params` | blocking/warning/nominal/no_data block (`main.py:326-350`) — each gated on `continuity.situation` absence except `blocking` | structured |
| `active_variables` | one compact line (`main.py:352-355`) — only when `continuity.evidence` absent | dict, max 3 keys |
| `suggested_action` | "→ …" hint (`main.py:358-368`) — only when no `continuity.next_useful_step` | dict `{label, reason, hint}` |
| `architecture_progress`, `next_architecture_label`, `next_block_status` | "Arquitectura … — Siguiente: …" (`main.py:370-384`) | strings |
| `physical_requirements_lines` | "Requisitos físicos:" bullets (`main.py:386-391`) — only when no `continuity.evidence` | pre-rendered `list[str]` |
| `component_bom_lines` | "Componentes / gaps:" (`main.py:402-407`) | pre-rendered `list[str]`, always shown when non-empty |
| `propulsion_resolution` | "Propulsión (evidencia): …" (`main.py:412-438`) | dict |
| `motor_operating_point_electrical` | "Propulsión (OP eléctrico): …" (`main.py:446-456`) | dict |
| `hover_energy` | "Energía hover (evidencia): …" (`main.py:464-480`) | dict |
| `battery_endurance` (`.envelope`) | "Autonomía estimada (ESTIMATIVO…)" block via `_render_estimative_endurance_lines` (`main.py:253-287`, called `main.py:483-485`) | `list[dict]` rows |
| `readiness` (`dataclasses.asdict(EngineeringReadinessResult)`) | "ENGINEERING READINESS" block — 9 subsystems + footnotes + `PROJECT STATUS:` + up to 3 `TOP GAPS` — via `_render_readiness_block` (`main.py:192-250`, called `main.py:488-493`) | full nested dict (`subsystems`, `overall`, `prioritized_gaps`) |
| `prop_energy_block_closure` | "BLOQUE PROPULSIÓN/ENERGÍA: …" (`main.py:500-537`) | dict (`status`, `evidence_tier`, `facts`) |
| `margin_claim_weak` | only a boolean gate on the `situation` string + one `NOTE:` line inside the readiness block (`main.py:233-234`) | bool |

All fields above are **dicts or pre-rendered `list[str]`**, never free LLM prose — `render_startup_context` is pure formatting over them (no engineering logic, confirmed by its own docstring at `main.py:192-211`).

### `attach_project_coherence` (`orchestrator.py:1539-1576`)

Runs only for `action in {define_missing_params, iterate, calculate, simulate, create_project, component_description_saved, dse_apply, apply_exploration_result}` (`orchestrator.py:1550-1559`) — **not** for any vehicle Skill (`armar`/`hold`/`land`/…). When it fires, it re-derives `build_startup_context()` and attaches only `cont = ctx["continuity"]` as `result["coherence_footer"]` (`orchestrator.py:1568-1576`) — the **same five-field dict** as above, never the full `startup_context`.

---

## Q3 — Speak-vs-print matrix (today, tip `0.7.3`)

| Class | Surfaces | Speaks under `--chat --voice-speak`? |
|---|---|---|
| **Print-only, never speak** | startup banner, `_print_welcome` (Q1) | No |
| **Print + speak (paired, honest-failure safe)** | every `_say(...)`/explicit `speak(...)` call in `run_chat` (Q1 rows 3–11) | Yes — same string, via `_chat_speak_fn` |
| **Speak-only honesty** | `TTS no disponible: …` printed inside the `speak()` closure on `TtsError` | n/a — a failure notice about speaking, not itself re-spoken |

**Bare `--chat` never calls TTS** — re-confirmed structurally, not just by default value: `_chat_speak_fn(False)` (`main.py:930-934`) returns a `noop` that **never imports** `speak_egress`/`TtsError`; the module-level `import` only executes inside the `if speak_tts:` branch (`main.py:936`). `inspect.getsource(run_chat)` still contains zero occurrence of `speak_egress`/`JARVIS_TTS_CMD`/`_voice_speak_fn`/`TtsError` (re-ran the exact check T42/T43 use):

```text
$ python3 -c "import inspect; from jarvis.adapters.cli.main import run_chat; \
  s = inspect.getsource(run_chat); \
  print([t for t in ('speak_egress','JARVIS_TTS_CMD','_voice_speak_fn','TtsError') if t in s])"
[]
```

---

## Q4 — Relevance ranking (spoken continuity)

Deterministic, from the fields above — no new field, no LLM:

**must-speak-brief** (always spoken under `--chat --voice-speak`, kept short):
- `continuity.situation`, `continuity.next_useful_step`, `continuity.next_useful_why` — the three facts a returning Engineer needs to *continue*, already the smallest existing continuity shape (it is literally what `coherence_footer` already carries).
- A one-fact project-status signal derived from `readiness.overall` (`ASSEMBLY_READY` / not) — the single highest-leverage go/no-go fact, without the 9-subsystem table it lives inside today.
- The top entry of `readiness.prioritized_gaps` (title only) — "what's blocking," one line, not the full gap block (blocks/depends_on/next).
- Every short Skill-turn reply (`Acción ejecutada: …` for `armar`/`hold`/`land`/…), every error message, every wizard prompt/question — these are **already** one–two sentences; "brief" here means *speak as printed*, no extraction needed.

**speak-on-request** (only when the user explicitly asks for "completo"/full):
- `continuity.evidence` (the bullet list beyond the one-line situation).
- The full `render_startup_context` wall (Situación+Evidencia+Conceptos+Componentes/gaps+Readiness table+TOP GAPS detail+propulsión/hover/ESTIMATIVO lines+block closure) — i.e. everything currently spoken verbatim on project load and on `estado`.
- The `reasoning` block (`explanation`/`insights`/`tradeoffs`/`PRIORIDAD CRÍTICA`/`Siguientes pasos`/`Evitar`) in `render_response`'s `ok` branch — dense, screen-shaped, and in practice rarely reached once a coherence footer exists (see Q7).
- `component_bom_lines`, `physical_requirements_lines`, `propulsion_resolution`, `motor_operating_point_electrical`, `hover_energy`, `battery_endurance` envelope, `prop_energy_block_closure` — all evidence-grade detail, valuable on screen, noisy read aloud by default.

**screen-only** (never default-speak, even on request, because they are visual/operator noise, not continuity facts):
- Startup banner (`Modelo:`/`Ollama:`/`Logs LLM:`) — operator diagnostics.
- `_print_welcome`'s numbered project picker — a list meant to be *read*, not heard, before any project is even loaded.
- The raw `json.dumps(...)` fallback at the end of `render_response` (`main.py:743`) for any status the function doesn't otherwise handle.

---

## Q5 — Brief spoken shape (existing fields only, ordered)

Proposed default brief payload, in order, naming the exact field each item comes from:

1. `continuity["situation"]` — `project_continuity.py:389` key `"situation"`.
2. `continuity["next_useful_step"]` — key `"next_useful_step"`.
3. `continuity["next_useful_why"]` — key `"next_useful_why"` (skip the line if `None`).
4. A short status phrase derived from `startup_context["readiness"]["overall"]` (`orchestrator.py:7924`, field `overall` on the `EngineeringReadinessResult` dataclass) — e.g. map `"ASSEMBLY_READY"` → "listo para ensamblar" / anything else → "no listo para ensamblar," mirroring the existing `PROJECT STATUS:` line text at `main.py:230` without rendering the subsystem table around it.
5. `startup_context["readiness"]["prioritized_gaps"][0]["title"]` when the list is non-empty (`orchestrator.py:7924` → same dataclass, field `prioritized_gaps`; title rendered today at `main.py:242`) — one gap, title only.

**Explicitly excluded from the brief default:** `continuity["evidence"]`, `component_bom_lines`, the full readiness subsystem table, `propulsion_resolution`/`motor_operating_point_electrical`/`hover_energy`/`battery_endurance`, `prop_energy_block_closure`, `explain_topics`/Conceptos. All of these stay screen-only by default and move to "speak-on-request" under Q6's full-mode trigger — never silently dropped from the screen, only from the default spoken brief.

This shape already exists in miniature as `coherence_footer`/`result["continuity"]` (items 1–3); items 4–5 are the only two *new* extractions a future IC would add, and both are single-field reads off an already-computed dataclass — no new computation, no LLM.

---

## Q6 — Full-on-request (recommendation, not implemented)

Recommend a **chat command phrase**, following the exact precedent already in the codebase for `estado` itself: `CONTINUITY_DEFER_PHRASES` (`jarvis/config.py:51-61`) is a finite, pre-normalized phrase set matched with zero LLM inside `try_defer_to_continuity_task` (`jarvis/intelligence/assistant_task.py:394-429`), intercepted in `_handle_global_commands` before any classify/LLM call (`orchestrator.py:423-538`). A future Buy can add a small sibling phrase set (e.g. `"estado completo"`, `"cuéntame todo"`, `"completo"`) through the same intercept point, flagging the resulting `project_status`/turn result so `run_chat`'s speak call renders the full wall instead of the Q5 brief for that one turn only — session state does not need to persist the choice.

A secondary, narrower option — a one-off `--voice-speak-full` CLI flag that forces full speech every turn for scripted/testing use — is useful for CI/demo recording (mirrors `--voice-speak` itself) but should **not** be the Engineer's primary interactive path; the command-phrase route is cheaper (no new flag to remember) and matches how `estado` itself already works. Either way, this must not change bare `--chat`'s default (text-only) or `--chat --voice-speak`'s default (brief) behavior — both are strictly additive.

---

## Q7 — Non-Continuity turns (rule per class)

| Class | Example | Rule |
|---|---|---|
| Short Skill "Acción ejecutada" reply | `armar`/`hold`/`land`/`takeoff`/… | **speak-as-printed** — already one–two sentences; `attach_project_coherence` never fires for these (not in its `coherent_actions` set, `orchestrator.py:1550-1559`), so there is no footer to extract from even if we wanted one |
| Interactive wizard prompts | startup project pick, `define_missing_params`, structural-change confirm | **speak-as-printed** — the `interactive` status shape (`error`+`question`) is already a short couplet (`render_response`, `main.py:546-555`) |
| Errors / Safety rejects | `status == "error"`, Safety `reject`/`disarmed` messages | **speak-as-printed** — short, operationally load-bearing; must stay must-speak-brief, never screen-only |
| Full Continuity wall (project load / `estado`) | `main.py:1003-1005` and `render_response`'s `project_status` branch (`main.py:560-574`) | **brief-extract** by default (Q5 shape); full on request (Q6) |
| Calculate/iterate/simulate with a coherence footer | any `coherent_actions` member once `continuity.situation`/`next_useful_step` exists | **brief-extract** using the *same* Q5 shape — the coherence footer already *is* a subset of Q5's inputs (`situation`/`next_useful_step`/`next_useful_why`), so no separate rule is needed |
| Calculate/iterate/simulate **without** a coherence footer (rare — e.g. `create_project` before any Continuity exists) | falls through to the `reasoning` block (`main.py:696-734`) | **speak-on-request** — dense, multi-part (insights/tradeoffs/PRIORIDAD CRÍTICA/Evitar); a future IC should speak only the top `PRIORIDAD CRÍTICA` action's label by default, full detail on request — this is the one genuinely new judgment call for the future IC, flagged here rather than decided |

Note: because `attach_project_coherence`'s `return` in `render_response` happens **before** the `reasoning` block is ever reached (`main.py:679-694` returns early when `coherence` is truthy), the "no coherence footer" row above is the *only* path that still reaches `reasoning` in practice — confirmed by reading the branch order, not assumed.

---

## Q8 — Living map artifact

Delivered: [`.jes/artifacts/engineer_note_chat_spoken_continuity_map.md`](engineer_note_chat_spoken_continuity_map.md) — full surface/field inventory (Q1+Q2 tables, same citations) with the must-speak-brief/speak-on-request/screen-only classification (Q4) as its own column, plus the proposed norm header (Q9).

---

## Q9 — Process norm (draft, not applied)

Proposed `CLAUDE.md` clause (paste-ready for Engineer ★; **not** applied to `CLAUDE.md` in this INV):

> ### Chat / spoken-continuity egress map
>
> Whenever a Buy adds or changes a `--chat` print surface, a `build_startup_context`/`build_project_continuity` field, or any `render_*` function that produces chat egress, update `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` **in the same Buy** — add the new surface/field row and classify it (`must-speak-brief` / `speak-on-request` / `screen-only`). Do not leave the map stale; the spoken-continuity layer treats it as its single source of truth for what exists to classify.

**Landing recommendation:** land this clause in `CLAUDE.md` only after Engineer ★ on this INV's findings (not here), under a new short section (sibling to the existing "Tests" section) — and add one pointer line from `engineer_note_voice_phase_c_cola.md` to the living map, the same way that note already points at `USER_GUIDE_VOICE.md`.

---

## Q10 — Next-Buy recommendation

**Small DC, then IC — not a straight tiny IC.** Rationale: the DC needs to lock three product decisions the Engineer should ★ explicitly before any code — (a) the two-layer model (truth-print unchanged / spoken-continuity as a strictly additive extract), (b) the exact Q5 brief field list + Q4 classification table as the authoritative map, (c) the Q6 "completo" trigger shape (command phrase vs. flag). Once those are locked, the IC is narrow and mechanical: a new pure function (likely `adapters/voice/spoken_continuity.py::brief_continuity_text(...)`) consuming only existing dict fields, called from inside `_chat_speak_fn`'s `speak(...)` path only when the egress being spoken originated from a Continuity-shaped result — **truth `print()` calls in `run_chat` stay byte-identical**; only what gets handed to `speak_egress` changes. Tip/package for that code Buy is **TBD after DC/IC ★** (not this INV's package — stays `0.7.3`).

---

## Q11 — T40 / craft boundary

Confirmed: everything mapped here is **egress over today's existing `--chat` Continuity/Skill surface** — the same brain T34-DC locked, the same fields `render_startup_context`/`render_response` already print. **None of it is `world/` location resolution or voice-driven craft authority** (T40's own scope, still Parked with its own future DC).

What T40 would still need to classify in the living map **when it lands** (not now — these surfaces don't exist yet): any new `world`-aware craft egress it introduces (e.g. a future "ubicado en X" confirmation, or location-resolve prompts) would need its own new row in the map, per the Q9 norm — the map's structure already accommodates this (an open "future" note is left in the living map's header), but no placeholder row is invented here for something that doesn't exist in code yet.

---

## Q12 — Cola / PRIORIDAD

- **PRIORIDAD after this INV:** "T44-inv Implemented (Claude Code) — await Cursor review → Engineer ★ on findings → authorize small DC then IC for spoken-continuity (speak path only)."
- **T40** stays **Parked** — unaffected by this INV, confirmed in Q11.
- **Connect-plugs:** no new row needed — `a4-voice-world` (voice half ★ / world half pending T40) is unchanged; this INV is entirely inside the already-★-closed voice-half surface, adding a documentation/classification layer on top of it, not a new connect-plugs debt.

---

## Forensic method — what was actually re-run

1. **Re-verified tip `0.7.3`/T43** — read `run_chat`/`_chat_speak_fn`/`main()`'s `--voice-speak` wiring directly off disk (not from memory of implementing it) and re-ran the `inspect.getsource` zero-reference check (Q3). Confirmed unchanged since T43's own commit.
2. **Traced project-load Continuity** — `main.py:993-1017` → `orchestrator.build_startup_context()` (`orchestrator.py:7564`) → `render_startup_context` (`main.py:290-539`) → `speak(startup_block)` (`main.py:1005`). This is the exact "wall" path.
3. **Traced a short Skill turn and an `estado` turn** — confirmed `armar`/`hold` never enter `attach_project_coherence`'s `coherent_actions` set (`orchestrator.py:1550-1559`) and render via the plain `ok` branch (`render_response`, `main.py:590-598`); confirmed `estado` (via `CONTINUITY_DEFER_PHRASES`, `jarvis/config.py:51-61`) routes to `_handle_project_status` (`orchestrator.py:6799-6826`), which calls the **same** `build_startup_context`/`render_startup_context` pair as project load — same wall, different trigger.
4. **Inventoried `render_response`'s status branches** (`main.py:542-743`) and `render_startup_context`'s sections (`main.py:290-539`) line-by-line against the live file — not from the earlier T43 session's memory.
5. **Grepped the two Continuity builders** for field names directly off their `return` statements (`project_continuity.py:389-395`, `orchestrator.py:7862-7938`) — no aspirational field names invented.
6. **No second Continuity truth, no LLM summarizer proposed** — every recommendation above (Q4/Q5/Q6/Q7) extracts from fields that already exist and are already computed before `render_*` ever runs.

No `src/` file was modified. No test file was modified. `pyproject.toml` stays `0.7.3`.
