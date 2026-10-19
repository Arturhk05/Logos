import { describe, expect, it } from "vitest";

import type { IncidentDetail } from "../../api/client";
import { conflictMessage } from "./conflict";

const base: IncidentDetail = {
  id: 7,
  version: 5,
  category: "VEHICLE_ACCIDENT",
  criticality: "HIGH",
  status: "OPEN",
  location: "BR-381, km 501",
  description: "Colisão entre dois carros.",
  reporter: { id: 9, username: "jose" },
  assignee: null,
  closed_by: null,
  closed_at: null,
  closure_reason: null,
  created_at: "2026-10-18T09:00:00Z",
  updated_at: "2026-10-18T09:10:00Z",
};
const camila = { id: 1 };
const API_MESSAGE = "Este incidente foi alterado por outra pessoa. Confira o estado atual.";

describe("conflictMessage", () => {
  it("names who assumed the incident first", () => {
    const current = {
      ...base,
      status: "INVESTIGATING" as const,
      assignee: { id: 2, username: "lucas" },
    };

    expect(conflictMessage(current, camila, API_MESSAGE)).toBe(
      "lucas assumiu este incidente antes de você.",
    );
  });

  it("names who closed the incident", () => {
    const current = {
      ...base,
      status: "CLOSED" as const,
      assignee: { id: 2, username: "lucas" },
      closed_by: { id: 3, username: "roberto" },
    };

    expect(conflictMessage(current, camila, API_MESSAGE)).toBe(
      "Este incidente foi encerrado por roberto.",
    );
  });

  it("falls back to the API message otherwise", () => {
    expect(conflictMessage(base, camila, API_MESSAGE)).toBe(API_MESSAGE);
  });

  it("does not blame the user for their own assignment", () => {
    const current = {
      ...base,
      status: "INVESTIGATING" as const,
      assignee: { id: 1, username: "camila" },
    };

    expect(conflictMessage(current, camila, API_MESSAGE)).toBe(API_MESSAGE);
  });
});
