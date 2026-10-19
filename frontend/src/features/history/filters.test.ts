import { describe, expect, it } from "vitest";

import { historySearchParams, pageCount, parseHistoryFilters } from "./filters";

describe("parseHistoryFilters", () => {
  it("reads every filter and the page", () => {
    const params = new URLSearchParams(
      "status=INCONCLUSIVE&criticality=HIGH&category=ROAD_BLOCKAGE&page=3",
    );

    expect(parseHistoryFilters(params)).toEqual({
      status: ["INCONCLUSIVE"],
      criticality: ["HIGH"],
      category: ["ROAD_BLOCKAGE"],
      page: 3,
    });
  });

  it("keeps only closed statuses", () => {
    const params = new URLSearchParams("status=CLOSED&status=OPEN&status=INVESTIGATING");

    expect(parseHistoryFilters(params).status).toEqual(["CLOSED"]);
  });

  it.each(["-1", "0", "abc", "2.5", ""])("starts at the first page for page=%s", (page) => {
    expect(parseHistoryFilters(new URLSearchParams(`page=${page}`)).page).toBe(1);
  });
});

describe("historySearchParams", () => {
  it("omits the first page from the URL", () => {
    const params = historySearchParams({
      status: ["INCONCLUSIVE"],
      criticality: [],
      category: [],
      page: 1,
    });

    expect(params.toString()).toBe("status=INCONCLUSIVE");
  });

  it("keeps the other pages", () => {
    const params = historySearchParams({ status: [], criticality: ["LOW"], category: [], page: 2 });

    expect(params.toString()).toBe("criticality=LOW&page=2");
  });
});

describe("pageCount", () => {
  it.each([
    [0, 1],
    [1, 1],
    [20, 1],
    [21, 2],
    [45, 3],
  ])("%i incidents make %i page(s) of 20", (total, pages) => {
    expect(pageCount(total, 20)).toBe(pages);
  });
});
