import { describe, expect, it } from "vitest";
import { isSolidHitThrough, resolveClusterCenter } from "./situarInteractionState";

describe("isSolidHitThrough (E2)", () => {
  it("T1: false when situar+selected but idle (not dragging/preview/posting)", () => {
    expect(
      isSolidHitThrough({ situar: true, selectedId: "esc", solidId: "battery", busy: false }),
    ).toBe(false);
  });

  it("T2: true when situar+selected+busy (drag/preview/posting live)", () => {
    expect(
      isSolidHitThrough({ situar: true, selectedId: "esc", solidId: "battery", busy: true }),
    ).toBe(true);
  });

  it("never true for the selected solid itself, even when busy", () => {
    expect(
      isSolidHitThrough({ situar: true, selectedId: "esc", solidId: "esc", busy: true }),
    ).toBe(false);
  });

  it("never true when situar is off, even with a selection and busy", () => {
    expect(
      isSolidHitThrough({ situar: false, selectedId: "esc", solidId: "battery", busy: true }),
    ).toBe(false);
  });

  it("never true with no selection at all", () => {
    expect(
      isSolidHitThrough({ situar: true, selectedId: null, solidId: "battery", busy: true }),
    ).toBe(false);
  });
});

describe("resolveClusterCenter (E3)", () => {
  it("T3: while situar ON, a frozen center does not follow a live bbox change", () => {
    const frozen = { x: 10, y: 20 };
    const liveBefore = { x: 10, y: 20 };
    const liveAfter = { x: 400, y: -150 }; // a piece was dragged far away
    expect(resolveClusterCenter({ situar: true, liveCenter: liveBefore, frozenCenter: frozen })).toEqual(frozen);
    expect(resolveClusterCenter({ situar: true, liveCenter: liveAfter, frozenCenter: frozen })).toEqual(frozen);
  });

  it("falls back to the live center when situar is ON but nothing frozen yet", () => {
    const live = { x: 5, y: 5 };
    expect(resolveClusterCenter({ situar: true, liveCenter: live, frozenCenter: null })).toEqual(live);
  });

  it("always returns the live center when situar is OFF, regardless of any frozen value", () => {
    const live = { x: 7, y: -3 };
    const frozen = { x: 999, y: 999 };
    expect(resolveClusterCenter({ situar: false, liveCenter: live, frozenCenter: frozen })).toEqual(live);
  });
});
