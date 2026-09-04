# Engineer notes — Structure A (hypotheses)

**Not a report.** Claude must verify or refute **seams** with `file:line`. Product model below is Engineer-ratified (physics + class-compatibility language).

## Product (locked)

```text
diameter_in → propulsion (OP / filter / D⁴ if no thrust)     [do not edit]
diameter_in + size_class_inch → CLASS COMPATIBILITY LEVEL A  [this slice]
size_class_inch ↛ thrust / power / RPM / Ct / autonomy
```

- \(D\) is physical prop diameter. `size_class_inch` is an architectural **label**. Screening, not CAD.
- \(D\) known + no class → unverifiable / incomplete (not silent ✓).
- \(D \le\) class → CLASS COMPATIBILITY PASS (clearance **not** demonstrated).
- \(D >\) class → CLASS COMPATIBILITY GAP / incomplete (physical impossibility **not** demonstrated).
- Never: FIT VERIFIED, “cabe”, +0.25", mm→class, copy class from prop.
- Pitch / tri-blade / bullnose: no invented \(C_T\).
- Physically **B** (masa + class compatibility). A only if code seams are unclean.

## Code hypotheses (seams)

1. Walk `PVC 200g` → iterate strips grams before `set_frame_material` (Claude report: session extractor, not only `apply_material_definition`).
2. `"carbono 450g"` already `set_frame_material`.
3. Completeness is mass+material; class-required-when-\(D\) needs a project-level helper or 4/4 lies.
4. `GAP-PROP-MOTOR-MISMATCH` ≠ frame class screen.
5. No +0.25 slack.

## Frozen

No CAD, no class→thrust, no invent density, no VERIFIED, no “cabe”, no H5.
