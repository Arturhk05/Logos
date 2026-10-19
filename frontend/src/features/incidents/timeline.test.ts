import { describe, expect, it } from "vitest";

import { eventLabel } from "./timeline";

// Written by hand from RN-12: the transition says what happened, and no previous status is the report.
describe("eventLabel", () => {
  it.each([
    [null, "OPEN", "Reportado"],
    ["OPEN", "INVESTIGATING", "Assumido"],
    ["INVESTIGATING", "OPEN", "Devolvido à fila"],
    ["INVESTIGATING", "CLOSED", "Fechado"],
    ["INVESTIGATING", "INCONCLUSIVE", "Marcado como inconclusivo"],
  ] as const)("%s → %s reads %s", (from_status, to_status, expected) => {
    expect(eventLabel({ from_status, to_status })).toBe(expected);
  });
});
