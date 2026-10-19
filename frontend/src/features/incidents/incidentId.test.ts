import { describe, expect, it } from "vitest";

import { parseIncidentId } from "./incidentId";

describe("parseIncidentId", () => {
  it("reads a positive id from the URL", () => {
    expect(parseIncidentId("142")).toBe(142);
  });

  it.each([undefined, "", "abc", "0", "-3", "2.5", "1e3", "2147483648"])("rejects %o", (value) => {
    expect(parseIncidentId(value)).toBeNull();
  });
});
