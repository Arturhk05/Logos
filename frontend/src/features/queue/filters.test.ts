import { describe, expect, it } from "vitest";

import { hasFilters, parseQueueFilters, queueSearchParams, toggle } from "./filters";

describe("parseQueueFilters", () => {
  it("reads repeated criticality and category params, most critical first", () => {
    const params = new URLSearchParams("criticality=LOW&criticality=HIGH&category=ROAD_BLOCKAGE");

    expect(parseQueueFilters(params)).toEqual({
      criticality: ["HIGH", "LOW"],
      category: ["ROAD_BLOCKAGE"],
      assignee: null,
    });
  });

  it.each([
    ["assignee=me", "me"],
    ["assignee=none", "none"],
    ["", null],
    ["assignee=lucas", null],
  ])("reads %j as assignee %s", (query, expected) => {
    expect(parseQueueFilters(new URLSearchParams(query)).assignee).toBe(expected);
  });

  it("ignores unknown and repeated values", () => {
    const params = new URLSearchParams(
      "criticality=FOO&criticality=HIGH&criticality=HIGH&category=bar&page=2",
    );

    expect(parseQueueFilters(params)).toEqual({
      criticality: ["HIGH"],
      category: [],
      assignee: null,
    });
  });
});

describe("queueSearchParams", () => {
  it("writes filters back as repeated params", () => {
    const params = queueSearchParams({
      criticality: ["HIGH", "MEDIUM"],
      category: [],
      assignee: null,
    });

    expect(params.toString()).toBe("criticality=HIGH&criticality=MEDIUM");
  });

  it("writes nothing without filters", () => {
    expect(queueSearchParams({ criticality: [], category: [], assignee: null }).toString()).toBe(
      "",
    );
  });

  it("writes the assignee only when it is set, and reads it back", () => {
    const filters = {
      criticality: [],
      category: ["ROAD_BLOCKAGE" as const],
      assignee: "none" as const,
    };
    const params = queueSearchParams(filters);

    expect(params.toString()).toBe("category=ROAD_BLOCKAGE&assignee=none");
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
    expect(hasFilters({ criticality: [], category: [], assignee: null })).toBe(false);
    expect(hasFilters({ criticality: [], category: ["ROAD_BLOCKAGE"], assignee: null })).toBe(true);
    expect(hasFilters({ criticality: [], category: [], assignee: "me" })).toBe(true);
    expect(hasFilters({ criticality: [], category: [], assignee: "none" })).toBe(true);
  });
});
