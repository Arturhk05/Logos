import { describe, expect, it } from "vitest";

import { hasFilters, parseQueueFilters, queueSearchParams, toggle } from "./filters";

describe("parseQueueFilters", () => {
  it("reads repeated criticality and category params, most critical first", () => {
    const params = new URLSearchParams("criticality=LOW&criticality=HIGH&category=ROAD_BLOCKAGE");

    expect(parseQueueFilters(params)).toEqual({
      criticality: ["HIGH", "LOW"],
      category: ["ROAD_BLOCKAGE"],
      assignedToMe: false,
    });
  });

  it.each([
    ["assigned_to_me=true", true],
    ["", false],
    ["assigned_to_me=false", false],
    ["assigned_to_me=talvez", false],
  ])("reads %j as assigned to me = %s", (query, expected) => {
    expect(parseQueueFilters(new URLSearchParams(query)).assignedToMe).toBe(expected);
  });

  it("ignores unknown and repeated values", () => {
    const params = new URLSearchParams(
      "criticality=FOO&criticality=HIGH&criticality=HIGH&category=bar&page=2",
    );

    expect(parseQueueFilters(params)).toEqual({
      criticality: ["HIGH"],
      category: [],
      assignedToMe: false,
    });
  });
});

describe("queueSearchParams", () => {
  it("writes filters back as repeated params", () => {
    const params = queueSearchParams({
      criticality: ["HIGH", "MEDIUM"],
      category: [],
      assignedToMe: false,
    });

    expect(params.toString()).toBe("criticality=HIGH&criticality=MEDIUM");
  });

  it("writes nothing without filters", () => {
    expect(
      queueSearchParams({ criticality: [], category: [], assignedToMe: false }).toString(),
    ).toBe("");
  });

  it("writes assigned to me only when it is on, and reads it back", () => {
    const filters = { criticality: [], category: ["ROAD_BLOCKAGE" as const], assignedToMe: true };
    const params = queueSearchParams(filters);

    expect(params.toString()).toBe("category=ROAD_BLOCKAGE&assigned_to_me=true");
    expect(parseQueueFilters(params)).toEqual(filters);
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
    expect(hasFilters({ criticality: [], category: [], assignedToMe: false })).toBe(false);
    expect(hasFilters({ criticality: [], category: ["ROAD_BLOCKAGE"], assignedToMe: false })).toBe(
      true,
    );
    expect(hasFilters({ criticality: [], category: [], assignedToMe: true })).toBe(true);
  });
});
