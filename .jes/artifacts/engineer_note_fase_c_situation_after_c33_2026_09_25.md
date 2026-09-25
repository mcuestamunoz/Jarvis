# Informe de situación — Fase C after C33 review (2026-09-25)

**Audience:** Engineer  
**C33:** [review PASS WITH NOTES](implementation_review_fase_c_spi_scripted_slave_b1.md) — ★ ACCEPT CLOSED @ **`v0.5.31`**  
**C34:** [review PASS WITH NOTES](implementation_review_fase_c_spi_scripted_gyro_probe_b1.md) — ★ ACCEPT CLOSED @ **`v0.5.32`**  
**Desk:** two plates in hand; **no battery, no motors**. F460 stack is on the table with Betaflight. Not a reason to flash Jarvis.

Honesty line for this whole phase:

```text
scripted SPI ≠ gyro live ≠ chip SPI ≠ DShot pin ≠ motors ≠ flying
```

---

## 1. Where the software tip is

Package **`0.5.32`**. Git tag **`v0.5.32`**.

C0–C34 are ACCEPT CLOSED.

On the Mac, the control ladder exists end-to-end **in RAM / host tests**:

| Layer | What exists | What it is not |
|---|---|---|
| Intent / Safety | HOLD/LAND surface; default **RejectAll**; ArmedAllowlist exists | allow ≠ execute |
| IMU | Simulated samples + EMA filter + complementary attitude | not ICM42688P |
| Control | PD → rate→torque-like → quad-X mixer → `step()` | not a flying plant |
| ESC path | `EscOutput` + simulated sink; PWM µs; **DShot 16-bit in RAM** | not a pin, not a spinning motor |
| Radio | CRSF fixture → bytes → host FD/baud 420000; aux→kill Authority | not live ELRS on UART2 |
| UART HAL | `UartBytePort` + loopback | not chip USART |
| SPI HAL | `SpiBytePort` + `LoopbackSpi` + `ScriptedSpi` + **`probe_rx` client** | not SPI1, not gyro |
| MCU image | `fc_mcu_stub.elf` / `.bin` + cited FLASH map + PC13 LED **in the binary** | **not flashed**; Betaflight stays |

`craft ↔ flight_software` is still **zero**. Registry skills list is still empty.

---

## 2. What “cerrar esta fase” means (without real ESC/FC)

The software-on-Mac / **no-pin** HAL *port* chapter is complete: **C33 ACCEPT** + tag **`v0.5.31`**.

That freeze is: UART stub, SPI loopback, SPI scripted slave, DShot *encode*, PWM *sim*, `step`, CRSF host path, Safety RejectAll, DFU **file** (unflashed).

You do **not** need motors, battery, or the F460 powered to close that chapter.

---

## 3. Still allowed later — still not real ESC/FC

Optional, one front at a time, **no solder**:

| # | Optional | Demonstrates | Still impossible |
|---|---|---|---|
| **1 → C34** | [`probe_rx`](implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md) | **CLOSED** @ `v0.5.32` | gyro live / SPI1 / WHO_AM_I |
| **2 → C35** | [`step` denser tests](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) (IC READY) | 1000 canned ticks + failsafe→`step` | 6-DoF flight |
| **3** | Taller CSS cuboid faces (COLA) | six faces meet on a thin plate | CAD / fit |
| **4** | Standoff perimeter points (COLA) | eight cylinders, points to correct | hole-pattern fact |

### 3.1 Do 1 and 2 lay a base for the real board?

**Yes, if they stay thin.** The foundation already shipped is the **port** (`SpiBytePort`) and the **tick** (`step()`). On the real board you swap the *implementation behind the same call*, not a new ladder.

- **Gyro-shaped test:** worth it if it is a **client of `SpiBytePort`** (ask for n bytes, get canned RX). That is the same call a later SPI1 port would answer. **Not** worth it if it becomes a fake ICM42688P register map — that would rot the day the real chip disagrees, and it is not a sample. Gain now: the driver-shaped code is written against the port; silicon only replaces `ScriptedSpi` with a chip port.
- **Denser `step`:** worth it if it locks **failsafe, hold, many ticks, no plant**. When IMU bytes later come from a gyro, `step()`’s inputs stay the same struct. **Not** a 6-DoF simulator. Gain now: regressions so a future HAL swap cannot silently break the mixer/`EscOutput` chain.

**3 and 4** (Taller / standoffs) do **not** help the F460. They help you see the two plates you already have.

Still parked as *other* no-pin software (not in the four-point attack): deepen C20 Authority; craft↔FS. None of this is required to close the no-pin HAL chapter (ACCEPT C33). None spin a motor.

---

## 4. Parked until bench + battery + motors (= real ESC/FC)

Do **not** open these to “finish Fase C”. They **are** the silicon/craft campaign ([bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md)):

- C30 **desk DFU** (overwrites Betaflight; needs restore path you trust)
- DShot **wire** / GPIO / timers
- On-chip USART
- Gyro driver on **SPI1** / CS pin
- Safety **execute**
- First power, motors tab, props

Missing on the desk for that campaign: **LiPo 6S**, **4 motors**, charger, smoke stopper, RX if you want sticks. Plates and the F460 stack are not enough. FC marketing 8S ≠ pack: ESC is **6S**.

---

## 5. Parallel geometry (not Fase C)

Plates in hand **are** useful here, without motors:

- Taller CSS cuboid: six faces explode on thin plates (visor bug, not extra parts)
- Standoff 8-cylinder layout: **COLA**, perimeter points to correct, no ACCEPT
- Bottom plate L×W still unknown
- ESC/FC 23 mm visor tope ≠ 18 mm sandwich caliper

That track does not close or block Fase C.

---

## 6. Recommended sequence

1. **C33 ACCEPT** @ **`v0.5.31`** — done.  
2. **C34 ACCEPT** @ **`v0.5.32`** — done. Port **client** closed.  
3. ★ **C35** [`B1-fase-c-step-failsafe-hold-ticks`](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) — tests only.  
4. Then cola: Taller CSS cuboid · standoff points. Stop Fase C **silicon** until battery + motors + bench exist.
