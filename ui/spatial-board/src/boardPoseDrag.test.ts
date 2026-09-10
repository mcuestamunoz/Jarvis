import { describe, expect, it } from "vitest";
import {
  computeDragPosePayload,
  computeDragPreviewOffsetPx,
  isDraggableSolid,
  screenDeltaToLocalPx,
} from "./boardPoseDrag";
import { pxToMm } from "./scene3dScale";

describe("isDraggableSolid", () => {
  it("no geometry -> not draggable", () => {
    expect(isDraggableSolid({})).toBe(false);
  });

  it("geometry present, no solidCopies -> draggable (singleton)", () => {
    expect(isDraggableSolid({ geometry: { shape: "box" } })).toBe(true);
  });

  it("solidCopies: 1 -> still draggable (not a real copy)", () => {
    expect(isDraggableSolid({ geometry: { shape: "box" }, solidCopies: 1 })).toBe(true);
  });

  it("solidCopies: 4 -> NOT draggable (station copies never arm)", () => {
    expect(isDraggableSolid({ geometry: { shape: "box" }, solidCopies: 4 })).toBe(false);
  });

  it("solidCopies: 2 -> NOT draggable (the >=2 threshold matches expandSolidCopies)", () => {
    expect(isDraggableSolid({ geometry: { shape: "disk" }, solidCopies: 2 })).toBe(false);
  });
});

describe("screenDeltaToLocalPx", () => {
  it("untilted: identity — screen Δ → local dx/dy, dz=0", () => {
    const local = screenDeltaToLocalPx({
      deltaScreenPxX: 10,
      deltaScreenPxY: -5,
      zoom: 1,
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    expect(local.dxPx).toBeCloseTo(10);
    expect(local.dyPx).toBeCloseTo(-5);
    expect(local.dzPx).toBeCloseTo(0);
  });

  it("side view (rotateY≈90°): screen-X lands mostly on local Z (declared Y / depth)", () => {
    const local = screenDeltaToLocalPx({
      deltaScreenPxX: 10,
      deltaScreenPxY: 0,
      zoom: 1,
      rotateXDeg: 0,
      rotateYDeg: 90,
    });
    expect(local.dxPx).toBeCloseTo(0, 5);
    expect(local.dyPx).toBeCloseTo(0, 5);
    expect(local.dzPx).toBeCloseTo(10, 5);
  });

  it("zoom un-scales before the inverse", () => {
    const local = screenDeltaToLocalPx({
      deltaScreenPxX: 20,
      deltaScreenPxY: 0,
      zoom: 2,
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    expect(local.dxPx).toBeCloseTo(10);
  });
});

describe("computeDragPosePayload", () => {
  it("untilted WYSIWYG: screen Δx→x_mm, screen Δy→z_mm; y_mm untouched when dz=0", () => {
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      priorPose: undefined,
      deltaScreenPxX: 10,
      deltaScreenPxY: -5,
      zoom: 1,
      pxPerMm: 0.5,
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    expect(payload).toEqual({
      component_key: "battery",
      origin_key: "frame_plate",
      x_mm: 20,
      y_mm: 0,
      z_mm: -10,
    });
  });

  it("prior pose: Δ adds to x_mm and z_mm; y_mm carries at tilt 0", () => {
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate_2",
      priorPose: { originKey: "frame_plate_2", xMm: 0, yMm: 4, zMm: 13 },
      deltaScreenPxX: 5,
      deltaScreenPxY: 5,
      zoom: 1,
      pxPerMm: 0.5,
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    expect(payload.x_mm).toBeCloseTo(10);
    expect(payload.y_mm).toBe(4);
    expect(payload.z_mm).toBeCloseTo(23);
  });

  it("zero vertical delta keeps z_mm null when never set", () => {
    const payload = computeDragPosePayload({
      componentKey: "esc",
      originKey: "flight_controller",
      priorPose: { originKey: "flight_controller", xMm: 5 },
      deltaScreenPxX: 0,
      deltaScreenPxY: 0,
      zoom: 1,
      pxPerMm: 0.5,
    });
    expect(payload.z_mm).toBeNull();
    expect(payload.x_mm).toBeCloseTo(5);
    expect(payload.y_mm).toBeCloseTo(0);
  });

  it("zoom un-scales the screen delta before converting to mm", () => {
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      priorPose: undefined,
      deltaScreenPxX: 20,
      deltaScreenPxY: 0,
      zoom: 2,
      pxPerMm: 0.5,
    });
    expect(payload.x_mm).toBeCloseTo(20);
    expect(payload.z_mm).toBeNull();
  });

  it("U1: untilted default leaves y_mm at prior; writes z_mm from screen Δy", () => {
    const withPrior = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      priorPose: { originKey: "frame_plate", yMm: 2, zMm: 13 },
      deltaScreenPxX: 10,
      deltaScreenPxY: 10,
      zoom: 1,
      pxPerMm: 0.5,
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    expect(withPrior.y_mm).toBe(2);
    expect(withPrior.z_mm).toBeCloseTo(33);
    expect(withPrior.x_mm).toBeCloseTo(20);
  });

  it("side view: lateral screen drag writes y_mm (depth), not only x_mm", () => {
    // Engineer field: "no me deja mover lateral" — at rotateY=90, screen-X
    // is world depth; must land on declared y_mm / originZ.
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      priorPose: { originKey: "frame_plate", xMm: 1, yMm: 0, zMm: 2 },
      deltaScreenPxX: 10,
      deltaScreenPxY: 0,
      zoom: 1,
      pxPerMm: 0.5,
      rotateXDeg: 0,
      rotateYDeg: 90,
    });
    expect(payload.x_mm).toBeCloseTo(1, 5);
    expect(payload.z_mm).toBeCloseTo(2, 5);
    expect(payload.y_mm).toBeCloseTo(20, 5); // 10px → 20mm depth
  });

  it("U2: Shift mode writes only y_mm from local dz; x/z unchanged", () => {
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate_2",
      priorPose: { originKey: "frame_plate_2", xMm: 7, yMm: -3, zMm: 13 },
      deltaScreenPxX: 0,
      deltaScreenPxY: 10,
      zoom: 1,
      pxPerMm: 0.5,
      axisMode: "z",
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    // At tilt 0, screen Δy → local dy only, dz=0 — Shift depth is 0 from
    // a pure vertical screen drag untilted. Use side view for a real dz:
    expect(payload.y_mm).toBeCloseTo(-3);
    expect(payload.x_mm).toBe(7);
    expect(payload.z_mm).toBe(13);

    const side = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate_2",
      priorPose: { originKey: "frame_plate_2", xMm: 7, yMm: -3, zMm: 13 },
      deltaScreenPxX: 10,
      deltaScreenPxY: 0,
      zoom: 1,
      pxPerMm: 0.5,
      axisMode: "z",
      rotateXDeg: 0,
      rotateYDeg: 90,
    });
    expect(side.y_mm).toBeCloseTo(17, 5); // -3 + 20
    expect(side.x_mm).toBe(7);
    expect(side.z_mm).toBe(13);
  });

  it("U2: Shift mode with no prior starts y_mm from 0 (side-view horizontal)", () => {
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      deltaScreenPxX: 20,
      deltaScreenPxY: 0,
      zoom: 1,
      pxPerMm: 0.5,
      axisMode: "z",
      rotateXDeg: 0,
      rotateYDeg: 90,
    });
    expect(payload.y_mm).toBeCloseTo(40, 5);
    expect(payload.x_mm).toBe(0);
    expect(payload.z_mm).toBeNull();
  });

  it("U2: Shift mode respects zoom", () => {
    const payload = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      deltaScreenPxX: 20,
      deltaScreenPxY: 0,
      zoom: 2,
      pxPerMm: 0.5,
      axisMode: "z",
      rotateXDeg: 0,
      rotateYDeg: 90,
    });
    expect(payload.y_mm).toBeCloseTo(20, 5);
  });
});

describe("computeDragPreviewOffsetPx", () => {
  it("untilted preview matches commit: dx→x_mm, dy→z_mm", () => {
    const args = {
      deltaScreenPxX: 17,
      deltaScreenPxY: -9,
      zoom: 1.5,
      rotateXDeg: 0,
      rotateYDeg: 0,
    };
    const preview = computeDragPreviewOffsetPx(args);
    const commit = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      priorPose: undefined,
      ...args,
      pxPerMm: 0.5,
    });
    expect(pxToMm(preview.dxPx, 0.5)).toBeCloseTo(commit.x_mm);
    expect(pxToMm(preview.dyPx, 0.5)).toBeCloseTo(commit.z_mm as number);
    expect(preview.dzPx).toBeCloseTo(0);
  });

  it("side-view preview dz matches commit y_mm", () => {
    const args = {
      deltaScreenPxX: 10,
      deltaScreenPxY: 0,
      zoom: 1,
      rotateXDeg: 0,
      rotateYDeg: 90,
    };
    const preview = computeDragPreviewOffsetPx(args);
    const commit = computeDragPosePayload({
      componentKey: "battery",
      originKey: "frame_plate",
      ...args,
      pxPerMm: 0.5,
    });
    expect(pxToMm(preview.dzPx, 0.5)).toBeCloseTo(commit.y_mm);
    expect(preview.dxPx).toBeCloseTo(0, 5);
  });

  it("Shift preview zeroes dx/dy, keeps dz", () => {
    const preview = computeDragPreviewOffsetPx({
      deltaScreenPxX: 10,
      deltaScreenPxY: 0,
      zoom: 1,
      rotateXDeg: 0,
      rotateYDeg: 90,
      axisMode: "z",
    });
    expect(preview.dxPx).toBe(0);
    expect(preview.dyPx).toBe(0);
    expect(preview.dzPx).toBeCloseTo(10, 5);
  });

  it("un-scales by zoom", () => {
    const preview = computeDragPreviewOffsetPx({
      deltaScreenPxX: 20,
      deltaScreenPxY: 40,
      zoom: 2,
      rotateXDeg: 0,
      rotateYDeg: 0,
    });
    expect(preview.dxPx).toBeCloseTo(10);
    expect(preview.dyPx).toBeCloseTo(20);
    expect(preview.dzPx).toBeCloseTo(0);
  });

  it("zero delta -> zero offset", () => {
    const preview = computeDragPreviewOffsetPx({
      deltaScreenPxX: 0,
      deltaScreenPxY: 0,
      zoom: 1,
    });
    expect(preview).toEqual({ dxPx: 0, dyPx: 0, dzPx: 0 });
  });
});
