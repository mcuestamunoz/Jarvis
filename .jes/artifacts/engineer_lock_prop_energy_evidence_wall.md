# Engineer lock — Prop/Energy evidence wall (2026-09-05)

**Status:** LOCKED (docs only — no IC)  
**Author:** Engineer reflection → Cursor recorded  
**Suite:** **2294** · Structure plate multiplicity smoke ACCEPT  

## Lock

**Propulsion / Energy experimental validation is a physical wall, not software debt and not 🔴 PRIORIDAD.**

Current `~N min` autonomy is at most an **orientative energy estimate** from a simplified power model. It is **not** “the drone will fly N minutes.”

Closing a physically defensible autonomy requires:

```text
hardware + measurement → experimental evidence → model → autonomy
```

not:

```text
more code → reliable autonomy
```

Specifically: an **Operating Point → consumption** relation (thrust/voltage/current/power across regimes), not only max OP → max power. Without bench + instrumented motor/ESC/prop/battery, Jarvis must not invent SOC/sag/C-rate/efficiency/thermal “precision.”

## Allowed meanwhile

- Keep claim boundaries honest (weak evidence labels, ESTIMATIVO, L1/L2 posture already shipped).
- Optional later: **investigation** of what evidence schema to ingest *when* the bench exists — **not** an implementation campaign now.
- Work software where evidence already exists: System-level Optimization, further KNOW Structure (model Buy only), robustness — without pretending autonomy maturity rose.

## Forbidden as default next

- “Prop/Energy Evidence implementation” framed as closing autonomy.
- Adding sag / SOC / variable efficiency / thermal models without T1/T2 data.
- Proposing HD-* as 🔴 PRIORIDAD after closing a product IC.

## Pointers

- Live register: [`docs/HARDWARE_DEBT.md`](../../docs/HARDWARE_DEBT.md) (HD-001… + **HD-004** OP→consumption wall).
- Queue: [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD.
- Vision: [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) §8/§9.
