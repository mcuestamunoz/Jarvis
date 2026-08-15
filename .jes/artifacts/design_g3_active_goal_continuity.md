# G3 Design — Active Goal Continuity for Explore

**Status:** DESIGN CLOSED — Engineer lock ★1–★4 (2026-08-14)  
**Date:** 2026-08-14  
**Author:** JES / Cursor (Engineer Interface)  
**Base:** `checkpoint-g5-dse-component-sync` (F-1 + G5 closed; G5 CLI PASS)  

**Related findings:**  
- G3 in [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)  
- H1 / FN-024: bare `"explora opciones"` already binds via `HandoffContext.goal_key`  

**Explicitly not this document:** G6 (mass auditability) · G7 (iterate `operation=None`) · G1/G2 · H5 · Catalog Impl C · code  

**Next:** Implementation Contract — G3 (Active Goal Continuity)  
→ [`.jes/artifacts/implementation_contract_g3_active_goal_continuity.md`](implementation_contract_g3_active_goal_continuity.md)

**Process:** Design CLOSED → IC → code. Do not implement from this doc alone.

---

## 0. Problem

After a Goal Plan creates an active `HandoffContext`, two explore-shaped phrases behave differently:

```text
Plan activo: reducir_payload

"explora opciones"     → DSE(reducir_payload)     ✅  (H1 bare bind)
"optimiza payload"     → DSE(aumentar_payload)    ❌  (text re-derived)
```

Root mechanism today (`orchestrator._handle_explore`):

- If `resolve_explore_goal(text)` returns `None` → bind from handoff (H1).  
- If it returns a goal → **use that goal**, ignoring the active plan.

So undirected / domain-only explore phrases (`optimiza payload`) re-enter `detect_goal`, which for bare `"payload"` still defaults to `aumentar_payload` (F-1 intentional default). Continuity is lost.

This is **not** a goal-planner bug and **not** a catalog bug. It is a **precedence** problem between:

```text
intención conversacional activa (HandoffContext)
        vs
intención inferida de un mensaje aislado
```

---

## 1. Design principle

> **Continuation of an active engineering operation must not silently invert that operation.**  
> **An explicit new goal from the user must always be allowed to replace the active goal.**

Precedence (locked target):

```text
explicit new goal
        >
active goal (HandoffContext)
        >
inferred / default goal from bare dimension
```

G3 only migrates **explore-path** consumption of this precedence. Iterate / Goal Plan creation paths stay as today unless a follow-up contract says otherwise.

---

## 2. Definitions

### 2.1 Active goal

The `goal_key` on the current `HandoffContext` when:

- `handoff.project_id == active project_id`
- `handoff.dse_capability == "active"` (or still usable per H1 rules — do not invent a second store)

If no bindable handoff → today's behavior (derive from text only).

### 2.2 Continuation phrase (inherits active goal)

User is asking to **run / continue exploration** without stating a **new direction**.

Examples (normalized, non-exhaustive):

| Pattern class | Examples |
|---|---|
| Bare explore (already H1) | `explora opciones`, `explora el espacio` |
| Undirected optimize | `optimiza`, `optimiza opciones`, `prueba otra`, `continúa`, `sigue explorando` |
| Domain-only explore | `optimiza payload`, `optimiza para payload`, `explora payload`, `mejora carga útil` *(no increase/decrease verb)* |

**Rule:** If the phrase is an explore intent **and** either:

1. resolves to **no** goal_key, **or**  
2. resolves to a goal in the **same dimension family** as the active goal **without** an explicit opposite direction,

→ **prefer `handoff.goal_key`**.

### 2.3 Explicit new goal (replaces active goal)

User states a **direction or a different engineering goal** that conflicts with or supersedes the plan.

Examples:

| Input | Expected |
|---|---|
| `ahora aumenta el payload` | `aumentar_payload` (override) |
| `aumentar carga útil` | `aumentar_payload` |
| `reducir payload` *(new plan turn)* | new engineering_intent / replace handoff via existing Goal Plan path |
| `mejorar autonomia` / `optimiza para autonomia` | `mejorar_autonomia` (different dimension) |
| `aumentar empuje` / `mejorar estabilidad` | `mejorar_estabilidad` |

**Rule:** If text resolves to a goal_key that is:

- a **different dimension** than the active goal, **or**  
- the **opposite direction** within the same dimension (e.g. active `reducir_payload`, text clearly `aumentar_payload`),

→ **use the text-derived goal** (explicit override). Do **not** silently keep the old plan.

### 2.4 Same-dimension undirected vs directed

Payload family example:

| Active | User text | Classification | Result |
|---|---|---|---|
| `reducir_payload` | `explora opciones` | continuation | `reducir_payload` |
| `reducir_payload` | `optimiza payload` | continuation (undirected domain) | `reducir_payload` |
| `reducir_payload` | `optimiza para reducir carga` | same goal / reinforce | `reducir_payload` |
| `reducir_payload` | `ahora aumenta el payload` | explicit opposite | `aumentar_payload` |
| `reducir_payload` | `optimiza para autonomia` | different dimension | `mejorar_autonomia` |
| `aumentar_payload` | `optimiza payload` | continuation | `aumentar_payload` |

**Critical:** `"optimiza payload"` must **not** default to `aumentar_payload` when active goal is `reducir_payload`. That was the CLI failure.

---

## 3. Dimension families (minimal for G3)

Only what explore needs; do not rebuild goal_planner:

| Family | Goals |
|---|---|
| payload | `aumentar_payload`, `reducir_payload` |
| mass | `reducir_masa` |
| autonomy | `mejorar_autonomia` |
| stability / margin | `mejorar_estabilidad` |

Opposite pairs (for override detection):

```text
aumentar_payload  ↔  reducir_payload
```

Other goals have no opposite in v1 → different-dimension always overrides.

---

## 4. Proposed resolution algorithm (explore only)

```text
intent = explore_design_space
text_goal = resolve_explore_goal(user_input)   # may call detect_goal
handoff = active bindable HandoffContext or None

if handoff is None:
    use text_goal   # today; if None → existing fallback / analyze

if text_goal is None:
    use handoff.goal_key   # H1 today

if text_goal == handoff.goal_key:
    use text_goal

if same_dimension_family(text_goal, handoff.goal_key)
   AND NOT opposite_direction(text_goal, handoff.goal_key)
   AND NOT has_explicit_direction_override(user_input):
    use handoff.goal_key    # G3: undirected / soft domain phrase

else:
    use text_goal           # explicit new goal or other dimension
```

`has_explicit_direction_override` / opposite detection must reuse F-1 direction helpers where possible (`_direction_of`, payload resolver) — **do not** invent a parallel synonym NLP layer.

Exact helper placement is an IC detail; design constraint: **one precedence function**, testable pure, called from `_handle_explore` (or immediately before it).

---

## 5. Non-goals / anti-patterns

| Forbidden | Why |
|---|---|
| Always inherit active goal for any explore phrase | Ignores user override (`ahora aumenta…`) |
| Stuff synonyms into H4 `match_plan_lever` | Wrong layer |
| Change F-1 bare `"payload"` → `aumentar_payload` default globally | Breaks unrelated paths; G3 is explore+handoff scoped |
| Implement G6/G7 in the same cut | Different subsystems |
| Catalog / Impl C | Roadmap |

---

## 6. Engineer decisions — LOCKED (2026-08-14)

| # | Question | Lock |
|---|---|---|
| **★1** | `"optimiza payload"` with active `reducir_payload` inherits reduce? | **Yes** — continuation |
| **★2** | `"optimiza para autonomia"` with active payload plan switches? | **Yes** — different dimension = explicit override |
| **★3** | Full Goal Plan phrase while explore intent active? | If routed as **explore** → use text goal; if **engineering_intent** → existing plan replace. Do not dual-fire. |
| **★4** | After override explore to a new goal? | **Replace** handoff on successful explore (new `goal_key` / levers) so next `"explora opciones"` stays honest |

---

## 7. Acceptance sketch (for IC)

| Case | Expected |
|---|---|
| Plan reducir → `explora opciones` | DSE reducir |
| Plan reducir → `optimiza payload` | DSE reducir |
| Plan reducir → `ahora aumenta el payload` / explore-shaped increase | DSE aumentar |
| Plan reducir → `optimiza para autonomia` | DSE autonomia |
| No handoff → `optimiza payload` | today's text derive (aumentar) |
| Override explore succeeds | HandoffContext replaced with new goal |
| H1–H4 / F-1 regressions | green |

---

## 8. Queue

```text
checkpoint-g5-dse-component-sync ✅
G5 CLI PASS ✅
G6 / G7 registered (no implement) ✅
G3 Design ★1–★4 LOCKED ✅
        ↓
G3 Implementation Contract → Claude
        ↓
G3 code + CLI
        ↓
G1/G2 + H5 design
        ↓
UX catálogo → Impl C
```

---

## 9. Status

**DESIGN CLOSED.** Implementation Contract may be issued. No code until IC is sent to Claude.
