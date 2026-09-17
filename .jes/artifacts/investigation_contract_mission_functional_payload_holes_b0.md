# Investigation Contract — Mission → functional payload holes before propulsion (B0)

**Project:** Jarvis  
**Date:** 2026-09-15  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_mission_functional_payload_holes_b0.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · [report](investigation_report_mission_functional_payload_holes_b0.md) · [review](investigation_review_mission_functional_payload_holes_b0.md) · await Engineer ★ Buy shape (lean **B1-min (a)** gate)  
**Parents:**
- Post-smoke design note — [engineer_note_next_after_craft_montage_smoke.md](engineer_note_next_after_craft_montage_smoke.md) — lean **A** (novice design spine before mounts)
- Greenfield smoke ACCEPT — `dron-de-vigilancia-doméstico` (craft montage guide walk): wizard asks payload **kg**, then propulsion; Continuity later suggests “Aumentar carga útil” despite mission “vigilancia”
- Craft montage guide CLOSED — [USER_GUIDE_CRAFT_MONTAGE.md](../../docs/USER_GUIDE_CRAFT_MONTAGE.md) — Board path exists; **does not** teach mission decomposition
- Continuity / ERF — [CONTINUITY_MAP.md](../../docs/system_map/08_continuity/CONTINUITY_MAP.md) · claim hygiene / ASSEMBLY READY semantics
- Reasoning next-step — `reasoning_layer.py` margin → `increase_payload` (observe; **not** the primary Q of this investigation)
- Assembly kit template / kit hardware — connector/harness/prop_adapter exist as **identity kit holes**, not camera/VTX/RX
- Control parity — FC/GPS = identity + envelope; **no** firmware generation
- Feature locks: craft montage honesty · no invent mm · LLM ≠ engineering SoT

**Type:** Deep **as-is vs product-need** investigation of the **early design spine**: how (if at all) Jarvis turns a **mission objective** into **functional payload / subsystem holes** (camera, link, endurance target, navigation, communications) **before** propulsion catalog picks — for a user with **no prior drone knowledge**.  
**Not** an IC. **Do not implement. Do not bump version. Do not invent catalog SKUs or masses. Do not mutate `workspace/`. Do not open a Conversation Engine. Do not “generate FC software.”**

**Checkpoint:** package **`0.4.1`** · suite ≥**2929** · UI ≥**105** (or current green at ★ time)

**Live smoke that triggered this (Engineer 2026-09-15):**

```text
nuevo proyecto → "dron de vigilancia doméstico" → payload 1 kg → no restrictions
→ detallado → 4 motors → propulsion catalog first
→ kit holes (power_connector / signal_harness / prop_adapter) nag Continuity
→ later PASS + "Siguiente paso: Aumentar carga útil"
→ montage path worked only after guide + actualiza frame + arm box

Missing from the path: camera, video link, autonomy target as design driver,
comms — anything that "vigilancia doméstico" implies beyond "1 kg payload".
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy shape(s) before any IC.

---

## 0. Role split

```text
Engineer  → wants novice 0→drone design that respects mission, not only kg + motors
Cursor    → this contract; review; IC only after ★ on Buy shape(s)
Claude    → investigation_report_mission_functional_payload_holes_b0.md
```

---

## 1. Why this exists

Craft montage (Board) is now **walkable**. The remaining product gap for a true novice is **upstream**:

| Today (as seen in smoke) | Needed (design spine A) |
|---|---|
| Objective is free text → stored | Objective **decomposed** into what the craft must carry/do |
| `payload_kg` is a number | Payload = **functional stack** (camera + link + …) whose masses **sum** toward kg |
| Architecture = motors/props/ESC/battery/frame/FC/sensors | Plus (or before) mission-driven holes: imaging, air-link, endurance, … |
| Next-step after PASS = thrust-margin heuristics | Next-step **aware of undemonstrated mission needs** (observe Continuity; investigate coupling carefully) |

Wrong next step:

```text
· LLM invents camera Wh / link range / “typical vigilancia kit”
· Generate Betaflight/PX4 config or companion apps
· Collapse into Continuity “intent engine” mega-Buy without inventory
· Force montage/geometry Buys
· Quietly add library/camera with invented mm/g
· Treat “Aumentar carga útil” fix as the whole of A
```

Right questions (all must be answered with evidence):

> **Q1 (as-is create path):** What does `CREATE_PROJECT_INTERACTIVE` (and immediately after) actually ask and store for aerial drones? Where does `objective` / `payload_kg` / `restrictions` go, and what **never** gets asked?  
> **Q2 (architecture holes):** What component keys / blocks exist today for “mission payload” (camera, VTX, RX, companion, …)? What is only kit identity (XT60/JST/prop_adapter)? What would a new family require (schema, library, ERF, Continuity)?  
> **Q3 (mass/energy coupling):** How does `payload_kg` enter calc/sim today? Can functional components’ cited masses replace or constrain that number honestly? What breaks if we add holes without masses?  
> **Q4 (novice spine):** Ranked Buy shapes from **B0 leave gap** → thin checklist assist → wizard steps → catalog families — what is the **smallest honest** next ★ that helps “vigilancia” without inventing physics or firmware?  
> **Q5 (Continuity observe):** Confirm (cite) why PASS → “Aumentar carga útil” ignores mission text; recommend **park / separate ★ / couple to A** with evidence — do **not** implement Continuity rewrite in this investigation.

---

## 2. Locked stances

1. **ProjectState remains SoT.** No parallel “mission graph” SoT in the LLM.  
2. **Deterministic engineering stays deterministic.** Mission assist may be checklist / structured questions; masses/power still cited or Engineer-declared.  
3. **No invented camera/VTX/RX specs.** Catalog Class A only with real bags; otherwise hole = identity stub / “pendiente”.  
4. **No firmware / MAVLink / radio flashing Buy** from this investigation — capability tags later, if ever.  
5. **FC/GPS stay** identity + envelope (library/fc · library/sensors). Do not reopen P0.  
6. **Montage / Situar / plate-box / Path N** out of scope except as “comes after design spine”.  
7. **Prefer ranked Buys**, including **B0 park**, and **split** “mission checklist” from “new catalog family” from “Continuity next-step”.  
8. **No Conversation Engine.** No version bump. Read-only on `workspace/` (census only).  
9. **Spanish CLI reality** — any proposed phrases must fit Continuity/IDLE patterns already used (or be explicitly new surface).

---

## 3. Baseline to inventory (cite live tree · `file:line`)

### 3.1 Project create / requirements

| Surface | Check |
|---|---|
| `CREATE_PROJECT_INTERACTIVE` session / wizard steps | Exact questions; order; what “dron” unlocks |
| `objective`, `payload_kg`, `restrictions`, detail level | Where stored on `ProjectState` / `current_parameters` |
| `state_schema` / `parsed_constraints` | Autonomy/weight mined from restrictions/objective — limits |
| Requirements / ERF requirements subsystem | What “PASS” means without mission payload |

### 3.2 Architecture & BOM holes

| Surface | Check |
|---|---|
| Architecture default for aerial | Block list; when kit holes appear |
| `BLOCK_TO_COMPONENTS` / BOM classifier | Which keys are first-class |
| Kit template (power_connector, signal_harness, prop_adapter) | Why Continuity nags them; relation to “mission” |
| Sensors / FC | GNSS vs “camera” — naming collision risk |
| Any existing camera/VTX/RX/companion mentions | Docs, HARDWARE_DEBT, library folders |

### 3.3 Mass / energy / propulsion entry

| Surface | Check |
|---|---|
| How `payload_kg` feeds `CalculationEngine` / sim | Formula path |
| Component masses from catalog bind | Do they reduce or add to payload? |
| Autonomy_target / endurance | Opt-in paths; when asked vs never |
| Propulsion-first acquisition | Why motor catalog opens before mission stack |

### 3.4 Continuity next-step (observe arm)

| Surface | Check |
|---|---|
| `reasoning_layer` `increase_payload` | Trigger conditions |
| `project_continuity` ranking | When suggested_action becomes next_useful_step |
| Tests that already suppress “Aumentar carga útil” | What gates exist today |

### 3.5 Live census (read-only)

| Project | Check |
|---|---|
| `dron-de-vigilancia-doméstico-*` | objective, payload_kg, restrictions, components present/absent vs “vigilancia” intuition |
| Contrast `10-min-autonomía` | Autonomy-named project — does spine ask endurance earlier? |

Do **not** mutate workspace.

---

## 4. Report sections (required)

### A. Create-path map (as-is)

Step table: wizard/Continuity step → user answer in vigilancia smoke → field written → what it enables next. Mark **mission-blind** steps.

### B. Hole taxonomy

Table of potential “functional payload” concepts:

| Concept | Exists as key today? | Catalog? | Mass in energy? | Geometry? | Notes |
|---|---|---|---|---|---|
| camera / gimbal | | | | | |
| video tx / goggles path | | | | | |
| RC / ELRS / radio | | | | | |
| companion computer | | | | | |
| autonomy target (min) | | | | | |
| GNSS (already sensors) | | | | | |
| kit connector/harness/adapter | | | | | |

Classify each: **EXISTS** / **STUB-ONLY** / **MISSING** / **OUT (firmware)**.

### C. Coupling risks

If we add mission holes, what must stay honest:

- Double-counting mass (payload_kg **and** camera mass)  
- ERF BOM INCOMPLETE forever if camera has no catalog  
- ASSEMBLY READY while mission undemonstrated (claim hygiene)  
- Sensors key overloaded (GNSS vs camera)

### D. Ranked Buy options (mandatory)

At least:

| ID | Shape | In | Out | Risk |
|---|---|---|---|---|
| **B0** | Leave gap; improve guide “mission before montage” only | docs | code | Novice still lost in CLI |
| **B1-min checklist** | IDLE/`estado` suggest-only: “para vigilancia declara/pendiente: cámara, link, autonomía…” from **deterministic** keyword/mission tags — **no** new components | thin assist | catalog invent | Keyword brittleness |
| **B1 wizard steps** | Extra create questions (endurance? camera yes/no?) → store structured flags / pending holes | create session | firmware | Scope creep |
| **B1 catalog family** | `library/cameras` or `payload` (+ bind) with **cited** seeds only | new family | invent mm/g | Needs Engineer bags |
| **Separate ★** | Continuity next-step vs intent (suppress/replace increase_payload when mission undemonstrated) | Continuity | mission decomposition | Easy to overfit |

Recommend **one primary ★** + what to park. Explicitly allow **B0**.

### E. Continuity observe (short)

Cite code for “Aumentar carga útil”; recommend park vs couple; **no** implementation plan beyond “future IC if ★”.

### F. Non-goals confirmed

Firmware, MAVLink, montage, invent SKUs, Conversation Engine — explicitly not recommended as next.

---

## 5. Done when

- [ ] ★ on this investigation  
- [ ] Report covers Q1–Q5 + sections A–F with `file:line` evidence  
- [ ] Ranked Buys including B0  
- [ ] Cursor investigation review  
- [ ] Engineer ★ picks Buy shape (or B0 park) → only then IC

---

## 6. Handoff

```text
Engineer → ★ this investigation (optional: focus mission example = vigilancia)
Claude   → report only (read-only code + workspace census)
Cursor   → investigation review
Engineer → ★ Buy shape or B0
Cursor   → IC if Buy taken
```
