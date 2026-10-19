import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, request } from "../../api/client";
import type { components } from "../../api/schema";
import type { QueueFilters } from "./filters";

export type QueueItem = components["schemas"]["IncidentSummary"];

// New incidents and changes by other analysts show up without a reload.
export const QUEUE_REFRESH_MS = 15_000;

export function queueQueryOptions(filters: QueueFilters) {
  return queryOptions({
    queryKey: ["incidents", "queue", filters],
    queryFn: ({ signal }) =>
      request(
        api.GET("/api/incidents", {
          params: {
            query: {
              criticality: filters.criticality.length > 0 ? filters.criticality : undefined,
              category: filters.category.length > 0 ? filters.category : undefined,
              assignee: filters.assignee ?? undefined,
            },
          },
          signal,
        }),
      ),
    refetchInterval: QUEUE_REFRESH_MS,
    // While a new filter loads, the old list stays instead of a blank screen.
    placeholderData: keepPreviousData,
  });
}
