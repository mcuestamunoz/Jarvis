import { describe, expect, it } from "vitest";
import { cylinderSolidLayout } from "./cylinderFaces";

describe("cylinderSolidLayout", () => {
  it("T1: cube-like D=H=40 — two caps (left=0, top=0, translateZ 20), 16 slats with the correct chord/left", () => {
    const { caps, slats } = cylinderSolidLayout(40, 40);

    expect(caps).toHaveLength(2);
    expect(caps.map((c) => c.name).sort()).toEqual(["bottom", "top"]);
    for (const cap of caps) {
      expect(cap.width).toBe(40);
      expect(cap.height).toBe(40);
      expect(cap.left).toBe(0);
      expect(cap.top).toBe(0);
      expect(cap.transform).toMatch(/translateZ\(20px\)/);
    }

    expect(slats).toHaveLength(16);
    const chord = 2 * 20 * Math.sin(Math.PI / 16);
    for (const slat of slats) {
      expect(slat.width).toBeCloseTo(chord);
      expect(slat.left).toBeCloseTo((40 - chord) / 2);
      expect(slat.top).toBe(0);
      expect(slat.height).toBe(40);
    }
  });

  it("T2: thin hub D=65.36, H=3.4 — Gemfan 51466-class prop-hub fixture (Ø130.72 x 6.8mm @ pxPerMm 0.5)", () => {
    const { caps } = cylinderSolidLayout(65.36, 3.4);

    for (const cap of caps) {
      expect(cap.width).toBe(65.36);
      expect(cap.height).toBe(65.36);
      expect(cap.top).toBeCloseTo(-30.98);
      expect(cap.transform).toContain("translateZ(1.7px)");
      expect(cap.transform).not.toMatch(/translateX/);
      expect(cap.transform).not.toMatch(/translateY/);
    }
  });

  it("T2b: tall post D=3, H=15 — standoff-visor-sized fixture (Ø6 x 30mm @ pxPerMm 0.5)", () => {
    const { caps } = cylinderSolidLayout(3, 15);

    for (const cap of caps) {
      expect(cap.top).toBeCloseTo(6);
      expect(cap.transform).toContain("translateZ(7.5px)");
    }
  });

  it("T2c: cap top follows (H-D)/2 exactly, including the negative case", () => {
    for (const [d, h] of [[65.36, 3.4], [3, 15], [40, 40], [21, 1]] as const) {
      const { caps } = cylinderSolidLayout(d, h);
      for (const cap of caps) {
        expect(cap.top).toBeCloseTo((h - d) / 2);
      }
    }
  });

  it("normals match the IC §0.5 lock exactly, and no cap/slat transform ever uses translateX/translateY", () => {
    const { caps, slats } = cylinderSolidLayout(10, 6);
    const byName = Object.fromEntries(caps.map((c) => [c.name, c]));

    expect(byName.top.transform).toBe("rotateX(90deg) translateZ(3px)");
    expect(byName.bottom.transform).toBe("rotateX(-90deg) translateZ(3px)");

    for (const cap of caps) {
      expect(cap.transform).not.toMatch(/translateX/);
      expect(cap.transform).not.toMatch(/translateY/);
    }
    for (const slat of slats) {
      expect(slat.transform).not.toMatch(/translateX/);
      expect(slat.transform).not.toMatch(/translateY/);
      expect(slat.transform).toMatch(/^rotateY\([\d.]+deg\) translateZ\(5px\)$/);
    }
  });

  it("always exactly 2 caps and 16 slats (N frozen), regardless of D/H", () => {
    for (const [d, h] of [[1, 1], [200, 5], [5, 200]] as const) {
      const { caps, slats } = cylinderSolidLayout(d, h);
      expect(caps).toHaveLength(2);
      expect(slats).toHaveLength(16);
    }
  });
});
