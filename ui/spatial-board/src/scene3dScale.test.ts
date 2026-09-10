import { describe, expect, it } from "vitest";
import { clampZoom, mmToPx, pxToMm, solidExtentPx, solidWrapperPx, ZOOM_MAX, ZOOM_MIN } from "./scene3dScale";

describe("mmToPx", () => {
  it("U1: mmToPx(127) at 0.5 -> 63.5, not capped", () => {
    expect(mmToPx(127, 0.5)).toBe(63.5);
  });

  it("U2: mmToPx(300) at 0.5 -> 150, must not match GLYPH's 120 cap", () => {
    expect(mmToPx(300, 0.5)).toBe(150);
  });
});

describe("pxToMm", () => {
  it("Board drag → Continuity pose B1 — inverse of mmToPx at the default scale", () => {
    expect(pxToMm(63.5, 0.5)).toBeCloseTo(127);
    expect(pxToMm(150, 0.5)).toBeCloseTo(300);
  });

  it("round-trips mmToPx for arbitrary mm/scale combinations", () => {
    for (const mm of [0, 1, 5.5, -12.3, 47.5, 230]) {
      for (const pxPerMm of [0.25, 0.5, 1, 2]) {
        expect(pxToMm(mmToPx(mm, pxPerMm), pxPerMm)).toBeCloseTo(mm);
      }
    }
  });

  it("defaults to SCENE3D.pxPerMm (0.5) when no scale is given", () => {
    expect(pxToMm(mmToPx(81.317))).toBeCloseTo(81.317);
  });
});

describe("clampZoom", () => {
  it("U1: Situar UX B1 — widened bounds allow values above the former max 2 and below the former min 0.5", () => {
    expect(ZOOM_MIN).toBe(0.25);
    expect(ZOOM_MAX).toBe(4);
    expect(clampZoom(10)).toBe(4);
    expect(clampZoom(0.01)).toBe(0.25);
    expect(clampZoom(3)).toBe(3); // above the OLD max 2, allowed now
    expect(clampZoom(0.3)).toBe(0.3); // below the OLD min 0.5, allowed now
  });

  it("passes an in-range value through unchanged", () => {
    expect(clampZoom(1)).toBe(1);
  });

  it("respects explicit min/max overrides", () => {
    expect(clampZoom(5, 0.5, 2)).toBe(2);
    expect(clampZoom(0.1, 0.5, 2)).toBe(0.5);
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

describe("solidWrapperPx", () => {
  it("box 50x21.6x12 at 0.5 -> {width:25, height:6} (CSS width=length, CSS height=height; width_mm/+Y lives only in translateZ)", () => {
    const wrap = solidWrapperPx(
      { shape: "box", length_mm: 50, width_mm: 21.6, height_mm: 12 },
      0.5,
    );
    expect(wrap.width).toBeCloseTo(25);
    expect(wrap.height).toBeCloseTo(6);
  });

  it("disk 127 at 0.5 -> {width:63.5, height:63.5}, never extent.z", () => {
    const wrap = solidWrapperPx({ shape: "disk", diameter_mm: 127 }, 0.5);
    expect(wrap.width).toBeCloseTo(63.5);
    expect(wrap.height).toBeCloseTo(63.5);
  });
});
