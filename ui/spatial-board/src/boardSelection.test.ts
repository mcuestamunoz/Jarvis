import { describe, expect, it } from "vitest";
import { nextSelectedId, reconcileSelection } from "./boardSelection";

describe("nextSelectedId", () => {
  it("U1: null + select esc -> esc", () => {
    expect(nextSelectedId(null, { type: "select", id: "esc" })).toBe("esc");
  });

  it("U2: esc + select motors -> motors", () => {
    expect(nextSelectedId("esc", { type: "select", id: "motors" })).toBe("motors");
  });

  it("U3: esc + select esc -> esc (no toggle-off)", () => {
    expect(nextSelectedId("esc", { type: "select", id: "esc" })).toBe("esc");
  });

  it("U4: esc + clear -> null", () => {
    expect(nextSelectedId("esc", { type: "clear" })).toBeNull();
  });

  it("U5: null + clear -> null", () => {
    expect(nextSelectedId(null, { type: "clear" })).toBeNull();
  });
});

describe("reconcileSelection", () => {
  it("U6: esc still present -> esc", () => {
    expect(reconcileSelection("esc", ["esc", "motors"])).toBe("esc");
  });

  it("U7: esc no longer present -> null", () => {
    expect(reconcileSelection("esc", ["motors"])).toBeNull();
  });

  it("U8: already null -> null", () => {
    expect(reconcileSelection(null, ["esc"])).toBeNull();
  });
});
