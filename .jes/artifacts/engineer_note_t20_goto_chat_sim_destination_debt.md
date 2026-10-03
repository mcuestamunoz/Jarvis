# Engineer note — T20 debt: chat GO_TO ↔ C40 sim needs destination

**Date:** 2026-10-01  
**Authority:** Engineer (pre-ACCEPT T20) — leave architecture ready; document debt; wire later when destination exists  
**Status:** **Buy AUTHORIZED** · T32 `B1-assistant-chat-go-to-destination` @ **`0.6.41`** — closes on Engineer ★ ACCEPT of that Buy · T20 ★ @ **`v0.6.29`**  

**Parents:** T8 ★ (`B1-assistant-vehicle-go-to-task` @ `v0.6.16`) · C40 ★ (`B1-fase-c-autonomy-executor` @ `v0.5.41`) · T20 ★ @ **`v0.6.29`**  
**SoT pointers:** [T20 review N1](implementation_review_assistant_chat_sim_copper_b1.md) · [T20 report §2](implementation_report_assistant_chat_sim_copper_b1.md) · PRIORIDAD cola row **SD-GO_TO** · this row is indexed, alongside every other connect-later debt, in the [connect plugs / real-data map](engineer_note_connect_plugs_real_data_map.md) (T33, id `sd-go-to`)

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

## 4. Buy (★ AUTHORIZED 2026-10-03)

**Id:** `B1-assistant-chat-go-to-destination` (cola **T32**, package **`0.6.41`**)  
**DC:** [design_contract_assistant_chat_go_to_destination_b0.md](design_contract_assistant_chat_go_to_destination_b0.md) ★ CLOSED  
**IC:** [implementation_contract_assistant_chat_go_to_destination_b1.md](implementation_contract_assistant_chat_go_to_destination_b1.md) ★ AUTHORIZED  

Locks (summary): resolver seam — (1) metadata `go_to_x_m`/`go_to_y_m` connect plug for later real coords, (2) finite prove-now parse `go to <x> <y>` etc., (3) else None / sin destino — never invent defaults; wire into existing T20 tick path only.

**Out unless ★:** TAKEOFF/RH/FOLLOW/PATROL sim ticks · live copper · voice · GPS hardware.

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

**2026-10-03:** After Skill-first phase B ★ @ `v0.6.40`, Engineer opens T32 Buy now — leave wire ready so real coordinates later only connect into the metadata plug. Close this note on T32 ★ ACCEPT.
