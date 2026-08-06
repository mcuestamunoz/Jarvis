# Calibration — LLM routing (Python SessionManager)

**Date:** 2026-08-05  
**Status:** CLOSED (cycle complete)  
**Closure:** `.jes/artifacts/cycle_close_llm_calibration.md`  
**Path:** `JarvisSessionManager.chat` (= MCP/CLI core)  
**Project:** inspección-de-puentes-…-9656971237a1  
**Log:** `.jes/artifacts/calibration_session.jsonl`  
**Turns:** 35 unique (≥30)

## Hotfix (fixed mid-session)

`session.mode` restored from U4 runtime snapshot as plain `str` → `AttributeError: 'str' object has no attribute 'value'` on LLM interpret.

Fix:
- `state_manager.restore_from_snapshot` coerces `OrchestratorMode`
- `prompt_builder._mode_label` accepts enum or str
- tests: `test_session_mode_coercion.py`

## Routing distribution (this session)

| Bucket | Count | Notes |
|---|---|---|
| local_no_llm | 26 | status, simula, calcula, DSE, components, cancel… |
| llm analyze / no semantic_trace | 6 | text answers |
| preseed_step2 | 2 | `quiero más autonomía`, **`más chicha`** |
| rejected_derived_variable | 1 | spurious on warnings question |

## What works well

- Strong actions win: `calcula cómo influye…` → **calculate** (not analyze)
- Local status/simulate/explore/apply/components OK when idle
- Analyze answers are usable (~50–70 s with qwen2.5:14b)
- Goal-ish phrases often open iterate or goal plan
- Component intercept: carbono / batería / Pixhawk OK when idle

## Friction / misroutes (actionable)

1. **Sticky `ITERATE_INTERACTIVE`** — ~~after opening iterate, later intents eaten as wizard answers~~ **FIXED 2026-08-05**: hard preempt for explore/calculate/simulate/iterate/components; soft interrupt kept for status/analyze (Bug 7).
2. **`más chicha` → preseed `battery_capacity_wh` confidence 1.0** — ~~overconfident slang~~ **FIXED 2026-08-05**: `SemanticIntentAdapter` caps confidence unless user text grounds the variable; strips invented `valor` without a number in input.
3. **`dime cuáles son los warnings`** — got `rejected_derived_variable` (autonomia) in log while still answering via analyze path; noisy semantic_trace.
4. **`autonomía` alone → calculate** — odd; expected derived redirect or analyze.
5. **`optimiza para payload` / `mejora la estabilidad`** — ~~→ iterate wizard~~ **FIXED 2026-08-05**: `EXPLORE_PATTERNS` covers all DSE goal domains; `detect_goal` keywords for margen / para masa|peso.
6. Latency analyze ~55–70 s — product concern, not routing.

## Recommended next code cycles (evidence-based)

1. ~~Soften overconfident slang~~ **DONE** (lexical grounding + drop invented valor; prompt guidance).
2. ~~UX: when iterate wizard is open, allow strong intents to preempt~~ **DONE** (hard preempt + soft status/analyze).
3. ~~Tighten explore patterns for “optimiza para …”~~ **DONE**.
4. Optionally lower or re-validate `CONFIDENCE_THRESHOLD` after collecting more `preseed_step2` false positives — sample still small (n=2 preseeds; one was slang, now fixed).

## Checklist vs roadmap

- [x] ≥30 real inputs
- [x] Routing distribution measured
- [x] Adjust prompt_builder / slang overconfidence — **done via adapter grounding + prompt**
- [x] Precedence strong action > analyze — validated
- [x] Motor suggestions value — **validated 2026-08-05** (value on catalog hits; preempt regression fixed)
