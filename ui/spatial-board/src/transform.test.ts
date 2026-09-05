import { describe, expect, it } from "vitest";
import {
  applyZoomToPoint,
  screenToWorld,
  screenToWorldDelta,
  worldToScreen,
} from "./transform";
import type { CanvasTransform } from "./types";

const t: CanvasTransform = { zoom: 2, panX: 10, panY: -4 };

describe("transform", () => {
  it("worldToScreen and screenToWorld invert", () => {
    const world = { x: 40, y: 80 };
    const screen = worldToScreen(world, t);
    const back = screenToWorld(screen, t);
    expect(back.x).toBeCloseTo(world.x);
    expect(back.y).toBeCloseTo(world.y);
  });

  it("Q1 zoom-to-cursor keeps the world point under the screen cursor", () => {
    const screen = { x: 120, y: 90 };
    const worldBefore = screenToWorld(screen, t);
    const next = applyZoomToPoint(t, screen, t.zoom * 1.1);
    const worldAfter = screenToWorld(screen, next);
    expect(worldAfter.x).toBeCloseTo(worldBefore.x, 8);
    expect(worldAfter.y).toBeCloseTo(worldBefore.y, 8);
  });

  it("Q2 screen delta to world divides by zoom", () => {
    const d = screenToWorldDelta(20, -10, t);
    expect(d.x).toBeCloseTo(10);
    expect(d.y).toBeCloseTo(-5);
  });

  it("clamps zoom to 0.1–5", () => {
    const screen = { x: 0, y: 0 };
    expect(applyZoomToPoint(t, screen, 99).zoom).toBe(5);
    expect(applyZoomToPoint(t, screen, 0.001).zoom).toBe(0.1);
  });
});
