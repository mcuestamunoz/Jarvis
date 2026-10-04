# Connections Registry

Every directed edge in Jarvis that carries control, data, and/or state, as a first-class entity. Subsystem maps **reference** these by ID; they do not redefine them. IDs are stable within this map version (SYS-MAP-002); do not renumber on future edits — append new IDs, deprecate old ones in place with a note.

## Document structure (count correctly)

```text
CONNECTIONS.md
│
├── Canonical registry  ← THIS SECTION ONLY defines the connection count
│   └── 68 unique C-xxx  (ID space sparse through C-115)
│         66 🟢 connected · 1 ⛔ removed (C-032) · 2 🟡 partial
│
├── Derived / detail views  ← may repeat C-xxx for readability
│   └── "Detail — NN …" sections below; NOT additional connections
│
└── Forbidden transitions  ← 10 structural absences; NOT C-xxx registry edges
```

**FN-024 (2026-08-10):** C-042 flipped 🔴→🟢 (Plan→DSE now binds through a Handoff Context — see `HANDOFF_CONTEXT_DESIGN.md`); two new connections added, **C-105** (`_handle_engineering_intent` → create/replace context) and **C-106** (bound context → `_handle_explore` goal bind). Registry count moved **57 → 59**.

**FN-025 (2026-08-12):** C-025/C-044 flipped 🔴→🟢 (help + named goal now reaches the same Goal Plan path as FN-022/024, via `IntentResolver.ANALYZE_HELP_PATTERNS`/`ANALYZE_VERB_PATTERNS`). C-043 (H4) was the only remaining 🔴 in the registry — not touched by that cut.

**FN-026 (2026-08-12):** C-043 flipped 🔴→🟢 (a Goal Plan lever named by the user now preseeds the Iterate wizard's `variable` slot, via `handoff_matching.match_plan_lever` reading the active `handoff_context.levers` — C-105 stays the sole writer). **Registry was 58🟢 · 0🔴 · 1🟡 — H1–H4 all closed, only C-081 (H5, design-only, deferred) remained non-green.**

**ERF-1 (2026-08-18):** Four new connections added — **C-107** (authorities → `build_engineering_readiness`), **C-108** (readiness → Continuity catalog-gap ranking, 🟡 PARTIAL), **C-109** (startup context exposes `"readiness"`), **C-110** (CLI renders `ENGINEERING READINESS` block). Registry count moved **59 → 63**; **62🟢 · 0🔴 · 2🟡** (C-081 + C-108). Two forbidden absences added (Continuity→Readiness; persist `readiness.json`). Report: [`.jes/artifacts/implementation_report_erf1.md`](../../.jes/artifacts/implementation_report_erf1.md).

**ERF-2 (2026-08-19):** Two new connections added — **C-111** (`electrical_compatibility` pure checks → `build_engineering_readiness` gap generation), **C-112** (ESC acquisition routing in `orchestrator._handle_component_description` — out-of-scope explicit save). C-107 updated (9 subsystems, `electronics` added). C-110 updated (9 readiness lines). Registry count moved **63 → 65**; **64🟢 · 0🔴 · 2🟡** (C-081 + C-108). Report: [`.jes/artifacts/implementation_report_erf2.md`](../../.jes/artifacts/implementation_report_erf2.md).

**G23 (2026-08-20):** **C-032** flipped 🟢→⛔ **REMOVED** — FN-015 pending-help feature deleted in full (Brief replay, IDLE wizard auto-open). Replacement is **not** a new C-xxx: `is_define_missing_confusion_phrase` + `_define_missing_confusion_reask` (anti-LLM gate only; short re-ask in `DEFINE_MISSING`, `project_status` at IDLE). **C-038** callers updated (FN-015's `_help_current_pending_acquisition` removed). Registry: **63🟢 · 1⛔ · 2🟡** (C-032 removed; C-081 + C-108 partial). Report: [`.jes/artifacts/implementation_report_g23_remove_fn015.md`](../../.jes/artifacts/implementation_report_g23_remove_fn015.md).

**Motor OP Voltage Coherence (2026-09-01, v0.3.4):** No registry change. **C-030** / **C-091** detail updated: battery catalog bind still routes through `set_battery_component` only at the orchestrator layer, but that writer now **conditionally** re-calls `set_motor_component` when stored `propulsion_resolution` was never `voltage_validated` or is validated at an incompatible pack voltage — preserving the P2-2/IC2 lock when already validated at the same voltage. `library.resolve_operating_point` exact match now requires `voltage_v is not None`. Report: [`.jes/artifacts/implementation_report_motor_op_voltage_coherence.md`](../../.jes/artifacts/implementation_report_motor_op_voltage_coherence.md).

**Phase 2.5–2.7-B + Option A (2026-09-01):** No registry change. **C-060** detail: user `calcular`/`iterate`/simulate-rebuild wrap `build()` via `endurance_sweep_writer` (4S labeled L2, ephemeral). `CalculationEngine.build` stays opt-in; DSE apply stays a bare `build()`. Lab remainder is [`docs/HARDWARE_DEBT.md`](../HARDWARE_DEBT.md), not a map edge. **No new C-xxx.**

**Structure catalog + parts + IDLE rebind + plate multiplicity (2026-09-04→05):** No new C-xxx. **C-030** detail expanded to frame catalog pick / IDLE rebind / `frame_part_specs_from_catalog` (arm thickness + curated ordinal plates). Continuity/State/Acquisition maps synced. Structure close suite **2294**.

**Spatial board visor + B3 honest absence (2026-09-05→06):** No new C-xxx. `jarvis board` + `spatial_board.project_spatial_nodes` = derived presentation (C-094 class). **Continuity spatial assembly → `v0.4.0` (2026-09-08→10):** same projector/DTO path — envelopes + `declaredBoxPose` + `solidCopies`/offsets (quad-X + Main Plate corners for standoffs); UI composes multi-hop + assembly root. Feature lock: `.jes/artifacts/engineer_lock_continuity_spatial_assembly_feature.md`. Suite **2652**. Queue: `docs/IMPLEMENTATION_TASKS.md`.

**Board drag → Continuity pose B1 + Situar free camera (2026-09-10 → `v0.4.1`):** **C-113** — `POST /api/projects/:id/pose` → `board_pose_bridge.apply_drag_pose` → same `set_component_declared_box_pose` + persist to Vite `state_path`. Situar: free camera (no forced tilt), screen-plane drag follows cursor (inverse rotate), Shift = profundidad (`y_mm`), singleton-only, origin picker (never silent default). Standoff count gate B4-min. Suite **2669** · UI **80**. Artifacts: `.jes/artifacts/implementation_report_board_drag_pose_b1.md` · free-camera + situar UX reviews.

**Fase M mission craft ladder CLOSED (2026-09-16→18, `v0.4.2`):** No registry change. `library/cameras` (RunCam Phoenix 2) + `library/vtx` (HGLRC Zeus 800) full catalog families; mission Continuity ladder identity→mass→mount→autonomy-target→power→VTX→margin. New `video_link` architecture block (`vtx` key). Suite **3166** · UI **105**. Report: `.jes/artifacts/engineer_note_fase_m_closeout_m7.md`.

**Board Taller 3D + docs truth-sync (2026-09-20, `v0.4.3`):** No registry change. Board default tab → Taller 3D, mount-ancestor-chain inspector (reuses `ASSEMBLY_ROOT_CANDIDATE_ID`), overlap piece-picker, 3D dimming — all presentation-only, same C-094 class as the rest of the spatial board visor. Full `docs/` audit synced to code @ `v0.4.2`. Suite **3166** · UI **132**. Report: `.jes/artifacts/implementation_report_board_3d_first_inspector_b1.md`.

**Fase C C1–C5 scaffold note (2026-09-20):** **No new C-xxx.** Tagged tip **`v0.5.3`** (C4+C5 ACCEPT as one block; no `v0.5.2` tag). Packages under `src/jarvis/` remain structurally isolated (zero import from `core/`/`adapters/`/Board/`library/`). Suite **3236** · UI **132**. Details: `docs/PLATFORM_CAPABILITY_VISION.md` §13 · `docs/ARCHITECTURE.md` §1a–1e · `.jes/artifacts/engineer_note_docs_truth_sync_fase_c_2026_09_20.md`.

**Fase C C6–C35 + Taller CSS visor faces (2026-09-20→25, tip `v0.5.35`):** **No new C-xxx.** C6–C12 (Python control ladder rungs), C13–C24 (host C++ port + named control tick under `native/flight_control/`), C25–C27 (RC setpoint + stale/failsafe watch), C28 (UART byte port), C29–C30 (cited FLASH map + DFU-flashable LED image — desk hardware, unflashed by default), C31 (DShot 16-bit encode, RAM only), C32–C33 (SPI byte port `SpiBytePort`/`LoopbackSpi`/`ScriptedSpi`), C34 (`probe_rx`, a port **client**, not a gyro driver), C35 (1000-tick + stale-RC-failsafe density tests, `step`/`loop.*` unchanged), and Taller CSS visor faces (`cuboidFaceLayout`/`cylinderSolidLayout`, `ui/spatial-board/src/Solid3D.tsx`'s box/cylinder branches — a rendering fix, not a new solid type) all remain **structurally isolated**: zero import edge from `core/`/`adapters/`/orchestrator/Board/`library/` into any of `native/flight_control/`, `src/jarvis/capabilities/`, `src/jarvis/flight_software/`, `src/jarvis/vehicle_profiles/`, or the two new `ui/spatial-board/src/*Faces.ts` helpers (grep-verified per Buy, re-confirmed here). Canonical registry **unchanged** — still C-001…C-113. Suite **3691** · UI vitest **142** · host `ctest` **76/76**. None of this flies, reads a real gyro, or opens a chip SPI/DShot pin. Details: `docs/ARCHITECTURE.md` §1c · `docs/PLATFORM_CAPABILITY_VISION.md` §13 · `native/flight_control/README.md`.

**Capability registry product fill, T2 (2026-09-29, ★ ACCEPT CLOSED @ `v0.6.10`):** **No new C-xxx** — a data/schema fill inside `src/jarvis/capabilities/`, not a new edge. C1's checked-in `data/default_registry.json` (always empty since `v0.5.0`) now declares two `CapabilityRecord`s, `ontology.explain` and `engineering.continuity`, both `CapabilityAvailability.AVAILABLE` (new enum member) via one `ProviderKind.SOFTWARE` (new enum member) `ProviderRecord` each — the same two strings `jarvis.intelligence.assistant_task`'s `CAPABILITY_ONTOLOGY_EXPLAIN`/`CAPABILITY_ENGINEERING_CONTINUITY` already put on `Task.required_capability_ids` since T0/T1 (id-synced by test, not by import — `registry.py` does not import `jarvis.intelligence`). `CapabilityRegistry` still has zero dispatcher/execute/actuate method, still zero flight/vehicle/device row in the product seed, and the C1/C2 isolation proofs above are **unaffected** by this fill (their own now-stale "registry stays empty" sub-assertions were the one part of each that needed correcting — 39 Fase C test files plus C1's/C2's own dedicated capability tests, all fixed to assert the new honest shape instead of a blanket empty check, none weakened). Reports: `.jes/artifacts/implementation_report_capability_registry_product_fill_b1.md`.

**Extended by T3, registry coherence gate (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.11`):** **No new C-xxx** — still a soft-check inside `src/jarvis/intelligence/assistant_task.py`, not a dispatcher. Before returning a `Task`, both `try_explain_concept_task` and `try_defer_to_continuity_task` now call `_capabilities_known_in_default_registry`, which soft-checks every `required_capability_ids` entry against `CapabilityRegistry.load_default().get_capability(id) is not None` — membership only, never `availability`, never a provider call, fulfill paths unchanged. This **flips** T2's own "`assistant_task.py` does not import `jarvis.capabilities.registry`" note above: that one-way edge (`assistant_task` → `capabilities.registry`) is new and explicitly authorized by this Buy's IC (T2's own IC/DC had deliberately deferred it here). `registry.py` still does not import `jarvis.intelligence` — the reverse edge stays closed. On an unknown id, the emitter refuses (`None`), no `task_kind` written, same shape as any other classify-miss. Report: `.jes/artifacts/implementation_report_assistant_task_registry_coherence_b1.md`.

**Extended by T4, software Safety bridge (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.12`):** **No new C-xxx** — still inside `src/jarvis/intelligence/assistant_task.py` (plus a new gate class in `src/jarvis/capabilities/safety.py`), not a dispatcher and not a new C-010/C-021 branch. After T3's `_capabilities_known_in_default_registry` passes, both `try_explain_concept_task` and `try_defer_to_continuity_task` now also call a new `_software_safety_allows(intent_id, capability_ids)` helper, which builds a `SafetyRequest(action_id="capability:<id>[,<id>...]")` and asks a new `SoftwareCapabilitySafetyGate` (`gate_id="software_capability"`, in `jarvis.capabilities.safety`) to `evaluate(...)` it — `allow` iff every id is `available` *and* bound to a `software`-kind provider (T3's own check never reads either field). A reject → refuse (`None`), same untouched-metadata grain as T3. This adds a new intra-`capabilities/` edge, `safety.py` → `registry.py`/`schemas.py` (safety.py previously imported only `intent.py`) — `safety.py` still never imports `jarvis.intelligence`. `default_safety_gate()` (still `RejectAllSafetyGate`) and `ArmedAllowlistSafetyGate`'s allow-list/arm state are both byte-unchanged; this gate is never routed through the factory and answers a structurally different request shape (`capability:...`, never `autonomy:{verb}:{id}`). Report: `.jes/artifacts/implementation_report_assistant_software_safety_bridge_b1.md`.

**Extended by T5, Skills catalog seed (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.13`):** **No new C-xxx** — a data fill inside `src/jarvis/capabilities/data/default_registry.json`'s `skills` array, not a new edge; `assistant_task.py`, `safety.py`, `core/orchestrator.py`, and Continuity ranking are all byte-unchanged (`git diff` confirms zero lines touched in any of them). C1's checked-in seed (`skills: []` since `v0.5.0`) now declares two `SkillRecord`s, `skill.explain_concept` (`required_capability_ids=["ontology.explain"]`) and `skill.project_status` (`required_capability_ids=["engineering.continuity"]`), both `availability=stub` — declared catalog rows only, no Skill execution path anywhere in this package. The Assistant's Task classify (`try_explain_concept_task`/`try_defer_to_continuity_task`) never calls `registry.skills()` — a Skill row existing or not has zero effect on whether a Task is emitted; T0–T4's classify→registry-membership→Safety chain stays exactly as it was. Existing reject-on-load still catches a skill referencing an unknown capability id (re-verified by a dedicated test). The 39-file T2-era "Fase C isolation" cascade that still asserted `registry.skills() == []` (plus three dedicated assertions in T2's/C1's/C2's own suites, one of them a test *function name* that literally said `..._no_skills`) was adapted to assert the new, honest two-skill-id shape instead — same scripted-and-verified approach T2 used for its own capabilities/providers cascade, isolation/no-dispatch checks unchanged. Report: `.jes/artifacts/implementation_report_capability_skills_seed_b1.md`.

**Extended by T6, vehicle HOLD Task (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.14`):** **No new C-xxx** (IC §0 row 11 explicit lock), documented here as the same finite-phrase-table/Assistant-Task-seam pattern as C-010/C-114/C-021, not a new connection class, despite being the first Buy where `core/orchestrator.py` imports `jarvis.flight_software` at all. `jarvis.intelligence.assistant_task.try_request_hold_task` classifies `jarvis.config.VEHICLE_HOLD_PHRASES` into `Task(request_hold, required_capability_ids=["flight.hold"])` — T3-style membership check only (`_capabilities_known_in_default_registry`), **no** `SoftwareCapabilitySafetyGate` (IC §0 row 6: that gate only ever allows `available`+`software`, and the new `flight.hold` capability is seeded `not_implemented`+`vehicle`, deliberately neither). `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core` — fulfilling a matched Task is entirely `core/orchestrator.py`'s new `_handle_vehicle_hold` method: `propose_command(AutonomyVerb.HOLD, intent_id=...)` + `submit_command(cmd, gate)` through the existing C4 autonomy surface, with a **fresh `ArmedAllowlistSafetyGate` constructed per call and never armed** — `gate.arm()` does not appear anywhere on this path. `default_safety_gate()` (still `RejectAllSafetyGate`) is untouched and unused here. Wired into `_handle_global_commands` immediately after the existing Continuity-defer branch and before the final `return None` — precedence is explain → Continuity defer → HOLD → fallthrough, enforced both by that call order and by `try_request_hold_task`'s own internal guards against explain-shaped/Continuity-shaped input (mirrors T1's own explain guard). The registry gains a third capability/provider/skill row (`flight.hold`/`provider.flight_hold`/`skill.request_hold`); several Fase C/T2/T5-era test-suite boundary checks that asserted "core/adapters never reference `flight_software`/`ArmedAllowlistSafetyGate`" or "the seed has exactly two capabilities/providers/skills, all software" were adapted to allow-list this one new, intentional exception (`core/orchestrator.py` specifically, nothing else) — no other isolation/no-dispatch check was weakened. Report: `.jes/artifacts/implementation_report_assistant_vehicle_hold_task_b1.md`.

**Extended by T7, vehicle LAND Task (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.15`):** **No new C-xxx** (IC §0 row 12 explicit lock), same seam as T6's HOLD note above — no new connection class. `jarvis.intelligence.assistant_task.try_request_land_task` classifies `jarvis.config.VEHICLE_LAND_PHRASES` into `Task(request_land, required_capability_ids=["flight.land"])` — same T3-style membership check, no `SoftwareCapabilitySafetyGate`, same reasoning. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`. Fulfilling a matched Task is `core/orchestrator.py`'s new `_handle_vehicle_land` method — thin duplication of `_handle_vehicle_hold`'s own shape (`propose_command(AutonomyVerb.LAND, intent_id=...)` + `submit_command(cmd, gate)` through the same C4 surface, same fresh-never-armed `ArmedAllowlistSafetyGate` policy, `action="vehicle_land"`) rather than a shared multi-verb helper — DC's own "Not" list explicitly excludes collapsing HOLD+LAND into a generic framework this Buy, and `_handle_vehicle_hold` itself is left byte-for-byte unchanged so HOLD's own tested behavior cannot regress. Wired into `_handle_global_commands` immediately after the HOLD branch and before the final `return None` — precedence is explain → Continuity defer → HOLD → LAND → fallthrough, enforced both by that call order and by `try_request_land_task`'s own internal guards against explain-, Continuity-, *and* HOLD-shaped input (a direct caller cannot have HOLD's phrases stolen by LAND). The registry gains a fourth capability/provider/skill row (`flight.land`/`provider.flight_land` — a **separate** provider from `provider.flight_hold`, per DC §0 row 5's explicit no-merge lock — /`skill.request_land`), keeping every HOLD/software row byte-unchanged. The same allow-listed `core/orchestrator.py` exception T6 established in several Fase C/T2/T5/T6-era boundary tests needed no further change (it excludes the file by identity, not by verb); their skill/capability-count assertions were extended from three to four ids. T6's own regression suite (`tests/test_assistant_vehicle_hold_task_b1.py`) re-verified green throughout. Report: `.jes/artifacts/implementation_report_assistant_vehicle_land_task_b1.md`.

**Extended by T8, vehicle GO_TO Task (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.16`):** **No new C-xxx** (IC §0 row 12 explicit lock), same seam as T6/T7's own notes above. `jarvis.intelligence.assistant_task.try_request_go_to_task` classifies `jarvis.config.VEHICLE_GO_TO_PHRASES` into `Task(request_go_to, required_capability_ids=["flight.go_to"])` — same T3-style membership check, no `SoftwareCapabilitySafetyGate`. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`. Fulfilling a matched Task is `core/orchestrator.py`'s new `_handle_vehicle_go_to` method — thin sibling of `_handle_vehicle_hold`/`_handle_vehicle_land` (`propose_command(AutonomyVerb.GO_TO, intent_id=..., params={})` — **empty `params`, no coordinate/waypoint parsing this Buy, DC §0 row 9** — + `submit_command(cmd, gate)` through the same C4 surface, same fresh-never-armed `ArmedAllowlistSafetyGate` policy, `action="vehicle_go_to"`) rather than a shared multi-verb helper — IC's own "Not" list explicitly excludes a generic multi-verb framework, and both `_handle_vehicle_hold` and `_handle_vehicle_land` are left byte-for-byte unchanged (`git diff` confirms zero removed/modified lines in `orchestrator.py`, only additions). Wired into `_handle_global_commands` immediately after the LAND branch and before the final `return None` — precedence is explain → Continuity defer → HOLD → LAND → GO_TO → fallthrough, enforced both by that call order and by `try_request_go_to_task`'s own internal guards against explain-, Continuity-, HOLD-, *and* LAND-shaped input. The registry gains a fifth capability/provider/skill row (`flight.go_to`/`provider.flight_go_to` — its own **separate** provider, distinct from `provider.flight_hold`/`provider.flight_land` — /`skill.request_go_to`), keeping every HOLD/LAND/software row byte-unchanged. The same allow-listed `core/orchestrator.py` exceptions T6 established needed no further change (they exclude the file by identity, not by verb); the cascade's skill/capability-count assertions were extended from four to five ids, scripted and verified the same way as every prior round, with no cascade-adaptation gap this time (unlike T7's own turn, where this step was initially missed and caught by a broader regression run — see that report's own §2). Both HOLD's (`tests/test_assistant_vehicle_hold_task_b1.py`) and LAND's (`tests/test_assistant_vehicle_land_task_b1.py`) own regression suites re-verified green throughout. Report: `.jes/artifacts/implementation_report_assistant_vehicle_go_to_task_b1.md`.

**Extended by T9, vehicle TAKEOFF Task (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.17`):** **No new C-xxx** (IC §0 row 12 explicit lock), same seam as T6/T7/T8's own notes above. `jarvis.intelligence.assistant_task.try_request_takeoff_task` classifies `jarvis.config.VEHICLE_TAKEOFF_PHRASES` into `Task(request_takeoff, required_capability_ids=["flight.takeoff"])` — same T3-style membership check, no `SoftwareCapabilitySafetyGate`. `assistant_task.py` still never imports `jarvis.flight_software`/`jarvis.vehicle_profiles`/`jarvis.core`. Fulfilling a matched Task is `core/orchestrator.py`'s new `_handle_vehicle_takeoff` method — thin sibling of `_handle_vehicle_hold`/`_handle_vehicle_land`/`_handle_vehicle_go_to` (`propose_command(AutonomyVerb.TAKEOFF, intent_id=..., params={})` — **empty `params`, no altitude parsing this Buy, DC §0 row 9** — + `submit_command(cmd, gate)` through the same C4 surface, same fresh-never-armed `ArmedAllowlistSafetyGate` policy, `action="vehicle_takeoff"`) rather than a shared multi-verb helper — IC's own "Not" list explicitly excludes a generic multi-verb framework, and all three earlier fulfill methods are left byte-for-byte unchanged (`git diff` confirms zero removed/modified lines anywhere in `orchestrator.py`, only additions). Wired into `_handle_global_commands` immediately after the GO_TO branch and before the final `return None` — precedence is explain → Continuity defer → HOLD → LAND → GO_TO → TAKEOFF → fallthrough, enforced both by that call order and by `try_request_takeoff_task`'s own internal guards against explain-, Continuity-, HOLD-, LAND-, *and* GO_TO-shaped input. The registry gains a sixth capability/provider/skill row (`flight.takeoff`/`provider.flight_takeoff` — its own **separate** provider, distinct from the three earlier vehicle providers — /`skill.request_takeoff`), keeping every HOLD/LAND/GO_TO/software row byte-unchanged. `ArmedAllowlistSafetyGate`'s own allow-list stays `{HOLD, LAND, GO_TO}` — TAKEOFF was deliberately not added (DC §0 row 7): irrelevant on the always-disarmed product path (still `"disarmed"` either way), but an armed caller would get `verb_not_allowed` for TAKEOFF specifically until a separate, later allow-list-widening Buy. The same `core/orchestrator.py`-only allow-list exceptions T6 established needed no further change; the cascade's skill/capability-count assertions were extended from five to six ids, run proactively immediately after wiring the orchestrator (applying the cascade-timing lesson from T7's own report — no gap this time, same clean result as T8). HOLD's, LAND's, and GO_TO's own regression suites all re-verified green throughout. Report: `.jes/artifacts/implementation_report_assistant_vehicle_takeoff_task_b1.md`.

**Extended by T10, vehicle RETURN_HOME Task (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.18`):** **No new C-xxx**. Fifth vehicle Task kind — closes basic mando set (TAKEOFF/HOLD/GO_TO/RETURN_HOME/LAND). `try_request_return_home_task` + `VEHICLE_RETURN_HOME_PHRASES` (exact match only; short words `casa`/`home`/`volver` do not steal longer craft lines). Membership only; fulfill via `_handle_vehicle_return_home` with empty params. At Buy time allow-list still `{HOLD,LAND,GO_TO}` — **superseded by T14**. Precedence: explain → defer → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME. Report: `.jes/artifacts/implementation_report_assistant_vehicle_return_home_task_b1.md`.

**Extended by T11, vehicle Safety arm UX (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.19`):** **No new C-xxx**. Not a sixth AutonomyVerb. `try_request_arm_policy_task` / `try_request_disarm_policy_task` + `VEHICLE_ARM_PHRASES` / `VEHICLE_DISARM_PHRASES` → `safety.chat_armed_allowlist` (`available`+software) through T4 `SoftwareCapabilitySafetyGate`. Orchestrator owns one process-scoped `ArmedAllowlistSafetyGate`; vehicle fulfills submit through it (five at T11; seven after T12/T13). At Buy time allow-list unwidened — **superseded by T14**. Precedence: explain → defer → ARM → DISARM → HOLD → … → RETURN_HOME (later + FOLLOW/PATROL). Review: `.jes/artifacts/implementation_review_assistant_vehicle_arm_ux_b1.md`.

**Extended by T12, vehicle FOLLOW Task (2026-09-30, ★ ACCEPT CLOSED @ `v0.6.20`):** **No new C-xxx**. Sixth vehicle Task kind. `try_request_follow_task` + `VEHICLE_FOLLOW_PHRASES` → `flight.follow` (`not_implemented`+vehicle), membership only. Fulfill via shared T11 ArmedAllowlist. At Buy time allow-list unwidened (FOLLOW → `verb_not_allowed` when armed) — **superseded by T14** (armed FOLLOW → `allow`/`not_implemented`). Empty params — no person/target. Precedence: … → RETURN_HOME → **FOLLOW** → fallthrough. Review: `.jes/artifacts/implementation_review_assistant_vehicle_follow_task_b1.md`.

**Extended by T13, vehicle PATROL Task (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.21`):** **No new C-xxx**. Seventh and last vehicle Task kind — last C4 `AutonomyVerb` without a chat Task. `try_request_patrol_task` + `VEHICLE_PATROL_PHRASES` → `flight.patrol` (`not_implemented`+vehicle), membership only. Fulfill via shared T11 ArmedAllowlist. At Buy time allow-list unwidened (PATROL → `verb_not_allowed` when armed) — **superseded by T14**. Empty params — no waypoint/route parse. Precedence: … → FOLLOW → **PATROL** → fallthrough. Review: `.jes/artifacts/implementation_review_assistant_vehicle_patrol_task_b1.md`.

**Extended by T15, FN-016 RTL wizard precedence (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.23`):** **No new C-xxx** — routing honesty inside existing **C-010** / **C-034**. When `session.mode == DEFINE_MISSING_PARAMETERS`, `_handle_global_commands` runs FN-016 nav-back (`atrás`/`volver`/`vuelve` → cancel wizard) **before** the T10 RETURN_HOME vehicle intercept, so mid-wizard `volver` cannot be stolen as RTL. IDLE / non-wizard: RETURN_HOME path unchanged. Review: `.jes/artifacts/implementation_review_fn016_rtl_wizard_precedence_b1.md`.

**Extended by T16, ESC fence import-only (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.24`):** **No new C-xxx**. Suite honesty — AST/import-only fence for `SimulatedEscSink` / `flight_control.esc` in `core`/`adapters` (comments/docstrings allowed). No product routing change. Review: `.jes/artifacts/implementation_review_esc_fence_import_only_b1.md`.

**Extended by T14, chat allow-list widen (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.25`):** **No new C-xxx**. Safety-policy widen, not a new Task kind. **As-is tip:** `ArmedAllowlistSafetyGate._ALLOWED_VERBS` = all seven chat `AutonomyVerb` values `{HOLD,LAND,GO_TO,TAKEOFF,RETURN_HOME,FOLLOW,PATROL}`. After `armar`, every chat vehicle verb → Safety `allow` + execution `not_implemented`, never `"executed"`; `SimAutonomyExecutor` stays HOLD/LAND/GO_TO-only in sim, never wired from chat. Latch API and disarmed path unchanged. Review: `.jes/artifacts/implementation_review_assistant_vehicle_allowlist_widen_b1.md`.

**Extended by T17, suite tip-pin cleanup (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.26`):** **No new C-xxx**. Suite honesty only — retires tip/package version pin tests; policy guard forbids reintroducing them. No routing / authority / connection change. Review: `.jes/artifacts/implementation_review_suite_tip_pin_cleanup_b1.md`.

**Extended by T18, orchestrator fulfill docstring honesty (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.27`):** **No new C-xxx**. Comment/docstring honesty only, zero behavior change. Stale `verb_not_allowed`/"allow-list excludes" claims in the TAKEOFF/RETURN_HOME/FOLLOW/PATROL intercept comments and fulfill docstrings (left over from before T14's widen) corrected to the current seven-verb allow-list truth. Review: `.jes/artifacts/implementation_review_orchestrator_fulfill_docstring_honesty_b1.md`.

**Extended by T19, ops CHARGE Task (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.28`):** **No new C-xxx**. First **ops** Assistant Task kind — CHARGE is deliberately **not** an `AutonomyVerb`, so it never touches `ArmedAllowlistSafetyGate` at all (armed or disarmed makes no difference). `try_request_charge_task` + `OPS_CHARGE_PHRASES` → `ops.charge` (`not_implemented`+**device**, membership only, no `SoftwareCapabilitySafetyGate` either). Fulfilled in `_handle_ops_charge` — no `propose_command`/`AutonomyVerb`/sim executor; honest Spanish that charge ops are not implemented. Exact match only — never steals mission/payload lines ("carga util", "aumentar la carga"). Precedence: … → PATROL → **CHARGE** → fallthrough. Not real battery-charging hardware (parked until assembly). Review: `.jes/artifacts/implementation_review_assistant_ops_charge_task_b1.md`.

**Extended by T20, chat → sim copper (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.29`):** **No new C-xxx**. First Safety-`allow` → **sim** tick bridge for the chat vehicle path. `core/orchestrator.py` now owns one lazy, process-scoped `SimAutonomyExecutor` (C40) + `ToyQuad6DofPlant`; after Safety `allow` for HOLD/LAND/GO_TO only, it runs one `tick` and reports the sim outcome in the chat message — `submit_command`'s own `execution` field stays byte-unchanged at `"not_implemented"` (preferred path (a), C4 surface honesty untouched). TAKEOFF/RETURN_HOME/FOLLOW/PATROL still `allow` with **no** tick (unsupported by the sim executor). GO_TO's own chat path carries no coordinates (T8), so its tick attempt is caught and reported as sim-unavailable-without-a-target rather than invented. Disarmed path unchanged. Never imports `SimulatedEscSink`/`flight_control.esc` (T16 fence re-verified green). Three historical core/adapters isolation tests that pre-dated this Buy (`test_fase_c_autonomy_executor_b1.py`, `test_fase_c_controlled_flight_sim_tip_b1.py`, `test_fase_c_sim_6dof_plant_b1.py`) retargeted to exclude `orchestrator.py` by name — every other file under `core/`/`adapters/` still must never reference `SimAutonomyExecutor`/`ToyQuad6DofPlant`. Report: `.jes/artifacts/implementation_report_assistant_chat_sim_copper_b1.md`. **Software debt SD-GO_TO (OPEN):** chat GO_TO still has empty params (T8) while C40 requires `x_m`/`y_m` — T20 leaves the allow→tick seam and honest “sin destino” note; wire destination later. SoT: `.jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md`.

**Extended by T21, Skills runtime software-only (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.30`):** **No new C-xxx**. First Skill **runner** — `jarvis.capabilities.skills_runtime.run_skill` is a thin dispatcher: Skill lookup → `availability=available` required → same T4-shaped software Safety re-check → existing fulfill path. `skill.explain_concept`/`skill.project_status` flip from `stub` to `available`; every vehicle/ops Skill stays `stub`. One deliberate new edge (named here since it's not entirely avoidable): `jarvis.capabilities.skills_runtime` imports `jarvis.intelligence.assistant_task.fulfill_ontology_explain` (lazily, inside the function body) to reuse the explain cite path byte-for-byte rather than duplicating it — the first `capabilities → intelligence` import in this codebase; `skill.project_status`'s own Continuity formatting is instead *injected* by the caller (`project_status_provider`), so this module never imports `jarvis.core`. Chat Task classify untouched — `run_skill` is not wired into `_handle_global_commands` this Buy. Report: `.jes/artifacts/implementation_report_capability_skills_runtime_software_b1.md`.

**Extended by T22, chat Skill-first software (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.31`):** **No new C-xxx**. Chat explain fulfill goes through `run_skill("skill.explain_concept")`; Continuity defer is gated by `run_skill("skill.project_status")` then keeps `project_status`/`startup_context` shape. Vehicle/ops remain Task-direct at T22 ship. Report: `.jes/artifacts/implementation_report_assistant_chat_skill_first_software_b1.md`. Review ★: `.jes/artifacts/implementation_review_assistant_chat_skill_first_software_b1.md`.

**Extended by T23, chat Skill-first vehicle HOLD (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.32`):** **No new C-xxx**. First **vehicle** Skill-first slice: `skill.request_hold` → `available`; `run_skill` vehicle gate (membership + provider `kind==vehicle`) — not `SoftwareCapabilitySafetyGate` (`flight.hold` stays `not_implemented`). Chat `hold` → `run_skill` then `_handle_vehicle_hold` (ArmedAllowlist + T20 sim copper unchanged). Other vehicle/ops Skills stay `stub` at T23 ship. Review ★: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_hold_b1.md`.

**Extended by T24, chat Skill-first vehicle LAND (2026-10-01, ★ ACCEPT CLOSED @ `v0.6.33`):** **No new C-xxx**. Second vehicle Skill-first: `skill.request_land` → `available`; HOLD+LAND share `_vehicle_skill_gate` (`_VEHICLE_GATE_SKILL_IDS`); `flight.land` stays `not_implemented`. Chat `land` → `run_skill` then `_handle_vehicle_land`. Review ★: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_land_b1.md`.

**Extended by T25, chat Skill-first vehicle GO_TO (2026-10-02, ★ ACCEPT CLOSED @ `v0.6.34`):** **No new C-xxx**. Third vehicle Skill-first: `skill.request_go_to` → `available`; `_VEHICLE_GATE_SKILL_IDS` now `{skill.request_hold, skill.request_land, skill.request_go_to}`; `flight.go_to` stays `not_implemented`. Chat GO_TO phrase → `run_skill("skill.request_go_to")` → on `ok`, existing `_handle_vehicle_go_to` unchanged (empty params + ArmedAllowlist + T20 sim-copper honesty, including the "sin destino" note); on hard reject, honest "Skill … no disponible (reason)" — no silent Task-only fallback. **SD-GO_TO stays explicitly OPEN** — this Buy is gate-only, never a coordinate parse/invent. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_go_to_b1.md`.

**Extended by T26, chat Skill-first vehicle TAKEOFF (2026-10-02, ★ ACCEPT CLOSED @ `v0.6.35`):** **No new C-xxx**. Fourth vehicle Skill-first: `skill.request_takeoff` → `available`; `_VEHICLE_GATE_SKILL_IDS` now `{skill.request_hold, skill.request_land, skill.request_go_to, skill.request_takeoff}`; `flight.takeoff` stays `not_implemented`. Chat TAKEOFF phrase → `run_skill("skill.request_takeoff")` → on `ok`, existing `_handle_vehicle_takeoff` unchanged (empty params + ArmedAllowlist + allow/`not_implemented` honesty); on hard reject, honest "Skill … no disponible (reason)". **No sim tick added** — TAKEOFF is explicitly outside T20's HOLD/LAND/GO_TO tick set. SD-GO_TO untouched/OPEN. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_takeoff_b1.md`.

**Extended by T27, chat Skill-first vehicle RETURN_HOME (2026-10-02, ★ ACCEPT CLOSED @ `v0.6.36`):** **No new C-xxx**. Fifth vehicle Skill-first: `skill.request_return_home` → `available`; `_VEHICLE_GATE_SKILL_IDS` now `{skill.request_hold, skill.request_land, skill.request_go_to, skill.request_takeoff, skill.request_return_home}`; `flight.return_home` stays `not_implemented`. Chat RETURN_HOME phrase → `run_skill("skill.request_return_home")` → on `ok`, existing `_handle_vehicle_return_home` unchanged (empty params + ArmedAllowlist + allow/`not_implemented` honesty); on hard reject, honest "Skill … no disponible (reason)". **No sim tick added** — RETURN_HOME is explicitly outside T20's HOLD/LAND/GO_TO tick set. **FN-016 (T15) precedence unreordered** — the wizard nav-back cancel (`DEFINE_MISSING_PARAMETERS` + `is_navigation_back_phrase`) still runs before this intercept, regression-tested. SD-GO_TO untouched/OPEN. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_return_home_b1.md`.

**Extended by T28, chat Skill-first vehicle FOLLOW (2026-10-02, ★ ACCEPT CLOSED @ `v0.6.37`):** **No new C-xxx**. Sixth vehicle Skill-first: `skill.request_follow` → `available`; `_VEHICLE_GATE_SKILL_IDS` now `{skill.request_hold, skill.request_land, skill.request_go_to, skill.request_takeoff, skill.request_return_home, skill.request_follow}`; `flight.follow` stays `not_implemented`. Chat FOLLOW phrase → `run_skill("skill.request_follow")` → on `ok`, existing `_handle_vehicle_follow` unchanged (empty params + ArmedAllowlist + allow/`not_implemented` honesty); on hard reject, honest "Skill … no disponible (reason)" — no silent Task-only fallback. **No sim tick added** — FOLLOW is explicitly outside T20's HOLD/LAND/GO_TO tick set. No track/target invent. SD-GO_TO untouched/OPEN. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_follow_b1.md`.

**Extended by T29, chat Skill-first vehicle PATROL (2026-10-02, ★ ACCEPT CLOSED @ `v0.6.38`):** **No new C-xxx**. Seventh and last vehicle Skill-first: `skill.request_patrol` → `available`; `_VEHICLE_GATE_SKILL_IDS` now `{skill.request_hold, skill.request_land, skill.request_go_to, skill.request_takeoff, skill.request_return_home, skill.request_follow, skill.request_patrol}` — closes the full seven-verb chat AutonomyVerb Skill-first set; `flight.patrol` stays `not_implemented`. Chat PATROL phrase → `run_skill("skill.request_patrol")` → on `ok`, existing `_handle_vehicle_patrol` unchanged (empty params + ArmedAllowlist + allow/`not_implemented` honesty); on hard reject, honest "Skill … no disponible (reason)" — no silent Task-only fallback. **No sim tick added** — PATROL is explicitly outside T20's HOLD/LAND/GO_TO tick set. No route/circuit invent. Remaining Skill-first candidates are policy/ops (ARM/DISARM/CHARGE), not further AutonomyVerbs. SD-GO_TO untouched/OPEN. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_vehicle_patrol_b1.md`.

**Extended by T30, chat Skill-first policy ARM/DISARM (2026-10-03, ★ ACCEPT CLOSED @ `v0.6.39`):** **No new C-xxx**. First policy Skill-first: `skill.request_arm_policy` + `skill.request_disarm_policy` → `available`; **not** members of `_VEHICLE_GATE_SKILL_IDS` — after T4-shaped `SoftwareCapabilitySafetyGate` allow on `safety.chat_armed_allowlist` (`available`+`software`), `_POLICY_GATE_SKILL_IDS` returns gate-only `outcome="ok"` (no latch mutate inside `skills_runtime`). Chat ARM/DISARM phrases → `run_skill` → on `ok`, existing `_handle_arm_policy` / `_handle_disarm_policy` unchanged (process-scoped ArmedAllowlist latch — never ESC/motors/drone); on hard reject, honest "Skill … no disponible (reason)" — no silent Task-only fallback. Remaining Skill-first candidate is ops CHARGE. Seven vehicle Skill-first paths unchanged. SD-GO_TO untouched/OPEN. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_policy_arm_b1.md`.

**Extended by T31, chat Skill-first ops CHARGE (2026-10-03, ★ ACCEPT CLOSED @ `v0.6.40`):** **No new C-xxx**. First ops/device Skill-first (last chat Skill stub): `skill.request_charge` → `available`; **not** in `_VEHICLE_GATE_SKILL_IDS` / `_POLICY_GATE_SKILL_IDS` — `_DEVICE_GATE_SKILL_IDS` + `_device_skill_gate` (membership + provider `kind==device`) runs **before** `SoftwareCapabilitySafetyGate` (that gate would reject `not_implemented`+`device`); gate-only `outcome="ok"`. Chat CHARGE phrases → `run_skill` → on `ok`, existing `_handle_ops_charge` unchanged (honest not-implemented — never AutonomyVerb / ArmedAllowlist / real battery); on hard reject, honest "Skill … no disponible (reason)" — no silent Task-only fallback. `ops.charge` stays `not_implemented`+`device`. Closes twelve chat Skills Skill-first. SD-GO_TO untouched/OPEN. Review: `.jes/artifacts/implementation_review_assistant_chat_skill_first_ops_charge_b1.md`.

**Extended by T32, chat GO_TO destination (2026-10-03, ★ ACCEPT CLOSED @ `v0.6.41` — closes SD-GO_TO note):** **No new C-xxx**. Closes SD-GO_TO debt: `_resolve_go_to_destination` ordered (metadata `go_to_x_m`/`go_to_y_m` connect plug → `jarvis.intelligence.assistant_task.parse_go_to_destination` prove-now two-float parse on `go to|goto|ir a|ve a <x> <y>` → `None`). `try_request_go_to_task` now also accepts that destination-bearing pattern (not just bare `VEHICLE_GO_TO_PHRASES`); all five later sibling `try_request_*_task` (TAKEOFF/RETURN_HOME/FOLLOW/PATROL/CHARGE) plus ARM/DISARM refuse it so it can't be stolen. `_handle_vehicle_go_to` passes resolved coords into `propose_command` (`params` stays `dict[str,str]`) and the existing T20 `_sim_autonomy_tick_note` (now takes optional `x_m`/`y_m`; HOLD/LAND callers unchanged) → `SimAutonomyParams` when present; bare GO_TO keeps honest sin-destino note (N1 polish). `flight.go_to` stays `not_implemented`. Skill-first `run_skill("skill.request_go_to")` still gates first, unchanged. Not copper/ESC/GPS/voice. Review: `.jes/artifacts/implementation_review_assistant_chat_go_to_destination_b1.md`.

**Extended by T33, connect plugs / real-data debt map (2026-10-03, ★ ACCEPT CLOSED @ `v0.6.42`):** **No new C-xxx**. Docs-only living index `.jes/artifacts/engineer_note_connect_plugs_real_data_map.md` of connect-later seams (software plugs, honesty stubs, parked hardware/lab, voice/world horizon) — forensically re-verified, not a blind seed copy. Does not implement GPS/ESC/battery/voice; `sd-go-to` row updated CLOSED via stacked T32 ★. Review: `.jes/artifacts/implementation_review_connect_plugs_real_data_map_b1.md`.

**Extended by T34-inv, voice end-to-end investigation (2026-10-03, ★ ACCEPT CLOSED):** **No new C-xxx**. Docs-only INV — forensic map for Skill-first phase C voice. Review: `.jes/artifacts/investigation_review_assistant_voice_e2e_b0.md`.

**Extended by T34-DC, voice/channels block (2026-10-03, ★ CLOSED) + voice phase C cola:** **No new C-xxx**. Design lock for voice over existing Skill-first brain; cola T35…T38 @ `0.6.43`–`0.6.46`, **T39 product milestone `v0.7.0`**; T40 craft/world Parked. DC: `.jes/artifacts/design_contract_assistant_chat_voice_channels_b0.md` · cola: `.jes/artifacts/engineer_note_voice_phase_c_cola.md`.

**Extended by T35, voice Intent ingress (2026-10-03, ★ ACCEPT CLOSED @ tip `v0.6.43`):** **No new C-xxx**. `VoiceIntentAdapter.parse` fills (mirrors `TerminalIntentAdapter`, tags `IntentSource.VOICE`; Radio/Api unchanged, still `NotImplementedError`). `handle_user_text` → `_handle_global_commands` thread an optional keyword-only `source` (default `TERMINAL`); the twelve classify sites collapse into one shared `_parse_intent(raw_text, source)` helper. No STT/TTS/loop/craft/world/Authority-from-voice yet. Review: `.jes/artifacts/implementation_review_assistant_voice_intent_ingress_b1.md`.

**Extended by T36, voice fixture loop (2026-10-03, ★ ACCEPT CLOSED @ tip `v0.6.44`):** **No new C-xxx**. New `src/jarvis/adapters/voice/` package: `FixtureSttSource` (plain-text stand-in for "what STT produced") → `run_voice_turn` (`handle_user_text(..., source=IntentSource.VOICE)` → reuse `render_response`, no fulfill fork) → `run_voice` (fixture-driven loop, optional `speak` callback, parallel in spirit to `run_chat` but never `input()`). Optional `--voice-fixture PATH` flag in `adapters/cli/main.py`; `--chat`/MCP unchanged. No real mic/STT/TTS. Review: `.jes/artifacts/implementation_review_assistant_voice_fixture_loop_b1.md`.

**Extended by T37, voice STT external (2026-10-03, ★ ACCEPT CLOSED @ tip `v0.6.45`):** **No new C-xxx**. External STT **process** seam in `adapters/voice/external_stt.py` (`JARVIS_STT_CMD` + `{audio}` → stdout transcript → `run_voice_turn`); typed `SttError` family — never a silent fixture fallback. Optional `--voice-audio PATH`; `--chat`/`--voice-fixture` unchanged. No speech SDK in deps; vendor pick = separate ★. Review: `.jes/artifacts/implementation_review_assistant_voice_stt_external_b1.md`.

**Extended by T38, voice TTS external (2026-10-03, ★ ACCEPT CLOSED @ tip `v0.6.46`):** **No new C-xxx**. External TTS **process** seam in `adapters/voice/external_tts.py` (`JARVIS_TTS_CMD` + stdin egress → `run_voice`/`speak=`); typed `TtsError` family — never a silent no-op success. Optional `--voice-speak`; `--chat`/`--voice-fixture`/`--voice-audio` unchanged. No speech SDK in deps; free-first demo = Piper `en_GB` outside package. Review: `.jes/artifacts/implementation_review_assistant_voice_tts_external_b1.md` · brief: `.jes/artifacts/engineer_note_voice_tts_product_brief.md`.

**Extended by T39, voice v1 checkpoint (2026-10-04, ★ ACCEPT CLOSED @ tip `v0.7.0`):** **No new C-xxx**. Product-milestone integration proof — reuse T35–T38 voice surface; no new adapter seam. Twelve Skills on voice path + fake TTS + STT→Skill→TTS proven. Package/tag **`0.7.0` / `v0.7.0`**. Review: `.jes/artifacts/implementation_review_assistant_voice_v1_checkpoint_b1.md`.

**Extended by T41, voice demo-ready (2026-10-04, Cursor PASS WITH NOTES @ `0.7.1`, ACCEPT deferred until T42 lands):** **No new C-xxx**. Operator path only, **zero `src/` change** — `docs/USER_GUIDE_VOICE.md` plus external wrappers under `scripts/voice/` (`piper_tts.sh`: egress on stdin → Piper → play/wav, `--check` probe, non-zero on every missing piece; `whisper_stt.sh`: audio path → bare transcript on stdout; `fixtures/demo_skills.txt`). Reuses the existing `JARVIS_TTS_CMD`/`JARVIS_STT_CMD`/`--voice-fixture`/`--voice-audio`/`--voice-speak` seams from T36–T38 unchanged. No speech SDK in core deps; Piper/whisper stay operator-installed outside the package. IC: `.jes/artifacts/implementation_contract_assistant_voice_demo_ready_b1.md`.

**Extended by T42, voice interactive CLI (2026-10-04, Implemented (Claude Code) @ `0.7.2`, await Cursor review → Engineer ★ ACCEPT):** **No new C-xxx**. New `--voice` flag + `run_voice_interactive` in `adapters/cli/main.py` — an interactive REPL reusing T36's `run_voice_turn` (`source=VOICE`) and T38's `_voice_speak_fn`/`JARVIS_TTS_CMD` seam unchanged; `quit`/`salir`/EOF/Ctrl-C exit; missing/failed TTS prints an honest message without crashing the loop. `--chat` has zero reference to the TTS seam — confirmed by source inspection, not just by default-off behavior. `docs/USER_GUIDE_VOICE.md` restructured so §4 leads with `--voice`; `--voice-fixture`/`--voice-audio` demoted to §5 (batch/CI). No speech SDK in core deps. IC: `.jes/artifacts/implementation_contract_assistant_voice_interactive_cli_b1.md`.

**Extended by T43, chat + spoken replies (2026-10-04, Cursor PASS WITH NOTES @ `0.7.3`, await Engineer ★ ACCEPT):** **No new C-xxx**. Opt-in spoken egress on the existing `--chat` REPL — `--chat --voice-speak` → `run_chat(speak_tts=True)` speaks the same string already printed as every `Jarvis > …` reply, via a new `_chat_speak_fn` helper calling T38's `speak_egress`/`JARVIS_TTS_CMD` (never `_voice_speak_fn`, which would double-print); bare `--chat` stays silent (`_chat_speak_fn(False)` is a no-op, no import/call of the TTS seam — `run_chat`'s own source still has zero literal reference to it). Chat brain stays `TERMINAL`/Continuity/craft, unchanged; `--voice` (T42) unchanged. IC: `.jes/artifacts/implementation_contract_assistant_chat_voice_speak_b1.md`. Review: `.jes/artifacts/implementation_review_assistant_chat_voice_speak_b1.md`.

**Extended by T44-inv / T44-DC / T45, spoken continuity (2026-10-04, T45 Implemented (Claude Code) @ `0.7.4`, await Cursor review → Engineer ACCEPT):** **No new C-xxx**. `adapters/voice/spoken_continuity.py` (new) changed only the **speak** path for Continuity walls (project load + `action == "project_status"`) — `print`/`render_*` stay byte-identical Layer 1. `run_chat` calls `spoken_text_for_wall(user_input, printed_wall, ctx)` on both wall sites: brief extract by default, the printed wall verbatim for one turn when the typed line matches the locked FULL phrase set. Three new entries landed in `CONTINUITY_DEFER_PHRASES` (`jarvis/config.py`) so `completo`/`estado completo`/`cuentame todo` resolve to `project_status` at all (the other seven FULL phrases were already members). Every non-wall turn is unaffected. Living map: `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md`. DC: `.jes/artifacts/design_contract_assistant_chat_spoken_continuity_b0.md`. IC: `.jes/artifacts/implementation_contract_assistant_chat_spoken_continuity_b1.md`. Report: `.jes/artifacts/implementation_report_assistant_chat_spoken_continuity_b1.md`. Cola: `.jes/artifacts/engineer_note_voice_phase_c_cola.md`.

**Assistant `jarvis explain` canal — `intelligence/` read-only ontology bridge (2026-09-28, package `0.6.1`→`0.6.4`):** One new connection added — **C-114** (`jarvis explain` CLI subcommand → `jarvis.intelligence.explain`/`explain_maps` → `jarvis.intelligence.ontology_retrieve` → `ontology/` vault frontmatter + `[DEFINICION]`/`[INTUICION]`, read-only). Five Buys, all **★ ACCEPT CLOSED**: placement DC, scaffold (`B1-intelligence-scaffold` @ `v0.6.1`), retrieve (`B1-ontology-retrieve-r2` @ `v0.6.2`), terminal canal (`B1-assistant-terminal-canal` @ `v0.6.3`), explain maps (`B1-explain-maps-expand` @ `v0.6.4`). `src/jarvis/intelligence/` remains **structurally isolated** from Continuity, same discipline as the Fase C packages above: zero import edge from `jarvis.intelligence.*` into `jarvis.core` (Continuity/orchestrator), `jarvis.flight_software`, or `jarvis.vehicle_profiles` (AST-verified per Buy, re-confirmed here); `explain`/`explain_maps` never call `submit_command`, never construct `JarvisOrchestrator`, never reach `CalculationEngine.build`/`state_manager`/`WorkspaceManager`, and never read or write `library/` catalog JSON. Registry count moved **65 → 66**. Reports: `.jes/artifacts/implementation_report_intelligence_scaffold_b1.md` · `.jes/artifacts/implementation_report_ontology_retrieve_r2_b1.md` · `.jes/artifacts/implementation_report_assistant_terminal_canal_b1.md` · `.jes/artifacts/implementation_report_explain_maps_expand_b1.md`. User guide: `docs/USER_GUIDE_EXPLAIN.md`.

**Continuity explain cite R3 — Continuity ↔ `jarvis explain` bridge (2026-09-28, ★ ACCEPT CLOSED @ `v0.6.5`):** One new connection added — **C-115** (`build_project_continuity`'s finite `explain_topics` tags → CLI → `jarvis.intelligence.continuity_cite.cites_for_topics` → `ontology_retrieve`, read-only). `B1-continuity-explain-cite-r3` — Continuity's own ranking (`situation`/`next_useful_step`/`next_useful_why`) is **byte-for-byte unchanged**: two existing fixtures' pre-Buy output strings were captured as golden values and re-asserted against the post-Buy code. `project_continuity.py` still never imports `jarvis.intelligence` and never reads `ontology/` — it only emits topic tags, computed strictly after next_step/why are final, so they can never feed back into ranking (AST + ordering both verified). CLI never dumps note bodies into `estado` — only `id` + a `jarvis explain <id>` pointer. Registry count moved **66 → 67**. Report: `.jes/artifacts/implementation_report_continuity_explain_cite_r3_b1.md`. User guide: `docs/USER_GUIDE_EXPLAIN.md` §7.

**Craft montage honesty layer (2026-09-13, still `v0.4.1` — no new C-xxx):** Suggest-only IDLE assists over existing Continuity writers / screening — estimated-temporary plate · Path F craft montage stack · cited layout pack · mount-standard assist · silhouette Product B\* checklist (`parece un dron` = declared checklist, never visual recognition) · arm radial L-aware Visor layout · **fit-relations checklist** (`fit_relations_assist.py` — IDLE `relaciones`/`fit`; 6 locked relations; estimated plate blocks attest; disk motors/props = n/a). Reuses plate pick / `screen_posed_envelope` / mount checklist. Not ASSEMBLY READY. Suite **2873** · UI **103**. Locks: `.jes/artifacts/engineer_lock_craft_montage_honest_reproducible.md` · `.jes/artifacts/engineer_lock_silhouette_checklist_semantics.md`. Queue: `docs/IMPLEMENTATION_TASKS.md` (await next ★; holds plate-box / Path N).

**Disk-axial Visor + library FC/sensors P0 (2026-09-14, still `v0.4.1` — no new C-xxx):** `_geometry_from_spec` emits `cylinder` when Ø + cited axial (`height_mm` or `hub_thickness_mm`) both exist; diameter-only stays flat disk; screening/attest unchanged. **P0:** FC/GPS physical envelopes relocated to `library/fc/_datos.json` + `library/sensors/_datos.json` via `ComponentLibrary` (`FcSpec`/`SensorSpec`); `aerial.py` keeps alias maps only — supersedes #4b “no library/fc|sensors” ban. Additive binds exist; IDLE rebind trigger not invented this cycle. Suite **2911** · UI **105**. Queue: `docs/IMPLEMENTATION_TASKS.md` (library smoke · holds plate-box / Path N).

**Craft montage + mission-gate + mission-payload identity closed (2026-09-15, still `v0.4.1` — no new C-xxx):** Estimated-temporary ESC height (Skystars) — suite **2929**. **B0** (`mission_functional_payload_holes_b0`) → gate **`B1-system-definition-block-gate`** (refuse unresolvable blocks) — suite **2938**. **`B1-mission-payload-identity`:** identity `ComponentRule`s for `cameras`/`radio_module`; perception→`["cameras"]`; unlocks SYSTEM_DEFINITION B for cámara/comunicación; payload/manipulation/actuation/transmission still refuse — suite **2945** · UI **105**. User guide: `docs/USER_GUIDE_CRAFT_MONTAGE.md`. Queue: `docs/IMPLEMENTATION_TASKS.md` (idle / holds plate-box · Path N).

**Fase M mission craft ladder, CLOSED (2026-09-16→18, tag `v0.4.2` — no new C-xxx):** Every new family/step below rides the *existing* pick→bind→catalog_ref→mirror pattern and the *existing* Continuity waterfall shape — no new connection class. **`B1-mission-mass-energy`:** `mission_payload_mass_kg` mirror (writer `set_mission_component_mass`) — first mass step in the ladder. **`B1-library-cameras-seed`:** `library/cameras/_datos.json` (RunCam Phoenix 2) — full ESC-shaped catalog path (`bind_camera_from_catalog`, `cambiar cámara`, `actualiza la cámara`). **`B1-mission-continuity-mount-endurance`:** mount + autonomy-target ladder steps, reusing `mount_standard_assist`. **`B1-mission-power-w`:** `mission_accessory_power_w` mirror (writer `set_mission_component_power`, cameras/radio only), additive term in both `calculation_engine` autonomy paths. **`B1-catalog-camera-power-w`:** Phoenix 2's cited `200mA@5V` → Engineer-locked `power_w=1.0` JSON field, projected on bind. **`B1-mission-vtx-identity`:** `library/vtx/_datos.json` (HGLRC Zeus 800), new `video_link` block/`vtx` key, mass-only mirror (RF milliwatts never converted to electrical W). Suite **3166** · UI **105**. User guide: `docs/USER_GUIDE_CRAFT_MONTAGE.md` §3/§4. M7 closeout: `.jes/artifacts/engineer_note_fase_m_closeout_m7.md`. Queue: `docs/IMPLEMENTATION_TASKS.md` (Fase M CLOSED; PRIORIDAD → Fase C, await Engineer ★).

**Do not count** leading `| C-xxx |` table cells across the whole file as the registry size — several IDs are re-listed in derived summary tables. The only authoritative count is the length of **Canonical registry** below.

Visual companions (`DIAGRAMS.md`, `jarvis-system-map.canvas.tsx`) must mirror this registry; if they diverge, **this file wins**.

## Status taxonomy

```text
🟢 CONNECTED       — explicit path in code; works for intended use
🟡 PARTIAL         — implicit, incomplete, or only some payloads handled
🔴 BROKEN          — path claims to work but fails / falls to wrong layer (CLI evidence)
⚪ NOT IMPLEMENTED — designed/discussed but no code path exists
⚠ SUSPECT          — LLM or the wrong layer appears to decide (authority smell)
```

## Canonical registry

**67 unique edges.** Append new IDs here first; then add a Detail section. Derived tables elsewhere in this file must not be treated as new edges.

| ID | From | To | Status |
|---|---|---|---|
| C-001 | User | CLI adapter | 🟢 |
| C-002 | CLI/MCP adapter | `orchestrator.handle_user_text` | 🟢 |
| C-003 | CLI/MCP adapter (structured) | `orchestrator.handle` | 🟢 |
| C-010 | Runtime | Global commands intercept | 🟢 |
| C-011 | Runtime | FN-004 structural-confirm consume | 🟢 |
| C-012 | Runtime | Bug 54 pending_define_missing consume | 🟢 |
| C-013 | Runtime | Global component intercept (any mode) | 🟢 |
| C-014 | Runtime | Mode-branch dispatch | 🟢 |
| C-015 | Runtime | Parameter ingestion layer | 🟢 |
| C-016 | `orchestrator.handle` | `ActionRouter.resolve` → `Action.run` | 🟢 (dual-dispatch seam, documented not fixed) |
| C-020 | Runtime | `IntentResolver.resolve_intent` | 🟢 |
| C-021 | Intent (`project_status`) | `_handle_project_status` | 🟢 |
| C-022 | Intent (`analyze`) | `_handle_analyze` | 🟢 |
| C-023 | Intent (`define_params`) | `start_define_missing_params` bridge | 🟢 |
| C-024 | Intent (`dismiss_suggestion`) | `_handle_dismiss_suggestion` | 🟢 |
| C-025 | "ayúdame" + named goal | Intent → engineering_intent (was analyze) | 🟢 (FN-025) |
| C-030 | Runtime (IDLE) | FN-005 assisted motor help / catalog pick (motor·prop·battery·frame) + IDLE rebind | 🟢 |
| C-031 | Runtime (IDLE) | FN-014 acquisition mention → wizard open | 🟢 |
| C-032 | ~~Runtime (IDLE) FN-015 pending-help~~ | REMOVED (G23) | ⛔ |
| C-033 | Runtime (DEFINE_MISSING) | FN-013 reprompt active block | 🟢 |
| C-034 | Runtime (DEFINE_MISSING) | FN-016 navigation cancel | 🟢 |
| C-035 | Intent (`project_status`, FN-023 phrasing) | `_handle_project_status` (Continuity) | 🟢 |
| C-036 | Continuity | Acquisition (`_next_pending_block` shared read) | 🟢 |
| C-037 | Acquisition wizard completion | `_set_pending_next_block` → next block or IDLE | 🟢 (FN-021 invariant) |
| C-038 | Acquisition wizard open | `acquisition_brief.build_acquisition_brief` | 🟢 |
| C-040 | Intent (`iterate`/`unknown`) | `is_engineering_intention` → `_handle_engineering_intent` | 🟢 (IDLE / via C-052; **not** mid DEFINE_MISSING — G8 / SYS-MAP-004) |
| C-041 | `_handle_engineering_intent` | `goal_planner.format_goal_plan` | 🟢 |
| C-042 | Goal Plan CTA (`"explora opciones"`) | DSE (goal binding) | 🟢 (FN-024 — binds via `handoff_context`, see C-105/C-106) |
| C-043 | Goal Plan lever (e.g. `safety_factor`) | Iterate wizard preseed | 🟢 (FN-026 — via `handoff_matching.match_plan_lever`) |
| C-044 | "ayúdame" + named goal | Plan/Explore | 🟢 (= C-025, cross-ref; H3 — FN-025) |
| C-045 | Intent (`explore_design_space`) | `_handle_explore` → `DesignExplorer.explore` | 🟢 (when `goal_key` is resolved, explicitly or via C-106 bind) |
| C-046 | `_handle_explore` result | `_handle_apply_exploration` (via `session.last_exploration_result`) | 🟢 |
| C-105 | `_handle_engineering_intent` (successful plan) | Create/replace `session.handoff_context` | 🟢 (FN-024, new) |
| C-106 | Active `handoff_context` (`dse_capability="active"`, matching `project_id`) | `_handle_explore` goal bind | 🟢 (FN-024, new) |
| C-050 | `orchestrator.handle` (ITERATE) | `IterateInteractiveSession.start`/`answer` | 🟢 |
| C-051 | ITERATE_INTERACTIVE | Bug 7 soft-interrupt (`project_status`/`analyze`) | 🟢 |
| C-052 | ITERATE_INTERACTIVE | Calibration preempt → re-dispatch as IDLE | 🟢 |
| C-053 | `IterateInteractiveSession.answer` | `semantic_interpreter` slot filling | 🟢 |
| C-054 | Iterate final confirm | `MutationEngine` / `apply_and_recalculate` | 🟢 |
| C-060 | `current_parameters` | `CalculationEngine.build` | 🟢 |
| C-061 | `component_resolver.resolve_propulsion_parameters` | Calculation input override | 🟢 |
| C-070 | `CalculationBundle` | `FeasibilitySimulator.evaluate` | 🟢 |
| C-071 | `SimulationResult` | `state_manager.record_action` → persisted `latest_results` | 🟢 |
| C-080 | ProjectState + BOM + requirements | `project_continuity.build_project_continuity` | 🟢 |
| C-081 | Sim (`safety_margin_ratio`) | Continuity `next_useful_step` (PASS+risky thread) | 🟡 PARTIAL (WEAK) |
| C-082 | `classify_component` | BOM buckets (`build_component_bom`) + `sku_resolved` display | 🟢 (FN-020, IC 3 propeller branch) |
| C-083 | `classify_component` (via `component_presence_tier`) | `_block_progress_status` (architecture presence) | 🟢 (FN-020, same classifier as C-082) |
| C-084 | ProjectState | `PhaseLayer.infer` | 🟢 |
| C-085 | Context (incl. C-084) | `ReasoningLayer.build` | 🟢 |
| C-090 | Free text | `component_inference.infer_component[s]` → `ComponentSpec` | 🟢 (pure) |
| C-091 | `ComponentSpec` | `component_writers.set_*` → `design_properties.components[key]` | 🟢 (single write point) |
| C-092 | Any orchestrator checkpoint | `StateManager.set_runtime_session` / `clear_runtime_session` | 🟢 |
| C-093 | `ProjectState` | `WorkspaceManager.save_state` → `state.json` | 🟢 |
| C-094 | `ProjectState` | `WorkspaceManager.render_views` → `estado_actual.md`/`sistema.md` (markdown). Sibling derived view, not a new ID: `spatial_board.project_spatial_nodes` → visor cards/slots. | 🟢 |
| C-100 | `orchestrator` | `llm_interface.interpret` → `PromptBuilder.build_messages` | 🟢 |
| C-101 | `PromptBuilder` messages | `LLMClient.complete` (Ollama) | 🟢 |
| C-102 | Raw LLM response | `LLMResponseParser.parse/validate_for_runtime` (`ActionPolicy`) | 🟢 |
| C-103 | Validated `action_request` | `orchestrator.handle` (closed 4-verb set) | 🟢 |
| C-104 | `orchestrator` | `llm_interface.analyze` → narration string | 🟢 |
| C-107 | `ProjectState` + closure/arch/sim/electrical authorities | `engineering_readiness.build_engineering_readiness` (9 subsystems, ERF-2; IC 1 requirements explicit-none) | 🟢 (ERF-1, updated ERF-2 + IC 1) |
| C-108 | `EngineeringReadinessResult` | `project_continuity.build_project_continuity(readiness=…)` — catalog-gap ranking only | 🟡 PARTIAL (ERF-1) |
| C-109 | `orchestrator.build_startup_context` | startup context `"readiness"` field | 🟢 (ERF-1) |
| C-110 | CLI `render_startup_context` | `ENGINEERING READINESS` block (9 lines, ERF-2) | 🟢 (ERF-1, updated ERF-2) |
| C-111 | `electrical_compatibility` checks | `engineering_readiness` gap generation (4 electrical gap types) | 🟢 (ERF-2) |
| C-112 | `orchestrator._handle_component_description` | ESC out-of-scope explicit save (`OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS`) | 🟢 (ERF-2, FN-ESC) |
| C-113 | Board `Scene3D` situar drag (`POST /api/projects/:id/pose`) | `board_pose_bridge.apply_drag_pose` → `set_component_declared_box_pose` → `WorkspaceManager.save_state` | 🟢 (Board drag → Continuity pose B1) |
| C-114 | `jarvis explain` CLI subcommand **or** `--chat` `jarvis explain `/`explain ` prefix (A7, now via Assistant Task, T0) | `jarvis.intelligence.explain`/`explain_maps` → `jarvis.intelligence.ontology_retrieve` → `ontology/` vault (read-only); chat path via `assistant_task.handle_explain_intent` (`Task` required-capability `ontology.explain`) | 🟢 (Assistant A1–A5 `v0.6.1`→`v0.6.4`; A7 chat ingress `v0.6.6`; T0 Assistant Task refactor, package `0.6.8`) |
| C-115 | `project_continuity.build_project_continuity` (`explain_topics` tags, incl. A8's `current`) | CLI (`render_startup_context`/coherence footer) → `jarvis.intelligence.continuity_cite.cites_for_topics` → `ontology_retrieve` (read-only) | 🟢 (Assistant A6/R3 `v0.6.5`; A8 `current` tagging rule, package `0.6.7`) |

## Forbidden transitions (not registry edges)

**10** normative absences — listed even where no code path exists, so a future change can be checked against them. **Do not add these to the 63.** They have no `C-xxx` IDs.

```text
LLM → acquisition target            NOT IMPLEMENTED — ActionPolicy.ALLOWED_ACTIONS has no such action (structurally impossible today)
LLM → goal selection                NOT IMPLEMENTED — same
LLM → DSE configuration choice      NOT IMPLEMENTED — same
Continuity → mutate ProjectState    NOT IMPLEMENTED — project_continuity.py has zero writes/I-O
Continuity → engineering_readiness  NOT IMPLEMENTED — circularity forbidden (ERF-1 ★7); Readiness composes authorities, never Continuity output
engineering_readiness → persist readiness.json  NOT IMPLEMENTED — derived-on-read only (ERF-1); no parallel persisted readiness state
DSE → silent mutate without apply   NOT IMPLEMENTED — DesignExplorer docstring guarantee + C-046 is the only apply path, and it is a distinct, explicit user turn
Goal Planner → write physical params NOT IMPLEMENTED — goal_planner.py has zero writes/I-O
Component Inference → write direct  NOT IMPLEMENTED — only component_writers.py (C-091) may write components[key]
Analyze (LLM) → choose next gap     NOT IMPLEMENTED — analyze()'s return is a message string only, never parsed as routing
```

None of these are currently violated in code (all `NOT IMPLEMENTED`, i.e. structurally absent, which is the desired state — see `AUTHORITY.md` for the mechanism). They are listed here as a checklist for future FN reviews, not because a violation was found.

---

## Derived detail (may repeat C-xxx)

Sections below expand evidence for canonical IDs. Summary tables that re-list IDs (e.g. C-021…024, C-084/085, C-093/094) are **derived views**, not additional connections.

## Detail — 00 Entry

### C-001 — User → CLI adapter
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | terminal stdin loop |
| Symbols | `adapters/cli/main.py` main loop |
| Payload | raw text line |
| Authority | n/a (input boundary) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `src/jarvis/adapters/cli/main.py` |

### C-002 — CLI/MCP adapter → `orchestrator.handle_user_text`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct method call |
| Symbols | `JarvisOrchestrator.handle_user_text(user_input, llm_interface)` |
| Payload | `user_input: str`, `llm_interface` |
| Authority | Orchestrator (routing owner from here down) |
| Mutation | Indirect (delegates) |
| LLM | INDIRECT (passed through, only invoked deep in the chain — C-100/C-104) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:559` (`handle_user_text`), `:577` (`_handle_user_text_inner`) |

### C-003 — CLI/MCP adapter (structured) → `orchestrator.handle`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct method call, `ActionRequest` |
| Symbols | `JarvisOrchestrator.handle(request)` |
| Payload | `ActionRequest` (`action`, `parameters`) |
| Authority | Orchestrator / `ActionRouter` |
| Mutation | Indirect (delegates to Action objects) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:199` |

### C-114 — `jarvis explain` CLI (or `--chat` prefix, via Assistant Task since T0) → `intelligence.ontology_retrieve` (read-only ontology cite)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | **Two ingresses, one resolve path.** (1) `explain` argparse subcommand (positional `query` / `--list` / `--rung KEY`, mutually exclusive) — calls `jarvis.intelligence.explain.resolve_explain_query`/`run_explain_list_cli`/`run_explain_rung_cli` directly, unchanged since A5. (2) **`--chat` (A7 `v0.6.6`, refactored by T0 `B1-assistant-explain-task`, package `0.6.8`):** `JarvisOrchestrator._handle_global_commands` — same checkpoint escape words/`nuevo` use, first line of `_handle_user_text_inner`, strictly before any LLM call (see C-010) — probes the same `jarvis explain `/`explain ` prefix table, then builds `TerminalIntentAdapter.parse(text)` and calls `jarvis.intelligence.assistant_task.handle_explain_intent(intent)`. That function classifies via `try_explain_concept_task` (→ `Task(required_capability_ids=["ontology.explain"])`, or `None` for a `--list`/`--rung` flag-only line — no fake capability claim) and fulfills via `fulfill_ontology_explain`, which itself calls the identical `resolve_explain_query`/`format_explain_cite` the CLI path uses. Both ingresses end at `jarvis.intelligence.ontology_retrieve.retrieve_by_id`/`retrieve_by_nombre`/`list_solid_ids` → `ontology/*.md` frontmatter + `[DEFINICION]`/`[INTUICION]` sections |
| Symbols | `adapters/cli/main.py` (`explain` subparser + dispatch), `core/orchestrator.py` (`_handle_global_commands`), `config.CHAT_EXPLAIN_PREFIXES`, `jarvis.capabilities.intent.{Intent,Task,TerminalIntentAdapter}`, `jarvis.intelligence.assistant_task.{try_explain_concept_task,fulfill_ontology_explain,handle_explain_intent}`, `jarvis.intelligence.explain`, `jarvis.intelligence.explain_aliases.EXPLAIN_ALIASES`, `jarvis.intelligence.explain_maps.{FS_EXPLAIN_MAP,HD_EXPLAIN_MAP,ids_for_rung}`, `jarvis.intelligence.ontology_retrieve` |
| Payload | query string / rung key → `OntologyCite` (`id`, `nombre`, `path`, `estado`, `never_invents`, `formula_citation`, `definicion`, `intuicion`) or an honest miss (`None` / exit 1 from the CLI; a `status="ok"` honest-miss message from chat — never a raise, never an LLM fallback). Chat path also threads through a real `Task` (`jarvis.capabilities.intent.Task`, `required_capability_ids=["ontology.explain"]`) for genuine queries — never for `--list`/`--rung` lines |
| Authority | `jarvis.intelligence.*` — a separate package, never `orchestrator`/Continuity. `core/orchestrator.py` **may** import `jarvis.capabilities.intent` and `jarvis.intelligence.assistant_task`/`.explain` (one-way — see Non-edges); `jarvis.intelligence.*` still must never import back. Since T0, the *classify* decision (explain-shaped or not) lives in `jarvis.intelligence.assistant_task`, not duplicated in the orchestrator — the orchestrator's own prefix probe is only a cheap early-out, not a second brain |
| Mutation | NO (read-only `Path.read_text`; no write API anywhere in `jarvis.intelligence`) |
| LLM | NO — on **both** ingresses. The chat path returns from `_handle_global_commands` before `_handle_user_text_inner` ever reaches an LLM call, on hit, miss, or `--list`/`--rung`, even if `llm_interface` itself would raise |
| Status | 🟢 CONNECTED |
| Evidence | `src/jarvis/adapters/cli/main.py`, `src/jarvis/core/orchestrator.py`, `src/jarvis/config.py`, `src/jarvis/capabilities/intent.py`, `src/jarvis/intelligence/{explain,explain_aliases,explain_maps,ontology_retrieve,assistant_task}.py`, `tests/test_intelligence_scaffold_b1.py`, `tests/test_ontology_retrieve_r2_b1.py`, `tests/test_assistant_terminal_canal_b1.py`, `tests/test_explain_maps_expand_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_assistant_explain_task_b1.py` |

**Non-edges (verified, not violated — same discipline as the Fase C isolation note above):** `jarvis.intelligence.*` never imports `jarvis.core` (Continuity/orchestrator) and never calls `submit_command` or constructs `JarvisOrchestrator` — this canal never reaches `CalculationEngine.build`, `step()`/the Fase C control loop, or any Continuity write; never imports `jarvis.flight_software` or `jarvis.vehicle_profiles`; never reads or writes `library/` catalog JSON. AST-enforced per Buy (see the evidence tests above: T3/T5 scaffold, T5/T7 retrieve, T5/T6 canal, T6 maps-expand, T6 chat-intercept, T6 assistant-task). The import edges stay exactly two, both one-way: `jarvis.core.orchestrator` → `jarvis.capabilities.intent` and `jarvis.core.orchestrator` → `jarvis.intelligence.{assistant_task,explain}` (all local imports inside `_handle_global_commands`) — the same kind of edge the CLI (`adapters/cli/main.py`) already had; `project_continuity.py` specifically remains untouched by both A7 and T0 and still never imports `jarvis.intelligence` (that fence is R3's, unchanged here — see C-115).

---

## Detail — 01 Runtime

### C-010 — Runtime → Global commands intercept
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | function call, first line of `_handle_user_text_inner` |
| Symbols | `_handle_global_commands` (+ Assistant Task seam: explain · Continuity defer · ARM/DISARM · HOLD · LAND · GO_TO · TAKEOFF · RETURN_HOME · FOLLOW · PATROL — via `TerminalIntentAdapter.parse` + `assistant_task.try_*` / `_handle_vehicle_*` / `_handle_arm_policy`) |
| Payload | `user_input` |
| Authority | escape / `nuevo` tables · `CHAT_EXPLAIN_PREFIXES` (→ C-114) · `CONTINUITY_DEFER_PHRASES` (→ C-021) · `VEHICLE_ARM_PHRASES`/`VEHICLE_DISARM_PHRASES` (T11 latch) · seven vehicle phrase tables (`VEHICLE_HOLD_PHRASES`…`VEHICLE_PATROL_PHRASES`) → Task → shared T11 `ArmedAllowlistSafetyGate` (T14: all seven verbs allowed when armed; allow ≠ execute) · **T15:** when mode is `DEFINE_MISSING_PARAMETERS`, FN-016 nav-back (`is_navigation_back_phrase`) cancels the wizard **before** RETURN_HOME (see C-034). Precedence (first-match): explain → defer → **FN-016 early cancel (wizard only)** → ARM → DISARM → HOLD → LAND → GO_TO → TAKEOFF → RETURN_HOME → FOLLOW → PATROL → fallthrough |
| Mutation | YES (may `clear_runtime_session`); explain / defer / arm-policy / all seven vehicle branches are deterministic and never call an LLM — vehicle `submit_command` calls are Safety-gated *proposals*, never Continuity/`library`/Board mutation |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py` (`_handle_global_commands`), `src/jarvis/intelligence/assistant_task.py`, `config.py` (phrase tables), `tests/test_assistant_vehicle_*_b1.py`, `tests/test_assistant_vehicle_arm_ux_b1.py`, `tests/test_assistant_vehicle_allowlist_widen_b1.py`, `tests/test_fn016_navigation_parse_safety.py` |

### C-011 — Runtime → FN-004 structural-confirm consume
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | session-field check (`pending_structural_change`) |
| Symbols | `_consume_structural_confirm` |
| Payload | sí/no answer |
| Authority | session state (FN-004) |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:587` |

### C-012 — Runtime → Bug 54 pending_define_missing consume
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | session-field check + affirmative-phrase match |
| Symbols | `_is_affirmative`, `start_define_missing_params` |
| Payload | sí/no answer |
| Authority | session state (Bug 54) |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:596` |

### C-013 — Runtime → Global component intercept (any mode)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | free-text component detection, mode-independent |
| Symbols | `_interceptable_component_specs`, `_should_intercept_component`, `_handle_component_description` |
| Payload | inferred `ComponentSpec[]` |
| Authority | `component_inference` (C-090) |
| Mutation | YES (via C-091) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:330` (`_interceptable_component_specs`), `:368` (`_should_intercept_component`), `:646` (call site) |

### C-014 — Runtime → Mode-branch dispatch
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | `if current_session.mode == OrchestratorMode.X` chain |
| Symbols | `OrchestratorMode` (5 values) |
| Payload | — |
| Authority | `StateManager` session mode |
| Mutation | Indirect |
| LLM | INDIRECT (ITERATE_INTERACTIVE's Bug 7 soft-interrupt can reach `analyze`) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:660-830` |

### C-015 — Runtime → Parameter ingestion layer
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct param input recognized before intent resolution |
| Symbols | `param_definition_session.try_ingest` |
| Payload | e.g. "4 motores" |
| Authority | `ParamDefinitionSession` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:840` |

### C-016 — `orchestrator.handle` → `ActionRouter.resolve` → `Action.run` (dual-dispatch seam)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | dict lookup + method call |
| Symbols | `ActionRouter.resolve(ActionName)`, `CreateProjectAction/IterateAction/CalculateAction/SimulateAction.run` |
| Payload | `parameters: dict` |
| Authority | `ActionRouter.ALLOWED` (4-action closed set — same set `ActionPolicy` enforces for the LLM) |
| Mutation | YES (varies by action) |
| LLM | NO (this is the *target* of both LLM's `action_request` and the orchestrator's own resolved-intent handoff — see C-019/C-103) |
| Status | 🟢 CONNECTED — but reached from **two** independent call sites (`orchestrator.handle` directly, and `_handle_user_text_inner`'s `intent in {...}` branch calling `self.handle(...)`), which is the documented dual-dispatch seam. Not a bug; a structural note. |
| Evidence | `core/orchestrator.py:257` (`handle`'s own dispatch), `:901-904` (`_handle_user_text_inner`'s handoff into `handle`), `core/action_router.py` |

---

## Detail — 02 Intent

### C-020 — Runtime → `IntentResolver.resolve_intent`
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | function call |
| Symbols | `IntentResolver.resolve_intent(user_input) -> IntentType` |
| Payload | `user_input: str` → one of 13 `IntentType` values |
| Authority | `IntentResolver` (regex tables, GUIDANCE before ANALYZE before ITERATE, see `AUTHORITY.md`) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:845`, `core/intent_resolver.py:280` |

### C-021 / C-022 / C-023 / C-024 — Intent → dedicated handler
> Derived summary — IDs already in Canonical registry (not +4 edges).

| ID | Intent | Handler | Status |
|---|---|---|---|
| C-021 | `project_status` | `_handle_project_status` (0 LLM, Continuity-backed) | 🟢 |
| C-022 | `analyze` | `_handle_analyze` (LLM narration) | 🟢 |
| C-023 | `define_params` | `start_define_missing_params` bridge | 🟢 |
| C-024 | `dismiss_suggestion` | `_handle_dismiss_suggestion` | 🟢 |

Evidence: `core/orchestrator.py:846,850,864,906`.

**C-021, second ingress since T1 (`B1-assistant-defer-continuity`):** `_handle_project_status` is also reached earlier — before `IntentResolver` runs at all — from `_handle_global_commands` (C-010) when `jarvis.intelligence.assistant_task.try_defer_to_continuity_task` classifies the line as an exact `CONTINUITY_DEFER_PHRASES` match (`Task(defer_to_continuity)`, capability `engineering.continuity`). Same destination function, same dict shape, same UX — `jarvis.intelligence` never formats a Continuity body of its own. Not a new `C-xxx`.

### C-025 — "ayúdame" + named goal → Intent → `analyze` 🟢 CONNECTED (FN-025)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | `intent == "analyze"` is now split at the orchestrator: `IntentResolver.ANALYZE_PATTERNS` was split into `ANALYZE_VERB_PATTERNS` (analiza/evalúa/revisa/...) and `ANALYZE_HELP_PATTERNS` (ayúdame/oriéntame/...), same union, zero change to `resolve_intent`'s own classification. When the match came from the help group only (not the verb group), the orchestrator checks `goal_planner.is_engineering_intention` before falling to `_handle_analyze` |
| Symbols | `intent_resolver.ANALYZE_VERB_PATTERNS`, `ANALYZE_HELP_PATTERNS` (new, FN-025), `orchestrator`'s `intent == "analyze"` branch, `goal_planner.is_engineering_intention`, `orchestrator._handle_engineering_intent` (reused, unchanged, same as C-040) |
| Payload | e.g. `"ayudame a mejorar la estabilidad"` → `goal_key="mejorar_estabilidad"` |
| Authority | `goal_planner.is_engineering_intention` — the exact same authority C-040/FN-022 already uses; no second goal detector |
| Mutation | YES (session) — routes into `_handle_engineering_intent`, which creates/replaces `handoff_context` via the existing C-105, same as any other engineering-intent entry |
| LLM | NO for help+goal (routes to the plan) and for bare help with no goal (routes to `project_status`). Still YES for genuine analytical verbs (`"analiza el margen..."`) and for help+verb combinations where a real analyze verb is also present (verb wins, unaffected) — this gate never claims those. |
| Status | 🟢 CONNECTED (FN-025, 2026-08-12) |
| Evidence | `core/intent_resolver.py` (`ANALYZE_VERB_PATTERNS`/`ANALYZE_HELP_PATTERNS`), `core/orchestrator.py`'s `intent == "analyze"` branch, `tests/test_fn025_help_goal_intent.py` (T1–T8 + 2 regressions). Verified live: `"ayudame a mejorar la estabilidad"` → `action="engineering_intent"`, `goal_key="mejorar_estabilidad"`, `handoff_context` created; `"ayudame con el siguiente paso"` (FN-023) and `"analiza el margen de seguridad"` both unaffected. Same underlying fix as C-044 (cross-ref, one finding, one fix). |

---

## Detail — 03 Acquisition

### C-030 — Runtime (IDLE + DEFINE_MISSING) → catalog pick UX (motor / propeller / battery / frame)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | phrase match + numbered list + pick index; IDLE rebind reopen after arch 4/4 |
| Symbols | `is_help_choose_phrase`, `_try_start_assisted_motor_help`; `_offer/_apply_component_{motor,propeller,battery,frame}_catalog*`; `catalog_bind.bind_*_from_catalog` / `frame_part_specs_from_catalog` → `component_writers.set_*` / `upsert_frame_part`; IDLE `resolve_idle_catalog_rebind` + `clear_frame_part_children` on frame re-pick |
| Payload | `"ayúdame a elegir"`, `"cambiar frame"` / motors/propellers/battery pure phrases, pick `N` |
| Authority | `motor_catalog_assist.py`, `battery_catalog_assist.py`, `frame_catalog_assist.py`, `catalog_rebind_assist.py`, `catalog_bind.py`, orchestrator pick handlers |
| Mutation | YES (bind + component writer). Battery pick calls `set_battery_component` only at orchestrator layer; that writer **conditionally** re-calls `set_motor_component` when OP was never voltage-validated or pack voltage changed beyond `_OP_VOLTAGE_EPSILON_V` (v0.3.4 MOP-2). Unconditional motor re-call on every battery bind remains forbidden (P2-2/IC2 lock). Frame pick projects curated part children (arm thickness + ordinal plates when seeded). |
| LLM | NO |
| Status | 🟢 CONNECTED (G21 motor; v0.3.0 propeller; IC 2 battery + G27; Structure frame IC-2/IC-3 + IDLE rebind B2+B3; plate multiplicity B2 @ 2294; v0.3.4 MOP-2 conditional OP re-resolve) |
| Evidence | `core/orchestrator.py`, `core/motor_catalog_assist.py`, `core/battery_catalog_assist.py`, `core/frame_catalog_assist.py`, `core/catalog_rebind_assist.py`, `core/catalog_bind.py`, `core/component_writers.py`, `tests/test_propeller_catalog_bind_ux.py`, `tests/test_battery_catalog_bind_ux.py`, `tests/test_frame_catalog_bind_ux.py`, `tests/test_idle_frame_rebind_b2.py`, `tests/test_idle_catalog_rebind_b3.py`, `tests/test_frame_parts_graph_v1.py`, `tests/test_dse_motor_op_dual_truth.py` |

### C-031 — Runtime (IDLE) → FN-014 acquisition mention → wizard open
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | mention resolution + Bug54 bridge |
| Symbols | `_try_start_acquisition_from_mention`, `acquisition_target.resolve_acquisition_mention`, `_continue_block_acquisition` |
| Payload | "declarar/definir/completar X" (block or component) |
| Authority | `acquisition_target.py` + `_next_pending_block` |
| Mutation | YES (session `pending_*`) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:630-634`, `core/acquisition_target.py` (FN-011/013/014) |

### C-032 — REMOVED (G23)

The FN-015 pending-help feature this connection described (IDLE bare-help
phrase → auto-open `DEFINE_MISSING` wizard → deterministic help / Brief
replay) was **deleted in full** by G23
(`.jes/artifacts/implementation_contract_g23_remove_fn015.md`) — zero
product value; duplicated Continuity/FN-011/014/023.

**Deleted symbols:** `_try_help_define_pending_idle`, `_help_current_pending_acquisition`, `is_help_define_pending_phrase` (product framing).

**Replacement (not a new C-xxx — Runtime-internal anti-LLM gate only):**

| Mode | Mechanism | Symbols |
|---|---|---|
| IDLE | confusion phrase → Continuity, no wizard | `is_define_missing_confusion_phrase` → `_handle_project_status` (`orchestrator.py:~832-838`) |
| DEFINE_MISSING | confusion phrase → one-line re-ask, no Brief/catalog | `is_define_missing_confusion_phrase` → `_define_missing_confusion_reask` (`orchestrator.py:~972-976`, method ~1614-1652) |

**Why not folded into C-035 `GUIDANCE_PATTERNS`:** that table is resolved globally; mid-wizard it would collide with Bug-56's `project_status` intercept and dump full Continuity instead of the short re-ask (G23 report §4).

| Field | Value |
|---|---|
| Status | ⛔ REMOVED |

### C-033 — Runtime (DEFINE_MISSING) → FN-013 reprompt active block
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | in-wizard re-prompt, no restart |
| Symbols | `_try_reprompt_active_block_declaration`, `resolve_declare_block_request` |
| Payload | "definir/declarar X" while X's wizard is already open |
| Authority | `intent_resolver.resolve_declare_block_request` + `acquisition_brief` (FN-018) |
| Mutation | NO (re-reads, doesn't reset `collected_params`) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:~957-960` (FN-013 reprompt gate), `~1550-1612` (`_try_reprompt_active_block_declaration`) |

### C-034 — Runtime (DEFINE_MISSING) → FN-016 navigation cancel
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | exact-match navigation word → clean cancel |
| Symbols | `is_navigation_back_phrase`, `clear_runtime_session` |
| Payload | "atrás"/"volver"/"vuelve" |
| Authority | `acquisition_target.py` (scoped, not global `ESCAPE_WORDS`). **T15 ★ @ `v0.6.23`:** also honored early inside C-010 `_handle_global_commands` when mode is `DEFINE_MISSING_PARAMETERS`, so those words cancel the wizard **before** the T10 RETURN_HOME vehicle intercept can claim them. IDLE: RETURN_HOME still reachable via C-010 |
| Mutation | YES (clears session) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py` (DEFINE_MISSING branch + T15 early cancel in `_handle_global_commands`), `tests/test_fn016_navigation_parse_safety.py` |

### C-035 — Intent (`project_status`, FN-023 phrasing) → `_handle_project_status`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | `GUIDANCE_PATTERNS` (checked before `ANALYZE_PATTERNS`) |
| Symbols | `intent_resolver.GUIDANCE_PATTERNS` (FN-023's 3 additions), `_handle_project_status` |
| Payload | "ayúdame con el siguiente paso"; also bare `"ayúdame a definir"` / confusion phrases at **IDLE only** (G23 — dedicated check, **not** `GUIDANCE_PATTERNS`; see C-032 replacement) |
| Authority | Continuity (via `build_startup_context`) |
| Mutation | NO (read-only; may set Bug54 `pending_define_missing` as an existing side effect, IDLE only) |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-023; G23 IDLE confusion phrases share this authority) |
| Evidence | `core/intent_resolver.py` (GUIDANCE_PATTERNS FN-023 block), `core/orchestrator.py:~832-838` (G23 IDLE confusion → `_handle_project_status`), `~972-976` (DEFINE_MISSING confusion re-ask — **not** this connection); mid-wizard `"siguiente paso"` family still via C-014's `_dm_intent == "project_status"` (Bug 56) |

### C-036 — Continuity → Acquisition (`_next_pending_block` shared read)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | both read the same underlying computation |
| Symbols | `orchestrator._next_pending_block`, `_block_progress_status`, consumed by both `_try_start_acquisition_from_mention` (Acquisition) and `build_startup_context`'s `arch_progress`/`next_architecture_label` (Continuity) |
| Payload | `(block_key, status)` or `None` |
| Authority | `_block_progress_status` (via `classify_component`, FN-020) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED — this shared-source property is *why* C-082/C-083 (FN-020) closed the old architecture-vs-BOM contradiction |
| Evidence | `core/orchestrator.py:1438-1463` (`_next_pending_block`, `_architecture_progress_str`) |

### C-037 — Acquisition wizard completion → `_set_pending_next_block` → next block or IDLE
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | post-completion hook, gated on `_next_pending_block` result and current mode |
| Symbols | `_set_pending_next_block`, `StateManager.clear_runtime_session` |
| Payload | — |
| Authority | Orchestrator (FN-021 invariant) |
| Mutation | YES (session) |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-021 closed the "stays in DEFINE_MISSING forever" bug) |
| Evidence | `core/orchestrator.py:1366-1437`, `tests/test_fn021_session_hygiene.py` |

### C-038 — Acquisition wizard open → `acquisition_brief.build_acquisition_brief`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | direct call, composes blurb + known facts + why-line |
| Symbols | `build_acquisition_brief(key, project_state)` |
| Payload | `{"message": str, "question": str}` |
| Authority | `acquisition_brief.py` (FN-018), reuses `COMPONENT_PROMPTS` (`acquisition_target.py`) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/acquisition_brief.py::build_acquisition_brief`. **Live callers only** (G23 removed FN-015 help path): `param_definition_session.start` (wizard open), `orchestrator._try_reprompt_active_block_declaration` (FN-013 reprompt), `orchestrator._handle_component_description` (low-completeness re-prompt). **Not** called from confusion re-ask (`_define_missing_confusion_reask` returns one-line `question` only). Motors Brief advertises `ayúdame a elegir` (G21); no `ayúdame a definir` bullet. |

---

## Detail — 04 Engineering

### C-040 — Intent (`iterate`/`unknown`) → `is_engineering_intention` → `_handle_engineering_intent`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | goal detection + numeric-mutate guard, gated to two intent values only |
| Symbols | `goal_planner.is_engineering_intention`, `orchestrator._handle_engineering_intent` |
| Payload | e.g. "aumentar el empuje" → `goal_key="mejorar_estabilidad"`; "reducir payload" → `goal_key="reducir_payload"` (F-1) |
| Authority | `goal_planner.py` (FN-022) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-022) — **reachability is mode-gated** (SYS-MAP-004 / G8). Reachable from **IDLE**, and from **ITERATE_INTERACTIVE** via C-052 preempt-and-redispatch. **Not reachable from `DEFINE_MISSING_PARAMETERS`** while `param_definition_reason`/`pending_missing_reason` == `MISSING_COMPONENT_DEFINITION`: UX-C (`_handle_component_description`) intercepts unconditionally and returns before this gate. The runtime comment at the gate already states it runs only in IDLE; earlier map rows omitted that caveat (map overclaim by omission — not a broken connection when IDLE). |
| Evidence | `core/orchestrator.py:931-936` (C-040 gate; FN-025 also calls `is_engineering_intention` earlier at ~`:880` inside the analyze branch); `core/goal_planner.py`; contrast C-052. Finding: G8 in `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`; audit `.jes/artifacts/sys_map_004_routing_audit.md`. |

### C-041 — `_handle_engineering_intent` → `goal_planner.format_goal_plan`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | direct call, deterministic template over `GOAL_STRATEGIES` |
| Symbols | `format_goal_plan(goal_key, sim_context)`, `_prioritize_strategies` |
| Payload | plan text (numbered strategies + levers) |
| Authority | `goal_planner.GOAL_STRATEGIES` |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:2245-2263` (`_handle_engineering_intent`) |

### C-042 — Goal Plan CTA (`"explora opciones"`) → DSE (goal binding) 🟢 CONNECTED (FN-024)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA, STATE |
| Mechanism | bare `"explora opciones"` (`goal_key is None`) binds through `session.handoff_context` — see C-105 (create) / C-106 (bind) — when the context belongs to the current project (`project_id` match) and `dse_capability == "active"` |
| Symbols | `orchestrator._handle_explore`, `schemas.action_schema.HandoffContext` |
| Payload | `handoff_context.goal_key` (never invented — reused from the plan `_handle_engineering_intent` already showed) |
| Authority | `HandoffContext` created by `_handle_engineering_intent` (C-105); `_handle_explore` only reads it, never invents a goal |
| Mutation | YES (session only) — successful bind+explore sets `dse_capability = "consumed"`; `goal_key`/`levers`/`iterate_capability` untouched |
| LLM | NO for the bound case. A second bare `"explora opciones"` after consumption gets a deterministic 0-LLM message (not analyze — see `05_iteration`/`04_engineering` maps). Falls to `_handle_analyze` only when no bindable context exists at all (no context, wrong project, or unknown goal) — same honest fallback as before FN-024. |
| Status | 🟢 CONNECTED (FN-024, 2026-08-10) |
| Evidence | `core/orchestrator.py::_handle_explore` (bind logic), `::_handle_engineering_intent` (C-105, context creation), `tests/test_fn024_handoff_context_dse.py` (T1–T9). Verified live: plan for `mejorar_estabilidad` → `"explora opciones"` → `action="explore_design_space"`, `goal_key="mejorar_estabilidad"`, 0 LLM. Design authority: `HANDOFF_CONTEXT_DESIGN.md` Decision log (Hybrid Operation-Scoped Context). H2 (CTA honesty, M-002) closed as a consequence — the CTA's `'explora opciones'` promise is now true by construction (a fresh active context is always created immediately before the CTA is built). |

### C-043 — Goal Plan lever (e.g. `safety_factor`) → Iterate preseed 🟢 CONNECTED (FN-026)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | `orchestrator._preseed_variable_from_handoff` runs right before an `intent == "iterate"` action request is dispatched to `self.handle(...)`. It reads the active `handoff_context` (C-105, never a second store), guards on `handoff.iterate_capability == "active"` and `handoff.project_id == project_state.project_id`, then calls the pure helper `handoff_matching.match_plan_lever(user_input, handoff)`, which checks each lever's full string and its slash-separated tokens against the normalized user text and resolves a hit to a canonical variable via the exact same `normalize_alias`/`_VARIABLE_NORMALIZATION`/`_fuzzy_normalize_variable` chain `iterate_interactive_session._apply_answer` already uses at step 1 — no parallel vocabulary. |
| Symbols | `orchestrator._preseed_variable_from_handoff`, `handoff_matching.match_plan_lever`, `iterate_domain._is_valid_variable`/`_VARIABLE_NORMALIZATION`/`_fuzzy_normalize_variable` |
| Payload | "incrementa safety_factor" (after a `mejorar_estabilidad` plan) → confirm → `iteration_draft.variable == "safety_factor"`, wizard jumps straight to step 2 — step 1 ("¿Qué quieres modificar?") never asked |
| Authority | `GOAL_STRATEGIES[goal_key][i]["lever"]` membership (via `handoff_context.levers`) — exactly the H4 design in `MISMATCHES.md`/`HANDOFF_CONTEXT_DESIGN.md` |
| Mutation | YES (session only — `iteration_draft.variable` seeded at wizard start); never touches `dse_capability` or wipes the context |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-026, 2026-08-12) |
| Evidence | `core/handoff_matching.py::match_plan_lever`, `core/orchestrator.py::_preseed_variable_from_handoff`, `tests/test_fn026_lever_iterate_preseed.py` (T1–T8), `tests/test_fn025_help_goal_intent.py::test_iterate_lever_preseed_now_implemented` (regression flipped from the pre-FN-026 pin). A compound lever like `"per_motor_max_thrust_n / motors"` (aumentar_payload) or `"total_power_w / motors"` (mejorar_autonomia) only preseeds from its settable sibling token (`motors`) — a derived/computed token (`total_power_w`) fails `_is_valid_variable` and is honestly skipped, same as if the user had typed it at step 1 manually. |

### C-044 — "ayúdame" + named goal → Plan/Explore (cross-ref C-025) 🟢 CONNECTED (FN-025)
Same underlying phrase and root cause as **C-025** — listed under both Intent and Engineering because the fix could plausibly live in either layer. **FN-025 chose Option A** (orchestrator-side gate, per the contract's preferred option): the fix lives in `orchestrator.py`'s `intent == "analyze"` branch, reusing `intent_resolver.py`'s new `ANALYZE_HELP_PATTERNS`/`ANALYZE_VERB_PATTERNS` split — not a `GUIDANCE_PATTERNS` extension (Option B was considered and rejected: it would have required teaching `resolve_intent` itself to reach into `goal_planner`, blurring intent classification with goal detection). Full evidence at C-025 (do not treat as two separate findings when counting BROKEN edges — now zero, both closed by the one fix).

### C-045 — Intent (`explore_design_space`) → `_handle_explore` → `DesignExplorer.explore`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct call, in-memory only |
| Symbols | `_handle_explore`, `DesignExplorer.explore(project_state, goal_key)`, `EXPLORATION_GRIDS` |
| Payload | `ExplorationResult` (candidates, viable, baseline_simulation) |
| Authority | `design_explorer.py` |
| Mutation | NO ("100% en memoria: no escribe en disco, no muta project_state") |
| LLM | NO — **when `goal_key` is resolved** either explicitly from text or via a C-106 bind. Falls to `_handle_analyze` only when no `goal_key` and no bindable context exist. |
| Status | 🟢 CONNECTED (`goal_key` now resolves either from explicit text or, since FN-024, from a bound `handoff_context` — see C-042/C-106) |
| Evidence | `core/orchestrator.py:912-917,1981-2046`, `core/design_explorer.py` |

### C-046 — `_handle_explore` result → `_handle_apply_exploration`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA, STATE |
| Mechanism | runtime-session field carries the result across turns |
| Symbols | `session.last_exploration_result`, `_handle_apply_exploration` |
| Payload | best viable candidate's delta |
| Authority | Orchestrator (DSE v1.1) |
| Mutation | YES — this is the one DSE-adjacent path that **does** write `ProjectState`, and only on an explicit "aplica" turn |
| LLM | NO |
| Status | 🟢 CONNECTED — **this is the existing precedent** the `MISMATCHES.md` design appendix points to for how a future Plan/Handoff Context (H1) should be shaped: runtime-only, consumed-and-cleared by its own explicit next action |
| Evidence | `core/orchestrator.py:919-923,2047-2090`, `schemas/action_schema.py` (`InteractiveSessionState.last_exploration_result`) |

### C-105 — `_handle_engineering_intent` (successful plan) → create/replace `handoff_context` (FN-024, new)
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | unconditional create-or-replace, every successful `_handle_engineering_intent(goal_key)` call builds a fresh `HandoffContext` and overwrites any previous one via `session.model_copy(update={"handoff_context": ...})` |
| Symbols | `orchestrator._handle_engineering_intent`, `schemas.action_schema.HandoffContext` |
| Payload | `HandoffContext(goal_key, levers=[s["lever"] for s in GOAL_STRATEGIES[goal_key]], origin="engineering_intent", dse_capability="active", iterate_capability="active", project_id=project_state.project_id)` |
| Authority | `goal_planner.GOAL_STRATEGIES` (levers), `_handle_engineering_intent`'s own `goal_key` (already resolved deterministically by C-040, never invented here) |
| Mutation | YES (session only — never `ProjectState`, never disk) |
| LLM | NO |
| Status | 🟢 CONNECTED (FN-024, new) |
| Evidence | `core/orchestrator.py::_handle_engineering_intent`, `tests/test_fn024_handoff_context_dse.py::test_plan_creates_active_handoff_context`, `::test_new_engineering_intent_replaces_context` |

### C-106 — Active `handoff_context` → `_handle_explore` goal bind (FN-024, new)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | read-only lookup at the top of `_handle_explore`, gated on `handoff.project_id == project_state.project_id` (project-boundary proof, not an assumed clear — see `HANDOFF_CONTEXT_DESIGN.md`) and `handoff.dse_capability == "active"` |
| Symbols | `orchestrator._handle_explore`, `StateManager.get_runtime_session().handoff_context` |
| Payload | `handoff_context.goal_key` read into the local `goal_key` used by the rest of `_handle_explore` — from that point on, indistinguishable from an explicitly-resolved `goal_key` (C-045) except for the capability-consumption side effect on success |
| Authority | Same as C-105 — this connection only *reads*, `_handle_engineering_intent` (C-105) is the sole writer |
| Mutation | YES (session only) — successful bind + explore sets `dse_capability = "consumed"`, nothing else changes |
| LLM | NO — a bind either succeeds deterministically or falls through to the pre-existing `_handle_analyze` fallback (C-042) / the deterministic "already explored" message (§4.3) |
| Status | 🟢 CONNECTED (FN-024, new) |
| Evidence | `core/orchestrator.py::_handle_explore` (bind block), `tests/test_fn024_handoff_context_dse.py::test_bare_explore_binds_context_and_consumes_dse_capability_only`, `::test_handoff_context_inert_across_project_boundary` |

---

## Detail — 05 Iteration

### C-050 — `orchestrator.handle` (ITERATE) → `IterateInteractiveSession.start`/`answer`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | interactive-session short-circuit inside `handle()`, or mode-branch inside `_handle_user_text_inner` |
| Symbols | `IterateInteractiveSession.start`, `.answer` |
| Payload | seed parameters, then multi-turn free text |
| Authority | `iterate_interactive_session.py` |
| Mutation | YES (via `apply_and_recalculate`/`record_action` at final confirm) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:220-255,669-721`, `core/iterate_interactive_session.py:88,130` |

### C-051 — ITERATE_INTERACTIVE → Bug 7 soft-interrupt
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | interim intent check, wizard stays open (`wizard_reprompt` attached) |
| Symbols | `resolve_intent` (interim), `_handle_project_status`/`_handle_analyze` |
| Payload | "¿cómo va el proyecto?" mid-wizard |
| Authority | Same as C-021/C-022, scoped to not close the wizard |
| Mutation | NO |
| LLM | INDIRECT (analyze branch) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:672-685` |

### C-052 — ITERATE_INTERACTIVE → Calibration preempt
| Field | Value |
|---|---|
| Kind | CONTROL, STATE |
| Mechanism | pattern-based preempt check, clears session, re-dispatches as IDLE |
| Symbols | `_should_preempt_iterate_wizard`, `clear_runtime_session` |
| Payload | a new strong-intent/component phrase mid-wizard |
| Authority | Orchestrator (2026-08-05 calibration) |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:405-459` (`_should_preempt_iterate_wizard`), `:693-707` (call site) |

### C-053 — `IterateInteractiveSession.answer` → `semantic_interpreter` slot filling
| Field | Value |
|---|---|
| Kind | DATA, STATE |
| Mechanism | `SemanticState` slot extraction/merge |
| Symbols | `semantic_interpreter.update/decide/extract_entities`, `SemanticState` |
| Payload | operation/variable/value slots |
| Authority | `semantic_interpreter.py` |
| Mutation | YES (session `semantic_state`) |
| LLM | NO |
| Status | 🟢 CONNECTED — since FN-026, this is also the mechanism C-043 feeds: `_preseed_variable_from_handoff` writes `iteration_draft.variable` directly on `.start()`, upstream of this slot-filling loop |
| Evidence | `core/semantic_interpreter.py`, `core/iterate_interactive_session.py:1108-1224` |

### C-054 — Iterate final confirm → `MutationEngine`/`apply_and_recalculate`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA, STATE |
| Mechanism | direct call chain |
| Symbols | `MutationEngine`, `param_definition_session.apply_and_recalculate`, `state_manager.record_action` |
| Payload | resolved parameter delta |
| Authority | `mutation_engine.py` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/mutation_engine.py`, `core/param_definition_session.py:715` |

---

## Detail — 06 Calculation / 07 Simulation

### C-060 — `current_parameters` → `CalculationEngine.build`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function |
| Symbols | `CalculationEngine.build(current_parameters) -> CalculationBundle` |
| Payload | `current_parameters: dict` |
| Authority | `calculation_engine.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/calculation_engine.py` (`build` still opt-in for L2), `core/endurance_sweep_writer.py` (user calculate/iterate wrapper only), `actions/calculate.py` |

User-facing `calcular` may two-pass via `build_with_estimative_sweep` (4S labeled sweep on a **copy** of params). `CalculationEngine.build` itself never invents a grid. DSE apply stays a bare `build()` (P27-B ★3 / Option A ★5). **No new C-xxx.**

### C-061 — `component_resolver.resolve_propulsion_parameters` → calculation input override
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function, declarative components → physical override |
| Symbols | `resolve_propulsion_parameters(components) -> PhysicalOverride` |
| Payload | `PhysicalOverride` |
| Authority | `component_resolver.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/component_resolver.py:73` |

### C-070 — `CalculationBundle` → `FeasibilitySimulator.evaluate`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function |
| Symbols | `FeasibilitySimulator.evaluate(calculations, autonomy_threshold) -> SimulationResult` |
| Payload | `CalculationBundle` → `SimulationResult` |
| Authority | `simulation/simulator.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `simulation/simulator.py:18`, `actions/simulate.py` |

### C-071 — `SimulationResult` → `state_manager.record_action` → persisted `latest_results`
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | direct call, immutable `model_copy` |
| Symbols | `StateManager.record_action`, `WorkspaceManager.save_state` |
| Payload | `HistoryEntry` + `latest_results` dict |
| Authority | `state_manager.py` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/state_manager.py:195-215`, `actions/calculate.py`, `actions/simulate.py` |

---

## Detail — 08 Continuity

### C-080 — ProjectState + BOM + requirements → `build_project_continuity`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function, recomputed every call |
| Symbols | `project_continuity.build_project_continuity` |
| Payload | `{situation, evidence, next_useful_step, next_useful_why}` |
| Authority | `project_continuity.py` |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/project_continuity.py:10` |

### C-081 — Sim (`safety_margin_ratio`) → Continuity `next_useful_step` 🟡 PARTIAL (WEAK)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `sim_status == "pass"` branch does not read `safety_margin_ratio` at all |
| Symbols | `build_project_continuity`'s `elif sim_status == "pass": next_step = "Diseño en PASS..."` |
| Payload | margin value is available (`sim.get("safety_margin_ratio")`) but unused in this branch |
| Authority | Continuity is still the sole decider — just under-informed |
| Mutation | NO |
| LLM | NO |
| Status | 🟡 PARTIAL — not `BROKEN` (never wrong, never claims something false) but degrades to a generic fallback identical for margin=1.08 and margin=3.0. Verified via direct `build_project_continuity` call with `safety_margin_ratio=1.08`, architecture 4/4, no incomplete/missing components. |
| Evidence | `core/project_continuity.py` (the `elif sim_status == "pass":` branch, no margin read). Failure D of the predecessor map; H5 (design-only, `MISMATCHES.md`) is the open question, not yet a queued FN. |

### C-107 — Authorities → `build_engineering_readiness` 🟢 (ERF-1, updated ERF-2)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure projection over `ProjectState` + existing authority helpers + `electrical_compatibility` (ERF-2, C-111) |
| Symbols | `engineering_readiness.build_engineering_readiness` |
| Payload | `EngineeringReadinessResult` — gap registry (primary), nine subsystem lines (ERF-2: +`electronics`), `overall`, `top_gap`. ERF-2 adds 4 electrical gap types and `INCOMPATIBLE` verdicts (★3 gate). **IC 1:** `requirements.defined` via `requirements_declared()` (numeric `parsed_constraints` or explicit-none `restrictions`). Product contract: `ENGINEERING_READINESS_VISION.md` §11. |
| Authority | `engineering_readiness.py` — authoritative over **gap aggregation and assembly-ready rollup**, not over physics/BOM/sim truth |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/engineering_readiness.py`, `core/electrical_compatibility.py`, `tests/test_engineering_readiness_*.py`, `tests/test_engineering_readiness_erf2_*.py` |

### C-108 — Readiness → Continuity (catalog-gap ranking only) 🟡 PARTIAL (ERF-1)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | optional kw-only `readiness=` on `build_project_continuity`; gates catalog-gap branches via `readiness.top_gap.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"` and `subsystems["catalog"].warning_type` (G9-B demotion) |
| Symbols | `project_continuity.build_project_continuity(..., readiness=readiness)` |
| Payload | affects only the two motor-catalog-gap `next_useful_step` branches; all other ranking (blocking, FN-005, BOM, arch, optimization, fallback) remains Continuity's legacy chain |
| Authority | Gap ordering from C-107; human next-step copy still from Continuity |
| Mutation | NO |
| LLM | NO |
| Status | 🟡 PARTIAL — intentional ERF-1 scope cut; full handoff deferred (Slice 4b). See `.jes/artifacts/implementation_report_erf1.md` "Scope decision". |
| Evidence | `core/project_continuity.py`, `core/orchestrator.py` (`build_startup_context`), `tests/test_engineering_readiness_continuity.py` |

### C-109 — `build_startup_context` → `"readiness"` field 🟢 (ERF-1)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `readiness = build_engineering_readiness(project_state)` then `dataclasses.asdict(readiness)` in return dict |
| Symbols | `orchestrator.build_startup_context` |
| Payload | full readiness snapshot (derived on read, not persisted) |
| Authority | C-107 |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py`, `tests/test_engineering_readiness_cli.py` |

### C-110 — CLI → `ENGINEERING READINESS` render block 🟢 (ERF-1)
| Field | Value |
|---|---|
| Kind | DATA (presentation) |
| Mechanism | `_render_readiness_block` in `render_startup_context` |
| Symbols | `adapters/cli/main.py::_render_readiness_block` |
| Payload | 9 subsystem verdict lines (ERF-2), `PROJECT STATUS`, up to 3 `TOP GAPS` |
| Authority | display only — reads C-109 payload, no new domain logic |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED (ERF-1, updated ERF-2 — 8→9 lines) |
| Evidence | `adapters/cli/main.py`, `tests/test_engineering_readiness_cli.py` |

### C-111 — `electrical_compatibility` → `engineering_readiness` gap generation 🟢 (ERF-2)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `build_engineering_readiness` calls `check_esc_presence`, `check_esc_vs_motor`, `check_battery_discharge`, library `match_motor_propeller` |
| Symbols | `electrical_compatibility.check_esc_presence`, `.check_esc_vs_motor`, `.check_battery_discharge`; `library.match_motor_propeller` |
| Payload | per-check boolean/numeric facts → 4 gap types (`GAP-ESC-MISSING`, `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`) |
| Authority | `electrical_compatibility.py` — pure facts; `engineering_readiness.py` aggregates into gaps |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/electrical_compatibility.py`, `core/engineering_readiness.py`, `tests/test_electrical_compatibility.py`, `tests/test_engineering_readiness_erf2_gaps.py` |

### C-112 — ESC acquisition routing (out-of-scope explicit save) 🟢 (ERF-2, FN-ESC)
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | `_handle_component_description` checks `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS` + `user_explicitly_named_component()` |
| Symbols | `orchestrator._handle_component_description`, `acquisition_target.COMPONENT_TERM_ALIASES["esc"]`, `COMPONENT_PROMPTS["esc"]` |
| Payload | user text `"esc 30a"` → ESC saved even when wizard expects different key (e.g. `motors`) |
| Authority | `acquisition_target.py` (aliases), `orchestrator.py` (narrow save gate) |
| Mutation | YES (via C-091, component_writers) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py`, `core/acquisition_target.py`, `tests/test_fn_esc_acquisition.py` |

### C-082 — `classify_component` → BOM buckets
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure classifier, routes into 4 buckets; each entry adds `catalog_ref`, `sku_resolved`, `quantity` |
| Symbols | `project_closure.classify_component`, `build_component_bom`, `_bom_sku_resolved`, `format_bom_lines` |
| Payload | `"missing"/"stub"/"declared"/"defined"` → `{defined, incomplete, missing, declarative}`; `[sku]` suffix when `sku_resolved` (motor/battery/**propeller** via `has_*` re-check — IC 3) |
| Authority | `project_closure.py` (FN-020, Impl D, IC 3 display fix) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED — `sku_resolved` is **display-only** (C-094 views); never consumed by C-107 gap/verdict derivation |
| Evidence | `core/project_closure.py`, `tests/test_impl_d_sku_bom.py` |

### C-083 — `classify_component` (via `component_presence_tier`) → `_block_progress_status`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | thin wrapper — same primitive as C-082, not a second threshold |
| Symbols | `orchestrator._component_is_low` → `project_closure.component_presence_tier` |
| Payload | `"stub"/"present"` |
| Authority | `project_closure.py` (FN-020) |
| Mutation | NO |
| LLM | NO |
| Status | 🟢 CONNECTED — **this is the connection whose absence was the FN-020 bug**: before FN-020, architecture progress and BOM used two independently-defined thresholds that could disagree; now both read the same primitive |
| Evidence | `core/orchestrator.py` (`_component_is_low`), `core/project_closure.py` (`component_presence_tier`) |

### C-084 / C-085 — Phase / Reasoning
> Derived summary — IDs already in Canonical registry (not +2 edges).

| ID | From | To | Status | Evidence |
|---|---|---|---|---|
| C-084 | ProjectState | `PhaseLayer.infer` | 🟢 | `core/phase_layer.py:28` |
| C-085 | Context (incl. phase, signals) | `ReasoningLayer.build` → insights/suggested_actions | 🟢 | `core/reasoning_layer.py:28` |

### C-115 — Continuity `explain_topics` → CLI → `intelligence.continuity_cite` (read-only, additive)
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | `build_project_continuity` computes a finite `explain_topics: list[str]` via its own pure `_explain_topics_for_continuity(...)` helper, called **after** `next_useful_step`/`next_useful_why` are finalized (last statement before the return dict) — from signals it already had (`motor_catalog_gap`, catalog-underspec, `energy_model_note`, `autonomy_target_min`, watts-recovery-active) **plus**, since A8, `op_current_present` (a direct read of the already-surfaced `current_parameters["motor_op_current_a"]` field — the same one the CLI's own "OP eléctrico" line uses). The CLI (`render_startup_context`'s Continuity block, and `render_response`'s coherence footer) then calls `jarvis.intelligence.continuity_cite.cites_for_topics(topics)` → A2 `retrieve_by_id` per mapped id, and `format_continuity_cite_lines` to print an optional "Conceptos" block |
| Symbols | `core/project_continuity.py` (`_explain_topics_for_continuity`, `build_project_continuity`), `adapters/cli/main.py` (`_render_concept_lines`), `jarvis.intelligence.continuity_cite` (`CONTINUITY_TOPIC_MAP`, `cites_for_topics`, `format_continuity_cite_lines`) |
| Payload | `explain_topics: list[str]` (finite seed: `c_rate`, `operating_point`, `motor`, `current`, `thrust_stand` — **all five now tagged by a real signal as of A8**; `current` was seeded-but-unused from R3 until then) → zero or more `OntologyCite`s → `"  - <id>  →  jarvis explain <id>"` lines |
| Authority | Continuity owns the tags (topic vocabulary only); `jarvis.intelligence` owns resolving a tag to a cite. Neither owns the other's decision |
| Mutation | NO (topics are additive-only; resolving them is a read-only vault lookup, same as C-114) |
| LLM | NO |
| Status | 🟢 CONNECTED (Assistant A6/R3 ★ @ `v0.6.5`; A8 `current` tagging ★ @ `v0.6.7`) |
| Evidence | `src/jarvis/core/project_continuity.py`, `src/jarvis/intelligence/continuity_cite.py`, `src/jarvis/adapters/cli/main.py`, `tests/test_continuity_explain_cite_r3_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_project_continuity.py` (unchanged, re-run as regression proof) |

**Non-edges (verified, not violated):** `project_continuity.py` never imports `jarvis.intelligence` and never reads `ontology/` (AST-enforced, T3/A8-T4) — it only ever emits the finite topic-tag list, and that computation happens strictly after `next_useful_step`/`next_useful_why`/`situation` are already decided, so topics can never feed back into Continuity's own ranking (regression-tested against existing fixtures' exact pre-Buy `next_useful_step`/`next_useful_why` strings — R3's T2, A8's T3). `continuity_cite.py` never imports `jarvis.core` and never calls `submit_command` (AST-enforced, T4/A8-T4). The CLI never dumps `[DEFINICION]`/`[INTUICION]` into `estado` — only `id` + a `jarvis explain <id>` pointer (full text stays behind the explicit C-114 canal). **A8 addendum:** `current` is deliberately never tagged from watts-recovery activity or a generic `energy_model_note` alone — only from the one distinguished `motor_op_current_a` field (verified by A8's own T2b, two fixtures that exercise those other signals without setting `current`).

---

## Detail — 09 State

### C-090 — Free text → `component_inference.infer_component[s]`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | pure function, domain-registry keyword match + property extraction |
| Symbols | `infer_component`, `infer_components`, `infer_component_for_key` (FN-019), `ComponentRuleRegistry.match` |
| Payload | free text → `ComponentSpec` |
| Authority | `component_inference.py` + `domains/{aerial,ground}.py` |
| Mutation | NO (pure) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/component_inference.py`, `core/component_rules.py` |

### C-091 — `ComponentSpec` → `component_writers.set_*` (single write point)
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | direct call, atomic write to `components[key]` + mirrored `current_parameters` |
| Symbols | `set_frame_material`, `merge_frame_root_declared_properties`, `upsert_frame_part`, `set_control_component`, `set_battery_component`, `set_motor_component`, `set_propeller_component`, `apply_components_delta` |
| Payload | `ComponentSpec` → `ProjectState` update |
| Authority | `component_writers.py` — **the only** legal writer of `design_properties.components` |
| Mutation | YES |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/component_writers.py`, `tests/test_d4_param_gatekeeper.py` (locks the mirrored-param invariant) |

### C-092 — Any orchestrator checkpoint → `StateManager.set_runtime_session`/`clear_runtime_session`
| Field | Value |
|---|---|
| Kind | STATE |
| Mechanism | whole-session `model_copy(update={...})`, or full reset to a fresh IDLE `InteractiveSessionState` |
| Symbols | `StateManager.set_runtime_session`, `clear_runtime_session` |
| Payload | `InteractiveSessionState` fields (`mode`, `pending_*`, `last_exploration_result`, etc. — full field list in `09_state/STATE_MAP.md`) |
| Authority | `state_manager.py` |
| Mutation | YES (session, not disk, though snapshotted — see C-093) |
| LLM | NO |
| Status | 🟢 CONNECTED |
| Evidence | `core/state_manager.py:98-114` |

### C-093 / C-094 — ProjectState → disk
> Derived summary — IDs already in Canonical registry (not +2 edges).

| ID | To | Symbols | Status | Evidence |
|---|---|---|---|---|
| C-093 | `state.json` | `WorkspaceManager.save_state` | 🟢 | `workspace/workspace_manager.py:82` |
| C-094 | `estado_actual.md`/`sistema.md` | `WorkspaceManager.render_views` (uses `project_closure`'s BOM). **Sibling derived view (no new ID):** `workspace/spatial_board.project_spatial_nodes` → visor DTOs (`component`/`part`/`slot`); not markdown, not BOM. | 🟢 | `workspace/workspace_manager.py:115`, `workspace/render_views.py`, `workspace/spatial_board.py` |

---

## Detail — 10 LLM

### C-100 — `orchestrator` → `llm_interface.interpret` → `PromptBuilder.build_messages`
| Field | Value |
|---|---|
| Kind | CONTROL, DATA |
| Mechanism | direct call |
| Symbols | `JarvisLLMInterface.interpret`, `PromptBuilder.build_messages` |
| Payload | `user_input`, `runtime_state` → `messages: list[dict]` |
| Authority | `llm/prompt_builder.py` |
| Mutation | NO |
| LLM | YES (this is the boundary itself) |
| Status | 🟢 CONNECTED |
| Evidence | `llm/llm_client.py:34-35` |

### C-101 — `PromptBuilder` messages → `LLMClient.complete`
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | network call to the model backend |
| Symbols | `LLMClient.complete(messages, json_mode=True)`, implemented by `OllamaClient` |
| Payload | messages → raw JSON string |
| Authority | the model itself (outside this codebase) |
| Mutation | NO |
| LLM | YES |
| Status | 🟢 CONNECTED |
| Evidence | `llm/llm_client.py:38`, `llm/ollama_client.py` |

### C-102 — Raw LLM response → `LLMResponseParser.parse/validate_for_runtime`
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | JSON parse → schema validation → **`ActionPolicy.validate`** |
| Symbols | `LLMResponseParser.parse`, `.validate_for_runtime`, `ActionPolicy.validate`, `ActionPolicy.ALLOWED_ACTIONS` |
| Payload | raw JSON → validated `LLMActionRequest` |
| Authority | **`ActionPolicy`** — this is the structural enforcement point for "LLM must not choose the next engineering target" (see `AUTHORITY.md`) |
| Mutation | NO |
| LLM | YES (validating its output, not itself deciding) |
| Status | 🟢 CONNECTED |
| Evidence | `llm/response_parser.py:17-18`, `llm/action_policy.py:14-38` |

### C-103 — Validated `action_request` → `orchestrator.handle` (closed 4-verb set)
| Field | Value |
|---|---|
| Kind | CONTROL |
| Mechanism | `to_action_request` → `self.handle(action_request)` |
| Symbols | `LLMResponseParser.to_action_request`, `orchestrator.handle` |
| Payload | `{"action": one of 4, "parameters": {...}}` |
| Authority | Same closed set as C-016 |
| Mutation | YES (delegates to the resolved Action) |
| LLM | INDIRECT (this is the LLM's output being consumed, not the LLM itself acting) |
| Status | 🟢 CONNECTED |
| Evidence | `core/orchestrator.py:925,939` |

### C-104 — `orchestrator` → `llm_interface.analyze` → narration string
| Field | Value |
|---|---|
| Kind | DATA |
| Mechanism | direct call, return value is text only |
| Symbols | `JarvisLLMInterface.analyze` |
| Payload | `user_input`, `context`, `goal_context` (optional, from `get_goal_context_for_llm`) → message string |
| Authority | n/a — narration is not a decision |
| Mutation | NO |
| LLM | YES |
| Status | 🟢 CONNECTED |
| Evidence | `llm/llm_client.py:76`, `core/orchestrator.py:2194-2253` (`_handle_analyze`) |

---

## Suspected missing edges (flagged, not fabricated)

These are gaps observed while building this registry — not claimed as connections, and not implemented anywhere. Listed so a future contributor doesn't have to rediscover them from scratch.

- **Plan/Handoff Context → DSE consumer** — **IMPLEMENTED (FN-024, C-105/C-106)**, closing C-042. **Help+Goal routing (H3/C-025/C-044)** — **IMPLEMENTED (FN-025)**, closing both. **Plan/Handoff Context → Iterate consumer (H4/C-043)** — **IMPLEMENTED (FN-026)**, via `handoff_matching.match_plan_lever` + `orchestrator._preseed_variable_from_handoff`. H1–H4 all closed; only H5 (C-081, below) remains. See `MISMATCHES.md` design appendix.
- **Continuity → margin/goal "thread"** — `⚪ NOT IMPLEMENTED` in the sense that no data surface currently carries "we are worried about margin" across turns; C-081 is the read-side symptom.
- **`ActionRouter` entry for `analyze`/`project_status`/`explore_design_space`/etc.** — `⚪ NOT IMPLEMENTED` by design (§1.4 dual-dispatch note) — these intents never touch `ActionRouter` at all, which is why the seam exists. Not a bug, listed for completeness.
- **Spatial board visor → DEFINE / catalog pick** — still `⚪ NOT IMPLEMENTED` by design (U1). Slots remain display-only. Pose commit is the narrow exception **C-113** (Scene3D situar only); layout overlay stays `localStorage`, not `ProjectState`. Do **not** open DEFINE/catalog-from-card without a dedicated ★.
- **Board drag → pose writer** — now `🟢 C-113` (Board drag → Continuity pose B1, 2026-09-10) — singleton solids only, "situar" mode, POST bridge. See the chronology entry above.
- **Board resize → envelope writer** — still `⚪ NOT IMPLEMENTED`. Desired: resize handles on eligible solids commit L×W×H via `set_component_declared_box_envelope`, mirroring C-113's own pose bridge shape — a later, separate Buy (`B1+`), not folded into this one.
- **Board drag on `solidCopies >= 2` station copies** — still `⚪ NOT IMPLEMENTED`, structurally: `isDraggableSolid` fails closed for any copy, since N copies share one identity and a per-copy pose mechanism has no schema today. Do **not** add a C-xxx for this absence without a dedicated multiplicity-pose ★ first.
- **Board card-px (2D layout overlay) → any writer** — still `⚪ NOT IMPLEMENTED` by design (`localStorage` layout overlay stays presentation-only; C-113 only ever wires the 3D Scene3D pane, never `useNodeGestures`' 2D card drag).
