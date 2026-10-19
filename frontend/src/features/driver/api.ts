import { queryOptions } from "@tanstack/react-query";

import { api, request, type IncidentDetail } from "../../api/client";
import type { ReportIncidentRequest } from "./report";

export const categoriesQueryOptions = queryOptions({
  queryKey: ["categories"],
  queryFn: ({ signal }) => request(api.GET("/api/categories", { signal })),
  // The categories and their suggested criticality only change with a new release of the API.
  staleTime: Infinity,
});

/**
 * The same key is sent on every attempt of the same report, so a double tap or a retry after a
 * timeout creates only one incident (US-08, ADR-08).
 */
export function reportIncident(
  body: ReportIncidentRequest,
  idempotencyKey: string,
): Promise<IncidentDetail> {
  return request(
    api.POST("/api/incidents", {
      params: { header: { "Idempotency-Key": idempotencyKey } },
      body,
    }),
  );
}

export const myReportsQueryOptions = queryOptions({
  queryKey: ["incidents", "mine"],
  queryFn: ({ signal }) => request(api.GET("/api/incidents/mine", { signal })),
  // The driver sees the central take over a report without reloading (US-09).
  refetchInterval: 30_000,
});
