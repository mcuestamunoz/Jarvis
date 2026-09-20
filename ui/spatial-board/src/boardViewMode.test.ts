import { describe, expect, it } from "vitest";
import { resolveInitialViewMode, viewModeStorageKey } from "./boardViewMode";

describe("resolveInitialViewMode", () => {
  it("T1: no stored value (fresh load) -> taller", () => {
    expect(resolveInitialViewMode(null)).toBe("taller");
  });

  it("T1: corrupted/unknown stored value -> taller, never throws", () => {
    expect(resolveInitialViewMode("bogus")).toBe("taller");
    expect(resolveInitialViewMode("")).toBe("taller");
  });

  it("T2: a valid stored 'grafo' is honored (persisted tab switch survives reload)", () => {
    expect(resolveInitialViewMode("grafo")).toBe("grafo");
  });

  it("T2: a valid stored 'taller' is honored", () => {
    expect(resolveInitialViewMode("taller")).toBe("taller");
  });
});

describe("viewModeStorageKey", () => {
  it("scopes the key per project", () => {
    expect(viewModeStorageKey("proj-1")).toBe("jarvis.spatial-board.view-mode.v1.proj-1");
    expect(viewModeStorageKey("proj-2")).toBe("jarvis.spatial-board.view-mode.v1.proj-2");
  });

  it("falls back to the bare key with no project", () => {
    expect(viewModeStorageKey(null)).toBe("jarvis.spatial-board.view-mode.v1");
  });
});
