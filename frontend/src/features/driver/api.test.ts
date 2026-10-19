import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { reportIncident } from "./api";

const API = "http://localhost/api";
const KEY = "6f1c2a4e-8a1b-4c3d-9e2f-0a1b2c3d4e5f";

describe("reportIncident", () => {
  it("sends the report with its idempotency key", async () => {
    let key: string | null = null;
    let body: unknown;
    server.use(
      http.post(`${API}/incidents`, async ({ request }) => {
        key = request.headers.get("Idempotency-Key");
        body = await request.json();
        return HttpResponse.json({ id: 142 }, { status: 201 });
      }),
    );

    const created = await reportIncident(
      {
        category: "ROAD_BLOCKAGE",
        criticality: "MEDIUM",
        location: "BR-101, km 45",
        description: "Carreta tombada",
      },
      KEY,
    );

    expect(key).toBe(KEY);
    expect(body).toEqual({
      category: "ROAD_BLOCKAGE",
      criticality: "MEDIUM",
      location: "BR-101, km 45",
      description: "Carreta tombada",
    });
    expect(created.id).toBe(142);
  });
});
