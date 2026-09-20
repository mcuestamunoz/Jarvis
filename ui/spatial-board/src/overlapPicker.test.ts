import { describe, expect, it } from "vitest";
import { pieceStripSolids } from "./overlapPicker";

describe("pieceStripSolids", () => {
  it("T8: Situar OFF lists every geometry-bearing solid, including station copies", () => {
    const solids = [
      { id: "esc", geometry: { shape: "box" } },
      { id: "motors", geometry: { shape: "cylinder" }, solidCopies: 4 },
    ];
    expect(pieceStripSolids(solids, false).map((s) => s.id)).toEqual(["esc", "motors"]);
  });

  it("T8: Situar ON drops station copies (isDraggableSolid gate)", () => {
    const solids = [
      { id: "esc", geometry: { shape: "box" } },
      { id: "motors", geometry: { shape: "cylinder" }, solidCopies: 4 },
    ];
    expect(pieceStripSolids(solids, true).map((s) => s.id)).toEqual(["esc"]);
  });

  it("T8: a stacked occluded id is still selectable from the strip regardless of 3D hit-test", () => {
    const solids = [
      { id: "esc", geometry: { shape: "box" } },
      { id: "battery", geometry: { shape: "box" } },
      { id: "flight_controller", geometry: { shape: "box" } },
    ];
    const ids = pieceStripSolids(solids, false).map((s) => s.id);
    expect(ids).toContain("battery");
    expect(ids).toHaveLength(3);
  });

  it("never mutates the input array", () => {
    const solids = [{ id: "esc", geometry: { shape: "box" } }];
    const result = pieceStripSolids(solids, false);
    expect(result).not.toBe(solids);
    expect(solids).toHaveLength(1);
  });
});
