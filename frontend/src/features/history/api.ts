import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, request } from "../../api/client";
import type { components } from "../../api/schema";
import type { HistoryFilters } from "./filters";

export type HistoryItem = components["schemas"]["IncidentHistoryItem"];

export const HISTORY_PAGE_SIZE = 20;

function orUndefined<T>(values: T[]): T[] | undefined {
  return values.length > 0 ? values : undefined;
}

export function historyQueryOptions(filters: HistoryFilters) {
  return queryOptions({
    queryKey: ["incidents", "history", filters],
    queryFn: ({ signal }) =>
      request(
        api.GET("/api/incidents/history", {
          params: {
            query: {
              status: orUndefined(filters.status),
              criticality: orUndefined(filters.criticality),
              category: orUndefined(filters.category),
              page: filters.page,
              page_size: HISTORY_PAGE_SIZE,
            },
          },
          signal,
        }),
      ),
    // Turning the page keeps the current one on screen until the next arrives.
    placeholderData: keepPreviousData,
  });
}
