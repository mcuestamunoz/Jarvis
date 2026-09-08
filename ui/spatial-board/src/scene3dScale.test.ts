import { describe, expect, it } from "vitest";
import { mmToPx, solidExtentPx } from "./scene3dScale";

describe("mmToPx", () => {
  it("U1: mmToPx(127) at 0.5 -> 63.5, not capped", () => {
    expect(mmToPx(127, 0.5)).toBe(63.5);
  });

  it("U2: mmToPx(300) at 0.5 -> 150, must not match GLYPH's 120 cap", () => {
    expect(mmToPx(300, 0.5)).toBe(150);
  });
});

describe("solidExtentPx", () => {
  it("U3: box 50x21.6x12 -> {x:25, y:10.8, z:6} at 0.5", () => {
    const extent = solidExtentPx(
      { shape: "box", length_mm: 50, width_mm: 21.6, height_mm: 12 },
      0.5,
    );
    expect(extent.x).toBeCloseTo(25);
    expect(extent.y).toBeCloseTo(10.8);
    expect(extent.z).toBeCloseTo(6);
  });

  it("U4: disk 127 -> {x:63.5, y:63.5, z:0}", () => {
    const extent = solidExtentPx({ shape: "disk", diameter_mm: 127 }, 0.5);
    expect(extent.x).toBeCloseTo(63.5);
    expect(extent.y).toBeCloseTo(63.5);
    expect(extent.z).toBe(0);
  });
});
