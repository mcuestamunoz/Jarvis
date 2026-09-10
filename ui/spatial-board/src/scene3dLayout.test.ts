import { describe, expect, it } from "vitest";
import { clusterCenterPx, expandSolidCopies, layoutSolidsFromPose, layoutSolidsRow } from "./scene3dLayout";
import { mmToPx, solidWrapperPx } from "./scene3dScale";

describe("layoutSolidsRow", () => {
  it("U5: second originX = first footprint + gap; ignores a fake card x", () => {
    const items = [
      { id: "esc", geometry: { shape: "box" as const, length_mm: 50, width_mm: 21.6, height_mm: 12 }, x: 9999 },
      { id: "motors", geometry: { shape: "disk" as const, diameter_mm: 27.9 } },
    ];
    const laid = layoutSolidsRow(items, 24, 0.5);
    expect(laid[0]).toEqual({ id: "esc", originX: 0 });
    // esc footprint: max(25, 10.8) = 25; next origin = 25 + 24 = 49
    expect(laid[1]).toEqual({ id: "motors", originX: 49 });
  });

  it("U6: empty list -> []", () => {
    expect(layoutSolidsRow([], 24, 0.5)).toEqual([]);
  });

  it("preserves input order", () => {
    const items = [
      { id: "b", geometry: { shape: "disk" as const, diameter_mm: 10 } },
      { id: "a", geometry: { shape: "disk" as const, diameter_mm: 10 } },
    ];
    const laid = layoutSolidsRow(items, 10, 0.5);
    expect(laid.map((l) => l.id)).toEqual(["b", "a"]);
  });
});

describe("layoutSolidsFromPose", () => {
  const fc = { id: "fc", geometry: { shape: "box" as const, length_mm: 44, width_mm: 84, height_mm: 12 } };
  const escBase = { id: "esc", geometry: { shape: "box" as const, length_mm: 50, width_mm: 21.6, height_mm: 12 } };

  it("unposed item stays at its row slot, originY/originZ = 0", () => {
    const laid = layoutSolidsFromPose([fc, escBase], 24, 0.5);
    expect(laid[0]).toEqual({ id: "fc", originX: 0, originY: 0, originZ: 0 });
    // esc footprint fallback slot: fc footprint max(22,42)=42; 42+24=66
    expect(laid[1]).toEqual({ id: "esc", originX: 66, originY: 0, originZ: 0 });
  });

  it("posed item (box origin, all 3 axes) center-to-center with the declared Y<->Z swap", () => {
    const esc = { ...escBase, declaredBoxPose: { originKey: "fc", xMm: 5, yMm: 3, zMm: -2 } };
    const laid = layoutSolidsFromPose([fc, esc], 24, 0.5);
    const escLaid = laid.find((l) => l.id === "esc")!;
    // originCenterX = 0 + 22/2 = 11; originCenterY = 6/2 = 3
    // originX = 11 + mmToPx(5)=2.5 - childWrap.width/2=12.5 -> 1
    expect(escLaid.originX).toBeCloseTo(1);
    // originY = 3 + mmToPx(-2)=-1 - childWrap.height/2=3 -> -1  (declared +Z -> CSS Y)
    expect(escLaid.originY).toBeCloseTo(-1);
    // originZ = mmToPx(3) = 1.5  (declared +Y -> CSS Z/depth, no half-width subtract)
    expect(escLaid.originZ).toBeCloseTo(1.5);
  });

  it("omitted xMm/yMm/zMm count as 0 for display, not a schema default", () => {
    const esc = { ...escBase, declaredBoxPose: { originKey: "fc" } };
    const laid = layoutSolidsFromPose([fc, esc], 24, 0.5);
    const escLaid = laid.find((l) => l.id === "esc")!;
    expect(escLaid.originX).toBeCloseTo(-1.5);
    expect(escLaid.originY).toBeCloseTo(0);
    expect(escLaid.originZ).toBeCloseTo(0);
  });

  it("origin resolving to a disk (not box) falls back to the row slot", () => {
    const motors = { id: "motors", geometry: { shape: "disk" as const, diameter_mm: 27.9 } };
    const propeller = {
      id: "propeller",
      geometry: { shape: "disk" as const, diameter_mm: 127 },
      declaredBoxPose: { originKey: "motors", xMm: 5 },
    };
    const laid = layoutSolidsFromPose([motors, propeller], 24, 0.5);
    // motors footprint 13.95; propeller fallback slot = 13.95 + 24 = 37.95
    expect(laid.find((l) => l.id === "propeller")).toEqual({
      id: "propeller", originX: 37.95, originY: 0, originZ: 0,
    });
  });

  it("origin key absent from the list falls back to the row slot", () => {
    const esc = { ...escBase, declaredBoxPose: { originKey: "ghost", xMm: 5 } };
    const laid = layoutSolidsFromPose([esc], 24, 0.5);
    expect(laid[0]).toEqual({ id: "esc", originX: 0, originY: 0, originZ: 0 });
  });

  it("empty list -> []", () => {
    expect(layoutSolidsFromPose([], 24, 0.5)).toEqual([]);
  });

  it("preserves input order regardless of pose", () => {
    const esc = { ...escBase, declaredBoxPose: { originKey: "fc", xMm: 5 } };
    const laid = layoutSolidsFromPose([esc, fc], 24, 0.5);
    expect(laid.map((l) => l.id)).toEqual(["esc", "fc"]);
  });

  it("U8 (superseded by multi-hop): composes through a posed origin", () => {
    const battery = { id: "battery", geometry: { shape: "box" as const, length_mm: 37, width_mm: 35, height_mm: 75 } };
    const fcPosed = { ...fc, declaredBoxPose: { originKey: "esc", xMm: 100 } };
    const batPosed = { ...battery, declaredBoxPose: { originKey: "fc", xMm: 5 } };
    const laid = layoutSolidsFromPose([fcPosed, escBase, batPosed], 24, 0.5);
    const fromSlot = layoutSolidsFromPose([fc, batPosed], 24, 0.5).find((l) => l.id === "battery")!;
    const batLaid = laid.find((l) => l.id === "battery")!;
    // Multi-hop: battery rides FC's composed center (FC is +100mm X vs ESC),
    // not FC's bare row slot — must differ from the unposed-FC baseline.
    expect(batLaid.originX).not.toBeCloseTo(fromSlot.originX);
    const escWrap = solidWrapperPx(escBase.geometry, 0.5);
    const batWrap = solidWrapperPx(battery.geometry, 0.5);
    // Row order [fc, esc, battery]: ESC slot = fc footprint 42 + gap 24 = 66
    const escSlotX = 66;
    const expectedCenterX = escSlotX + escWrap.width / 2 + mmToPx(100, 0.5) + mmToPx(5, 0.5);
    expect(batLaid.originX).toBeCloseTo(expectedCenterX - batWrap.width / 2);
  });
});

describe("clusterCenterPx", () => {
  const fc = { id: "fc", geometry: { shape: "box" as const, length_mm: 44, width_mm: 84, height_mm: 12 } };
  const esc = { id: "esc", geometry: { shape: "box" as const, length_mm: 50, width_mm: 21.6, height_mm: 12 } };

  it("empty -> {0,0}", () => {
    expect(clusterCenterPx([], [], 0.5)).toEqual({ x: 0, y: 0 });
  });

  it("unposed FC+ESC row: midpoint of the wrapper AABB", () => {
    const items = [fc, esc];
    const laid = layoutSolidsFromPose(items, 24, 0.5);
    const c = clusterCenterPx(laid, items, 0.5);
    // FC wrap 22×6 at (0,0); ESC wrap 25×6 at (66,0) → [0,91] × [0,6]
    expect(c.x).toBeCloseTo(45.5);
    expect(c.y).toBeCloseTo(3);
  });
});

describe("expandSolidCopies", () => {
  const motorsDisk = { shape: "disk" as const, diameter_mm: 27.9 };
  const fc = { id: "fc", geometry: { shape: "box" as const, length_mm: 44, width_mm: 84, height_mm: 12 } };

  it("U1: solidCopies:3 -> three layout ids sharing one selectId, increasing row originX", () => {
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 3 };
    const expanded = expandSolidCopies([motors]);
    expect(expanded.map((e) => e.layoutId)).toEqual(["motors#0", "motors#1", "motors#2"]);
    expect(expanded.every((e) => e.selectId === "motors")).toBe(true);

    const laid = layoutSolidsFromPose(
      expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry, declaredBoxPose: e.declaredBoxPose })),
      24,
      0.5,
    );
    expect(laid[0].originX).toBeLessThan(laid[1].originX);
    expect(laid[1].originX).toBeLessThan(laid[2].originX);
  });

  it("U2: omitted solidCopies -> one item, layoutId === selectId === node id", () => {
    const motors = { id: "motors", geometry: motorsDisk };
    const expanded = expandSolidCopies([motors]);
    expect(expanded).toEqual([{ layoutId: "motors", selectId: "motors", geometry: motorsDisk, declaredBoxPose: undefined }]);
  });

  it("U3: declaredBoxPose on a solidCopies:3 node is stripped from every expanded copy", () => {
    const motors = {
      id: "motors",
      geometry: motorsDisk,
      solidCopies: 3,
      declaredBoxPose: { originKey: "fc", xMm: 5 },
    };
    const expanded = expandSolidCopies([motors]);
    expect(expanded.every((e) => e.declaredBoxPose === undefined)).toBe(true);
  });

  it("U4: clusterCenterPx after expanding two copies is a finite midpoint (unique ids)", () => {
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 2 };
    const expanded = expandSolidCopies([fc, motors]);
    const laid = layoutSolidsFromPose(
      expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry, declaredBoxPose: e.declaredBoxPose })),
      24,
      0.5,
    );
    const c = clusterCenterPx(laid, expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry })), 0.5);
    expect(Number.isFinite(c.x)).toBe(true);
    expect(Number.isFinite(c.y)).toBe(true);
  });

  it("U5: Propeller visor copies B1 — a propellers node with solidCopies:3 expands the same as motors, no id-based special-case", () => {
    const propDisk = { shape: "disk" as const, diameter_mm: 127 };
    const propellers = { id: "propellers", geometry: propDisk, solidCopies: 3 };
    const expanded = expandSolidCopies([propellers]);
    expect(expanded.map((e) => e.layoutId)).toEqual(["propellers#0", "propellers#1", "propellers#2"]);
    expect(expanded.every((e) => e.selectId === "propellers")).toBe(true);
    expect(expanded.every((e) => e.declaredBoxPose === undefined)).toBe(true);
  });

  const quadXOffsets = [
    { xMm: 81.317, yMm: 81.317, zMm: 0 },
    { xMm: 81.317, yMm: -81.317, zMm: 0 },
    { xMm: -81.317, yMm: -81.317, zMm: 0 },
    { xMm: -81.317, yMm: 81.317, zMm: 0 },
  ];

  it("U6: Visor X stations B1 — solidCopies:4 + 4 offsets places copies at those points, not a packed row", () => {
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 4, solidCopyOffsetsMm: quadXOffsets };
    const expanded = expandSolidCopies([motors]);
    expect(expanded.map((e) => e.layoutId)).toEqual(["motors#0", "motors#1", "motors#2", "motors#3"]);
    expect(expanded.map((e) => e.offsetMm)).toEqual(quadXOffsets);

    const laid = layoutSolidsFromPose(
      expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry, offsetMm: e.offsetMm })),
      24,
      0.5,
    );
    // Copy 0 (+a,+a) and copy 2 (-a,-a) are on opposite sides — not a
    // monotonically increasing row (U1's `originX < originX < originX`).
    expect(laid[0].originX).toBeGreaterThan(laid[2].originX);
    expect(laid[0].originZ).toBeGreaterThan(laid[2].originZ);
  });

  it("U7: solidCopies:4 without solidCopyOffsetsMm still lays out as today's row", () => {
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 4 };
    const expanded = expandSolidCopies([motors]);
    expect(expanded.every((e) => e.offsetMm === undefined)).toBe(true);

    const laid = layoutSolidsFromPose(
      expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry, offsetMm: e.offsetMm })),
      24,
      0.5,
    );
    expect(laid[0].originX).toBeLessThan(laid[1].originX);
    expect(laid[1].originX).toBeLessThan(laid[2].originX);
    expect(laid[2].originX).toBeLessThan(laid[3].originX);
  });

  it("U8: solidCopyOffsetsMm length mismatch falls back to the plain row (never a partial station set)", () => {
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 4, solidCopyOffsetsMm: quadXOffsets.slice(0, 2) };
    const expanded = expandSolidCopies([motors]);
    expect(expanded.every((e) => e.offsetMm === undefined)).toBe(true);
  });

  it("U9: declaredBoxPose stays stripped on copies even when offsets are present", () => {
    const motors = {
      id: "motors",
      geometry: motorsDisk,
      solidCopies: 4,
      solidCopyOffsetsMm: quadXOffsets,
      declaredBoxPose: { originKey: "fc", xMm: 5 },
    };
    const expanded = expandSolidCopies([motors]);
    expect(expanded.every((e) => e.declaredBoxPose === undefined)).toBe(true);
  });
});

describe("Visor assembly root B1 (Main Plate at world origin)", () => {
  const motorsDisk = { shape: "disk" as const, diameter_mm: 27.9 };
  const plateBox = { shape: "box" as const, length_mm: 100, width_mm: 100, height_mm: 4 };
  const quadXOffsets = [
    { xMm: 81.317, yMm: 81.317, zMm: 0 },
    { xMm: 81.317, yMm: -81.317, zMm: 0 },
    { xMm: -81.317, yMm: -81.317, zMm: 0 },
    { xMm: -81.317, yMm: 81.317, zMm: 0 },
  ];

  it("U10: frame_plate box roots at world 0; stations share it; a plain row item never inherits the station footprint", () => {
    const plate = { id: "frame_plate", geometry: plateBox };
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 4, solidCopyOffsetsMm: quadXOffsets };
    const esc = { id: "esc", geometry: { shape: "box" as const, length_mm: 50, width_mm: 21.6, height_mm: 12 } };

    const expanded = expandSolidCopies([plate, motors, esc]);
    const laid = layoutSolidsFromPose(
      expanded.map((e) => ({
        id: e.layoutId, geometry: e.geometry, declaredBoxPose: e.declaredBoxPose, offsetMm: e.offsetMm,
      })),
      24,
      0.5,
    );

    const plateWrap = solidWrapperPx(plateBox, 0.5);
    const plateLaid = laid.find((l) => l.id === "frame_plate")!;
    expect(plateLaid.originX).toBeCloseTo(-plateWrap.width / 2);
    expect(plateLaid.originY).toBeCloseTo(-plateWrap.height / 2);
    expect(plateLaid.originZ).toBe(0);

    const motorWrap = solidWrapperPx(motorsDisk, 0.5);
    const motor0 = laid.find((l) => l.id === "motors#0")!;
    expect(motor0.originX).toBeCloseTo(mmToPx(81.317, 0.5) - motorWrap.width / 2);
    expect(motor0.originZ).toBeCloseTo(mmToPx(81.317, 0.5));

    // esc is the ONLY plain-row item -> row cursor 0, never pushed right by
    // the 4 station footprints (N1 tidy, locked #7).
    const escLaid = laid.find((l) => l.id === "esc")!;
    expect(escLaid.originX).toBe(0);
  });

  it("U11: a child posed against the active root measures Δmm from the root's world-0 center, not a row slot", () => {
    const plate = { id: "frame_plate", geometry: plateBox };
    const battery = {
      id: "battery",
      geometry: { shape: "box" as const, length_mm: 80, width_mm: 34, height_mm: 22 },
      declaredBoxPose: { originKey: "frame_plate", zMm: 8 },
    };
    const laid = layoutSolidsFromPose([plate, battery], 24, 0.5);
    const batteryWrap = solidWrapperPx(battery.geometry, 0.5);
    const batteryLaid = laid.find((l) => l.id === "battery")!;
    // origin center (0,0) + zMm=8 on the CSS Y axis (declared +Z -> CSS Y).
    expect(batteryLaid.originX).toBeCloseTo(0 - batteryWrap.width / 2);
    expect(batteryLaid.originY).toBeCloseTo(mmToPx(8, 0.5) - batteryWrap.height / 2);
  });

  it("U12: no frame_plate box -> stations still sit at world 0 and a plain row item stays footprint-free (N1 tidy applies with or without a root)", () => {
    const motors = { id: "motors", geometry: motorsDisk, solidCopies: 4, solidCopyOffsetsMm: quadXOffsets };
    const fc = { id: "flight_controller", geometry: { shape: "box" as const, length_mm: 44, width_mm: 84, height_mm: 12 } };
    const expanded = expandSolidCopies([motors, fc]);
    const laid = layoutSolidsFromPose(
      expanded.map((e) => ({
        id: e.layoutId, geometry: e.geometry, declaredBoxPose: e.declaredBoxPose, offsetMm: e.offsetMm,
      })),
      24,
      0.5,
    );
    const motorWrap = solidWrapperPx(motorsDisk, 0.5);
    const motor0 = laid.find((l) => l.id === "motors#0")!;
    expect(motor0.originX).toBeCloseTo(mmToPx(81.317, 0.5) - motorWrap.width / 2);

    // Documented choice (IC §0.7's unqualified "items with offsetMm do not
    // advance the row cursor" — the N1 tidy fixes this regardless of
    // whether a root is active this cycle): FC is the only row item, so it
    // sits at cursor 0 even with no frame_plate box anywhere in the list.
    const fcLaid = laid.find((l) => l.id === "flight_controller")!;
    expect(fcLaid.originX).toBe(0);
  });

  it("U13: only exactly frame_plate as a box activates root — frame_plate_2 and a boxless frame_plate do not", () => {
    const plate2 = { id: "frame_plate_2", geometry: plateBox };
    const fc = { id: "flight_controller", geometry: { shape: "box" as const, length_mm: 44, width_mm: 84, height_mm: 12 } };

    const laidWrongKey = layoutSolidsFromPose([plate2, fc], 24, 0.5);
    // frame_plate_2 gets a PLAIN row slot at cursor 0 — never world-0
    // centering, even though it's a box.
    expect(laidWrongKey.find((l) => l.id === "frame_plate_2")!.originX).toBe(0);
    expect(laidWrongKey.find((l) => l.id === "flight_controller")!.originX).toBeGreaterThan(0);

    const plateDisk = { id: "frame_plate", geometry: { shape: "disk" as const, diameter_mm: 50 } };
    const laidNotBox = layoutSolidsFromPose([plateDisk, fc], 24, 0.5);
    // frame_plate present but shaped as a disk (no envelope box declared)
    // -> still today's row, not root.
    expect(laidNotBox.find((l) => l.id === "frame_plate")!.originX).toBe(0);
    expect(laidNotBox.find((l) => l.id === "flight_controller")!.originX).toBeGreaterThan(0);
  });
});

describe("Pose multi-hop composition B1", () => {
  const plateBox = { shape: "box" as const, length_mm: 100, width_mm: 100, height_mm: 4 };
  const fcBox = { shape: "box" as const, length_mm: 44, width_mm: 84, height_mm: 12 };
  const escBox = { shape: "box" as const, length_mm: 50, width_mm: 21.6, height_mm: 12 };

  it("U20: ESC vs posed FC vs plate root sits on composed FC center, not FC row slot", () => {
    const plate = { id: "frame_plate", geometry: plateBox };
    const fc = { id: "flight_controller", geometry: fcBox, declaredBoxPose: { originKey: "frame_plate", zMm: 8 } };
    const esc = { id: "esc", geometry: escBox, declaredBoxPose: { originKey: "flight_controller", xMm: 5 } };
    const laid = layoutSolidsFromPose([plate, fc, esc], 24, 0.5);
    const escWrap = solidWrapperPx(escBox, 0.5);
    const escLaid = laid.find((l) => l.id === "esc")!;
    // FC composed center = (0, mmToPx(8), 0); ESC = that + 5mm X
    expect(escLaid.originX).toBeCloseTo(mmToPx(5, 0.5) - escWrap.width / 2);
    expect(escLaid.originY).toBeCloseTo(mmToPx(8, 0.5) - escWrap.height / 2);
    expect(escLaid.originZ).toBeCloseTo(0);

    // Prove it is NOT the old single-hop-from-FC-slot placement: with root
    // active FC is the only row item → slot 0; old math would put ESC at
    // FC slot center + 5mm X with originY from FC wrap height/2 only (no +8).
    const fcWrap = solidWrapperPx(fcBox, 0.5);
    const oldOriginY = fcWrap.height / 2 - escWrap.height / 2;
    expect(escLaid.originY).not.toBeCloseTo(oldOriginY);
  });

  it("U21: single-hop ESC vs unposed FC (no root) matches pre-multihop arithmetic", () => {
    const fc = { id: "fc", geometry: fcBox };
    const esc = { id: "esc", geometry: escBox, declaredBoxPose: { originKey: "fc", xMm: 5, yMm: 3, zMm: -2 } };
    const laid = layoutSolidsFromPose([fc, esc], 24, 0.5);
    const escLaid = laid.find((l) => l.id === "esc")!;
    expect(escLaid.originX).toBeCloseTo(1);
    expect(escLaid.originY).toBeCloseTo(-1);
    expect(escLaid.originZ).toBeCloseTo(1.5);
  });

  it("U22: cycle A↔B still lays both solids without throwing", () => {
    const a = {
      id: "a",
      geometry: { shape: "box" as const, length_mm: 40, width_mm: 20, height_mm: 10 },
      declaredBoxPose: { originKey: "b", xMm: 10 },
    };
    const b = {
      id: "b",
      geometry: { shape: "box" as const, length_mm: 30, width_mm: 20, height_mm: 10 },
      declaredBoxPose: { originKey: "a", xMm: 10 },
    };
    expect(() => layoutSolidsFromPose([a, b], 24, 0.5)).not.toThrow();
    const laid = layoutSolidsFromPose([a, b], 24, 0.5);
    expect(laid).toHaveLength(2);
    expect(laid.every((l) => Number.isFinite(l.originX) && Number.isFinite(l.originY) && Number.isFinite(l.originZ))).toBe(true);
  });

  it("U23: mid-chain not-box origin -> child stays on its row slot", () => {
    const disk = { id: "motors", geometry: { shape: "disk" as const, diameter_mm: 27.9 } };
    const esc = {
      id: "esc",
      geometry: escBox,
      declaredBoxPose: { originKey: "motors", xMm: 5 },
    };
    const laid = layoutSolidsFromPose([disk, esc], 24, 0.5);
    expect(laid.find((l) => l.id === "esc")).toEqual({
      id: "esc", originX: 13.95 + 24, originY: 0, originZ: 0,
    });
  });

  it("U24: offsetMm station ignores pose chain and stays absolute around world 0", () => {
    const plate = { id: "frame_plate", geometry: plateBox };
    const fc = { id: "flight_controller", geometry: fcBox, declaredBoxPose: { originKey: "frame_plate", zMm: 8 } };
    const motor = {
      id: "motors#0",
      geometry: { shape: "disk" as const, diameter_mm: 27.9 },
      offsetMm: { xMm: 81.317, yMm: 81.317, zMm: 0 },
      declaredBoxPose: { originKey: "flight_controller", xMm: 999 },
    };
    const laid = layoutSolidsFromPose([plate, fc, motor], 24, 0.5);
    const motorWrap = solidWrapperPx(motor.geometry, 0.5);
    const motorLaid = laid.find((l) => l.id === "motors#0")!;
    expect(motorLaid.originX).toBeCloseTo(mmToPx(81.317, 0.5) - motorWrap.width / 2);
    expect(motorLaid.originZ).toBeCloseTo(mmToPx(81.317, 0.5));
    // Must not pick up FC's +8mm Z→Y from the stripped/ignored pose.
    expect(motorLaid.originY).toBeCloseTo(0 - motorWrap.height / 2);
  });
});
