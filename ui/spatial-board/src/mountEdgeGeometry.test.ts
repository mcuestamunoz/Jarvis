import { describe, expect, it } from "vitest";
import { mountEdgeSegments } from "./mountEdgeGeometry";
import type { SpatialNode } from "./types";

function node(
  id: string,
  patch: Partial<SpatialNode> = {},
): SpatialNode {
  return {
    id,
    title: id,
    declaredName: "",
    kind: "component",
    fields: [],
    x: 0,
    y: 0,
    width: 100,
    height: 80,
    ...patch,
  };
}

describe("mountEdgeSegments", () => {
  it("U1: mountedOn to present target → one segment with mid-bottom → mid-top", () => {
    const nodes = [
      node("flight_controller", { x: 0, y: 0, width: 100, height: 80, mountedOn: "frame_plate" }),
      node("frame_plate", { x: 200, y: 200, width: 100, height: 80 }),
    ];
    const edges = mountEdgeSegments(nodes);
    expect(edges).toHaveLength(1);
    expect(edges[0]).toEqual({
      fromId: "flight_controller",
      toId: "frame_plate",
      x1: 50,
      y1: 80,
      x2: 250,
      y2: 200,
    });
  });

  it("U2: mountedOn to missing id → zero edges", () => {
    const nodes = [
      node("flight_controller", { mountedOn: "frame_plate_missing" }),
    ];
    expect(mountEdgeSegments(nodes)).toEqual([]);
  });

  it("U3: no mountedOn → zero edges", () => {
    const nodes = [node("flight_controller"), node("frame_plate", { x: 200, y: 200 })];
    expect(mountEdgeSegments(nodes)).toEqual([]);
  });
});
