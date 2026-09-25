import { describe, expect, it } from "vitest";
import { cuboidFaceLayout } from "./cuboidFaces";

describe("cuboidFaceLayout", () => {
  it("T1: cube w=d=h=40 — six faces, each centered (left/top 0), each translateZ 20", () => {
    const faces = cuboidFaceLayout(40, 40, 40);
    expect(faces).toHaveLength(6);
    expect(faces.map((f) => f.name).sort()).toEqual(["back", "bottom", "front", "left", "right", "top"].sort());

    for (const face of faces) {
      expect(face.left).toBe(0);
      expect(face.top).toBe(0);
      expect(face.transform).toMatch(/translateZ\(20px\)/);
    }
  });

  it("T2: thin plate w=80.5, d=21, h=1 — MY5 top plate fixture (161x42x2mm @ pxPerMm 0.5)", () => {
    const faces = cuboidFaceLayout(80.5, 21, 1);
    const byName = Object.fromEntries(faces.map((f) => [f.name, f]));

    // top/bottom: fw=w, fh=d, translateZ(h/2)
    for (const name of ["top", "bottom"] as const) {
      expect(byName[name].width).toBe(80.5);
      expect(byName[name].height).toBe(21);
      expect(byName[name].transform).toContain("translateZ(0.5px)");
    }

    // left/right: fw=d, fh=h, translateZ(w/2)
    for (const name of ["left", "right"] as const) {
      expect(byName[name].width).toBe(21);
      expect(byName[name].height).toBe(1);
      expect(byName[name].transform).toContain("translateZ(40.25px)");
    }

    // No face's transform string re-centers via translateX/translateY —
    // centering lives entirely in left/top, never in the transform.
    for (const face of faces) {
      expect(face.transform).not.toMatch(/translateX/);
      expect(face.transform).not.toMatch(/translateY/);
    }
  });

  it("T2b: thin plate faces are actually centered within the w x h wrapper, not flush at an edge", () => {
    const faces = cuboidFaceLayout(80.5, 21, 1);
    const byName = Object.fromEntries(faces.map((f) => [f.name, f]));

    // left/right narrower (21px) than the wrapper (80.5px wide) must be
    // horizontally centered, not left:0 (the pre-fix bug).
    expect(byName.left.left).toBeCloseTo((80.5 - 21) / 2);
    expect(byName.right.left).toBeCloseTo((80.5 - 21) / 2);
    expect(byName.left.top).toBe(0);
    expect(byName.right.top).toBe(0);

    // top/bottom shorter (21px) than the wrapper (1px tall!) must be
    // vertically centered around the wrapper's own mid-height, not top:0.
    expect(byName.top.top).toBeCloseTo((1 - 21) / 2);
    expect(byName.bottom.top).toBeCloseTo((1 - 21) / 2);
    expect(byName.top.left).toBe(0);
    expect(byName.bottom.left).toBe(0);

    // front/back already matched the wrapper's own w x h before this
    // Buy — still centered (0,0), unchanged shape.
    expect(byName.front.left).toBe(0);
    expect(byName.front.top).toBe(0);
    expect(byName.back.left).toBe(0);
    expect(byName.back.top).toBe(0);
  });

  it("normals match the IC §0.6 lock exactly", () => {
    const faces = cuboidFaceLayout(10, 6, 4);
    const byName = Object.fromEntries(faces.map((f) => [f.name, f]));

    expect(byName.front.transform).toBe("translateZ(3px)");
    expect(byName.back.transform).toBe("rotateY(180deg) translateZ(3px)");
    expect(byName.left.transform).toBe("rotateY(-90deg) translateZ(5px)");
    expect(byName.right.transform).toBe("rotateY(90deg) translateZ(5px)");
    expect(byName.top.transform).toBe("rotateX(90deg) translateZ(2px)");
    expect(byName.bottom.transform).toBe("rotateX(-90deg) translateZ(2px)");
  });
});
