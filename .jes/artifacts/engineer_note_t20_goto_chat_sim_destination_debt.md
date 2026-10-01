# Engineer note — T20 debt: chat GO_TO ↔ C40 sim needs destination

**Date:** 2026-10-01  
**Authority:** Engineer (pre-ACCEPT T20) — leave architecture ready; document debt; wire later when destination exists  
**Status:** **OPEN debt** · T20 ★ ACCEPT CLOSED @ **`v0.6.29`** (debt remains; seam ready)  
**Parents:** T8 ★ (`B1-assistant-vehicle-go-to-task` @ `v0.6.16`) · C40 ★ (`B1-fase-c-autonomy-executor` @ `v0.5.41`) · T20 ★ @ **`v0.6.29`**  
**SoT pointers:** [T20 review N1](implementation_review_assistant_chat_sim_copper_b1.md) · [T20 report §2](implementation_report_assistant_chat_sim_copper_b1.md) · PRIORIDAD cola row **SD-GO_TO**

---

## 1. What the clash is (product language)

Two correct locks from different eras meet at chat GO_TO:

| Layer | Lock | Effect today |
|---|---|---|
| **T8 — chat** | GO_TO is a mando phrase; **no coordinate / waypoint parse** — empty params forever in that Buy | Chat can say “go to” without a destination |
| **C40 — sim** | `SimAutonomyExecutor.tick(GO_TO, …)` **requires** finite `x_m` / `y_m` | Sim cannot tick GO_TO without a target |
| **T20 — bridge** | After Safety `allow`, attempt sim tick for HOLD/LAND/GO_TO | HOLD/LAND tick; GO_TO cannot honestly tick |

This is **architecture debt**, not a hidden bug. T20 chose honesty over invention.

---

## 2. What T20 already leaves ready (do not rip out)

The wire is already shaped for a later fill-in:

1. Chat path: `_handle_vehicle_go_to` → after `allow` → `_sim_autonomy_tick_note(GO_TO)`.
2. Helper owns the lazy `SimAutonomyExecutor` (same process as HOLD/LAND).
3. Today: empty `SimAutonomyParams()` → C40 `ValueError` → Spanish note *“Simulación no disponible sin destino…”*.
4. `submit_command` / C4 surface stay `not_implemented` (path a) — unchanged when destination arrives unless a separate Buy widens execution semantics.
5. Test T1c locks the honest “sin destino” message until a destination Buy replaces it.

**Later wire (when ready):** supply real `x_m`/`y_m` into the tick (from parse, default, or explicit user target) **inside** that helper / fulfill — then the same allow→tick path produces a real sim note like HOLD/LAND. No need to invent a parallel GO_TO executor.

---

## 3. What must NOT be done as a “quick fix”

- Invent default coordinates (`0,0`, home, etc.) without an Engineer ★ that defines the meaning.
- Silently catch all errors and claim a successful GO_TO tick.
- Relax C40 so GO_TO ticks without a target (breaks sim honesty).
- Claim copper / ESC / live navigation.

---

## 4. Future Buy sketch (not AUTHORIZED)

**Candidate id:** `B1-assistant-chat-go-to-destination` (name flexible)  
**When:** after T20 ★; typically after Skill-first / when chat (or voice) can name a target honestly.  
**Likely locks (draft — DC later):**

1. Finite, honest way to obtain destination for chat GO_TO (phrase params, follow-up turn, or documented default with Engineer ★).
2. Pass `x_m`/`y_m` into `SimAutonomyParams` on the existing T20 tick path.
3. Message: real simulación note when tick succeeds; keep “sin destino” if still missing.
4. Still never copper / ESC; still path (a) unless a separate execution Buy.
5. Retarget T1c; no tip pins.

**Out of that Buy unless ★:** TAKEOFF/RH/FOLLOW/PATROL sim ticks · live copper · voice.

---

## 5. Checklist for whoever opens the Buy

- [ ] DC ★ locks how destination is obtained (no silent invent)
- [ ] IC wires params into existing `_sim_autonomy_tick_note` / fulfill — not a second sim stack
- [ ] T1c replaced by armed GO_TO → tick observed (or still honest miss if no target)
- [ ] HOLD/LAND/PATROL/disarmed regressions still green
- [ ] This note Status → **CLOSED** on ★ ACCEPT of that Buy

---

## 6. Engineer decision (this note)

**2026-10-01:** Leave T20 as-is for ACCEPT. Architecture seam stays. Debt listed in PRIORIDAD as **SD-GO_TO**. Do not block the cola on coordinate parse today.
