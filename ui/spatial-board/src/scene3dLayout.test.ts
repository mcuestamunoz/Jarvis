import { describe, expect, it } from "vitest";
import { layoutSolidsRow } from "./scene3dLayout";

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
