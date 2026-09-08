# Investigation Report — Connect Remaining `mounted_on` (Fase 3 / Conn)

**IC:** [investigation_contract_connect_remaining_mounted_on_b1.md](investigation_contract_connect_remaining_mounted_on_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2418 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B1 — one narrow, symmetric bug fix in already-shipped `mounted_on_declare_assist`, not a new capability.** Continuity already covers every remaining Conn candidate (propellers, sensors) with zero new code — proven live, both via the pure parser and end-to-end through the real orchestrator. But I found and empirically reproduced a real collision bug: `_resolve_subject` scans the **entire** phrase for a subject noun, with no positional awareness, so when the natural Spanish target word for a mount happens to also be a recognized subject noun elsewhere in the fixed-priority table, the wrong component gets declared as the subject. This breaks the single most expected Conn phrase — **"hélices montadas en los motores"** — and a second case, **"sensor montado en el esc,"** produces an outright self-mount attempt. Neither corrupts state (both fail at the writer's own guards), but both give the user a confusing, wrong-cause error for a completely natural sentence. The fix is a direct mirror of the fix already applied to target resolution in the same file (scope the search to before the first "en" instead of the whole string) — small, symmetric, zero new vocabulary, zero inference.

---

## 2. Gap matrix (demo + Continuity coverage)

| Key | `mounted_on` today | Should it have one? | Blocker |
|---|---|---|---|
| `motors` | `frame_arm` | ✅ already connected | — |
| `esc` / `flight_controller` | `frame_plate` | ✅ already connected | — |
| `battery` | `frame` | ✅ already connected | — |
| `propellers` | `None` | Yes — physically mounted on a motor shaft | **Continuity subject noun exists**, but the natural phrase collides with the `motors` subject pattern (§3) — walk works only via literal English keys or careful phrasing today |
| `sensors` (Here3) | `None` | Yes — physically mounted on a plate | **Continuity subject noun exists and works**; target resolution against a translated/paraphrased plate label ("la placa principal" vs. the stored "Main Plate") correctly fails per the label-match design (verbatim quotes only, never translated) — not a bug, an existing, intentional limit |
| `frame` (root) | `None` | **No** — nothing mounts "on the whole frame" as a meaningful relation beyond what `battery→frame` already expresses; the root is not a mount surface in the way a plate/arm is | out of scope by design |
| `frame_arm` / `frame_plate*` / `frame_cage` / `frame_standoff` | `None` | **No** — see §4 (C) | `parent_key="frame"` already expresses the only fact there is to express; `mounted_on` is not a Continuity **subject** vocabulary for these keys today, and shouldn't become one |

---

## 3. Empirical parse results (live, this session — not assumed)

All run against `mounted_on_declare_assist.parse_mounted_on_declare` and, where noted, the full `JarvisOrchestrator.handle_user_text` with real `motors`/`propellers`/`sensors`/`esc` components actually declared:

| Phrase | Pure parse result | Orchestrator outcome |
|---|---|---|
| `"propellers montados en motors"` (literal keys) | `SET(propellers → motors)` ✅ | (not separately re-run; pure parse is authoritative here — literal keys never collide) |
| `"monta las helices en frame_arm"` / `"...en el brazo"` | `SET(propellers → frame_arm)` ✅ | works — arm has no subject-noun collision |
| **`"helices montadas en los motores"`** (the natural, expected phrase) | `AMBIGUOUS_TARGET(component_key='motors', candidates=())` ❌ **wrong subject** | `{"status": "interactive", "message": "No encontré esa parte declarada para el montaje..."}` — **fails safely, zero write**, but for the wrong reason (message reads as "target not found," the real fault is subject misresolution) |
| **`"sensor montado en el esc"`** | `SET(component_key='esc', target_key='esc')` ❌ **self-mount** | `{"status": "error", "message": "'esc' no puede estar montado en sí mismo."}` — **fails safely** at the writer's existing self-mount guard, but the error is baffling (user never said "esc en esc") |
| `"sensor montado en la placa"` | `AMBIGUOUS_TARGET`, 4 real candidates listed | expected, honest behavior — locked stance 4 working exactly as designed (2+ plates, never guessed) |
| `"here3 montado en la placa principal"` | `AMBIGUOUS_TARGET`, 4 candidates (label "principal" doesn't match stored "Main Plate") | **Not a bug** — labels are verbatim manufacturer quotes, deliberately never translated (per the original Continuity-declare investigation's own design) |
| `"here3 montado en la main plate"` (exact stored label) | `SET(sensors → frame_plate)` ✅ | confirms the label-match mechanism itself works correctly once given the real, stored text |
| `"monta el brazo en el frame"` / `"monta la jaula en el frame"` | `NONE` | confirmed: structure parts have **no subject-noun pattern at all** — cannot be declared as the mounting party today, by construction, not by accident |

**Root cause of the two failing cases, precisely:** `_resolve_subject(normalized)` (line 81-85) searches the **whole** normalized phrase, in a fixed priority order (`flight_controller > esc > motors > battery > sensors > propellers`), for the first pattern that matches **anywhere**. It has no concept of "the subject should be the noun before the verb/gate," unlike `_resolve_target`, which was already scoped in the Continuity-declare implementation to search only the text **after** the first `"en"` specifically to prevent this exact class of self-reference. Subject resolution never received the same treatment. Any phrase of the shape *"[intended subject] montado en [target noun that happens to also be a table-priority subject noun]"* — `motores` for `motors`, `esc` for `esc` — will misfire whenever the target noun's table entry outranks the true subject's.

---

## 4. Answers

**(B) Continuity coverage:** Propellers and sensors are **already declareable with zero new code** for the common case — every non-colliding phrasing (literal keys, exact stored labels, arm/plate/cage/standoff targets) works today, proven above. The gap is narrowly the two collision cases, not a missing capability.

**(C) `parent_key` vs `mounted_on` for frame parts — recommendation: keep them target-only, do not add subject-noun support.** `parent_key="frame"` already states the complete, honest fact a frame part has to state about its own place in the design: "I am a declared sub-part of the frame." A hypothetical `frame_arm.mounted_on = "frame"` would assert nothing new — it would be the same fact, spelled a second way, through a field this project has deliberately kept orthogonal to `parent_key` specifically so the two never collapse into redundant restatement (per the assembly-espacial B1 investigation's own §C reasoning). Conn's real job is connecting the **electronics/propulsion/payload layer** (motors, ESC, FC, battery, sensors, propellers) to the **structure layer** (frame and its parts) — not connecting structure parts to each other, which composition already fully covers. No Buy is needed or justified here; this is a "confirm as already correct," not a gap.

---

## 5. Buy options

| Option | Assessment |
|---|---|
| **B0 — Walk-only close** | Would be correct **except** for the two reproduced collision bugs — an Engineer attempting the single most expected Conn phrase ("hélices montadas en los motores") today gets a confusing wrong-cause error, not silent corruption but also not a real walk. B0 as a full close is not honest given this evidence. |
| **B1 — Thin, symmetric fix (recommended)** | Scope `_resolve_subject`'s search to the text **before** the first `"en"` (mirroring the exact discipline `_resolve_target` already uses for the text after it) — a small, local, zero-new-vocabulary change to one function in `mounted_on_declare_assist.py`. Fixes both reproduced cases (propellers↔motors, sensors↔esc) and any future instance of the same class, since it removes the root cause (whole-string, position-blind subject search) rather than patching the two symptoms individually. No new Continuity phrases, no new target nouns, no writer change. |
| **B1+ — Guided missing-mount list** | Not justified by evidence — the only real gap found is the one collision class B1 fixes; a "what's still unmounted" status line is a nice-to-have with no failing case behind it today. Defer unless the Engineer wants discoverability UX independent of this bug. |
| **B2 — Auto-infer mounts** | **Rejected**, consistent with Locked Stance 1. The collision bugs found here are, if anything, a caution *against* inference: a system that guesses "propellers must mean motors" would have silently written the WRONG relation in exactly the cases where the deterministic parser instead (safely) refused. |

---

## 6. Contingency sketch (if Engineer ★ Buys B1 — not an IC)

```text
mounted_on_declare_assist.py, parse_mounted_on_declare (SET branch only):

  en_match = _EN_RE.search(normalized)
  subject_segment = normalized[:en_match.start()] if en_match else normalized
  subject = _resolve_subject(subject_segment)   # was: _resolve_subject(normalized)
  ...
  target_segment = normalized[en_match.end():] if en_match else ""
  target = _resolve_target(target_segment, components)   # unchanged
```

The `_CLEAR_RE` branch (no "en" involved, e.g. "quita el montaje del esc") is unaffected — it already only ever needs one noun and has no target segment to collide with. A Cursor-authored IC should add regression tests for both reproduced phrases (`"helices montadas en los motores"` → `SET(propellers, motors)`; `"sensor montado en el esc"` → `SET(sensors, esc)`) plus a check that the existing, already-passing non-colliding phrases (arm/plate/cage/standoff targets, literal-key phrasing) are unaffected.

---

## 7. Non-goals honored

No pose/fit opened. No auto-inference proposed or implemented — both reproduced failures are named specifically as evidence *against* inference, not a case for it. `parent_key` semantics untouched and explicitly recommended to stay untouched (§4C). Fase 2 (G) not reopened — no seed, geometry, or projector file was touched. Here3 identity stays frozen — every sensors phrase tested uses only the existing `gps_model`/name-level declare, no dimension was read, sourced, or invented. Board layout was not touched or treated as any kind of ground truth. No code changed — `git status --short -- src/ tests/` is empty for this cycle; every finding above was reproduced via ad hoc read-only Python calls against the live library/orchestrator, never persisted (the demo project's own `state.json` was read only, confirmed unchanged).
