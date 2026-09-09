import { describe, expect, it } from "vitest";
import { clusterCenterPx, expandSolidCopies, layoutSolidsFromPose, layoutSolidsRow } from "./scene3dLayout";

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

  it("U8: does not compose through a posed origin (one hop from the origin row slot)", () => {
    const battery = { id: "battery", geometry: { shape: "box" as const, length_mm: 37, width_mm: 35, height_mm: 75 } };
    const fcPosed = { ...fc, declaredBoxPose: { originKey: "esc", xMm: 100 } };
    const batPosed = { ...battery, declaredBoxPose: { originKey: "fc", xMm: 5 } };
    const laid = layoutSolidsFromPose([fcPosed, escBase, batPosed], 24, 0.5);
    const fromSlot = layoutSolidsFromPose([fc, batPosed], 24, 0.5).find((l) => l.id === "battery")!;
    const batLaid = laid.find((l) => l.id === "battery")!;
    // Same child math as if FC had never left its own row slot.
    expect(batLaid.originX).toBeCloseTo(fromSlot.originX);
    expect(batLaid.originY).toBeCloseTo(fromSlot.originY);
    expect(batLaid.originZ).toBeCloseTo(fromSlot.originZ);
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
});
