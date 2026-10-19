import { describe, expect, it } from "vitest";

import { formatDateTime, formatElapsed } from "./format";

const now = new Date("2026-10-18T10:00:00Z");

describe("formatElapsed", () => {
  it.each([
    ["2026-10-18T09:59:30Z", "agora"],
    ["2026-10-18T09:57:00Z", "3 min"],
    ["2026-10-18T08:00:00Z", "2 h"],
    ["2026-10-17T09:00:00Z", "1 dia"],
    ["2026-10-13T10:00:00Z", "5 dias"],
  ])("formats %s as %s", (createdAt, expected) => {
    expect(formatElapsed(createdAt, now)).toBe(expected);
  });
});

describe("formatDateTime", () => {
  it("formats dates of this year without the year", () => {
    expect(formatDateTime("2026-10-18T07:02:00Z", now, "UTC")).toBe("18/10, 07:02");
  });

  it("formats dates of other years with the year", () => {
    expect(formatDateTime("2025-03-04T15:30:00Z", now, "UTC")).toBe("04/03/2025, 15:30");
  });
});
