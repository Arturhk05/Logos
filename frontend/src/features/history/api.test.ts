import { QueryClient } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { historyQueryOptions } from "./api";

const API = "http://localhost/api";

describe("historyQueryOptions", () => {
  it("asks the API for the page, 20 items and the filters", async () => {
    let url = new URL("http://localhost");
    server.use(
      http.get(`${API}/incidents/history`, ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json({ items: [], page: 2, page_size: 20, total: 0 });
      }),
    );

    await new QueryClient().query(
      historyQueryOptions({ status: ["CLOSED"], criticality: ["HIGH"], category: [], page: 2 }),
    );

    expect(url.searchParams.get("page")).toBe("2");
    expect(url.searchParams.get("page_size")).toBe("20");
    expect(url.searchParams.getAll("status")).toEqual(["CLOSED"]);
    expect(url.searchParams.getAll("criticality")).toEqual(["HIGH"]);
    expect(url.searchParams.has("category")).toBe(false);
  });
});
