import { describe, expect, it } from "vitest";
import { computeAncestorChain, isAssemblyRootPlate, isDimmed } from "./mountAncestorChain";

describe("isAssemblyRootPlate", () => {
  it("U1: frame_plate is the assembly root", () => {
    expect(isAssemblyRootPlate("frame_plate")).toBe(true);
  });

  it("U2: frame_plate_2 (a sibling plate) is not", () => {
    expect(isAssemblyRootPlate("frame_plate_2")).toBe(false);
  });

  it("U3: frame (the root spec, not the plate part) is not", () => {
    expect(isAssemblyRootPlate("frame")).toBe(false);
  });
});

describe("computeAncestorChain", () => {
  it("T3: esc -> frame_plate, ordered chain ending at the plate", () => {
    const nodes = new Map([
      ["esc", { id: "esc", mountedOn: "frame_plate" }],
      ["frame_plate", { id: "frame_plate", mountedOn: undefined }],
    ]);
    expect(computeAncestorChain("esc", nodes)).toEqual(["esc", "frame_plate"]);
  });

  it("T3: multi-hop — battery -> flight_controller -> frame_plate", () => {
    const nodes = new Map([
      ["battery", { id: "battery", mountedOn: "flight_controller" }],
      ["flight_controller", { id: "flight_controller", mountedOn: "frame_plate" }],
      ["frame_plate", { id: "frame_plate", mountedOn: undefined }],
    ]);
    expect(computeAncestorChain("battery", nodes)).toEqual([
      "battery",
      "flight_controller",
      "frame_plate",
    ]);
  });

  it("T4: no mountedOn at all -> chain of 1, honest stop", () => {
    const nodes = new Map([["esc", { id: "esc", mountedOn: undefined }]]);
    expect(computeAncestorChain("esc", nodes)).toEqual(["esc"]);
  });

  it("T4: mountedOn points at a target that isn't a projected node -> honest stop", () => {
    const nodes = new Map([["esc", { id: "esc", mountedOn: "frame_plate_removed" }]]);
    expect(computeAncestorChain("esc", nodes)).toEqual(["esc"]);
  });

  it("T4: cycle guard — A -> B -> A never loops, never throws", () => {
    const nodes = new Map([
      ["a", { id: "a", mountedOn: "b" }],
      ["b", { id: "b", mountedOn: "a" }],
    ]);
    expect(computeAncestorChain("a", nodes)).toEqual(["a", "b"]);
  });

  it("T4: self-mount (A -> A) stops immediately, never throws", () => {
    const nodes = new Map([["a", { id: "a", mountedOn: "a" }]]);
    expect(computeAncestorChain("a", nodes)).toEqual(["a"]);
  });

  it("stops AT the assembly root, never walks past it even if it has its own mountedOn", () => {
    const nodes = new Map([
      ["esc", { id: "esc", mountedOn: "frame_plate" }],
      // Defensive: even if frame_plate somehow carried a mountedOn, the
      // walk must stop the moment it reaches the root, never continue.
      ["frame_plate", { id: "frame_plate", mountedOn: "frame" }],
      ["frame", { id: "frame", mountedOn: undefined }],
    ]);
    expect(computeAncestorChain("esc", nodes)).toEqual(["esc", "frame_plate"]);
  });
});

describe("isDimmed", () => {
  it("T5: a solid in the chain stays full opacity (not dimmed)", () => {
    const chain = ["esc", "frame_plate"];
    expect(isDimmed("esc", chain)).toBe(false);
    expect(isDimmed("frame_plate", chain)).toBe(false);
  });

  it("T5: a solid outside the chain dims", () => {
    const chain = ["esc", "frame_plate"];
    expect(isDimmed("battery", chain)).toBe(true);
  });

  it("T5: no selection (empty chain) -> nothing dims", () => {
    expect(isDimmed("battery", [])).toBe(false);
    expect(isDimmed("esc", [])).toBe(false);
  });
});
