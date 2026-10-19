import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { IncidentDetail } from "../../api/client";
import { server } from "../../test/server";
import { assumeIncident, changeStatus } from "./api";

const API = "http://localhost/api";

const incident: IncidentDetail = {
  id: 7,
  version: 3,
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
  events: [],
};

describe("assumeIncident", () => {
  it("assumes with the version the user saw", async () => {
    let body: unknown;
    server.use(
      http.post(`${API}/incidents/7/assume`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...incident, version: 4, status: "INVESTIGATING" });
      }),
    );

    const updated = await assumeIncident(incident);

    expect(body).toEqual({ version: 3 });
    expect(updated.status).toBe("INVESTIGATING");
  });

  it("returns the current incident on a conflict", async () => {
    server.use(
      http.post(`${API}/incidents/7/assume`, () =>
        HttpResponse.json(
          {
            detail: "Este incidente foi alterado por outra pessoa. Confira o estado atual.",
            current: {
              ...incident,
              version: 5,
              status: "INVESTIGATING",
              assignee: { id: 2, username: "lucas" },
            },
          },
          { status: 409 },
        ),
      ),
    );

    await expect(assumeIncident(incident)).rejects.toMatchObject({
      kind: "conflict",
      current: { version: 5, assignee: { username: "lucas" } },
    });
  });
});

describe("changeStatus", () => {
  it("sends the status, the reason and the version", async () => {
    let body: unknown;
    server.use(
      http.patch(`${API}/incidents/7/status`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...incident, version: 5, status: "CLOSED" });
      }),
    );

    await changeStatus(
      { ...incident, version: 4, status: "INVESTIGATING" },
      "CLOSED",
      "Pista liberada",
    );

    expect(body).toEqual({ version: 4, status: "CLOSED", reason: "Pista liberada" });
  });

  it("leaves the reason out when there is none", async () => {
    let body: unknown;
    server.use(
      http.patch(`${API}/incidents/7/status`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...incident, version: 5 });
      }),
    );

    await changeStatus({ ...incident, version: 4, status: "INVESTIGATING" }, "OPEN");

    expect(body).toEqual({ version: 4, status: "OPEN" });
  });

  it("sends no reason when sending the incident back to the queue", async () => {
    let body: unknown;
    server.use(
      http.patch(`${API}/incidents/7/status`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...incident, version: 5 });
      }),
    );

    await changeStatus({ ...incident, version: 4, status: "INVESTIGATING" }, "OPEN");

    expect(body).toEqual({ version: 4, status: "OPEN" });
  });
});
