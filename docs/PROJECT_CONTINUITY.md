# Project Continuity → Project Coherence

**Validated:** 2026-08-06 — workspace experiment + live CLI field notes
(`inspección-de-puentes-…`, `transportar-cámara-800g-…`).

## Product contract (A')

Whenever the engineer **reopens** a project, Jarvis must answer:

1. **Situation** — Where am I?
2. **Evidence** — Why am I there?
3. **Next useful step** — One concrete technical action

Decisions come and go. The **project** is the stable unit.

## Deeper discovery: Project Coherence

Continuity at **startup** is not enough. After the first user turn, Jarvis often becomes a set of **operations** (analyze / iterate / define) and the project disappears from the reply.

The real property is not “conversational continuity”. It is:

> **Project Coherence** — every response must still make sense as coming from *this* engineering project. The project remains the protagonist.

```text
User
  → Project context
  → Operation (may run)
  → Project context updated
  → Response (still about the project)
```

Not:

```text
User → Operation → Response
```

### Continuity Rule (document this)

After every **relevant** operation, Jarvis must answer — implicitly or explicitly:

1. **What just changed in the project?**
2. **What is the project state now?**
3. **What is the single most useful next technical decision?**

Not always as three visible sections. But that information must exist in the response.

### Field-note metric

If you feel: *“I’m talking to an operation, not to Jarvis / not to my project”* — that is a field note. Collect 10–15 before designing a large response layer.

**Do not build a Conversation Engine yet.** Discover the shape from CLI use.

## Experiment notes (abridged)

| Need | Jarvis said | Human engineer expectation |
|------|-------------|----------------------------|
| Where am I / summary | Phase “completado” + sim OK **and** competing nexts | One situation + one next |
| “dame detalles” | Analyze / “impacto” | Project narrative (resolved / pending / why) |
| motor_count=6 vs “faltan motores” | Conflicting evidence | One coherent story |
| “define 4 motores” with 6 set | Silent execute | Conscious substitute + impact on project |

**Synthesis:** Engineers stop asking for more physics and start asking for better accompaniment. That means the calc/sim core is starting to be good enough; the next gains are in **project-first behaviour**.

## Field notes FN-001…004 — closed

| ID | Fix | Status |
|----|-----|--------|
| FN-001 | No auto-start `define_missing_params` on load when `missing_params` empty / Continuity already has next | ✅ |
| FN-002 | Continuity-first status render (hide noisy “Fase: completado” / competing suggestions) | ✅ |
| FN-003 | “dame detalles” / “cuéntame el proyecto” → `project_status` | ✅ |
| FN-004 | Confirm Sí/No before substituting defined `motor_count` (define + component intercept `"4 motores"` + iterate) | ✅ |
| Evidencia | BOM gap “número de motores” suppressed when `motor_count` in params | ✅ |
| P4 | After iterate/define/calc/sim `ok`: Continuity footer (estado + next) | ✅ |

## Field note FN-005 — Assisted Acquisition (closed)

| ID | Symptom | Fix | Status |
|----|---------|-----|--------|
| FN-005 | Wizard asks `motor_power_w`; “ayúdame a elegir” → LLM analyze | Human 3-path prompt + D8 catalog picker in DEFINE; Continuity next aligned | ✅ |

**Surface:** `motor_catalog_assist` + `param_question` / DEFINE wizard. Choosing a catalog motor writes `motor_power_w` ← `max_watts` (catalog nominal, not a flight curve) and enriches `components["motors"]`.

## Field note FN-006 — Assisted Acquisition hygiene (closed)

Localized, behavior-preserving cleanup after FN-005:

- `_answer_assisted_motor` isolates the assisted branch from the generic parameter flow.
- `offer_catalog_help()` is the public session entry point; IDLE no longer re-enters through a magic user string.
- `MotorSuggestion` and `_format_candidate_line` centralize the local candidate contract and rendering.
- Review verdict: **PASS WITH NOTES** — 160 focused/related tests and 1428 full-suite tests reported green.

### Recorded MINOR notes

1. `_question_for_param(..., suggestions=...)` still uses `list[dict] | None` instead of propagating `MotorSuggestion`.
2. `test_offer_catalog_help_is_public_session_entry_point` asserts the private worker `_offer_catalog_help`; future tests should verify only the public API and observable result.

These notes are non-blocking and do not reopen FN-006.

## Success criterion

> Can Jarvis look at a two-week-old project *and* survive a multi-turn session without the project vanishing behind operations?

## Not building yet

- Conversation Engine / dialogue framework
- Engineering Decision as a first-class entity
- Purchase / assembly / firmware modules
- Symptom diagnostic as a separate product slice

## Surface today

`build_startup_context` / `project_status` / CLI expose a `continuity` block (situation / evidence / one next step).

After relevant `ok` ops, `attach_project_coherence` + CLI `render_response` append the same Continuity Rule (cambio / estado / siguiente paso). Further field notes still welcome before any larger response layer.
