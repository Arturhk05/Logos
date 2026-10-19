import { describe, expect, it } from "vitest";

import { hasFilters, parseQueueFilters, queueSearchParams, toggle } from "./filters";

describe("parseQueueFilters", () => {
  it("reads repeated criticality and category params, most critical first", () => {
    const params = new URLSearchParams("criticality=LOW&criticality=HIGH&category=ROAD_BLOCKAGE");

    expect(parseQueueFilters(params)).toEqual({
      criticality: ["HIGH", "LOW"],
      category: ["ROAD_BLOCKAGE"],
    });
  });

  it("ignores unknown and repeated values", () => {
    const params = new URLSearchParams(
      "criticality=FOO&criticality=HIGH&criticality=HIGH&category=bar&page=2",
    );

    expect(parseQueueFilters(params)).toEqual({ criticality: ["HIGH"], category: [] });
  });
});

describe("queueSearchParams", () => {
  it("writes filters back as repeated params", () => {
    const params = queueSearchParams({ criticality: ["HIGH", "MEDIUM"], category: [] });

    expect(params.toString()).toBe("criticality=HIGH&criticality=MEDIUM");
  });

  it("writes nothing without filters", () => {
    expect(queueSearchParams({ criticality: [], category: [] }).toString()).toBe("");
  });
});

describe("toggle", () => {
  it("adds a value that is off and removes one that is on", () => {
    expect(toggle(["HIGH"], "LOW")).toEqual(["HIGH", "LOW"]);
    expect(toggle(["HIGH", "LOW"], "HIGH")).toEqual(["LOW"]);
  });
});

describe("hasFilters", () => {
  it("tells whether any filter is on", () => {
    expect(hasFilters({ criticality: [], category: [] })).toBe(false);
    expect(hasFilters({ criticality: [], category: ["ROAD_BLOCKAGE"] })).toBe(true);
  });
});
