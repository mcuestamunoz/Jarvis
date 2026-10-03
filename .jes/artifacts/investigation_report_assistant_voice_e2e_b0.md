# Investigation Report — Assistant voice end-to-end (`INV-assistant-voice-e2e`, T34-inv)

**Project:** Jarvis
**Date:** 2026-10-03
**Investigator:** Claude Code (read-only forensic pass)
**Contract:** [`investigation_contract_assistant_voice_e2e_b0.md`](investigation_contract_assistant_voice_e2e_b0.md)
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ on findings. No `src/` mutation. No ACCEPT claim.
**Package:** tip stays `0.6.42` (docs/report only).

---

## 0. Forensic re-verify (method step 1)

The INV contract's seed cites T32 as "AUTHORIZED @ 0.6.41" via the connect-plugs map. Re-checked directly on this tip (`cursor/voice-e2e-investigation-ic-8ac5` @ `69273c5`, which stacks on T33's ACCEPT merge of T32):

```
$ grep -n "_resolve_go_to_destination\|parse_go_to_destination" src/jarvis/core/orchestrator.py src/jarvis/intelligence/assistant_task.py
src/jarvis/intelligence/assistant_task.py:365:def parse_go_to_destination(...)
src/jarvis/core/orchestrator.py:882:    def _resolve_go_to_destination(self, intent: Any) -> tuple[float, float] | None:
```

**Both symbols are landed on this tip** — unlike when T33's own report was written (where T32 lived only on a sibling, unmerged branch). `pytest -q` on this tip: `3962 passed, 9 skipped, 0 failed`. The connect-plugs map's `sd-go-to`/`go-to-metadata-plug-for-world` rows, written against an earlier tip, are now stale in one respect (they said "not yet landed") — Deliverable 4 below updates them with a one-line pointer, not a rewrite.

---

## 1. Happy-path trace (method step 2): `armar` → `hold` → `go to 1.0 2.0`

| Step | Call | File:line |
|---|---|---|
| 1 | CLI reads raw text | `input("User > ")` | `src/jarvis/adapters/cli/main.py:932` |
| 2 | Channel-agnostic entry | `orchestrator.handle_user_text(user_input, llm_interface)` | `src/jarvis/adapters/cli/main.py:975` → `src/jarvis/core/orchestrator.py:1548` |
| 3 | Snapshot wrapper → inner | `_handle_user_text_inner` | `src/jarvis/core/orchestrator.py:1550,1566` |
| 4 | Global command router (first check, always) | `_handle_global_commands(user_input)` | `src/jarvis/core/orchestrator.py:1568` → `:407` |
| 5a | `armar`: classify | `Intent = TerminalIntentAdapter.parse(stripped)` then `try_request_arm_policy_task(arm_intent)` | `src/jarvis/core/orchestrator.py:559` → `src/jarvis/intelligence/assistant_task.py:441` |
| 5b | `armar`: Skill gate | `run_skill("skill.request_arm_policy")` → policy gate-only `ok` | `src/jarvis/capabilities/skills_runtime.py:189,244` |
| 5c | `armar`: fulfill | `_handle_arm_policy` → `gate.arm()` on the shared `ArmedAllowlistSafetyGate` | `src/jarvis/core/orchestrator.py:870` |
| 6a | `hold`: classify + Skill gate + fulfill | `try_request_hold_task` → `run_skill("skill.request_hold")` (vehicle gate) → `_handle_vehicle_hold` → `propose_command`/`submit_command` → `allow` → `_sim_autonomy_tick_note(HOLD)` | `src/jarvis/core/orchestrator.py:602,608,897` |
| 7a | `go to 1.0 2.0`: classify | `try_request_go_to_task` now accepts bare `VEHICLE_GO_TO_PHRASES` **or** `parse_go_to_destination` match | `src/jarvis/intelligence/assistant_task.py:709` |
| 7b | `go to 1.0 2.0`: Skill gate | `run_skill("skill.request_go_to")` (vehicle gate) | `src/jarvis/capabilities/skills_runtime.py:230` |
| 7c | `go to 1.0 2.0`: fulfill | `_handle_vehicle_go_to` → `_resolve_go_to_destination(intent)` → `(1.0, 2.0)` → `propose_command(params={"x_m":"1.0","y_m":"2.0"})` → `allow` → `_sim_autonomy_tick_note(GO_TO, x_m=1.0, y_m=2.0)` — real tick, not sin-destino | `src/jarvis/core/orchestrator.py:882,961` |
| 8 | Egress | `render_response(result)` → `print(f"Jarvis > {...}")` | `src/jarvis/adapters/cli/main.py:542,984` |

**What a voice twin would call, if it existed today:** everything from step 2 onward is identical — `handle_user_text` takes a plain `str`, not a CLI-specific object. The only two things a voice loop needs that don't exist yet: (a) something upstream of step 2 that turns audio into that `str` (external STT, Q4), and (b) a different step 8 (TTS-shaped text, Q5). Step 5a's `TerminalIntentAdapter.parse(stripped)` — and the twelve other call sites just like it (§2 below) — would mislabel a voice-origin turn as `source=IntentSource.TERMINAL`; today there is no parameter on `handle_user_text` to carry the real channel through to those calls.

**Independent confirmation that step 2 is already channel-agnostic in practice, not just in theory:** `src/jarvis/adapters/mcp/session_manager.py:44-54` (`JarvisSessionManager.chat`) is a **second real caller** of `handle_user_text`, for the MCP server — and it reuses `render_response`/`render_startup_context` from the CLI module (`session_manager.py:23`) rather than inventing its own renderer. Two channels already share one brain and one renderer; a third (voice) is additive, not a rewrite.

---

## 2. Craft-path trace (method step 3): wizard / Continuity, and whether voice v1 should include it

`estado` (project status) is itself one of the twelve Skill-first Skills (`skill.project_status`, gated at `src/jarvis/core/orchestrator.py:508-524`) — it is **not** the craft path the INV means to flag. The real craft path lives *below* `_handle_global_commands`, inside `_handle_user_text_inner` (`src/jarvis/core/orchestrator.py:1566` onward): session-mode state machine (`OrchestratorMode.IDLE` / `DEFINE_MISSING_PARAMETERS` / etc.), catalog rebind triage (`resolve_idle_catalog_rebind`, `:1611`), structural-change confirmations, parameter-definition wizards, proactive "¿Definimos X ahora?" prompts, and LLM-backed design reasoning — none of this is reached via `run_skill`; it is the pre-Skill-first craft brain (frame/motor/battery/ESC/etc. design), multi-turn and stateful.

Traced one concrete instance: `render_startup_context` (`src/jarvis/adapters/cli/main.py:290`) — the function every wizard/Continuity reply eventually renders through — builds output with `"─" * 44` separator rules, bulleted evidence lists (`"   • {item}"`), and multi-section headers ("Situación:", "Evidencia:", "Siguiente paso:"). This is **screen-shaped text**, not spoken text; reading it aloud verbatim would be confusing (a wall of bullets and separator characters) even though it would not crash.

**Recommendation for voice v1: exclude the craft path.** It is large, multi-turn, console-table-heavy (catalog listings, numeric parameter tables), and already explicitly out of the twelve Skill-first Skills per the Skill-first DC's own phase boundary. Voice v1 should cover only the Skill-first surface (Q3); the craft path becomes its own, later voice phase if the Engineer ever wants it (it would need its own egress redesign, not reuse of `render_startup_context` as-is).

---

## Q1 — Ingress boundary

**Exact symbols:**
- `IntentSource.VOICE = "voice"` — enum member, `src/jarvis/capabilities/intent.py:24`
- `Intent.metadata: dict[str, str]` — `src/jarvis/capabilities/intent.py:39`
- `VoiceIntentAdapter.parse(raw_payload: object) -> Intent` — always `raise NotImplementedError("voice intent ingress is not_implemented in C2")` — `src/jarvis/capabilities/intent.py:62-65`

**Payload shape recommendation:** `raw_text: str` (post-STT text), **not** audio bytes. Reasons:
1. `TerminalIntentAdapter.parse(raw_text: str) -> Intent` (`intent.py:57-59`) is the only adapter that ever produces a real `Intent`, and it takes exactly this shape. Mirroring it for voice (`VoiceIntentAdapter.parse(raw_text: str) -> Intent` returning `Intent(source=IntentSource.VOICE, raw_text=raw_text)`) is the thinnest possible honest seam — same shape, different tag, zero new concepts.
2. Taking audio bytes would require an STT dependency *inside* `jarvis.capabilities` (currently zero speech packages anywhere in the dependency tree, §Q4) and would blur the C2 Intent-ingress boundary that already exists to keep "what was asked" separate from "how it arrived."
3. `Intent.metadata: dict[str, str]` is exactly the connect plug T32 already proved out for GO_TO coordinates (`go_to_x_m`/`go_to_y_m`) — a voice adapter populating e.g. a confidence score or raw STT transcript alongside `raw_text` would use the same mechanism, no new field type needed.

**The real gap this exposes (ties to Q2):** even once `VoiceIntentAdapter.parse` exists and is called, `handle_user_text(user_input: str, llm_interface)` has no parameter to carry `IntentSource.VOICE` down into the thirteen `TerminalIntentAdapter.parse(stripped)` call sites inside `_handle_global_commands` (§Q2 below) — those always construct `Intent(source=IntentSource.TERMINAL, ...)` regardless of true origin. **Filling `VoiceIntentAdapter.parse` alone is necessary but not sufficient** for an honest voice-tagged Intent to reach classify; threading a `source` parameter through is part of the first code Buy (§ phase plan).

## Q2 — Chat brain reuse

**The chain:** CLI (`run_chat`, `main.py:917`) → `orchestrator.handle_user_text(str, llm)` (`main.py:975` → `orchestrator.py:1548`) → `_handle_user_text_inner` (`:1566`) → `_handle_global_commands` (`:407`, first check always) → per-kind `TerminalIntentAdapter.parse` + `try_request_*_task` classify (thirteen call sites, `:478,507,559,577,602,629,662,692,723,751,780,808` — one per: explain, Continuity-defer, ARM, DISARM, HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, FOLLOW, PATROL, CHARGE) → `run_skill(skill_id)` (`skills_runtime.py:189`) → existing `_handle_*` fulfill methods.

**Channel-agnostic (reuse unchanged):**
- `handle_user_text(user_input: str, llm_interface) -> dict` itself — takes a plain string, proven by two real callers today (CLI `main.py:975`, MCP `session_manager.py:47`).
- Every `try_request_*_task` classify function in `assistant_task.py` — takes an `Intent`, has zero CLI awareness.
- `run_skill` and every gate (`_vehicle_skill_gate`, `_device_skill_gate`, `_POLICY_GATE_SKILL_IDS` branch) in `skills_runtime.py`.
- Every `_handle_*` fulfill method on `JarvisOrchestrator` (e.g. `_handle_vehicle_hold`, `_handle_arm_policy`, `_handle_ops_charge`) — none reads anything terminal-specific (no `input()`/`print()`/ANSI).
- `render_response`'s **input contract** (`dict -> str`) — any channel can hand it a result dict.

**Terminal-coupled (need a peer or a small generalization):**
- The thirteen `TerminalIntentAdapter.parse(stripped)` call sites inside `_handle_global_commands` — hardcode `source=IntentSource.TERMINAL`. Needs either (a) a `source` parameter threaded from `handle_user_text` down to each site, or (b) each site swapped for a shared helper `self._parse_intent(stripped)` that reads a session/call-scoped channel flag.
- `run_chat()` itself (`main.py:917-984`) — the `input()`/`print()` loop, project-selection bootstrap, and `KeyboardInterrupt`/`EOFError` handling are all terminal-specific; a voice loop needs its own outer loop (audio in → STT → `handle_user_text` → TTS → audio out), not this one.
- `render_response`'s **output shape** — screen-formatted text (separators, bullets, "Acción ejecutada:" prefixes); fine as a *bootstrap* egress for voice v1 (§Q5), but a dedicated voice-friendly renderer is a natural later-phase polish.
- `render_startup_context` (`main.py:290`) — same concern, more acute (dash separators, bulleted evidence) — this is the craft-path renderer, already recommended out of voice v1 (§2 above).

## Q3 — Surface inventory (today)

| Surface | Reachable via | Voice v1? | Why |
|---|---|---|---|
| (a) Skill-first twelve Skills (explain, project_status, HOLD…PATROL, ARM/DISARM, CHARGE) | `run_skill` through `_handle_global_commands` | **Yes** | Channel-agnostic by construction (Q2); short, single-turn, honest-reject/allow replies — the best-shaped surface for speech |
| (b) Craft Continuity/wizards (frame/motor/battery/ESC design, parameter-definition sessions, proactive suggestions) | `_handle_user_text_inner`'s session-mode machinery, below the global-command router | **No, defer** | Multi-turn, stateful, LLM-backed, catalog-table-heavy egress (§2) — needs its own voice-UX phase, not a v1 freebie |
| (c1) `jarvis explain <query>` standalone subcommand | `main.py` `explain` subparser → `run_explain_cli` directly (`intelligence/explain.py:92`) | **Never as-is** | Bypasses `run_skill`/orchestrator entirely; redundant with the chat `explain` intercept, which *is* Skill-first (`handle_explain_intent` → `run_skill`, `orchestrator.py:478-481`). A voice "explain" request should go through the chat intercept, not this standalone path |
| (c2) `jarvis board` (spatial board visor) | `main.py` `board` subparser → `launch_board` | **Never** | Visual GUI; has no voice-shaped analogue |

## Q4 — Audio I/O (STT/TTS)

**Confirmed absence:** `pyproject.toml` dependencies are exactly `pydantic>=2.0` (+ dev `pytest`, optional `mcp`) — zero speech packages. A repo-wide case-insensitive search for `whisper`, `speech_recognition`, `pyttsx`, `text_to_speech`, `elevenlabs`, `vosk`, `sounddevice`, `pyaudio` under `src/jarvis/` returns **no genuine matches** (an initial broad grep hit was a false positive from unrelated substrings; a tightened re-check confirmed zero).

**Options, no vendor lock:**
- **(A) External STT → text into the adapter; TTS outside.** STT/TTS run as separate processes/services the Engineer picks later; `VoiceIntentAdapter.parse(raw_text: str)` only ever sees text (same shape as Q1). **Recommended** — keeps `jarvis.capabilities`/`jarvis.intelligence` free of audio deps (preserves the existing isolation fence pattern used for `jarvis.intelligence` vs `jarvis.core`/`flight_software`), no tip-pinned vendor SDK version, and matches the "thinnest honest seam" framing.
- **(B) In-repo adapters behind `NotImplementedError` until wired.** Ship typed `AudioInAdapter`/`AudioOutAdapter` interfaces now, implement later. Pro: names the shape early. Con: speculative — nothing today proves what a real STT/TTS integration needs; risks inventing an interface that doesn't fit the eventual vendor, which is exactly the "parallel brain" anti-pattern this INV must avoid.
- **(C) Defer audio entirely; first Buys are text-shaped voice Intent only.** Build and prove `VoiceIntentAdapter`/the `source`-threading fix (§Q2) with a **text** fixture standing in for "what STT produced" — identical in spirit to `RadioStubFrame` (`capabilities/radio.py:33`) standing in for "what came off the link" without decoding real RF. **Recommended, paired with (A)**: it proves the whole chain (ingress → classify → Skill → fulfill → egress) long before any real microphone exists, with zero audio dependency risk and zero tip pins.

## Q5 — Egress

Chat returns a `dict`; `render_response(result) -> str` (`main.py:542`) renders it for a screen. A clean voice-speak path: **an adapter after the result, never a fork of fulfill logic** — `_handle_*` methods and `run_skill` already produce the final honest message string inside `result["message"]`/`render_response`'s formatting; a voice egress only needs to turn that into TTS-ready text (or, for v1, literally hand `render_response`'s own output straight to an external TTS engine — most TTS reads prose fine and only mildly stumbles on a dash separator, which never appears in the Skill-first messages used in voice v1 since those are single-sentence, per §Q3(a)).

**Out of first phase:** a dedicated voice-tuned renderer (shorter phrasing, no "Acción ejecutada:" prefix, SSML hints). Reusing `render_response` unchanged for v1 is honest and sufficient — the twelve Skill-first messages are already short, single-sentence Spanish strings with no tables/bullets (verified by reading each `_handle_*` method's `message = (...)` construction across `orchestrator.py`), so the renderer concern is much smaller for voice v1's actual scope than it would be for the craft path.

## Q6 — GO_TO / metadata

T32's resolver (`_resolve_go_to_destination`, `orchestrator.py:882`) is **landed on this tip** (§0). Its two sources map directly onto voice:
1. **Metadata-only connect plug** (`intent.metadata["go_to_x_m"]`/`["go_to_y_m"]`) — the eventual target for a voice/world pipeline that resolves "the kitchen" or "waypoint 3" into real coordinates *before* handing text to the orchestrator. This is exactly the `go-to-metadata-plug-for-world` row in the connect-plugs map — still correct, no code change needed to support it once a world/NLU layer exists.
2. **Prove-now spoken coordinates** (`parse_go_to_destination`, `assistant_task.py:365`) — a user literally saying "go to one point zero two point zero" would need STT to transcribe into the exact text pattern `go to 1.0 2.0` (or `ir a`/`ve a`/`goto`), which is plausible but fragile for natural speech. **Recommendation:** voice v1 relies on the metadata plug path (source 1) being filled by whatever NLU/number-parsing a later phase adds, rather than depending on STT transcribing decimal-point speech into exact regex-matchable text. Deferred either way past v1 (§Q3(a) — v1 is the non-coordinate Skills: HOLD/LAND/TAKEOFF/RETURN_HOME/FOLLOW/PATROL/ARM/DISARM/CHARGE/explain/status, plus bare "go to" honest sin-destino).

## Q7 — `world/` and A4

**Not required for phase C.1** ("voz de principio a fin" using Jarvis as it exists). Confirmed directly: `ls src/jarvis/` has no `world` entry (`actions, adapters, capabilities, config.py, core, domains, flight_software, intelligence, knowledge, llm, main.py, memory, runtime, schemas, simulation, suggestions, tools, utils, vehicle_profiles, workspace` — no `world`). Placement DC (`design_contract_assistant_placement_b0.md` §2) already locks `world/` as "NOT ON DISK — candidate later," with Voice explicitly named a **separate**, already-stubbed ingress peer in the same DC row ("Voice remains an ingress in `capabilities/intent.py`… It is not the Assistant package").

**Explicit split recommended:** Phase C.1 (this INV's scope) = voice-over-existing-chat-surfaces, **zero** `world/` dependency — every Skill-first Skill today operates on the single active project/vehicle, never a multi-room graph. `world/` is a **sibling, later** Buy (its own DC) for when "go to the kitchen" needs a room graph to resolve a name into coordinates — at that point it feeds the *same* GO_TO metadata plug (Q6), it does not require redesigning voice ingress again.

## Q8 — Safety / authority

Confirmed, no change needed, no change recommended:
- `ArmedAllowlistSafetyGate._ALLOWED_VERBS` (`capabilities/safety.py:190`) is the single allow-list every vehicle verb goes through, armed or not — a voice-originated `armar`/`hold`/etc. would hit the exact same gate instance via the exact same `_handle_*` fulfill, with the exact same disarmed-by-default honesty. No voice-specific bypass exists or is proposed.
- `AuthoritySignal.source: AuthoritySource` is `Literal["radio", "api", "operator"]` (`capabilities/safety.py:97-103`) — **"voice" is not a member of this literal.** Voice cannot carry Authority (override/kill/mode) today even if someone tried; adding it would require an explicit type change plus a new Engineer ★, which this INV does not request and explicitly recommends against doing opportunistically.
- C5 radio dual-role (`capabilities/radio.py`) stays architecturally separate — `RadioIntentAdapter.parse` is still `NotImplementedError` (confirmed, `intent.py`) and `SimulatedRadioIngress` is a distinct, explicitly-simulated API (`radio.py:1-18` docstring) that the voice work does not touch, extend, or reuse.
- **Recommendation:** voice v1 adds zero new Authority surface. If a future phase ever wants "voice as a kill-switch," that is its own Engineer ★-gated decision, explicitly out of this INV and out of the phase plan below.

## Q9 — Phased CLI migrate

The authoritative source is the Skill-first DC's own phase table (`design_contract_assistant_chat_skill_first_b0.md:19`): **"C — channels: voz / world / CLI migrate | same Skills; new ingress only."** Operationally, given the code traced above, this means: the *Skills* never move or duplicate; what changes over time is which **ingress/egress adapter** sits in front of them. Three sub-steps, in an order that avoids a big-bang rewrite:

1. **Voice flag beside `--chat`** (not instead of it) — e.g. a `run_voice()` function parallel to `run_chat()` in `adapters/cli/`, reusing `handle_user_text`/`render_response` exactly as MCP's `session_manager.py` already does. Zero risk to the existing terminal path.
2. **Shared ingress helper extracted from the orchestrator** — the thirteen `TerminalIntentAdapter.parse` call sites (§Q2) collapse into one small helper that takes a `source: IntentSource` (defaulting to `TERMINAL` for every existing caller, so CLI/MCP behavior is byte-identical), used by both the CLI path and the new voice path. This is the "first code Buy" (§ phase plan) — small, mechanical, fully covered by existing regression tests plus a few new ones.
3. **Later, migrate the remaining craft CLI** (`jarvis explain` standalone, `board`) onto the same adapter pattern *if and when* that's ever wanted for voice — explicitly **not** part of reaching "voice end-to-end" for the Skill-first surface, since (c1)/(c2) in §Q3 are not v1 candidates. No migration of `board` is proposed ever (visual-only).

This order means every phase is shippable and testable alone, and the terminal/MCP channels are never put at risk while voice is built.

## Q10 — Phase plan

| Phase | Goal | In | Out | Depends on | Primary files likely touched | Risk if skipped |
|---|---|---|---|---|---|---|
| **V0 — DC voice/channels** | Lock the design before any code: adapter shape, `source`-threading approach, v1 scope = Skill-first only (no craft, no `world/`), STT/TTS as external (Q4 option A+C) | Design-only | Any `src/` change | This INV ★ | `.jes/artifacts/design_contract_*` (new) | Skipping straight to code risks re-deriving the same seam ad hoc per Buy, or coupling STT to craft |
| **V1 — Intent ingress prove-now** | Fill `VoiceIntentAdapter.parse(raw_text: str) -> Intent` (mirrors `TerminalIntentAdapter`, tags `IntentSource.VOICE`); thread an optional `source` parameter through `handle_user_text` → `_handle_global_commands` → the thirteen classify call sites (default `TERMINAL`, byte-identical for existing callers) | `VoiceIntentAdapter` fill, `source` threading, unit tests proving a voice-tagged Intent reaches classify | STT, TTS, a real voice loop, craft path | V0 ★ | `capabilities/intent.py`, `core/orchestrator.py` | Every later phase is blocked; this is the one truly new piece of code voice needs |
| **V2 — Text-shaped voice loop (fixture STT)** | A `run_voice()`-style loop, parallel to `run_chat()`, driven by a **text fixture** standing in for STT output (no real audio) — proves ingress→classify→`run_skill`→fulfill→`render_response` end-to-end for a voice-tagged turn | New thin CLI-adjacent adapter, fixture-driven tests | Real microphone/speaker I/O | V1 ★ | `adapters/cli/` (new function) or a new `adapters/voice/` module | Without this, V1's plumbing is unit-tested but never proven as one coherent turn |
| **V3 — Real STT wired (external, vendor TBD)** | Replace the V2 fixture with a real external STT call feeding the same `VoiceIntentAdapter.parse(raw_text)` seam | STT process/service integration, one explicit vendor choice (Engineer ★, not this INV) | TTS, craft path, `world/` | V2 ★ | a new adapter module; no change to `core`/`intelligence` | Deferring forever means "voice" stays a demo, never real input |
| **V4 — Real TTS wired (external, vendor TBD)** | Speak `render_response`'s output (reused as-is per Q5) through a real TTS engine | TTS process/service integration, one explicit vendor choice (Engineer ★) | A dedicated voice-tuned renderer (defer to V5+ if ever wanted) | V2 ★ (can run before or after V3) | a new adapter module | Deferring forever means voice is one-directional (speak-only, read-reply) |
| **V5 — Voice v1 ★ complete** | Engineer-facing milestone: V1–V4 together deliver "speak → Skill-first brain → spoken reply" for the twelve Skills, end-to-end, no craft/`world/` | Nothing new — this is the integration checkpoint | Craft path, `world/`, coordinate speech (Q6) | V1, V2, V3, V4 ★ | none (checkpoint) | — |
| **V6 — (optional, later, own DC) Craft/world/CLI-migrate phases** | Extend voice to the craft path and/or `world/`-backed location resolution, per Q2/Q3/Q6/Q7/Q9's explicit deferrals | Craft wizard voice-UX, `world/` package (its own DC), voice-tuned renderer | — | V5 ★ | TBD — new DC required | Not a blocker for "voice end-to-end" as the Engineer defined it in §0 of the INV contract |

Every phase reuses `run_skill` and existing `_handle_*` fulfills untouched; none introduces a parallel Skill runtime or a second orchestrator. V1 is the only phase that touches `core/orchestrator.py`'s dispatch shape (an additive, default-preserving parameter), and V2–V4 are purely new adapter-layer code.

## Q11 — First Buy recommendation

**DC first, then a tiny IC** — not straight to code. Recommended: **DC `B1-assistant-chat-voice-channels`** (locks V0's scope: adapter shape, `source`-threading approach, explicit v1-excludes-craft/world boundary, STT/TTS-as-external decision) → then **IC `B1-assistant-voice-intent-ingress`** (= phase V1 above: fill `VoiceIntentAdapter`, thread `source`, tests). This matches the INV contract's own expectation ("Expected: DC voice/channels block then first IC (likely Intent ingress prove-now)") and the established pattern every other phase of this project has followed (DC locks the design, IC implements one small slice).

## Q12 — Map / PRIORIDAD updates

**Connect-plugs map rows** (`engineer_note_connect_plugs_real_data_map.md`) — one-line pointers added (Deliverable 4 below), **status unchanged** (still OPEN/Parked, per the INV's explicit "do NOT mark debts CLOSED"):
- `voice-intent-ingress` (B) → pointer to this INV + the V1 phase recommendation.
- `a4-voice-world` (D) → pointer to this INV's phase table.
- `world-package` (D) → pointer to Q7's explicit split (world/ not needed for v1).
- `go-to-metadata-plug-for-world` (D) → pointer to Q6's metadata-plug recommendation; also note this row's earlier "not yet landed" caveat is now stale — T32 is landed on this tip (§0) — without rewriting the row's history.

**PRIORIDAD cola rows to add** (`docs/IMPLEMENTATION_TASKS.md`): a `T34-DC` row (voice/channels DC, Candidate — awaiting Engineer ★ on this INV's findings) and a parked `T35` placeholder row (voice Intent-ingress IC, blocked on T34-DC ★). Neither is authorized by this INV — they are queue placeholders for the Engineer to pick up, matching how every prior DC→IC handoff in this project has been queued.

---

## Deliverables checklist

- [x] 1 — `investigation_report_assistant_voice_e2e_b0.md` (this file) answers Q1–Q12 with file:symbol citations
- [x] 2 — Phase table (Q10, 7 phases) + first-Buy recommendation (Q11)
- [x] 3 — PRIORIDAD / `engineering_state.json` update: T34-inv **Implemented**, await Cursor review → Engineer ★ (no ACCEPT claim, no `src/` change — verified via `git status`)
- [x] 4 — One-line pointers on connect-plugs map voice rows (status left OPEN/Parked, not CLOSED)
