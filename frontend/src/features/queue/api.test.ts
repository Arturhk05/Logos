import { QueryClient } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { queueQueryOptions } from "./api";

const API = "http://localhost/api";
const EMPTY_QUEUE = { items: [], counts: { HIGH: 0, MEDIUM: 0, LOW: 0 } };

describe("queueQueryOptions", () => {
  it("sends the filters to the queue endpoint", async () => {
    let url = new URL("http://localhost");
    server.use(
      http.get(`${API}/incidents`, ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json(EMPTY_QUEUE);
      }),
    );

    await new QueryClient().query(
      queueQueryOptions({
        criticality: ["HIGH", "LOW"],
        category: ["ROAD_BLOCKAGE"],
        assignee: "me",
      }),
    );

    expect(url.searchParams.getAll("criticality")).toEqual(["HIGH", "LOW"]);
    expect(url.searchParams.getAll("category")).toEqual(["ROAD_BLOCKAGE"]);
    expect(url.searchParams.get("assignee")).toBe("me");
  });

  it("asks for every active incident without filters", async () => {
    let url = new URL("http://localhost");
    server.use(
      http.get(`${API}/incidents`, ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json(EMPTY_QUEUE);
      }),
    );

    await new QueryClient().query(
      queueQueryOptions({ criticality: [], category: [], assignee: null }),
    );

    expect(url.search).toBe("");
  });
});
